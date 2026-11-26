# Stage 2 Proposal: Stereo HIL, an RDK X5 that drives a simulated car and is scored against ground truth

## The problem

Testing a robot's perception on real roads is slow, unsafe and gives no ground truth: when a stereo camera says a
pedestrian is 7.4 m away, nobody knows the true distance. Most RDK X5 projects therefore show boxes on a screen and never
measure whether the depth or the braking decision was right.

## Where the project stands

| ✅ Built and checked today | 🔨 Planned for Stage 3 |
|---|---|
| Stage 1 node on the board, **real camera**: YOLO11m on the BPU + distance per box | `hil_input`: feed simulator images to that node on the board |
| Two simulator worlds with traffic; a pedestrian crossing in the city test | StereoNet on the BPU as the second workload |
| `ros_bridge`: stereo out, drive commands in, **full brake after 0.5 s of silence** | Planner and safety nodes (adaptive cruise, emergency brake, e-stop) |
| Pixel-exact depth ground truth and a depth checker (6 injected faults caught, 2 good inputs pass) | Scenario scorer (stopping gap, collisions), speed-up to 10 Hz |
| Humble ↔ Jazzy messaging, tested from a Humble container | The first run with the **board in the loop** |

## The concept

The RDK X5 **will run** its real perception and control stack on its own BPU and CPU, with a simulated stereo camera as
its eyes. A laptop runs Webots with SUMO traffic and will send the board a rendered stereo pair (80 mm baseline and
96.8° horizontal field of view, an idealised pinhole model of the GS130W). The board will send back speed and brake
commands; lane keeping is a stretch goal. Because the simulator knows the exact depth of every pixel
and the exact position of every car and pedestrian, **each decision the board makes can be scored automatically**: depth
error by range, stopping gap, collisions, latency.

The real GS130W stays in the loop for **real-world accuracy runs** (tape measure on 60 cm floor tiles), so the project
measures both sim-to-board and real-world performance with the same code.

## Why test this way

Testing braking against a person can't be done safely with a real person, repeated exactly, or checked against a true
distance on a road. In a simulator it can: the same crossing can be run again and again, and the true distance of every
pixel is known. Hardware-in-the-loop is the step between a desktop simulation and a vehicle: the **software and the
compute are the real ones**, only the world is simulated.

| This test bench can show | It cannot show |
|---|---|
| Whether the board sees the hazard in time, on its own BPU and CPU | That the system is safe on real roads |
| Depth error by distance, stopping gap, latency, dropped frames | Behaviour with real glare, rain, dirt, lens blur or motion blur |
| Whether a software change made things better or worse (repeatable runs) | How a real car's brakes and tyres respond |

So this is a **perception and braking test bench**, not a self-driving car. The real GS130W tape-measure runs stay in
the project to keep the simulator results honest.

## The test scene, and the problem to solve

Left camera frames from the city world, 640x352. There's **no perception or planner in the loop yet**: a scripted test
controller drives straight at 10 km/h, so it goes through the pedestrian. Stage 3 has to make the board stop.

![Three frames: pedestrians approach a crossing, the car gets close, the car drives into a pedestrian](../images/11_sim_crossing_no_brain.jpg)

What only a simulator can give: the exact depth of every pixel (right), used for scoring and never sent to the board.

![Left camera view beside its ground-truth depth image](../images/12_sim_view_and_ground_truth.jpg)

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
| Closed loop | Detection only | Planned: the board **controls the speed** of a car in traffic, with brake and follow decisions scored |
| Prior HIL on RDK X5 | GaussianRPG v2.0 (Feb 2025): mono camera over HDMI capture, brake only, replayed scenes, no depth | **Stereo**, live SUMO traffic, **depth ground truth**, a depth scoring tool (built); speed control planned |
| Fault finding | — | `check_depth.py` names the fault (scale, offset, units, missing pixels, shifted image grid, range instead of planar Z): 6 injected faults caught |

## Decision logic (planned)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../figures/decision_flow_dark.svg">
  <img src="../figures/decision_flow_light.svg" alt="Planned decision flow: e-stop, stale perception, time to collision, object in lane, else cruise">
</picture>

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
