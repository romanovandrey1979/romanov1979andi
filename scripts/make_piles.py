"""Нагрузка на каждую сваю: проверочный расчёт заказчика по КЖ0, РПЗ КЖ0 и ИГИ.

Координаты 74 свай — с векторного листа 5 КЖ0 (план свайного поля), нагрузки проектировщика —
с рис. 19 РПЗ (подписи сопоставлены со сваями аффинным преобразованием). Собственный расчёт:
сбор нагрузок по РПЗ и спецификации бруса КД1, плита 250 мм — грильяж на упругих опорах-сваях,
стены — балки над плитой с разной изгибной жёсткостью. Несущая способность сваи — СП 24.13330.2021,
табл. 7.2, 7.3, ф. 7.9.

Запуск: python3 make_piles.py (нужны pymupdf, scipy).
"""
import os
import re

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as sla
import pymupdf
from scipy.optimize import linear_sum_assignment
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from openpyxl import Workbook

from docbuild import Doc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "00_Исходные_данные")
OUT = os.path.join(ROOT, "Заключение")
SCRATCH = os.environ.get("SCRATCH", "/tmp/piles")
KJ0 = os.path.join(SRC, "КЖ0.Фундамент Берта Ромарио 29.09.26.pdf")
RPZ = os.path.join(SRC, "РПЗ КЖ0 Берта Ромарио_30.09.26.pdf")

# ---------------------------------------------------------------- исходные данные
PT_M = 72 / 25.4 * 10          # pt листа на метр натуры при М 1:100
AXIS2_PT, AXISB_PT = 229.4, 521.4

# участки плиты по осям КЖ0 (м от осей 2 и Б), бетон на 0,1 м за осями (лист 6 КЖ0)
RECTS = [(-0.1, 7.3, 1.5, 16.0), (7.3, 14.0, 3.9, 8.2), (14.0, 22.3, -0.1, 13.0)]

# расчётные нагрузки РПЗ (рис. 2–11), кН/м² и кН/м
Q_SLAB, Q_FLOOR1, Q_PART, Q_LIVE = 6.74, 4.97, 1.20, 1.95
Q_FLOOR2, Q_ATTIC, Q_ROOF, Q_SNOW = 2.39, 0.36, 0.64, 2.10
Q_STRIP, Q_WALL = 1.10, 1.55
BRUS_M3, BRUS_B = 228.53, 0.24  # спецификация КД1: брус клеёный 240×320, м³
OVH = 0.7                       # свес кровли, м (принят)

K_PILE = 35e3                   # кН/м: осадка 2,88 мм в РПЗ при ≈ 100 кН на сваю
E_SLAB = 28.5e6                 # кПа, бетон B22,5
H_SLAB = 0.25
WALL_CASES = [                  # изгибная жёсткость стены над плитой, кН·м²
    ("Только плита", 0.0, "стены не работают как балки"),
    ("Брус, венцы раздельно", 1.0e5, "≈ 14 венцов 240×310 мм, E = 11,5 ГПа, без совместной работы"),
    ("10 % сплошной стены", 2.1e6, "частичная совместная работа венцов (нагели, шпильки)"),
    ("Сплошная стена", 2.1e7, "стена-диафрагма высотой 4,5 м — как оболочки в модели ЛИРА"),
]
N_DESIGN_MAX = 137.8
FD_RPZ = 198.41
GK_CALC, GK_DYN = 1.4, 1.25


def pile_coords():
    page = pymupdf.open(KJ0)[5]
    pts = []
    for d in page.get_drawings():
        r = d["rect"]
        if 5.5 < r.width < 5.8 and 5.5 < r.height < 5.8 and r.y0 < 600:
            c = ((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2)
            if not any(abs(c[0] - a) < 1.5 and abs(c[1] - b) < 1.5 for a, b in pts):
                pts.append(c)
    p = np.array(pts)
    xy = np.c_[(p[:, 0] - AXIS2_PT) / PT_M, (AXISB_PT - p[:, 1]) / PT_M]
    # нумерация: ряды сверху (ось П) вниз, в ряду слева направо
    order = sorted(range(len(xy)), key=lambda i: (-round(xy[i, 1] / 0.15), xy[i, 0]))
    return xy[order]


def lira_loads(P):
    page = pymupdf.open(RPZ)[12]
    W = page.get_text("words")
    lab = np.array([((w[0] + w[2]) / 2, (w[1] + w[3]) / 2, float(w[4])) for w in W
                    if re.fullmatch(r"-?\d+\.\d+", w[4]) and 60 < w[1] < 267])
    U = lab[:, :2]
    Ph = np.c_[P, np.ones(len(P))]
    best = None
    for th in np.linspace(0, 2 * np.pi, 72, endpoint=False):
        for flip in (1, -1):
            for sc in (12, 15, 18):
                for sy in (0.4, 0.6, 0.8, 1.0):
                    R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]]) \
                        @ np.diag([sc, flip * sc * sy])
                    Q = P @ R.T
                    Q += U.mean(0) - Q.mean(0)
                    for _ in range(15):
                        C = ((Q[:, None] - U[None]) ** 2).sum(-1)
                        r, c = linear_sum_assignment(C)
                        A = np.linalg.lstsq(Ph[r], U[c], rcond=None)[0]
                        Q = Ph @ A
                    C = ((Q[:, None] - U[None]) ** 2).sum(-1)
                    r, c = linear_sum_assignment(C)
                    e = np.sqrt(C[r, c].mean())
                    if best is None or e < best[0]:
                        best = (e, c.copy())
    assert best[0] < 1.0, best[0]
    return lab[best[1], 2]


