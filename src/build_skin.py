"""Генератор скина Rainmeter «Тихий день» v3 по картинке «Тёмный дашборд погоды, календаря и финансов».
Запуск: python build_skin.py"""
import os

from build_icons import build as build_icons
from i18n import tr
from td_common import CFG, COLORS, DATA, NC, NE, NF, NT, PYTHONW, SKIN_DIR, SKIN_NAME, chunks, geo_keys, hex_rgba, safe, screen_size, text_keys
from td_layout import (AG_H, AG_Y, CAL_GRID_Y, CAL_WD_Y, CAL_Y, CP_EV_H, CP_EV_Y, CP_FX_H, CP_FX_Y, CP_TOTAL_H, CP_WX_H, CP_WX_Y, CR_H, CR_Y, CW, DY_H,
                       DY_Y, FX_H, FX_Y, HR_H, HR_Y, RH, S, SCALE, TOTAL_H, W, WX_H, WX_Y)

ROOT = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(ROOT, "engine.py")
PT = lambda px: round(px * SCALE * 0.75, 2)  # noqa: E731  px -> pt
RGBA = lambda name, m=1.0: hex_rgba(COLORS[name], m)  # noqa: E731
out = []


def add(*lines):
    out.extend(lines)


def sec(name, **opts):
    add("", f"[{name}]")
    if "DynamicVariables" not in opts and any(isinstance(v, str) and ("[G_" in v or "[T_" in v) for v in opts.values()):
        opts["DynamicVariables"] = 1
    for k, v in opts.items():
        add(f"{k}={v}")


def act(*args):
    return '["%s" "%s" %s]' % (PYTHONW, ENGINE, " ".join(str(a) for a in args))


def hid(flag):
    return {"Hidden": f"[G_{safe(flag)}]"} if flag else {}


# ----------------------------------------------------------------- примитивы (координаты в дизайн-пикселях)
def glass(name, x, y, w, h, r=12, flag=None, a_top=14, a_bot=5, stroke=22):
    sec(name, Meter="Shape", X=0, Y=0,
        Shape=f"Rectangle {S(x)},{S(y)},{S(w)},{S(h)},{S(r)} | Fill LinearGradient Gr | StrokeWidth 1 | Stroke Color 255,255,255,{stroke}",
        Gr=f"90 | 255,255,255,{a_top} ; 0.0 | 255,255,255,{a_bot} ; 1.0", **hid(flag))


def rect(name, x, y, w, h, r, fill, flag=None, stroke=None, action=None):
    s = f"Rectangle {S(x)},{S(y)},{S(w)},{S(h)},{S(r)} | Fill Color {fill} | StrokeWidth {1 if stroke else 0}"
    if stroke:
        s += f" | Stroke Color {stroke}"
    opts = {"Meter": "Shape", "X": 0, "Y": 0, "Shape": s, **hid(flag)}
    if action:
        opts["LeftMouseUpAction"] = action
    sec(name, **opts)


def hit(name, x, y, w, h, action, flag=None):
    rect(name, x, y, w, h, 0, "0,0,0,1", flag, None, action)


def line(name, x1, y1, x2, y2, color="255,255,255,16", flag=None):
    sec(name, Meter="Shape", X=0, Y=0, Shape=f"Line {S(x1)},{S(y1)},{S(x2)},{S(y2)} | StrokeWidth 1 | Stroke Color {color}", **hid(flag))


def txt(name, x, y, w, h, key=None, static=None, px=14, color=None, colkey=None, bold=False, align="left", flag=None):
    ax = {"left": ("LeftCenter", x), "center": ("CenterCenter", x + w / 2), "right": ("RightCenter", x + w)}[align]
    opts = {"Meter": "String", "X": S(ax[1]), "Y": S(y + h / 2), "W": S(w), "H": S(h), "ClipString": 1,
            "StringAlign": ax[0], "FontFace": "Segoe UI", "FontSize": PT(px), "AntiAlias": 1}
    if bold:
        opts["StringStyle"] = "Bold"
    if colkey:
        opts["FontColor"] = f"[G_{safe(colkey)}]"
    else:
        opts["FontColor"] = color or RGBA("text")
    if key:
        opts["MeasureName"] = f"T_{safe(key)}"
        opts["Text"] = "%1"
    else:
        opts["Text"] = static
    opts.update(hid(flag))
    sec(name, **opts)


