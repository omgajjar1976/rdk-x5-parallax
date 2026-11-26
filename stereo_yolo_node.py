#!/usr/bin/env python3
"""YOLOv8n on the BPU + per-object stereo distance, for the RDK X5 with a GS130W stereo camera.

In:  /image_combine_raw  (sensor_msgs/Image nv12, left on top of right, rectified by mipi_cam,
                          which must run with mipi_rotation:=90.0 so disparity is horizontal)
     /image_combine_raw/right/camera_info  (rectified P: fx = P[0], fx*B = -P[3] in px*mm)
Out: /stereo_yolo/detections  (ai_msgs/PerceptionTargets, same stamp as the image;
                               roi type = "<class> <Z>m" for the web view, attribute distance_m)
     /stereo_yolo/perf        (std_msgs/String JSON, timings per frame)

Distance per box: NCC patch search along the same row in the right image over the central part of
the box, median disparity with sub-pixel fit, Z = fx*B / d (planar depth from the left camera).
"""
import json
import sys
import time

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import CameraInfo, Image
from std_msgs.msg import String
from ai_msgs.msg import Attribute, PerceptionTargets, Roi, Target

import hbm_runtime
sys.path.insert(0, '/app/pydev_demo')  # D-Robotics helpers, package hobot-sp-samples
import utils.postprocess_utils as post  # noqa: E402

from stereo_geom import box_disparity, decode_yolov8_level, letterbox_nv12, nms  # noqa: E402

COCO = [l.strip() for l in open('/app/pydev_demo/02_detection_sample/03_ultralytics_yolov8/coco_classes.names')]


class StereoYolo(Node):
    def __init__(self):
        super().__init__('stereo_yolo')
        self.declare_parameter('model', '/app/pydev_demo/models/yolov8_640x640_nv12.bin')
        self.declare_parameter('score_thres', 0.35)
        self.declare_parameter('nms_thres', 0.45)
        self.score = self.get_parameter('score_thres').value
        self.nms = self.get_parameter('nms_thres').value
        self.m = hbm_runtime.HB_HBMRuntime(self.get_parameter('model').value)
        self.mn = self.m.model_names[0]
        self.inp = self.m.input_names[self.mn][0]
        self.outs = self.m.output_names[self.mn]   # [cls80, box80, cls40, box40, cls20, box20]
        self.quants = self.m.output_quants[self.mn]
        assert [self.m.output_shapes[self.mn][n][-1] for n in self.outs] == [80, 64] * 3, 'unexpected YOLOv8 head layout'
        self.scales = {k: (q.scale.astype(np.float32) if int(q.quant_type) == 2 else None) for k, q in self.quants.items()}
        self.fxB = None  # px*m, from camera_info
        self.acc, self.t_acc = [], time.perf_counter()
        self.create_subscription(CameraInfo, '/image_combine_raw/right/camera_info', self.on_info, 1)
        # depth 1: newest frame, no backlog; RELIABLE because best-effort drops whole 4 MB frames (got none)
        latest = QoSProfile(depth=1, history=HistoryPolicy.KEEP_LAST, reliability=ReliabilityPolicy.RELIABLE)
        self.create_subscription(Image, '/image_combine_raw', self.on_image, latest)
        self.pub = self.create_publisher(PerceptionTargets, '/stereo_yolo/detections', 10)
        self.pub_perf = self.create_publisher(String, '/stereo_yolo/perf', 10)
        self.get_logger().info(f'model {self.mn} loaded')

    def on_info(self, ci):
        if ci.p[0] > 0 and ci.p[3] < 0:
            fxB = -ci.p[3] / 1000.0   # P[3] = -fx*B with B in mm
            if self.fxB is None:
                self.get_logger().info(f'rectified fx={ci.p[0]:.2f}px  fx*B={fxB:.3f}px*m  B={fxB / ci.p[0] * 1000:.2f}mm')
            self.fxB = fxB

    def detect(self, y, uv):
        h, w = y.shape
        out = self.m.run({self.mn: {self.inp: letterbox_nv12(y, uv)}})[self.mn]
        B, S, I = [], [], []
        for i, stride in enumerate([8, 16, 32]):
            bn = self.outs[2 * i + 1]
            # own dequant: utils.dequantize_tensor skips SCALE (=2) outputs, leaving the int32 box head raw
            b, ids, s = decode_yolov8_level(out[self.outs[2 * i]], out[bn], self.scales[bn], stride, self.score)
            B.append(b); S.append(s); I.append(ids)
        B, S, I = np.concatenate(B), np.concatenate(S), np.concatenate(I)
        keep = nms(B, S, I, self.nms)
        return post.scale_coords_back(B[keep], w, h, 640, 640, 1), I[keep], S[keep]

    def on_image(self, msg):
        if self.fxB is None:
            return
        t0 = time.perf_counter()
        W, H2 = msg.width, msg.height
        H = H2 // 2
        a = np.frombuffer(msg.data, np.uint8)
        yy = a[:W * H2].reshape(H2, W)
        L, R = yy[:H], yy[H:]
        uv = a[W * H2:].reshape(H2 // 2, W // 2, 2)[:H // 2]   # left half of the UV plane rows
        t1 = time.perf_counter()
        boxes, ids, scores = self.detect(L, uv)
        t2 = time.perf_counter()
        out = PerceptionTargets()
        out.header = msg.header
        for b, c, s in zip(boxes, ids, scores):
            d, iqr, n = box_disparity(L, R, b)
            z = self.fxB / d if d and d > 0.5 else float('nan')
            name = COCO[int(c)]
            t = Target()
            t.type = name
            roi = Roi()
            roi.type = f'{name} {z:.2f}m' if np.isfinite(z) else f'{name} ?m'
            roi.rect.x_offset, roi.rect.y_offset = int(b[0]), int(b[1])
            roi.rect.width, roi.rect.height = int(b[2] - b[0]), int(b[3] - b[1])
            roi.confidence = float(s)
            t.rois.append(roi)
            for k, v in (('distance_m', z), ('disparity_px', d or 0.0), ('disparity_iqr_px', iqr or 0.0), ('patches', n)):
                at = Attribute()
                at.type, at.value = k, float(v)
                t.attributes.append(at)
            out.targets.append(t)
        self.pub.publish(out)
        t3 = time.perf_counter()
        age = (self.get_clock().now().nanoseconds - (msg.header.stamp.sec * 10**9 + msg.header.stamp.nanosec)) / 1e6
        p = {'unpack_ms': 1e3 * (t1 - t0), 'yolo_ms': 1e3 * (t2 - t1), 'stereo_ms': 1e3 * (t3 - t2),
             'total_ms': 1e3 * (t3 - t0), 'age_ms': age, 'n': len(boxes)}
        self.pub_perf.publish(String(data=json.dumps({k: round(v, 2) for k, v in p.items()})))
        self.acc.append(p)
        if len(self.acc) == 30:   # one summary line per 30 frames
            dt = time.perf_counter() - self.t_acc
            mean = {k: np.mean([a[k] for a in self.acc]) for k in p}
            self.get_logger().info(f"{30 / dt:.1f} fps | yolo {mean['yolo_ms']:.1f} ms, stereo {mean['stereo_ms']:.1f} ms, "
                                   f"total {mean['total_ms']:.1f} ms, frame age {mean['age_ms']:.0f} ms, objects {mean['n']:.1f} | "
                                   + ', '.join(f'{r.type}' for t in out.targets for r in t.rois))
            self.acc, self.t_acc = [], time.perf_counter()


def main():
    rclpy.init()
    rclpy.spin(StereoYolo())


if __name__ == '__main__':
    main()
