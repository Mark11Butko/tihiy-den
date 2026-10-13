"""Геометрия виджета (в «дизайн-пикселях»; в Rainmeter всё умножается на SCALE)."""
from td_common import CFG

SCALE = min(1.3, max(0.6, float(CFG.get("scale", 0.9))))


def S(v):
    return round(v * SCALE, 2)


W = 392
PAD = 16
IN_W = W - 2 * PAD  # 360

# шапка
HEADER_H = 78
# погода
WX_Y, WX_H = 84, 104
HR_Y, HR_H = 194, 64
DY_Y, DY_H = 264, 84
# календарь
CAL_Y, CAL_H = 354, 222
CAL_TITLE_H = 34
CAL_WD_Y = CAL_Y + CAL_TITLE_H            # строка дней недели
CAL_GRID_Y = CAL_WD_Y + 22                # начало сетки
CW = IN_W / 7.0                           # ширина ячейки
RH = 26                                   # высота строки сетки
# повестка
AG_Y, AG_H = 582, 214
# валюты и крипта
FX_Y, FX_H = 802, 114
CR_Y, CR_H = 922, 114
TOTAL_H = CR_Y + CR_H + 10                # 1028 дизайн-пикселей

# компактный режим
CP_WX_Y, CP_WX_H = 84, 88
CP_EV_Y, CP_EV_H = 178, 96
CP_FX_Y, CP_FX_H = 280, 70
CP_TOTAL_H = CP_FX_Y + CP_FX_H + 12

# график (раскрытый, заменяет повестку+валюты+крипту)
CH_Y, CH_H = AG_Y, CR_Y + CR_H - AG_Y

SPARK_W, SPARK_H = 76, 20
TILE_SPARK_W, TILE_SPARK_H = 54, 22