def img(name, x, y, w, h, file=None, gkey=None, flag=None):
    name_expr = f"#@#icons\\[G_{safe(gkey)}].png" if gkey else f"#@#icons\\{file}.png"
    sec(name, Meter="Image", X=S(x), Y=S(y), W=S(w), H=S(h), PreserveAspectRatio=1, ImageName=name_expr, **hid(flag))


def spark(name, x, y, base, flag, stroke=1.4):
    sec(name, Meter="Shape", X=S(x), Y=S(y),
        Shape=f"Path Ln | Fill Color 0,0,0,0 | StrokeWidth {stroke} | Stroke Color [G_col_{base}]",
        Shape2="Path Ar | Fill Color [G_cola_%s] | StrokeWidth 0" % base,
        Ln=f"[G_sp_{base}_l]", Ar=f"[G_sp_{base}_a]", **hid(flag))


def blue_button(name, x, y, w, h, r, flag, action):
    sec(name + "_bg", Meter="Shape", X=0, Y=0,
        Shape=f"Rectangle {S(x)},{S(y)},{S(w)},{S(h)},{S(r)} | Fill LinearGradient Bg | StrokeWidth 1 | Stroke Color 120,170,255,70",
        Bg="90 | 70,140,255,255 ; 0.0 | 36,98,225,255 ; 1.0", **hid(flag))
    hit(name, x, y, w, h, action, flag)


# ----------------------------------------------------------------- заголовок файла
SCREEN_W, SCREEN_H = screen_size()
DEF_X, DEF_Y = max(0, SCREEN_W - int(S(W)) - 24), 24
MOVE = ('[!Move "((#CURRENTCONFIGX#=0 && #CURRENTCONFIGY#=0) ? %d : #CURRENTCONFIGX#)" ' % DEF_X +
        '"((#CURRENTCONFIGX#=0 && #CURRENTCONFIGY#=0) ? %d : #CURRENTCONFIGY#)"]' % DEF_Y)
add("[Rainmeter]", "Update=1000", "AccurateText=1", "DynamicWindowSize=1", "Draggable=1",
    f"OnWakeAction={MOVE}",
    f'OnRefreshAction={MOVE}["{PYTHONW}" "{ENGINE}" render]')
add("", "[Metadata]", "Name=Quiet Day / Тихий день", "Author=Mark Butko", "Information=Weather, calendar, currencies and crypto widget")
add("", "[Variables]", f"D={DATA}\\")
sec("PosGuard", Measure="Calc", Formula=1, UpdateDivider=2, DynamicVariables=1,
    IfCondition="(#CURRENTCONFIGX# = 0) && (#CURRENTCONFIGY# = 0)", IfTrueAction=f'[!Move "{DEF_X}" "{DEF_Y}"]')


def parents(prefix, keys, tag):
    for n, ks in enumerate(chunks(keys)):
        sec(f"P_{tag}{n}", Measure="WebParser", URL=f"file://{DATA}\\{prefix}{n}.txt", CodePage=65001,
            RegExp="(?siU)" + "(.*)\\n" * len(ks), UpdateRate=1)
        for i, k in enumerate(ks):
            sec(f"{'T' if tag == 't' else 'G'}_{safe(k)}", Measure="WebParser", URL=f"[P_{tag}{n}]", StringIndex=i + 1)


parents("text", text_keys(), "t")
parents("geo", geo_keys(), "g")
sec("mClock", Measure="Time", Format="%H:%M" if CFG.get("clock24", True) else "%I:%M")

# ----------------------------------------------------------------- главная карточка
for nm, h, flag in (("CardExp", TOTAL_H, "hid.ex"), ("CardCmp", CP_TOTAL_H, "hid.k")):
    sec(nm, Meter="Shape", X=0, Y=0,
        Shape=f"Rectangle 0,0,{S(W)},{S(h)},{S(24)} | Fill LinearGradient Gm | StrokeWidth 1 | Stroke Color 140,180,255,46",
        Gm="90 | 20,34,58,236 ; 0.0 | 11,19,34,238 ; 1.0", **hid(flag))

