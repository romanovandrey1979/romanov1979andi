"""Планы трассировки на подложке АР (масштаб 1:100)."""
import os
import subprocess
import numpy as np
from PIL import Image
from matplotlib.patches import Rectangle, Circle

import ovk_plan as G
from ovk_spec import AC, AC_SYS

HERE = os.path.dirname(os.path.abspath(__file__))
APR = os.path.join(HERE, "..", "00_Исходные_данные", "АПР Берта Ромарио.pdf")
CACHE = os.path.join(HERE, ".cache")
CROP = (330, 450, 2720, 2178)            # px при 200 dpi
SCALE = 25.4 / 200                       # мм листа на пиксель
TOP, LEFT = 290, 22
OX = LEFT + (G.PX0 - CROP[0]) * SCALE    # положение оси 1 на листе
OY = TOP - (G.PY0 - CROP[1]) * SCALE     # положение оси А на листе

RED, BLUE, GREEN, GRAY, MAG, ORANGE = "#c62828", "#1565c0", "#2e7d32", "#555555", "#6a1b9a", "#ef6c00"


def underlay(page):
    os.makedirs(CACHE, exist_ok=True)
    png = os.path.join(CACHE, f"apr{page}.png")
    if not os.path.exists(png):
        base = os.path.join(CACHE, f"raw{page}")
        subprocess.run(["pdftoppm", "-r", "200", "-gray", "-f", str(page), "-l", str(page),
                        "-png", "-singlefile", APR, base], check=True)
        im = Image.open(base + ".png").convert("L").crop(CROP)
        a = np.asarray(im).astype(np.float32)
        a = 255 - (255 - a) * 0.38          # осветление подложки
        im = Image.fromarray(a.astype(np.uint8)).resize(
            (im.width * 3 // 4, im.height * 3 // 4), Image.LANCZOS)
        im.save(png, optimize=True)
    return np.asarray(Image.open(png))


def S(pt):
    return OX + pt[0] / 100, OY + pt[1] / 100


def draw_underlay(ax, page):
    img = underlay(page)
    w = (CROP[2] - CROP[0]) * SCALE
    h = (CROP[3] - CROP[1]) * SCALE
    ax.imshow(img, cmap="gray", vmin=0, vmax=255, extent=(LEFT, LEFT + w, TOP - h, TOP),
              interpolation="bilinear", zorder=0)


def lw_for(d):
    return max(0.8, d / 100 * 2.835 * 0.55)


def draw_tree(ax, tree, color, label_fn=None, fs=4.3):
    for pts, q, d, v, c in G.segments(tree):
        xs, ys = zip(*[S(p) for p in pts])
        ax.plot(xs, ys, c=color, lw=lw_for(d), solid_capstyle="butt", zorder=3, alpha=0.9)
        # подпись на самом длинном участке ломаной
        legs = [(pts[i], pts[i + 1]) for i in range(2)]
        a, b = max(legs, key=lambda l: abs(l[0][0] - l[1][0]) + abs(l[0][1] - l[1][1]))
        if abs(a[0] - b[0]) + abs(a[1] - b[1]) < 700:
            continue
        mx, my = S(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2))
        vert = abs(a[0] - b[0]) < 1
        txt = label_fn(q, d) if label_fn else f"Ø{d} L={q}"
        ax.text(mx + (1.2 if vert else 0), my + (0 if vert else 1.0), txt, fontsize=fs,
                color=color, rotation=90 if vert else 0, ha="left" if vert else "center",
                va="center" if vert else "bottom", zorder=5,
                bbox=dict(fc="white", ec="none", pad=0.15, alpha=0.8))


def diffuser(ax, pt, color, txt, fs=4.3, r=1.6):
    x, y = S(pt)
    ax.add_patch(Circle((x, y), r, fc="white", ec=color, lw=0.9, zorder=6))
    ax.plot([x - r * 0.7, x + r * 0.7], [y - r * 0.7, y + r * 0.7], c=color, lw=0.5, zorder=7)
    ax.plot([x - r * 0.7, x + r * 0.7], [y + r * 0.7, y - r * 0.7], c=color, lw=0.5, zorder=7)
    if txt:
        ax.text(x + r + 0.6, y - r - 0.3, txt, fontsize=fs, color=color, va="top", zorder=7,
                bbox=dict(fc="white", ec="none", pad=0.1, alpha=0.8))


def riser(ax, pt, color, txt, fs=4.3):
    x, y = S(pt)
    ax.add_patch(Rectangle((x - 1.5, y - 1.5), 3, 3, fc=color, ec="k", lw=0.5, zorder=8))
    if txt:
        ax.text(x + 2, y + 1.6, txt, fontsize=fs, color=color, weight="bold", zorder=8,
                bbox=dict(fc="white", ec="none", pad=0.1, alpha=0.85))


def box(ax, rect, txt, fs=4.6, fc="#fff3e0"):
    x0, y0 = S(rect[:2])
    x1, y1 = S(rect[2:])
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=fc, ec="k", lw=0.8, zorder=8))
    ax.text((x0 + x1) / 2, (y0 + y1) / 2, txt, ha="center", va="center", fontsize=fs, zorder=9,
            weight="bold")


