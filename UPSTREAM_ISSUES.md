# Problems found in the stock D-Robotics stack (candidates for upstream issues / PRs)

Board: RDK X5 4 GB, RDK OS 3.5.0, tros-humble 2.5.2, mipi_cam from tros-humble, hobot-sp-samples on the image,
camera: RDK Stereo Camera GS130W. Found 2026-11-25/26. Each entry: what, evidence, suggested fix, status.

## 1. `dequantize_tensor` skips SCALE-quantized outputs (wrong YOLOv8 boxes)
- **Upstream PR:** https://github.com/D-Robotics/x5-hobot-sp-samples/pull/21
- Where: `/app/pydev_demo/utils/postprocess_utils.py` (package `hobot-sp-samples`), `dequantize_tensor`.
- What: `if quant_info.quant_type != 1: return q_tensor`. `hbm_runtime` reports scale quantization as
  `hbDNNQuantiType.SCALE == 2`, so int32 outputs are returned raw.
- Evidence: `/app/pydev_demo/models/yolov8_640x640_nv12.bin` box heads `318/334/350` are int32, `quant_type 2`,
  per-channel `scale` (64,) along axis 3, no zero point. The raw ints go straight into the DFL softmax.
  Unit test in `tests/test_stereo_geom.py` shows the decoded box differs with vs without the scale.
- Fix: compare against the enum (`hbDNNQuantiType.SCALE`) and handle an empty `zero_point`.
- Status: worked around in `stereo_geom.decode_yolov8_level`.
- Upstream: `D-Robotics/x5-hobot-sp-samples`, `debian/app/pydev_demo/utils/postprocess_utils.py` line 186, still present on `main` (checked 2026-11-26).
  `D-Robotics/rdk_model_zoo` `utils/py_utils/quantization.py` already compares by name (`"SCALE"`), so that is the reference fix.

## 2. Sample letterbox is slow (25 ms per frame on X5)
- Where: same samples, `preprocess_utils.resized_image` + `bgr_to_nv12_planes` path (BGR round trip).
- Evidence: 25.5 ms for 1280x1088 on the board. A direct NV12 letterbox with strided 2x copy into a reused
  buffer takes ~1 ms (`stereo_geom.letterbox_nv12`).
- Fix: offer an NV12-in letterbox for camera frames.

## 3. YOLO samples set the NMS IoU threshold from the score threshold (5 samples)
- **Upstream PR:** https://github.com/D-Robotics/x5-hobot-sp-samples/pull/22
- Where: `/app/pydev_demo/02_detection_sample/03_ultralytics_yolov8/ultralytics_yolov8.py`,
  `self.nms_thresh = opt.score_thres` while a separate `--nms-thres` argument exists and is unused.
- Fix: `self.nms_thresh = opt.nms_thres`. (Not yet tested on the board.)
- Upstream: `D-Robotics/x5-hobot-sp-samples`, `debian/app/pydev_demo/02_detection_sample/03_ultralytics_yolov8/ultralytics_yolov8.py` line 69, still on `main`.

## 4. Default `mipi_rotation` with the GS130W gives vertical disparity and rotated camera_info
- **Upstream issue:** https://github.com/D-Robotics/hobot_mipi_cam/issues/115
- Where: `hobot_mipi_cam`, `hobot_mipi_cap.cpp`: output turn = `rotation - cal_rotate`; the GS130W EEPROM
  stores angle 1 (90 deg), launch default `mipi_rotation 0.0`, so output is turned 270 deg.
- Evidence: default launch: left/right shifted vertically (patch match dy ~55 px, dx 0), camera_info K/R/P look
  scrambled (rotated frame, R holds a GDC homography). With `mipi_rotation:=90.0`: clean 1280x1088
  camera_info, f 501.797, P[3] = -40153.5 (B 80.02 mm), horizontal disparity, rows aligned (|dy|<=1 px 83%).
  The websocket preview with defaults also looks sideways.
- Fix: default the dual-channel launch to the EEPROM angle (rotation = cal_rotate) or document it for GS130W.
- Upstream: `D-Robotics/hobot_mipi_cam` (default branch `develop`, active: PRs #112-114 merged recently). Behaviour change, so open an issue first.

## 5. `camera_info` header frame_id `default_cam` for both eyes, distortion_model empty
- Evidence: `/image_combine_raw/{left,right}/camera_info` both `frame_id: default_cam`, `distortion_model: ''`,
  `d` all zeros (fine for rectified output but the model should then be `plumb_bob` with zeros).
- Fix: per-eye frame ids, set distortion_model.

## 6. A second `mipi_cam` launch while one runs fails with an unclear error
- Evidence: `create_and_run_vflow(1590) failed, ret -217` then `rcl node's context is invalid`,
  and with another holder: `There are no available host.` No hint that the camera is busy.
- Fix: detect the busy device and print "camera already in use by PID ...".

## 7. hobot_shm env is required to receive the 4 MB stereo frames; failure is silent
- Evidence: a Python subscriber started outside the launch (no `FASTRTPS_DEFAULT_PROFILES_FILE`
  /`RMW_FASTRTPS_USE_QOS_FROM_XML`), or a BEST_EFFORT one, received no `/image_combine_raw` frames and no error.
- Fix: document in mipi_cam README; warn on QoS/transport mismatch.

## 8. Websocket viewer floods "cache image num > 100" when no AI messages match
- Evidence: `websocket_only_show_image False` before the AI publisher matches: two WARN lines per frame.
- Fix: rate-limit the warning.

## 9. GS130W docs / board docs inconsistencies
- RDK X5 standard board has no IO voltage selector (docs "None.") but some notes imply one; GS130W FFC
  orientation (camera side contacts away from PCB, board side toward Ethernet) is only in accessory docs,
  the generic X5 doc says "away from the black latch". Our first attempt with the generic rule gave
  `i2c_designware 341d0000.i2c: controller timed out` on bus 6 and no sensor; fixed after reseating per the
  GS130W rule (sensors at 0x33 bus 6, 0x32 bus 4).
- Fix: link the GS130W orientation from the X5 hardware page; i2c timeout troubleshooting note.

## 10. Model build / runtime version warning on the shipped yolov8n
- Evidence: `Inconsistency between the hbrt library version 3.15.55.0 and the model build version 3.15.49.0`.
- Fix: rebuild shipped models with the current OpenExplorer.

## Not bugs, but useful data for the docs
- `rdkos_info` without sudo prints "Permission denied" for cpufreq lines.
- Python small-op overhead on loaded A55 cores: `matchTemplate` 15x15 vs 15x275 ~1.3 ms, `ndarray.std` on
  225 px ~0.7 ms (load ~4.7 with camera + jpeg + websocket + node).

## Our own limits (for the README, not upstream)
- Transparent objects: background through the object gives wrong/low NCC; mitigated with more patches + NCC 0.75.
- Python pipeline ~5-7 fps with YOLO11m (yolo ~73 ms incl. pre/post, stereo ~80 ms for one box under load);
  next step a C++ node on hobot zero-copy (hbmem) messages.