def inside(x, y):
    return any(a - 1e-9 <= x <= b + 1e-9 and c - 1e-9 <= y <= d + 1e-9 for a, b, c, d in RECTS)


def wall_lines(P, tol=0.08, gap=3.6):
    """Стены — по рядам свай (сваи стоят под стенами КД1); пролёт между сваями ≤ 3,6 м."""
    segs = []
    for k in (0, 1):                     # 0 — стена вдоль Y (x = const), 1 — вдоль X
        used = set()
        for v in np.unique(np.round(P[:, k] / 0.05) * 0.05):
            idx = np.where(abs(P[:, k] - v) < tol)[0]
            key = tuple(sorted(idx))
            if len(idx) < 2 or key in used:
                continue
            used.add(key)
            o = np.sort(P[idx, 1 - k])
            for a, b in zip(o[:-1], o[1:]):
                m = (a + b) / 2
                if b - a <= gap and inside(*((v, m) if k == 0 else (m, v))):
                    segs.append((k, float(np.mean(P[idx, k])), a, b))
    # парные сваи под колоннами у оси 12 и сдвоенные сваи у оси 7 — не стены
    segs = [g for g in segs if not (g[0] == 0 and 18.2 < g[1] < 19.0 and g[3] < 6.5)
            and not (g[0] == 0 and 6.4 < g[1] < 6.7)]
    segs.append((1, 0.05, 13.96, 17.86))   # наружная стена по оси Б между осями 9 и 11
    return segs


def is_perimeter(g):
    k, v, a, b = g
    m = (a + b) / 2
    pts = [(v + .25, m), (v - .25, m)] if k == 0 else [(m, v + .25), (m, v - .25)]
    return sum(inside(*p) for p in pts) == 1


def take_down(segs, s=0.1):
    """Сбор нагрузок: по площади плиты и погонные по стенам (кН/м)."""
    xs = np.arange(-0.05, 22.3, s)
    ys = np.arange(-0.05, 16.0, s)
    trib = np.zeros(len(segs))
    area = 0.0
    for x in xs:
        for y in ys:
            if not inside(x, y):
                continue
            area += s * s
            d = [abs(x - v) + max(0, a - y, y - b) if k == 0 else abs(y - v) + max(0, a - x, x - b)
                 for k, v, a, b in segs]
            trib[int(np.argmin(d))] += s * s
    L = np.array([b - a for _, _, a, b in segs])
    per = np.array([is_perimeter(g) for g in segs])
    q_f2 = Q_FLOOR2 + Q_PART + Q_LIVE
    q_rf = Q_ATTIC + Q_ROOF + Q_SNOW
    w_brus = BRUS_M3 / BRUS_B * Q_WALL
    roof_area = trib + per * L * OVH
    line = w_brus / L.sum() + (trib * q_f2 + roof_area * q_rf) / L + per * Q_STRIP
    parts = [
        ("Плита 250 мм", Q_SLAB, area),
        ("Пол 1 этажа (стяжка, утеплитель, подсыпка)", Q_FLOOR1, area),
        ("Перегородки 1 этажа", Q_PART, area),
        ("Полезная 1 этажа", Q_LIVE, area),
        ("Перекрытие 2 этажа, перегородки, полезная", q_f2, area),
        ("Чердак, кровля, снег (с учётом свеса 0,7 м)", q_rf, roof_area.sum()),
        ("Брусовые стены: 228,5 м³ по КД1 = 952 м² стен", Q_WALL, BRUS_M3 / BRUS_B),
        ("Подвенечная лента, кН/м", Q_STRIP, (L * per).sum()),
    ]
    return dict(area=area, L=L, per=per, line=line, parts=parts,
                total=sum(q * a for _, q, a in parts))


