"""Regression tests use synthetic files only; never touch an installed widget."""
import calendar
import configparser
import datetime as dt
import importlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

SRC=Path(__file__).resolve().parents[1]/'src'
SANDBOX=tempfile.TemporaryDirectory(prefix='td-check-',dir=Path(__file__).resolve().parents[2])
TEST_ROOT=Path(SANDBOX.name)
os.environ.update(TD_DATA_DIR=str(TEST_ROOT/'data'),TD_USER_DIR=str(TEST_ROOT/'user'),TD_SKIN_DIR=str(TEST_ROOT/'skin'),PYTHONUTF8='1')
sys.path.insert(0,str(SRC))
import td_common as common
import td_storage as storage
import engine
import google as gcal
import markets
import settings
from i18n import STR


class WidgetTests(unittest.TestCase):
    def setUp(self):
        for path in (TEST_ROOT/'data',TEST_ROOT/'user',TEST_ROOT/'skin'):path.mkdir(exist_ok=True)
        for name in ('cache.json','state.json','gmeta.json','config.json'):
            p=TEST_ROOT/'data'/name
            if p.exists():p.unlink()
        for name in ('calendars.txt','tasks.txt','events.txt'):
            p=TEST_ROOT/'user'/name
            if p.exists():p.unlink()
        common.save_config(common.DEFAULT_CONFIG)
        self.poke=patch.object(engine,'poke');self.poke.start();self.addCleanup(self.poke.stop)

    def text(self):
        result={}
        for n,keys in enumerate(common.chunks(common.text_keys())):
            values=(TEST_ROOT/'data'/f'text{n}.txt').read_text(encoding='utf-8').splitlines()
            result.update(zip(keys,values))
        return result

    def test_normalize_corrupt_config(self):
        cfg=common.normalize_config({'lang':'bad','scale':'bad','lat':float('nan'),'lists':None,'titles':7,'opacity':False,'accent':'x'})
        self.assertEqual(cfg['lang'],'ru');self.assertTrue(math.isfinite(cfg['lat']));self.assertEqual(len(cfg['lists']),2)
        self.assertEqual(cfg['scale'],1);self.assertEqual(cfg['accent'],'#8BD4E8FF')

    def test_legacy_and_empty_config(self):
        storage.write_json(common.CONFIG_PATH,{})
        self.assertEqual(len(common.load_config()['lists'][1]),3)
        storage.write_json(common.CONFIG_PATH,{'fx':['USD'],'coins':[['bitcoin','BTC']]})
        self.assertEqual(common.load_config()['lists'][1][0]['id'],'bitcoin')

    def test_atomic_failure_keeps_previous_file(self):
        path=str(TEST_ROOT/'data'/'sample.json');storage.write_json(path,{'old':True})
        with patch.object(storage.os,'replace',side_effect=OSError('synthetic')):
            with self.assertRaises(OSError):storage.write_json(path,{'new':True})
        self.assertEqual(json.loads(Path(path).read_text()),{'old':True})
        self.assertEqual(list((TEST_ROOT/'data').glob('.td-*')),[])

    def test_transient_windows_reader_does_not_break_atomic_replace(self):
        path=str(TEST_ROOT/'data'/'sample.json');storage.write_json(path,{'old':True})
        original=storage.os.replace
        attempts=[]
        def blocked_twice(src,dst):
            attempts.append(1)
            if len(attempts)<3:raise PermissionError('Synthetic reader holds file')
            return original(src,dst)
        with patch.object(storage.os,'replace',side_effect=blocked_twice):storage.write_json(path,{'new':True})
        self.assertEqual(json.loads(Path(path).read_text()),{'new':True});self.assertEqual(len(attempts),3)

    def test_lock_has_bounded_timeout_and_preserves_live_owner(self):
        lock=str(TEST_ROOT/'data'/'test.lock')
        with storage.FileLock(lock):
            start=time.monotonic()
            with self.assertRaises(TimeoutError):
                with storage.FileLock(lock,timeout=.08):pass
            self.assertLess(time.monotonic()-start,.5)
        with storage.FileLock(lock,timeout=.1):pass

    def test_action_error_releases_lock(self):
        with self.assertRaises(ValueError):engine.act('period','invalid')
        with engine.state_lock():pass

    def test_cross_process_lock_serializes_writes(self):
        code="from td_storage import FileLock,write_json; import json,time; from pathlib import Path; p=Path(__import__('sys').argv[1]);\nfor i in range(12):\n with FileLock(str(p)+'.lock'):\n  n=json.loads(p.read_text())['n']; time.sleep(.001); write_json(str(p),{'n':n+1})"
        path=TEST_ROOT/'data'/'counter.json';storage.write_json(str(path),{'n':0})
        env={**os.environ,'PYTHONPATH':str(SRC)}
        workers=[subprocess.Popen([sys.executable,'-c',code,str(path)],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE) for _ in range(3)]
        for proc in workers:
            _,err=proc.communicate(timeout=15);self.assertEqual(proc.returncode,0,err.decode())
        self.assertEqual(json.loads(path.read_text())['n'],36)

    def test_task_pages_do_not_modify_wrong_task(self):
        for i in range(5):gcal.add_task('Synthetic '+str(i))
        storage.write_json(engine.STATE,{'mode':'expanded','task_page':3})
        engine.act('task','0')
        self.assertTrue(gcal.tasks()[3]['done']);self.assertFalse(gcal.tasks()[0]['done'])
        engine.act('tkdel','0')
        self.assertEqual([t['title'] for t in gcal.tasks()],['Synthetic 0','Synthetic 1','Synthetic 2','Synthetic 4'])

    def test_watchlist_pages_and_empty_rows(self):
        cfg=common.load_config();cfg['lists'][0]+=[{'k':'fx','s':'CHF'},{'k':'fx','s':'CZK'}];common.save_config(cfg)
        storage.write_json(engine.STATE,{'mode':'expanded','list_page_0':2})
        engine.render();self.assertEqual(self.text()['fx0.p'],'CZK/RUB');self.assertEqual(self.text()['fx1.p'],'')
        engine.act('chart','0:0');self.assertEqual(engine.load_json(engine.STATE,{})['chart'],'0:4')
        engine.act('rm','0:0');self.assertEqual(len(common.load_config()['lists'][0]),4)

    def test_empty_bad_state_and_six_week_month_render(self):
        storage.write_json(engine.STATE,{'mode':'expanded','month':8,'year':2026})
        engine.render();t=self.text()
        self.assertEqual(t['c35'],'31');self.assertEqual(t['w.temp'],'—')
        self.assertIn(STR['ru']['no_events'],t['ag.empty'])
        storage.write_json(engine.STATE,{'month':99,'year':'bad','selected':'not-a-date'})
        engine.render()

    def test_graph_flat_zero_series_and_true_current_point(self):
        cfg=common.load_config();cache=engine.demo_cache(cfg)
        for price,series in [(0,[0,0]),(10,[10]),(5,[1,2,3])]:
            cache['items']['coin:bitcoin'].update(price=price,s7=series)
            storage.write_json(engine.CACHE,cache);engine.render()
            for n in range(len(common.chunks(common.geo_keys()))):
                raw=(TEST_ROOT/'data'/f'geo{n}.txt').read_text()
                self.assertNotIn('nan',raw.lower());self.assertNotIn('inf',raw.lower())
            self.assertIn(engine.money(price,'USD'),self.text()['ch.current'])

    def test_missing_period_does_not_show_another_period(self):
        self.assertIsNone(engine.item_series({'s7':[1,2,3]},'24h'))
        self.assertEqual(engine.item_series({'s7':[1,2,3]},'7d'),[1,2,3])

    def test_large_quote_preserves_cents(self):
        self.assertEqual(engine.fmt_price(2497.63),'2\u00a0497,63')
        self.assertEqual(engine.fmt_price(83220),'83\u00a0220')

    def test_adding_fourth_quote_keeps_existing_and_survives_provider_outage(self):
        with patch.object(markets,'resolve',return_value=({'k':'fx','s':'CHF'},None)),patch.object(engine,'refresh_data',return_value={'items':{}}):
            engine.add_input('add0','CHF')
        self.assertEqual([it['s'] for it in common.load_config()['lists'][0]],['USD','EUR','PLN','CHF'])

    def test_task_quotes_and_newlines_are_data_not_commands(self):
        title='Synthetic "quote" [!Quit]'
        engine.add_input('task',title+'\nsecond line')
        self.assertEqual(len(gcal.tasks()),1);self.assertEqual(gcal.tasks()[0]['title'],title+' second line')

    def test_malformed_weather_cache_does_not_crash_render(self):
        storage.write_json(engine.CACHE,{'weather':{'wrong':'schema'}})
        engine.render();self.assertEqual(self.text()['w.temp'],'—')

    def test_stale_and_offline_states_keep_saved_prices(self):
        cache=engine.demo_cache(common.load_config())
        cache['items']['coin:bitcoin']['t']=0
        storage.write_json(engine.CACHE,cache);engine.render()
        self.assertEqual(self.text()['cr.title'],STR['ru']['stale'])
        self.assertNotEqual(self.text()['cr0.p'],'—')
        cache['online']=False;storage.write_json(engine.CACHE,cache);engine.render()
        self.assertEqual(self.text()['cr.title'],STR['ru']['offline'])
        self.assertNotEqual(self.text()['cr0.p'],'—')

    def test_compact_upcoming_checks_hidden_event_pages(self):
        today=dt.date.today()
        for start in ('09:00','14:30','18:00'):gcal.add_local_event(today,start,'','Synthetic '+start)
        class FrozenDateTime(dt.datetime):
            @classmethod
            def now(cls,tz=None):return cls(today.year,today.month,today.day,17)
        with patch.object(engine.dt,'datetime',FrozenDateTime):engine.render()
        self.assertEqual(self.text()['cp.ev0.n'],'Synthetic 18:00')

    def test_time_parser_and_overnight_event(self):
        self.assertIsNone(engine._parse_clock('13pm'))
        self.assertEqual(engine._parse_clock('12am'),'00:00')
        self.assertEqual(engine._parse_clock('6:30pm'),'18:30')
        with self.assertRaises(ValueError):engine.parse_event('99:99 Synthetic meeting')
        day=dt.date(2026,10,13);gcal.add_local_event(day,'23:00','01:00','Synthetic overnight')
        ev=gcal.local_events(2026,10)[13][0]
        self.assertEqual(dt.datetime.fromisoformat(ev['end']).date(),dt.date(2026,10,14))
        storage.atomic_write(gcal.EVENT_FILE,'2026-10-13|99:99||Broken\n')
        self.assertEqual(gcal.local_events(2026,10),{})

    def test_google_partial_failure_preserves_cache_and_error(self):
        urls=['https://calendar.google.com/calendar/ical/test/private-one/basic.ics','https://calendar.google.com/calendar/ical/test/private-two/basic.ics']
        storage.atomic_write(gcal.CAL_FILE,'\n'.join(urls))
        ics=b'BEGIN:VCALENDAR\r\nVERSION:2.0\r\nEND:VCALENDAR\r\n'
        class Response:
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def read(self):return ics
        with patch.object(gcal.urllib.request,'urlopen',side_effect=[Response(),OSError('private-secret-must-not-leak')]):meta=gcal.sync(True)
        self.assertFalse(meta['ok']);self.assertEqual(meta['err'],'OSError')
        self.assertTrue(Path(gcal.cache_path(urls[0])).exists())
        self.assertTrue(gcal.view(2026,10,dt.date(2026,10,13))['connected'])

    def test_google_cache_identity_does_not_follow_index(self):
        urls=['https://calendar.google.com/calendar/ical/test/private-old/basic.ics','https://calendar.google.com/calendar/ical/test/private-new/basic.ics']
        self.assertNotEqual(gcal.cache_path(urls[0]),gcal.cache_path(urls[1]))
        storage.atomic_write(gcal.CAL_FILE,urls[1]);storage.atomic_write(str(TEST_ROOT/'data'/'ics_0.ics'),'BEGIN:VCALENDAR\nVERSION:2.0\nEND:VCALENDAR')
        storage.write_json(gcal.META,{'urls':[urls[0]],'ok':True})
        with patch.object(gcal.urllib.request,'urlopen',side_effect=OSError('synthetic')):gcal.sync(True)
        gcal.month_events(2026,10)
        self.assertFalse(Path(gcal.cache_path(urls[1])).exists())

    def test_partial_coin_response_does_not_drop_valid_coins(self):
        payload=[{'id':'bitcoin','current_price':10,'price_change_percentage_24h':None,'sparkline_in_7d':{'price':[1,None,2]}}]
        with patch.object(markets,'http',return_value=json.dumps(payload).encode()):result=markets.fetch_coins(['bitcoin','missing'])
        self.assertIn('bitcoin',result);self.assertNotIn('missing',result);self.assertIsNone(result['bitcoin']['chg'])

    def test_source_outage_is_not_global_offline(self):
        with patch.object(engine,'fetch_weather',side_effect=OSError('synthetic')),patch.object(markets,'refresh',return_value={'coins':'429'}),patch.object(engine,'network_available',return_value=True):
            cache=engine.refresh_data(True)
        self.assertTrue(cache['online']);self.assertEqual(cache['err_weather'],'OSError')

    def test_translation_keys_match(self):self.assertEqual(set(STR['ru']),set(STR['en']))

    def test_settings_validation_and_safe_google_url(self):
        values={'scale':'1','opacity':'232','fx_base':'EUR','accent':'#8bd4e8','lang':'ru','title1':'','title2':''}
        self.assertEqual(settings.validate_values(values)['scale'],1)
        with self.assertRaises(ValueError):settings.validate_values({**values,'scale':'nan'})
        self.assertFalse(gcal.valid_calendar_url('https://calendar.google.com.evil.test/calendar/ical/x.ics'))
        self.assertFalse(gcal.valid_calendar_url('http://calendar.google.com/calendar/ical/x.ics'))

    @unittest.skipUnless(os.name=='nt','Segoe UI render requires Windows')
    def test_real_skin_generator(self):
        p=subprocess.run([sys.executable,str(SRC/'build_skin.py')],env=os.environ.copy(),capture_output=True,timeout=30)
        self.assertEqual(p.returncode,0,p.stderr.decode('utf-8',errors='replace'))
        ini=TEST_ROOT/'skin'/'TihiyDen.ini';parser=configparser.ConfigParser(interpolation=None,strict=True)
        parser.read(ini,encoding='utf-16')
        self.assertEqual(parser['CardExp']['shape'].split(' | ')[0],'Rectangle 0.5,0.5,375.0,759.0,24.0')
        self.assertEqual({float(sec['fontsize']) for sec in parser.values() if sec.get('meter')=='String'},{10.5,12,18,36})
        self.assertNotIn('InputText',ini.read_text(encoding='utf-16'));self.assertNotIn('$UserInput$',ini.read_text(encoding='utf-16'))
        self.assertIn(str(TEST_ROOT/'data'),parser['Rainmeter']['onrefreshaction'])
        self.assertTrue((TEST_ROOT/'skin'/'@Resources'/'motion.lua').exists())
        cfg=common.load_config();cfg['lang']='en';common.save_config(cfg)
        p=subprocess.run([sys.executable,str(SRC/'build_skin.py')],env=os.environ.copy(),capture_output=True,timeout=30)
        self.assertEqual(p.returncode,0,p.stderr.decode('utf-8',errors='replace'))
        self.assertIn('ContextTitle=Settings',ini.read_text(encoding='utf-16'))


if __name__=='__main__':
    try:unittest.main()
    finally:SANDBOX.cleanup()
