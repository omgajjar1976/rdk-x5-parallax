#!/usr/bin/env python3
"""Regenerate the README figures (light + dark): python3 tools/make_figures.py

Numbers are the measured values from the README tables; edit DATA below, not the PNGs.
"""
import os
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), '..', 'docs', 'figures')
# validated palette (dataviz reference): slot 1 blue, slot 2 orange; light / dark steps
THEME = {
    'light': dict(bg='#ffffff', ink='#191919', ink2='#666666', grid='#e7e7e7', axis='#c2c2c2',
                  s1='#257de0', s2='#f47230', box='#f6f8fa', edge='#8c959f', hi='#257de0'),
    'dark': dict(bg='#0d1117', ink='#efefef', ink2='#9c9c9c', grid='#303030', axis='#474747',
                 s1='#338ced', s2='#e76624', box='#161b22', edge='#6e7681', hi='#338ced'),
}

# ---- data (measured on the board, see README) ----
ACCURACY = [  # label, true cm, measured low cm, measured high cm
    ('Transparent bottle', 30, 30.0, 31.5),
    ('Coca-Cola bottle', 60, 59.0, 62.0),
    ('Cup', 60, 60.4, 60.4),
    ('RDK X5 box', 60, 60.9, 60.9),
]
BPU = [('YOLOv8n', 12.1), ('YOLOv12n', 27.6), ('YOLOv5s v7', 33.2), ('YOLO11m (used)', 40.5), ('YOLOv10', 52.2)]
SPEEDUP = [  # step, first version ms, now ms (both measured live on the board)
    ('YOLOv8n step incl. pre/post', 62.6, 33.0),
    ('Stereo, one tall box', 890.0, 80.0),
]


def style(ax, t):
    ax.set_facecolor(t['bg'])
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color(t['axis'])
    ax.tick_params(colors=t['ink2'], labelsize=10, length=0)
    ax.xaxis.grid(True, color=t['grid'], linewidth=0.8)
    ax.set_axisbelow(True)


def save(fig, name, mode):
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, f'{name}_{mode}.png'), dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def accuracy(mode):
    t = THEME[mode]
    fig, ax = plt.subplots(figsize=(8, 3.5), facecolor=t['bg'])
    style(ax, t)
    for i, (lab, true, lo, hi) in enumerate(ACCURACY):
        ax.plot([true], [i], marker='|', markersize=22, markeredgewidth=2.5, color=t['ink'], zorder=3)
        if lo == hi:
            ax.plot([lo], [i], marker='o', markersize=10, color=t['s1'], markeredgecolor=t['bg'], markeredgewidth=2, zorder=4)
        else:
            ax.plot([lo, hi], [i, i], color=t['s1'], linewidth=7, solid_capstyle='round', zorder=4)
        txt = f'{lo:.1f} cm' if lo == hi else f'{lo:.1f}-{hi:.1f} cm'
        ax.text(max(hi, true) + 1.2, i, f'{txt}  (true {true} cm)', va='center', fontsize=10, color=t['ink'])
    ax.set_yticks(range(len(ACCURACY)))
    ax.set_yticklabels([a[0] for a in ACCURACY], color=t['ink'], fontsize=10)
    ax.set_xlim(25, 80)
    ax.set_xlabel('distance (cm)', color=t['ink2'], fontsize=10)
    ax.set_title('Stereo distance vs tape measure', loc='left', color=t['ink'], fontsize=12, fontweight='bold', pad=34)
    ax.plot([], [], marker='o', linestyle='none', markersize=8, color=t['s1'], label='measured on the RDK X5 (dot = one value, bar = range)')
    ax.plot([], [], marker='|', linestyle='none', markersize=14, markeredgewidth=2.5, color=t['ink'], label='tape measure')
    leg = ax.legend(loc='lower left', bbox_to_anchor=(0, 1.02), ncol=2, frameon=False, fontsize=9, borderaxespad=0)
    for tx in leg.get_texts():
        tx.set_color(t['ink2'])
    fig.tight_layout()
    save(fig, 'accuracy', mode)


