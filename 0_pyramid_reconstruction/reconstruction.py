import cv2
import numpy as np
import os

def build_gaussian_pyramid(img, levels):
    gp = [img.astype(np.float64)]
    for i in range(levels):
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

def reconstruct_from_laplacian(lp):
    levels = len(lp) - 1
    current = lp[-1]
    recons = [current]
    for i in range(levels-1, -1, -1):
        size = (lp[i].shape[1], lp[i].shape[0])
        current = cv2.pyrUp(current, dstsize=size)
        current = cv2.add(current, lp[i])
        recons.append(current)
    return recons

if __name__ == "__main__":
    os.makedirs("tmp", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    img = cv2.imread("input/focus_mid.png").astype(np.float64)
    levels = 3

    gp = build_gaussian_pyramid(img, levels)
    lp = build_laplacian_pyramid(img, levels)

    for i, g in enumerate(gp):
        cv2.imwrite(f"tmp/gaussian_level_{i}.png", np.clip(g, 0, 255).astype(np.uint8))
    for i, l in enumerate(lp):
        norm_l = cv2.normalize(l, None, 0, 255, cv2.NORM_MINMAX)
        cv2.imwrite(f"tmp/laplacian_level_{i}.png", norm_l.astype(np.uint8))

    recons = reconstruct_from_laplacian(lp)

    for i, r in enumerate(recons):
        cv2.imwrite(f"output/reconstruct_step_{i}.png", np.clip(r, 0, 255).astype(np.uint8))