def roof_unit(ax, pt, color, txt):
    x, y = S(pt)
    ax.add_patch(Circle((x, y), 2.2, fc="white", ec=color, lw=1.2, zorder=8, hatch="////"))
    ax.text(x, y - 3.2, txt, fontsize=4.3, color=color, ha="center", va="top", zorder=9,
            bbox=dict(fc="white", ec="none", pad=0.1, alpha=0.85))


def legend(ax, x, y, items):
    ax.text(x, y, "Условные обозначения", fontsize=6.5, weight="bold")
    y -= 5
    for kind, color, txt in items:
        if kind == "line":
            ax.plot([x, x + 12], [y, y], c=color, lw=2.2)
        elif kind == "dot":
            ax.plot([x, x + 12], [y, y], c=color, lw=1, ls=(0, (1.5, 1.2)))
        elif kind == "dash":
            ax.plot([x, x + 12], [y, y], c=color, lw=1, ls="--")
        elif kind == "diff":
            ax.add_patch(Circle((x + 6, y), 1.6, fc="white", ec=color, lw=0.9))
        elif kind == "riser":
            ax.add_patch(Rectangle((x + 4.5, y - 1.5), 3, 3, fc=color, ec="k", lw=0.5))
        elif kind == "unit":
            ax.add_patch(Rectangle((x + 2, y - 1.2), 8, 2.4, fc="#e1bee7", ec=MAG, lw=0.8))
        elif kind == "roof":
            ax.add_patch(Circle((x + 6, y), 2.2, fc="white", ec=color, lw=1.2, hatch="////"))
        ax.text(x + 15, y, txt, fontsize=5.2, va="center")
        y -= 5.5
    return y


def notes(ax, x, y, lines, width=48, fs=5.2):
    from make_drawings import wrap
    ax.text(x, y, "Примечания", fontsize=6.5, weight="bold")
    y -= 4
    for i, t in enumerate(lines, 1):
        s = wrap(f"{i}. {t}", width)
        ax.text(x, y, s, fontsize=fs, va="top")
        y -= 2.75 * (s.count("\n") + 1) + 1.2
    return y


def title(ax, t):
    ax.text(LEFT + 3, TOP - 1, t, fontsize=8, weight="bold", va="top",
            bbox=dict(fc="white", ec="none", pad=0.5), zorder=20)


def ahu_title(q, d):
    return f"Ø{d} L={q}"


# ================================================================== листы
def slot(ax, pt, color, txt, fs=4.3):
    """Щелевой линейный диффузор у наружной стены."""
    x, y = S(pt)
    ax.add_patch(Rectangle((x - 3.2, y - 0.8), 6.4, 1.6, fc="white", ec=color, lw=0.9, zorder=6,
                           hatch="||||"))
    if txt:
        ax.text(x, y - 1.6, txt, fontsize=fs, color=color, ha="center", va="top", zorder=7,
                bbox=dict(fc="white", ec="none", pad=0.1, alpha=0.85))


def _ortho(ax, a, b, color, d, ls="-", path="hv"):
    mid = (b[0], a[1]) if path == "hv" else (a[0], b[1])
    xs, ys = zip(*[S(p) for p in (a, mid, b)])
    ax.plot(xs, ys, c=color, lw=lw_for(d), ls=ls, solid_capstyle="butt", zorder=3, alpha=0.9)


