"""Геометрия виджета (в «дизайн-пикселях»; в Rainmeter всё умножается на SCALE)."""
from td_common import CFG

SCALE = min(1.3, max(0.6, float(CFG.get("scale", 0.9))))


def S(v):
    return round(v * SCALE, 2)


W = 376
PAD = 16
IN_W = W - 2 * PAD  # 360

# шапка
HEADER_H = 78
# погода
WX_Y, WX_H = 88, 64
HR_Y, HR_H = 160, 40
DY_Y, DY_H = 208, 48
# календарь
CAL_Y, CAL_H = 264, 184
CAL_TITLE_H = 24
CAL_WD_Y = CAL_Y + CAL_TITLE_H            # строка дней недели
CAL_GRID_Y = CAL_WD_Y + 16                # начало сетки
CW = IN_W / 7.0                           # ширина ячейки
RH = 24                                   # высота строки сетки
# повестка
AG_Y, AG_H = 456, 112
# валюты и крипта
FX_Y, FX_H = 576, 80
CR_Y, CR_H = 664, 80
TOTAL_H = 760

# компактный режим
CP_WX_Y, CP_WX_H = 88, 32
CP_EV_Y, CP_EV_H = 128, 72
CP_FX_Y, CP_FX_H = 208, 40
CP_TOTAL_H = 264

# график заменяет только списки котировок; повестка остаётся видимой
CH_Y, CH_H = FX_Y, CR_Y + CR_H - FX_Y
CHART_W, CHART_H = 312, 64

SPARK_W, SPARK_H = 64, 16
TILE_SPARK_W, TILE_SPARK_H = 54, 22