# ----------------------------------------------------------------- шапка (общая)
sec("Clock", Meter="String", MeasureName="mClock", X=S(18), Y=S(40), W=S(180), H=S(68), ClipString=1, StringAlign="LeftCenter",
    FontFace="Segoe UI", StringStyle="Bold", FontSize=PT(56), AntiAlias=1, FontColor=RGBA("text"), Text="%1")
txt("Date1", 196, 14, 180, 26, key="date1", px=18)
txt("Date2", 196, 40, 180, 26, key="date2", px=18)
txt("Mode_exp", 352, 8, 28, 24, static="−", px=20, color=RGBA("textDim"), align="center", flag="hid.ex")
hit("Mode_exp_hit", 348, 6, 34, 30, act("act", "mode"), "hid.ex")
txt("Mode_cmp", 352, 8, 28, 24, static="+", px=20, color=RGBA("textDim"), align="center", flag="hid.k")
hit("Mode_cmp_hit", 348, 6, 34, 30, act("act", "mode"), "hid.k")

# ----------------------------------------------------------------- погода
EX = "hid.ex"
glass("G_wx", 16, WX_Y, 360, WX_H, 12, EX)
img("Wx_pin", 26, WX_Y + 11, 14, 14, "u_pin", flag=EX)
txt("Wx_loc", 44, WX_Y + 8, 150, 20, key="w.loc", px=14, bold=True, color=RGBA("textDim"), flag=EX)
img("Wx_icon", 22, WX_Y + 34, 48, 48, gkey="ic.cur", flag=EX)
txt("Wx_temp", 72, WX_Y + 32, 100, 52, key="w.temp", px=38, bold=True, flag=EX)
txt("Wx_feels", 168, WX_Y + 36, 118, 20, key="w.feels", px=12, flag=EX)
txt("Wx_up", 168, WX_Y + 62, 14, 20, static="↑", px=14, color=RGBA("up"), flag=EX)
txt("Wx_hi", 182, WX_Y + 62, 44, 20, key="w.hi", px=13, bold=True, flag=EX)
txt("Wx_dn", 226, WX_Y + 62, 14, 20, static="↓", px=14, color=RGBA("accent"), flag=EX)
txt("Wx_lo", 240, WX_Y + 62, 44, 20, key="w.lo", px=13, bold=True, flag=EX)
line("Wx_div", 290, WX_Y + 14, 290, WX_Y + WX_H - 14, "255,255,255,24", EX)
img("Wx_windi", 300, WX_Y + 26, 16, 16, "u_wind", flag=EX)
txt("Wx_wind", 320, WX_Y + 24, 56, 20, key="w.wind", px=12, flag=EX)
img("Wx_humi", 300, WX_Y + 62, 16, 16, "u_drop", flag=EX)
txt("Wx_hum", 320, WX_Y + 60, 56, 20, key="w.hum", px=12, flag=EX)

glass("G_hr", 16, HR_Y, 360, HR_H, 12, EX)
for i in range(6):
    cx = 16 + 30 + 60 * i
    txt(f"Hr{i}_l", cx - 28, HR_Y + 4, 56, 16, key=f"h{i}.l", px=12, color=RGBA("textDim"), align="center", flag=EX)
    img(f"Hr{i}_i", cx - 12, HR_Y + 20, 24, 24, gkey=f"ic.h{i}", flag=EX)
    txt(f"Hr{i}_t", cx - 28, HR_Y + 44, 56, 16, key=f"h{i}.t", px=13, bold=True, align="center", flag=EX)
    if i:
        line(f"Hr_sep{i}", 16 + 60 * i, HR_Y + 8, 16 + 60 * i, HR_Y + HR_H - 8, "255,255,255,14", EX)

