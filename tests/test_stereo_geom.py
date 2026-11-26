"""Synthetic check of box_disparity and letterbox_nv12: python3 tests/test_stereo_geom.py"""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from stereo_geom import box_disparity, letterbox_nv12  # noqa: E402

rng = np.random.default_rng(0)
H, W = 1088, 1280
bg = cv2.GaussianBlur(rng.integers(0, 255, (H, W)).astype(np.uint8), (3, 3), 0)
obj = cv2.GaussianBlur(rng.integers(0, 255, (300, 260)).astype(np.uint8), (3, 3), 0)
for true_d in (12.0, 40.25, 66.9, 150.5, 216.3):
    L, R = bg.copy(), np.roll(bg, -3, axis=1)          # background at 3 px
    L[400:700, 500:760] = obj
    # right image: background at 3 px, object shifted left by true_d (sub-pixel, cubic remap)
    R[400:700, 200:1060] = np.roll(bg, -3, axis=1)[400:700, 200:1060]
    x0 = 500 - true_d
    xs = np.arange(200, 1060)
    src_x = (xs - x0).astype(np.float32)
    inside = (src_x >= 0) & (src_x <= 259)
    mapx = np.tile(src_x, (300, 1))
    mapy = np.tile(np.arange(300, dtype=np.float32)[:, None], (1, 860))
    warped = cv2.remap(obj, mapx, mapy, cv2.INTER_CUBIC)
    R[400:700, 200:1060][:, inside] = warped[:, inside]
    d, iqr, n = box_disparity(L, R, (500, 400, 760, 700))
    assert d is not None and abs(d - true_d) < 0.25, (true_d, d, n)
    print(f'disparity true {true_d:7.2f}  measured {d:7.2f}  iqr {iqr:.2f}  patches {n}')
# flat box -> no texture -> None
flat = np.full((H, W), 120, np.uint8)
assert box_disparity(flat, flat, (500, 400, 760, 700))[0] is None
# letterbox: 1280x1088 -> 640x544 with 48-row bars
y = np.full((H, W), 200, np.uint8); uv = np.full((H // 2, W // 2, 2), 90, np.uint8)
t = letterbox_nv12(y, uv)
assert t.shape == (1, 960, 640, 1)
ty = t.reshape(-1)[:640 * 640].reshape(640, 640)
assert ty[47, 320] == 127 and ty[48, 320] == 200 and ty[591, 320] == 200 and ty[592, 320] == 127
print('all checks passed')
