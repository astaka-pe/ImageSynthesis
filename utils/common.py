import cv2
import numpy as np

def align_images(ref_img, img):
    """Align img to ref_img using ECC (affine warp)."""
    ref_gray = cv2.cvtColor(ref_img, cv2.COLOR_BGR2GRAY)
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    warp_mode = cv2.MOTION_AFFINE
    warp_matrix = np.eye(2, 3, dtype=np.float32)

    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 5000, 1e-6)
    cc, warp_matrix = cv2.findTransformECC(ref_gray, img_gray, warp_matrix, warp_mode, criteria)
    
    aligned = cv2.warpAffine(img, warp_matrix, (ref_img.shape[1], ref_img.shape[0]),
                             flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
        
    return aligned

def normalize_map(weight):
    weight = cv2.GaussianBlur(weight, (5,5), 0)
    return weight / (np.max(weight) + 1e-8)
