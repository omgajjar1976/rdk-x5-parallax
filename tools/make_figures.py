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
    W, H = 1200, 360
    boxes = {  # name: x, y, w, h, title, subtitle, highlight
        'cam': (20, 160, 190, 92, 'GS130W stereo camera', '2x SC132GS, 1280x1088', False),
        'mipi': (280, 160, 200, 92, 'mipi_cam', 'GDC rectify, rotation 90', False),
        'codec': (680, 30, 220, 80, 'hobot_codec', 'JPEG encode', False),
        'node': (680, 150, 240, 112, 'stereo_yolo_node', 'YOLO11m on BPU + stereo', True),
        'web': (1010, 30, 175, 80, 'websocket', 'browser view, :8000', False),
        'perf': (1010, 266, 175, 72, '/stereo_yolo/perf', 'stage timings', False),
    }
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">',
           f'<rect width="{W}" height="{H}" rx="12" fill="{t["bg"]}"/>',
           f'<defs><marker id="a" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto">'
           f'<path d="M0,0 L10,5 L0,10 z" fill="{t["edge"]}"/></marker></defs>']

    def edge(points, label, lx, ly):
        d = 'M' + ' L'.join(f'{x},{y}' for x, y in points)
        out.append(f'<path d="{d}" fill="none" stroke="{t["edge"]}" stroke-width="2" marker-end="url(#a)"/>')
        out.append(f'<text x="{lx}" y="{ly}" font-size="13" fill="{t["ink2"]}" text-anchor="middle">{label}</text>')

    edge([(210, 206), (278, 206)], 'MIPI x2', 244, 196)
    edge([(480, 196), (678, 196)], '/image_combine_raw (nv12)', 579, 186)
    edge([(480, 236), (678, 236)], 'camera_info: f, baseline', 579, 258)
    edge([(440, 160), (440, 70), (678, 70)], '/image_combine_raw', 560, 60)
    edge([(900, 70), (1008, 70)], 'JPEG', 954, 60)
    edge([(920, 190), (960, 190), (960, 96), (1008, 96)], '', 0, 0)
    out.append(f'<text x="968" y="150" font-size="13" fill="{t["ink2"]}">detections</text>')
    out.append(f'<text x="968" y="166" font-size="13" fill="{t["ink2"]}">(class + metres)</text>')
    edge([(920, 240), (960, 240), (960, 302), (1008, 302)], '', 0, 0)
    for x, y, w, h, title, sub, hi in boxes.values():
        stroke = t['hi'] if hi else t['edge']
        sw = 3 if hi else 1.5
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{t["box"]}" stroke="{stroke}" stroke-width="{sw}"/>')
        out.append(f'<text x="{x + w / 2}" y="{y + h / 2 - 4}" font-size="16" font-weight="600" fill="{t["ink"]}" text-anchor="middle">{title}</text>')
        out.append(f'<text x="{x + w / 2}" y="{y + h / 2 + 18}" font-size="13" fill="{t["ink2"]}" text-anchor="middle">{sub}</text>')
        if hi:
            out.append(f'<text x="{x + w / 2}" y="{y + h - 10}" font-size="12" font-weight="600" fill="{t["hi"]}" text-anchor="middle">this repo</text>')
    out.append(f'<text x="20" y="335" font-size="13" fill="{t["ink2"]}">All nodes run on the RDK X5. Only the browser is on the laptop.</text>')
    out.append('</svg>')
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, f'architecture_{mode}.svg'), 'w').write('\n'.join(out))


if __name__ == '__main__':
    for m in THEME:
        accuracy(m)
        bpu(m)
        speedup(m)
        architecture(m)
    print('figures written to', os.path.abspath(OUT))