glass("G_dy", 16, DY_Y, 360, DY_H, 12, EX)
for i in range(5):
    cx = 16 + 36 + 72 * i
    txt(f"Dy{i}_n", cx - 40, DY_Y + 6, 36, 16, key=f"d{i}.n", px=13, bold=True, align="right", flag=EX)
    txt(f"Dy{i}_d", cx + 1, DY_Y + 8, 36, 16, key=f"d{i}.d", px=10, color=RGBA("textFaint"), align="left", flag=EX)
    img(f"Dy{i}_i", cx - 14, DY_Y + 24, 28, 28, gkey=f"ic.d{i}", flag=EX)
    txt(f"Dy{i}_h", cx - 34, DY_Y + 52, 68, 16, key=f"d{i}.h", px=14, bold=True, align="center", flag=EX)
    txt(f"Dy{i}_l", cx - 34, DY_Y + 66, 68, 14, key=f"d{i}.l", px=12, color=RGBA("textDim"), align="center", flag=EX)
    if i:
        line(f"Dy_sep{i}", 16 + 72 * i, DY_Y + 8, 16 + 72 * i, DY_Y + DY_H - 8, "255,255,255,14", EX)

# ----------------------------------------------------------------- календарь
CL = "hid.cal"
glass("G_cal", 16, CAL_Y, 360, 224, 12, CL)
txt("Cal_title", 28, CAL_Y + 6, 140, 26, key="cal.title", px=16, bold=True, flag=CL)
img("Cal_prev", 134, CAL_Y + 11, 16, 16, "u_chev_l", flag=CL)
img("Cal_next", 160, CAL_Y + 11, 16, 16, "u_chev_r", flag=CL)
hit("Cal_prev_hit", 128, CAL_Y + 6, 28, 26, act("act", "month", -1), CL)
hit("Cal_next_hit", 156, CAL_Y + 6, 28, 26, act("act", "month", 1), CL)
hit("Cal_title_hit", 28, CAL_Y + 6, 100, 26, act("act", "today"), CL)
img("Cal_sync_i", 214, CAL_Y + 12, 14, 14, "u_sync", flag="hid.sync")
txt("Cal_sync", 230, CAL_Y + 8, 140, 22, key="cal.sync", px=11, colkey="stale", align="right", flag="hid.sync")
for c, lab in enumerate(tr("wd_short")):
    txt(f"WD{c}", 16 + CW * c, CAL_WD_Y + 2, CW, 18, static=lab, px=12, color=RGBA("textDim"), align="center", flag=CL)
for r in range(6):
    line(f"CalLn{r}", 24, CAL_GRID_Y + RH * (r + 1), 368, CAL_GRID_Y + RH * (r + 1), "255,255,255,14", CL)
sec("CalShapes", Meter="Shape", X=S(16), Y=S(CAL_GRID_Y), Shape="[G_sel]", Shape2="[G_today]",
    **{("Shape%d" % (3 + i)): f"[G_dot{i}]" for i in range(60)}, **hid(CL))
for i in range(42):
    r, c = divmod(i, 7)
    txt(f"C{i}", 16 + CW * c, CAL_GRID_Y + RH * r, CW, RH - 2, key=f"c{i}", px=13, colkey=f"cc{i}", align="center", flag=CL)
    hit(f"C{i}_hit", 16 + CW * c, CAL_GRID_Y + RH * r, CW, RH, act("act", "date", i), CL)

# ----------------------------------------------------------------- повестка
AGF = "hid.ag"
glass("G_ag", 16, AG_Y, 360, AG_H, 12, AGF)
txt("Ag_title", 28, AG_Y + 8, 200, 26, key="ag.title", px=15, bold=True, flag=AGF)
blue_button("Ag_add", 236, AG_Y + 8, 136, 28, 8, AGF, act("act", "taskadd"))
img("Ag_add_i", 244, AG_Y + 14, 16, 16, "u_plus", flag=AGF)
txt("Ag_add_t", 262, AG_Y + 8, 108, 28, static=tr("ui_add_task"), px=12, bold=True, color="255,255,255,255", flag=AGF)
txt("Ag_empty", 28, AG_Y + 40, 330, 22, key="ag.empty", px=13, color=RGBA("textDim"), flag=AGF)
for i in range(NE):
    y = AG_Y + 40 + 22 * i
    sec(f"Ev{i}_dot", Meter="Shape", X=S(34), Y=S(y + 11), Shape=f"Ellipse 0,0,{S(4)} | Fill Color [G_col_ev{i}] | StrokeWidth 0", **hid(AGF))
    txt(f"Ev{i}_t", 46, y, 104, 22, key=f"ev{i}.t", px=13, flag=AGF)
    txt(f"Ev{i}_n", 152, y, 220, 22, key=f"ev{i}.n", px=13, flag=AGF)
