"""291-ЭОМ «Электрооборудование и электроосвещение» — PDF, А3."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Circle

from make_drawings import new_sheet, table, wrap, set_doc
from make_plans import S, draw_underlay, legend, notes, title
import eom_data as E
from make_review import SCEN, i3

RED, BLUE, GREEN, GRAY, ORANGE, MAG = "#c62828", "#1565c0", "#2e7d32", "#555", "#ef6c00", "#6a1b9a"
CODE = "291-ЭОМ"
SHEETS = [
    "Общие данные",
    "Однолинейная схема ГРЩ",
    "Схемы щитов ЩР1, ЩР2",
    "Схемы щитов ЩК, ЩВ, отходящие линии ГРЩ. Баланс фаз",
    "План 1 этажа. Розеточная сеть и силовое оборудование",
    "План 1 этажа. Электроосвещение",
    "План 2 этажа. Розеточная сеть и силовое оборудование",
    "План 2 этажа. Электроосвещение",
    "Ведомость отверстий «Эл» в брусе (задание в КД1), лист 1",
    "Ведомость отверстий «Эл» в брусе (задание в КД1), лист 2",
    "Спецификация оборудования, изделий и материалов",
]
PANELS = {1: {"ГРЩ": (19550, 5300), "ЩР1": (19550, 6500), "ЩК": (19550, 2900)},
          2: {"ЩР2": (18000, 8800)}}
for i, h in enumerate(E.HOLES, 1):
    h["id"] = f"Эл-{i:02d}"


def sheet_general(pdf):
    fig, ax = new_sheet(1, SHEETS[0])
    ax.text(25, 287, "Общие данные", fontsize=8, weight="bold")
    rows = [("Лист", "Наименование")] + [(str(i + 1), s) for i, s in enumerate(SHEETS)]
    yb = table(ax, 25, 283, [12, 115], rows, rh=4.4, fs=5.5)
    pu = sum(g["p"] for g in E.GROUPS if "Резерв" not in g["name"])
    rows = [("Показатель", "Значение"),
            ("Категория надёжности электроснабжения", "III"),
            ("Напряжение, система заземления", "380/220 В, TN-C-S (разделение PEN в ГРЩ)"),
            ("Разрешённая мощность (заявить)", "50 кВт, 3 фазы (см. расчёт нагрузок)"),
            ("Установленная мощность Pу", f"{pu:.1f} кВт"),
            ("Расчётная мощность, штатная зима / лето", f"{SCEN[0][1]:.1f} / {SCEN[3][1]:.1f} кВт"),
            ("Расчётная мощность, резерв с реле приоритета", f"{SCEN[2][1]:.1f} кВт, {i3(SCEN[2][1]):.0f} А"),
            ("Вводной автомат ГРЩ", "C80 3P + УЗИП I+II + реле приоритета"),
            ("Светильников / розеток / отверстий «Эл» в брусе",
             f"{sum(r['n_lum'] for r in E.ROOMS)} / {sum(r['n_sock'] for r in E.ROOMS)} / {len(E.HOLES)}")]
    ax.text(25, yb - 5, "Основные показатели", fontsize=7, weight="bold")
    table(ax, 25, yb - 8, [70, 72], rows, rh=4.6, fs=5.5)
    ax.text(185, 287, "Общие указания", fontsize=8, weight="bold")
    gn = [
        "Раздел выполнен по АПР, КД1, КЖ0 и разделам 291-ОВК, ОВ, ВК, МЗ.ПС, СС. Нормы: ПУЭ (7 изд.), "
        "СП 256.1325800.2016, СП 52.13330.2016, СП 6.13130.2021.",
        "Электроснабжение — от сетей Россетей по ТУ (заявка 50 кВт). Шкаф учёта — на границе участка, "
        "далее кабель в земле до ввода в дом через закладные КЖ0 (10×ПНД Ø50, оси 11/Д–Е).",
        "ГРЩ, ЩР1 — в нише гардеробной (пом. 3) у ввода кабеля; ЩК — в котельной; ЩР2 — в "
        "кладовой 2 эт. (пом. 6); ЩВ — на чердаке у ПВУ; ЩУ — на фасаде у входа.",
        "Реле приоритета (ограничитель нагрузки) в ГРЩ: при токе ввода > 75 А отключает "
        "электропечь сауны, затем нагреватель П2, затем ступени электрокотла.",
        "Деревянный дом: скрытая проводка — только в стальных трубах или металлорукаве с "
        "заземлением, кабели ВВГнг(А)-LS; в брусе — по заводским отверстиям «Эл» (лист 9, 10), "
        "подъём от пола (1 эт. — из пирога пола по плите, 2 эт. — из межэтажного перекрытия). "
        "Монтажные коробки — металлические или с огнестойкой прокладкой.",
        "Отверстия «Эл» выполняет завод-изготовитель бруса по ведомости (листы 9, 10). Привязки "
        "даны от осей; если точка попадает в проём, нагель или шпильку — сдвинуть до 300 мм "
        "вдоль стены и отметить в КД1.",
        "Розетки — h=300 мм от пола (кухня — 1100 мм, С/У — IP44 на удалении ≥ 600 мм от ванны и "
        "душа), выключатели — h=900 мм, наружные светильники — h=2400 мм, наружные розетки IP54 — "
        "h=500 мм.",
        "Все розеточные группы, кухня, сауна, С/У, улица — с УЗО 30 мА; ДСУП в С/У и сауне (291-МЗ.ПС).",
        "Освещение — светодиодное; расчётные точки показаны условно, окончательно — по "
        "дизайн-проекту (сохранить число групп и привязку к отверстиям в брусе).",
        "Сауна: кабель к печи и светильникам — термостойкий; светильники IP54, +125 °C; "
        "выключатели и пульт печи — вне парилки.",
    ]
    y = 282
    for i, t in enumerate(gn, 1):
        s = wrap(f"{i}. {t}", 95)
        ax.text(185, y, s, fontsize=5.5, va="top")
        y -= 3.1 * (s.count("\n") + 1) + 1.1
    pdf.savefig(fig)
    plt.close(fig)


def sheet_sld(pdf):
    fig, ax = new_sheet(2, SHEETS[1])
    ax.text(25, 287, "Однолинейная схема ГРЩ", fontsize=8, weight="bold")

    def box(x, y, w, h, t, fc="white", fs=5.2):
        ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec="k", lw=0.9))
        ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs)
    box(30, 235, 46, 30, "Сеть Россети\nВЛ/КЛ 0,4 кВ\nТУ на 50 кВт", "#eeeeee")
    box(30, 190, 46, 32, "Шкаф учёта\nна границе участка\nQF C80 3P, счётчик\n3ф прямого вкл.", "#fff8e1")
    ax.plot([53, 53], [235, 222], c="k", lw=1.5)
    ax.plot([53, 53, 100], [190, 175, 175], c="k", lw=1.5)
    ax.text(58, 179, "АВБбШв 4×35 / ВБбШв 5×16\nв земле, h=0,7 м", fontsize=4.8)
    box(100, 120, 50, 120, "", "#e3f2fd")
    ax.text(125, 232, "ГРЩ", fontsize=7, weight="bold", ha="center")
    items = ["QS 100 A (рубильник)", "Разделение PEN → PE+N\n(ГЗШ, повт. заземление)",
             "УЗИП I+II класса", "QF C80 3P", "Реле приоритета\n(ограничитель нагрузки)",
             "Шины A, B, C, N, PE"]
    y = 222
    for it in items:
        ax.text(125, y, it, fontsize=4.9, ha="center", va="top")
        y -= 16
    out = [("ЩР1 (1 этаж)", "C63 3P", "ВВГнг(А)-LS 5×16"), ("ЩР2 (2 этаж)", "C40 3P", "ВВГнг(А)-LS 5×10"),
           ("ЩК (котельная)", "C50 3P", "ВВГнг(А)-LS 5×16"), ("ЩВ (чердак, вентиляция)", "C32 3P", "ВВГнг(А)-LS 5×6")]
    out += [(g["name"], g["br"], g["cab"]) for g in E.GROUPS if g["panel"] == "ГРЩ"]
    y = 255
    for nm, br, cab in out:
        ax.plot([150, 175], [y, y], c="k", lw=1)
        ax.add_patch(Rectangle((175, y - 3), 22, 6, fc="white", ec="k", lw=0.7))
        ax.text(186, y, br, ha="center", va="center", fontsize=4.6)
        ax.plot([197, 215], [y, y], c="k", lw=1)
        ax.text(217, y, f"{nm}  —  {cab}", va="center", fontsize=5)
        y -= 14
    ax.plot([150, 150], [255, y + 14], c="k", lw=1.6)
    ax.text(25, 100, wrap(
        "Примечания: 1. Ток уставки реле приоритета 75 А; порядок отключения: сауна → нагреватель "
        "П2 → ступени электрокотла (возврат с задержкой 5 мин). 2. Счётчик — по ТУ сетевой "
        "организации (возможен вынос на опору). 3. Защита ввода от перенапряжений согласована "
        "с молниезащитой (291-МЗ.ПС). 4. Сечения кабелей ввода уточнить по длине линии и "
        "потере напряжения ≤ 5 %.", 140), fontsize=5.6, va="top")
    pdf.savefig(fig)
    plt.close(fig)


def group_table(ax, x, y, panel, n0=1):
    rows = [("№", "Наименование", "Pу, кВт", "Фаза", "Автомат", "УЗО/диф.", "Кабель")]
    for i, g in enumerate([g for g in E.GROUPS if g["panel"] == panel], n0):
        rows.append((f"{panel}-{i}", wrap(g["name"], 60), f"{g['p']:.2f}".replace(".", ","),
                     g["phase"], g["br"], g["prot"], g["cab"]))
    return table(ax, x, y, [16, 92, 13, 11, 18, 22, 50], rows, rh=4.3, fs=4.8)


def sheet_panels1(pdf):
    fig, ax = new_sheet(3, SHEETS[2])
    ax.text(25, 287, "Щит ЩР1 (1 этаж) — ввод C63 3P, ВВГнг(А)-LS 5×16", fontsize=7, weight="bold")
    yb = group_table(ax, 25, 284, "ЩР1")
    ax.text(25, yb - 5, "Щит ЩР2 (2 этаж) — ввод C40 3P, ВВГнг(А)-LS 5×10", fontsize=7, weight="bold")
    group_table(ax, 25, yb - 8, "ЩР2")
    pdf.savefig(fig)
    plt.close(fig)


def sheet_panels2(pdf):
    fig, ax = new_sheet(4, SHEETS[3])
    ax.text(25, 287, "Щит ЩК (котельная) — ввод C50 3P, ВВГнг(А)-LS 5×16", fontsize=7, weight="bold")
    yb = group_table(ax, 25, 284, "ЩК")
    ax.text(25, yb - 5, "Щит ЩВ (чердак) — ввод C32 3P, ВВГнг(А)-LS 5×6", fontsize=7, weight="bold")
    yb = group_table(ax, 25, yb - 8, "ЩВ")
    ax.text(25, yb - 5, "Отходящие линии ГРЩ", fontsize=7, weight="bold")
    yb = group_table(ax, 25, yb - 8, "ГРЩ")
    ax.text(25, yb - 6, "Баланс фаз (установленная мощность без резерва, кВт)", fontsize=7, weight="bold")
    ph = E.PHASES
    avg = sum(ph.values()) / 3
    rows = [("Фаза", "Pу, кВт", "Отклонение от среднего")] + [
        (k, f"{v:.1f}".replace(".", ","), f"{(v - avg) / avg * 100:+.0f} %") for k, v in ph.items()]
    table(ax, 25, yb - 9, [20, 25, 40], rows, rh=4.6, fs=5.4)
    pdf.savefig(fig)
    plt.close(fig)


def plan(fig, ax, floor, kind):
    draw_underlay(ax, 4 if floor == 1 else 5)
    title(ax, f"План {floor} этажа. " + ("Розеточная сеть и силовое оборудование"
                                          if kind == "p" else "Электроосвещение") + " (М 1:100)")
    hole_at = {(h["x"], h["y"]): h["id"] for h in E.HOLES if h["floor"] == floor}
    if kind == "p":
        for fl, x, y, t, room in E.POINTS:
            if fl != floor or t in ("В", "Н", "КК"):
                continue
            sx, sy = S((x, y))
            brus = (x, y) in hole_at
            ax.add_patch(Rectangle((sx - 1.3, sy - 1.0), 2.6, 2.0, fc=ORANGE if brus else "white",
                                   ec=RED, lw=0.7, zorder=7))
            if brus:
                ax.text(sx + 1.6, sy + 1.1, hole_at[(x, y)], fontsize=3.6, color=ORANGE, zorder=8)
        for nm, pt in PANELS.get(floor, {}).items():
            sx, sy = S(pt)
            ax.add_patch(Rectangle((sx - 3.5, sy - 1.8), 7, 3.6, fc="#fff9c4", ec="k", lw=0.9, zorder=9))
            ax.text(sx, sy, nm, ha="center", va="center", fontsize=4.4, weight="bold", zorder=10)
    else:
        for r in E.ROOMS:
            if r["floor"] != floor:
                continue
            for x, y in E.lum_points(r["geom"], r["n_lum"]):
                sx, sy = S((x, y))
                ax.add_patch(Circle((sx, sy), 1.0, fc="white", ec=BLUE, lw=0.6, zorder=7))
                ax.plot([sx - 0.7, sx + 0.7], [sy - 0.7, sy + 0.7], c=BLUE, lw=0.4, zorder=8)
                ax.plot([sx - 0.7, sx + 0.7], [sy + 0.7, sy - 0.7], c=BLUE, lw=0.4, zorder=8)
            x0, y0, x1, y1 = r["geom"]
            cx, cy = S(((x0 + x1) / 2, y0 + 350))
            ax.text(cx, cy, f"{r['E']} лк, {r['n_lum']}×{E.LUM_W} Вт", fontsize=3.8, ha="center",
                    color=BLUE, zorder=9, bbox=dict(fc="white", ec="none", pad=0.1, alpha=0.8))
        for fl, x, y, t, room in E.POINTS:
            if fl != floor or t not in ("В", "Н"):
                continue
            sx, sy = S((x, y))
            brus = (x, y) in hole_at
            if t == "В":
                ax.add_patch(Circle((sx, sy), 0.9, fc=ORANGE if brus else "white", ec="k", lw=0.6, zorder=8))
                ax.plot([sx, sx + 1.6], [sy, sy + 1.6], c="k", lw=0.6, zorder=8)
            else:
                ax.add_patch(Rectangle((sx - 1.2, sy - 1.2), 2.4, 2.4, fc=ORANGE, ec=GREEN, lw=0.8, zorder=8))
            if brus:
                ax.text(sx + 1.8, sy - 2, hole_at[(x, y)], fontsize=3.6, color=ORANGE, zorder=9)
    y = 288
    ax.text(333, y, "Условные обозначения", fontsize=6.5, weight="bold")
    y -= 6
    sym = ([("rect", "white", RED, "Розетка (на каркасной перегородке)"),
            ("rect", ORANGE, RED, "Розетка на брусе — отверстие «Эл»"),
            ("rect", "#fff9c4", "k", "Щит")] if kind == "p" else
           [("lum", "white", BLUE, "Светильник LED 15 Вт (условно)"),
            ("sw", ORANGE, "k", "Выключатель (оранжевый — на брусе)"),
            ("rect", ORANGE, GREEN, "Наружный светильник (отверстие в брусе)")])
    for kd, fc, ec, t in sym:
        if kd == "rect":
            ax.add_patch(Rectangle((336, y - 1.2), 4, 2.4, fc=fc, ec=ec, lw=0.8))
        elif kd == "lum":
            ax.add_patch(Circle((338, y), 1.2, fc=fc, ec=ec, lw=0.8))
        else:
            ax.add_patch(Circle((338, y), 1.0, fc=fc, ec=ec, lw=0.8))
        ax.text(345, y, t, fontsize=5.2, va="center")
        y -= 5.5
    notes(ax, 333, y - 2, [
        "Точки — расчётные (число и группы); размещение уточняется дизайн-проектом.",
        "Оранжевым — точки на брусовых стенах: отверстия выполняет завод по ведомости (листы 9, 10).",
        "Проводка — в стальных трубах/металлорукаве; к щитам — в конструкции пола и перекрытия.",
        "Тёплые полы, конвекторы, кондиционеры — питание по разделам ОВ/ОВК от групп щитов.",
    ])


def holes_sheet(pdf, n, part):
    fig, ax = new_sheet(n, SHEETS[n - 1])
    ax.text(25, 287, "Ведомость отверстий «Эл» в брусе — задание заводу-изготовителю (КД1)",
            fontsize=7.5, weight="bold")
    half = (len(E.HOLES) + 1) // 2
    hs = E.HOLES[:half] if part == 1 else E.HOLES[half:]
    rows = [("№", "Этаж", "Стена (ось)", "Привязка от оси", "Высота от пола, мм",
             "Отм. абс. (от ±0,000)", "Тип", "Помещение / назначение")]
    tnames = {"Р": "розетка", "РК": "розетка кухонная", "В": "выключатель", "Н": "наружный светильник",
              "РН": "наружная розетка IP54", "КК": "камера / вызывная панель"}
    for h in hs:
        rows.append((h["id"], h["floor"], h["axis"], f"{h['off']:+d} мм от оси {h['ref']}",
                     h["h"], h["abs_h"], tnames[h["type"]], h["room"]))
    table(ax, 22, 283, [16, 12, 22, 45, 26, 28, 40, 90], rows, rh=5.2, fs=5.0)
    ax.text(25, 52, wrap(
        "Отверстие — вертикальный канал Ø25…32 мм от низа стены (1 эт. — от подвенечного венца, "
        "2 эт. — от уровня перекрытия) до точки + горизонтальный подрозетник Ø68 на высоте точки; "
        "для наружных — сквозное Ø25 через стену с уклоном наружу. Знак «+» — в сторону "
        "возрастания осей (цифры вправо, буквы вверх по плану).", 200), fontsize=5.6, va="top")
    pdf.savefig(fig)
    plt.close(fig)


def spec_rows():
    n_lum = sum(r["n_lum"] for r in E.ROOMS)
    n_sock = sum(r["n_sock"] for r in E.ROOMS)
    rows = [("#", "Щиты и вводное устройство"),
            ("", "Шкаф учёта уличный с QF C80 3P и счётчиком 3ф (по ТУ)", "", "компл.", 1, ""),
            ("ГРЩ", "Щит распределительный навесной 72 мод.: QS 100 A, QF C80 3P, УЗИП I+II, реле "
                    "приоритета, шины N/PE, автоматы отходящих линий", "", "компл.", 1, ""),
            ("ЩР1, ЩР2", "Щит распределительный встраиваемый 72/48 мод. с автоматами и УЗО по схемам",
             "", "компл.", 2, ""),
            ("ЩК, ЩВ", "Щит навесной 36/24 мод. с автоматами по схемам", "", "компл.", 2, ""),
            ("ЩУ", "Щит уличный IP65 12 мод., УЗО, автоматы, реле времени/фотореле", "", "компл.", 1, ""),
            ("#", "Кабели и защита"),
            ("", "Кабель ВВГнг(А)-LS 3×1,5", "", "м", 900, "Ориентир."),
            ("", "Кабель ВВГнг(А)-LS 3×2,5", "", "м", 1100, ""),
            ("", "Кабель ВВГнг(А)-LS 3×4 / 3×10", "", "м", 40, ""),
            ("", "Кабель ВВГнг(А)-LS 5×2,5 / 5×4 / 5×6", "", "м", 180, ""),
            ("", "Кабель ВВГнг(А)-LS 5×10 / 5×16", "", "м", 70, ""),
            ("", "Кабель ввода АВБбШв 4×35 (или ВБбШв 5×16)", "", "м", 40, "По ТУ"),
            ("", "Труба стальная тонкостенная / металлорукав РЗ-ЦХ Ø16…32 с фитингами", "", "м", 1600, ""),
            ("", "Коробки монтажные металлические / огнестойкие", "", "шт.", n_sock + 60, ""),
            ("#", "Электроустановочные изделия и освещение"),
            ("", "Розетка 16 А с заземлением (IP20 / IP44 в С/У)", "", "шт.", n_sock, ""),
            ("", "Розетка наружная IP54", "", "шт.", 4, ""),
            ("", "Выключатель 1–2 клавиши / проходной", "", "шт.", 40, ""),
            ("", f"Светильник LED {E.LUM_W} Вт ≈ 1500 лм (тип по дизайн-проекту)", "", "шт.", n_lum, ""),
            ("", "Светильник наружный фасадный IP65", "", "шт.", 8, ""),
            ("", "Светильник для сауны +125 °C IP54", "", "шт.", 2, ""),
            ("", "Освещение и розетка чердака, светильник IP54", "", "компл.", 1, ""),
        ]
    return rows


def sheet_spec(pdf):
    fig, ax = new_sheet(11, SHEETS[10])
    ax.text(25, 287, "Спецификация оборудования, изделий и материалов (ГОСТ 21.110-2013)",
            fontsize=7.5, weight="bold")
    data = [("Поз.", "Наименование и техническая характеристика", "Тип, марка", "Ед.",
             "Кол.", "Примечание")]
    for r in spec_rows():
        data.append(r if r[0] == "#" else (r[0], wrap(r[1], 105), r[2], r[3], r[4], r[5]))
    table(ax, 22, 284, [16, 190, 40, 13, 13, 116], data, rh=5.0, fs=5.3,
          aligns=["center", "left", "left", "center", "center", "left"])
    pdf.savefig(fig)
    plt.close(fig)


def main(out):
    set_doc(CODE, SHEETS)
    with PdfPages(out) as pdf:
        sheet_general(pdf)
        sheet_sld(pdf)
        sheet_panels1(pdf)
        sheet_panels2(pdf)
        for n, fl, kind in ((5, 1, "p"), (6, 1, "l"), (7, 2, "p"), (8, 2, "l")):
            fig, ax = new_sheet(n, SHEETS[n - 1])
            plan(fig, ax, fl, kind)
            pdf.savefig(fig)
            plt.close(fig)
        holes_sheet(pdf, 9, 1)
        holes_sheet(pdf, 10, 2)
        sheet_spec(pdf)
        pdf.infodict()["Title"] = f"{CODE} Электрооборудование и электроосвещение"
    set_doc()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "291-ЭОМ.pdf")
