"""Генерация графической части 291-ОВК (PDF, листы А3)."""
import math
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Polygon

from ovk_data import PROJECT, CLIMATE, duct_d, HOOD_FLOW, HOOD_COMP
from make_plans import (plan_floor1_vent, plan_floor2_vent, plan_attic, plan_floor1_ac,
                        plan_floor2_ac)
from ovk_spec import (ROOMS, TOT, AC, AC_SYS, spec_rows, p1_heater, p2_heater, tubes,
                      branch_info, p1_rooms, v1_rooms)

plt.rcParams["font.family"] = "DejaVu Sans"
W, H = 420, 297
RED, BLUE, GREEN, GRAY, MAG = "#c62828", "#1565c0", "#2e7d32", "#555555", "#6a1b9a"

SHEETS = [
    "Общие данные (начало)",
    "Общие данные (окончание). Характеристика систем",
    "Расчёт воздухообмена по помещениям",
    "План 1 этажа. Вентиляция",
    "План 2 этажа. Вентиляция",
    "План чердака. Вентиляция",
    "План 1 этажа. Кондиционирование",
    "План 2 этажа. Кондиционирование",
    "Принципиальная схема системы П1",
    "Принципиальная схема системы В1",
    "Принципиальные схемы систем П2, В3, В2, ЕВ1, ПЕ1, ПЕ2",
    "Принципиальные схемы систем К1, К2",
    "Спецификация оборудования, изделий и материалов",
    "Спецификация оборудования, изделий и материалов (окончание)",
    "Задание смежным разделам (АР, КД, ЭОМ, ВК)",
]