txt("Ag_tasks", 28, AG_Y + 114, 200, 22, static=tr("ui_tasks"), px=14, bold=True, flag=AGF)
for i in range(NT):
    y = AG_Y + 138 + 24 * i
    sec(f"Tk{i}_box", Meter="Shape", X=S(28), Y=S(y + 4), Shape=f"[G_chk{i}a]", Shape2=f"[G_chk{i}b]",
        P=f"{S(3.5)},{S(8.2)} | LineTo {S(6.5)},{S(11)} | LineTo {S(12)},{S(4.8)}", **hid(AGF))
    txt(f"Tk{i}_l", 52, y, 316, 24, key=f"tk{i}", px=13, colkey=f"tkcol{i}", flag=AGF)
    hit(f"Tk{i}_hit", 24, y, 348, 24, act("act", "task", i), AGF)

# ----------------------------------------------------------------- Google не подключён
GO = "hid.go"
glass("G_go", 16, CAL_Y, 360, AG_Y + AG_H - CAL_Y, 12, GO)
txt("Go_title", 28, CAL_Y + 8, 300, 26, static=tr("ui_calendar_planner"), px=15, bold=True, flag=GO)
rect("Go_inner", 28, CAL_Y + 40, 336, AG_Y + AG_H - CAL_Y - 52, 10, "0,0,0,50", GO, "255,255,255,16")
img("Go_g", 168, CAL_Y + 128, 56, 56, "u_google", flag=GO)
txt("Go_msg", 40, CAL_Y + 198, 312, 26, static=tr("ui_not_connected"), px=16, bold=True, align="center", flag=GO)
txt("Go_d1", 40, CAL_Y + 230, 312, 20, static=tr("ui_connect_d1"), px=12, color=RGBA("textDim"), align="center", flag=GO)
txt("Go_d2", 40, CAL_Y + 250, 312, 20, static=tr("ui_connect_d2"), px=12, color=RGBA("textDim"), align="center", flag=GO)
blue_button("Go_btn", 84, CAL_Y + 292, 224, 42, 10, GO, act("act", "connect"))
img("Go_btn_i", 108, CAL_Y + 302, 22, 22, "u_link", flag=GO)
txt("Go_btn_t", 136, CAL_Y + 292, 172, 42, static=tr("ui_connect_btn"), px=15, bold=True, color="255,255,255,255", flag=GO)

# ----------------------------------------------------------------- валюты и крипта
LS = "hid.lists"
for key, y0, h0, title, act_name in (("Fx", FX_Y, FX_H, tr("ui_currencies"), "fxsettings"), ("Cr", CR_Y, CR_H, tr("ui_crypto"), "cryptosettings")):
    glass(f"G_{key}", 16, y0, 360, h0, 12, LS)
    txt(f"{key}_title", 28, y0 + 6, 200, 26, static=title, px=15, bold=True, flag=LS)
    img(f"{key}_add_i", 300, y0 + 12, 14, 14, "u_plus_blue", flag=LS)
    txt(f"{key}_add", 316, y0 + 7, 58, 24, static=tr("ui_add"), px=12, color="120,170,255,255", flag=LS)
    hit(f"{key}_add_hit", 296, y0 + 6, 80, 26, act("act", act_name), LS)
