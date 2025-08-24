import cv2
import numpy as np

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