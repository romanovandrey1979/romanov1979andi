"""Исходные данные и расчёт воздухообменов / холодильной нагрузки.

Объект: индивидуальный жилой дом «Берта Ромарио», Московская обл., Истринский р-н.
Источник экспликации помещений: АПР «Берта Ромарио» (ООО «Строй Хауз», 2026), листы 4, 5.
"""
import math

PROJECT = {
    "code": "291-ОВК",
    "name": "Индивидуальный жилой дом «Берта Ромарио»",
    "address": "Московская обл., Истринский р-н, д. Веледниково, ул. Живописная, д. 25",
    "section": "Вентиляция и кондиционирование воздуха",
    "org": "ООО «Строй Хауз»",
    "stage": "Р",
    "year": "2026",
    "date": "10.26",
}

# Климат (СП 131.13330.2020, ближайший пункт — Москва; уточнить по действующей редакции)
CLIMATE = {
    "t_winter": -25.0,   # °C, параметры Б (холодная пятидневка 0,92)
    "t_summer": 28.0,    # °C, принято для расчёта кондиционирования (с запасом к параметрам Б)
    "t_in_winter": 20.0,
    "t_in_summer": 23.0,
    "t_supply": 20.0,    # °C, температура притока после ПВУ зимой
}

H1 = 3.70   # высота 1 этажа в чистоте, м
H2 = 3.40   # высота 2 этажа в чистоте, м
H_HALL = 7.90  # холл-лестница со вторым светом: от ±0,000 до низа чердачного перекрытия

# Нормативные удельные значения (СП 54.13330.2022 табл. 9.1 / СП 55.13330.2016 / СП 60.13330.2020 прил. К)
# kind: тип помещения; n — кол-во людей; ach — кратность; fixed — фиксированный расход
# sup/exh — расчётный приток / вытяжка, м³/ч (заполняются функцией calc_air)
ROOMS = [
    # floor, №, наименование, площадь, kind, people
    (1, 1, "Парадное крыльцо", 7.02, "outdoor", 0),
    (1, 2, "Прихожая", 18.53, "hall_sup", 0),
    (1, 3, "Гардеробная", 10.35, "wardrobe", 0),
    (1, 4, "Постирочная", 9.00, "laundry", 0),
    (1, 5, "Котельная", 11.21, "boiler", 0),
    (1, 6, "С/У", 3.25, "wc", 0),
    (1, 7, "Холл - лестница (второй свет)", 26.97, "stair", 0),
    (1, 8, "Кухня-столовая", 50.77, "kitchen", 6),
    (1, 9, "Гостиная (камин)", 43.06, "living", 6),
    (1, 10, "Кладовая", 4.48, "storage", 0),
    (1, 11, "Сауна", 8.54, "sauna", 4),
    (1, 12, "Зона отдыха", 19.89, "relax", 4),
    (1, 13, "Душевые", 4.14, "shower", 0),
    (2, 1, "Лестничный холл", 12.35, "hall", 0),
    (2, 2, "Холл", 9.50, "hall", 0),
    (2, 3, "Мастер-спальня", 25.69, "bedroom", 2),
    (2, 4, "Гардеробная", 18.78, "wardrobe", 0),
    (2, 5, "С/У", 16.17, "bath", 0),
    (2, 6, "Кладовая", 8.82, "storage", 0),
    (2, 7, "Спальня гостевая", 22.12, "bedroom", 2),
    (2, 8, "С/У", 9.00, "bath", 0),
    (2, 9, "Холл", 13.00, "hall", 0),
    (2, 10, "Спальня детская", 21.40, "bedroom", 1),
    (2, 11, "С/У", 6.55, "bath", 0),
    (2, 12, "Спальня детская", 21.40, "bedroom", 1),
    (2, 13, "С/У", 6.25, "bath", 0),
    (2, 14, "Спальня детская", 23.01, "bedroom", 1),
    (2, 15, "С/У", 6.25, "bath", 0),
    (2, 16, "Постирочная", 7.58, "laundry", 0),
]

STD_D = [100, 125, 160, 200, 250, 315, 355, 400, 450, 500]


def up10(x):
    return int(math.ceil(x / 10.0) * 10)


def room_height(floor, kind):
    if kind == "stair":
        return H_HALL
    return H1 if floor == 1 else H2


