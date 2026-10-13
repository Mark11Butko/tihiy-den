"""Генератор скина Rainmeter «Тихий день» 1.2: 376×760, четыре размера шрифта.
Запуск: python build_skin.py"""
import os

from build_icons import build as build_icons
from i18n import tr
from td_common import CFG, COLORS, DATA, USER_ROOT, NC, NE, NF, NT, NDOTS, PYTHONW, SKIN_DIR, SKIN_NAME, chunks, geo_keys, hex_rgba, safe, screen_size, text_keys, data_chunk_path
from td_layout import (AG_H, AG_Y, CAL_GRID_Y, CAL_WD_Y, CAL_Y, CP_EV_H, CP_EV_Y, CP_FX_H, CP_FX_Y, CP_TOTAL_H, CP_WX_H, CP_WX_Y, CR_H, CR_Y, CW, DY_H,
                       DY_Y, FX_H, FX_Y, HR_H, HR_Y, RH, S, SCALE, TOTAL_H, W, WX_H, WX_Y, CH_Y, CH_H)

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
    if name.startswith('Ch_'): opts['Group'] = 'ChartPanel'
    for k, v in opts.items():
        add(f"{k}={v}")


def act(*args):
    return '["%s" "%s" --data-dir "%s" --user-dir "%s" --skin-dir "%s" %s]' % (PYTHONW, ENGINE, DATA, USER_ROOT, SKIN_DIR, " ".join(str(a) for a in args))


def hid(flag):
    return {"Hidden": f"[G_{safe(flag)}]"} if flag else {}


# ----------------------------------------------------------------- примитивы (координаты в дизайн-пикселях)

def rect(name, x, y, w, h, r, fill, flag=None, stroke=None, action=None):
    s = f"Rectangle {S(x)},{S(y)},{S(w)},{S(h)},{S(r)} | Fill Color {fill} | StrokeWidth {1 if stroke else 0}"
    if stroke:
        s += f" | Stroke Color {stroke}"
    opts = {"Meter": "Shape", "X": 0, "Y": 0, "Shape": s, **hid(flag)}
    if action:
        opts["LeftMouseUpAction"] = action
    sec(name, **opts)


HOVER_FILL = "255,255,255,22"


def hit(name, x, y, w, h, action, flag=None, tip=None, r=7, hover=True, rclick=None):
    """Невидимая зона клика. При наведении подсвечивается (hover), есть всплывающая подсказка (tip)."""
    # X/Y мейтра = левый верхний угол зоны: у Shape-мейтра зона клика — от (X,Y) до правого нижнего края фигуры
    base = f"Rectangle 0,0,{S(w)},{S(h)},{S(r)} | Fill Color %s | StrokeWidth 0"
    opts = {"Meter": "Shape", "X": S(x), "Y": S(y), "Shape": base % "0,0,0,1", "LeftMouseUpAction": action, **hid(flag)}
    if tip:
        opts["ToolTipText"] = tip
    if rclick:
        opts["RightMouseUpAction"] = rclick
    if hover:
        opts["MouseOverAction"] = f'[!SetOption "{name}" Shape "{base % HOVER_FILL}"][!UpdateMeter "{name}"][!Redraw]'
        opts["MouseLeaveAction"] = f'[!SetOption "{name}" Shape "{base % "0,0,0,1"}"][!UpdateMeter "{name}"][!Redraw]'
    sec(name, **opts)




def line(name, x1, y1, x2, y2, color="255,255,255,16", flag=None):
    sec(name, Meter="Shape", X=0, Y=0, Shape=f"Line {S(x1)},{S(y1)},{S(x2)},{S(y2)} | StrokeWidth 1 | Stroke Color {color}", **hid(flag))


def txt(name, x, y, w, h, key=None, static=None, px=14, color=None, colkey=None, bold=False, align="left", flag=None):
    ax = {"left": ("LeftCenter", x), "center": ("CenterCenter", x + w / 2), "right": ("RightCenter", x + w)}[align]
    opts = {"Meter": "String", "X": S(ax[1]), "Y": S(y + h / 2), "W": S(w), "H": S(h), "ClipString": 1,
            "StringAlign": ax[0], "FontFace": "Segoe UI Semibold" if bold else "Segoe UI", "FontSize": PT(px), "AntiAlias": 1}
    if bold:
        opts["StringStyle"] = "Normal"
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