def bpu(mode):
    t = THEME[mode]
    fig, ax = plt.subplots(figsize=(8, 3.0), facecolor=t['bg'])
    style(ax, t)
    names = [b[0] for b in BPU][::-1]
    vals = [b[1] for b in BPU][::-1]
    ax.barh(names, vals, color=t['s1'], height=0.55, zorder=3)
    for i, v in enumerate(vals):
        ax.text(v + 0.8, i, f'{v:.1f} ms  ({1000 / v:.0f} FPS)', va='center', fontsize=10, color=t['ink'])
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, color=t['ink'], fontsize=10)
    ax.set_xlim(0, 68)
    ax.set_xlabel('BPU latency per frame, 640x640, 1 thread (ms, lower is better)', color=t['ink2'], fontsize=10)
    ax.set_title('YOLO models on the RDK X5 BPU (hrt_model_exec)', loc='left', color=t['ink'], fontsize=12, fontweight='bold')
    fig.tight_layout()
    save(fig, 'bpu', mode)


def speedup(mode):
    t = THEME[mode]
    fig, ax = plt.subplots(figsize=(8, 3.3), facecolor=t['bg'])
    style(ax, t)
    ax.set_xscale('log')
    y = range(len(SPEEDUP))
    h = 0.34
    for i, (lab, stock, ours) in enumerate(SPEEDUP[::-1]):
        ax.barh(i + h / 2 + 0.02, stock, height=h, color=t['s2'], zorder=3)
        ax.barh(i - h / 2 - 0.02, ours, height=h, color=t['s1'], zorder=3)
        ax.text(stock * 1.12, i + h / 2 + 0.02, f'{stock:g} ms', va='center', fontsize=9, color=t['ink'])
        ax.text(ours * 1.12, i - h / 2 - 0.02, f'{ours:g} ms  ({stock / ours:.0f}x faster)', va='center', fontsize=9, color=t['ink'])
    ax.set_yticks(list(y))
    ax.set_yticklabels([s[0] for s in SPEEDUP][::-1], color=t['ink'], fontsize=10)
    ax.set_xlim(1, 6000)
    ax.set_xlabel('time per frame, log scale (ms)', color=t['ink2'], fontsize=10)
    ax.set_title('Before vs after optimising, measured live on the board', loc='left', color=t['ink'], fontsize=12, fontweight='bold', pad=34)
    from matplotlib.patches import Patch
    from matplotlib.ticker import FixedLocator, FixedFormatter, NullLocator
    ax.xaxis.set_major_locator(FixedLocator([1, 10, 100, 1000]))
    ax.xaxis.set_major_formatter(FixedFormatter(['1', '10', '100', '1000']))
    ax.xaxis.set_minor_locator(NullLocator())
    leg = ax.legend(handles=[Patch(color=t['s2'], label='first version (stock helpers, dense grid)'), Patch(color=t['s1'], label='this repo')],
                    loc='lower left', bbox_to_anchor=(0, 1.02), ncol=2, frameon=False, fontsize=9, borderaxespad=0)
    for tx in leg.get_texts():
        tx.set_color(t['ink2'])
    fig.tight_layout()
    save(fig, 'speedup', mode)


