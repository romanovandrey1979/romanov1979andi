"""291-СС «Слаботочные системы и автоматизация» (СКС, Wi-Fi, Home Assistant, видеонаблюдение,
домофон, охрана, аудио) — концепт заказчика по ТЗ на автоматизацию ред. 4 и Прил. 4."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Circle

from make_drawings import new_sheet, table, wrap, set_doc
from make_plans import S, draw_underlay, notes, title
import eom_data as E

GEOM = E.GEOM
BLUE, GREEN, MAG, GRAY, ORANGE, TEAL = "#1565c0", "#2e7d32", "#6a1b9a", "#555", "#ef6c00", "#00838f"
CODE = "291-СС"
SHEETS = ["Общие данные. Структурная схема",
          "Матрица помещений: слаботочные системы и автоматизация",
          "План 1 этажа. Слаботочные системы",
          "План 2 этажа и чердака. Слаботочные системы",
          "Спецификация оборудования и материалов"]

RACK = (7750, 5600)          # стойка 18U 600×800 — кладовая 10 (1-10)
OPTICS = (6600, 1300)        # ввод оптики посёлка З7/З8 (5/Б)
AP = {1: [(4000, 7000), (4500, 14800), (12000, 6800), (17600, 12000)],
      2: [(3000, 9000), (12000, 8500), (17600, 12500)]}
AP_TERRACE = (12000, 12800)
ZB = {1: [(12000, 6000)], 2: [(12000, 7600)]}          # координаторы Zigbee SLZB-06 PoE
CAMS = [(p[1], p[2], p[4]) for p in E.OUTDOOR if p[3] == "КК"]
INTERCOM = [(p[1], p[2], p[4]) for p in E.OUTDOOR if p[3] == "ДФ"][0]
GATE = (17650, -6500)
AUDIO = {(1, 9): "5.1", (1, 8): "2.0", (2, 3): "2.0", (1, 11): "термост.", (1, 12): "2.0"}
STATIONS = [(1, 2), (1, 8), (1, 9), (1, 12), (2, 3), (2, 7), (2, 10), (2, 12), (2, 14), (1, 7)]
RS485 = [("Котельная: котёл (OpenTherm/Modbus), насосы, контроллер ТП", "котельная → стойка"),
         ("Шлюз VRF (Modbus / CoolMasterNet), НБ1/НБ2", "котельная → стойка"),
         ("ПВУ П1В1, П2, увлажнители ПУ1–ПУ6 (Modbus TCP/RTU)", "чердак → стойка"),
         ("Счётчики электроэнергии ГРЩ (Modbus RTU), импульс воды", "ГРЩ → стойка"),
         ("Инвертор и АКБ, АВР генератора (Modbus, сухие контакты)", "кладовая 10 / котельная"),
         ("Защита от протечек (Neptun-класс): RS-485 или Zigbee", "котельная → стойка"),
         ("Пульт печи сауны (сухие контакты / Modbus)", "сауна → стойка"),
         ("Зарядная станция ЭМ (OCPP 1.6J по UTP)", "въезд (З18) → стойка")]


def sheet_general(pdf):
    fig, ax = new_sheet(1, SHEETS[0])
    ax.text(25, 287, "Общие данные", fontsize=8, weight="bold")
    gn = [
        "Концепт заказчика по ТЗ на автоматизацию ред. 4 (14.10.2026) и Прил. 4 (21.10.2026): "
        "Home Assistant + Zigbee 3.0 + «Дом с Алисой». KNX, Crestron, Control4, Loxone и шины "
        "не применяются; облачные сервисы — не единственный канал управления.",
        "Стойка 18U 600×800 — в кладовой 10 (1-10): 2 м² свободного пола, вентиляция, дверь "
        "≥ 0,8 м; питание — две линии через ИБП, управляемый PDU с перезагрузкой по розеткам.",
        "Ввод оптики посёлка — гильзы Ø50 З7/З8 у 5/Б; резерв — LTE-маршрутизатор.",
        "Сервер Home Assistant — мини-ПК класса Intel N100, 16 ГБ, SSD, на ИБП; резервные копии и "
        "архив видео 30 сут — на NAS (Frigate). Координаторы Zigbee SLZB-06 с PoE — по одному на "
        "этаж в центре этажа, не в металлическом щите (не более 60–80 устройств на координатор).",
        "Сеть: коммутатор PoE+ 48 портов (бюджет ≥ 370–500 Вт), VLAN: IoT, камеры, гости. "
        "Wi-Fi 6 — 2–3 точки на этаж + терраса + спа; план каналов Wi-Fi 2,4 ГГц и Zigbee без "
        "наложения.",
        f"Видеонаблюдение: {len(CAMS)} PoE-камер ONVIF S/T, запись постоянная, без облака; питание "
        "камер и фасадного света — сверху из подшивки свесов (гильзы Ø25 по БР-ЗК П7).",
        "Домофон 2N (SIP + RTSP + HTTP API): вызывная панель у калитки (гильза З16), монитор в "
        "прихожей; входной замок — Zigbee/Matter. Охрана Ajax — хаб у стойки, ретрансляторы на "
        "этажах, события в HA по SIA DC-09 (только чтение).",
        "Аудио — 6 зон: гостиная 5.1, кухня-столовая, мастер-спальня, сауна/душ (термостойкий "
        "динамик, Станция вне парной), зона отдыха спа, терраса; акустический кабель от стойки к "
        "каждой зоне. Станции Алисы — во всех жилых, на кухне с экраном.",
        f"ТВ-точки — {E.N_TV} (8 помещений + терраса): питание, UTP cat.6 и 2 трубы Ø32 к каждому ТВ.",
        "Кабели RS-485 (экранированная витая пара, шина с терминаторами) и UTP от инженерного "
        "оборудования до стойки — по таблице справа.",
        "Все слаботочные линии — в отдельных трубах; в брусе — отдельные каналы на расстоянии "
        "150–200 мм от силовых (291-ЭОМ, лист 10).",
    ]
    y = 282
    for i, t in enumerate(gn, 1):
        s = wrap(f"{i}. {t}", 98)
        ax.text(25, y, s, fontsize=5.3, va="top")
        y -= 2.95 * (s.count("\n") + 1) + 1.0
    ax.text(200, 287, "Структурная схема (концепт)", fontsize=8, weight="bold")

    def box(x, y, w, h, t, fc="white"):
        ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec="k", lw=0.8))
        ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=4.6)
    box(255, 205, 60, 62, "Стойка 18U (кладовая 10)\nоптика + LTE-роутер\nPoE+ 48 портов\n"
                         "сервер HA (N100), NAS\nхаб Ajax, PDU\nИБП 2 линии", "#e3f2fd")
    box(200, 262, 42, 10, "Оптика посёлка (З7/З8)", "#eee")
    ax.plot([242, 285, 285], [267, 267, 267], c="k", lw=0.8)
    left = [(f"Wi-Fi 6 ×{len(AP[1]) + len(AP[2]) + 1} (PoE)", 250), (f"Камеры ×{len(CAMS)} (PoE)", 238),
            ("Zigbee SLZB-06 ×2–3 (PoE)", 226), (f"ТВ-точки ×{E.N_TV}", 214), ("RJ45 рабочие места", 202)]
    for t, y in left:
        box(200, y - 4, 42, 8, t)
        ax.plot([242, 255], [y, y], c=GRAY, lw=0.6)
    right = [("Домофон 2N, монитор, замок", 255), ("Аудио 6 зон, Станции ×10", 243),
             ("Ajax: охрана, ПС (291-МЗ.ПС)", 231), ("RS-485 / Modbus: котельная,\nVRF, ПВУ, учёт", 219),
             ("Инвертор, АВР, зарядка ЭМ", 207)]
    for t, y in right:
        box(330, y - 4, 50, 8, t)
        ax.plot([315, 330], [y, y], c=GRAY, lw=0.6)
    ax.text(200, 190, "Линии RS-485 / UTP от оборудования к стойке", fontsize=7, weight="bold")
    rows = [("Система", "Трасса")] + RS485
    table(ax, 200, 186, [120, 60], rows, rh=4.6, fs=5.0)
    pdf.savefig(fig)
    plt.close(fig)


MATRIX_COLS = ["Свет (гр.)", "Дим.", "Шторы", "ТВ", "Аудио", "Станция", "Wi-Fi", "Протечка",
               "CO₂/RH", "Движение"]


def sheet_matrix(pdf):
    fig, ax = new_sheet(2, SHEETS[1])
    ax.text(25, 287, "Матрица помещений (ТЗ ред. 4 §12, паспорт № 83 табл. 6) — «+» есть, «—» нет",
            fontsize=7.2, weight="bold")
    wet = ("с/у", "душ", "постир", "котельн", "кухня")
    ap_rooms = {(1, 7), (1, 8), (1, 9), (1, 12), (2, 1), (2, 3), (2, 10)}
    co2 = {(2, 3), (2, 7), (2, 10), (2, 12), (2, 14), (1, 9)}
    motion = ("холл", "гардероб", "кладов", "котельн", "прихож")
    rows = [("Помещение",) + tuple(MATRIX_COLS)]
    for r in E.ROOMS:
        k = (r["floor"], r["num"])
        n = r["name"].lower()
        yn = lambda c: "+" if c else "—"
        rows.append((f"{r['floor']}-{r['num']} {r['name'][:30]}", str(len(r["groups"])), yn(r["dim"]),
                     str(r["n_curtain"]) if r["n_curtain"] else "—", yn(r["n_tv"]),
                     AUDIO.get(k, "—"), yn(k in STATIONS), yn(k in ap_rooms),
                     yn(any(w in n for w in wet)), yn(k in co2), yn(any(w in n for w in motion))))
    rows.append(("Терраса", "2", "—", "ZIP-экраны", "+", "2.0", "+ (IP)", "+", "—", "—", "+"))
    table(ax, 25, 283, [70] + [24] * 10, rows, rh=6.6, fs=5.0,
          aligns=["left"] + ["center"] * 10)
    ax.text(25, 58, wrap(
        "Дым и тепло — во всех помещениях (291-МЗ.ПС). USB-C — у кроватей, рабочих мест и на кухне "
        "(291-ЭОМ). Термостаты — скрытые датчики Zigbee в каждом помещении с тёплым полом; поворотный "
        "термостат той же серии в спальнях и гостиной — по решению семьи. Автосвет по датчикам — "
        "лестница, коридоры, гардеробные, кладовые, котельная, вход; в жилых и санузлах датчиков нет.",
        125), fontsize=5.4, va="top")
    pdf.savefig(fig)
    plt.close(fig)


def plan(fig, ax, floor, n):
    draw_underlay(ax, 4 if floor == 1 else 5)
    title(ax, f"План {floor} этажа{' и чердака' if floor == 2 else ''}. Слаботочные системы (М 1:100)")
    aps = AP[floor] + ([AP_TERRACE] if floor == 1 else [])
    for x, y in aps:
        sx, sy = S((x, y))
        ax.add_patch(Circle((sx, sy), 1.8, fc="white", ec=BLUE, lw=1, zorder=8))
        ax.text(sx, sy, "W", ha="center", va="center", fontsize=4, color=BLUE, weight="bold", zorder=9)
    for x, y in ZB[floor]:
        sx, sy = S((x, y))
        ax.add_patch(Rectangle((sx - 1.6, sy - 1.6), 3.2, 3.2, fc="#e0f7fa", ec=TEAL, lw=0.8, zorder=8))
        ax.text(sx, sy, "Z", ha="center", va="center", fontsize=4, color=TEAL, weight="bold", zorder=9)
    for r in [r for r in E.ROOMS if r["floor"] == floor]:
        x0, y0, x1, y1 = r["geom"]
        k = (r["floor"], r["num"])
        if r["n_tv"]:
            sx, sy = S((x0 + 500, (y0 + y1) / 2 + 700))
            ax.add_patch(Rectangle((sx - 1.2, sy - 1.2), 2.4, 2.4, fc="#c8e6c9", ec=GREEN, lw=0.7, zorder=8))
        if k in AUDIO:
            sx, sy = S((x1 - 600, y1 - 600))
            ax.add_patch(Circle((sx, sy), 1.3, fc="#ffe0b2", ec=ORANGE, lw=0.7, zorder=8))
            ax.text(sx + 1.6, sy, AUDIO[k], fontsize=3.6, color=ORANGE, va="center", zorder=9)
        if k in STATIONS:
            sx, sy = S((x0 + 600, y1 - 600))
            ax.add_patch(Circle((sx, sy), 0.9, fc=MAG, ec="k", lw=0.4, zorder=8))
    if floor == 1:
        for x, y, t in CAMS:
            sx, sy = S((x, y))
            ax.add_patch(Rectangle((sx - 1.6, sy - 1.0), 3.2, 2.0, fc=MAG, ec="k", lw=0.5, zorder=8))
        sx, sy = S(RACK)
        ax.add_patch(Rectangle((sx - 4, sy - 1.8), 8, 3.6, fc="#e3f2fd", ec="k", lw=0.9, zorder=9))
        ax.text(sx, sy, "СТОЙКА", ha="center", va="center", fontsize=3.8, weight="bold", zorder=10)
        ox, oy = S(OPTICS)
        ax.annotate("", xy=(sx, sy - 2), xytext=(ox, oy - 6),
                    arrowprops=dict(arrowstyle="-|>", color=GRAY, lw=0.8))
        ax.text(ox + 1, oy - 8, "оптика посёлка З7/З8 (5/Б)", fontsize=4, color=GRAY)
        ix, iy = S((INTERCOM[0], INTERCOM[1]))
        ax.add_patch(Rectangle((ix - 1.5, iy - 1.5), 3, 3, fc="#fff9c4", ec="k", lw=0.6, zorder=9))
        ax.text(ix + 2, iy, "монитор / замок", fontsize=3.8, va="center", zorder=9)
        gx, gy = S((17650, 0))
        ax.annotate("", xy=(gx, gy + 3), xytext=(gx, gy - 10),
                    arrowprops=dict(arrowstyle="-|>", color=GRAY, lw=0.8))
        ax.text(gx + 1, gy - 12, "к калитке и воротам (З16): 2N, привод, камера", fontsize=4, color=GRAY)
    else:
        sx, sy = S((11500, 7300))
        ax.add_patch(Rectangle((sx - 4, sy - 1.8), 8, 3.6, fc="#f3e5f5", ec="k", lw=0.8, ls="--", zorder=9))
        ax.text(sx, sy, "ПВУ (чердак)", ha="center", va="center", fontsize=3.6, zorder=10)
    y = 288
    ax.text(333, y, "Условные обозначения", fontsize=6.5, weight="bold")
    y -= 6
    for kind, t in (("ap", "Точка доступа Wi-Fi 6 (PoE)"), ("zb", "Координатор Zigbee SLZB-06 (PoE)"),
                    ("tv", "ТВ-точка: UTP + 220 В + 2×Ø32"), ("au", "Аудиозона (колонки потолочные)"),
                    ("st", "Станция Алиса"), ("cam", "IP-камера (ONVIF, PoE)"), ("rack", "Стойка 18U")):
        if kind == "ap":
            ax.add_patch(Circle((338, y), 1.8, fc="white", ec=BLUE, lw=1))
        elif kind == "zb":
            ax.add_patch(Rectangle((336.4, y - 1.6), 3.2, 3.2, fc="#e0f7fa", ec=TEAL, lw=0.8))
        elif kind == "tv":
            ax.add_patch(Rectangle((336.8, y - 1.2), 2.4, 2.4, fc="#c8e6c9", ec=GREEN, lw=0.7))
        elif kind == "au":
            ax.add_patch(Circle((338, y), 1.3, fc="#ffe0b2", ec=ORANGE, lw=0.7))
        elif kind == "st":
            ax.add_patch(Circle((338, y), 0.9, fc=MAG, ec="k", lw=0.4))
        elif kind == "cam":
            ax.add_patch(Rectangle((336.4, y - 1.0), 3.2, 2.0, fc=MAG, ec="k", lw=0.5))
        else:
            ax.add_patch(Rectangle((334.5, y - 1.8), 7, 3.6, fc="#e3f2fd", ec="k", lw=0.9))
        ax.text(345, y, t, fontsize=5.0, va="center")
        y -= 5.2
    notes(ax, 333, y - 2, [
        "Кабели UTP cat.6 звездой от стойки, в отдельных трубах; RS-485 — экранированная витая пара.",
        "Места точек — по карте дизайнера к 13.11.2026; точки Wi-Fi — между балками, без экранов.",
        "Камеры — питание сверху из подшивки свесов (Ø25, БР-ЗК П7).",
        "Метеостанция Ecowitt — мачта на фронтоне 13/Ж (проходка кровли К11, Ø25).",
    ])


def spec_rows():
    n_ap = len(AP[1]) + len(AP[2]) + 1
    return [
        ("#", "Стойка и активное оборудование"),
        ("СТ", "Стойка напольная 19\" 18U 600×800 с вентиляцией, полками, PDU управляемый", "", "шт.", 1, "кладовая 10"),
        ("", "Маршрутизатор с резервным LTE-каналом, VPN (Tailscale)", "", "шт.", 1, ""),
        ("", "Коммутатор PoE+ 48 портов, управляемый, VLAN, бюджет ≥ 370–500 Вт", "", "шт.", 1, ""),
        ("", "Сервер Home Assistant: мини-ПК Intel N100, 16 ГБ, SSD", "", "шт.", 1, "на ИБП"),
        ("", "NAS 2 диска (архив камер 30 сут, Frigate, резервные копии HA)", "", "шт.", 1, ""),
        ("", "ИБП онлайн для стойки (≥ 30 мин), NUT по USB/SNMP", "", "шт.", 1, ""),
        ("", "Координатор Zigbee SLZB-06 с PoE (Zigbee2MQTT)", "", "шт.", 3, "1 на этаж + резерв"),
        ("#", "Конечные устройства"),
        ("", "Точка доступа Wi-Fi 6, PoE (потолочная / уличная на террасе)", "", "шт.", n_ap, ""),
        ("", "IP-камера ONVIF Profile S/T, PoE, уличная", "", "шт.", len(CAMS), ""),
        ("", "Домофон 2N: вызывная панель с камерой (SIP/RTSP/API), монитор, замок Zigbee/Matter",
         "2N", "компл.", 1, ""),
        ("", "Охранная система Ajax: хаб, ретрансляторы ×2, датчики открытия/движения", "Ajax", "компл.", 1, ""),
        ("", "Станция Алиса (кухня — с экраном, терраса — влагозащищённая)", "", "шт.", 12, ""),
        ("", "Усилитель / мультирум 6 зон с IP API, колонки потолочные", "", "компл.", 1, "гостиная 5.1"),
        ("", "Динамик термостойкий для сауны (до 120 °C)", "", "шт.", 1, ""),
        ("", "Розетка RJ45 cat.6 двойная (ТВ, рабочие места, кабинет-гостевая 2 шт.)", "", "шт.", 14, ""),
        ("", "Датчики Zigbee: температура/влажность, CO₂ (спальни, гостиная)", "", "шт.", 28, ""),
        ("", "Метеостанция Ecowitt (локальный API)", "", "шт.", 1, ""),
        ("#", "Кабели и трассы"),
        ("", "Кабель U/UTP cat.6 LSZH", "", "м", 1500, "Ориентир."),
        ("", "Кабель U/UTP cat.6 наружный (в земле — в трубе)", "", "м", 150, ""),
        ("", "Кабель RS-485 экранированная витая пара 2×2×0,5", "", "м", 250, ""),
        ("", "Кабель акустический 2×1,5 (6 зон, 5.1)", "", "м", 350, ""),
        ("", "Труба ПНД Ø50 (оптика, калитка, ворота, зарядка ЭМ)", "", "м", 100, ""),
        ("", "Металлорукав / гофра Ø20–25 для слаботочки, трубы Ø32 к ТВ", "", "м", 800, ""),
    ]


def sheet_spec(pdf):
    fig, ax = new_sheet(5, SHEETS[4])
    ax.text(25, 287, "Спецификация оборудования и материалов (концепт, без цен)", fontsize=7.5,
            weight="bold")
    data = [("Поз.", "Наименование", "Тип, марка", "Ед.", "Кол.", "Примечание")]
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
        sheet_matrix(pdf)
        for n, fl in ((3, 1), (4, 2)):
            fig, ax = new_sheet(n, SHEETS[n - 1])
            plan(fig, ax, fl, n)
            pdf.savefig(fig)
            plt.close(fig)
        sheet_spec(pdf)
        pdf.infodict()["Title"] = f"{CODE} Слаботочные системы и автоматизация (концепт)"
    set_doc()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "291-СС.pdf")