for i in range(NF):
    y = FX_Y + 34 + 26 * i
    img(f"Fx{i}_flag", 28, y + 2, 22, 22, gkey=f"fl.fx{i}", flag=LS)
    txt(f"Fx{i}_p", 56, y, 84, 26, key=f"fx{i}.p", px=13, flag=LS)
    txt(f"Fx{i}_r", 138, y, 58, 26, key=f"fx{i}.r", px=14, bold=True, align="right", flag=LS)
    txt(f"Fx{i}_c", 206, y, 76, 26, key=f"fx{i}.c", px=12, colkey=f"col.fx{i}", flag=LS)
    spark(f"Fx{i}_s", 282, y + 3, f"fx{i}", LS)
    img(f"Fx{i}_chev", 360, y + 6, 14, 14, "u_chev_r", flag=LS)
    if i < NF - 1:
        line(f"Fx_ln{i}", 28, y + 26, 372, y + 26, "255,255,255,12", LS)
for i in range(NC):
    y = CR_Y + 34 + 26 * i
    img(f"Cr{i}_logo", 28, y + 2, 22, 22, gkey=f"lg.c{i}", flag=LS)
    txt(f"Cr{i}_s", 56, y, 70, 26, key=f"cr{i}.s", px=13, flag=LS)
    txt(f"Cr{i}_p", 112, y, 84, 26, key=f"cr{i}.p", px=14, bold=True, align="right", flag=LS)
    txt(f"Cr{i}_c", 206, y, 76, 26, key=f"cr{i}.c", px=12, colkey=f"col.c{i}", flag=LS)
    spark(f"Cr{i}_sp", 282, y + 3, f"c{i}", LS)
    img(f"Cr{i}_chev", 360, y + 6, 14, 14, "u_chev_r", flag=LS)
    hit(f"Cr{i}_hit", 24, y, 352, 26, act("act", "chart", i), LS)
    if i < NC - 1:
        line(f"Cr_ln{i}", 28, y + 26, 372, y + 26, "255,255,255,12", LS)

# ----------------------------------------------------------------- график
CH = "hid.ch"
glass("G_ch", 16, AG_Y, 360, CR_Y + CR_H - AG_Y, 12, CH)
txt("Ch_title", 28, AG_Y + 8, 280, 28, key="ch.title", px=17, bold=True, flag=CH)
txt("Ch_close", 340, AG_Y + 8, 28, 28, static="×", px=20, color=RGBA("text"), align="center", flag=CH)
hit("Ch_close_hit", 336, AG_Y + 6, 36, 32, act("act", "chartclose"), CH)
for i, lab in enumerate(tr("periods")):
    x = 28 + 64 * i
    rect(f"Ch_p{i}_bg", x, AG_Y + 46, 56, 28, 8, "255,255,255,14", CH, "255,255,255,22")
    txt(f"Ch_p{i}_t", x, AG_Y + 46, 56, 28, static=lab, px=13, bold=True, colkey=f"pc{i}", align="center", flag=CH)
    hit(f"Ch_p{i}", x, AG_Y + 46, 56, 28, act("act", "period", ("24h", "7d", "30d")[i]), CH)
sec("Ch_line", Meter="Shape", X=S(28), Y=S(AG_Y + 90),
    Shape="Path Ln | Fill Color 0,0,0,0 | StrokeWidth 1.8 | Stroke Color [G_ch_col]", Shape2="Path Ar | Fill Color [G_ch_cola] | StrokeWidth 0",
    Shape3="[G_ch_dot]", Ln="[G_ch_l]", Ar="[G_ch_a]", **hid(CH))
sec("Ch_cur", Meter="String", MeasureName="T_ch_current", X=S(372), Y=f"({S(AG_Y + 90)}+[G_ch_cury]+{S(11)})", W=S(140), H=S(22), ClipString=1,
    StringAlign="RightCenter", FontFace="Segoe UI", StringStyle="Bold", FontSize=PT(13), AntiAlias=1, FontColor=RGBA("accent"), Text="%1", **hid(CH))
txt("Ch_minmax", 28, AG_Y + 342, 340, 24, key="ch.minmax", px=13, color=RGBA("textDim"), flag=CH)

