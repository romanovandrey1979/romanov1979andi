"""291-СС «Слаботочные системы» (СКС, Wi-Fi, видеонаблюдение, домофон, охрана, умный дом)."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Circle

from make_drawings import new_sheet, table, wrap, set_doc
from make_plans import S, draw_underlay, notes, title
from make_ov import GEOM
import eom_data as E

BLUE, GREEN, MAG, GRAY, ORANGE = "#1565c0", "#2e7d32", "#6a1b9a", "#555", "#ef6c00"
CODE = "291-СС"
SHEETS = ["Общие данные. Структурная схема", "План 1 этажа. Слаботочные системы",
          "План 2 этажа и чердака. Слаботочные системы", "Спецификация оборудования и материалов"]

RACK = (19300, 5800)        # слаботочный шкаф рядом с ГРЩ
AP = {1: [(4500, 14800), (4000, 7000), (12000, 7300), (18000, 12000), (17300, 5000)],
      2: [(5600, 14600), (3000, 9000), (12000, 8500), (17600, 12500), (17600, 3000)]}
RJ = {1: [(1, 9), (1, 8), (1, 12), (1, 5)], 2: [(2, 3), (2, 7), (2, 10), (2, 12), (2, 14)]}
CAMS = [(p[1], p[2], p[4]) for p in E.OUTDOOR if p[3] == "КК"] + [
    (23500, 12000, "камера"), (15300, 13000, "камера терраса"), (8600, 4000, "камера"),
    (1300, 4000, "камера")]
TV = [(1, 9), (2, 3), (2, 7)]
KEYPAD = (15600, 4200)
GATE = (15500, -6500)


def sheet_general(pdf):
    fig, ax = new_sheet(1, SHEETS[0])
    ax.text(25, 287, "Общие данные", fontsize=8, weight="bold")
    gn = [
        "Интернет — оптический ввод от провайдера (ОНТ) в слаботочный шкаф (СШ) у ГРЩ, пом. 3; кабель "
        "в земле — в трубе ПНД Ø50 через закладные КЖ0 (10×Ø50).",
        "СКС: кабель U/UTP cat.6 звездой от СШ к каждой розетке RJ45 и точке Wi-Fi (PoE).",
        "Wi-Fi: 5 потолочных точек на этаж (Wi-Fi 6/7, PoE), бесшовный роуминг; на чердаке — питание "
        "от PoE-коммутатора.",
        f"Видеонаблюдение: {len(CAMS)} IP-камер 4 Мп с ИК-подсветкой по фасадам и у входа/ворот, "
        "видеорегистратор (NVR) на 8–16 каналов в СШ, хранение ≥ 14 сут.",
        "Домофон: вызывная панель у калитки (IP, с камерой) — кабель в земле в трубе ПНД; "
        "мониторы в прихожей и на 2 этаже, приложение на смартфоне.",
        "Охрана и пожарная сигнализация — общая радиоканальная централь (291-МЗ.ПС): датчики "
        "открытия на входных дверях и витражах 1 этажа, датчики движения в холлах.",
        "Умный дом: контроллер в СШ, интеграция по Modbus/KNX/Wi-Fi: котельная (каскад, "
        "погодозависимость), тёплые полы (термостаты по комнатам), вентиляция П1В1 (режимы, "
        "CO₂), кондиционеры (шлюз VRF), защита от протечек, освещение (сценарии), сауна "
        "(дистанционное включение — с ограничением по времени).",
        "Все слаботочные кабели в брусе — по тем же каналам «Эл» (291-ЭОМ, листы 9, 10) в "
        "отдельной трубе; совместная прокладка с силовыми — запрещена.",
        "Питание СШ — отдельная группа ГРЩ C10 + ИБП 1 кВА (≥ 30 мин для роутера, NVR, централи).",
    ]
    y = 282
    for i, t in enumerate(gn, 1):
        s = wrap(f"{i}. {t}", 100)
        ax.text(25, y, s, fontsize=5.6, va="top")
        y -= 3.15 * (s.count("\n") + 1) + 1.1
    # структурная схема
    ax.text(250, 287, "Структурная схема", fontsize=8, weight="bold")

    def box(x, y, w, h, t, fc="white"):
        ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec="k", lw=0.8))
        ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=4.8)
    box(300, 200, 50, 50, "СШ 19\" 12U\nОНТ, роутер,\nPoE-коммутатор 24п,\nNVR, контроллер\nумного дома, ИБП", "#e3f2fd")
    box(250, 262, 40, 12, "Провайдер (оптика)", "#eee")
    ax.plot([290, 325, 325], [268, 268, 250], c="k", lw=0.8)
    peers = [("Wi-Fi точки ×10 (PoE)", 270, 232), ("RJ45 розетки ×9", 270, 214),
             (f"IP-камеры ×{len(CAMS)} (PoE)", 270, 196), ("Домофон у калитки (IP)", 360, 262),
             ("Мониторы домофона ×2", 365, 240), ("Радиоцентраль ПС/охраны", 365, 222),
             ("Котельная, ПВУ, VRF, «Нептун»", 365, 204), ("Термостаты ТП ×24", 365, 186)]
    for t, x, y in peers:
        box(x - (5 if x < 300 else 0), y - 5, 40 if x > 300 else 26, 10, t)
        xc = 300 if x < 300 else 350
        ax.plot([x + (21 if x < 300 else 0), xc], [y, y if 200 <= y <= 250 else max(min(y, 250), 200)],
                c=GRAY, lw=0.6)
    pdf.savefig(fig)
    plt.close(fig)


def plan(fig, ax, floor, n):
    draw_underlay(ax, 4 if floor == 1 else 5)
    title(ax, f"План {floor} этажа{' и чердака' if floor == 2 else ''}. Слаботочные системы (М 1:100)")
    for x, y in AP[floor]:
        sx, sy = S((x, y))
        ax.add_patch(Circle((sx, sy), 1.8, fc="white", ec=BLUE, lw=1, zorder=8))
        ax.text(sx, sy, "W", ha="center", va="center", fontsize=4, color=BLUE, weight="bold", zorder=9)
    for key in RJ[floor]:
        x0, y0, x1, y1 = GEOM[key]
        sx, sy = S((x0 + 500, (y0 + y1) / 2))
        ax.add_patch(Rectangle((sx - 1.2, sy - 1.2), 2.4, 2.4, fc="#bbdefb", ec=BLUE, lw=0.7, zorder=8))
    for key in TV:
        if key[0] != floor:
            continue
        x0, y0, x1, y1 = GEOM[key]
        sx, sy = S((x0 + 500, (y0 + y1) / 2 + 700))
        ax.add_patch(Rectangle((sx - 1.2, sy - 1.2), 2.4, 2.4, fc="#c8e6c9", ec=GREEN, lw=0.7, zorder=8))
    if floor == 1:
        for x, y, t in CAMS:
            sx, sy = S((x, y))
            ax.add_patch(Rectangle((sx - 1.6, sy - 1.0), 3.2, 2.0, fc=MAG, ec="k", lw=0.5, zorder=8))
        sx, sy = S(RACK)
        ax.add_patch(Rectangle((sx - 3.5, sy - 1.8), 7, 3.6, fc="#e3f2fd", ec="k", lw=0.9, zorder=9))
        ax.text(sx, sy, "СШ", ha="center", va="center", fontsize=4.5, weight="bold", zorder=10)
        sx, sy = S(KEYPAD)
        ax.add_patch(Rectangle((sx - 1.5, sy - 1.5), 3, 3, fc="#fff9c4", ec="k", lw=0.6, zorder=9))
        ax.text(sx + 2, sy, "монитор\nдомофона", fontsize=3.8, va="center", zorder=9)
        gx, gy = S((15500, -500))
        ax.annotate("", xy=S((15300, 1300)), xytext=(gx, gy - 4),
                    arrowprops=dict(arrowstyle="-|>", color=GRAY, lw=0.8))
        ax.text(gx + 1, gy - 6, "к калитке: домофон, камера\n(ПНД Ø50 в земле)", fontsize=4, color=GRAY)
    else:
        sx, sy = S((11400, 6200))
        ax.add_patch(Circle((sx, sy), 1.8, fc="white", ec=BLUE, lw=1, ls="--", zorder=8))
        ax.text(sx + 2.5, sy, "Wi-Fi/датчики\nна чердаке (опция)", fontsize=3.8, color=GRAY, zorder=9)
    y = 288
    ax.text(333, y, "Условные обозначения", fontsize=6.5, weight="bold")
    y -= 6
    for kind, t in (("ap", "Точка доступа Wi-Fi потолочная (PoE)"), ("rj", "Розетка RJ45 cat.6 (2 порта)"),
                    ("tv", "Розетка ТВ/HDMI-over-IP"), ("cam", "IP-камера (наружная)"),
                    ("rack", "Слаботочный шкаф")):
        if kind == "ap":
            ax.add_patch(Circle((338, y), 1.8, fc="white", ec=BLUE, lw=1))
        elif kind == "rj":
            ax.add_patch(Rectangle((336.8, y - 1.2), 2.4, 2.4, fc="#bbdefb", ec=BLUE, lw=0.7))
        elif kind == "tv":
            ax.add_patch(Rectangle((336.8, y - 1.2), 2.4, 2.4, fc="#c8e6c9", ec=GREEN, lw=0.7))
        elif kind == "cam":
            ax.add_patch(Rectangle((336.4, y - 1.0), 3.2, 2.0, fc=MAG, ec="k", lw=0.5))
        else:
            ax.add_patch(Rectangle((334.5, y - 1.8), 7, 3.6, fc="#e3f2fd", ec="k", lw=0.9))
        ax.text(345, y, t, fontsize=5.2, va="center")
        y -= 5.5
    notes(ax, 333, y - 2, [
        "Кабели — U/UTP cat.6 звездой от СШ, в отдельных трубах/металлорукаве.",
        "Точки на брусовых стенах — по каналам «Эл» (291-ЭОМ) с отдельной трубой.",
        "Места точек доступа — по центру зон, между балками, без металлических экранов.",
    ])


def spec_rows():
    return [
        ("#", "Слаботочный шкаф и активное оборудование"),
        ("СШ", "Шкаф 19\" 12U настенный с вентиляцией и полками", "", "шт.", 1, ""),
        ("", "Оптический терминал провайдера (ОНТ)", "провайдер", "шт.", 1, ""),
        ("", "Маршрутизатор с поддержкой резервного LTE-канала", "", "шт.", 1, ""),
        ("", "Коммутатор PoE+ 24 порта, управляемый", "", "шт.", 1, ""),
        ("", "Видеорегистратор (NVR) 16 каналов, HDD 2×4 ТБ", "", "компл.", 1, ""),
        ("", "Контроллер «умного дома» с модулями Modbus/KNX, шлюз VRF", "", "компл.", 1, ""),
        ("", "ИБП 1 кВА онлайн", "", "шт.", 1, ""),
        ("#", "Конечные устройства"),
        ("", "Точка доступа Wi-Fi 6/7 потолочная, PoE", "", "шт.", len(AP[1]) + len(AP[2]), ""),
        ("", "IP-камера 4 Мп уличная, ИК 30 м, PoE", "", "шт.", len(CAMS), ""),
        ("", "Вызывная панель IP с камерой, электрозамок калитки", "", "компл.", 1, ""),
        ("", "Монитор домофона IP 7\"", "", "шт.", 2, ""),
        ("", "Розетка RJ45 cat.6 двойная", "", "шт.", len(RJ[1]) + len(RJ[2]), ""),
        ("", "Розетка ТВ/HDMI-over-IP", "", "шт.", len(TV), ""),
        ("", "Датчики открытия/движения (к централи 291-МЗ.ПС)", "", "шт.", 14, ""),
        ("#", "Кабели и трассы"),
        ("", "Кабель U/UTP cat.6 LSZH", "", "м", 900, "Ориентир."),
        ("", "Кабель U/UTP cat.6 наружный (в земле — в трубе)", "", "м", 120, ""),
        ("", "Труба ПНД Ø50 (ввод, калитка)", "", "м", 80, ""),
        ("", "Металлорукав / гофра Ø20 для слаботочки", "", "м", 600, ""),
    ]


def sheet_spec(pdf):
    fig, ax = new_sheet(4, SHEETS[3])
    ax.text(25, 287, "Спецификация оборудования и материалов", fontsize=7.5, weight="bold")
    data = [("Поз.", "Наименование", "Тип, марка", "Ед.", "Кол.", "Примечание")]
    for r in spec_rows():
        data.append(r if r[0] == "#" else (r[0], wrap(r[1], 105), r[2], r[3], r[4], r[5]))
    table(ax, 22, 284, [16, 190, 40, 13, 13, 116], data, rh=5.2, fs=5.4,
          aligns=["center", "left", "left", "center", "center", "left"])
    pdf.savefig(fig)
    plt.close(fig)


def main(out):
    set_doc(CODE, SHEETS)
    with PdfPages(out) as pdf:
        sheet_general(pdf)
        for n, fl in ((2, 1), (3, 2)):
            fig, ax = new_sheet(n, SHEETS[n - 1])
            plan(fig, ax, fl, n)
            pdf.savefig(fig)
            plt.close(fig)
        sheet_spec(pdf)
        pdf.infodict()["Title"] = f"{CODE} Слаботочные системы"
    set_doc()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "291-СС.pdf")
