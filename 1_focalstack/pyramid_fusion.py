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

def compute_focus_map(img_gray, ksize=5):
    lap = cv2.Laplacian(img_gray, cv2.CV_64F, ksize=ksize)
    return np.abs(lap)

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

def multi_focus_fusion_pyramid(images, levels=3):
    gray_imgs = [cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) for img in images]
    
    focus_maps = [compute_focus_map(g) for g in gray_imgs]
    weights = [normalize_map(f) for f in focus_maps]

    weight_pyrs = [build_gaussian_pyramid(w, levels) for i, w in enumerate(weights)]

    lap_pyrs = [build_laplacian_pyramid(img, levels) for i, img in enumerate(images)]

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
        
    fused_img = reconstruct_laplacian_pyramid(fused_pyr)
    return fused_img

# ========== Main ==========
if __name__ == "__main__":
    os.makedirs("tmp", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    img1 = cv2.imread("input/focus_near.png")
    img2 = cv2.imread("input/focus_mid.png")
    img3 = cv2.imread("input/focus_far.png")

    # Align images to the first one
    img2_aligned = align_images(img1, img2, name="aligned_mid")
    img3_aligned = align_images(img1, img3, name="aligned_far")

    fused = multi_focus_fusion_pyramid([img1, img2_aligned, img3_aligned], levels=3)
    cv2.imwrite("output/fused_pyramid.jpg", fused)