# ----------------------------------------------------------------- skin lifecycle and data measures
SCREEN_W, SCREEN_H = screen_size()
DEF_X, DEF_Y = max(0, SCREEN_W - int(S(W)) - 24), 24
add('[Rainmeter]', 'Update=1000', 'AccurateText=1', 'DynamicWindowSize=1', 'Draggable=1',
    f'OnRefreshAction={act("render")}', f'ContextTitle={tr("settings")}', f'ContextAction={act("act", "cfg")}')
add('', '[Metadata]', 'Name=Quiet Day / Тихий день', 'Author=Mark Butko', 'Version=1.2.0', 'License=MIT')
add('', '[Variables]', f'D={DATA}\\', f'Scale={SCALE}', f'MotionEnabled={0 if CFG.get("reduced_motion", True) else 1}')
def parents(prefix, keys, tag):
    for n, ks in enumerate(chunks(keys)):
        sec(f'P_{tag}{n}', Measure='WebParser', URL='file://' + data_chunk_path(prefix, n), CodePage=65001,
            RegExp='(?siU)' + '(.*)\\n' * len(ks), UpdateRate=1)
        for i, k in enumerate(ks):
            options = {}
            if tag == 'g':
                if k.startswith('hid.'): fallback = '0' if k == 'hid.ex' else '1'
                elif k.startswith('ic.'): fallback = 'w_none'
                elif k.startswith(('col.', 'cola.', 'cc', 'pc', 'tkcol')) or k in ('stale','ch.col','ch.cola'): fallback = RGBA('textDim')
                elif k.startswith(('sp.', 'ch.l', 'ch.a')): fallback = '0,0 | LineTo 0.1,0.1' + (' | ClosePath 1' if k.endswith('.a') else '')
                elif k in ('ch.pillx', 'ch.cury'): fallback = '0'
                else: fallback = 'Ellipse -50,-50,0.1 | Fill Color 0,0,0,0 | StrokeWidth 0'
                options['Substitute'] = '"":"' + fallback + '"'
            sec(f'{"T" if tag == "t" else "G"}_{safe(k)}', Measure='WebParser', URL=f'[P_{tag}{n}]', StringIndex=i+1, **options)
parents('text', text_keys(), 't'); parents('geo', geo_keys(), 'g')
sec('mClock', Measure='Time', Format='%H:%M' if CFG.get('clock24', True) else '%I:%M %p')
sec('Motion', Measure='Script', ScriptFile='#@#motion.lua')
sec('MotionTimer', Measure='Plugin', Plugin='ActionTimer', ActionList1='Repeat Step,16,16', Step='[!CommandMeasure Motion "Advance()"]', ActionList2='Repeat CheckStep,16,22', CheckStep='[!CommandMeasure Motion "CheckAdvance()"]', ActionList3='Repeat PanelStep,16,16', PanelStep='[!CommandMeasure Motion "PanelAdvance()"]')
EX, CL, AGF, LS, CH, K = 'hid.ex', 'hid.cal', 'hid.ag', 'hid.lists', 'hid.ch', 'hid.k'
def button(name,x,y,w,label,action,flag=None,tip=None):
    if name in ('Cfg','Mode_exp','Mode_cmp','Add_event','Add_task','Cal_sync','Ch_close'):
        rect(name+'_surface',x,y,w,24,8,RGBA('surface'),flag,RGBA('stroke'))
    icon_name = {'⚙':'u_settings','↻':'u_sync','✓':'u_check'}.get(label)
    if icon_name: img(name+'_icon',x+(w-16)/2,y+4,16,16,file=icon_name,flag=flag)
    else: txt(name+'_text',x,y,w,24,static=label,px=14,color=RGBA('accent'),align='center',flag=flag)
    hit(name,x,y,w,24,action,flag,tip=tip,r=8)
def input_action(kind):return act('act','input',kind)
for nm,h,flag in [('CardExp',TOTAL_H,EX),('CardCmp',CP_TOTAL_H,K)]:
    rect(nm,.5,.5,W-1,h-1,24,RGBA('background'),flag,RGBA('stroke'))
# Header: one time hierarchy, date below, no overlapping controls.
sec('Clock',Meter='String',MeasureName='mClock',X=S(16),Y=S(40),W=S(272),H=S(56),ClipString=1,StringAlign='LeftCenter',
    FontFace='Segoe UI Semibold',FontSize=PT(48),AntiAlias=1,FontColor=RGBA('text'),Text='%1')
