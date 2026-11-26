# Roadmap

| Status | Dates | Milestone | Done when |
|---|---|---|---|
| ✅ | Nov 24–26 | **Stage 1:** flash, GS130W bring-up, YOLO11m on the BPU + per-box stereo distance | +1.5 % at 60 cm; repo, Discord post, showcase PR #20 |
| ✅ | Nov 25 | HIL base: Webots + SUMO worlds, ros_bridge, Humble↔Jazzy check, pixel-exact depth ground truth, `check_depth.py` | Depth checker self-test (8 cases) + geometry check pass in both worlds; bridge test PASS |
| ✅ | Nov 26 | Upstream: 2 PRs (`x5-hobot-sp-samples` #21, #22), 1 issue (`hobot_mipi_cam` #115) | Opened |
| ✅ | Nov 26 | **Stage 2:** proposal, architecture, engineering plan, roadmap | This document set |
| ⬜ | Nov 27–Dec 2 | `hil_input`; stereo_yolo on sim frames; Ethernet link; StereoNet input test; first scored depth run | Depth report per range bin (T1) |
| ⬜ | **Dec 3** | **Mid-Point Showcase** (14:00 UTC) | Board perceives the sim, depth scored live |
| ⬜ | Dec 3–6 | Planner (nearest object in lane, ACC, emergency brake) + safety node | Car stops for the zebra-crossing pedestrians |
| ⬜ | Dec 6–9 | Performance: C++ port / zero-copy, StereoNet + YOLO concurrently | T3, T4, T7 |
| ⬜ | Dec 9–11 | Scenario runs ×10 (crossing, cut-in, following); real-world table at 1.2 / 1.8 / 2.4 m | T2, T5, T6 |
| ⬜ | Dec 12–15 | Final 72 h: benchmark table, 3–7 min demo video, Quick Start, final post and PR | Stage 3 package submitted |