def solve(P, segs, line, EIw=0.0, k=K_PILE, s=0.1, E=E_SLAB, h=H_SLAB, extra=(), loads=True):
    """Плита — грильяж с шагом s (изгиб + кручение, Hambly), сваи — пружины, стены — балки."""
    xs = np.arange(-0.1, 22.3 + 1e-9, s)
    ys = np.arange(-0.1, 16.0 + 1e-9, s)
    ids = -np.ones((len(xs), len(ys)), int)
    n = 0
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            if inside(x, y):
                ids[i, j] = n
                n += 1
    nd = 3 * n                     # w, φx = ∂w/∂x, φy = ∂w/∂y
    rows, cols, vals = [], [], []

    def add(dofs, K):
        for a in range(len(dofs)):
            for b in range(len(dofs)):
                rows.append(dofs[a])
                cols.append(dofs[b])
                vals.append(K[a, b])

    I, J, G, L = s * h ** 3 / 12, s * h ** 3 / 6, E / 2.4, s

    def kb(EI):
        return EI / L ** 3 * np.array([[12, 6 * L, -12, 6 * L], [6 * L, 4 * L * L, -6 * L, 2 * L * L],
                                       [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L * L, -6 * L, 4 * L * L]])
    kt = G * J / L * np.array([[1, -1], [-1, 1]])

    def on_wall(kind, x, y):
        for kk, v, a, b in segs:
            c, t = (x, y) if kk == 0 else (y, x)
            if kk == kind and abs(c - v) < s / 2 + 1e-6 and a - 1e-6 <= t <= b + 1e-6:
                return True
        return False

    for i in range(len(xs)):
        for j in range(len(ys)):
            p = ids[i, j]
            if p < 0:
                continue
            if i + 1 < len(xs) and ids[i + 1, j] >= 0:
                q = ids[i + 1, j]
                EI = E * I + (EIw if on_wall(1, xs[i] + s / 2, ys[j]) else 0)
                add([3 * p, 3 * p + 1, 3 * q, 3 * q + 1], kb(EI))
                add([3 * p + 2, 3 * q + 2], kt)
            if j + 1 < len(ys) and ids[i, j + 1] >= 0:
                q = ids[i, j + 1]
                EI = E * I + (EIw if on_wall(0, xs[i], ys[j] + s / 2) else 0)
                add([3 * p, 3 * p + 2, 3 * q, 3 * q + 2], kb(EI))
                add([3 * p + 1, 3 * q + 1], kt)

    def node(x, y):
        return ids[int(round((x + 0.1) / s)), int(round((y + 0.1) / s))]

    F = np.zeros(nd)
    if loads:
        F[0::3] -= (Q_SLAB + Q_FLOOR1 + Q_PART + Q_LIVE) * s * s
        for (kind, v, a, b), q in zip(segs, line):
            t = np.arange(a, b + 1e-9, s)
            for u in t:
                p = node(*((v, u) if kind == 0 else (u, v)))
                if p >= 0:
                    F[3 * p] -= q * s * (0.5 if u in (t[0], t[-1]) else 1)
    for x, y, f in extra:
        F[3 * node(x, y)] -= f
    pn = np.array([node(x, y) for x, y in P])
    for p in pn:
        rows.append(3 * p)
        cols.append(3 * p)
        vals.append(k)
    K = sp.csc_matrix((vals, (rows, cols)), shape=(nd, nd))
    u = sla.spsolve(K, F)
    return -k * u[3 * pn], -F.sum()


# ---------------------------------------------------------------- несущая способность (СП 24)
F73 = {1: (35, 23, 15), 2: (42, 30, 21), 3: (48, 35, 25), 4: (53, 38, 27), 5: (56, 40, 29)}
R72 = {3: (3100, 2000, 1200), 4: (3200, 2500, 1600), 5: (3400, 2800, 2000)}
# столбцы: песок средней крупности средней плотности; суглинок IL 0,3; суглинок IL 0,4


def _tab(tab, z, c):
    ks = sorted(tab)
    return float(np.interp(min(max(z, ks[0]), ks[-1]), ks, [tab[k][c] for k in ks]))


def fd(L, loam=0.0, IL=0.4, top=0.2):
    """Fd = R·A + u·Σf·h, свая 200×200, γc = γcR = γcf = 1; L — глубина острия от рельефа."""
    col = 1 if IL <= 0.3 else 2
    bounds = sorted({top, min(top + loam, L) if loam > 0 else top, L})
    sfh = 0.0
    for a, b in zip(bounds[:-1], bounds[1:]):
        n = int(np.ceil((b - a) / 1.0))
        for i in range(n):
            za, zb = a + (b - a) * i / n, a + (b - a) * (i + 1) / n
            c = col if (loam > 0 and zb <= top + loam + 1e-9) else 0
            sfh += _tab(F73, (za + zb) / 2, c) * (zb - za)
    R = _tab(R72, L, col if (loam > 0 and L <= top + loam + 1e-9) else 0)
    return R, sfh, R * 0.04 + 0.8 * sfh


