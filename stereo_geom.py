"""Pure helpers (no ROS, no BPU) so they can be tested on any machine."""
import cv2
import numpy as np


_LB = {}


def letterbox_nv12(y, uv, size=640):
    """Letterbox an NV12 frame (y: HxW, uv: H/2 x W/2 x 2) to size x size; returns the model input.

    Reuses one output buffer per input size; an exact 2x downscale (1280-wide camera) is a strided copy.
    """
    h, w = y.shape
    s = min(size / w, size / h)
    nw, nh = int(w * s) // 2 * 2, int(h * s) // 2 * 2
    top, left = (size - nh) // 2 // 2 * 2, (size - nw) // 2 // 2 * 2
    if (h, w, size) not in _LB:
        buf = np.empty(size * size * 3 // 2, np.uint8)
        buf[:size * size] = 127
        buf[size * size:] = 128
        _LB[(h, w, size)] = buf
    buf = _LB[(h, w, size)]
    oy = buf[:size * size].reshape(size, size)
    ouv = buf[size * size:].reshape(size // 2, size // 2, 2)
    if (nw, nh) == (w // 2, h // 2):
        oy[top:top + nh, left:left + nw] = y[::2, ::2]
        ouv[top // 2:(top + nh) // 2, left // 2:(left + nw) // 2] = uv[::2, ::2]
    else:
        oy[top:top + nh, left:left + nw] = cv2.resize(y, (nw, nh), interpolation=cv2.INTER_AREA)
        ouv[top // 2:(top + nh) // 2, left // 2:(left + nw) // 2] = cv2.resize(uv, (nw // 2, nh // 2), interpolation=cv2.INTER_AREA)
    return buf.reshape(1, size * 3 // 2, size, 1)


def decode_yolov8_level(cls, box, scale, stride, score):
    """One YOLOv8 head level (cls: ..xC logits, box: ..x64 DFL bins) -> xyxy (640 input px), class ids, scores.

    scale: per-channel dequant scale for an int32 box output (64,), or None for float output.
    Only rows above the score threshold are dequantized and decoded.
    """
    c = cls.reshape(-1, cls.shape[-1])
    mx = c.max(1)
    idx = np.flatnonzero(mx >= -np.log(1 / score - 1))
    if idx.size == 0:
        return np.zeros((0, 4), np.float32), np.zeros(0, int), np.zeros(0, np.float32)
    ids = c[idx].argmax(1)
    sc = 1 / (1 + np.exp(-mx[idx]))
    b = box.reshape(-1, box.shape[-1])[idx].astype(np.float32)
    if scale is not None:
        b *= scale
    b = b.reshape(-1, 4, 16)
    b = np.exp(b - b.max(2, keepdims=True))
    ltrb = (b * np.arange(16, dtype=np.float32)).sum(2) / b.sum(2)
    g = int(round(np.sqrt(c.shape[0])))
    gx, gy = idx % g + 0.5, idx // g + 0.5
    xyxy = np.stack([gx - ltrb[:, 0], gy - ltrb[:, 1], gx + ltrb[:, 2], gy + ltrb[:, 3]], 1) * stride
    return xyxy.astype(np.float32), ids, sc.astype(np.float32)


def nms(xyxy, scores, ids, iou=0.45, score=0.0):
    """Class-wise NMS (OpenCV); returns kept indices."""
    if len(xyxy) == 0:
        return np.zeros(0, int)
    xywh = np.c_[xyxy[:, :2], xyxy[:, 2:] - xyxy[:, :2]].tolist()
    return np.asarray(cv2.dnn.NMSBoxesBatched(xywh, scores.tolist(), ids.tolist(), score, iou), int).reshape(-1)


def box_disparity(L, R, box, max_disp=260, half=7, min_std=12.0, min_ncc=0.85, grid=5):
    """Median disparity (px, R shifted left) over textured patches in the middle of box; None if too few.

    Returns (median, iqr, n_patches). L, R: rectified grey images, same size.
    """
    h, w = L.shape
    x0, y0, x1, y1 = box
    # central 60% of the box: less background bleeding in at the edges
    cx0, cx1 = x0 + 0.2 * (x1 - x0), x1 - 0.2 * (x1 - x0)
    cy0, cy1 = y0 + 0.2 * (y1 - y0), y1 - 0.2 * (y1 - y0)
    # at most grid x grid patch centres per box: cost stays flat for big boxes (a tall bottle took 890 ms;
    # each small matchTemplate costs ~1.3 ms on the busy A55 cores, so the grid is kept small)
    vs = np.unique(np.linspace(max(cy0, half), min(cy1, h - half - 2), grid).astype(int))
    us = np.unique(np.linspace(max(cx0, half + 1), min(cx1, w - half - 2), grid).astype(int))
    ds = []
    for v in vs:
        for u in us:
            p = L[v - half:v + half + 1, u - half:u + half + 1]
            if cv2.meanStdDev(p)[1][0, 0] < min_std:
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