def plan_floor1_vent(fig, ax):
    draw_underlay(ax, 4)
    title(ax, "План 1 этажа на отм. ±0,000. Вентиляция (М 1:100)")
    tag = {"П1": RED, "В1": BLUE}
    for shaft, sysn, pt, rooms in G.FLOOR1:
        c = tag[sysn]
        for room, q, outs in rooms:
            per = round(q / len(outs))
            d, _ = G.duct_d(per, 3.0)
            for o in outs:
                _ortho(ax, pt, o, c, d, path="vh" if abs(o[1] - pt[1]) > abs(o[0] - pt[0]) else "hv")
                if sysn == "П1":
                    slot(ax, o, c, f"П1 {per} м³/ч\nщелевой, Ø{d}")
                else:
                    diffuser(ax, o, c, f"В1 {per} м³/ч\nØ{d}")
        riser(ax, pt, c, "")
    for k in ("ВК-1", "ВК-4"):
        x, y = S(G.SHAFTS[k]["pt"])
        ax.text(x + 2.4, y - 3.2, f"{k}: П1/В1", fontsize=4.6, color=GREEN, weight="bold", zorder=9,
                bbox=dict(fc="white", ec="none", pad=0.1, alpha=0.85))
    # кухня: зонт и компенсация
    hx, hy = S(G.HOOD)
    ax.add_patch(Rectangle((hx - 4, hy - 2), 8, 4, fc="white", ec=BLUE, lw=1, zorder=6,
                           hatch="xx"))
    ax.text(hx, hy - 3.2, "В3 зонт 450 м³/ч", fontsize=4.5, color=BLUE, ha="center", va="top",
            zorder=7, bbox=dict(fc="white", ec="none", pad=0.1, alpha=0.85))
    sx, sy = S(G.SHAFTS["ВК-2"]["pt"])
    ax.plot([hx + 4, sx, sx], [hy, hy, sy], c=BLUE, lw=lw_for(200), zorder=4)
    ax.text((hx + sx) / 2, hy + 1.6, "Ø200 в подшивке", fontsize=4.2, color=BLUE,
            ha="center", zorder=7, bbox=dict(fc="white", ec="none", pad=0.1, alpha=0.85))
    px, py = S(G.P2_GRILLE)
    ax.plot([sx, sx, px], [sy, py, py], c=RED, lw=lw_for(200), zorder=4)
    diffuser(ax, G.P2_GRILLE, RED, "П2 400 м³/ч\n400×150")
    riser(ax, G.SHAFTS["ВК-2"]["pt"], GREEN, "ВК-2: П2, В3")
    # сауна
    ex, ey = S(G.SAUNA_EXH)
    s3x, s3y = S(G.SHAFTS["ВК-3"]["pt"])
    ax.plot([ex, ex, s3x], [ey, s3y, s3y], c=BLUE, lw=lw_for(125), zorder=4)
    diffuser(ax, G.SAUNA_EXH, BLUE, "В2 130 м³/ч\nØ125 нерж.")
    riser(ax, G.SHAFTS["ВК-3"]["pt"], BLUE, "ВК-3: В2")
    diffuser(ax, G.SAUNA_OVF, GRAY, "Перет. реш.\n300×150 (низ)")
    # котельная
    riser(ax, G.BOILER_EXH, BLUE, "ВК-5: ЕВ1 Ø200\n130 м³/ч")
    fx, fy = S(G.BOILER_FLUE)
    ax.add_patch(Rectangle((fx - 2.25, fy - 2.25), 4.5, 4.5, fc="#ffccbc", ec="k", lw=0.6, zorder=8))
    ax.text(fx - 2.6, fy, "Дымоход\nкотла 450×450\n(ОВ)", fontsize=4.0, ha="right", va="center",
            zorder=9, bbox=dict(fc="white", ec="none", pad=0.1, alpha=0.85))
    bx, by = S(G.BOILER_SUP)
    ax.annotate("", xy=(bx - 3, by), xytext=(bx + 4, by),
                arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=1.2), zorder=8)
    ax.text(bx + 4.5, by, "ПЕ1 Ø160\nреш. 300×200\nh=0,3 м", fontsize=4.3, color=GREEN, va="center")
    # камин: решётка в стене по оси 7
    gx, gy = S(G.FIRE_GRILLE)
    ax.add_patch(Rectangle((gx - 0.8, gy - 1.5), 1.6, 3, fc=GREEN, ec="k", lw=0.5, zorder=8))
    ax.text(gx + 1.5, gy + 2, "ПЕ2 реш. 300×150\nв стене оси 7,\nна уровне пола", fontsize=4.3,
            color=GREEN, zorder=9, bbox=dict(fc="white", ec="none", pad=0.1, alpha=0.85))
    y = legend(ax, 333, 288, [
        ("line", RED, "Воздуховод приточный П1/П2 (подшивка)"),
        ("line", BLUE, "Воздуховод вытяжной В1/В2/В3"),
        ("diff", BLUE, "Решётка вытяжная потолочная"),
        ("riser", RED, "Выход из шахты ВК-1 / ВК-4"),
    ])
    ax.add_patch(Rectangle((335, y - 0.8), 8, 1.6, fc="white", ec=RED, lw=0.9, hatch="||||"))
    ax.text(348, y, "Диффузор щелевой у стены (приток)", fontsize=5.2, va="center")
    notes(ax, 333, y - 6, [
        "Разводка 1 этажа — от шахт ВК-1, ВК-4 воздуховодами в подшивных потолках коридорных "
        "зон, опусках и коробах ВДОЛЬ балок; сквозных отверстий в двутаврах не делать.",
        "Приток — щелевые диффузоры у наружных стен/витражей, вытяжка — потолочные решётки. "
        "Места и отделка — по дизайн-проекту.",
        "Двери С/У, гардеробных, постирочной, кладовой — с подрезом 20 мм.",
        "Зонт В3 включается только при работающей П2 (блокировка); П2 с утеплённым клапаном.",
        "ПЕ2 — решётка с утеплённой заслонкой в наружной стене по оси 7 (сторона террасы); "
        "трубы в плите нет.",
        "Расходы — по листу 3; схема — эскиз заказчика, уточняет проектировщик.",
    ])


