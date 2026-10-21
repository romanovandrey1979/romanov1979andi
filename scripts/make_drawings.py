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
from ovk_spec import (ROOMS, TOT, AC, AC_SYS, HUMID, spec_rows, p1_heater, p2_heater,
                      branch_info, p1_rooms, v1_rooms, elec_loads, P1_HEATER_KW, P2_HEATER_KW,
                      ETA_ROTOR)

plt.rcParams["font.family"] = "DejaVu Sans"
W, H = 420, 297
RED, BLUE, GREEN, GRAY, MAG = "#c62828", "#1565c0", "#2e7d32", "#555555", "#6a1b9a"

SHEETS = [
    "Общие данные (начало)",
    "Общие данные (окончание). Характеристика систем",
    "Расчёт воздухообмена по помещениям",
    "План 1 этажа. Вентиляция",
    "План 2 этажа. Вентиляция",
    "План чердака. Вентиляция и увлажнение",
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


CUR = {"code": None, "sheets": None}


def set_doc(code=None, sheets=None):
    """Переключает шифр и перечень листов для штампа (для других разделов)."""
    CUR["code"], CUR["sheets"] = code, sheets


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
    ax.text(xr + 60, y0 + h - 7.5, CUR["code"] or PROJECT["code"], ha="center", va="center", fontsize=10,
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
        ax.text(xr + 110, yb - 8.5, str(len(CUR["sheets"] or SHEETS)), ha="center", fontsize=6)
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
    "Статус: концепт заказчика — исходные данные для инженерного проектировщика (стадия «Э»). "
    "Основание: АПР, КЖ0, КД1–КД5 Строй Хауз; пакет исходных заказчика № 83 / Прил. 2 к заданию "
    "(18.10.2026); эскиз БР-ОВК; решения 14.10, 17.10, 18.10.2026. Не для закупки и монтажа.",
    "Здание — двухэтажный индивидуальный жилой дом (Ф1.4) из клееного бруса 240 мм, плита на "
    "забивных сваях, кровля фальцевая, утепление 250 мм; чердак ТЁПЛЫЙ (ответ СХ 18.10). "
    "Отапливаемая площадь 438 м²; высоты этажей 3,7 / 3,4 м; холл со вторым светом.",
    f"Наружный воздух (СП 131.13330.2020, Москва): зима tн={CLIMATE['t_winter']:.0f} °C; "
    f"лето для кондиционирования tн=+{CLIMATE['t_summer']:.0f} °C.",
    "Внутренний воздух (ГОСТ 30494-2011): зима +20…+22 °C, относительная влажность в спальнях "
    "и гостиной не ниже 40 % (паровое увлажнение); лето в кондиционируемых помещениях +23±1 °C.",
    "Воздухообмены — СП 55.13330.2016, СП 60.13330.2020 (прил. К); СП 54.13330.2022 табл. 9.1 "
    "использован справочно. См. лист 3.",
    f"Вентиляция — механическая приточно-вытяжная П1В1 1050/1050 м³/ч с роторным рекуператором "
    f"(η ≥ {ETA_ROTOR:.0%}) на тёплом чердаке над холлом; догрев — водяной калорифер "
    f"{P1_HEATER_KW:.0f} кВт от буфера котельной (гликоль 30 %). Электронагревателей нет.",
    "Разводка 2 этажа — от магистралей на чердаке прямо в потолочные диффузоры. Разводка "
    "1 этажа — из шахт ВК-1, ВК-4 воздуховодами в подшивных потолках, опусках и коробах вдоль "
    "балок к щелевым диффузорам у наружных стен. Сквозных отверстий в двутаврах КД4 нет.",
    "Забор наружного воздуха (К1) и выброс (К2) — через кровлю Ø315, разнос ≈ 5 м (не менее "
    "3 м), до дымоходов котла и камина не менее 5 м; выброс выше забора.",
    "Клееный брус даёт усадку по высоте 3–5 %. Вертикальные участки воздуховодов, фреоновых и "
    "дренажных трубопроводов через перекрытия — с компенсаторами усадки (гибкие вставки, "
    "скользящие муфты, гильзы с зазором ≥ 50 мм), скользящие крепления к брусу.",
    f"Кухонный зонт В3 {HOOD_FLOW} м³/ч — выброс через кровлю с обратным и утеплённым клапаном. "
    f"Компенсация — П2 {HOOD_COMP} м³/ч с водяным калорифером {P2_HEATER_KW:.1f} кВт; зонт "
    f"разрешён только при работающей П2.",
    "Сауна — вытяжка В2 130 м³/ч термостойким вентилятором, воздуховод из нержавеющей стали; "
    "просушка по гигростату; приток — перетоком из зоны отдыха.",
    "Котельная — ЕВ1 Ø200 (в ВК-5, через кровлю, с дефлектором) и ПЕ1 Ø160 через наружную "
    "стену (решётка с утеплённой заслонкой); приток = вытяжка + воздух на горение пеллетного "
    "котла 30 кВт; датчик CO. После перехода на газ — проверить по паспорту газового котла.",
    "Камин — воздух на горение ПЕ2 через решётку 300×150 в наружной стене по оси 7 на уровне "
    "пола (сторона террасы), с утеплённой заслонкой; трубы в плите нет.",
    "Баланс давлений: матрица режимов на листе 2; датчик перепада «помещение — улица» "
    "(порог −5 Па) переводит В1 на сниженный расход и выдаёт сигнал в HA — защита от "
    "опрокидывания тяги камина и котла.",
    "Паровое увлажнение ПУ1–ПУ6 (6 зон: спальни 3, 7, 10, 12, 14; гостиная и кухня) — "
    "6,8 кг/ч при −25 °C и 40 %; пароувлажнители на чердаке, вода после обратного осмоса.",
    "Кондиционирование — две системы мульти-сплит / мини-VRF: К1 (1 этаж), К2 (2 этаж); "
    "внутренние блоки только канальные скрытые. НБ1, НБ2 — на земле в коробе с жалюзи у южной "
    "стены котельной; трассы — через гильзы Ø110 З11, З12 в плите.",
    "Управление: Home Assistant по Modbus TCP/RTU (ПВУ, П2, шлюзы НБ, ПУ); датчики CO₂ + RH "
    "в 5 спальнях и гостиной; ночью расход по CO₂ до 50 %. Облачные сервисы как единственный "
    "канал не допускаются.",
    "Уровень шума в жилых комнатах — не выше 30 дБА ночью (СП 51.13330.2011). Скорость в "
    "ответвлениях — не более 3 м/с, в магистралях — не более 5 м/с.",
    "При срабатывании пожарной сигнализации П1В1 и П2 отключаются.",
    "Монтаж, испытания и наладку выполнять по СП 73.13330.2016 и инструкциям производителей.",
]


N1 = 10


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
    for i, t in enumerate(GENERAL_NOTES[:N1], 1):
        txt = wrap(f"{i}. {t}", 88)
        ax.text(185, y, txt, fontsize=6.4, va="top")
        y -= 3.55 * (txt.count("\n") + 1) + 1.6
    pdf.savefig(fig)
    plt.close(fig)


def sheet2(pdf):
    fig, ax = new_sheet(2, "Общие данные (окончание). Характеристика систем")
    ax.text(25, 285, "Общие указания (окончание)", fontsize=7, weight="bold")
    y = 280
    for i, t in enumerate(GENERAL_NOTES[N1:], N1 + 1):
        txt = wrap(f"{i}. {t}", 105)
        ax.text(25, y, txt, fontsize=5.8, va="top")
        y -= 3.2 * (txt.count("\n") + 1) + 1.2

    t_after, q1 = p1_heater()
    q2 = p2_heater()
    ax.text(25, y - 4, "Характеристика систем вентиляции", fontsize=7, weight="bold")
    rows = [("Система", "Обслуживаемые помещения", "Оборудование", "L, м³/ч", "Pсв, Па",
             "Nнагр, кВт", "Место")]
    rows += [
        ("П1", "Жилые комнаты, кухня-столовая,\nприхожая, холл, зона отдыха", "ПВУ роторн.", TOT["П1"],
         250, f"{P1_HEATER_KW:.0f} (вода)", "Чердак"),
        ("В1", "С/У, гардеробные, кладовые,\nпостирочные, кухня, холл (верх)", "ПВУ роторн.",
         TOT["В1"], 250, "—", "Чердак"),
        ("П2", "Кухня-столовая (компенсация зонта)", "Прит. уст.", HOOD_COMP, 200,
         f"{P2_HEATER_KW:.1f} (вода)", "Чердак"),
        ("В3", "Кухонный зонт", "Зонт с вент.", HOOD_FLOW, "—", "—", "Кухня"),
        ("В2", "Сауна (режим просушки)", "Вент. канал.", TOT["В2"], 150, "—", "Чердак"),
        ("ЕВ1", "Котельная", "Естеств.", TOT["ЕВ1"], "—", "—", "—"),
        ("ПЕ1", "Котельная", "Естеств.", TOT["ПЕ1"], "—", "—", "—"),
        ("ПЕ2", "Камин (воздух на горение)", "Решётка", "по паспорту", "—", "—", "Ось 7"),
    ]
    rows[0] = ("Система", "Обслуживаемые помещения", "Оборудование", "L, м³/ч", "Pсв, Па",
               "Qкал, кВт", "Место")
    yb = table(ax, 25, y - 7, [16, 62, 22, 16, 14, 16, 16], rows, rh=4.6, fs=5)

    ax.text(25, yb - 5, "Характеристика систем кондиционирования", fontsize=7, weight="bold")
    rows = [("Система", "Зона", "Qрасч, кВт", "Qрасч×0,85", "ΣQвб, кВт", "Qнб, кВт", "Загрузка, %")]
    for s in AC_SYS:
        rows.append((s["sys"], "1 этаж" if s["sys"] == "К1" else "2 этаж", s["q"], s["q_div"],
                     s["sum_units"], s["outdoor"], s["ratio"]))
    yb = table(ax, 25, yb - 7, [18, 30, 22, 22, 22, 22, 22], rows, rh=4.6, fs=5)
    ax.text(25, yb - 5, "Матрица режимов и баланс воздуха (защита тяги камина и котла)",
            fontsize=7, weight="bold")
    rows = [("Режим", "П1", "В1", "П2", "В3", "В2", "Баланс", "Мера"),
            ("Норма", 1050, 1050, 0, 0, 0, "0", "—"),
            ("Ночь (по CO₂)", "≥525", "=П1", 0, 0, 0, "0", "П1 = В1"),
            ("Зонт", 1050, 1000, 400, 450, 0, "0", "В1 −50; зонт только с П2"),
            ("Просушка сауны", 1050, 920, 0, 0, 130, "0", "В1 −130 на время В2"),
            ("Зонт + сауна", 1050, 870, 400, 450, 130, "0", "В1 −180"),
            ("Камин", 1050, 950, 0, 0, 0, "+100", "подпор +100"),
            ("Пожар", 0, 0, 0, "—", "—", "—", "отключение П1В1, П2")]
    yb = table(ax, 25, yb - 7, [30, 14, 14, 12, 12, 12, 14, 70], rows, rh=4.4, fs=4.8)
    ax.text(25, yb - 3, wrap("Отрицательный баланс не допускается: при включении В3 и В2 "
                             "контроллер ПВУ снижает В1 на их разницу с притоком; датчик "
                             "перепада −5 Па — аварийный сигнал в HA. П1 не завышать сверх "
                             "1050 м³/ч.", 150), fontsize=5.4, va="top")

    # условные обозначения
    ax.text(225, 285, "Условные обозначения", fontsize=7, weight="bold")
    items = [
        (RED, "-", "Воздуховод приточный"),
        (BLUE, "-", "Воздуховод вытяжной"),
        (GREEN, "-", "Воздуховод наружного воздуха / выброса"),
        (MAG, "-", "Фреонопровод (жидкость/газ)"),
        (GRAY, "--", "Дренаж конденсата"),
    ]
    y = 278
    for c, ls, t in items:
        ax.plot([228, 248], [y, y], c=c, ls=ls, lw=1.4)
        ax.text(252, y, t, va="center", fontsize=5.5)
        y -= 6
    sym = [("ДПУ", "Диффузор потолочный"), ("ДЩ", "Диффузор щелевой линейный"),
           ("ПУ", "Пароувлажнитель канальный"),
           ("ШГ", "Шумоглушитель"), ("КВ", "Клапан воздушный с эл. приводом"),
           ("ОК", "Клапан обратный"), ("ДК", "Дроссель-клапан"), ("ВБ", "Внутренний блок канальный"),
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
    ax.text(xr + 1.5, 190, f"Стояки в шахтах\nВК-1, ВК-4\nΣL={sum1} м³/ч\n(компенсаторы\nусадки)",
            fontsize=5.4, color=color)
    # магистраль 1 этажа в подшивных потолках
    ax.plot([xr, xr], [110, 106], c=color, lw=1.8)
    ax.text(xr + 1.5, 112, "Подшивные потолки / опуски 1 эт.", fontsize=5.0, color=color)
    n1 = len(rooms1)
    if n1:
        bw = min(40, (410 - 110) / n1 - 4)
        for i, r in enumerate(rooms1):
            x = 110 + i * (bw + 4)
            lab, k = branch_info(r, r[key], 1)
            if key != "sup":
                lab = lab.split(",")[0] + " решётка"
            room_box(ax, x, 76, bw, 22, r, r[key], lab, color)
            xm = x + bw / 2
            ax.plot([xr, xm, xm], [106 - i * 0.6, 106 - i * 0.6, 98], c=color, lw=1.0)
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
        "v≤3 м/с; разводка 1 этажа — из шахт ВК-1/ВК-4 в подшивных потолках вдоль балок к щелевым "
        "диффузорам (приток) и потолочным решёткам (вытяжка). Пароувлажнители ПУ1–ПУ6 — на ветках "
        "притока (лист 6). 3. Наладку выполнить дроссель-клапанами на расходы, "
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
    box(37, 250, 16, 14, f"П2\n{HOOD_COMP} м³/ч\nкалор. {P2_HEATER_KW:.1f}\n(вода)", 4.6)
    ax.plot([45, 45, 70, 70], [250, 240, 240, 200], c=RED, lw=1.8)
    ax.text(72, 225, "Ø200, утепл. δ32\nчерез вент. короб", fontsize=5.4, color=RED)
    box(60, 192, 20, 8, "Решётка\n400×150")
    ax.plot([110, 110], [200, 270], c=BLUE, lw=1.8)
    box(100, 192, 20, 8, f"В3 зонт\n{HOOD_FLOW} м³/ч")
    box(105, 245, 10, 5, "ОК", 4.5)
    ax.text(112, 272, "Выброс выше кровли Ø200", fontsize=5.4, color=BLUE)
    ax.text(28, 186, wrap("Блокировка: сухой контакт зонта → открытие утеплённого клапана, пуск П2, "
                          "В1 −50 м³/ч; зонт без П2 не работает. Наружный воздух П2 — К3 через "
                          "кровлю; шумоглушитель Ø200.", 70),
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
                           "Режим: работа при парении на 30 % и просушка по гигростату; "
                           "на время В2 — В1 −130 м³/ч.",
                           60), fontsize=6, va="top")

    # ЕВ1/ПЕ1 котельная
    block(28, 160, "Системы ЕВ1, ПЕ1 — котельная (естественные)")
    ax.add_patch(Rectangle((40, 90), 60, 50, fill=False, lw=0.8))
    ax.text(70, 115, "Котельная\n11,21 м²", ha="center", va="center", fontsize=5.5)
    ax.plot([90, 90], [130, 156], c=BLUE, lw=1.8)
    ax.text(92, 150, f"ЕВ1 Ø200, L={TOT['ЕВ1']}\nс дефлектором", fontsize=5.4, color=BLUE)
    ax.annotate("", xy=(48, 95), xytext=(30, 95),
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.2))
    ax.text(28, 98, f"ПЕ1 Ø160\nреш. 300×200\nL={TOT['ПЕ1']}", fontsize=5.4, color=GREEN)
    ax.text(28, 86, wrap("Приток ПЕ1 = вытяжка ЕВ1 + воздух на горение пеллетного котла 30 кВт; "
                         "датчик CO; ЕВ1 в шахте ВК-5 через кровлю (К6).", 60), fontsize=6, va="top")

    # ПЕ2 камин
    block(160, 160, "Система ПЕ2 — воздух на горение камина")
    box(200, 100, 30, 18, "Топка камина\n(гостиная, ось 7)", 5)
    ax.plot([165, 200], [109, 109], c=GREEN, lw=1.6)
    ax.text(166, 112, "Решётка 300×150 в стене\nоси 7 на уровне пола,\nутеплённая заслонка",
            fontsize=5.4, color=GREEN)
    ax.text(160, 92, wrap("Сечение — по паспорту топки. Режим «Камин»: подпор +100 м³/ч (В1 −100), "
                          "датчик перепада −5 Па. Трубы в плите нет.", 60), fontsize=6, va="top")

    # Увлажнение
    block(255, 282, "Паровое увлажнение ПУ1–ПУ6")
    rows = [("Марка", "Зона", "L, м³/ч", "G расч,\nкг/ч", "ПУ, кг/ч", "N, кВт")]
    for h in HUMID:
        rows.append((h["mark"], wrap(h["zone"], 22), h["flow"], h["g"], h["cap"], h["kw"]))
    rows.append(("Итого", "", sum(h["flow"] for h in HUMID), round(sum(h["g"] for h in HUMID), 1),
                 sum(h["cap"] for h in HUMID), round(sum(h["kw"] for h in HUMID), 1)))
    yb = table(ax, 255, 278, [14, 44, 16, 16, 16, 14], rows, rh=4.6, fs=5, bold_rows=(len(rows) - 1,))
    ax.text(255, yb - 3, wrap("G = L·1,2·(6,6 − 0,4)/1000 (улица −25 °C; помещение +22 °C, 40 %). "
                              "Принято заказчиком 6,8 кг/ч с запасом. Вода — после обратного осмоса "
                              "(котельная), подпитка по ВК-5, дренаж в Ст.К1-4. Управление по "
                              "датчикам RH в зонах, интеграция в HA.", 70), fontsize=5.6, va="top")
    pdf.savefig(fig)
    plt.close(fig)


