import cv2
import numpy as np
import os

def align_images(ref_img, img, name="aligned"):
    """Align img to ref_img using ECC (affine warp)."""
    ref_gray = cv2.cvtColor(ref_img, cv2.COLOR_BGR2GRAY)
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    warp_mode = cv2.MOTION_AFFINE
    warp_matrix = np.eye(2, 3, dtype=np.float32)

    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 5000, 1e-6)
    cc, warp_matrix = cv2.findTransformECC(ref_gray, img_gray, warp_matrix, warp_mode, criteria)
    
    aligned = cv2.warpAffine(img, warp_matrix, (ref_img.shape[1], ref_img.shape[0]),
                             flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
    
    cv2.imwrite(f"tmp/{name}.png", aligned)

    return aligned

def compute_exposure_weights(img):
    """Compute weight map based on contrast, saturation, and well-exposedness."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0

    # Contrast: Laplacian response
    contrast = np.abs(cv2.Laplacian(gray, cv2.CV_32F, ksize=3))

    # Saturation: per-pixel standard deviation across color channels
    saturation = img.std(axis=2) / 255.0

    # Well-exposedness: Gaussian curve centered at 0.5
    sigma = 0.2
    well_exposed = np.exp(-0.5 * ((img.astype(np.float32)/255.0 - 0.5)**2) / (sigma**2))
    well_exposed = np.prod(well_exposed, axis=2)

    weight = contrast * saturation * well_exposed
    return weight + 1e-12  # avoid zero

def normalize_map(weight):
    weight = cv2.GaussianBlur(weight, (5,5), 0)
    weight = np.clip(weight, 0, None)
    return weight / (np.max(weight) + 1e-8)

def build_gaussian_pyramid(img, levels):
    gp = [img.astype(np.float64)]
    for i in range(1, levels+1):
        img = cv2.pyrDown(img)
        gp.append(img.astype(np.float64))
    return gp

def build_laplacian_pyramid(img, levels):
    gp = build_gaussian_pyramid(img, levels)
    lp = []

    for i in range(levels):
        size = (gp[i].shape[1], gp[i].shape[0])
        GE = cv2.pyrUp(gp[i+1], dstsize=size)
        L = gp[i] - GE
        lp.append(L)
    lp.append(gp[-1])
    return lp

def reconstruct_laplacian_pyramid(lp):
    img = lp[-1]
    for i in range(len(lp)-2, -1, -1):
        size = (lp[i].shape[1], lp[i].shape[0])
        img = cv2.pyrUp(img, dstsize=size) + lp[i]
    return np.clip(img, 0, 255).astype(np.uint8)

def exposure_fusion_pyramid(images, levels=5):
    # Compute exposure-based weights
    weights = [normalize_map(compute_exposure_weights(img)) for img in images]

    # Build Gaussian pyramids of weights
    weight_pyrs = [build_gaussian_pyramid(w, levels) for w in weights]

    # Build Laplacian pyramids of images
    lap_pyrs = [build_laplacian_pyramid(img, levels) for img in images]

    # Fuse pyramids
    fused_pyr = []
    for level in range(levels+1):
        num = np.zeros_like(lap_pyrs[0][level])
        den = np.zeros_like(weight_pyrs[0][level])
        for lap, wp in zip(lap_pyrs, weight_pyrs):
            w = cv2.merge([wp[level]]*3)
            num += lap[level] * w
            den += wp[level]
        den3 = cv2.merge([den, den, den])
        fused = num / (den3 + 1e-8)
        fused_pyr.append(fused)
        
    return reconstruct_laplacian_pyramid(fused_pyr)

# ========== Main ==========
if __name__ == "__main__":
    os.makedirs("tmp", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    # Load input LDR images with different exposures
    img1 = cv2.imread("input/ev_low.png")
    img2 = cv2.imread("input/ev_mid.png")
    img3 = cv2.imread("input/ev_high.png")

    # Align images to the middle exposure
    img1_aligned = align_images(img2, img1, name="ev_low")
    img3_aligned = align_images(img2, img3, name="ev_high")

    # Exposure fusion
    fused = exposure_fusion_pyramid([img1_aligned, img2, img3_aligned], levels=5)

    # Save result
    cv2.imwrite("output/fused_exposure.png", fused)