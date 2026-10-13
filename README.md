# Тихий день · Quiet Day

**RU** · [EN](#english)

Тёмный стеклянный виджет для рабочего стола Windows на [Rainmeter](https://www.rainmeter.net/): время, погода, календарь Google, задачи, курсы валют и криптовалют с графиками. Без аккаунтов, без API-ключей — только открытые источники данных.

![Виджет](docs/screenshot-ru.png)

## Что умеет
- Погода: сейчас, по часам, на 5 дней (Open-Meteo)
- Календарь с точками событий и списком дел на выбранный день
- **Google Календарь** — по секретной iCal-ссылке (только чтение, без OAuth)
- Задачи — простой файл `tasks.txt`
- Курсы валют: ЦБ РФ (база RUB) или ЕЦБ (EUR, USD, PLN…)
- Криптовалюты (CoinGecko), график 24Ч / 7Д / 30Д по клику
- Компактный режим, русский и английский интерфейс
- Положение окна не «убегает» в угол после сна ноутбука

## Установка
Нужен Windows 10/11. Всё остальное (Rainmeter, Python) установщик поставит сам через `winget`.

```powershell
git clone https://github.com/Mark11Butko/tihiy-den.git
cd tihiy-den
powershell -ExecutionPolicy Bypass -File install.ps1
```
Установщик спросит язык, город и базовую валюту. Параметры можно передать сразу:
`install.ps1 -Lang ru -City Bratislava -FxBase EUR`

Программа ставится в `%LOCALAPPDATA%\TihiyDen`, скин — в папку скинов Rainmeter. Данные обновляет задача Планировщика раз в минуту (погода раз в 15 мин, курсы раз в час, крипта раз в 5 мин).

## Google Календарь
1. calendar.google.com → шестерёнка → «Настройки» → ваш календарь → «Интеграция календаря».
2. Скопируйте **«Секретный адрес в формате iCal»** (в адресе есть `private-`; «общедоступный» не подойдёт).
3. Нажмите «Подключить Google» в виджете — откроется `calendars.txt`; вставьте адрес отдельной строкой, сохраните.

Адрес — это ключ доступа к календарю: **не публикуйте его**. Файл `calendars.txt` лежит только у вас на компьютере и в репозиторий не попадает (`.gitignore`).

## Настройка
`%LOCALAPPDATA%\TihiyDen\data\config.json`: язык (`lang`), город и координаты (`label`, `lat`, `lon`), валюты (`fx`), монеты (`coins`, id с CoinGecko), размер (`scale`), 24-часовой формат (`clock24`). После правки — `python build_skin.py` в папке программы (для языка и размера).

## Удаление
```powershell
powershell -ExecutionPolicy Bypass -File uninstall.ps1
```
Скин и папка программы уходят в Корзину, задачи Планировщика удаляются.

## Источники данных и благодарности
[Open-Meteo](https://open-meteo.com/) (погода, CC BY 4.0) · [ЦБ РФ](https://www.cbr.ru/) · [Frankfurter / ЕЦБ](https://frankfurter.dev/) · [CoinGecko](https://www.coingecko.com/) · [Rainmeter](https://www.rainmeter.net/).
Google и Google Calendar — товарные знаки Google LLC; проект с Google не связан.

## Лицензия
MIT — см. [LICENSE](LICENSE).

---

## English

A dark glass desktop widget for Windows built on [Rainmeter](https://www.rainmeter.net/): clock, weather, Google Calendar, tasks, exchange rates and a crypto chart. No accounts, no API keys — public data sources only.

![Widget](docs/screenshot-en.png)

| Chart | Compact mode |
|---|---|
| ![Chart](docs/screenshot-chart-en.png) | ![Compact](docs/screenshot-compact-en.png) |

### Features
- Weather: now, hourly, 5-day forecast (Open-Meteo)
- Month calendar with event dots and a day agenda
- **Google Calendar** via the secret iCal URL (read-only, no OAuth)
- Tasks in a plain `tasks.txt`
- Exchange rates: Bank of Russia (base RUB) or ECB (EUR, USD, PLN…)
- Crypto prices (CoinGecko) with 24H / 7D / 30D chart
- Compact mode, Russian and English UI
- The window no longer jumps to the screen corner after sleep

### Install
Windows 10/11. The installer fetches Rainmeter and Python via `winget` if they are missing.

```powershell
git clone https://github.com/Mark11Butko/tihiy-den.git
cd tihiy-den
powershell -ExecutionPolicy Bypass -File install.ps1 -Lang en -City Vienna -FxBase EUR
```

### Google Calendar
Calendar settings → *Integrate calendar* → copy the **Secret address in iCal format** (contains `private-`; the public address will not work). Click *Connect Google* in the widget and paste it into `calendars.txt`. Treat that URL like a password — never commit or share it.

### Configuration
`%LOCALAPPDATA%\TihiyDen\data\config.json` (language, city, currencies, coins, scale, 24h clock); run `python build_skin.py` in the app folder after changing language or scale.

### Uninstall
`powershell -ExecutionPolicy Bypass -File uninstall.ps1` (moves files to the Recycle Bin, removes scheduled tasks).

### Data sources
Open-Meteo (CC BY 4.0), Bank of Russia, Frankfurter / ECB, CoinGecko. Google and Google Calendar are trademarks of Google LLC; this project is not affiliated with Google.

### License
MIT — see [LICENSE](LICENSE).
