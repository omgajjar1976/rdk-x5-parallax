# Stage 2 Engineering Plan

## Bill of materials

| # | Item | Qty | Supplier / SKU | Voltage / interface | Status |
|---|---|---|---|---|---|
| 1 | RDK X5, 4 GB | 1 | D-Robotics (challenge kit) | 5 V / 5 A USB-C; Wi-Fi 6, GbE | In hand |
| 2 | RDK Stereo Camera GS130W | 1 | D-Robotics (challenge kit) | 2x 22-pin MIPI CSI-2, IO 3.3 V | In hand |
| 3 | 22-pin FFC, ~100 mm | 2 | Included with GS130W | Same-side contacts | In hand |
| 4 | microSD, 256 GB | 1 | Own | — | In hand, RDK OS 3.5.0 |
| 5 | USB-C power adapter 5 V / 5 A | 1 | Own | 25 W | In hand |
| 6 | Micro-USB cable (debug serial, 115200) | 1 | Own | CH340 | In hand |
| 7 | Cat6 Ethernet cable, 2 m | 1 | Local | GbE, direct to laptop (risk 1) | To buy |
| 8 | 3D-printed camera stand | 1 | Own design (PLA) | Tilt pivot, M3/M4 | Printed |
| 9 | Laptop | 1 | Own: Intel Core 5 210H, 16 GB, RTX 4050 | Ubuntu 24.04, ROS 2 Jazzy, Webots R2025a, SUMO 1.18 | In hand |

No physical actuators: the actuator is the simulated car (decided for Stage 3).

## Schedule

See [ROADMAP.md](../../ROADMAP.md). Milestones: **Dec 3** Mid-Point Showcase (board perceives the sim, depth scored);
**Dec 9** closed loop (braking and following scored); **Dec 12–15** final package.

## Top five risks

| # | Risk | Trigger (how we notice) | Mitigation | Fallback |
|---|---|---|---|---|
| 1 | Wi-Fi can't carry the stereo stream (640x352 bgr8 x2 at 14 Hz ≈ 150 Mbit/s) | Board receives < 10 Hz, or frame age > 150 ms | Direct Ethernet cable; send NV12 instead of bgr8 (half the bytes) | JPEG per eye with the board's hardware decoder; 7 Hz |
| 2 | Python pipeline too slow (5–6 fps today) | `/stereo_yolo/perf` total > 100 ms | C++ node on zero-copy `hbmem` messages; per-box stereo in C++ | YOLOv8n (12 ms on the BPU) for the closed loop; YOLO11m only for scoring runs |
| 3 | StereoNet can't take ROS-topic stereo input in the needed format | No depth from a sim pair in the first test (week 1) | Read the `hobot_stereonet` source and docs (offline/local input exists) | Per-box stereo as the only depth; 2nd BPU workload = YOLO on the right image |
| 4 | YOLO misses rendered objects (sim-to-real gap) | Detection recall < 80 % on sim frames with ground-truth boxes | Lower threshold, test both worlds; check frames | Use the scorer to report it; StereoNet obstacle in lane as the braking trigger |
| 5 | Humble ↔ Jazzy DDS issue under load | Dropped messages or the open CycloneDDS warning turning into data loss | Same CycloneDDS config on both, pinned interface; already tested from a Humble container | Run the bridge in the tested Humble container on the laptop |

## Repository structure (target for Stage 3)

```text
rdk-x5-stereo-yolo/
├── src/
│   ├── stereo_yolo/        # Stage 1 node (YOLO on BPU + per-box stereo), later the C++ port
│   ├── hil_input/          # sim stereo -> NV12 /image_combine_raw
│   ├── hil_planner/        # nearest object in lane, ACC + emergency brake
│   └── hil_safety/         # e-stop latch, heartbeat, command clamps
├── sim/                    # Webots world builders, ros_bridge controller, SUMO routes (from ~/rdk_x5/hil)
├── launch/                 # board.launch.py, laptop_sim.launch.py
├── config/                 # thresholds, time gap, limits (YAML)
├── models/                 # README with model names and paths (models stay on the board image)
├── tools/                  # check_depth.py, scenario scorer, make_figures.py, deploy.sh
├── tests/                  # unit tests + bridge/interop tests
└── docs/                   # stage2/, figures/, images/, results/
```

Today the repo holds the Stage 1 node at the top level; it moves into `src/stereo_yolo/` in the first Stage 3 week.
Code reaches the board by `deploy.sh` (committed tree only, no `.git` on the board).