txt('Date1',16,64,128,16,key='date1',px=14)
txt('Date2',144,64,216,16,key='date2',px=14,color=RGBA('textDim'),align='right')
button('Mode_exp',336,16,24,'−',act('act','mode'),EX,tr('tip_mode'))
button('Mode_cmp',336,16,24,'+',act('act','mode'),K,tr('tip_mode'))
button('Cfg',304,16,24,'⚙',act('act','cfg'),tip=tr('settings'))
rect('Day_track',16,80,344,2,1,RGBA('surface'))
sec('Day_progress',Meter='Shape',X=S(16),Y=S(80),Shape='[G_day_progress]',ToolTipText='[T_day_progressLabel]')
# Weather: no decorative subcards, no shadows/blur/gradients.
rect('Weather_surface',16,88,344,72,16,RGBA('surface2'),EX,RGBA('stroke',.5))
txt('Wx_loc',24,96,160,16,key='w.loc',px=14,color=RGBA('textDim'),flag=EX)
hit('Wx_loc_hit',24,92,160,24,input_action('city'),EX,tr('tip_city'))
img('Wx_icon',24,120,32,32,gkey='ic.cur',flag=EX)
txt('Wx_temp',64,112,80,40,key='w.temp',px=24,bold=True,flag=EX)
txt('Wx_feels',144,120,208,16,key='w.feels',px=14,flag=EX)
txt('Wx_range',144,136,112,16,key='w.range',px=14,color=RGBA('textDim'),flag=EX)
img('Wx_wind_icon',192,96,16,16,file='u_wind',flag=EX)
txt('Wx_wind',216,96,136,16,key='w.wind',px=14,color=RGBA('textDim'),align='right',flag=EX)
txt('Wx_precip',264,136,88,16,key='w.precip',px=14,color=RGBA('textDim'),align='right',flag=EX)
for i in range(6):
    x=16+i*(344/6)
    txt(f'Hr{i}_l',x,168,344/6,16,key=f'h{i}.l',px=14,color=RGBA('textDim'),align='center',flag=EX)
    txt(f'Hr{i}_t',x,184,344/6,16,key=f'h{i}.t',px=16,align='center',flag=EX)
for i in range(5):
    x=16+i*(344/5)
    txt(f'Dy{i}_n',x,208,344/5,16,key=f'd{i}.n',px=14,color=RGBA('textDim'),align='center',flag=EX)
    txt(f'Dy{i}_l',x,232,344/10,16,key=f'd{i}.l',px=14,color=RGBA('textDim'),align='center',flag=EX)
    txt(f'Dy{i}_h',x+344/10,232,344/10,16,key=f'd{i}.h',px=14,align='center',flag=EX)
    txt(f'Dy{i}_slash',x+344/10-3,232,6,16,static='/',px=14,color=RGBA('textDim'),align='center',flag=EX)
    if i: line(f'Dy{i}_divider',x,212,x,248,RGBA('stroke',.5),EX)
# Month: 42 cells include every possible six-week month.
txt('Cal_title',16,CAL_Y,248,24,key='cal.title',px=16,bold=True,flag=CL)
button('Cal_prev',272,CAL_Y,24,'‹',act('act','month',-1),CL,tr('tip_prev'))
button('Cal_next',304,CAL_Y,24,'›',act('act','month',1),CL,tr('tip_next'))
button('Cal_sync',336,CAL_Y,24,'↻',act('act','gclick'),CL,tr('tip_sync'))
hit('Cal_today',16,CAL_Y,248,24,act('act','today'),CL,tr('tip_today'))
for c,lab in enumerate(tr('wd_short')):txt(f'WD{c}',16+CW*c,CAL_WD_Y,CW,16,static=lab,px=14,color=RGBA('textDim'),align='center',flag=CL)
sec('CalShapes',Meter='Shape',X=S(16),Y=S(CAL_GRID_Y),Shape='[G_sel]',Shape2='[G_today]',
    **{f'Shape{3+i}':f'[G_dot{i}]' for i in range(NDOTS)},**hid(CL))
for i in range(42):
    r,c=divmod(i,7)
    txt(f'C{i}',16+CW*c,CAL_GRID_Y+RH*r,CW,RH,key=f'c{i}',px=14,colkey=f'cc{i}',align='center',flag=CL)
    hit(f'C{i}_hit',16+CW*c,CAL_GRID_Y+RH*r,CW,RH,act('act','date',i),CL,tr('tip_day'))
