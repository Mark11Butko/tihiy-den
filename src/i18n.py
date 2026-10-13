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
        "ui_add_task": "Добавить задачу",
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
        "ui_add_task": "Add task",
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


def tr(key):
    return STR[LANG][key]