def plan_floor2_vent(fig, ax):
    draw_underlay(ax, 5)
    title(ax, "План 2 этажа на отм. +4,500. Вентиляция (М 1:100)")
    for n in G.walk(G.P1_TREE):
        if n["kind"] == "diff":
            d, _ = G.duct_d(n["flow"], 3.0)
            diffuser(ax, n["pt"], RED, f"П1 {n['flow']} м³/ч\nДПУ Ø{d}")
    for n in G.walk(G.V1_TREE):
        if n["kind"] == "diff":
            d, _ = G.duct_d(n["flow"], 3.0)
            diffuser(ax, n["pt"], BLUE, f"В1 {n['flow']} м³/ч\nДПУ Ø{d}")
    for name, s in G.SHAFTS.items():
        riser(ax, s["pt"], GREEN, f"{name}")
    fx, fy = S(G.BOILER_FLUE)
    ax.add_patch(Rectangle((fx - 2.25, fy - 2.25), 4.5, 4.5, fc="#ffccbc", ec="k", lw=0.6, zorder=8))
    ax.text(fx - 2.6, fy - 3, "Короб дымохода\n450×450 (С/У 8)", fontsize=4.0, ha="right",
            va="top", zorder=9, bbox=dict(fc="white", ec="none", pad=0.1, alpha=0.85))
    y = legend(ax, 333, 288, [
        ("diff", RED, "Диффузор приточный (из чердака)"),
        ("diff", BLUE, "Диффузор вытяжной (в чердак)"),
        ("riser", GREEN, "Вентиляционный короб (транзит)"),
    ])
    y = notes(ax, 333, y - 3, [
        "Диффузоры 2 этажа — прямо от магистралей на тёплом чердаке, воздуховодов по этажу "
        "нет. Проход через чердачное перекрытие — в гильзе с уплотнением и пароизоляцией.",
        "Датчики CO₂ + RH — в пом. 3, 7, 10, 12, 14; ночью расход по CO₂ снижается до 50 %.",
        "Пароувлажнение — в приток пом. 3, 7, 10, 12, 14 (ПУ1–ПУ5, см. план чердака).",
        "Диффузор вытяжки холла-лестницы (L=235 м³/ч) — в потолке над вторым светом.",
        "Помещения 2 этажа №1, 2, 9 (холлы) вентилируются перетоком.",
    ])
    from make_drawings import table, wrap
    rows = [("Короб", "Размер", "Назначение")]
    for k, s in G.SHAFTS.items():
        rows.append((k, s["size"], wrap(s["use"], 26)))
    table(ax, 333, y - 3, [13, 15, 50], rows, rh=4.2, fs=4.6)


