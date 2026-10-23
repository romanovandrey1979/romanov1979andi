"""Графика пакета: типовые узлы КР, схема котельной, однолинейная схема, график ПОС, диаграмма бюджета."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from elling_data import slab_check, piles, heat_loss, el_calc
from elling_cost import totals, SC, SC_NAME

plt.rcParams["font.family"] = "DejaVu Sans"
K = "#333333"
CONC, SOIL, INS, BLUE, RED = "#c9c9c9", "#e8dcc4", "#f4e27a", "#1565c0", "#c62828"


def _save(fig, path):
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    return path


def fig_slab(path):
    s = slab_check()
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.set_aspect("equal"); ax.axis("off")
    # плита и два ребра (мм)
    ax.add_patch(Rectangle((0, 400), 5000, 200, fc=CONC, ec=K))
    for x in (1100, 3600):
        ax.add_patch(Rectangle((x, 0), 300, 400, fc=CONC, ec=K))
        for dx in (60, 150, 240):
            ax.add_patch(plt.Circle((x + dx, 55), 22, color=RED))
        ax.add_patch(Rectangle((x + 30, 30), 240, 540, fill=False, ec=RED, lw=0.8, ls="--"))
    ax.plot([0, 5000], [560, 560], c=RED, lw=0.8); ax.plot([0, 5000], [440, 440], c=RED, lw=0.8)
    ax.add_patch(Rectangle((0, 600), 5000, 70, fc="#ddd", ec=K, lw=0.5))
    ax.text(5050, 630, "стяжка 70 + звукоизоляция + пол", fontsize=8, va="center")
    ax.text(5050, 500, "плита 200, В25, А500: сетки Ø10 шаг 200 верх/низ", fontsize=8, va="center")
    ax.text(5050, 200, f"ребро 300×600 (от низа плиты 400), шаг {2500} мм;\nнижняя арматура "
            f"{s['bars']}Ø22 (As = {s['bars'] * 380:.0f} ≥ {s['As']:.0f} мм²),\nхомуты Ø8 шаг 150/300; "
            f"защитный слой до оси 45 мм (REI 150)", fontsize=8, va="center")
    for x0, x1, y, t in [(1250, 3750, -150, "2 500 — шаг рёбер")]:
        ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="<->", lw=0.6))
        ax.text((x0 + x1) / 2, y - 70, t, ha="center", fontsize=7.5)
    ax.annotate("", (-150, 0), (-150, 600), arrowprops=dict(arrowstyle="<->", lw=0.6))
    ax.text(-260, 300, "600", rotation=90, va="center", fontsize=7.5)
    ax.set_xlim(-400, 9200); ax.set_ylim(-300, 800)
    ax.set_title("Узел 1. Ребристое монолитное перекрытие над гаражами и эллингом (типовое сечение)", fontsize=10)
    return _save(fig, path)


def fig_pile(path):
    p = piles()
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Rectangle((-500, -2600), 5500, 2350, fc=SOIL, ec="none"))
    ax.add_patch(Rectangle((-500, -250), 5500, 500, fc="#efe6cf", ec="none"))
    ax.text(1000, -2300, "суглинок/глина\n(по ИГИ — уточнить)", fontsize=8)
    ax.text(1000, -170, "песок уплотн. 500", fontsize=8)
    ax.add_patch(Rectangle((0, 250), 4000, 80, fc="#aaa", ec=K, lw=0.4))
    ax.add_patch(Rectangle((0, 330), 4000, 100, fc=INS, ec=K, lw=0.4))
    ax.add_patch(Rectangle((0, 430), 4000, 300, fc=CONC, ec=K))
    for x in (600, 2600):
        ax.add_patch(Rectangle((x, -2600), 300, 2930, fc="#b0b0b0", ec=K))
    ax.add_patch(Rectangle((0, 730), 400, 1300, fc="#f2f2f2", ec=K, hatch="..", lw=0.6))
    ax.add_patch(Rectangle((-120, 730), 120, 1300, fc="#b38b59", ec=K, lw=0.4))
    ax.add_patch(Rectangle((-220, 250), 100, 650, fc=INS, ec=K, lw=0.4))
    ax.text(-1700, 1400, "газобетон D500\n400 + вентфасад", fontsize=8)
    ax.text(-1700, 550, "ЭППС 100\nпо торцу", fontsize=8)
    ax.text(5100, 800, "плита 300, В25 W8 F150 — пол 1 этажа\n(топпинг в гаражах, без цокольного перекрытия)", fontsize=8, va="center")
    ax.text(5100, 470, "ЭППС 100 + гидроизоляция 2 слоя", fontsize=8, va="center")
    ax.text(5100, 250, "подбетонка 80", fontsize=8, va="center")
    ax.text(5100, -1200, f"сваи С80.30 L = 8 м, {p['count']} шт.\nNрасч ≈ {p['N_design'] / 1000:.1f} МН, "
            f"на сваю ≤ 380 кН\n(уточнить по испытаниям)", fontsize=8, va="center")
    ax.set_xlim(-1900, 9800); ax.set_ylim(-2700, 2100)
    ax.set_title("Узел 2. Фундаментная плита на забивных сваях (по периметру)", fontsize=10)
    return _save(fig, path)


def _box(ax, x, y, w, h, t, fc="#f7f7f7", fs=7.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fc=fc, ec=K, lw=0.8))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs)


def _ar(ax, a, b, c=K):
    ax.annotate("", b, a, arrowprops=dict(arrowstyle="->", lw=1.0, color=c))


def fig_boiler(path):
    hl = heat_loss()["total"]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.axis("off"); ax.set_xlim(0, 100); ax.set_ylim(0, 52)
    _box(ax, 2, 32, 16, 12, "Пеллетный котёл\n60 кВт\n+ бункер 1,5 м³", "#fde3c8")
    _box(ax, 2, 14, 16, 10, "Электрокотёл\n24 кВт (резерв)", "#e3f0fd")
    _box(ax, 2, 2, 16, 8, "Место под газовый\nкотёл (2028)", "#eeeeee")
    _box(ax, 30, 14, 14, 28, "Буфер\n1 000 л", "#fff4c2")
    _box(ax, 56, 40, 18, 9, "Бойлер ГВС 500 л\nприоритет, рецирк.", "#e3f0fd")
    _box(ax, 56, 28, 18, 9, "ТП проживание\nи спортзал 35/30 °C\n(смеситель)", "#f7f7f7")
    _box(ax, 56, 16, 18, 9, "Конвекторы, радиаторы\n70/50 °C", "#f7f7f7")
    _box(ax, 56, 4, 18, 9, "Калориферы П1/П2\nи агрегаты гаражей", "#f7f7f7")
    _box(ax, 82, 22, 16, 14, "Автоматика:\nкаскад, погодная\nкомпенсация,\nдиспетчеризация", "#e9f7e9")
    for y in (38, 19):
        _ar(ax, (18, y), (30, y), RED)
    for y in (44, 32, 20, 8):
        _ar(ax, (44, 28), (56, y + 0.5), RED)
    ax.text(50, 50.5, f"Расчётные теплопотери ≈ {hl:.0f} кВт (−25 °C); жилая часть +20, спортзал +18, гаражи и эллинг +5",
            ha="center", fontsize=8)
    ax.set_title("БЭ-ОВ. Принципиальная схема котельной (пом. 014, 21,48 м²)", fontsize=10)
    return _save(fig, path)


def fig_sld(path):
    e = el_calc()
    fig, ax = plt.subplots(figsize=(10, 5.4))
    ax.axis("off"); ax.set_xlim(0, 100); ax.set_ylim(0, 60)
    _box(ax, 2, 46, 18, 10, "ТП посёлка 0,4 кВ\n(250 → 400 кВт)", "#e3f0fd")
    _box(ax, 2, 30, 18, 10, "ДГУ посёлка\n(резерв, АВР)", "#fde3c8")
    _box(ax, 30, 36, 18, 16, f"ВРУ эллинга\n3ф 100 А, учёт\nPр ≈ {e['Pp']:.0f} кВт\nIр ≈ {e['I']:.0f} А", "#fff4c2")
    _ar(ax, (20, 51), (30, 47)); _ar(ax, (20, 35), (30, 41))
    groups = ["ЩО освещение", "ЩР-1 1 этаж, КПП, ворота", "ЩР-2 проживание, столовая",
              "ЩР-3 спортзал", "ЩК котельная", "ЩВ вентиляция и VRF", "ЩЗ зарядные станции", "ЩСС слаботочка (ИБП)"]
    for i, g in enumerate(groups):
        y = 54 - i * 6.6
        _box(ax, 62, y - 2.5, 30, 5, g, fs=7)
        ax.plot([48, 55, 55, 62], [44, 44, y, y], c=K, lw=0.7)
    ax.text(2, 24, "Защита: вводной автомат 100 А,\nУЗИП I+II, УЗО 30 мА на розеточных\nгруппах, "
            "блокировка электрокотла\nи зарядных станций по току ввода", fontsize=7.5, va="top")
    ax.set_title("БЭ-ЭОМ. Однолинейная схема (принципиальная)", fontsize=10)
    return _save(fig, path)


GANTT = [  # работа, начало (месяц от 11.2026 = 0), длительность мес
    ("Геология, юрист по ВОЗ/ЗСО, решение по ЭП", 0, 1.5),
    ("КР + ИОС + ПБ (рабочая документация)", 0.5, 3.5),
    ("Тендер на коробку (3 монолитчика)", 3, 1.5),
    ("Сваи, испытания, плита", 4.5, 2),
    ("Колонны, стены 1 этажа, перекрытие", 6.5, 2),
    ("Стены 2 этажа, плоская кровля", 8.5, 1.5),
    ("Скатная кровля, чердак, фронтоны", 9.5, 1.5),
    ("Окна, витражи, ворота (заказ за 3 мес)", 10, 1.5),
    ("Инженерные системы", 11, 4),
    ("Фасады", 10.5, 3),
    ("Отделка, оснащение", 13, 4),
    ("ПНР, техплан, регистрация", 16.5, 1.5),
]
MONTHS = ["ноя 26", "дек", "янв 27", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя",
          "дек", "янв 28", "фев", "мар", "апр", "май"]


def fig_gantt(path):
    fig, ax = plt.subplots(figsize=(11, 4.8))
    for i, (n, s, d) in enumerate(GANTT):
        ax.barh(i, d, left=s, zorder=2, color="#4a78b5" if i > 2 else "#8aa6cc", edgecolor=K, lw=0.4)
    ax.set_yticks(range(len(GANTT))); ax.set_yticklabels([g[0] for g in GANTT], fontsize=8)
    ax.invert_yaxis()
    ax.set_xticks(range(len(MONTHS))); ax.set_xticklabels(MONTHS, fontsize=7, rotation=45)
    ax.axvspan(1, 4.5, color="#e3f0fd", alpha=0.6, lw=0, zorder=0)
    ax.text(2.75, len(GANTT) - 0.4, "зима: без монолита", ha="center", fontsize=7.5, color=BLUE)
    ax.grid(axis="x", lw=0.3)
    ax.set_title("БЭ-ПОС. Укрупнённый график: ввод — апрель–май 2028", fontsize=10)
    return _save(fig, path)


def fig_budget(path):
    t = totals()
    groups = [("Коробка и кровля", ("01", "02", "03", "04", "05", "06")),
              ("Фасады, окна, ворота, МК", ("07", "08", "09")),
              ("Отделка", ("10", "11")), ("Инженерия", ("12", "13", "14", "15", "16"))]
    fig, ax = plt.subplots(figsize=(10, 4.4))
    cols = ["#7d8fa6", "#a7b98a", "#d9b26f", "#c47c6b", "#bbbbbb", "#eeeeee"]
    for j, s in enumerate(SC):
        left = 0
        vals = [sum(v for k, v in t[s]["by_sec"].items() if k[:2] in codes) / 1e6 for _, codes in groups]
        vals += [t[s]["ext_sum"] / 1e6, t[s]["reserve"] / 1e6]
        for i, v in enumerate(vals):
            ax.barh(j, v, left=left, color=cols[i], edgecolor="white")
            if v > 6:
                ax.text(left + v / 2, j, f"{v:.0f}", ha="center", va="center", fontsize=7.5)
            left += v
        ax.text(left + 1.5, j, f"{left:.0f} млн", va="center", fontsize=8.5, weight="bold")
    ax.set_yticks(range(3)); ax.set_yticklabels([SC_NAME[s] for s in SC], fontsize=8.5)
    ax.invert_yaxis()
    names = [g[0] for g in groups] + ["Вне СМР: проект, сети, оснащение, понтон", "Резерв"]
    ax.legend([Rectangle((0, 0), 1, 1, fc=c) for c in cols], names, fontsize=7, ncol=3,
              loc="upper center", bbox_to_anchor=(0.5, -0.12), frameon=False)
    ax.set_xlabel("млн ₽ с НДС", fontsize=8)
    ax.set_title("Полная стоимость эллинга по сценариям", fontsize=10)
    return _save(fig, path)


def build_all(d):
    os.makedirs(d, exist_ok=True)
    return {"slab": fig_slab(f"{d}/slab.png"), "pile": fig_pile(f"{d}/pile.png"),
            "boiler": fig_boiler(f"{d}/boiler.png"), "sld": fig_sld(f"{d}/sld.png"),
            "gantt": fig_gantt(f"{d}/gantt.png"), "budget": fig_budget(f"{d}/budget.png")}


if __name__ == "__main__":
    import sys
    print(build_all(sys.argv[1] if len(sys.argv) > 1 else "/tmp/elling_fig"))