# ----------------------------------------------------------------- компактный режим
K = "hid.k"
glass("G_cwx", 16, CP_WX_Y, 360, CP_WX_H, 12, K)
img("Cw_icon", 22, CP_WX_Y + 22, 44, 44, gkey="ic.cur", flag=K)
txt("Cw_temp", 70, CP_WX_Y + 18, 96, 52, key="w.temp", px=34, bold=True, flag=K)
img("Cw_pin", 170, CP_WX_Y + 14, 14, 14, "u_pin", flag=K)
txt("Cw_loc", 186, CP_WX_Y + 11, 100, 20, key="w.loc", px=13, bold=True, color=RGBA("textDim"), flag=K)
txt("Cw_up", 170, CP_WX_Y + 44, 14, 20, static="↑", px=14, color=RGBA("up"), flag=K)
txt("Cw_hi", 184, CP_WX_Y + 44, 42, 20, key="w.hi", px=13, bold=True, flag=K)
txt("Cw_dn", 226, CP_WX_Y + 44, 14, 20, static="↓", px=14, color=RGBA("accent"), flag=K)
txt("Cw_lo", 240, CP_WX_Y + 44, 44, 20, key="w.lo", px=13, bold=True, flag=K)
line("Cw_div", 290, CP_WX_Y + 14, 290, CP_WX_Y + CP_WX_H - 14, "255,255,255,24", K)
img("Cw_windi", 300, CP_WX_Y + 22, 16, 16, "u_wind", flag=K)
txt("Cw_wind", 320, CP_WX_Y + 20, 56, 20, key="w.wind", px=12, flag=K)
img("Cw_humi", 300, CP_WX_Y + 52, 16, 16, "u_drop", flag=K)
txt("Cw_hum", 320, CP_WX_Y + 50, 56, 20, key="w.hum", px=12, flag=K)

glass("G_cev", 16, CP_EV_Y, 360, CP_EV_H, 12, K)
txt("Cev_title", 28, CP_EV_Y + 6, 300, 24, static=tr("ui_upcoming"), px=14, bold=True, flag=K)
for i in range(2):
    y = CP_EV_Y + 34 + 28 * i
    sec(f"Cev{i}_bar", Meter="Shape", X=S(30), Y=S(y + 6), Shape=f"Rectangle 0,0,{S(4)},{S(16)},{S(2)} | Fill Color [G_cpcol_ev{i}] | StrokeWidth 0", **hid("hid.kev"))
    txt(f"Cev{i}_t", 42, y, 112, 28, key=f"cp.ev{i}.t", px=13, flag="hid.kev")
    txt(f"Cev{i}_n", 156, y, 130, 28, key=f"cp.ev{i}.n", px=13, flag="hid.kev")
    txt(f"Cev{i}_in", 372 - 100, y, 100, 28, key=f"cp.ev{i}.in", px=11, color=RGBA("accent"), align="right", flag="hid.kev")
txt("Cev_empty", 28, CP_EV_Y + 40, 330, 28, key="cp.empty", px=13, color=RGBA("textDim"), flag="hid.kempty")
hit("Cev_go_hit", 24, CP_EV_Y + 36, 348, 32, act("act", "connect"), "hid.kgo")

for i in range(3):
    x = 16 + 124 * i
    glass(f"G_ct{i}", x, CP_FX_Y, 112, CP_FX_H, 10, K)
    txt(f"Ct{i}_p", x + 10, CP_FX_Y + 6, 96, 18, key=f"cp.f{i}.p", px=11, color=RGBA("textDim"), flag=K)
    txt(f"Ct{i}_r", x + 10, CP_FX_Y + 22, 100, 22, key=f"cp.f{i}.r", px=14, bold=True, flag=K)
    txt(f"Ct{i}_c", x + 10, CP_FX_Y + 46, 100, 18, key=f"cp.f{i}.c", px=11, colkey=f"col.t{i}", flag=K)
    spark(f"Ct{i}_s", x + 54, CP_FX_Y + 26, f"t{i}", K)

# ----------------------------------------------------------------- запись
os.makedirs(SKIN_DIR, exist_ok=True)
path = os.path.join(SKIN_DIR, f"{SKIN_NAME}.ini")
with open(path, "w", encoding="utf-16", newline="") as f:
    f.write("\r\n".join(out) + "\r\n")
build_icons()
print("skin:", path, "lines:", len(out), "| size px:", S(W), "x", S(TOTAL_H))
