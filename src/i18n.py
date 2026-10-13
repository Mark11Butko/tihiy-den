"""Переводы интерфейса виджета (ru / en)."""
from td_common import CFG

LANG = CFG.get("lang", "ru") if CFG.get("lang") in ("ru", "en") else "ru"

STR = {
    "ru": {
        "weekdays": ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"],
        "wd_short": ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
        "months": ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"],
        "months_gen": ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"],
        "compass": ["С", "СВ", "В", "ЮВ", "Ю", "ЮЗ", "З", "СЗ"],
        "ms": "м/с",
        "feels": "Ощущается как %s",
        "no_weather": "Нет данных о погоде",
        "no_data": "Нет данных",
        "today_fmt": "Сегодня, {d} {m}",
        "day_fmt": "{d} {m}",
        "date_full": "{d} {m} {y}",
        "month_title": "{m} {y}",
        "no_events": "Событий нет",
        "all_day": "Весь день",
        "no_title": "Без названия",
        "offline": "Нет интернета",
        "synced": "Синхронизировано в %s",
        "in_h": "Через %d ч %d мин", "in_m": "Через %d мин", "ongoing": "Идёт", "tomorrow": "Завтра",
        "cp_disconnected": "Аккаунт Google не подключён · Подключить",
        "minmax": "Мин %s · Макс %s",
        "cal_name": "Календарь %d",
        "periods": ["24Ч", "7Д", "30Д"],
        # статические подписи скина
        "ui_calendar_planner": "Календарь и планировщик",
        "ui_not_connected": "Аккаунт Google не подключён",
        "ui_connect_d1": "Подключите аккаунт, чтобы видеть события из Google",
        "ui_connect_d2": "Календаря и задачи из Google Задач.",
        "ui_connect_btn": "Подключить Google",
        "ui_add_task": "Задача",
        "ui_markets1": "Валюты и сырьё", "ui_markets2": "Крипто и акции",
        "in_add": "Что добавить?", "in_city": "Город",
        "err_nofx": "Нет курса для «%s»", "err_notfound": "«%s» не найдено", "err_city": "Город «%s» не найден", "added": "Добавлено: %s",
        "tip_city": "Сменить город (Enter — применить)", "tip_rm": "Левая кнопка — график, правая — убрать из списка",
        "tip_add": "Добавьте что угодно: валюту (CHF), золото, нефть, монету (SOL), акцию (AAPL), индекс (S&P)",
        "ui_add_event": "Событие",
        "in_task": "Новая задача", "in_event": "Новое событие", "in_fx": "Валюта", "in_coin": "Монета",
        "hint_task": "Напишите задачу и нажмите Enter (Esc — отмена)",
        "hint_event": "Например: 18:30 Встреча (время можно не писать)",
        "hint_keys": "Enter ↵ · Esc",
        "err_fx": "Нет курса для %s", "err_coin": "Монета «%s» не найдена", "err_net": "Нет связи, попробуйте ещё раз",
        "no_tasks": "Задач нет — нажмите «+ Задача»",
        "more_events": "… и ещё %d",
        "connect_google": "Подключить Google",
        "tip_mode": "Свернуть / развернуть", "tip_cfg": "Файл настроек", "tip_prev": "Предыдущий месяц", "tip_next": "Следующий месяц",
        "tip_today": "Вернуться на сегодня", "tip_sync": "Обновить календарь Google", "tip_connect": "Подключить Google Календарь",
        "tip_add_task": "Добавить задачу", "tip_add_event": "Добавить событие на выбранный день", "tip_del": "Удалить",
        "tip_toggle": "Отметить выполненной", "tip_fx": "Добавить валюту", "tip_coin": "Добавить монету", "tip_chart": "Открыть график",
        "tip_close": "Закрыть график", "tip_day": "Показать этот день",
        "ui_tasks": "Задачи",
        "ui_currencies": "Валюты",
        "ui_crypto": "Криптовалюты",
        "ui_add": "Добавить",
        "ui_upcoming": "Ближайшие события",
        "cal_template": (
            "# ПОДКЛЮЧЕНИЕ GOOGLE КАЛЕНДАРЯ\n#\n"
            "# 1. Откройте calendar.google.com -> шестерёнка -> «Настройки».\n"
            "# 2. Слева в разделе «Настройки моих календарей» выберите нужный календарь.\n"
            "# 3. Откройте «Интеграция календаря» и скопируйте «Секретный адрес в формате iCal»\n"
            "#    (в адресе есть слово private-; «Общедоступный адрес» не подойдёт).\n"
            "# 4. Вставьте адрес ниже отдельной строкой (после адреса можно через пробел написать цвет\n"
            "#    в виде #8ACBFF и название календаря). Сохраните файл (Ctrl+S).\n#\n"
            "# Можно добавить несколько календарей — по одной строке на каждый.\n"
            "# Адрес — это ключ доступа к календарю: никому его не показывайте.\n#\n"
            "# Пример:\n# https://calendar.google.com/calendar/ical/ПОЧТА/private-xxxxxxxx/basic.ics #8ACBFF Рабочий\n"
        ),
        "task_example": "Пример задачи (удалите эту строку)\nx Выполненная задача начинается с «x » и пробела\n",
    },
    "en": {
        "weekdays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "wd_short": ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
        "months": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
        "months_gen": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
        "compass": ["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
        "ms": "m/s",
        "feels": "Feels like %s",
        "no_weather": "No weather data",
        "no_data": "No data",
        "today_fmt": "Today, {m} {d}",
        "day_fmt": "{m} {d}",
        "date_full": "{m} {d}, {y}",
        "month_title": "{m} {y}",
        "no_events": "No events",
        "all_day": "All day",
        "no_title": "Untitled",
        "offline": "No internet",
        "synced": "Synced at %s",
        "in_h": "In %d h %d min", "in_m": "In %d min", "ongoing": "Now", "tomorrow": "Tomorrow",
        "cp_disconnected": "Google account not connected · Connect",
        "minmax": "Low %s · High %s",
        "cal_name": "Calendar %d",
        "periods": ["24H", "7D", "30D"],
        "ui_calendar_planner": "Calendar & planner",
        "ui_not_connected": "Google account not connected",
        "ui_connect_d1": "Connect your account to see events from Google",
        "ui_connect_d2": "Calendar and tasks.",
        "ui_connect_btn": "Connect Google",
        "ui_add_task": "Task",
        "ui_markets1": "Currencies & commodities", "ui_markets2": "Crypto & stocks",
        "in_add": "What to add?", "in_city": "City",
        "err_nofx": "No rate for \"%s\"", "err_notfound": "\"%s\" not found", "err_city": "City \"%s\" not found", "added": "Added: %s",
        "tip_city": "Change city (Enter to apply)", "tip_rm": "Left click — chart, right click — remove from the list",
        "tip_add": "Add anything: a currency (CHF), gold, oil, a coin (SOL), a stock (AAPL), an index (S&P)",
        "ui_add_event": "Event",
        "in_task": "New task", "in_event": "New event", "in_fx": "Currency", "in_coin": "Coin",
        "hint_task": "Type a task and press Enter (Esc to cancel)",
        "hint_event": "E.g. 6:30pm Meeting or 18:30 Meeting (time optional)",
        "hint_keys": "Enter ↵ · Esc",
        "err_fx": "No rate for %s", "err_coin": "Coin \"%s\" not found", "err_net": "No connection, try again",
        "no_tasks": "No tasks — press \"+ Task\"",
        "more_events": "… and %d more",
        "connect_google": "Connect Google",
        "tip_mode": "Collapse / expand", "tip_cfg": "Settings file", "tip_prev": "Previous month", "tip_next": "Next month",
        "tip_today": "Back to today", "tip_sync": "Refresh Google Calendar", "tip_connect": "Connect Google Calendar",
        "tip_add_task": "Add a task", "tip_add_event": "Add an event on the selected day", "tip_del": "Delete",
        "tip_toggle": "Mark as done", "tip_fx": "Add a currency", "tip_coin": "Add a coin", "tip_chart": "Open chart",
        "tip_close": "Close chart", "tip_day": "Show this day",
        "ui_tasks": "Tasks",
        "ui_currencies": "Currencies",
        "ui_crypto": "Crypto",
        "ui_add": "Add",
        "ui_upcoming": "Upcoming events",
        "cal_template": (
            "# CONNECT GOOGLE CALENDAR\n#\n"
            "# 1. Open calendar.google.com -> gear icon -> Settings.\n"
            "# 2. On the left, under \"Settings for my calendars\", pick the calendar.\n"
            "# 3. Open \"Integrate calendar\" and copy \"Secret address in iCal format\"\n"
            "#    (the URL contains the word private-; the \"Public address\" will NOT work).\n"
            "# 4. Paste the URL below on its own line (optionally followed by a color like #8ACBFF and a name).\n"
            "#    Save the file (Ctrl+S).\n#\n"
            "# You can add several calendars, one per line.\n"
            "# The secret URL is a key to your calendar: never share it.\n#\n"
            "# Example:\n# https://calendar.google.com/calendar/ical/EMAIL/private-xxxxxxxx/basic.ics #8ACBFF Work\n"
        ),
        "task_example": "Example task (delete this line)\nx A finished task starts with \"x \" and a space\n",
    },
}


STR['ru'].update({
    'settings':'Настройки', 'save':'Сохранить', 'cancel':'Отмена', 'general':'Основные', 'appearance':'Оформление', 'watchlists':'Котировки',
    'language':'Язык', 'city':'Город', 'base':'Базовая валюта', 'scale':'Масштаб', 'opacity':'Непрозрачность', 'accent_label':'Акцентный цвет',
    'clock24_label':'24-часовой формат', 'motion_label':'Минимум движения', 'title1':'Название первого списка', 'title2':'Название второго списка',
    'working':'Сохранение…', 'loading':'Загрузка…', 'stale':'Данные устарели', 'sync_error':'Ошибка синхронизации',
    'precip':'Осадки %d%%', 'precip_unknown':'Осадки —', 'previous_page':'Предыдущая страница', 'next_page':'Следующая страница',
    'list_full':'Лимит списка: 40 инструментов', 'input_error':'Не удалось сохранить. Проверьте данные и повторите.',
    'saved_no_data':'Инструмент сохранён · источник пока недоступен',
    'source_error':'Ошибка источника',
    'day_progress':'День пройден на %d%%', 'palette':'Палитра', 'palette_ice':'Лёд', 'palette_champagne':'Шампань', 'palette_sage':'Шалфей', 'palette_custom':'Свой цвет',
    'invalid_settings':'Проверьте масштаб (0,7–1,3), цвет HEX и базовую валюту.',
    'google_url':'Секретная ссылка iCal', 'google_help':'Google Календарь: только чтение. Задачи и свои события хранятся на этом компьютере.',
    'google_invalid':'Нужна ссылка HTTPS из раздела «Интеграция календаря» Google.', 'google_added':'Календарь добавлен',
    'input_submit':'Добавить', 'quotes_help':'Стрелки перелистывают список. Добавление сохраняет все прежние инструменты. До 40 в каждом списке.',
    'ui_connect_d1':'Подключите ссылку Google Календаря для чтения событий.', 'ui_connect_d2':'Задачи сохраняются локально.',
    'ui_not_connected':'Google Календарь не подключён', 'cp_disconnected':'Google Календарь не подключён',
    'operation_failed':'Не удалось выполнить действие', 'close':'Закрыть', 'invalid_time':'Проверьте время события: например, 18:30 или 6:30pm.',
})
STR['en'].update({
    'settings':'Settings', 'save':'Save', 'cancel':'Cancel', 'general':'General', 'appearance':'Appearance', 'watchlists':'Watchlists',
    'language':'Language', 'city':'City', 'base':'Base currency', 'scale':'Scale', 'opacity':'Opacity', 'accent_label':'Accent color',
    'clock24_label':'24-hour clock', 'motion_label':'Reduce motion', 'title1':'First list title', 'title2':'Second list title',
    'working':'Saving…', 'loading':'Loading…', 'stale':'Data is stale', 'sync_error':'Sync failed',
    'precip':'Rain %d%%', 'precip_unknown':'Rain —', 'previous_page':'Previous page', 'next_page':'Next page',
    'list_full':'List limit: 40 instruments', 'input_error':'Could not save. Check the input and try again.',
    'saved_no_data':'Instrument saved · provider is unavailable',
    'source_error':'Provider error',
    'day_progress':'%d%% of the day has passed', 'palette':'Palette', 'palette_ice':'Ice', 'palette_champagne':'Champagne', 'palette_sage':'Sage', 'palette_custom':'Custom color',
    'invalid_settings':'Check the scale (0.7–1.3), HEX color and base currency.',
    'google_url':'Secret iCal URL', 'google_help':'Google Calendar is read-only. Tasks and your own events are stored on this computer.',
    'google_invalid':'Use an HTTPS URL from Google Calendar → Integrate calendar.', 'google_added':'Calendar added',
    'input_submit':'Add', 'quotes_help':'Arrows change pages. Adding keeps existing instruments. Up to 40 in each list.',
    'ui_connect_d1':'Connect a Google Calendar link to read events.', 'ui_connect_d2':'Tasks are stored locally.',
    'ui_not_connected':'Google Calendar is not connected', 'cp_disconnected':'Google Calendar is not connected',
    'operation_failed':'Could not complete the action', 'close':'Close', 'invalid_time':'Check the event time: for example 18:30 or 6:30pm.',
})


def tr(key):
    return STR[LANG][key]
