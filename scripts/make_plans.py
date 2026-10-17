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
def plan_floor1_vent(fig, ax):
    draw_underlay(ax, 4)
    title(ax, "План 1 этажа на отм. ±0,000. Вентиляция (М 1:100)")
    tag = {"П1": RED, "В1": BLUE}
    for name, pt, sysn, rooms in G.COLLECTORS:
        c = tag[sysn]
        x0, y0 = S(pt)
        for room, q, outs in rooms:
            n_total = sum(n for *_, n in outs)
            per = q / n_total
            for (x, y, n) in outs:
                xs, ys = S((x, y))
                ax.plot([x0, xs], [y0, ys], c=c, lw=0.9, ls=(0, (1.5, 1.2)), zorder=3)
                diffuser(ax, (x, y), c, f"{sysn} {round(per * n)} м³/ч\nØ90×{n}")
        riser(ax, pt, c, "")
        dx = -2 if sysn == "П1" else 2
        ax.text(x0 + dx, y0 + (-2.2 if sysn == "П1" else 2.2),
                f"{name} ({sum(n for r in rooms for *_, n in r[2])} лин.)", fontsize=4.4,
                color=c, weight="bold", ha="right" if sysn == "П1" else "left",
                va="top" if sysn == "П1" else "bottom", zorder=9,
                bbox=dict(fc="white", ec="none", pad=0.1, alpha=0.85))
    # кухня: зонт и компенсация
    hx, hy = S(G.HOOD)
    ax.add_patch(Rectangle((hx - 4, hy - 2), 8, 4, fc="white", ec=BLUE, lw=1, zorder=6,
                           hatch="xx"))
    ax.text(hx, hy - 3.2, "В3 зонт 450 м³/ч", fontsize=4.5, color=BLUE, ha="center", va="top",
            zorder=7, bbox=dict(fc="white", ec="none", pad=0.1, alpha=0.85))
    sx, sy = S(G.SHAFTS["ВК-2"]["pt"])
    ax.plot([hx + 4, sx, sx], [hy, hy, sy], c=BLUE, lw=lw_for(200), zorder=4)
    ax.text((hx + sx) / 2, hy + 1.6, "Ø200 в перекрытии", fontsize=4.2, color=BLUE,
            ha="center", zorder=7, bbox=dict(fc="white", ec="none", pad=0.1, alpha=0.85))
    px, py = S(G.P2_GRILLE)
    ax.plot([sx, sx, px], [sy, py, py], c=RED, lw=lw_for(200), zorder=4)
    diffuser(ax, G.P2_GRILLE, RED, "П2 400 м³/ч\n400×150")
    riser(ax, G.SHAFTS["ВК-2"]["pt"], GREEN, "ВК-2: П2, В3")
    # сауна
    ex, ey = S(G.SAUNA_EXH)
    s3x, s3y = S(G.SHAFTS["ВК-3"]["pt"])
    ax.plot([ex, ex, s3x], [ey, s3y, s3y], c=BLUE, lw=lw_for(125), zorder=4)
    diffuser(ax, G.SAUNA_EXH, BLUE, "В2 130 м³/ч\nØ125")
    riser(ax, G.SHAFTS["ВК-3"]["pt"], BLUE, "ВК-3: В2")
    diffuser(ax, G.SAUNA_OVF, GRAY, "Перет. реш.\n300×150 (низ)")
    # котельная
    riser(ax, G.BOILER_EXH, BLUE, "ВК-5: ЕВ1 Ø200\n130 м³/ч")
    bx, by = S(G.BOILER_SUP)
    ax.annotate("", xy=(bx - 3, by), xytext=(bx + 4, by),
                arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=1.2), zorder=8)
    ax.text(bx + 4.5, by, "ПЕ1\n300×200\nh=0,3 м", fontsize=4.3, color=GREEN, va="center")
    # камин
    (fx0, fy0), (fx1, fy1) = S(G.FIRE_AIR[0]), S(G.FIRE_AIR[1])
    ax.annotate("", xy=(fx1, fy1), xytext=(fx0, fy0),
                arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=1.4), zorder=8)
    ax.text(fx0 + 0.5, fy0 + 1.2, "ПЕ2 Ø125\nк топке камина", fontsize=4.3, color=GREEN)
    y = legend(ax, 333, 288, [
        ("dot", RED, "Гибкий воздуховод Ø90, приток П1"),
        ("dot", BLUE, "Гибкий воздуховод Ø90, вытяжка В1"),
        ("line", BLUE, "Воздуховод вытяжной (В2, В3)"),
        ("line", RED, "Воздуховод приточный (П2)"),
        ("diff", RED, "Диффузор потолочный"),
        ("riser", RED, "Коллектор / стояк в вент. коробе"),
    ])
    notes(ax, 333, y - 3, [
        "Гибкие воздуховоды Ø90 прокладывать в межэтажном перекрытии между балками; "
        "трасса — по месту, без пережатия, радиус поворота ≥ 1D, длина линии ≤ 15 м.",
        "Отверстия в двутавровых балках — только в зоне стенки по правилам производителя; "
        "клееные балки не прорезать.",
        "Коллекторы РК1…РК4 — в основании вент. коробов ВК-1, ВК-4 на уровне перекрытия, "
        "с ревизионным люком снизу.",
        "Двери С/У, гардеробных, постирочной, кладовой — с подрезом 20 мм.",
        "Диффузоры — в зазоре между видимыми балками, по дизайн-проекту.",
        "Зонт В3 — с собственным вентилятором и обратным клапаном; П2 сблокирована с зонтом.",
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
    y = legend(ax, 333, 288, [
        ("diff", RED, "Диффузор приточный (из чердака)"),
        ("diff", BLUE, "Диффузор вытяжной (в чердак)"),
        ("riser", GREEN, "Вентиляционный короб (транзит)"),
    ])
    y = notes(ax, 333, y - 3, [
        "Воздуховоды к диффузорам 2 этажа — сверху, из чердака (см. план чердака). "
        "Проход через чердачное перекрытие — в гильзе с уплотнением и пароизоляцией.",
        "Диффузор вытяжки холла-лестницы (L=235 м³/ч) — в потолке лестничного холла "
        "над проёмом второго света.",
        "Транзит через 2 этаж — в вентиляционных коробах ВК-1…ВК-5 (размеры — см. "
        "задание смежным разделам).",
        "Помещения 2 этажа №1, 2, 9 (холлы) вентилируются перетоком.",
    ])
    from make_drawings import table
    rows = [("Короб", "Размер", "Назначение")]
    for k, s in G.SHAFTS.items():
        from make_drawings import wrap
        rows.append((k, s["size"], wrap(s["use"], 26)))
    table(ax, 333, y - 3, [13, 15, 50], rows, rh=4.2, fs=4.6)


def plan_attic(fig, ax):
    draw_underlay(ax, 6)
    title(ax, "План чердака на отм. +7,900. Вентиляция (М 1:100)")
    draw_tree(ax, G.P1_TREE, RED)
    draw_tree(ax, G.V1_TREE, BLUE)
    for n in list(G.walk(G.P1_TREE)) + list(G.walk(G.V1_TREE)):
        color = RED if n in list(G.walk(G.P1_TREE)) else BLUE
        if n["kind"] == "diff":
            x, y = S(n["pt"])
            ax.add_patch(Circle((x, y), 1.1, fc=color, ec="k", lw=0.4, zorder=7))
            ax.text(x + 1.5, y - 1.5, n["label"], fontsize=4, color=color, va="top", zorder=7)
        if n["kind"] == "riser":
            riser(ax, n["pt"], color, n["label"])
    box(ax, G.AHU_BOX, "П1В1  1050 м³/ч")
    for (a, b), txt, c in ((G.AHU_INTAKE, "Наружный воздух П1\nØ315", GREEN),
                           (G.AHU_EXHAUST, "Выброс В1\nØ315 (выше на 1 м)", GREEN)):
        xa, ya = S(a)
        xb, yb = S(b)
        ax.plot([xa, xb], [ya, yb], c=c, lw=lw_for(315), zorder=4)
        roof_unit(ax, b, c, txt)
    # П2 и В3
    box(ax, G.P2_BOX, "П2", fs=4.5)
    xs, ys = zip(*[S(p) for p in G.P2_PATH])
    ax.plot(xs, ys, c=RED, lw=lw_for(200), zorder=4)
    xa, ya = S((G.P2_BOX[2], 3950))
    xb, yb = S(G.P2_INTAKE)
    ax.plot([xa, xb], [ya, yb], c=GREEN, lw=lw_for(200), zorder=4)
    roof_unit(ax, G.P2_INTAKE, GREEN, "Нар. воздух П2 Ø200")
    x3, y3 = S(G.SHAFTS["ВК-2"]["pt"])
    xr, yr = S(G.V3_ROOF)
    ax.plot([x3, x3, xr], [y3, yr, yr], c=BLUE, lw=lw_for(200), zorder=4)
    roof_unit(ax, G.V3_ROOF, BLUE, "В3 выброс Ø200\nвыше кровли")
    # В2 и ЕВ1
    x, y = S(G.V2_FAN)
    ax.add_patch(Rectangle((x - 2, y - 1.5), 4, 3, fc="#bbdefb", ec="k", lw=0.6, zorder=8))
    ax.text(x + 3, y + 1, "В2 вент. 130 м³/ч\n→ выброс Ø125", fontsize=4.3, color=BLUE,
            zorder=9, bbox=dict(fc="white", ec="none", pad=0.1, alpha=0.85))
    roof_unit(ax, G.EV1_ROOF, BLUE, "ЕВ1 Ø200\nс дефлектором")
    # шумоглушители у ПВУ
    for pts in ([(11600, 6350), (11600, 6000)], [(11000, 7350), (11000, 7900)]):
        (xa, ya), (xb, yb) = S(pts[0]), S(pts[1])
        ax.add_patch(Rectangle((xa - 1.8, min(ya, yb)), 3.6, abs(yb - ya), fc="white",
                               ec="k", lw=0.6, zorder=8, hatch="..."))
    y = legend(ax, 333, 288, [
        ("line", RED, "Воздуховод приточный П1/П2"),
        ("line", BLUE, "Воздуховод вытяжной В1/В2/В3"),
        ("line", GREEN, "Наружный воздух / выброс"),
        ("riser", RED, "Стояк в вент. коробе на 1 этаж"),
        ("roof", GREEN, "Узел прохода через кровлю"),
    ])
    notes(ax, 333, y - 3, [
        "Подписи участков: Ø — диаметр, мм; L — расход, м³/ч.",
        "ПВУ П1В1 — на площадке из сдвоенных лаг (зона сдвоенных чердачных лаг по АР), "
        "на виброопорах; доступ через люк. Масса с площадкой ≈ 180 кг — согласовать с КД.",
        "Воздуховоды прокладывать по лагам на опорах с виброизоляцией, отметка низа "
        "+8,000…+8,100. Приток — изоляция 19 мм; наружный воздух, выброс, П2, В3 — 32 мм.",
        "Крышные узлы — проходные элементы для фальцевой кровли, выброс выше воздухозабора "
        "П1 не менее чем на 1 м, расстояние по горизонтали ≥ 4 м.",
        "Опуски к диффузорам 2 этажа — гибкими вставками L≤0,5 м с дроссель-клапанами.",
    ])


def _draw_freon(ax, tree, color):
    for c in tree["children"]:
        (x0, y0), (x1, y1) = tree["pt"], c["pt"]
        mid = (x1, y0) if c["path"] == "hv" else (x0, y1)
        xs, ys = zip(*[S(p) for p in (tree["pt"], mid, c["pt"])])
        ax.plot(xs, ys, c=color, lw=1.6, zorder=4)
        if c["children"] and c["kind"] != "unit":
            x, y = S(c["pt"])
            ax.add_patch(Rectangle((x - 0.9, y - 0.9), 1.8, 1.8, fc="white", ec=color,
                                   lw=0.6, zorder=6))
        _draw_freon(ax, c, color)


def _units(ax, floor):
    for a in AC:
        if a["floor"] != floor:
            continue
        x, y = S(G.UNITS[a["mark"]])
        w, h = (2.4, 8) if a["mark"] in G.VERTICAL_UNITS else (8, 2.4)
        ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc="#e1bee7", ec=MAG, lw=0.8,
                               zorder=7))
        if a["mark"] in G.VERTICAL_UNITS:
            y += 3
        ax.text(x, y + 1.8, f"{a['mark']} {a['unit']} кВт", fontsize=4.5, color=MAG,
                ha="center", weight="bold", zorder=8,
                bbox=dict(fc="white", ec="none", pad=0.1, alpha=0.85))