def architecture(mode):
    """Hand-placed SVG: readable labels, no overlapping edge text."""
    t = THEME[mode]
    W, H = 1200, 430
    boxes = {  # name: x, y, w, h, title, subtitle, highlight
        'cam': (16, 190, 180, 104, 'GS130W', 'stereo camera', False),
        'mipi': (262, 190, 190, 104, 'mipi_cam', 'GDC rectify', False),
        'codec': (690, 24, 210, 92, 'hobot_codec', 'JPEG encode', False),
        'node': (690, 176, 250, 140, 'stereo_yolo_node', 'YOLO11m on BPU', True),
        'web': (1004, 24, 182, 92, 'websocket', 'browser :8000', False),
        'perf': (1004, 300, 182, 92, 'perf topic', 'stage timings', False),
    }
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">',
           f'<rect width="{W}" height="{H}" rx="14" fill="{t["bg"]}"/>',
           f'<defs><marker id="a" markerUnits="userSpaceOnUse" markerWidth="11" markerHeight="10" refX="10" refY="5" orient="auto">'
           f'<path d="M0,0 L11,5 L0,10 z" fill="{t["edge"]}"/></marker></defs>']

    def edge(points, label, lx, ly, anchor='middle'):
        d = 'M' + ' L'.join(f'{x},{y}' for x, y in points)
        out.append(f'<path d="{d}" fill="none" stroke="{t["edge"]}" stroke-width="2.5" marker-end="url(#a)"/>')
        if label:
            out.append(f'<text x="{lx}" y="{ly}" font-size="17" fill="{t["ink2"]}" text-anchor="{anchor}">{label}</text>')

    edge([(196, 242), (258, 242)], 'MIPI', 227, 230)
    edge([(452, 226), (686, 226)], 'stereo pair (rectified)', 569, 214)
    edge([(452, 270), (686, 270)], 'focal length, baseline', 569, 298)
    edge([(400, 190), (400, 70), (686, 70)], 'stereo pair', 543, 58)
    edge([(900, 70), (1000, 70)], 'JPEG', 950, 58)
    edge([(940, 220), (970, 220), (970, 100), (1000, 100)], '', 0, 0)
    out.append(f'<text x="978" y="168" font-size="17" fill="{t["ink2"]}">boxes +</text>')
    out.append(f'<text x="978" y="190" font-size="17" fill="{t["ink2"]}">metres</text>')
    edge([(940, 280), (970, 280), (970, 346), (1000, 346)], '', 0, 0)
    for x, y, w, h, title, sub, hi in boxes.values():
        stroke = t['hi'] if hi else t['edge']
        sw = 3.5 if hi else 2
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{t["box"]}" stroke="{stroke}" stroke-width="{sw}"/>')
        out.append(f'<text x="{x + w / 2}" y="{y + h / 2 - 6}" font-size="22" font-weight="600" fill="{t["ink"]}" text-anchor="middle">{title}</text>')
        out.append(f'<text x="{x + w / 2}" y="{y + h / 2 + 22}" font-size="17" fill="{t["ink2"]}" text-anchor="middle">{sub}</text>')
        if hi:
            out.append(f'<text x="{x + w / 2}" y="{y + h - 14}" font-size="16" font-weight="700" fill="{t["hi"]}" text-anchor="middle">+ stereo distance (this repo)</text>')
    out.append(f'<text x="16" y="414" font-size="17" fill="{t["ink2"]}">Everything runs on the RDK X5; only the browser is on the laptop.</text>')
    out.append('</svg>')
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, f'architecture_{mode}.svg'), 'w').write('\n'.join(out))


def hil_architecture(mode):
    """Stage 2/3 hardware-in-the-loop data flow: laptop sim <-> RDK X5."""
    t = THEME[mode]
    W, H = 1200, 620
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">',
           f'<rect width="{W}" height="{H}" rx="14" fill="{t["bg"]}"/>',
           f'<defs><marker id="a" markerUnits="userSpaceOnUse" markerWidth="11" markerHeight="10" refX="10" refY="5" orient="auto">'
           f'<path d="M0,0 L11,5 L0,10 z" fill="{t["edge"]}"/></marker></defs>']
    for x, w, label in ((12, 364, 'LAPTOP  (ROS 2 Jazzy)'), (448, 740, 'RDK X5  (ROS 2 Humble / TROS)')):
        out.append(f'<rect x="{x}" y="12" width="{w}" height="{H - 24}" rx="14" fill="none" stroke="{t["axis"]}" stroke-width="2" stroke-dasharray="8 6"/>')
        out.append(f'<text x="{x + 18}" y="42" font-size="18" font-weight="700" fill="{t["ink2"]}">{label}</text>')
    dash = ' stroke-dasharray="9 6"'

    def box(x, y, w, h, title, sub, hi=False, built=True):
        stroke = t['hi'] if hi else t['edge']
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{t["box"]}" stroke="{stroke}" stroke-width="{3.5 if hi else 2}"{"" if built else dash}/>')
        out.append(f'<text x="{x + w / 2}" y="{y + h / 2 - 4}" font-size="20" font-weight="600" fill="{t["ink"]}" text-anchor="middle">{title}</text>')
        out.append(f'<text x="{x + w / 2}" y="{y + h / 2 + 22}" font-size="15" fill="{t["ink2"]}" text-anchor="middle">{sub}</text>')

    def text(x, y, label, anchor='middle'):
        out.append(f'<text x="{x}" y="{y}" font-size="16" fill="{t["ink2"]}" text-anchor="{anchor}">{label}</text>')

    def edge(points):
        d = 'M' + ' L'.join(f'{x},{y}' for x, y in points)
        out.append(f'<path d="{d}" fill="none" stroke="{t["edge"]}" stroke-width="2.5" marker-end="url(#a)"/>')

    box(32, 112, 324, 90, 'Webots + SUMO world', 'city / SF, traffic, pedestrians')
    box(32, 246, 324, 100, 'ros_bridge', 'stereo 640x352, 14 Hz, watchdog')
    box(32, 484, 324, 90, 'Scorer (ground truth)', 'depth check built; scenarios next')
    box(498, 260, 160, 92, 'hil_input', 'to NV12', built=False)
    box(708, 140, 272, 92, 'stereo_yolo', 'YOLO11m on BPU + distance', hi=True)
    box(708, 380, 272, 92, 'StereoNet', 'dense depth on BPU', built=False)
    box(1030, 260, 146, 92, 'planner', '+ safety', hi=True, built=False)

    edge([(194, 202), (194, 246)])                                   # world -> bridge
    edge([(356, 320), (498, 320)]); text(412, 342, 'stereo'); text(412, 362, 'pair')
    edge([(658, 290), (683, 290), (683, 186), (708, 186)])           # hil_input fan-out
    edge([(658, 322), (683, 322), (683, 426), (708, 426)])
    edge([(980, 186), (1005, 186), (1005, 290), (1030, 290)])        # fan-in to planner
    edge([(980, 426), (1005, 426), (1005, 322), (1030, 322)])
    text(1014, 178, 'boxes + metres', 'start'); text(1014, 448, 'depth', 'start')
    edge([(1150, 260), (1150, 74), (412, 74), (412, 272), (356, 272)])  # command returns over the top
    text(757, 98, 'cmd_drive (Ackermann, 15 Hz)')
    edge([(194, 346), (194, 484)]); text(206, 411, 'ground truth:', 'start'); text(206, 432, 'depth + odom', 'start')
    edge([(844, 472), (844, 529), (356, 529)]); text(600, 519, 'board depth')
    out.append(f'<text x="466" y="586" font-size="15" fill="{t["ink2"]}">Dashed = planned. Ground truth never reaches the board.</text>')
    out.append('</svg>')
    open(os.path.join(OUT, f'hil_architecture_{mode}.svg'), 'w').write('\n'.join(out))


