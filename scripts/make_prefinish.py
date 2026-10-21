"""Бюджет дома «под чистовую отделку»: договор ООО «Строй Хауз» № 26/10-06/1 + всё, что в него
не входит, до начала чистовой отделки. Суммы в ₽, вывод в млн ₽."""
import csv
import io
import json
import os
import sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
import house_data as H
import make_rd_budget as R

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
SCRATCH = os.environ.get("SCRATCH", "/tmp")

CONTRACT = 43_500_000      # договор № 26/10-06/1, подписанная цена (42,0 — после допсоглашения)
CONTRACT_AGREED = 42_000_000
RESERVE = (0.10, 0.15)     # непредвиденные — на незаконтрактованную часть
LIGHT = ()                 # свет Maytoni (−50 %) уже в 291-ЭОМ

FLOOR = round(sum(r["area"] for r in H.heat_losses()))
FLOOR1 = round(sum(r["area"] for r in H.heat_losses() if r["floor"] == 1))
MAYTONI = []


def rd(code, exclude=()):
    return R.totals(code, exclude)["total"]


# Блоки: (группа, название, мин., макс., пометка)
def blocks():
    nc = "не входит в договор СХ"
    return [
        ("Коробка", "Строй Хауз: площадка, фундамент, брус, перекрытие, стропила, кровля, водосток "
         "(договор № 26/10-06/1)", CONTRACT, CONTRACT, "подписано 43,5; 42,0 после допсоглашения"),
        ("Коробка", "Окна и витражи ≈ 224–230 м², Schüco / Alutech, с монтажом и опциями",
         20_900_000, 26_500_000, "тендер: КП до 31.10"),
        ("Коробка", "Входные двери", 300_000, 800_000, nc),
        ("Коробка", "Защитное покрытие бруса снаружи (в течение 30 дней после сборки — условие "
         "гарантии), цоколь", 1_200_000, 2_200_000, nc),
        ("Коробка", "Каркасные перегородки (КД6)", 800_000, 1_400_000, nc),
        ("Коробка", f"Стяжка с тёплым полом 1 этажа ≈ {FLOOR1} м²", FLOOR1 * 1300, FLOOR1 * 2200, nc),
        ("Коробка", "Лестница, схема Б: металлокаркас + бетон, отделка, ограждение", 850_000,
         1_800_000, nc),
        ("Коробка", "Камин дровяной с дымоходом и подводом воздуха", 400_000, 1_200_000, nc),
        ("Коробка", "Отмостка", 500_000, 900_000, nc),
        ("Инженерия", "Вентиляция и кондиционирование, увлажнение", *rd("291-ОВК"), ""),
        ("Инженерия", "Отопление и котельная (пеллеты + электро)", *rd("291-ОВ"), ""),
        ("Инженерия", "Водопровод и канализация (без сантехприборов)", *rd("291-ВК"), ""),
        ("Инженерия", "Электрика, свет Maytoni (−50 %), батарея и генератор", *rd("291-ЭОМ"), ""),
        ("Инженерия", "Сеть, умный дом HA, камеры, домофон, охрана, базовое аудио", *rd("291-СС"), ""),
        ("Инженерия", "Аудио и кинозона сверх базового (5.1, экран/проектор)", 500_000, 1_500_000, ""),
        ("Инженерия", "Приводы штор и карнизы 12–15 шт.", 400_000, 900_000, ""),
        ("Инженерия", "Программирование и пусконаладка умного дома (интегратор)", 400_000, 1_000_000, ""),
        ("Инженерия", "Молниезащита, заземление, пожарная сигнализация", *rd("291-МЗ.ПС"), ""),
        ("Инженерия", "Наружные сети и подключения (вода, канализация, кабель, дренаж)",
         *rd("291-НС"), "до ТУ посёлка"),
        ("Организация", "Проектирование инженерии (тендер) и технадзор", 750_000, 1_800_000, ""),
        ("Организация", "Стройплощадка вне договора: электроэнергия 15 кВт, вода, охрана, дизель",
         400_000, 800_000, nc),
    ]


LATER = [  # не входит в «под чистовую»
    ("Чистовая отделка: полы, плитка, покраска бруса внутри, потолки, межкомнатные двери",
     8_800_000, 19_500_000),
    ("Сантехприборы по дизайн-проекту", 1_200_000, 3_500_000),
    ("Газ, этап 2 (2028): котёл, газопровод по участку, проект", 480_000, 1_190_000),
    ("Благоустройство: дорожки, настилы, озеленение, забор и ворота", 1_300_000, 4_500_000),
]
OPTIONS = [
    ("КНС на участке — только если нет самотёка (по ТУ)", 350_000, 800_000),
    ("Кухня, мебель, бытовая техника, ТВ", 5_000_000, 10_000_000),
]