def sheet7(pdf):
    fig, ax = new_sheet(12, "Принципиальные схемы систем К1, К2")
    pipes = {2.2: "6,35/9,52", 2.8: "6,35/9,52", 3.6: "6,35/12,7", 4.5: "6,35/12,7",
             5.6: "6,35/15,88", 7.1: "9,52/15,88"}
    main = {22.4: "9,52/19,05", 20.0: "9,52/19,05", 18.0: "9,52/19,05", 12.1: "9,52/15,88",
            14.0: "9,52/15,88"}
    for si, s in enumerate(AC_SYS):
        y0 = 270 - si * 120
        ax.text(25, y0 + 12, f"Система {s['sys']} ({'1' if s['sys'] == 'К1' else '2'} этаж) — "
                f"наружный блок {s['outdoor']} кВт, загрузка {s['ratio']}%", fontsize=7,
                weight="bold")
        ax.add_patch(Rectangle((30, y0 - 40), 30, 22, fc="#eeeeee", ec="k", lw=0.8))
        ax.text(45, y0 - 29, f"НБ{s['sys'][1]}\nQх={s['outdoor']} кВт\nкороб, ось Б", ha="center",
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
            ax.text(xm, y0 - 58, f"{a['mark']} канальн.\nQх={a['unit']} кВт\n"
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
        "нагрузки определены по укрупнённым показателям (Вт/м²); типоразмеры блоков — по эскизу "
        "заказчика БР-ОВК: ВБ2 (холл) и ВБ3 (кухня) меньше расчёта — проверить заводским подбором и "
        "покомнатным расчётом теплопритоков. 3. Все внутренние блоки — канальные скрытые. "
        "4. Трассы в дом — через гильзы Ø110 З11, З12 в плите; через перекрытия — в гильзах с "
        "компенсацией усадки. 5. Размещение — листы 7, 8.", 150), fontsize=6, va="top")
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
    fig, ax = new_sheet(15, SHEETS[14])
    ax.text(25, 287, "Задание смежным разделам", fontsize=8, weight="bold")
    ax.text(25, 279, "АР / КД — шахты и проёмы (по эскизу БР-ЗК; координаты ±100 мм уточняет "
            "проектировщик)", fontsize=6.5, weight="bold")
    rows = [("Короб", "Оси (≈)", "Внутр. размер, мм", "Этажи", "Назначение")]
    for k, s in G.SHAFTS.items():
        x, y = s["pt"]
        ax_ = min(G.AXES_X, key=lambda a: abs(G.AXES_X[a] - x))
        ay_ = min(G.AXES_Y, key=lambda a: abs(G.AXES_Y[a] - y))
        rows.append((k, f"{ax_}/{ay_}", s["size"], "1 эт. – 2 эт. – чердак", s["use"]))
    yb = table(ax, 25, 276, [16, 18, 26, 40, 120], rows, rh=4.6, fs=5.4)
    other = [
        "Проходы через кровлю (фальц): К1 забор П1 Ø315, К2 выброс В1 Ø315 (разнос ≈ 5 м), "
        "К3 забор П2 Ø200, К4 выброс В3 Ø200, К5 В2 Ø125, К6 ЕВ1 Ø200 — проходные элементы с "
        "утеплённым основанием; до дымоходов ≥ 5 м.",
        "Проходы через чердачное перекрытие к диффузорам 2 этажа: 14 шт. Ø100…Ø200, с гильзами и "
        "проклейкой пароизоляции.",
        "Площадка обслуживания ПВУ на тёплом чердаке 2,5×1,6 м по сдвоенным лагам (≈ 180 кг); "
        "места ПУ1–ПУ6 (по 15–25 кг) и П2; люк 800×1200 (К12) — подтвердить конструктором СХ.",
        "Отверстий в двутаврах КД4 под вентиляцию 1 этажа НЕТ: разводка в подшивных потолках "
        "и опусках вдоль балок; высоту опусков (≈ 250–300 мм) согласовать с дизайн-проектом.",
        "ПЕ1: Ø160 через наружную стену котельной (ось 13, низ), решётка 300×200 с заслонкой. "
        "ПЕ2: решётка 300×150 в стене по оси 7 на уровне пола. Других проходок ОВК в брусе нет.",
        "Гильзы в плите КЖ0: З11, З12 Ø110 — фреон/дренаж/кабель НБ1, НБ2 (ось Б, 11–13).",
        "Двери С/У, гардеробных, постирочных, кладовых — подрез 20 мм или переточные решётки.",
    ]
    y = yb - 3
    for t in other:
        s_ = wrap("• " + t, 175)
        ax.text(27, y, s_, fontsize=5.4, va="top")
        y -= 3.0 * (s_.count("\n") + 1) + 0.8
    ax.text(25, y - 2, "ЭОМ — электроснабжение оборудования (нагреватели ПВУ и П2 — водяные, в "
            "электрическую нагрузку не входят)", fontsize=6.5, weight="bold")
    loads = elec_loads()
    rows = [("Потребитель", "Pуст, кВт", "Сеть", "Примечание")]
    for nm, kw, net in loads:
        note = {"П1В1": "Сигнал ПС → отключение; Modbus в HA",
                "П2: ": "Блокировка с В3",
                "В3: ": "Сухой контакт → П2",
                "ПУ1–": "По группе на ПУ, на чердаке",
                "НБ1 ": "Отд. автомат, ориентир по EER 3,2",
                "НБ2 ": "Отд. автомат"}.get(nm[:4], "")
        rows.append((nm, f"{kw:.1f}".replace(".", ","), net, note))
    tot = sum(kw for _, kw, _ in loads)
    rows.append(("Итого ОВК", f"{tot:.1f}".replace(".", ","), "", "Кондиционирование и "
                 "увлажнение одновременно не работают"))
    yb = table(ax, 25, y - 5, [80, 20, 20, 100], rows, rh=4.4, fs=5.2, bold_rows=(len(rows) - 1,))
    ax.text(25, yb - 4, "ВК / ОВ", fontsize=6.5, weight="bold")
    s_ = wrap(f"• ОВ: контур «калориферы П1/П2» от буфера, гликоль 30 % через теплообменник, "
              f"{P1_HEATER_KW:.0f} + {P2_HEATER_KW:.1f} кВт; защита от замерзания. • ВК: установка "
              "обратного осмоса 50–100 л/ч для ПУ в котельной, подпитка Ø16 по ВК-5; дренаж ПУ, "
              "ПВУ и 11 внутренних блоков — в стояки К1 через сухие затворы (помпы где нет уклона).",
              175)
    ax.text(27, yb - 8, s_, fontsize=5.4, va="top")
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