GEO = [  # (разрез, глубина острия от рельефа, м, суглинок сверху, м, IL)
    ("Песок (скв. 6), глубина как в РПЗ", 2.45, 0, 0.4),
    ("Песок (скв. 6), рельеф на 1,2 м ниже ±0", 2.9, 0, 0.4),
    ("Песок (скв. 6), рельеф на 0,7 м ниже ±0", 3.4, 0, 0.4),
    ("Суглинок 1,0 м, остриё в песке", 3.4, 1.0, 0.4),
    ("Суглинок 2,4 м, остриё в песке, IL 0,3", 3.4, 2.4, 0.3),
    ("Суглинок 2,4 м, остриё в песке, IL 0,4", 3.4, 2.4, 0.4),
    ("Суглинок 4,2 м, остриё в суглинке, IL 0,3", 3.4, 4.2, 0.3),
    ("Суглинок 4,2 м, остриё в суглинке, IL 0,4", 3.4, 4.2, 0.4),
    ("То же, свая 6 м (остриё на 5,4 м — в песке), IL 0,4", 5.4, 4.2, 0.4),
]


# ---------------------------------------------------------------- рисунки
def fig_maps(P, cases, path):
    fig, axs = plt.subplots(2, 2, figsize=(11.5, 8.6))
    vmax = 230
    for ax, (title, R) in zip(axs.ravel(), cases):
        for a, b, c, d in RECTS:
            ax.add_patch(plt.Rectangle((a, c), b - a, d - c, fill=True, fc="#f2f2f2", ec="#888", lw=0.8))
        over = R > FD_RPZ / GK_CALC
        sc = ax.scatter(P[:, 0], P[:, 1], c=R, cmap="YlOrRd", vmin=40, vmax=vmax, s=55,
                        edgecolors=np.where(over, "#b00000", "#555"), linewidths=np.where(over, 1.8, 0.4),
                        zorder=3)
        for i, (x, y) in enumerate(P):
            ax.text(x, y - 0.55, f"{R[i]:.0f}", fontsize=5.2, ha="center", zorder=4)
        ax.set_title(f"{title}: {R.min():.0f}–{R.max():.0f} кН, выше 141,7 кН — {int(over.sum())}",
                     fontsize=9)
        ax.set_aspect("equal")
        ax.set_xlim(-1, 23.2)
        ax.set_ylim(-1.2, 16.8)
        ax.tick_params(labelsize=6)
    cb = fig.colorbar(sc, ax=axs, shrink=0.6, pad=0.02)
    cb.set_label("Расчётная нагрузка на сваю, кН", fontsize=8)
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)


def fig_numbers(P, segs, path):
    fig, ax = plt.subplots(figsize=(11, 8))
    for a, b, c, d in RECTS:
        ax.add_patch(plt.Rectangle((a, c), b - a, d - c, fill=True, fc="#f4f4f4", ec="#666", lw=1))
    for k, v, a, b in segs:
        ax.plot([v, v] if k == 0 else [a, b], [a, b] if k == 0 else [v, v], color="#8fb98f", lw=3,
                alpha=0.7, zorder=1)
    ax.scatter(P[:, 0], P[:, 1], marker="s", s=28, c="#333", zorder=3)
    for i, (x, y) in enumerate(P, 1):
        ax.text(x + 0.12, y + 0.15, str(i), fontsize=7, color="#003a8c", zorder=4)
    ax.set_aspect("equal")
    ax.set_xlabel("м от оси 2", fontsize=8)
    ax.set_ylabel("м от оси Б", fontsize=8)
    ax.tick_params(labelsize=7)
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def fig_compare(N, cases, path):
    fig, ax = plt.subplots(figsize=(10, 4.2))
    order = np.argsort(-N)
    ax.plot(range(74), N[order], "k-", lw=2, label="Проектировщик (ЛИРА-САПР)")
    for (nm, R), col in zip(cases, ("#d62728", "#ff7f0e", "#2ca02c", "#1f77b4")):
        ax.plot(range(74), R[order], ".", color=col, ms=5, label=nm)
    for y, lb in ((FD_RPZ / GK_CALC, "Fd/1,4 = 141,7 (РПЗ, без испытаний)"),
                  (fd(3.4)[2] / GK_CALC, "Fd/1,4 на глубине 3,4 м"),
                  (fd(3.4)[2] / GK_DYN, "Fd/1,25 на 3,4 м после динамических испытаний")):
        ax.axhline(y, ls="--", lw=0.8, color="#555")
        ax.text(73, y + 2, lb, fontsize=6.5, ha="right")
    ax.set_xlabel("Сваи по убыванию нагрузки у проектировщика", fontsize=8)
    ax.set_ylabel("кН", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=7, loc="upper right", ncol=2)
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- документ
def f0(x):
    return f"{x:.0f}"


