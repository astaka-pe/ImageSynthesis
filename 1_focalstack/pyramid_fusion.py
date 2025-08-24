import cv2
import numpy as np
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__name__), "..")))
from utils.common import align_images, normalize_map
import utils.pyramid as Pyramid

def compute_focus_map(img_gray, ksize=5):
    lap = cv2.Laplacian(img_gray, cv2.CV_64F, ksize=ksize)
    return np.abs(lap)

def multi_focus_fusion_pyramid(images, levels=3):
    gray_imgs = [cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) for img in images]
    
    focus_maps = [compute_focus_map(g) for g in gray_imgs]
    weights = [normalize_map(f) for f in focus_maps]

    weight_pyrs = [Pyramid.build_gaussian_pyramid(w, levels) for i, w in enumerate(weights)]

    lap_pyrs = [Pyramid.build_laplacian_pyramid(img, levels) for i, img in enumerate(images)]

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
        
    fused_img = Pyramid.reconstruct_laplacian_pyramid(fused_pyr)
    return fused_img

# ========== Main ==========
if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    img1 = cv2.imread("input/focus_near.png")
    img2 = cv2.imread("input/focus_mid.png")
    img3 = cv2.imread("input/focus_far.png")

    # Align images to the first one
    img2_aligned = align_images(img1, img2)
    img3_aligned = align_images(img1, img3)

    fused = multi_focus_fusion_pyramid([img1, img2_aligned, img3_aligned], levels=3)
    cv2.imwrite("output/fused_pyramid.png", fused)