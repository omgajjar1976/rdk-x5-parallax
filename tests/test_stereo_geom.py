"""Synthetic check of box_disparity and letterbox_nv12: python3 tests/test_stereo_geom.py"""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from stereo_geom import box_disparity, decode_yolov8_level, letterbox_nv12, nms  # noqa: E402

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
    assert d is not None and abs(d - true_d) < 0.25 and n <= 25, (true_d, d, n)
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
# YOLOv8 decode: one 40x40 cell (row 10, col 20) of class 7, DFL peaked at l=2,t=3,r=4,b=5, int32 + scale
cls = np.full((1, 40, 40, 80), -10, np.float32); cls[0, 10, 20, 7] = 3.0
scale = np.full(64, 0.01, np.float32)
box = np.zeros((1, 40, 40, 64), np.int32)
for side, k in enumerate((2, 3, 4, 5)):
    box[0, 10, 20, side * 16 + k] = 3000          # 30.0 after scale -> one-hot softmax
xyxy, ids, sc = decode_yolov8_level(cls, box, scale, 16, 0.35)
assert ids.tolist() == [7] and abs(sc[0] - 1 / (1 + np.exp(-3))) < 1e-6
assert np.allclose(xyxy[0], [(20.5 - 2) * 16, (10.5 - 3) * 16, (20.5 + 4) * 16, (10.5 + 5) * 16], atol=1e-3), xyxy
xyxy_raw, _, _ = decode_yolov8_level(cls, box, None, 16, 0.35)   # without the scale: still peaked, same box
assert np.allclose(xyxy_raw, xyxy, atol=1e-3)
box[0, 10, 20, :] = 0; box[0, 10, 20, [2, 16 + 3, 32 + 4, 48 + 5]] = 30   # small ints: only correct WITH scale
xs, _, _ = decode_yolov8_level(cls, box, scale, 16, 0.35); xn, _, _ = decode_yolov8_level(cls, box, None, 16, 0.35)
assert abs(xs[0, 2] - xs[0, 0] - (6 * 16)) > 1 and abs(xn[0, 2] - xn[0, 0] - 6 * 16) < 1e-2, (xs, xn)
keep = nms(np.array([[0, 0, 10, 10], [1, 1, 10, 10], [0, 0, 10, 10]], np.float32), np.array([.9, .8, .7], np.float32), np.array([0, 0, 1]))
assert sorted(keep.tolist()) == [0, 2], keep
print('all checks passed')
