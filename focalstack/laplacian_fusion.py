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
    
    # --- 追加: アライメント結果を保存 ---
    cv2.imwrite(f"tmp/{name}.png", aligned)

    return aligned

def compute_focus_map(img_gray, ksize=5, name="focusmap"):
    """Compute per-pixel focus measure (Laplacian absolute response)."""
    lap = cv2.Laplacian(img_gray, cv2.CV_64F, ksize=ksize)
    abs_lap = np.abs(lap)

    # --- 追加: 可視化用に正規化して保存 ---
    vis = cv2.normalize(abs_lap, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    cv2.imwrite(f"tmp/{name}.png", vis)

    return abs_lap

def normalize_map(weight, name="weightmap"):
    weight = cv2.GaussianBlur(weight, (5,5), 0)
    weight = np.clip(weight, 0, None)
    norm = weight / (np.max(weight) + 1e-8)

    # --- 追加: 可視化用に保存 ---
    vis = (norm * 255).astype(np.uint8)
    cv2.imwrite(f"tmp/{name}.png", vis)

    return norm

def multi_focus_fusion(images):
    """Perform multi-focus image fusion."""
    gray_imgs = [cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) for img in images]

    # Compute focus maps
    focus_maps = [compute_focus_map(g, name=f"focusmap_{i}") for i, g in enumerate(gray_imgs)]
    weights = [normalize_map(f, name=f"weightmap_{i}") for i, f in enumerate(focus_maps)]

    # Weighted average
    numerator = np.zeros_like(images[0], dtype=np.float64)
    denominator = np.zeros_like(gray_imgs[0], dtype=np.float64)

    for i, (img, w) in enumerate(zip(images, weights)):
        w3 = cv2.merge([w, w, w])  # 3 channels
        numerator += img.astype(np.float64) * w3
        denominator += w

        # --- 追加: 重み付き画像を保存 ---
        weighted_img = (img.astype(np.float64) * w3 / (np.max(w3)+1e-8)).astype(np.uint8)
        cv2.imwrite(f"tmp/weighted_{i}.png", weighted_img)

    denominator3 = cv2.merge([denominator, denominator, denominator])
    fused = numerator / (denominator3 + 1e-8)
    return np.clip(fused, 0, 255).astype(np.uint8)


# ========== Main ==========
if __name__ == "__main__":
    os.makedirs("tmp", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    # Load images (3 focus levels)
    img1 = cv2.imread("input/focus_near.png")
    img2 = cv2.imread("input/focus_mid.png")
    img3 = cv2.imread("input/focus_far.png")

    # Align images to the first one
    img2_aligned = align_images(img1, img2, name="aligned_mid")
    img3_aligned = align_images(img1, img3, name="aligned_far")

    # Multi-focus fusion
    fused = multi_focus_fusion([img1, img2_aligned, img3_aligned])

    # Save final result
    cv2.imwrite("output/fused_laplacian.png", fused)
