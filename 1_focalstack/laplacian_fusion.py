import cv2
import numpy as np
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__name__), "..")))
from utils.common import align_images, normalize_map

def compute_focus_map(img_gray, ksize=5):
    lap = cv2.Laplacian(img_gray, cv2.CV_64F, ksize=ksize)
    return np.abs(lap)

def multi_focus_fusion(images):
    """Perform multi-focus image fusion."""
    gray_imgs = [cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) for img in images]

    # Compute focus maps
    focus_maps = [compute_focus_map(g) for i, g in enumerate(gray_imgs)]
    weights = [normalize_map(f) for i, f in enumerate(focus_maps)]

    # Weighted average
    numerator = np.zeros_like(images[0], dtype=np.float64)
    denominator = np.zeros_like(gray_imgs[0], dtype=np.float64)

    for i, (img, w) in enumerate(zip(images, weights)):
        w3 = cv2.merge([w, w, w])  # 3 channels
        numerator += img.astype(np.float64) * w3
        denominator += w

    denominator3 = cv2.merge([denominator, denominator, denominator])
    fused = numerator / (denominator3 + 1e-8)
    return np.clip(fused, 0, 255).astype(np.uint8)


# ========== Main ==========
if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)

    # Load images (3 focus levels)
    img1 = cv2.imread("input/focus_near.png")
    img2 = cv2.imread("input/focus_mid.png")
    img3 = cv2.imread("input/focus_far.png")

    # Align images to the first one
    img2_aligned = align_images(img1, img2)
    img3_aligned = align_images(img1, img3)

    # Multi-focus fusion
    fused = multi_focus_fusion([img1, img2_aligned, img3_aligned])

    # Save final result
    cv2.imwrite("output/fused_laplacian.png", fused)
