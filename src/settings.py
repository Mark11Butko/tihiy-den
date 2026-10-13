"""Native settings and safe text entry. User text never becomes a Rainmeter command."""
import argparse
import json
import os
import queue
import re
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk

from i18n import tr
from td_common import DATA, ROOT, RAINMETER, load_config, normalize_config, save_config
from td_storage import FileLock, atomic_write, write_json

BG, FG, DIM, ACCENT = '#111820', '#F3F6FA', '#B4BEC9', load_config()['accent'][:7]


def window(title):
    app = tk.Tk()
    app.title(title)
    app.configure(bg=BG)
    app.geometry('520x580')
    app.minsize(480, 460)
    app.option_add('*Font', ('Segoe UI', 11))
    style = ttk.Style(app)
    style.theme_use('clam')
    style.configure('.', background=BG, foreground=FG, fieldbackground='#24303D', bordercolor='#46515F')
    style.configure('TEntry', insertcolor=FG)
    style.map('TCombobox', fieldbackground=[('readonly', '#24303D')], foreground=[('readonly', FG)])
    style.map('TButton', background=[('active', '#344654')])
    style.configure('TNotebook.Tab', padding=(16, 8))
    style.configure('TNotebook', background=BG, borderwidth=0)
    style.configure('TNotebook.Tab', background='#24303D', foreground=FG)
    style.map('TNotebook.Tab', background=[('selected',ACCENT),('active','#344654')], foreground=[('selected',BG),('active',FG)])
    app.bind('<Escape>', lambda e: app.destroy())
    return app


def label(parent, text):
    return ttk.Label(parent, text=text, wraplength=440)


def worker(app, status, button, fn, on_success):
    """Network/disk work stays off the UI thread; all Tk calls stay on it."""
    results = queue.Queue()
    status.set(tr('working'))
    button.configure(state='disabled')
    def run():
        try: results.put((True, fn()))
        except Exception: results.put((False, tr('input_error')))
    threading.Thread(target=run, daemon=False).start()
    def poll():
        try: ok, value = results.get_nowait()
        except queue.Empty:
            app.after(100, poll)
            return
        if ok: on_success(value)
        else:
            status.set(value)
            button.configure(state='normal')
    app.after(100, poll)


def validate_values(values):
    scale = float(str(values['scale']).replace(',', '.'))
    opacity = int(values['opacity'])
    base = values['fx_base'].upper()
    if not .7 <= scale <= 1.3 or not 180 <= opacity <= 255 or base not in ('RUB','EUR','USD','GBP','PLN','CZK','CHF','HUF'):
        raise ValueError('settings')
    if not re.fullmatch('#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?', values['accent']): raise ValueError('accent')
    if values['lang'] not in ('ru','en'): raise ValueError('language')
    return {**values, 'scale':scale, 'opacity':opacity, 'fx_base':base, 'titles':[values['title1'].strip() or None,values['title2'].strip() or None]}


def apply_settings(values):
    import engine
    validated = validate_values(values)
    city = values['label'].strip()
    old = load_config()
    location = None
    if city != old['label']:
        location = engine.geocode(city, validated['lang'])
        if not location: raise ValueError('city')
    with FileLock(os.path.join(DATA, 'state.lock')):
        cfg = load_config()  # preserve concurrent additions to watchlists
        cfg.update({k:v for k,v in validated.items() if k not in ('title1','title2')})
        if location: cfg.update({k:location[k] for k in ('label','lat','lon','tz')})
        save_config(cfg)
    if location or old['fx_base'] != validated['fx_base']:
        with FileLock(os.path.join(DATA, 'refresh.lock'), timeout=30):
            cache = engine.load_json(engine.CACHE, {})
            if location: cache.pop('weather', None)
            if old['fx_base'] != validated['fx_base']:
                cache['items'] = {k:v for k,v in cache.get('items',{}).items() if not k.startswith('fx:')}
            write_json(engine.CACHE, cache)
    env = {**os.environ, 'PYTHONUTF8':'1'}
    subprocess.run([sys.executable, os.path.join(ROOT,'build_skin.py')], env=env, check=True,
                   capture_output=True, creationflags=0x08000000 if os.name=='nt' else 0)
    subprocess.Popen([sys.executable, os.path.join(ROOT,'engine.py'),'refresh'], env=env,
                     creationflags=0x08000000 if os.name=='nt' else 0)
    if os.path.exists(RAINMETER): subprocess.Popen([RAINMETER,'!Refresh',cfg['skin_name']])