def new_sheet(n, title):
    fig = plt.figure(figsize=(W / 25.4, H / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")
    lw = 0.8
    ax.add_patch(Rectangle((20, 5), W - 25, H - 10, fill=False, lw=lw))
    stamp(ax, n, title, full=(n == 1))
    return fig, ax


def stamp(ax, n, title, full):
    x0, y0 = W - 5 - 185, 5
    h = 55 if full else 40
    ax.add_patch(Rectangle((x0, y0), 185, h, fill=False, lw=0.8))
    # левая часть — графы изменений и подписей
    cols = [0, 7, 17, 27, 42, 57, 65]
    for c in cols[1:]:
        ax.plot([x0 + c, x0 + c], [y0 + h - 25 if not full else y0, y0 + h], lw=0.4, c="k")
    for i in range(1, 11 if full else 8):
        y = y0 + i * 5
        if y < y0 + h:
            ax.plot([x0, x0 + 65], [y, y], lw=0.3, c="k")
    ax.plot([x0 + 65, x0 + 65], [y0, y0 + h], lw=0.8, c="k")
    hdr_y = y0 + h - 30 if full else y0 + h - 25
    for t, c in zip(["Изм.", "Кол.уч", "Лист", "№док.", "Подп.", "Дата"], cols):
        ax.text(x0 + c + 0.8, hdr_y + 1.2, t, fontsize=4.2)
    people = [("Разраб.", ""), ("Проверил", ""), ("ГИП", ""), ("Н.контр.", "")]
    for i, (role, nm) in enumerate(people):
        y = hdr_y - 5 * (i + 1) + 1.2
        if y > y0:
            ax.text(x0 + 0.8, y, role, fontsize=4.2)
            ax.text(x0 + 17.8, y, nm, fontsize=4.2)
    # правая часть
    xr = x0 + 65
    ax.plot([xr, x0 + 185], [y0 + h - 15, y0 + h - 15], lw=0.8, c="k")
    ax.text(xr + 60, y0 + h - 7.5, PROJECT["code"], ha="center", va="center", fontsize=10,
            weight="bold")
    if full:
        ax.plot([xr, x0 + 185], [y0 + h - 30, y0 + h - 30], lw=0.8, c="k")
        ax.text(xr + 60, y0 + h - 22.5, PROJECT["name"] + "\n" + PROJECT["address"],
                ha="center", va="center", fontsize=4.6)
    yb = y0 + h - (30 if full else 15)
    ax.plot([xr + 70, xr + 70], [y0, yb], lw=0.8, c="k")
    ax.plot([xr + 70, x0 + 185], [yb - 5, yb - 5], lw=0.5, c="k")
    ax.plot([xr + 70, x0 + 185], [yb - 10, yb - 10], lw=0.5, c="k")
    for c in (85, 100):
        ax.plot([xr + c, xr + c], [yb - 10, yb], lw=0.5, c="k")
    ax.text(xr + 77.5, yb - 3.5, "Стадия", ha="center", fontsize=4.2)
    ax.text(xr + 92.5, yb - 3.5, "Лист", ha="center", fontsize=4.2)
    ax.text(xr + 110, yb - 3.5, "Листов", ha="center", fontsize=4.2)
    ax.text(xr + 77.5, yb - 8.5, PROJECT["stage"], ha="center", fontsize=6)
    ax.text(xr + 92.5, yb - 8.5, str(n), ha="center", fontsize=6)
    if n == 1:
        ax.text(xr + 110, yb - 8.5, str(len(SHEETS)), ha="center", fontsize=6)
    ax.text(xr + 35, (y0 + yb) / 2, title, ha="center", va="center", fontsize=5.6, wrap=True)
    ax.text(W - 5, 2, "Формат А3", ha="right", fontsize=5)


def table(ax, x, y, widths, rows, rh=5.0, fs=5.8, header_rows=1, aligns=None, bold_rows=()):
    """Рисует таблицу; y — верх таблицы. Возвращает нижнюю координату."""
    total_w = sum(widths)
    cy = y
    for ri, row in enumerate(rows):
        lines = max(str(c).count("\n") + 1 for c in row) if row and row[0] != "#" else 1
        h = rh * lines if ri >= header_rows else rh * max(lines, 1)
        if row and row[0] == "#":
            ax.add_patch(Rectangle((x, cy - h), total_w, h, fill=False, lw=0.4))
            ax.text(x + total_w / 2, cy - h / 2, row[1], ha="center", va="center", fontsize=fs,
                    weight="bold")
            cy -= h
            continue
        cx = x
        for ci, (w, c) in enumerate(zip(widths, row)):
            ax.add_patch(Rectangle((cx, cy - h), w, h, fill=False, lw=0.4))
            al = "center" if ri < header_rows else (aligns[ci] if aligns else "left")
            tx = cx + (w / 2 if al == "center" else 1.0)
            ax.text(tx, cy - h / 2, str(c), ha=al, va="center", fontsize=fs,
                    weight="bold" if (ri < header_rows or ri in bold_rows) else "normal")
            cx += w
        cy -= h
    return cy


def wrap(s, n):
    words, lines, cur = s.split(), [], ""
    for w_ in words:
        if len(cur) + len(w_) + 1 > n:
            lines.append(cur)
            cur = w_
        else:
            cur = (cur + " " + w_).strip()
    if cur:
        lines.append(cur)
    return "\n".join(lines)


# ----------------------------------------------------------------- лист 1
GENERAL_NOTES = [
    "Рабочая документация раздела «Вентиляция и кондиционирование воздуха» разработана на "
    "основании архитектурно-планировочных решений (АПР «Берта Ромарио», ООО «Строй Хауз», 2026) и "
    "конструктивных разделов КЖ0, КД1–КД5.",
    "Здание — двухэтажный индивидуальный жилой дом (класс Ф1.4) из клееного бруса 240 мм, "
    "фундамент — ж/б плита на забивных сваях, кровля — фальцевая с утеплением, чердак "
    "холодный (низ перекрытия +7,900). Площадь здания 488 м².",
    f"Расчётные параметры наружного воздуха (СП 131.13330.2020, г. Москва): холодный период "
    f"tн={CLIMATE['t_winter']:.0f} °C; тёплый период для кондиционирования tн=+{CLIMATE['t_summer']:.0f} °C.",
    "Параметры внутреннего воздуха (ГОСТ 30494-2011): зима +20…+22 °C; лето (в "
    "кондиционируемых помещениях) +23±1 °C.",
    "Воздухообмены приняты по СП 54.13330.2022 табл. 9.1, СП 55.13330.2016, СП 60.13330.2020 "
    "(прил. К), см. лист 3.",
    "Вентиляция дома — механическая приточно-вытяжная с рекуперацией теплоты (система П1В1). "
    "Установка размещается на чердаке на виброопорах, с площадкой обслуживания.",
    "Разводка по 2 этажу — круглыми воздуховодами из оцинкованной стали по чердаку с выпуском "
    "через чердачное перекрытие в потолочные диффузоры. Разводка по 1 этажу — гибкими "
    "полимерными воздуховодами Ø90 (лучевая схема) в пространстве межэтажного перекрытия "
    "между балками от распределительных коллекторов в вентиляционных коробах.",
    "Отверстия в балках перекрытия выполнять только в местах, допускаемых производителем "
    "двутавровых балок (ТУ 5366-002-79366690-2010) и по согласованию с разработчиком КД4. "
    "Прорезка клееных балок и бруса не допускается.",
    "Клееный брус даёт усадку по высоте до 1,5%. Вертикальные участки воздуховодов, фреоновых и "
    "дренажных трубопроводов, проходящие через перекрытия и примыкающие к брусовым стенам, "
    "выполнять с компенсаторами усадки (гибкие вставки, скользящие муфты, гильзы с зазором "
    "не менее 50 мм).",
    "Кухонный зонт (В3) — автономная система с выбросом через кровлю и обратным клапаном. "
    "Компенсация — приточной установкой П2, сблокированной с зонтом.",
    "Сауна — отдельная вытяжка В2 термостойким вентилятором; приток — переток из зоны отдыха.",
    "Котельная — естественная вытяжка ЕВ1 и приток ПЕ1. Тип теплогенератора уточняется; при "
    "газовом котле воздухообмен проверить по СП 282.1325800 и паспорту котла.",
    "Камин — подача наружного воздуха на горение к топке (ПЕ2) по паспорту топки.",
    "Кондиционирование — две системы мини-VRF: К1 (1 этаж), К2 (2 этаж). Наружные блоки — на "
    "опорах у фасада. Дренаж от внутренних блоков — в канализацию через гидрозатворы (сухие "
    "затворы).",
    "Транзитные воздуховоды, проходящие через холодный чердак, теплоизолировать (приток — 19 мм, "
    "наружный воздух и выброс — 32 мм с паронепроницаемым покрытием).",
    "Уровень шума в жилых комнатах — не выше 30 дБА ночью (СП 51.13330.2011). Скорость в "
    "ответвлениях — не более 3 м/с, в магистралях — не более 5 м/с.",
    "При срабатывании автономных пожарных извещателей / системы сигнализации установки П1В1, П2 "
    "отключаются.",
    "Монтаж, испытания и наладку выполнять по СП 73.13330.2016 и инструкциям производителей.",
]


def sheet1(pdf):
    fig, ax = new_sheet(1, "Общие данные (начало)")
    ax.text(30, 285, "Ведомость рабочих чертежей основного комплекта", fontsize=7, weight="bold")
    rows = [("Лист", "Наименование", "Примечание")] + [(str(i + 1), s, "") for i, s in
                                                       enumerate(SHEETS)]
    yb = table(ax, 25, 282, [15, 110, 25], rows, rh=5)
    ax.text(30, yb - 6, "Ведомость ссылочных и прилагаемых документов", fontsize=7, weight="bold")
    refs = [("Обозначение", "Наименование", "Прим."),
            ("СП 60.13330.2020", "Отопление, вентиляция и кондиционирование воздуха", ""),
            ("СП 54.13330.2022", "Здания жилые многоквартирные (табл. 9.1)", ""),
            ("СП 55.13330.2016", "Дома жилые одноквартирные", ""),
            ("СП 131.13330.2020", "Строительная климатология", ""),
            ("СП 73.13330.2016", "Внутренние санитарно-технические системы зданий", ""),
            ("СП 7.13130.2013", "ОВиК. Противопожарные требования", ""),
            ("СП 51.13330.2011", "Защита от шума", ""),
            ("ГОСТ 30494-2011", "Параметры микроклимата в помещениях", ""),
            ("ГОСТ 21.602-2016", "Правила выполнения РД ОВиК", ""),
            ("291-ОВК.РПЗ", "Расчётно-пояснительная записка (прилагается)", "docx"),
            ("291-ОВК.Р", "Таблицы расчётов (прилагается)", "xlsx")]
    table(ax, 25, yb - 9, [32, 103, 15], refs, rh=5)

    ax.text(185, 285, "Общие указания", fontsize=7, weight="bold")
    y = 280
    for i, t in enumerate(GENERAL_NOTES[:11], 1):
        txt = wrap(f"{i}. {t}", 88)
        ax.text(185, y, txt, fontsize=6.4, va="top")
        y -= 3.55 * (txt.count("\n") + 1) + 1.6
    pdf.savefig(fig)
    plt.close(fig)


def sheet2(pdf):
    fig, ax = new_sheet(2, "Общие данные (окончание). Характеристика систем")
    ax.text(25, 285, "Общие указания (окончание)", fontsize=7, weight="bold")
    y = 280
    for i, t in enumerate(GENERAL_NOTES[11:], 12):
        txt = wrap(f"{i}. {t}", 105)
        ax.text(25, y, txt, fontsize=6.2, va="top")
        y -= 3.45 * (txt.count("\n") + 1) + 1.4

    t_after, q1 = p1_heater()
    q2 = p2_heater()
    ax.text(25, y - 4, "Характеристика систем вентиляции", fontsize=7, weight="bold")
    rows = [("Система", "Обслуживаемые помещения", "Оборудование", "L, м³/ч", "Pсв, Па",
             "Nнагр, кВт", "Место")]
    rows += [
        ("П1", "Жилые комнаты, кухня-столовая,\nприхожая, холл, зона отдыха", "ПВУ роторн.", TOT["П1"],
         250, f"{math.ceil(q1 * 2) / 2:.1f}", "Чердак"),
        ("В1", "С/У, гардеробные, кладовые,\nпостирочные, кухня, холл (верх)", "ПВУ роторн.",
         TOT["В1"], 250, "—", "Чердак"),
        ("П2", "Кухня-столовая (компенсация зонта)", "Прит. уст.", HOOD_COMP, 200,
         f"{math.ceil(q2):.0f}", "Чердак"),
        ("В3", "Кухонный зонт", "Зонт с вент.", HOOD_FLOW, "—", "—", "Кухня"),
        ("В2", "Сауна (режим просушки)", "Вент. канал.", TOT["В2"], 150, "—", "Чердак"),
        ("ЕВ1", "Котельная", "Естеств.", TOT["ЕВ1"], "—", "—", "—"),
        ("ПЕ1", "Котельная", "Естеств.", TOT["ПЕ1"], "—", "—", "—"),
        ("ПЕ2", "Камин (воздух на горение)", "Естеств.", "по паспорту", "—", "—", "—"),
    ]
    yb = table(ax, 25, y - 7, [16, 62, 22, 16, 14, 16, 16], rows, rh=5, fs=5)

    ax.text(25, yb - 6, "Характеристика систем кондиционирования", fontsize=7, weight="bold")
    rows = [("Система", "Зона", "Qрасч, кВт", "Qрасч×0,85", "ΣQвб, кВт", "Qнб, кВт", "Загрузка, %")]
    for s in AC_SYS:
        rows.append((s["sys"], "1 этаж" if s["sys"] == "К1" else "2 этаж", s["q"], s["q_div"],
                     s["sum_units"], s["outdoor"], s["ratio"]))
    table(ax, 25, yb - 9, [18, 30, 22, 22, 22, 22, 22], rows, rh=5, fs=5)

    # условные обозначения
    ax.text(225, 285, "Условные обозначения", fontsize=7, weight="bold")
    items = [
        (RED, "-", "Воздуховод приточный"),
        (BLUE, "-", "Воздуховод вытяжной"),
        (GREEN, "-", "Воздуховод наружного воздуха / выброса"),
        (RED, ":", "Гибкий воздуховод Ø90 (приток)"),
        (BLUE, ":", "Гибкий воздуховод Ø90 (вытяжка)"),
        (MAG, "-", "Фреонопровод (жидкость/газ)"),
        (GRAY, "--", "Дренаж конденсата"),
    ]
    y = 278
    for c, ls, t in items:
        ax.plot([228, 248], [y, y], c=c, ls=ls, lw=1.4)
        ax.text(252, y, t, va="center", fontsize=5.5)
        y -= 6
    sym = [("ДПУ", "Диффузор потолочный"), ("РК", "Распределительный коллектор"),
           ("ШГ", "Шумоглушитель"), ("КВ", "Клапан воздушный с эл. приводом"),
           ("ОК", "Клапан обратный"), ("ДК", "Дроссель-клапан"), ("ВБ", "Внутренний блок VRF"),
           ("НБ", "Наружный блок VRF"), ("Р", "Разветвитель (рефнет)")]
    for a, t in sym:
        ax.add_patch(Rectangle((228, y - 2), 20, 4, fill=False, lw=0.6))
        ax.text(238, y, a, ha="center", va="center", fontsize=5)
        ax.text(252, y, t, va="center", fontsize=5.5)
        y -= 6
    pdf.savefig(fig)
    plt.close(fig)


def sheet3(pdf):
    fig, ax = new_sheet(3, "Расчёт воздухообмена по помещениям")
    ax.text(25, 287, "Расчёт воздухообмена по помещениям", fontsize=7, weight="bold")
    hdr = ("Эт.", "№", "Наименование", "S, м²", "h, м", "V, м³", "Приток\nм³/ч", "Сист.",
           "Вытяжка\nм³/ч", "Сист.", "Обоснование")
    rows = [hdr]
    for r in ROOMS:
        rows.append((r["floor"], r["num"], r["name"], f"{r['area']:.2f}", f"{r['h']:.2f}",
                     f"{r['v']:.1f}", r["sup"] or "—", r["sup_sys"] or "—", r["exh"] or "—",
                     r["exh_sys"] or "—", r["basis"]))
    rows.append(("", "", "ИТОГО П1 / В1", "", "", "", TOT["П1"], "П1", TOT["В1"], "В1",
                 "Баланс П1 = В1"))
    yb = table(ax, 22, 284, [8, 8, 58, 15, 12, 15, 16, 12, 16, 12, 125], rows, rh=5.6, fs=5.6,
               bold_rows=(len(rows) - 1,))
    ax.text(25, yb - 5, wrap(
        "Примечания: 1. Холл-лестница со вторым светом: объём принят до низа чердачного перекрытия "
        "(+7,900); вытяжка из верхней зоны назначена по балансу П1=В1. 2. Помещения 2 этажа №1, 2, 9 "
        "(холлы) вентилируются перетоком. 3. Двери С/У, гардеробных, кладовых, постирочных — с "
        "подрезом 20 мм или переточными решётками.", 200), fontsize=6, va="top")
    pdf.savefig(fig)
    plt.close(fig)


# ------------------------------------------------- принципиальные схемы П1/В1
def room_box(ax, x, y, w, h, r, flow, label, color):
    ax.add_patch(Rectangle((x, y), w, h, fill=False, lw=0.6, ec="k"))
    ax.text(x + w / 2, y + h - 2.5, wrap(f"{r['num']}. {r['name']}", 18), ha="center", va="top",
            fontsize=5.6)
    ax.text(x + w / 2, y + 2.5, f"L={flow} м³/ч\n{label}", ha="center", va="bottom",
            fontsize=5.8, color=color, weight="bold")


def sys_scheme(pdf, n, title, sysname, color, rooms2, rooms1, key):
    fig, ax = new_sheet(n, title)
    ax.text(25, 287, f"Принципиальная схема системы {sysname}", fontsize=8, weight="bold")
    # уровни
    levels = [("Чердак (+7,900)", 222, 270), ("2 этаж (+4,500)", 152, 218),
              ("1 этаж (±0,000)", 72, 148)]
    for t, y0, y1 in levels:
        ax.add_patch(Rectangle((25, y0), 385, y1 - y0, fill=False, lw=0.4, ls="--", ec=GRAY))
        ax.text(398, y1 - 4, t, fontsize=6.5, color=GRAY, ha="right")
    # установка
    ax.add_patch(Rectangle((32, 236), 34, 18, fc="#eeeeee", ec="k", lw=0.8))
    ax.text(49, 245, "П1В1\nПВУ роторная\n1050 м³/ч", ha="center", va="center", fontsize=5.5)
    # наружный воздух / выброс
    ax.plot([40, 40], [254, 266], c=GREEN, lw=2)
    ax.plot([58, 58], [254, 266], c=GREEN, lw=2)
    ax.text(40, 268, "Наружный\nвоздух Ø315", ha="center", fontsize=5.2, color=GREEN)
    ax.text(58, 268, "Выброс\nØ315", ha="center", fontsize=5.2, color=GREEN)
    for xs in (40, 58):
        ax.add_patch(Rectangle((xs - 3, 257), 6, 4, fc="w", ec="k", lw=0.5))
        ax.text(xs, 259, "КВ", ha="center", va="center", fontsize=4)
    # магистраль
    ymain = 230
    xstart = 66
    ax.add_patch(Rectangle((66, 241), 12, 6, fc="w", ec="k", lw=0.5))
    ax.text(72, 244, "ШГ", ha="center", va="center", fontsize=4.5)
    ax.plot([78, 84, 84], [244, 244, ymain], c=color, lw=2)
    total = sum(r[key] for r in rooms2) + sum(r[key] for r in rooms1)
    sum1 = sum(r[key] for r in rooms1)
    # ветка на 1 этаж через короб
    xr = 92
    remaining = total
    d, v = duct_d(remaining, 5.0)
    ax.plot([84, xr], [ymain, ymain], c=color, lw=2)
    ax.text(86, ymain + 1.5, f"Ø{d}\n{remaining}", fontsize=5.2, color=color)
    # стояк
    d1, v1 = duct_d(sum1, 4.0)
    ax.plot([xr, xr], [ymain, 110], c=color, lw=1.8)
    rk = "РК1, РК3" if key == "sup" else "РК2, РК4"
    ax.text(xr + 1.5, 190, f"Стояки в коробах\nВК-1, ВК-4\nΣL={sum1} м³/ч\n(компенсаторы\nусадки)",
            fontsize=5.4, color=color)
    # коллекторы 1 этажа
    ntubes = sum(branch_info(r, r[key], 1)[1] for r in rooms1)
    nk = math.ceil(ntubes / 10)
    ax.add_patch(Rectangle((xr - 6, 102), 12, 8, fc="w", ec="k", lw=0.6))
    ax.text(xr, 106, rk, ha="center", va="center", fontsize=4.2)
    ax.text(xr - 6, 99, f"{ntubes} лин. Ø90", fontsize=5.2, color=color)
    # помещения 1 этажа
    n1 = len(rooms1)
    if n1:
        bw = min(40, (410 - 110) / n1 - 4)
        for i, r in enumerate(rooms1):
            x = 110 + i * (bw + 4)
            lab, k = branch_info(r, r[key], 1)
            room_box(ax, x, 76, bw, 22, r, r[key], lab, color)
            xm = x + bw / 2
            ax.plot([xr + 6, xm, xm], [106 - i * 0.6, 106 - i * 0.6, 98], c=color, lw=0.9, ls=":")
    # магистраль по чердаку на 2 этаж
    remaining -= sum1
    n2 = len(rooms2)
    if n2:
        bw = min(40, (410 - 110) / n2 - 4)
        xprev = xr
        for i, r in enumerate(rooms2):
            x = 110 + i * (bw + 4)
            xm = x + bw / 2
            d, v = duct_d(remaining, 5.0)
            ax.plot([xprev, xm], [ymain, ymain], c=color, lw=2 if remaining > 300 else 1.4)
            ax.text((xprev + xm) / 2, ymain + 1.5, f"Ø{d}  {remaining}", ha="center",
                    fontsize=5.2, color=color)
            lab, _ = branch_info(r, r[key], 2)
            ax.plot([xm, xm], [ymain, 180], c=color, lw=1.1)
            ax.add_patch(Rectangle((xm - 2.5, 205), 5, 3, fc="w", ec="k", lw=0.4))
            ax.text(xm + 3, 206.5, "ДК", fontsize=4)
            room_box(ax, x, 156, bw, 24, r, r[key], lab + " ДПУ", color)
            remaining -= r[key]
            xprev = xm
    ax.text(25, 62, wrap(
        "Примечания: 1. Схема принципиальная, без масштаба. Трассировку см. листы 4–6. 2. Диаметры магистралей подобраны при v≤5 м/с, ответвлений — "
        "v≤3 м/с; разводка 1 этажа — гибкими воздуховодами Ø90 (не более 35 м³/ч на линию). "
        "3. Наладку выполнить дроссель-клапанами и регуляторами коллекторов на расходы, "
        "указанные на схеме, с допуском ±10%.", 220), fontsize=6, va="top")
    pdf.savefig(fig)
    plt.close(fig)


def sheet6(pdf):
    fig, ax = new_sheet(11, "Принципиальные схемы систем П2, В3, В2, ЕВ1, ПЕ1, ПЕ2")
    t_after, q1 = p1_heater()
    q2 = p2_heater()

    def block(x, y, title):
        ax.text(x, y, title, fontsize=7, weight="bold")

    def box(x, y, w, h, t, fs=5):
        ax.add_patch(Rectangle((x, y), w, h, fc="w", ec="k", lw=0.6))
        ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs)

    # П2 + В3
    block(28, 282, "Системы П2 / В3 — кухонный зонт и компенсация")
    ax.plot([45, 45], [265, 270], c=GREEN, lw=2)
    ax.text(45, 271, "Наружный воздух Ø200", ha="center", fontsize=5.4, color=GREEN)
    box(37, 250, 16, 14, f"П2\n{HOOD_COMP} м³/ч\n{math.ceil(q2)} кВт")
    ax.plot([45, 45, 70, 70], [250, 240, 240, 200], c=RED, lw=1.8)
    ax.text(72, 225, "Ø200, утепл. δ32\nчерез вент. короб", fontsize=5.4, color=RED)
    box(60, 192, 20, 8, "Решётка\n400×150")
    ax.plot([110, 110], [200, 270], c=BLUE, lw=1.8)
    box(100, 192, 20, 8, f"В3 зонт\n{HOOD_FLOW} м³/ч")
    box(105, 245, 10, 5, "ОК", 4.5)
    ax.text(112, 272, "Выброс выше кровли Ø200", fontsize=5.4, color=BLUE)
    ax.text(28, 186, wrap("Блокировка: включение зонта → открытие клапана и пуск П2 (реле тока "
                          "или сухой контакт зонта). Кухня-столовая, 1 этаж.", 70),
            fontsize=6, va="top")

    # В2 сауна
    block(160, 282, "Система В2 — сауна")
    box(175, 192, 22, 10, "Сауна\nкл. вытяжной\nØ125", 4.6)
    ax.plot([186, 186], [202, 268], c=BLUE, lw=1.6)
    box(180, 235, 12, 8, f"В2\n{TOT['В2']}", 4.6)
    box(181, 250, 10, 5, "ОК", 4.5)
    ax.text(188, 271, "Выброс Ø125 (нерж.)", fontsize=5.4, color=BLUE)
    box(210, 192, 22, 10, "Зона отдыха\n(приток П1)", 4.6)
    ax.annotate("", xy=(197, 197), xytext=(210, 197),
                arrowprops=dict(arrowstyle="->", color=RED, lw=0.8))
    ax.text(196, 186, wrap("Приток в сауну — перетоком через решётку в нижней зоне двери/стены "
                           "у каменки; вытяжка — из верхней зоны противоположной стены. "
                           "Режим: работа во время парения на 30% и просушка 30–60 мин после.",
                           60), fontsize=6, va="top")

    # ЕВ1/ПЕ1 котельная
    block(28, 160, "Системы ЕВ1, ПЕ1 — котельная (естественные)")
    ax.add_patch(Rectangle((40, 90), 60, 50, fill=False, lw=0.8))
    ax.text(70, 115, "Котельная\n11,21 м²", ha="center", va="center", fontsize=5.5)
    ax.plot([90, 90], [130, 156], c=BLUE, lw=1.8)
    ax.text(92, 150, f"ЕВ1 Ø200, L={TOT['ЕВ1']}\nс дефлектором", fontsize=5.4, color=BLUE)
    ax.annotate("", xy=(48, 95), xytext=(30, 95),
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.2))
    ax.text(28, 98, f"ПЕ1 300×200\nL={TOT['ПЕ1']}", fontsize=5.4, color=GREEN)

    # ПЕ2 камин
    block(160, 160, "Система ПЕ2 — воздух на горение камина")
    box(200, 100, 30, 18, "Топка камина\n(гостиная)", 5)
    ax.plot([165, 200], [109, 109], c=GREEN, lw=1.6)
    ax.text(166, 112, "Ø125 с заслонкой\nот наружной решётки", fontsize=5.4, color=GREEN)
    ax.text(160, 92, wrap("Сечение и место подключения — по паспорту топки. Учитывать "
                          "работу П1В1 в режиме «Камин» (временный дисбаланс в пользу притока) "
                          "для исключения опрокидывания тяги.", 60), fontsize=6, va="top")
    pdf.savefig(fig)
    plt.close(fig)


