#!/bin/sh
# Пересборка всех разделов: ./scripts/build_all.sh
set -e
cd "$(dirname "$0")"
R=..
mkdir -p "$R/ОВК" "$R/ОВ" "$R/ВК" "$R/МЗ.ПС" "$R/ТТР" "$R/ПОС" "$R/Бюджет"
python3 make_drawings.py "$R/ОВК/291-ОВК Чертежи.pdf"
python3 make_docs.py "$R/ОВК"
python3 make_ov.py "$R/ОВ/291-ОВ Отопление и котельная.pdf"
python3 make_vk.py "$R/ВК/291-ВК Водоснабжение и канализация.pdf"
python3 make_mzps.py "$R/МЗ.ПС/291-МЗ.ПС Молниезащита, заземление, пожарная сигнализация.pdf"
SCRATCH=${SCRATCH:-/tmp} python3 make_reports.py "$R/_reports"
mv "$R/_reports/291-ТТР Теплотехнический расчёт.pdf" "$R/ТТР/"
mv "$R/_reports/291-ПОС Организация строительства и график.pdf" "$R/ПОС/"
mv "$R/_reports/Бюджет строительства — Берта Ромарио."* "$R/Бюджет/"
rmdir "$R/_reports"
mkdir -p "$R/Заключение"
FIG=${FIG:-review_fig} SCRATCH=${SCRATCH:-/tmp} python3 make_review.py "$R/Заключение"