def settings_window():
    cfg = load_config()
    app = window(tr('settings'))
    tabs = ttk.Notebook(app); tabs.pack(fill='both',expand=True,padx=16,pady=16)
    general, appearance, lists = [ttk.Frame(tabs,padding=16) for _ in range(3)]
    for tab,key in [(general,'general'),(appearance,'appearance'),(lists,'watchlists')]: tabs.add(tab,text=tr(key))
    fields = {}
    def field(parent,key,title,value,choices=None):
        label(parent,tr(title)).pack(anchor='w',pady=(8,4))
        var=tk.StringVar(value=str(value)); fields[key]=var
        entry=ttk.Combobox(parent,textvariable=var,values=choices,state='readonly') if choices else ttk.Entry(parent,textvariable=var)
        entry.pack(fill='x')
    field(general,'lang','language',cfg['lang'],['ru','en'])
    field(general,'label','city',cfg['label'])
    field(general,'fx_base','base',cfg['fx_base'],['RUB','EUR','USD','GBP','PLN','CZK','CHF','HUF'])
    fields['clock24']=tk.BooleanVar(value=cfg['clock24'])
    ttk.Checkbutton(general,text=tr('clock24_label'),variable=fields['clock24']).pack(anchor='w',pady=16)
    label(general,tr('google_help')).pack(anchor='w',pady=8)
    ttk.Button(general,text=tr('ui_connect_btn'),command=lambda: launch_input('google')).pack(anchor='w')
    field(appearance,'scale','scale',cfg['scale'])
    field(appearance,'opacity','opacity',cfg['opacity'])
    field(appearance,'accent','accent_label',cfg['accent'])
    label(appearance,tr('palette')).pack(anchor='w',pady=(8,4))
    palettes={tr('palette_ice'):'#8BD4E8FF',tr('palette_champagne'):'#E8C88EFF',tr('palette_sage'):'#A9D6BDFF'}
    palette_value=tk.StringVar(value=next((name for name,color in palettes.items() if color==cfg['accent']),tr('palette_custom')))
    palette_picker=ttk.Combobox(appearance,textvariable=palette_value,values=[*palettes,tr('palette_custom')],state='readonly')
    palette_picker.pack(fill='x')
    def select_palette(event):
        color=palettes.get(palette_value.get())
        if color:
            fields['accent'].set(color)
            ttk.Style(app).map('TNotebook.Tab',background=[('selected',color[:7]),('active','#344654')])
    palette_picker.bind('<<ComboboxSelected>>',select_palette)
    fields['reduced_motion']=tk.BooleanVar(value=cfg['reduced_motion'])
    ttk.Checkbutton(appearance,text=tr('motion_label'),variable=fields['reduced_motion']).pack(anchor='w',pady=16)
    field(lists,'title1','title1',cfg['titles'][0] or '')
    field(lists,'title2','title2',cfg['titles'][1] or '')
    label(lists,tr('quotes_help')).pack(anchor='w',pady=16)
    for i in range(2):
        label(lists,' · '.join(item['s'] for item in cfg['lists'][i])).pack(anchor='w')
        ttk.Button(lists,text=tr('ui_add'),command=lambda n=i:launch_input(f'add{n}')).pack(anchor='w',pady=8)
    status=tk.StringVar(); label_status=label(app,'');label_status.configure(textvariable=status);label_status.pack(fill='x',padx=32)
    controls=ttk.Frame(app,padding=16);controls.pack(fill='x')
    def save():
        values={key:var.get() for key,var in fields.items()}
        try:validate_values(values)
        except (ValueError,TypeError):status.set(tr('invalid_settings'));return
        worker(app,status,submit,lambda:apply_settings(values),lambda _:app.destroy())
    submit=ttk.Button(controls,text=tr('save'),command=save);submit.pack(side='right')
    app.bind('<Control-s>',lambda e:save())
    ttk.Button(controls,text=tr('cancel'),command=app.destroy).pack(side='right',padx=8)
    app.mainloop()


def launch_input(kind):
    subprocess.Popen([sys.executable,os.path.abspath(__file__),'--input',kind],creationflags=0x08000000 if os.name=='nt' else 0)


def input_window(kind):
    import engine
    import google as gcal
    title=tr('google_url') if kind=='google' else tr('in_city') if kind=='city' else tr('in_add') if kind.startswith('add') else tr('in_'+kind)
    app=window(title);app.geometry('520x280')
    label(app,tr('google_help') if kind=='google' else tr('hint_'+kind) if kind in ('event','task') else tr('tip_add') if kind.startswith('add') else tr('tip_city')).pack(fill='x',padx=24,pady=16)
    value=tk.StringVar()
    entry=ttk.Entry(app,textvariable=value,show='•' if kind=='google' else '')
    entry.pack(fill='x',padx=24,pady=8);entry.focus_set()
    status=tk.StringVar();hint=label(app,'');hint.configure(textvariable=status);hint.pack(fill='x',padx=24)
    def execute(text):
        if kind=='google':
            if not gcal.valid_calendar_url(text):raise ValueError('url')
            with engine.state_lock():
                existing=gcal.calendars()
                if all(c['url']!=text for c in existing):
                    content=open(gcal.CAL_FILE,encoding='utf-8').read()
                    atomic_write(gcal.CAL_FILE,content.rstrip()+'\n'+text+'\n')
            engine.refresh_data(force=True);engine.render();engine.poke()
        else:
            engine.add_input(kind,text)
            toast=engine.load_json(engine.STATE,{}).get('toast',{})
            if toast.get('sec') in (kind,'city') and not toast.get('success'):raise ValueError('input')
    def submit_input(event=None):
        if str(submit['state'])=='disabled':return
        text=value.get().strip()
        if not text:status.set(tr('input_error'));return
        if kind=='google' and not gcal.valid_calendar_url(text):status.set(tr('google_invalid'));return
        if kind=='event':
            try:engine.parse_event(text)
            except ValueError:status.set(tr('invalid_time'));return
        worker(app,status,submit,lambda:execute(text),lambda _:app.destroy())
    submit=ttk.Button(app,text=tr('input_submit'),command=submit_input);submit.pack(pady=16)
    app.bind('<Return>',submit_input)
    app.mainloop()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--input',choices=['task','event','city','add0','add1','google'])
    args=parser.parse_args()
    if args.input:input_window(args.input)
    else:settings_window()