def plan_floor1_ac(fig, ax):
    draw_underlay(ax, 4)
    title(ax, "План 1 этажа на отм. ±0,000. Кондиционирование (М 1:100)")
    _draw_freon(ax, G.K1_TREE, MAG)
    _units(ax, 1)
    for k, pt in G.OUT_UNITS.items():
        x, y = S(pt)
        ax.add_patch(Rectangle((x - 3, y - 4), 9, 8, fc="#eeeeee", ec="k", lw=0.9, zorder=8))
        s = next(s for s in AC_SYS if s["sys"] == ("К1" if k == "НБ1" else "К2"))
        ax.text(x + 1.5, y, f"{k}\n{s['outdoor']}\nкВт", fontsize=4.4, ha="center",
                va="center", zorder=9, weight="bold")
    # К2: подъём в ВК-5
    xa, ya = S(G.OUT_UNITS["НБ2"])
    xb, yb = S(G.SHAFTS["ВК-5"]["pt"])
    ax.plot([xa - 3, xb, xb], [ya, ya, yb], c=MAG, lw=1.6, ls="--", zorder=4)
    riser(ax, G.SHAFTS["ВК-5"]["pt"], MAG, "К2 ↑ в ВК-5")
    y = legend(ax, 333, 288, [
        ("line", MAG, "Фреонопровод К1 (в перекрытии)"),
        ("dash", MAG, "Фреонопровод К2 (транзит)"),
        ("unit", MAG, "Внутренний блок настенный"),
    ])
    notes(ax, 333, y - 3, [
        "Наружные блоки НБ1, НБ2 — на опорах (рама на фундаментных блоках, h≥400 мм над "
        "отмосткой) у восточного фасада, у котельной; вне окон спален.",
        "Ввод трасс — через стену котельной в гильзе с уплотнением и компенсацией усадки.",
        "Фреонопроводы К1 — в межэтажном перекрытии между балками, в изоляции 13 мм; "
        "подъём к блокам — в штробе каркасной перегородки / декоративном коробе.",
        "Дренаж — в ближайший канализационный стояк через сухой затвор (см. задание ВК).",
        "Точное место блоков — по дизайн-проекту; блоки не размещать над камином и плитой.",
    ])


def plan_floor2_ac(fig, ax):
    draw_underlay(ax, 5)
    title(ax, "План 2 этажа на отм. +4,500. Кондиционирование (М 1:100)")
    _draw_freon(ax, G.K2_TREE, MAG)
    _units(ax, 2)
    riser(ax, G.SHAFTS["ВК-5"]["pt"], MAG, "К2 из НБ2 (ВК-5)")
    y = legend(ax, 333, 288, [
        ("line", MAG, "Фреонопровод К2 (по чердаку)"),
        ("unit", MAG, "Внутренний блок настенный"),
    ])
    notes(ax, 333, y - 3, [
        "Трассы К2 — по чердаку над перекрытием в изоляции 13 мм (на холодном чердаке — "
        "дополнительно 25 мм с защитным покрытием), опуски к блокам через чердачное "
        "перекрытие в гильзах.",
        "Разветвители — горизонтально, по схеме производителя.",
        "Дренаж блоков 2 этажа — в канализацию в ближайших С/У через сухие затворы.",
    ])