def sheet7(pdf):
    fig, ax = new_sheet(12, "Принципиальные схемы систем К1, К2")
    pipes = {2.2: "6,35/9,52", 2.8: "6,35/9,52", 3.6: "6,35/12,7", 4.5: "6,35/12,7",
             5.6: "6,35/15,88", 7.1: "9,52/15,88"}
    main = {22.4: "9,52/19,05", 12.1: "9,52/15,88", 14.0: "9,52/15,88"}
    for si, s in enumerate(AC_SYS):
        y0 = 270 - si * 120
        ax.text(25, y0 + 12, f"Система {s['sys']} ({'1' if s['sys'] == 'К1' else '2'} этаж) — "
                f"наружный блок {s['outdoor']} кВт, загрузка {s['ratio']}%", fontsize=7,
                weight="bold")
        ax.add_patch(Rectangle((30, y0 - 40), 30, 22, fc="#eeeeee", ec="k", lw=0.8))
        ax.text(45, y0 - 29, f"НБ{s['sys'][1]}\nQх={s['outdoor']} кВт\nу фасада", ha="center",
                va="center", fontsize=6)
        units = s["units"]
        n = len(units)
        bw = min(42, (400 - 100) / n - 5)
        ymain = y0 - 29
        ax.plot([60, 95], [ymain, ymain], c=MAG, lw=2)
        ax.text(62, ymain + 1.5, main.get(s["outdoor"], "по ПО"), fontsize=5.6, color=MAG)
        for i, a in enumerate(units):
            x = 100 + i * (bw + 5)
            xm = x + bw / 2
            ax.plot([95 if i == 0 else xm - bw - 5, xm], [ymain, ymain], c=MAG, lw=1.6)
            if i < n - 1:
                ax.add_patch(Rectangle((xm - 2, ymain - 1.5), 4, 3, fc="w", ec=MAG, lw=0.6))
                ax.text(xm, ymain + 2.5, "Р", ha="center", fontsize=5, color=MAG)
            ax.plot([xm, xm], [ymain, y0 - 55], c=MAG, lw=1)
            ax.text(xm + 1, ymain - 13, pipes[a["unit"]], fontsize=5.4, color=MAG, rotation=90)
            ax.add_patch(Rectangle((x, y0 - 80), bw, 25, fill=False, lw=0.6))
            ax.text(xm, y0 - 58, f"{a['mark']} {a['unit_type']}\nQх={a['unit']} кВт\n"
                    f"(расч. {a['q']} кВт)", ha="center", va="top", fontsize=5.6)
            ax.text(xm, y0 - 78, wrap(f"пом. {a['num']}. {a['name']}", 20), ha="center",
                    va="bottom", fontsize=5.4)
            ax.plot([xm + 3, xm + 3], [y0 - 80, y0 - 90], c=GRAY, lw=0.8, ls="--")
        ax.plot([100, 100 + n * (bw + 5)], [y0 - 90, y0 - 90], c=GRAY, lw=0.8, ls="--")
        ax.text(100 + n * (bw + 5) + 2, y0 - 90, "Дренаж в канализацию\nчерез сухой затвор",
                fontsize=5.6, color=GRAY, va="center")
    ax.text(25, 30, wrap(
        "Примечания: 1. Диаметры фреонопроводов (жидкость/газ, мм) даны ориентировочно; "
        "окончательно — по программе подбора производителя выбранной марки. 2. Холодильные "
        "нагрузки определены по укрупнённым показателям (Вт/м²) с учётом людей и бытового "
        "оборудования с повышенными показателями для помещений с панорамным остеклением. "
        "3. Прокладку фреонопроводов через перекрытия выполнять в гильзах с компенсацией усадки "
        "бруса. 4. Размещение блоков и трассы — см. листы 7, 8.", 150), fontsize=6, va="top")
    pdf.savefig(fig)
    plt.close(fig)