def calc_air():
    """Возвращает список помещений с расчётным воздухообменом."""
    res = []
    for floor, num, name, area, kind, n in ROOMS:
        h = room_height(floor, kind)
        v = area * h
        sup = exh = 0
        sup_sys = exh_sys = ""
        basis = ""
        if kind in ("living", "bedroom"):
            sup = up10(max(1.0 * v if kind == "bedroom" else 1.0 * area * H1, 30 * n))
            sup_sys = "П1"
            basis = "1 крат, но ≥30 м³/ч на чел."
        elif kind == "kitchen":
            sup = up10(max(1.0 * v, 30 * n))
            sup_sys = "П1"
            exh = 150
            exh_sys = "В1"
            basis = "Приток 1 крат; вытяжка 60 м³/ч (эл. плита) с запасом + зонт В3"
        elif kind == "relax":
            sup = up10(max(1.0 * v, 30 * n)) + 30  # +компенсация вытяжки сауны В2
            sup_sys = "П1"
            basis = "1 крат, ≥30 м³/ч на чел. + компенсация В2"
        elif kind == "hall_sup":
            sup = 60
            sup_sys = "П1"
            basis = "Транзитный приток (зона входа)"
        elif kind == "stair":
            sup = 60
            sup_sys = "П1"
            exh = 0  # вытяжка из верхней зоны — назначается при балансировке
            exh_sys = "В1"
            basis = "Приток в нижнюю зону, вытяжка из верхней зоны (баланс)"
        elif kind == "wardrobe":
            exh = up10(1.0 * v)
            exh_sys = "В1"
            basis = "1 крат (принято с запасом к табл. 9.1)"
        elif kind == "storage":
            exh = up10(max(1.0 * v, 20))
            exh_sys = "В1"
            basis = "1 крат"
        elif kind == "laundry":
            exh = 90
            exh_sys = "В1"
            basis = "90 м³/ч (табл. 9.1)"
        elif kind == "wc":
            exh = 25
            exh_sys = "В1"
            basis = "25 м³/ч (уборная)"
        elif kind == "bath":
            exh = 50
            exh_sys = "В1"
            basis = "50 м³/ч (совмещённый С/У)"
        elif kind == "shower":
            exh = 50
            exh_sys = "В1"
            basis = "25 м³/ч на душевую сетку ×2"
        elif kind == "sauna":
            exh = up10(6 * area * 2.4)  # режим просушки 6 крат при h=2,4 м
            exh_sys = "В2"
            basis = "Просушка 6 крат (h=2,4 м); приток перетоком из зоны отдыха"
        elif kind == "boiler":
            exh = up10(3 * v)
            exh_sys = "ЕВ1"
            sup = exh
            sup_sys = "ПЕ1"
            basis = "3 крат + воздух на горение (уточнить по типу котла)"
        elif kind == "hall":
            basis = "Переток"
        elif kind == "outdoor":
            basis = "Неотапливаемое, не вентилируется"
        res.append(dict(floor=floor, num=num, name=name, area=area, h=h, v=round(v, 1),
                        kind=kind, n=n, sup=sup, exh=exh, sup_sys=sup_sys,
                        exh_sys=exh_sys, basis=basis))

    # балансировка П1/В1: недостающий объём вытяжки — из верхней зоны холла-лестницы
    p1 = sum(r["sup"] for r in res if r["sup_sys"] == "П1")
    v1 = sum(r["exh"] for r in res if r["exh_sys"] == "В1")
    stair = next(r for r in res if r["kind"] == "stair")
    if p1 > v1:
        stair["exh"] = p1 - v1
    return res


def system_totals(rooms):
    tot = {}
    for r in rooms:
        if r["sup_sys"]:
            tot[r["sup_sys"]] = tot.get(r["sup_sys"], 0) + r["sup"]
        if r["exh_sys"]:
            tot[r["exh_sys"]] = tot.get(r["exh_sys"], 0) + r["exh"]
    tot["В3"] = HOOD_FLOW
    tot["П2"] = HOOD_COMP
    return tot


HOOD_FLOW = 450     # м³/ч, кухонный зонт (В3), уточняется по паспорту вытяжки
HOOD_COMP = 400     # м³/ч, компенсация зонта (П2); остаток — за счёт П1


def duct_d(flow, vmax):
    """Минимальный стандартный круглый диаметр при скорости не выше vmax."""
    for d in STD_D:
        a = math.pi * (d / 1000) ** 2 / 4
        if flow / 3600 / a <= vmax:
            return d, round(flow / 3600 / a, 2)
    d = STD_D[-1]
    return d, round(flow / 3600 / (math.pi * (d / 1000) ** 2 / 4), 2)


def heater_kw(flow, t_from, t_to):
    return 0.336 * flow * (t_to - t_from) / 1000


# --- Кондиционирование ---
# удельная нагрузка (Вт/м²) по укрупнённым показателям; уточняется после получения
# ведомости заполнения проёмов АР
COOL_Q = {
    "living": 110, "kitchen": 100, "relax": 100, "stair": 150, "hall_sup": 70,
    "bedroom": 90, "hall": 70,
}
PEOPLE_W = 130  # Вт/чел (явное+скрытое)
EXTRA_W = {"kitchen": 800}  # бытовое оборудование
STD_UNITS = [2.2, 2.8, 3.6, 4.5, 5.6, 7.1, 9.0, 11.2, 14.0]

AC_ROOMS = {  # (этаж, №): тип внутреннего блока
    (1, 2): "настенный",
    (1, 7): "настенный",
    (1, 8): "настенный",
    (1, 9): "настенный",
    (1, 12): "настенный",
    (2, 3): "настенный",
    (2, 7): "настенный",
    (2, 10): "настенный",
    (2, 12): "настенный",
    (2, 14): "настенный",
    (2, 9): "настенный",
}


def calc_cooling(rooms):
    out = []
    for r in rooms:
        key = (r["floor"], r["num"])
        if key not in AC_ROOMS:
            continue
        q = COOL_Q[r["kind"]] * r["area"] + PEOPLE_W * r["n"] + EXTRA_W.get(r["kind"], 0)
        qk = q / 1000
        unit = next(u for u in STD_UNITS if u >= qk * 1.0)
        out.append(dict(r, q=round(qk, 2), unit=unit, unit_type=AC_ROOMS[key]))
    for i, o in enumerate(out, 1):
        o["mark"] = f"ВБ{i}"
    return out


if __name__ == "__main__":
    rooms = calc_air()
    for r in rooms:
        print(r["floor"], r["num"], r["name"], r["sup"], r["sup_sys"], r["exh"], r["exh_sys"])
    print(system_totals(rooms))
    ac = calc_cooling(rooms)
    for a in ac:
        print(a["mark"], a["name"], a["q"], a["unit"])
    print("sum q", sum(a["q"] for a in ac), "sum units", sum(a["unit"] for a in ac))
