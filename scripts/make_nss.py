"""291-НС «Наружные сети и генплан — предварительная схема» на подложке схемы размещения АПР (лист 3)."""
import os
import subprocess
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Circle
from PIL import Image

from make_drawings import new_sheet, wrap, set_doc, table
from make_plans import APR, CACHE, notes

BLUE, RED, BROWN, GREEN, ORANGE, MAG, GRAY = "#1565c0", "#c62828", "#6d4c41", "#2e7d32", "#ef6c00", "#6a1b9a", "#555"
CODE = "291-НС"
SHEETS = ["Схема наружных сетей и генплана (предварительная)", "Пояснения и ведомость сетей"]

# Привязка подложки (лист 3 АПР при 250 dpi): px = 214 + (484 + X·0,0257)/0,7839;
# py = 286 + (1230 − Y·0,0258)/0,7839 (X, Y — мм от осей 1/А)
CROP = (214, 286, 2000, 2286)
K_SH = 1 / (0.0329 * 250)   # мм листа на пиксель (масштаб 1:250)
TOP, LEFT = 290, 22


def to_px(x, y):
    return 214 + (484 + x * 0.0257) / 0.7839, 286 + (1230 - y * 0.0258) / 0.7839


def S(pt):
    px, py = to_px(*pt)
    return LEFT + (px - CROP[0]) * K_SH, TOP - (py - CROP[1]) * K_SH


def underlay(ax):
    os.makedirs(CACHE, exist_ok=True)
    png = os.path.join(CACHE, "apr3.png")
    if not os.path.exists(png):
        base = os.path.join(CACHE, "raw3")
        subprocess.run(["pdftoppm", "-r", "250", "-gray", "-f", "3", "-l", "3", "-png",
                        "-singlefile", APR, base], check=True)
        im = Image.open(base + ".png").convert("L").crop(CROP)
        a = 255 - (255 - np.asarray(im).astype(np.float32)) * 0.45
        Image.fromarray(a.astype(np.uint8)).save(png, optimize=True)
    img = np.asarray(Image.open(png))
    w = (CROP[2] - CROP[0]) * K_SH
    h = (CROP[3] - CROP[1]) * K_SH
    ax.imshow(img, cmap="gray", vmin=0, vmax=255, extent=(LEFT, LEFT + w, TOP - h, TOP), zorder=0)


WELLS = {"К1": (6730, 470), "К2": (-1790, 10230), "К3": (12720, 1860)}
OUTLETS = {"К2": (1745, 11950), "К1": (6880, 4360), "К3": (19370, 7890)}
ROAD_Y = -7400
LINES = [  # (имя, цвет, стиль, точки, подпись)
    ("К1", BROWN, "-", [WELLS["К2"], (-1790, 470), WELLS["К1"]], "К1 Ø160 ПП, i ≥ 0,02"),
    ("К1", BROWN, "-", [WELLS["К3"], (6730, 1860), WELLS["К1"]], ""),
    ("К1", BROWN, "-", [WELLS["К1"], (6730, ROAD_Y)], "К1 Ø160 → в центральную сеть (точка по ТУ)"),
    ("В1", BLUE, "-", [(18800, ROAD_Y), (18800, -500), (20970, -500), (20970, 4090)],
     "В1 ПЭ100 Ø32, h ≥ 1,8 м (глубже промерзания)"),
    ("Э", RED, "-", [(16300, ROAD_Y), (16300, 300), (18900, 300), (18900, 4800)],
     "Кабель 0,4 кВ в ПНД Ø110, h = 0,7 м"),
    ("СС", MAG, "--", [(17500, ROAD_Y), (17500, 900), (18900, 900)], "Слаботочка (оптика, домофон) ПНД Ø50"),
    ("Г", ORANGE, "--", [(24500, ROAD_Y), (24500, 2600), (23500, 2600)],
     "Газ (этап 2) — по проекту Мособлгаза"),
    ("К2", GREEN, ":", [(-500, 1800), (-500, 18200), (24500, 18200), (24500, 15200)],
     "Дренаж/ливнёвка → в канаву по согласованию или дренажный колодец"),
]
OBJECTS = [  # (подпись, прямоугольник x0,y0,x1,y1, цвет)
    ("Шкаф учёта", (15800, -7300, 16800, -6700), RED),
    ("НБ1/НБ2", (24600, 1800, 26200, 4800), GRAY),
    ("Склад пеллет 2–3 т", (20500, -2600, 23300, -700), BROWN),
    ("КНС (если нужна по ТУ)", (6000, -3200, 7500, -1800), BROWN),
    ("Ворота / калитка, домофон", (17200, -7600, 19800, -7000), MAG),
]


