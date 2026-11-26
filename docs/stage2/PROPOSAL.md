# Stage 2 Proposal: Stereo HIL, an RDK X5 that drives a simulated car and is scored against ground truth

## The problem

Testing a robot's perception on real roads is slow, unsafe and gives no ground truth: when a stereo camera says a
pedestrian is 7.4 m away, nobody knows the true distance. Most RDK X5 projects therefore show boxes on a screen and never
measure whether the depth or the braking decision was right.

## The concept

The RDK X5 runs its **real perception and control stack on its own BPU and CPU**, but its eyes are a simulated stereo
camera. A laptop runs Webots with SUMO traffic and sends the board a rendered stereo pair (same baseline and field of
view as the GS130W). The board sends back steering and speed. Because the simulator knows the exact depth of every pixel
and the exact position of every car and pedestrian, **every decision the board makes is scored automatically**: depth
error by range, stopping gap, collisions, latency.

The real GS130W stays in the loop for **real-world accuracy runs** (tape measure on 60 cm floor tiles), so the project
measures both sim-to-board and real-world performance with the same code.

## Users and interaction

| User | What they get |
|---|---|
| RDK developers and students | A safe test bench: run your own depth or detection node on the board and get a scored report, no car needed |
| Me (this challenge) | An ADAS-style stack (adaptive cruise + emergency braking) that is measured, not just demoed |
| D-Robotics ecosystem | A reproducible way to check StereoNet / YOLO accuracy on RDK hardware (see the open GS130W depth issues on the forum) |

Interaction: launch the sim on the laptop, launch the stack on the board, watch the car drive in Webots and the
board's view in the browser. A run ends with a report (`report.txt` + plots).

## Capabilities

| | What | Where |
|---|---|---|
| **Perception** | YOLO11m detection on the BPU; per-box stereo distance (Stage 1 node); StereoNet dense depth on the BPU | RDK X5 |
| **Decision** | Pick the nearest object in the ego lane; adaptive cruise (time gap) and emergency brake (time to collision) | RDK X5 CPU |
| **Actuation** | `ackermann_msgs/AckermannDriveStamped` to the simulated car, 15 Hz; speed ≤ 30 km/h, steer ≤ 0.5 rad | Sim car |
| **Safety** | Bridge watchdog: no command for 0.5 s → full brake (built and tested). Board e-stop topic, planner sanity limits | Both |
| **Scoring** | Depth vs pixel-exact ground truth (`check_depth.py`, built and self-tested); scenario scorer for stopping gap and collisions | Laptop |

## Innovation compared with a stock demo

| | Stock demo / prior art | This project |
|---|---|---|
| Stereo on RDK X5 | Depth image shown, accuracy unknown | Depth **scored per range bin** against exact sim ground truth, and against a tape in the real world |
| Closed loop | Detection only | Board **drives** a car in traffic; brake and follow decisions are scored |
| Prior HIL on RDK X5 | GaussianRPG v2.0 (Feb 2025): mono camera over HDMI capture, brake only, replayed scenes, no depth | **Stereo**, live SUMO traffic, steering + speed, **depth ground truth**, scoring tools |
| Fault finding | — | `check_depth.py` names the fault (wrong baseline/focal, cx offset, units, range vs planar Z, row shift) with 8 self-tested fault types |

## Measurable success targets (Stage 3)

| # | Metric | Target | Baseline today |
|---|---|---|---|
| T1 | Depth error in sim, AbsRel vs ground truth | ≤ 3 % at 2–5 m, ≤ 8 % at 5–10 m | Checker built; board not run on sim yet |
| T2 | Real-world distance error (tape, floor tiles) | ≤ 3 % to 1.2 m, ≤ 6 % to 2.4 m | +1.5 % at 0.6 m (measured) |
| T3 | Perception rate on the board for the sim stream | ≥ 10 Hz | 5–6 fps (Python, real camera) |
| T4 | Image-to-command latency (p95) | ≤ 150 ms | Frame age 224–236 ms today |
| T5 | Emergency brake for a crossing pedestrian | 10/10 runs stop with ≥ 2 m gap, 0 collisions | Scenario built (2 pedestrians on a zebra crossing) |
| T6 | Car following (adaptive cruise) | Time gap within ±20 % of 2.0 s after settling | — |
| T7 | Two concurrent BPU workloads | YOLO11m + StereoNet both ≥ 10 Hz | YOLO11m 40.5 ms alone (BPU) |

Stretch: lane keeping from the board's own perception (lateral control is fixed to the route until then).