def plan_attic(fig, ax):
    draw_underlay(ax, 6)
    title(ax, "План чердака (тёплый) на отм. +7,900. Вентиляция и увлажнение (М 1:100)")
    draw_tree(ax, G.P1_TREE, RED)
    draw_tree(ax, G.V1_TREE, BLUE)
    p1nodes = list(G.walk(G.P1_TREE))
    for n in p1nodes + list(G.walk(G.V1_TREE)):
        color = RED if n in p1nodes else BLUE
        if n["kind"] == "diff":
            x, y = S(n["pt"])
            ax.add_patch(Circle((x, y), 1.1, fc=color, ec="k", lw=0.4, zorder=7))
            ax.text(x + 1.5, y - 1.5, n["label"], fontsize=4, color=color, va="top", zorder=7)
        if n["kind"] == "riser":
            riser(ax, n["pt"], color, n["label"])
    box(ax, G.AHU_BOX, "П1В1  1050 м³/ч\nкалор. 7 кВт (вода)", fs=4.2)
    for (a, b), txt, c in ((G.AHU_INTAKE, "К1 забор П1\nØ315 (кровля)", GREEN),
                           (G.AHU_EXHAUST, "К2 выброс В1\nØ315 (кровля)", GREEN)):
        xa, ya = S(a)
        xb, yb = S(b)
        ax.plot([xa, xb], [ya, yb], c=c, lw=lw_for(315), zorder=4)
        roof_unit(ax, b, c, txt)
    # П2 и В3
    box(ax, G.P2_BOX, "П2 400\n5,5 кВт", fs=4.0)
    xs, ys = zip(*[S(p) for p in G.P2_PATH])
    ax.plot(xs, ys, c=RED, lw=lw_for(200), zorder=4)
    xa, ya = S((G.P2_BOX[2], 3950))
    xb, yb = S(G.P2_INTAKE)
    ax.plot([xa, xb], [ya, yb], c=GREEN, lw=lw_for(200), zorder=4)
    roof_unit(ax, G.P2_INTAKE, GREEN, "К3 забор П2 Ø200")
    x3, y3 = S(G.SHAFTS["ВК-2"]["pt"])
    xr, yr = S(G.V3_ROOF)
    ax.plot([x3, x3, xr], [y3, yr, yr], c=BLUE, lw=lw_for(200), zorder=4)
    roof_unit(ax, G.V3_ROOF, BLUE, "К4 В3 выброс Ø200")
    # В2 и ЕВ1
    x, y = S(G.V2_FAN)
    ax.add_patch(Rectangle((x - 2, y - 1.5), 4, 3, fc="#bbdefb", ec="k", lw=0.6, zorder=8))
    ax.text(x + 3, y + 1, "В2 вент. 130 м³/ч\n→ К5 Ø125", fontsize=4.3, color=BLUE,
            zorder=9, bbox=dict(fc="white", ec="none", pad=0.1, alpha=0.85))
    roof_unit(ax, G.EV1_ROOF, BLUE, "К6 ЕВ1 Ø200\nс дефлектором")
    # шумоглушители у ПВУ
    for pts in ([(11600, 6350), (11600, 6000)], [(11000, 7350), (11000, 7900)]):
        (xa, ya), (xb, yb) = S(pts[0]), S(pts[1])
        ax.add_patch(Rectangle((xa - 1.8, min(ya, yb)), 3.6, abs(yb - ya), fc="white",
                               ec="k", lw=0.6, zorder=8, hatch="..."))
    # пароувлажнители
    import ovk_spec as SP
    hum = {h["mark"]: h for h in SP.HUMID}
    nodes = {n["name"]: n for n in p1nodes}
    for mark, (pt, nd) in G.HUMIDIFIERS.items():
        x, y = S(pt)
        ax.add_patch(Rectangle((x - 2.2, y - 1.4), 4.4, 2.8, fc="#b2ebf2", ec="#00838f", lw=0.7,
                               zorder=8))
        ax.text(x, y, mark, ha="center", va="center", fontsize=4.0, weight="bold", zorder=9)
        tx, ty = S(nodes[nd]["pt"])
        ax.plot([x, tx], [y, ty], c="#00838f", lw=0.7, ls=":", zorder=7)
        ax.text(x, y - 2.0, f"{hum[mark]['cap']:.1f} кг/ч", fontsize=3.8, color="#00838f",
                ha="center", va="top", zorder=9)
    # люк
    hx0, hy0 = S(G.HATCH[:2])
    hx1, hy1 = S(G.HATCH[2:])
    ax.add_patch(Rectangle((hx0, hy0), hx1 - hx0, hy1 - hy0, fc="none", ec="k", lw=0.8, ls="--",
                           zorder=8))
    ax.text(hx1 + 0.8, (hy0 + hy1) / 2, "К12 люк 800×1200", fontsize=4.2, va="center", zorder=9,
            bbox=dict(fc="white", ec="none", pad=0.1, alpha=0.85))
    y = legend(ax, 333, 288, [
        ("line", RED, "Воздуховод приточный П1/П2"),
        ("line", BLUE, "Воздуховод вытяжной В1/В2/В3"),
        ("line", GREEN, "Наружный воздух / выброс"),
        ("riser", RED, "Стояк в вент. коробе на 1 этаж"),
        ("roof", GREEN, "Узел прохода через кровлю (К… по БР-ЗК)"),
    ])
    ax.add_patch(Rectangle((337, y - 1.2), 8, 2.4, fc="#b2ebf2", ec="#00838f", lw=0.7))
    ax.text(348, y, "Пароувлажнитель ПУ (паровая форсунка в притоке)", fontsize=5.2, va="center")
    notes(ax, 333, y - 6, [
        "Чердак тёплый (ответ СХ 18.10): изолируются только каналы наружного воздуха и "
        "выброса (32 мм); приток в шахтах — 19 мм от конденсации летом.",
        "ПВУ — на площадке по сдвоенным лагам, на виброопорах; масса ≈ 180 кг — подтвердить "
        "конструктором СХ. Калорифер водяной от буфера (гликоль 30 %), защита от замерзания.",
        "Забор К1 и выброс К2 — через кровлю, разнос ≈ 5 м (≥ 3 м), до дымоходов ≥ 5 м; "
        "выброс выше забора.",
        "Пароувлажнители ПУ1–ПУ6 — на ветках притока к зонам; вода после осмоса по ВК-5, "
        "дренаж в Ст.К1-4; управление по RH из HA.",
        "Подписи участков: Ø — диаметр, мм; L — расход, м³/ч. Опуски к диффузорам 2 этажа — "
        "гибкими вставками L ≤ 0,5 м с дроссель-клапанами.",
    ])