# Agenda remains visible when a quote graph opens.
txt('Ag_title',16,AG_Y,208,24,key='ag.title',px=16,bold=True,flag=AGF)
button('Add_event',232,AG_Y,24,'+',input_action('event'),AGF,tr('tip_add_event'))
button('Add_task',264,AG_Y,24,'✓',input_action('task'),AGF,tr('tip_add_task'))
button('Events_prev',296,AG_Y,24,'‹',act('act','page','event_page:-1'),AGF,tr('previous_page'))
button('Events_next',328,AG_Y,32,'›',act('act','page','event_page:1'),AGF,tr('next_page'))
txt('Ag_empty',16,480,344,24,key='ag.empty',px=14,color=RGBA('textDim'),flag=AGF)
for i in range(NE):
    y=480+i*24
    rect(f'Ev{i}_focus',16,y,344,24,8,RGBA('surface'),f'hid.focus{i}')
    sec(f'Ev{i}_dot',Meter='Shape',X=S(20),Y=S(y+12),Shape=f'Ellipse 0,0,{S(3)} | Fill Color [G_col_ev{i}] | StrokeWidth 0',**hid(AGF))
    txt(f'Ev{i}_t',32,y,72,24,key=f'ev{i}.t',px=14,flag=AGF)
    txt(f'Ev{i}_n',112,y,216,24,key=f'ev{i}.n',px=16,flag=AGF)
    sec(f'Ev{i}_tip',Meter='Shape',X=S(32),Y=S(y),Shape=f'Rectangle 0,0,{S(296)},{S(24)} | Fill Color 0,0,0,1 | StrokeWidth 0',ToolTipText=f'[T_ev{i}_t] · [T_ev{i}_n]',**hid(AGF))
    button(f'Ev{i}_x',336,y,24,'×',act('act','evdel',i),f'hid.evx{i}',tr('tip_del'))
txt('Task_empty',40,528,264,24,key='tk.empty',px=14,color=RGBA('textDim'),flag='hid.tkempty')
for i in range(NT):
    sec(f'Tk{i}_box',Meter='Shape',X=S(16),Y=S(532),Shape=f'[G_chk{i}a]',Shape2=f'[G_chk{i}b]',P=f'{S(3.5)},{S(8.2)} | LineTo {S(6.5)},{S(11)} | LineTo {S(12)},{S(4.8)}',**hid(AGF))
    txt(f'Tk{i}_l',40,528,264,24,key=f'tk{i}',px=16,colkey=f'tkcol{i}',flag=AGF)
    hit(f'Tk{i}_hit',16,528,288,24,act('act','task',i),f'hid.tkx{i}',tip=f'[T_tk{i}] · '+tr('tip_toggle'))
    button(f'Tk{i}_delete',304,528,24,'×',act('act','tkdel',i),f'hid.tkx{i}',tr('tip_del'))
button('Tasks_next',336,528,24,'›',act('act','page','task_page:1'),AGF,tr('next_page'))
txt('Sync_status',16,552,272,16,key='cal.sync',px=14,colkey='stale',flag=AGF)
txt('Task_page',296,552,64,16,key='tk.page',px=14,color=RGBA('textDim'),align='right',flag=AGF)
# Watchlists: two readable rows, paginated without throwing away older items.
for L,(key,y0,tkey) in enumerate([('Fx',FX_Y,'fx.title'),('Cr',CR_Y,'cr.title')]):
    pf='fx' if L==0 else 'cr'
    txt(key+'_title',16,y0,200,24,key=tkey,px=16,bold=True,flag=LS)
    txt(key+'_page',200,y0,40,24,key=f'{pf}.page',px=14,color=RGBA('textDim'),align='right',flag=LS)
    button(key+'_prev',240,y0,24,'‹',act('act','page',f'list_page_{L}:-1'),LS,tr('previous_page'))
    button(key+'_next',272,y0,24,'›',act('act','page',f'list_page_{L}:1'),LS,tr('next_page'))
    button(key+'_add',304,y0,56,'+',input_action(f'add{L}'),LS,tr('tip_add'))
    for i in range(NF):
        y=y0+24+i*24; flag=f'hid.{pf}{i}'; kk=f'fx{i}' if L==0 else f'c{i}'
        txt(f'{key}{i}_symbol',16,y,80,24,key=f'fx{i}.p' if L==0 else f'cr{i}.s',px=14,flag=flag)
        txt(f'{key}{i}_price',104,y,96,24,key=f'fx{i}.r' if L==0 else f'cr{i}.p',px=16,bold=True,align='right',flag=flag)
        txt(f'{key}{i}_change',208,y,80,24,key=f'{pf}{i}.c',px=14,colkey=f'col.{kk}',align='right',flag=flag)
        spark(f'{key}{i}_spark',296,y+4,kk,flag)
        price_key = f'T_fx{i}_r' if L == 0 else f'T_cr{i}_p'
        hit(f'{key}{i}_hit',16,y,344,24,act('act','chart',f'{L}:{i}'),flag,f'[{price_key}] · '+tr('tip_rm'),rclick=act('act','rm',f'{L}:{i}'))
