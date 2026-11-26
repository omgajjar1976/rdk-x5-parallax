"""Pure helpers (no ROS, no BPU) so they can be tested on any machine."""
import cv2
import numpy as np


def letterbox_nv12(y, uv, size=640):
    """Letterbox an NV12 frame (y: HxW, uv: H/2 x W/2 x 2) to size x size; returns the model input."""
    h, w = y.shape
    s = min(size / w, size / h)
    nw, nh = int(w * s) // 2 * 2, int(h * s) // 2 * 2
    top, left = (size - nh) // 2 // 2 * 2, (size - nw) // 2 // 2 * 2
    out_y = np.full((size, size), 127, np.uint8)
    out_uv = np.full((size // 2, size // 2, 2), 128, np.uint8)
    out_y[top:top + nh, left:left + nw] = cv2.resize(y, (nw, nh))
    out_uv[top // 2:(top + nh) // 2, left // 2:(left + nw) // 2] = cv2.resize(uv, (nw // 2, nh // 2))
    return np.concatenate([out_y.reshape(-1), out_uv.reshape(-1)]).reshape(1, size * 3 // 2, size, 1)


def box_disparity(L, R, box, max_disp=260, half=7, min_std=12.0, min_ncc=0.85):
    """Median disparity (px, R shifted left) over textured patches in the middle of box; None if too few.

    Returns (median, iqr, n_patches). L, R: rectified grey images, same size.
    """
    h, w = L.shape
    x0, y0, x1, y1 = box
    # central 60% of the box: less background bleeding in at the edges
    cx0, cx1 = x0 + 0.2 * (x1 - x0), x1 - 0.2 * (x1 - x0)
    cy0, cy1 = y0 + 0.2 * (y1 - y0), y1 - 0.2 * (y1 - y0)
    step = max(3, int(min(cx1 - cx0, cy1 - cy0) / 8))
    ds = []
    for v in range(int(max(cy0, half)), int(min(cy1, h - half - 1)), step):
        for u in range(int(max(cx0, half + 1)), int(min(cx1, w - half - 1)), step):
            p = L[v - half:v + half + 1, u - half:u + half + 1]
            if p.std() < min_std:
                continue
            a = max(0, u - half - max_disp)
            strip = R[v - half:v + half + 1, a:u + half + 1]
            r = cv2.matchTemplate(strip, p, cv2.TM_CCOEFF_NORMED)[0]
            k = int(np.argmax(r))
            if r[k] < min_ncc or k == 0 or k == len(r) - 1:
                continue
            den = r[k - 1] - 2 * r[k] + r[k + 1]
            off = 0.5 * (r[k - 1] - r[k + 1]) / den if den < 0 else 0.0
            ds.append((u - half) - (a + k + off))
    if len(ds) < 5:
        return None, None, len(ds)
    ds = np.asarray(ds)
    q1, med, q3 = np.percentile(ds, [25, 50, 75])
    return float(med), float(q3 - q1), len(ds)