def _draw_freon(ax, tree, color, ls="-"):
    for c in tree["children"]:
        (x0, y0), (x1, y1) = tree["pt"], c["pt"]
        mid = (x1, y0) if c["path"] == "hv" else (x0, y1)
        xs, ys = zip(*[S(p) for p in (tree["pt"], mid, c["pt"])])
        ax.plot(xs, ys, c=color, lw=1.6, ls=ls, zorder=4)
        if c["children"] and c["kind"] != "unit" and not c["name"].startswith("З"):
            x, y = S(c["pt"])
            ax.add_patch(Rectangle((x - 0.9, y - 0.9), 1.8, 1.8, fc="white", ec=color,
                                   lw=0.6, zorder=6))
        _draw_freon(ax, c, color, ls)


def _units(ax, floor):
    for a in AC:
        if a["floor"] != floor:
            continue
        x, y = S(G.UNITS[a["mark"]])
        ax.add_patch(Rectangle((x - 4, y - 2), 8, 4, fc="#f3e5f5", ec=MAG, lw=0.8, ls="--",
                               zorder=7))
        ax.plot([x - 4, x + 4], [y - 2, y + 2], c=MAG, lw=0.4, zorder=7)
        ax.text(x, y + 2.6, f"{a['mark']} {a['unit']} кВт", fontsize=4.5, color=MAG,
                ha="center", weight="bold", zorder=8,
                bbox=dict(fc="white", ec="none", pad=0.1, alpha=0.85))


def _outdoor(ax):
    for k, pt in G.OUT_UNITS.items():
        x, y = S(pt)
        ax.add_patch(Rectangle((x - 4, y - 3), 8, 6, fc="#eeeeee", ec="k", lw=0.9, zorder=8))
        s = next(s for s in AC_SYS if s["sys"] == ("К1" if k == "НБ1" else "К2"))
        ax.text(x, y, f"{k}\n{s['outdoor']} кВт", fontsize=4.2, ha="center", va="center",
                zorder=9, weight="bold")
    xa = S(G.OUT_UNITS["НБ1"])[0] - 6
    xb = S(G.OUT_UNITS["НБ2"])[0] + 6
    yb = S(G.OUT_UNITS["НБ1"])[1]
    ax.add_patch(Rectangle((xa, yb - 4.5), xb - xa, 9, fill=False, ec="k", lw=0.6, ls=(0, (3, 1.5)),
                           zorder=7))
    ax.text(xb + 1, yb - 4.5, "Короб с жалюзи\n(ось Б, 11–13)", fontsize=4.2, va="bottom", zorder=9,
            bbox=dict(fc="white", ec="none", pad=0.1, alpha=0.85))
    for k, pt in G.SLEEVES_AC.items():
        x, y = S(pt)
        ax.add_patch(Circle((x, y), 1.0, fc="white", ec=MAG, lw=0.8, zorder=9))
        ax.text(x + 1.3, y + 0.6, f"{k} Ø110", fontsize=4.0, color=MAG, zorder=9)