def sheet_scheme(pdf):
    fig, ax = new_sheet(1, SHEETS[0])
    underlay(ax)
    ax.text(LEFT + 3, TOP - 1, "Схема наружных сетей и генплана (предварительная, М 1:250)",
            fontsize=8, weight="bold", va="top", bbox=dict(fc="white", ec="none", pad=0.5), zorder=20)
    for name, c, ls, pts, lbl in LINES:
        xs, ys = zip(*[S(p) for p in pts])
        ax.plot(xs, ys, c=c, lw=1.6, ls=ls, zorder=5)
        if lbl:
            mx, my = S(pts[len(pts) // 2])
            ax.text(mx + 1, my + 1, lbl, fontsize=4.4, color=c, zorder=9,
                    bbox=dict(fc="white", ec="none", pad=0.1, alpha=0.85))
    for nm, pt in WELLS.items():
        x, y = S(pt)
        ax.add_patch(Circle((x, y), 1.8, fc="white", ec=BROWN, lw=1.2, zorder=8))
        ax.text(x + 2.2, y + 1, nm, fontsize=5, color=BROWN, weight="bold", zorder=9)
    for nm, pt in OUTLETS.items():
        xs, ys = zip(*[S(p) for p in (pt, WELLS[nm])])
        ax.plot(xs, ys, c=BROWN, lw=1.2, zorder=5)
    for nm, (x0, y0, x1, y1), c in OBJECTS:
        (a, b), (cc, d) = S((x0, y0)), S((x1, y1))
        ax.add_patch(Rectangle((a, b), cc - a, d - b, fc="white", ec=c, lw=1, ls="--" if "КНС" in nm else "-",
                               zorder=8))
        ax.text(cc + 1, (b + d) / 2, nm, fontsize=4.4, color=c, va="center", zorder=9,
                bbox=dict(fc="white", ec="none", pad=0.1, alpha=0.85))
    y = 288
    ax.text(260, y, "Условные обозначения", fontsize=6.5, weight="bold")
    y -= 6
    for nm, c, ls, t in (("К1", BROWN, "-", "Канализация бытовая"), ("В1", BLUE, "-", "Водопровод"),
                         ("Э", RED, "-", "Кабель электроснабжения 0,4 кВ"),
                         ("СС", MAG, "--", "Слаботочные сети"), ("Г", ORANGE, "--", "Газопровод (этап 2)"),
                         ("К2", GREEN, ":", "Дренаж / ливневая канализация")):
        ax.plot([260, 272], [y, y], c=c, lw=1.6, ls=ls)
        ax.text(275, y, t, fontsize=5.2, va="center")
        y -= 5.5
    notes(ax, 260, y - 2, [
        "Схема предварительная: трассы до точек подключения уточняются по ТУ (водоканал, Россети, "
        "Мособлгаз) и топосъёмке с отметками.",
        "Рельеф понижается от дороги (≈ 80) к дому (76–79) и канаве (68–73): самотёк канализации "
        "к коллектору на дороге возможен только при его глубине ≥ 3…4 м — иначе КНС.",
        "Колодцы К1–К3 — по КЖ0: дно К2 выше К1 на 82 мм, К3 выше К1 на 116 мм; К1 — сборный.",
        "Водопровод и канализация — глубже промерзания (1,25–1,34 м по КЖ0) или с утеплением.",
        "Ливнёвка и дренаж — в канаву только по согласованию; проверить водоохранную зону.",
        "Наружные блоки кондиционеров и склад пеллет — у котельной (восточный фасад).",
    ], width=52)
    pdf.savefig(fig)
    plt.close(fig)


def sheet_notes(pdf):
    fig, ax = new_sheet(2, SHEETS[1])
    ax.text(25, 287, "Ведомость наружных сетей (предварительная)", fontsize=8, weight="bold")
    rows = [("Сеть", "От", "До", "Материал, Ø", "Длина ≈, м", "Что нужно для проекта")]
    rows += [
        ("К1 бытовая", "Выпуски Ø160 (КЖ0)", "К2, К3 → К1 → центр. сеть", "ПП/ПВХ Ø160", "≈ 45",
         "ТУ водоканала с отметкой лотка; при недостатке уклона — КНС"),
        ("В1 водопровод", "Центр. сеть", "Ввод в котельную (КЖ0 Ø110)", "ПЭ100 SDR11 Ø32", "≈ 20",
         "ТУ водоканала, давление в сети, место врезки и колодца"),
        ("Электро 0,4 кВ", "Опора/КТП Россетей", "Шкаф учёта → ГРЩ (КЖ0 10×Ø50)", "АВБбШв 4×35 в ПНД", "≈ 20",
         "ТУ Россетей на 50 кВт (см. расчёт нагрузок)"),
        ("Слаботочка", "Провайдер / калитка", "СШ у ГРЩ", "ПНД Ø50", "≈ 25", "Договор с провайдером"),
        ("Газ (этап 2)", "Газопровод на улице", "Фасад котельной (ось 13)", "ПЭ / сталь", "≈ 15",
         "ТУ Мособлгаза, проект ГСВ лицензированной организации"),
        ("Дренаж/ливнёвка", "Водостоки, дренаж вокруг дома", "Канава / дренажный колодец", "ПВХ Ø110–160",
         "≈ 90", "Согласование сброса, отметки рельефа"),
        ("Контур заземления", "—", "Вокруг дома, 1 м от фундамента", "Полоса 40×4", "≈ 100",
         "Монтаж до обратной засыпки и отмостки (291-МЗ.ПС)"),
    ]
    yb = table(ax, 25, 283, [30, 40, 55, 35, 18, 120], rows, rh=8, fs=5.5)
    ax.text(25, yb - 6, "Что нужно для рабочего проекта наружных сетей и генплана", fontsize=7, weight="bold")
    y = yb - 12
    for i, t in enumerate([
        "Топосъёмка М 1:500 с отметками рельефа и существующими сетями (на листе 3 АПР есть "
        "горизонтали — нужна исполнительная съёмка в DWG).",
        "ГПЗУ / выписка ЕГРН: зоны с особыми условиями (канава, водоохранная зона), отступы.",
        "ТУ: водоканал (вода и канализация, отметки), Россети (50 кВт), Мособлгаз (газ).",
        "Решение по ливнёвке: сброс в канаву (согласование) или дренажные колодцы.",
    ], 1):
        s = wrap(f"{i}. {t}", 160)
        ax.text(25, y, s, fontsize=5.8, va="top")
        y -= 3.3 * (s.count("\n") + 1) + 1.5
    pdf.savefig(fig)
    plt.close(fig)


def main(out):
    set_doc(CODE, SHEETS)
    with PdfPages(out) as pdf:
        sheet_scheme(pdf)
        sheet_notes(pdf)
        pdf.infodict()["Title"] = f"{CODE} Наружные сети — предварительная схема"
    set_doc()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "291-НС.pdf")