def sheet8(pdf):
    rows = spec_rows()
    data = []
    for r in rows:
        if r[0] == "#":
            data.append(r)
        else:
            data.append((r[0], wrap(r[1], 105), r[2], r[3], r[4], r[5]))
    split = next(i for i, r in enumerate(data) if r[0] == "#" and "К1" in r[1])
    hdr = ("Поз.", "Наименование и техническая характеристика", "Тип, марка", "Ед.",
           "Кол.", "Примечание")
    for n, part, ttl in ((13, data[:split], "Спецификация оборудования, изделий и материалов"),
                         (14, data[split:], "Спецификация (окончание)")):
        fig, ax = new_sheet(n, ttl)
        ax.text(25, 287, ttl + " (ГОСТ 21.110-2013)", fontsize=7.5, weight="bold")
        table(ax, 22, 284, [14, 190, 44, 13, 13, 114], [hdr] + part, rh=4.4, fs=5.3,
              aligns=["center", "left", "left", "center", "center", "left"])
        pdf.savefig(fig)
        plt.close(fig)


def sheet15(pdf):
    import ovk_plan as G
    t_after, q1 = p1_heater()
    q2 = p2_heater()
    fig, ax = new_sheet(15, SHEETS[14])
    ax.text(25, 287, "Задание смежным разделам", fontsize=8, weight="bold")
    ax.text(25, 279, "АР / КД — вентиляционные короба и отверстия", fontsize=6.5, weight="bold")
    rows = [("Короб", "Оси (≈)", "Внутр. размер, мм", "Этажи", "Назначение")]
    for k, s in G.SHAFTS.items():
        x, y = s["pt"]
        ax_ = min(G.AXES_X, key=lambda a: abs(G.AXES_X[a] - x))
        ay_ = min(G.AXES_Y, key=lambda a: abs(G.AXES_Y[a] - y))
        rows.append((k, f"{ax_}/{ay_}", s["size"], "1 эт. (перекр.) – 2 эт. – чердак",
                     s["use"]))
    yb = table(ax, 25, 276, [16, 18, 26, 50, 110], rows, rh=5, fs=5.4)
    other = [
        "Проходы через чердачное перекрытие к диффузорам 2 этажа: 14 шт. Ø125…Ø250 (см. лист 6), "
        "с гильзами и проклейкой пароизоляции.",
        "Проходы через кровлю (фальц): П1 наружный воздух Ø315, выброс П1В1 Ø315, П2 Ø200, "
        "В3 Ø200, В2 Ø125, ЕВ1 Ø200 — проходные элементы с утеплённым основанием.",
        "Площадка обслуживания ПВУ на чердаке 2,5×1,6 м по сдвоенным лагам; нагрузка ≈180 кг.",
        "Отверстия в двутавровых балках перекрытия под гибкие воздуховоды Ø90 (наруж. ≈95 мм) — "
        "около 35 линий; согласовать допустимые зоны с разработчиком КД4.",
        "Решётка ПЕ1 300×200 в наружной стене котельной (h=0,3 м); отверстие Ø125 под ПЕ2 у камина.",
        "Двери С/У, гардеробных, постирочных, кладовых — подрез 20 мм или переточные решётки.",
    ]
    y = yb - 4
    for t in other:
        s_ = wrap("• " + t, 175)
        ax.text(27, y, s_, fontsize=5.6, va="top")
        y -= 3.2 * (s_.count("\n") + 1) + 1
    ax.text(25, y - 3, "ЭОМ — электроснабжение оборудования", fontsize=6.5, weight="bold")
    k1 = next(s for s in AC_SYS if s["sys"] == "К1")
    k2 = next(s for s in AC_SYS if s["sys"] == "К2")
    rows = [("Потребитель", "Место", "Pуст, кВт", "Сеть", "Примечание"),
            ("П1В1 (вентиляторы + эл. нагреватель)", "Чердак",
             f"{0.7 + math.ceil(q1 * 2) / 2:.1f}", "380 В", "Сигнал от пожарных извещателей"),
            ("П2 (вентилятор + эл. нагреватель)", "Чердак", f"{0.2 + math.ceil(q2):.1f}",
             "380 В", "Блокировка с зонтом В3"),
            ("В3 кухонный зонт", "Кухня", "0,3", "230 В", "Сухой контакт → П2"),
            ("В2 вентилятор сауны", "Чердак", "0,1", "230 В", "Выключатель + таймер"),
            ("НБ1 (К1)", "Улица, у котельной", f"{k1['outdoor'] / 3.2:.1f}", "380 В",
             "Отд. автомат, ориентир. по EER 3,2"),
            ("НБ2 (К2)", "Улица, у котельной", f"{k2['outdoor'] / 3.2:.1f}", "380 В",
             "Отд. автомат"),
            ("Внутренние блоки ВБ1…ВБ11", "По планам", "0,05×11", "230 В",
             "Питание от НБ/отд. линии по ПО")]
    yb = table(ax, 25, y - 6, [70, 40, 22, 18, 100], rows, rh=5, fs=5.4)
    ax.text(25, yb - 5, "ВК — дренаж", fontsize=6.5, weight="bold")
    s_ = wrap("• Подключение дренажа 11 внутренних блоков кондиционирования Ø20…32 к "
              "канализации через сухие затворы (гидрозатворы) в ближайших С/У, "
              "постирочных и на кухне. • ПВУ с роторным рекуператором конденсата не даёт, "
              "дренаж не требуется (уточнить по паспорту выбранной установки).", 175)
    ax.text(27, yb - 9, s_, fontsize=5.6, va="top")
    pdf.savefig(fig)
    plt.close(fig)


def main(out):
    with PdfPages(out) as pdf:
        sheet1(pdf)
        sheet2(pdf)
        sheet3(pdf)
        for n, fn in ((4, plan_floor1_vent), (5, plan_floor2_vent), (6, plan_attic),
                      (7, plan_floor1_ac), (8, plan_floor2_ac)):
            fig, ax = new_sheet(n, SHEETS[n - 1])
            fn(fig, ax)
            pdf.savefig(fig)
            plt.close(fig)
        sys_scheme(pdf, 9, "Принципиальная схема системы П1", "П1 (приток)", RED,
                   p1_rooms(2), p1_rooms(1), "sup")
        sys_scheme(pdf, 10, "Принципиальная схема системы В1", "В1 (вытяжка)", BLUE,
                   v1_rooms(2), v1_rooms(1), "exh")
        sheet6(pdf)
        sheet7(pdf)
        sheet8(pdf)
        sheet15(pdf)
        d = pdf.infodict()
        d["Title"] = f"{PROJECT['code']} {PROJECT['section']}"


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "291-ОВК.pdf")