def plan_floor1_ac(fig, ax):
    draw_underlay(ax, 4)
    title(ax, "План 1 этажа на отм. ±0,000. Кондиционирование (М 1:100)")
    _draw_freon(ax, G.K1_TREE, MAG)
    _units(ax, 1)
    _outdoor(ax)
    # К2: от НБ2 через З12 в ВК-5
    xa, ya = S(G.OUT_UNITS["НБ2"])
    xs, ys = S(G.SLEEVES_AC["З12"])
    xb, yb = S(G.SHAFTS["ВК-5"]["pt"])
    ax.plot([xa, xs, xs, xb, xb], [ya, ys - 0.01, ys, ys, yb], c=MAG, lw=1.6, ls="--", zorder=4)
    riser(ax, G.SHAFTS["ВК-5"]["pt"], MAG, "К2 ↑ в ВК-5")
    y = legend(ax, 333, 288, [
        ("line", MAG, "Фреонопровод К1 (подшивка 1 этажа)"),
        ("dash", MAG, "Фреонопровод К2 (транзит в ВК-5)"),
    ])
    ax.add_patch(Rectangle((337, y - 1.5), 8, 3, fc="#f3e5f5", ec=MAG, lw=0.8, ls="--"))
    ax.text(348, y, "Канальный блок скрытого монтажа", fontsize=5.2, va="center")
    notes(ax, 333, y - 6, [
        "Внутренние блоки — только канальные, скрытые (решение 18.10); настенных нет. "
        "1 этаж — в подшивных потолках и опусках (реечный потолок кухни, карниз кинозоны), "
        "решётки притока/возврата — по дизайн-проекту.",
        "НБ1, НБ2 — на земле в коробе с жалюзи у южной стены котельной (ось Б, 11–13), на "
        "опорах h ≥ 400 мм; трассы в дом — через гильзы Ø110 З11, З12 в плите (проходок в "
        "брусе нет).",
        "Фреонопроводы К1 — в подшивке 1 этажа вдоль балок, в изоляции 13 мм; К2 — через "
        "ВК-5 на чердак.",
        "Дренаж — в канализационные стояки через сухие затворы; где нет уклона — помпы.",
        "Высоту опусков под блоки (≈ 250–300 мм) проверить по балкам КД4.",
    ])


def plan_floor2_ac(fig, ax):
    draw_underlay(ax, 5)
    title(ax, "План 2 этажа на отм. +4,500. Кондиционирование (М 1:100)")
    _draw_freon(ax, G.K2_TREE, MAG)
    _units(ax, 2)
    riser(ax, G.SHAFTS["ВК-5"]["pt"], MAG, "К2 из НБ2 (ВК-5)")
    y = legend(ax, 333, 288, [
        ("line", MAG, "Фреонопровод К2 (по тёплому чердаку)"),
    ])
    ax.add_patch(Rectangle((337, y - 1.5), 8, 3, fc="#f3e5f5", ec=MAG, lw=0.8, ls="--"))
    ax.text(348, y, "Канальный блок на чердаке над помещением", fontsize=5.2, va="center")
    notes(ax, 333, y - 6, [
        "Канальные блоки 2 этажа — на тёплом чердаке над обслуживаемым помещением, решётки "
        "притока и возврата — в потолке; трассы К2 — по чердаку в изоляции 13 мм.",
        "Разветвители — горизонтально, по схеме производителя.",
        "Дренаж блоков — в канализационные стояки 2 этажа через сухие затворы (помпы при "
        "необходимости).",
        "Расчётные нагрузки — по листу 12; типоразмеры — эскиз заказчика, проверить "
        "заводским подбором.",
    ])