def decision_flow(mode):
    """Planned planner + safety logic, evaluated every control cycle."""
    t = THEME[mode]
    W, H = 1000, 760
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">',
           f'<rect width="{W}" height="{H}" rx="14" fill="{t["bg"]}"/>',
           f'<defs><marker id="a" markerUnits="userSpaceOnUse" markerWidth="11" markerHeight="10" refX="10" refY="5" orient="auto">'
           f'<path d="M0,0 L11,5 L0,10 z" fill="{t["edge"]}"/></marker></defs>']

    def text(x, y, s, size=19, color=None, weight=400, anchor='middle'):
        out.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color or t["ink"]}" text-anchor="{anchor}">{s}</text>')

    def rect(y, label, x=60, w=420, stroke=None, rx=12):
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="62" rx="{rx}" fill="{t["box"]}" stroke="{stroke or t["edge"]}" stroke-width="2.5"/>')
        text(x + w / 2, y + 38, label, weight=600)

    def diamond(cy, label):
        out.append(f'<path d="M270,{cy - 46} L500,{cy} L270,{cy + 46} L40,{cy} z" fill="{t["box"]}" stroke="{t["hi"]}" stroke-width="2.5"/>')
        text(270, cy + 7, label, size=18, weight=600)

    def edge(x1, y1, x2, y2, label='', lx=0, ly=0):
        out.append(f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{t["edge"]}" stroke-width="2.5" fill="none" marker-end="url(#a)"/>')
        if label:
            text(lx, ly, label, size=16, color=t['ink2'])

    rect(24, 'New control cycle (15 Hz)', rx=31)
    steps = [(160, 'E-stop pressed?', 'FULL BRAKE, stay latched'),
             (282, 'No perception for 0.3 s?', 'BRAKE'),
             (404, 'Time to collision too short?', 'EMERGENCY BRAKE'),
             (526, 'Object ahead in my lane?', 'FOLLOW: keep a 2.0 s gap')]
    edge(270, 86, 270, 112)
    for i, (cy, q, action) in enumerate(steps):
        diamond(cy, q)
        edge(500, cy, 598, cy, 'yes', 548, cy - 10)
        rect(cy - 31, action, x=600, w=360, stroke=t['s2'] if i < 3 else t['s1'])
        edge(270, cy + 46, 270, (steps[i + 1][0] - 46) if i < 3 else 610, 'no', 296, cy + 66)
    rect(612, 'CRUISE at the set speed (max 30 km/h)', x=60, w=420, stroke=t['s1'])
    text(24, 712, 'Planned logic for Stage 3. The time-to-collision limit will be tuned in the simulator.', 17, t['ink2'], anchor='start')
    text(24, 738, 'Already built on the laptop side: no command for 0.5 s gives full brake, even if the board dies.', 17, t['ink2'], anchor='start')
    out.append('</svg>')
    open(os.path.join(OUT, f'decision_flow_{mode}.svg'), 'w').write('\n'.join(out))


def ros_graph(mode):
    """ROS 2 graph: nodes = boxes (solid built, dashed planned), topics = pills with type and rate."""
    t = THEME[mode]
    W, H = 1000, 1080
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">',
           f'<rect width="{W}" height="{H}" rx="14" fill="{t["bg"]}"/>',
           f'<defs><marker id="a" markerUnits="userSpaceOnUse" markerWidth="11" markerHeight="10" refX="10" refY="5" orient="auto">'
           f'<path d="M0,0 L11,5 L0,10 z" fill="{t["edge"]}"/></marker></defs>']
    mono = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

    def band(y, h, label):
        out.append(f'<rect x="8" y="{y}" width="{W - 16}" height="{h}" rx="14" fill="none" stroke="{t["axis"]}" stroke-width="2" stroke-dasharray="8 6"/>')
        out.append(f'<text x="{W - 24}" y="{y + 30}" font-size="18" font-weight="700" fill="{t["ink2"]}" text-anchor="end">{label}</text>')

    def node(x, y, w, title, sub, built=True, hi=False):
        stroke = t['hi'] if hi else t['edge']
        dash = '' if built else ' stroke-dasharray="9 6"'
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="74" rx="12" fill="{t["box"]}" stroke="{stroke}" stroke-width="{3 if hi else 2}"{dash}/>')
        out.append(f'<text x="{x + w / 2}" y="{y + 32}" font-size="21" font-weight="700" fill="{t["ink"]}" text-anchor="middle">{title}</text>')
        out.append(f'<text x="{x + w / 2}" y="{y + 57}" font-size="16" fill="{t["ink2"]}" text-anchor="middle">{sub}</text>')

    def topic(x, y, w, name, info):
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="60" rx="30" fill="{t["bg"]}" stroke="{t["s1"]}" stroke-width="2"/>')
        out.append(f'<text x="{x + w / 2}" y="{y + 26}" font-size="16" font-family="{mono}" fill="{t["ink"]}" text-anchor="middle">{name}</text>')
        out.append(f'<text x="{x + w / 2}" y="{y + 47}" font-size="15" fill="{t["ink2"]}" text-anchor="middle">{info}</text>')

    def edge(points):
        d = 'M' + ' L'.join(f'{x},{y}' for x, y in points)
        out.append(f'<path d="{d}" fill="none" stroke="{t["edge"]}" stroke-width="2.2" marker-end="url(#a)"/>')

    band(10, 250, 'LAPTOP  (Jazzy)')
    band(276, 790, 'RDK X5  (Humble / TROS)')
    # laptop
    node(40, 56, 260, 'ros_bridge', 'Webots ego car + watchdog')
    topic(348, 63, 254, '/hil/ground_truth/*', 'depth + odom, 14 Hz')
    node(650, 56, 310, 'scorer', 'depth built; scenarios next')
    edge([(300, 93), (348, 93)]); edge([(602, 93), (650, 93)])
    topic(40, 168, 460, '/hil/stereo/{left,right}/image_raw', 'Image bgr8 640x352, 14 Hz (+ camera_info)')
    edge([(170, 130), (170, 168)])
    # board
    node(70, 316, 320, 'hil_input', 'pair to NV12 stereo', built=False)
    edge([(230, 228), (230, 316)])
    topic(40, 420, 380, '/image_combine_raw', 'Image nv12, left over right, 14 Hz')
    edge([(230, 390), (230, 420)])
    node(70, 524, 320, 'stereo_yolo', 'YOLO11m BPU + box distance', hi=True)
    node(440, 524, 300, 'StereoNet', 'BPU dense depth', built=False)
    edge([(230, 480), (230, 524)]); edge([(420, 450), (590, 450), (590, 524)])
    topic(70, 628, 320, '/stereo_yolo/detections', '10 Hz+, also to the web viewer')
    topic(440, 628, 300, 'StereoNet depth', 'Image depth, 10 Hz+')
    edge([(230, 598), (230, 628)]); edge([(590, 598), (590, 628)])
    edge([(740, 658), (860, 658), (860, 130)])
    node(40, 740, 290, 'planner', 'nearest object, ACC + brake', built=False, hi=True)
    edge([(170, 688), (170, 740)]); edge([(590, 688), (590, 714), (290, 714), (290, 740)])
    topic(380, 747, 250, '/hil/planner/cmd', 'Ackermann, 15 Hz')
    node(680, 740, 280, 'safety', 'e-stop latch, limits', built=False, hi=True)
    edge([(330, 777), (380, 777)]); edge([(630, 777), (680, 777)])
    topic(750, 866, 220, '/hil/estop', 'Bool, latched')
    edge([(860, 866), (860, 814)])
    topic(190, 936, 470, '/hil/cmd_drive', 'AckermannDriveStamped, 15 Hz, 0.5 s watchdog')
    edge([(720, 814), (720, 966), (660, 966)])
    edge([(190, 966), (22, 966), (22, 93), (40, 93)])
    # legend
    ly = 1048
    out.append(f'<rect x="30" y="{ly - 18}" width="34" height="22" rx="6" fill="{t["box"]}" stroke="{t["edge"]}" stroke-width="2"/>')
    out.append(f'<text x="72" y="{ly}" font-size="16" fill="{t["ink2"]}">built</text>')
    out.append(f'<rect x="130" y="{ly - 18}" width="34" height="22" rx="6" fill="{t["box"]}" stroke="{t["edge"]}" stroke-width="2" stroke-dasharray="7 5"/>')
    out.append(f'<text x="172" y="{ly}" font-size="16" fill="{t["ink2"]}">planned (Stage 3)</text>')
    out.append(f'<rect x="330" y="{ly - 18}" width="34" height="22" rx="11" fill="{t["bg"]}" stroke="{t["s1"]}" stroke-width="2"/>')
    out.append(f'<text x="372" y="{ly}" font-size="16" fill="{t["ink2"]}">topic: name, type, rate</text>')
    out.append(f'<rect x="590" y="{ly - 18}" width="34" height="22" rx="6" fill="{t["box"]}" stroke="{t["hi"]}" stroke-width="3"/>')
    out.append(f'<text x="632" y="{ly}" font-size="16" fill="{t["ink2"]}">my nodes</text>')
    out.append('</svg>')
    open(os.path.join(OUT, f'ros_graph_{mode}.svg'), 'w').write('\n'.join(out))


def check_layout(name):
    """Fail on slanted arrows, arrows through a box, arrows crossing each other, or no room for an arrowhead."""
    svg = open(os.path.join(OUT, name)).read()
    boxes = [tuple(map(float, g)) for g in re.findall(
        r'<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)" rx="\d+" fill="#', svg)]
    paths = [[tuple(map(float, p.split(','))) for p in d[1:].split(' L')]
             for d in re.findall(r'<path d="(M[^"z]+)"[^>]*marker-end', svg)]
    segs = [(i, a, b) for i, p in enumerate(paths) for a, b in zip(p, p[1:])]
    bad = []
    for i, p in enumerate(paths):
        if abs(p[-1][0] - p[-2][0]) + abs(p[-1][1] - p[-2][1]) < 18:
            bad.append(f'arrow {i} end too short {p}')
    for i, a, b in segs:
        if a[0] != b[0] and a[1] != b[1]:
            bad.append(f'slanted {a}->{b}')
        (x1, x2), (y1, y2) = sorted((a[0], b[0])), sorted((a[1], b[1]))
        for x, y, w, h in boxes:
            if x2 > x + 2 and x1 < x + w - 2 and y2 > y + 2 and y1 < y + h - 2:
                bad.append(f'through box {a}->{b} box {(x, y, w, h)}')
    for i, a, b in segs:
        for j, c, d in segs:
            if i != j and a[1] == b[1] and c[0] == d[0] and min(a[0], b[0]) < c[0] < max(a[0], b[0]) and min(c[1], d[1]) < a[1] < max(c[1], d[1]):
                bad.append(f'cross: arrow {i} and {j} at {(c[0], a[1])}')
    assert not bad, name + chr(10) + chr(10).join(bad)


if __name__ == '__main__':
    for m in THEME:
        accuracy(m)
        bpu(m)
        speedup(m)
        architecture(m)
        hil_architecture(m)
        ros_graph(m)
        decision_flow(m)
    for m in THEME:
        for n in ('architecture', 'hil_architecture', 'ros_graph'):
            check_layout(f'{n}_{m}.svg')
    print('layout check passed; figures written to', os.path.abspath(OUT))
