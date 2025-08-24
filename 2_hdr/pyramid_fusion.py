import cv2
import numpy as np
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__name__), "..")))
from utils.common import align_images, normalize_map
import utils.pyramid as Pyramid

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

def exposure_fusion_pyramid(images, levels=5):
    # Compute exposure-based weights
    weights = [normalize_map(compute_exposure_weights(img)) for img in images]

    # Build Gaussian pyramids of weights
    weight_pyrs = [Pyramid.build_gaussian_pyramid(w, levels) for w in weights]

    # Build Laplacian pyramids of images
    lap_pyrs = [Pyramid.build_laplacian_pyramid(img, levels) for img in images]

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
        
    return Pyramid.reconstruct_laplacian_pyramid(fused_pyr)

# ========== Main ==========
if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)

    # Load input LDR images with different exposures
    img1 = cv2.imread("input/ev_low.png")
    img2 = cv2.imread("input/ev_mid.png")
    img3 = cv2.imread("input/ev_high.png")

    # Align images to the middle exposure
    img1_aligned = align_images(img2, img1)
    img3_aligned = align_images(img2, img3)

    # Exposure fusion
    fused = exposure_fusion_pyramid([img1_aligned, img2, img3_aligned], levels=5)

    # Save result
    cv2.imwrite("output/fused_exposure.png", fused)