def f1(x):
    return f"{x:.1f}".replace(".", ",")


def build():
    os.makedirs(SCRATCH, exist_ok=True)
    P = pile_coords()
    N = lira_loads(P)
    segs = wall_lines(P)
    td = take_down(segs)
    res = []
    for nm, EIw, _ in WALL_CASES:
        R, tot = solve(P, segs, td["line"], EIw)
        res.append((nm, R))
    sens = {kk: solve(P, segs, td["line"], EIw, k=kk)[0]
            for kk in (70e3,) for nm, EIw, _ in WALL_CASES[1:2]}
    test, _ = solve(P, segs, td["line"], extra=[(3.56, 8.15, 100.0)], loads=False)

    fd_rpz = fd(2.45)[2]
    fd34 = fd(3.4)[2]
    allow = FD_RPZ / GK_CALC
    R_b = res[1][1]
    n_over_b = int((R_b > allow).sum())
    over_txt = ", ".join(str(i + 1) for i in np.argsort(-R_b)[:n_over_b])

    maps = os.path.join(SCRATCH, "piles_maps.png")
    nums = os.path.join(SCRATCH, "piles_numbers.png")
    comp = os.path.join(SCRATCH, "piles_compare.png")
    fig_maps(P, [("Проектировщик (ЛИРА)", N)] + [(nm, R) for nm, R in (res[0], res[1], res[3])], maps)
    fig_numbers(P, segs, nums)
    fig_compare(N, res, comp)

    d = Doc("Нагрузка на каждую сваю — проверочный расчёт по КЖ0, РПЗ и геологии",
            "Индивидуальный жилой дом «Ромарио», посёлок «Берта», г. о. Истра, участок 1. "
            "Исходные данные: 291-КЖ0 «Фундамент» от 29.09.2026 (ООО «Строй Хауз»), расчётно-"
            "пояснительная записка к КЖ0 от 30.09.2026 (ЛИРА-САПР 2022), 291-КД1 «Разбрусовка» от "
            "30.09.2026, технический отчёт ИГИ 2026-07.840 (ООО «Геолог»). Подготовлено заказчиком "
            "21.10.2026 для обсуждения с руководством посёлка, техническим надзором и проектировщиком.")
    d.h1("Коротко")
    d.table([
        ("Показатель", "Проектировщик", "Наш расчёт"),
        ("Свай по плану, в ведомости и в модели", "74", "74"),
        ("Сумма расчётных нагрузок на сваи, кН", "8 282", f"{td['total']:,.0f}".replace(",", " ")),
        ("Самая нагруженная свая", "№ 30 (ось 4 × ряд К), 137,7 кН", "та же № 30"),
        ("Несущая способность Fd на глубине 2,45 м, кН", "198,4", f0(fd_rpz)),
        ("Допустимая нагрузка Fd/1,4, кН", "141,7", f1(fd_rpz / GK_CALC)),
        ("Использование самой нагруженной сваи", "0,97", "0,97 при жёстких стенах; до "
         f"{R_b.max() / allow:.2f} при брусе без совместной работы венцов".replace(".", ",")),
    ], [3.4, 2.3, 3.3])
    d.items([
        "Да, по проекту и геологии нагрузку на каждую сваю посчитать можно. Мы сделали это "
        "независимо от модели проектировщика. Общая нагрузка сходится: у нас на "
        f"{(1 - td['total'] / 8282) * 100:.0f} % меньше, то есть модель проектировщика с запасом. "
        "Несущая способность сваи по скважине 6 сходится с РПЗ в пределах 3 %.",
        "Расхождение — в распределении нагрузки между сваями, и оно зависит от одного допущения: "
        "работают ли брусовые стены как жёсткие балки. В модели проектировщика стены — сплошные "
        "оболочки, поэтому нагрузки выровнены (69–138 кН) и все сваи проходят с запасом 3 %. "
        "Если венцы бруса работают раздельно (нагели и шпильки не делают из них монолит), то "
        f"нагрузка собирается на сваях под пересечениями внутренних стен: {n_over_b} свай выше "
        f"141,7 кН, максимум {R_b.max():.0f} кН — на тех же сваях оси 4, которые и у проектировщика "
        "самые нагруженные.",
        "Запас 3 % на самой нагруженной свае — это практически ноль: его съест любая неточность "
        "в нагрузках или грунте. Резервы есть, но их надо подтвердить: фактическая глубина "
        "острия от рельефа (в РПЗ — 2,45 м; остриё по КЖ0 на отметке −4,14, и при земле на 0,7 м "
        f"ниже ±0,000 глубина 3,4 м, Fd растёт до {fd34:.0f} кН) и динамические испытания свай (коэффициент 1,4 заменяется на 1,25).",
        "Геология важнее модели. РПЗ построена по одной скважине 6 (песок с 0,2 до 5 м). Если "
        "под частью дома сверху лежит тугопластичный суглинок, как в соседних скважинах, "
        "4-метровая свая теряет 7–55 % несущей способности, а при суглинке толще 4 м "
        "не проходит.",
        "Чего расчёт дать не может: фактическую несущую способность конкретной сваи. Её дают "
        "только отказы при забивке и динамические испытания. Расчёт показывает, какие сваи "
        "проверять в первую очередь и что спросить у проектировщика.",
    ])
    d.h1("Что сделать")
    d.items([
        "Проектировщику (Строй Хауз): (а) показать привязку скважины 6 к пятну дома и разрезы "
        "ближайших скважин; если в пятне есть суглинок — контрольное зондирование в 2–3 точках; "
        "(б) пересчитать Fd по фактической глубине острия от природного рельефа (отметка ±0,000 "
        "в абсолютных, отметки рельефа в точках свай); (в) выполнить вариант расчёта с "
        "пониженной жёсткостью брусовых стен (раздельные венцы) и показать нагрузки на сваи "
        f"№ {over_txt}; (г) подтвердить, учтён ли коэффициент "
        "γ0 = 1,15 для свайного поля (п. 7.1.11 СП 24.13330) — это дополнительный резерв.",
        f"Динамические испытания не менее 6 свай (ГОСТ 5686): в первую очередь № {over_txt}. "
        "По результатам — допустимая нагрузка с коэффициентом 1,25 и решение: оставить 4 м, "
        "удлинить наиболее нагруженные сваи до 5–6 м или добавить сваи.",
        "Журнал забивки с отказом по каждой свае. Если отказ не достигнут на проектной "
        "глубине или резко отличается от соседних свай — остановка и решение проектировщика.",
        "Если сваи уже забиты: запросить журнал забивки и протоколы испытаний — по ним "
        "несущая способность каждой сваи известна по факту, и расчёт выше уточняется.",
        "Сваи 4 м с заделкой в плиту при промерзании работают на выдёргивание (РПЗ: запас 1,03 "
        "без нагрузки от дома). Не оставлять забитые сваи без плиты на зиму в пучинистом "
        "грунте; плиту — до устойчивых морозов или с утеплением основания.",
    ], numbered=True)

    d.h1("1. Исходные данные")
    d.table([
        ("Источник", "Что взято"),
        ("КЖ0, лист 5 «План свайного поля»", "Координаты 74 свай С40.20-3 (200×200, L = 4 м, B25) "
         "сняты с векторного чертежа М 1:100; отметка верха забитой сваи −0,140, после срубки −0,540"),
        ("КЖ0, лист 6 «План плиты»", "Контур плиты 250 мм (B22,5) по осям 2–13 / Б–П, подвенечная "
         f"лента по периметру; площадь плиты {td['area']:.0f} м²"),
        ("РПЗ КЖ0 (ЛИРА-САПР 2022)", "Нагрузки (рис. 2–11), нагрузка на каждую сваю (рис. 19, "
         "сумма 8 282 кН, 69–137,7 кН), Fd = 198,41 кН (рис. 20), использование 0,49–0,97 "
         "(рис. 21), осадка 2,88 мм, скважина 6, проверка на пучение"),
        ("КД1, спецификация", "Брус клеёный 240×320 — 228,53 м³; развёртки по осям — "
         "расположение несущих стен"),
        ("ИГИ 2026-07.840 (ООО «Геолог»)", "Скважина 6 (абс. 177,00): 0,0–0,2 почвенный слой, "
         "0,2–5,0 песок средней крупности средней плотности (ИГЭ-2), воды нет. Суглинок "
         "тугопластичный (ИГЭ-1) — в части скважин участка; промерзание 1,03 м"),
        ("СП 24.13330.2021", "Табл. 7.2, 7.3, ф. 7.9; γc = γcR = γcf = 1 (забивные сваи); "
         "γk = 1,4 по расчёту, 1,25 по динамическим испытаниям"),
    ], [2.2, 6.8])

    d.h1("2. Сбор нагрузок")
    rows = [("Нагрузка", "кН/м² (кН/м)", "Площадь, м² (длина, м)", "Итого, кН")]
    for nm, q, a in td["parts"]:
        rows.append((nm, f"{q:.2f}".replace(".", ","), f"{a:.0f}", f"{q * a:,.0f}".replace(",", " ")))
    rows.append(("Итого на сваи", "", "", f"{td['total']:,.0f}".replace(",", " ")))
    d.table(rows, [5.2, 1.4, 1.8, 1.2], bold_last=True)
    d.small("Удельные нагрузки — расчётные значения из РПЗ (с коэффициентами надёжности). Вес "
            "стен — по объёму бруса из спецификации КД1. Перекрытие 2 этажа и кровля переданы на "
            "ближайшие стены (грузовые полосы). Наш итог на "
            f"{(1 - td['total'] / 8282) * 100:.0f} % меньше, чем в модели проектировщика: "
            "ЛИРА учитывает нагрузки с запасом, сбор нагрузок у проектировщика достаточный.")

    d.h1("3. Как распределяется нагрузка между сваями")
    d.p("Плита 250 мм рассчитана как перекрёстная система балок с шагом 0,1 м (изгиб и кручение), "
        f"сваи — упругие опоры {K_PILE / 1e3:.0f} МН/м (из осадки 2,88 мм в РПЗ). Стены поставлены "
        f"по рядам свай (сваи стоят под стенами КД1), длина стен {td['L'].sum():.0f} м, из них "
        f"наружных {(td['L'] * td['per']).sum():.0f} м. Стены заданы балками над плитой "
        "в четырёх вариантах жёсткости:")
    d.table([("Вариант", "Жёсткость стены", "Мин–макс, кН", "Свай > 141,7 кН", "Свай > "
              f"{fd34 / GK_CALC:.0f} кН")] +
            [(nm, desc, f"{R.min():.0f}–{R.max():.0f}", str(int((R > allow).sum())),
              str(int((R > fd34 / GK_CALC).sum()))) for (nm, _, desc), (_, R) in zip(WALL_CASES, res)] +
            [("Проектировщик (ЛИРА)", "стены — оболочки", f"{N.min():.0f}–{N.max():.0f}", "0", "0")],
            [2.2, 4.2, 1.3, 1.3, 1.3])
    d.small(f"Чувствительность: при жёсткости свай 70 МН/м вместо 35 вариант «брус» даёт максимум "
            f"{sens[70e3].max():.0f} кН. Проверка модели: сила 100 кН над сваей № 30 "
            f"распределяется на 74 сваи с суммой {f1(test.sum())} кН, на саму сваю — {test.max():.0f} кН.")
    d.image(maps, 180)
    d.small("Рис. 1. Нагрузка на каждую сваю, кН: модель проектировщика и наши варианты. "
            "Красная обводка — выше 141,7 кН (Fd/1,4 по РПЗ).")
    d.image(comp, 175)
    d.small("Рис. 2. Сваи по убыванию нагрузки у проектировщика и наши варианты. Самые "
            "нагруженные сваи совпадают; разница — в том, сколько нагрузки стены отдают в углы.")
    d.p("Вывод: при жёстких стенах наш расчёт подтверждает модель проектировщика "
        f"(максимум {res[3][1].max():.0f} против 137,7 кН). Клеёный брус 240×310 мм собран "
        "из отдельных венцов на нагелях Ø32 и шпильках М12; сплошной стеной-диафрагмой он не "
        "является, особенно в первые годы, пока идёт усадка. Реальная работа — между вариантами "
        "«брус» и «10 %». Поэтому сваи под пересечениями внутренних стен (№ " + over_txt +
        ") требуют подтверждения испытаниями или запаса по длине.")

    d.h1("4. Несущая способность сваи по грунту")
    rows = [("Разрез под сваей", "Остриё от рельефа, м", "R, кПа", "Σf·h, кПа·м", "Fd, кН",
             "Fd/1,4, кН", "Fd/1,25, кН", "Запас к 137,8 кН")]
    hl = {}
    for i, (nm, L, loam, IL) in enumerate(GEO, 1):
        R, sfh, F = fd(L, loam, IL)
        m = F / GK_CALC / N_DESIGN_MAX - 1
        rows.append((nm, f"{L:.2f}".rstrip("0").replace(".", ","), f0(R), f0(sfh), f0(F), f0(F / GK_CALC), f0(F / GK_DYN),
                     f"{m * 100:+.0f} %".replace("-0 %", "0 %").replace("+0 %", "0 %")))
        hl[(i, 7)] = "#f8d7d7" if m < 0 else "#d9efd9"
    d.table(rows, [3.6, 1.1, 0.8, 0.9, 0.8, 0.9, 0.9, 1.0], highlight=hl)
    d.small("Fd = R·A + u·Σf·h, A = 0,04 м², u = 0,8 м; глубины — от природного рельефа, почвенный "
            "слой в трение не включён. Проверка метода: по скважине 6 на глубине 2,45 м получено "
            f"{fd_rpz:.0f} кН против 198,41 кН в РПЗ. Острие сваи по КЖ0 — на отметке −4,14 "
            "(верх забитой сваи −0,140 + 4,0 м); глубина от рельефа зависит от отметки земли в "
            "точке сваи: при рельефе на 1,7 м ниже ±0,000 — 2,45 м (как в РПЗ), на 0,7 м ниже — "
            "3,4 м. Показатель текучести суглинка в ИГИ не дан, «тугопластичный» — IL 0,25–0,5.")
    d.p("Вывод: в песке свая 4 м проходит, запас от 0 до 20 % — в зависимости от фактической "
        "глубины. Под суглинком 2,4 м запас почти исчезает (от +7 до −1 %); лечится испытаниями "
        "(коэффициент 1,25) или сваей 5 м. Под суглинком 4,2 м свая 4 м не проходит при любых "
        "допущениях — нужна свая около 6 м с опиранием в песок. Поэтому первый вопрос — где именно "
        "под пятном дома суглинок.")

    d.pagebreak()
    d.h1("5. Таблица по каждой свае")
    d.image(nums, 165)
    d.small("Рис. 3. Нумерация свай: ряды сверху (ось П) вниз, в ряду слева (ось 2) направо. "
            "Зелёные линии — стены, принятые в расчёте.")
    rows = [("№", "x от оси 2, м", "y от оси Б, м", "ЛИРА, кН", "Плита, кН", "Брус, кН",
             "10 %, кН", "Сплошная, кН", "ЛИРА / 141,7", "Брус / 141,7")]
    hl = {}
    for i, (x, y) in enumerate(P):
        r = [str(i + 1), f"{x:.2f}".replace(".", ","), f"{y:.2f}".replace(".", ","), f1(N[i])] + \
            [f0(R[i]) for _, R in res] + [f"{N[i] / allow:.2f}".replace(".", ","),
                                          f"{R_b[i] / allow:.2f}".replace(".", ",")]
        rows.append(r)
        if R_b[i] > allow:
            hl[(i + 1, 9)] = "#f8d7d7"
            hl[(i + 1, 5)] = "#f8d7d7"
    rows.append(("Итого", "", "", f0(N.sum())) + tuple(f0(R.sum()) for _, R in res) +
                (f"{N.max() / allow:.2f}".replace(".", ","), f"{R_b.max() / allow:.2f}".replace(".", ",")))
    d.table(rows, [0.5, 0.9, 0.9, 0.8, 0.8, 0.8, 0.8, 0.9, 0.9, 0.9], bold_last=True, highlight=hl)
    d.small("Нагрузки — расчётные, по самому невыгодному сочетанию. Розовым — сваи, у которых в "
            "варианте «брус» нагрузка выше 141,7 кН. Координаты — по центрам свай, точность "
            "±0,05 м; значения ЛИРА — с рис. 19 РПЗ.")
    d.h1("6. Ограничения")
    d.small("Расчёт проверочный и не заменяет расчёт проектировщика и испытания свай. Не "
            "моделировались: рёбра и лента плиты (кроме веса), проёмы в стенах, колонны и лестница, "
            "переменная жёсткость грунта по площади. Перекрытие 2 этажа и кровля переданы на "
            "ближайшие стены без расчёта балок КД4 и стропил КД5. Разрезы скважин, кроме скважины 6, "
            "учтены как сценарии; привязка скважин к пятну дома по генплану — открытый вопрос.")

    os.makedirs(OUT, exist_ok=True)
    pdf = os.path.join(OUT, "Нагрузка на каждую сваю — проверочный расчёт.pdf")
    d.pdf(pdf, footer="Дом «Ромарио» · нагрузка на каждую сваю · 21.10.2026")
    open(os.path.join(SCRATCH, "piles.html"), "w").write(d.html())

    wb = Workbook()
    ws = wb.active
    ws.title = "Сваи"
    ws.append(["№", "x от оси 2, м", "y от оси Б, м", "ЛИРА, кН"] + [nm + ", кН" for nm, _ in res])
    for i, (x, y) in enumerate(P):
        ws.append([i + 1, round(float(x), 2), round(float(y), 2), round(float(N[i]), 1)] +
                  [round(float(R[i]), 1) for _, R in res])
    ws2 = wb.create_sheet("Fd")
    ws2.append(["Разрез", "Остриё от рельефа, м", "R, кПа", "Σf·h", "Fd, кН", "Fd/1,4", "Fd/1,25"])
    for nm, L, loam, IL in GEO:
        R, sfh, F = fd(L, loam, IL)
        ws2.append([nm, L, round(R), round(sfh, 1), round(F, 1), round(F / 1.4, 1), round(F / 1.25, 1)])
    wb.save(os.path.join(OUT, "Нагрузка на каждую сваю — таблица.xlsx"))

    print("сумма ЛИРА", round(N.sum(), 1), "наш сбор", round(td["total"]), "площадь", round(td["area"], 1),
          "стены", round(td["L"].sum(), 1))
    for nm, R in res:
        print(f"{nm:28s} {R.min():6.0f} {R.max():6.0f} >141,7: {(R > allow).sum()}")
    print("Fd 2,45 / 3,4:", round(fd_rpz), round(fd34), "тест", round(test.sum(), 1), round(test.max(), 1))


if __name__ == "__main__":
    build()
