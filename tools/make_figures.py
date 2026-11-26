#!/usr/bin/env python3
"""Regenerate the README figures (light + dark): python3 tools/make_figures.py

Numbers are the measured values from the README tables; edit DATA below, not the PNGs.
"""
import os

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
           f'<defs><marker id="a" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto">'
           f'<path d="M0,0 L12,6 L0,12 z" fill="{t["edge"]}"/></marker></defs>']

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
    W, H = 1200, 560
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">',
           f'<rect width="{W}" height="{H}" rx="14" fill="{t["bg"]}"/>',
           f'<defs><marker id="a" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto">'
           f'<path d="M0,0 L12,6 L0,12 z" fill="{t["edge"]}"/></marker></defs>']
    # two zones
    for x, w, label in ((12, 400, 'LAPTOP  (Ubuntu 24.04, ROS 2 Jazzy)'), (500, 688, 'RDK X5  (RDK OS 3.5.0, ROS 2 Humble / TROS)')):
        out.append(f'<rect x="{x}" y="12" width="{w}" height="{H - 24}" rx="14" fill="none" stroke="{t["axis"]}" stroke-width="2" stroke-dasharray="8 6"/>')
        out.append(f'<text x="{x + 18}" y="44" font-size="18" font-weight="700" fill="{t["ink2"]}">{label}</text>')

    def box(x, y, w, h, title, sub, hi=False):
        stroke = t['hi'] if hi else t['edge']
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{t["box"]}" stroke="{stroke}" stroke-width="{3.5 if hi else 2}"/>')
        out.append(f'<text x="{x + w / 2}" y="{y + h / 2 - 4}" font-size="20" font-weight="600" fill="{t["ink"]}" text-anchor="middle">{title}</text>')
        out.append(f'<text x="{x + w / 2}" y="{y + h / 2 + 22}" font-size="16" fill="{t["ink2"]}" text-anchor="middle">{sub}</text>')

    def edge(points, label='', lx=0, ly=0, anchor='middle'):
        d = 'M' + ' L'.join(f'{x},{y}' for x, y in points)
        out.append(f'<path d="{d}" fill="none" stroke="{t["edge"]}" stroke-width="2.5" marker-end="url(#a)"/>')
        if label:
            out.append(f'<text x="{lx}" y="{ly}" font-size="16" fill="{t["ink2"]}" text-anchor="{anchor}">{label}</text>')

    box(36, 70, 352, 96, 'Webots + SUMO world', 'city / SF, traffic, pedestrians')
    box(36, 214, 352, 96, 'ros_bridge', 'stereo 640x352, 14 Hz, watchdog')
    box(36, 400, 352, 110, 'Scorer (ground truth)', 'depth AbsRel, stop gap, collisions')
    box(540, 214, 200, 96, 'hil_input', 'pair -> NV12 stereo')
    box(790, 90, 340, 100, 'stereo_yolo', 'YOLO11m on BPU + box distance', hi=True)
    box(790, 214, 340, 96, 'StereoNet (BPU)', 'dense depth, 2nd workload')
    box(790, 340, 340, 96, 'planner + safety', 'ACC / emergency brake, e-stop', hi=True)
    edge([(212, 166), (212, 212)])
    edge([(388, 262), (538, 262)], 'stereo pair', 463, 250)
    edge([(740, 240), (765, 240), (765, 140), (788, 140)])
    edge([(740, 262), (788, 262)])
    edge([(1130, 140), (1152, 140), (1152, 388), (1132, 388)])
    out.append(f'<text x="1174" y="264" font-size="16" fill="{t["ink2"]}" text-anchor="middle" transform="rotate(90 1174 264)">boxes + metres</text>')
    edge([(960, 310), (960, 338)], 'depth', 975, 330, 'start')
    edge([(788, 388), (300, 388), (300, 312)], 'cmd_drive (Ackermann, 15 Hz)', 560, 378)
    edge([(150, 312), (150, 398)], 'GT depth + odom', 160, 360, 'start')
    edge([(810, 310), (810, 324), (752, 324), (752, 470), (390, 470)], 'board depth', 560, 460)
    out.append(f'<text x="36" y="540" font-size="16" fill="{t["ink2"]}">Ground truth only reaches the scorer, never the board. Wi-Fi 5 GHz now, Ethernet planned (risk 1).</text>')
    out.append('</svg>')
    open(os.path.join(OUT, f'hil_architecture_{mode}.svg'), 'w').write('\n'.join(out))


if __name__ == '__main__':
    for m in THEME:
        accuracy(m)
        bpu(m)
        speedup(m)
        architecture(m)
        hil_architecture(m)
    print('figures written to', os.path.abspath(OUT))