# Chart replaces watchlists only. Active tab has one sliding pill.
rect('Ch_surface',16,CH_Y,344,168,16,RGBA('surface2'),CH,RGBA('stroke',.5))
txt('Ch_title',16,CH_Y,304,24,key='ch.title',px=16,bold=True,flag=CH)
button('Ch_close',336,CH_Y,24,'×',act('act','chartclose'),CH,tr('tip_close'))
rect('Ch_tabs_track',16,CH_Y+32,184,24,8,RGBA('surface2'),CH)
sec('Ch_pill',Meter='Shape',X=f'({S(16)}+[G_ch_pillx])',Y=S(CH_Y+32),Shape='[G_ch_pill]',**hid(CH))
for i,lab in enumerate(tr('periods')):
    x=16+64*i
    txt(f'Ch_p{i}_t',x,CH_Y+32,56,24,static=lab,px=14,colkey=f'pc{i}',align='center',flag=CH)
    hit(f'Ch_p{i}',x,CH_Y+32,56,24,f'[!CommandMeasure Motion "SelectPeriod({i})"]'+act('act','period',('24h','7d','30d')[i]),CH,hover=False)
sec('Ch_line',Meter='Shape',X=S(32),Y=S(CH_Y+64),Shape='Path Ln | Fill Color 0,0,0,0 | StrokeWidth 1.5 | Stroke Color [G_ch_col]',
    Shape2='Path Ar | Fill Color [G_ch_cola] | StrokeWidth 0',Shape3='[G_ch_dot]',Ln='[G_ch_l]',Ar='[G_ch_a]',**hid(CH))
sec('Ch_cur',Meter='String',MeasureName='T_ch_current',X=S(344),Y=f'({S(CH_Y+64)}+[G_ch_cury]+{S(11)})',W=S(128),H=S(22),
    StringAlign='RightCenter',FontFace='Segoe UI Semibold',FontSize=PT(14),AntiAlias=1,FontColor=RGBA('accent'),Text='%1',**hid(CH))
txt('Ch_minmax',16,CH_Y+136,344,16,key='ch.minmax',px=14,color=RGBA('textDim'),flag=CH)
txt('Ch_status',16,CH_Y+152,344,16,key='ch.status',px=14,color=RGBA('warning'),flag=CH)
# Compact: time, one weather line, next two events, three selected quotes.
txt('Compact_weather',16,88,344,32,key='w.summary',px=16,flag=K)
hit('Compact_weather_hit',16,88,344,32,input_action('city'),K,tr('tip_city'))
txt('Cev_title',16,128,344,24,static=tr('ui_upcoming'),px=16,bold=True,flag=K)
for i in range(2):
    y=152+i*24
    txt(f'Cev{i}_time',16,y,112,24,key=f'cp.ev{i}.t',px=14,flag='hid.kev')
    txt(f'Cev{i}_title',136,y,224,24,key=f'cp.ev{i}.n',px=16,flag='hid.kev')
txt('Cev_empty',16,152,344,24,key='cp.empty',px=14,color=RGBA('textDim'),flag='hid.kempty')
for i in range(3):
    x=16+i*120
    txt(f'Ct{i}_symbol',x,208,104,16,key=f'cp.f{i}.p',px=14,color=RGBA('textDim'),flag=K)
    txt(f'Ct{i}_price',x,232,104,16,key=f'cp.f{i}.r',px=16,bold=True,flag=K)
os.makedirs(SKIN_DIR,exist_ok=True)
# Prepare this schema before exposing its INI. No network or live-calendar requests.
import engine
engine.render()
path=os.path.join(SKIN_DIR,f'{SKIN_NAME}.ini')
with open(path,'w',encoding='utf-16',newline='') as f:f.write('\r\n'.join(out)+'\r\n')
build_icons()
import shutil
shutil.copyfile(os.path.join(ROOT,'motion.lua'),os.path.join(SKIN_DIR,'@Resources','motion.lua'))
print('skin:',path,'| size px:',S(W),'x',S(TOTAL_H))