def summary():
    b = blocks()
    var_lo = sum(x[2] for x in b[1:])
    var_hi = sum(x[3] for x in b[1:])
    res = (var_lo * RESERVE[0], var_hi * RESERVE[1])
    tot = (CONTRACT + var_lo + res[0], CONTRACT + var_hi + res[1])
    sh_opt = [x for x in b if "Строй Хауза" in x[4]]
    return dict(blocks=b, reserve=res, total=tot,
                sh_opt=(sum(x[2] for x in sh_opt), sum(x[3] for x in sh_opt)),
                groups={g: (sum(x[2] for x in b if x[0] == g), sum(x[3] for x in b if x[0] == g))
                        for g in ("Коробка", "Инженерия", "Организация")},
                later=LATER, options=OPTIONS, maytoni=MAYTONI, floor=FLOOR,
                turnkey=(CONTRACT + (var_lo + sum(x[1] for x in LATER)) * (1 + RESERVE[0]),
                         CONTRACT + (var_hi + sum(x[2] for x in LATER)) * (1 + RESERVE[1])),
                agreed_delta=CONTRACT - CONTRACT_AGREED)


def m(x):
    return round(x / 1e6, 1)


def xlsx(path, s):
    wb = Workbook()
    ws = wb.active
    ws.title = "Под чистовую"
    thin = Side(style="thin")
    brd = Border(left=thin, right=thin, top=thin, bottom=thin)
    ws.append(["Группа", "Блок", "Мин., ₽", "Макс., ₽", "Среднее, ₽", "Примечание"])
    for g, n, lo, hi, note in s["blocks"]:
        r = ws.max_row + 1
        ws.append([g, n, round(lo, -3), round(hi, -3), f"=(C{r}+D{r})/2", note])
    last = ws.max_row
    r = ws.max_row + 1
    ws.append(["", "Непредвиденные 10–15 % (на незаконтрактованную часть)",
               f"=ROUND({RESERVE[0]}*SUM(C3:C{last}),-3)", f"=ROUND({RESERVE[1]}*SUM(D3:D{last}),-3)",
               f"=(C{r}+D{r})/2", ""])
    t = ws.max_row + 1
    ws.append(["", "ИТОГО под чистовую", f"=SUM(C2:C{r})", f"=SUM(D2:D{r})", f"=(C{t}+D{t})/2", ""])
    ws.append([])
    ws.append(["", "После — не входит в итог", None, None, None, ""])
    for n, lo, hi in LATER:
        r2 = ws.max_row + 1
        ws.append(["Позже", n, lo, hi, f"=(C{r2}+D{r2})/2", ""])
    for sh, widths in ((ws, [14, 80, 15, 15, 15, 40]),):
        for c in sh[1]:
            c.font = Font(bold=True)
            c.fill = PatternFill("solid", fgColor="DDDDDD")
        for i, wdt in enumerate(widths):
            sh.column_dimensions[chr(65 + i)].width = wdt
        for row in sh.iter_rows(min_row=1, max_row=sh.max_row):
            for c in row:
                c.border = brd
                c.alignment = Alignment(wrap_text=True, vertical="center")
                if isinstance(c.value, (int, float)) or (isinstance(c.value, str) and c.value.startswith("=")):
                    c.number_format = "# ##0"
    for c in ws[t]:
        c.font = Font(bold=True)
    wb.save(path)


def to_csv(s):
    b = io.StringIO()
    w = csv.writer(b)
    w.writerow(["Группа", "Блок", "Мин., млн ₽", "Макс., млн ₽", "Примечание"])
    for g, n, lo, hi, note in s["blocks"]:
        w.writerow([g, n, m(lo), m(hi), note])
    w.writerow(["", "Непредвиденные 10–15 %", m(s["reserve"][0]), m(s["reserve"][1]), ""])
    w.writerow(["", "ИТОГО под чистовую", m(s["total"][0]), m(s["total"][1]), ""])
    w.writerow([])
    for n, lo, hi in LATER:
        w.writerow(["Позже (не в итоге)", n, m(lo), m(hi), ""])
    w.writerow(["", "ПОД КЛЮЧ (под чистовую + позже)", m(s["turnkey"][0]), m(s["turnkey"][1]), ""])
    for n, lo, hi in OPTIONS:
        w.writerow(["Опции (не в итоге)", n, m(lo), m(hi), ""])
    return b.getvalue()


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    s = summary()
    xlsx(os.path.join(OUT, "Бюджет под чистовую — Берта Ромарио.xlsx"), s)
    open(os.path.join(SCRATCH, "prefinish.csv"), "w").write(to_csv(s))
    json.dump(s, open(os.path.join(SCRATCH, "prefinish.json"), "w"), ensure_ascii=False, indent=1)
    for g, n, lo, hi, note in s["blocks"]:
        print(f"{g:12} {n[:70]:70} {m(lo):6} {m(hi):6} {note}")
    print("резерв", m(s["reserve"][0]), m(s["reserve"][1]))
    print("ИТОГО", m(s["total"][0]), m(s["total"][1]), "группы", {k: (m(a), m(b)) for k, (a, b) in s["groups"].items()})
    print("под ключ", m(s["turnkey"][0]), m(s["turnkey"][1]))
