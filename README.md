# Тихий день · Quiet Day

**RU** · [EN](#english)

Тёмный стеклянный виджет для рабочего стола Windows на [Rainmeter](https://www.rainmeter.net/): время, погода, календарь Google, задачи, курсы валют и криптовалют с графиками. Без аккаунтов, без API-ключей — только открытые источники данных.

![Виджет](docs/screenshot-ru.png)

## Что умеет
- Погода: сейчас, по часам, на 5 дней. **Город меняется кликом по названию** — вводите «Вена» или «Paris, US», через секунду готово. Источник Open-Meteo, а если он не отвечает — автоматически met.no
- Календарь с точками событий и списком дел на выбранный день
- **Задачи и события добавляются прямо в виджете** (кнопки «Задача» / «Событие», ввод вроде `18:30 Встреча`), галочка — выполнено, × — удалить. Без текстовых файлов
- **Google Календарь** — по секретной iCal-ссылке (только чтение, без OAuth); свои события показываются вместе с ним
- **Свои котировки: что интересно вам.** Две карточки по 3 строки, кнопка «Добавить» принимает что угодно: валюту (`CHF`), `золото`, `нефть`, `серебро`, монету (`SOL`), акцию (`AAPL`, `Tesla`), индекс (`S&P`, `NASDAQ`). Клик по строке — график 24Ч / 7Д / 30Д, правая кнопка — убрать из списка
- Валюты: ЦБ РФ (база RUB) или ЕЦБ; крипта — CoinGecko; металлы, нефть, акции, индексы — Yahoo Finance
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
Почти всё меняется прямо в виджете (город, задачи, события, списки котировок). Остальное — в `%LOCALAPPDATA%\TihiyDen\data\config.json` (значок ⚙ в шапке открывает его): язык (`lang`), размер (`scale`), 24-часовой формат (`clock24`), базовая валюта (`fx_base`), названия карточек (`titles`). После правки языка или размера выполните `python build_skin.py` в папке программы.

## Удаление
```powershell
powershell -ExecutionPolicy Bypass -File uninstall.ps1
```
Скин и папка программы уходят в Корзину, задачи Планировщика удаляются.

## Источники данных и благодарности
[Open-Meteo](https://open-meteo.com/) (погода, CC BY 4.0) · [MET Norway](https://api.met.no/) · [ЦБ РФ](https://www.cbr.ru/) · [Frankfurter / ЕЦБ](https://frankfurter.dev/) · [CoinGecko](https://www.coingecko.com/) · Yahoo Finance (неофициальный публичный API: котировки могут запаздывать, это не инвестиционная рекомендация) · [Rainmeter](https://www.rainmeter.net/).
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
- Weather: now, hourly, 5-day forecast. **Change the city by clicking its name** — type "Vienna" or "Paris, US" and it is applied in a second. Open-Meteo, with automatic fallback to met.no
- Month calendar with event dots and a day agenda
- **Add tasks and events right in the widget** ("Task" / "Event" buttons, input like `6:30pm Meeting`), checkbox to complete, × to delete. No text files
- **Google Calendar** via the secret iCal URL (read-only, no OAuth); your own events are shown alongside it
- **Your own watchlists.** Two cards of three rows; the "Add" button takes anything: a currency (`CHF`), `gold`, `oil`, `silver`, a coin (`SOL`), a stock (`AAPL`, `Tesla`), an index (`S&P`, `NASDAQ`). Click a row for a 24H / 7D / 30D chart, right-click to remove it
- Currencies: Bank of Russia (base RUB) or ECB; crypto — CoinGecko; metals, oil, stocks, indices — Yahoo Finance
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
Almost everything is changed in the widget itself (city, tasks, events, watchlists). The rest lives in `%LOCALAPPDATA%\TihiyDen\data\config.json` (the ⚙ icon in the header opens it): language (`lang`), size (`scale`), 24h clock (`clock24`), base currency (`fx_base`), card titles (`titles`). Run `python build_skin.py` in the app folder after changing language or size.

### Uninstall
`powershell -ExecutionPolicy Bypass -File uninstall.ps1` (moves files to the Recycle Bin, removes scheduled tasks).

### Data sources
Open-Meteo (CC BY 4.0), MET Norway, Bank of Russia, Frankfurter / ECB, CoinGecko, Yahoo Finance (unofficial public API — quotes may be delayed and are not investment advice). Google and Google Calendar are trademarks of Google LLC; this project is not affiliated with Google.

### License
MIT — see [LICENSE](LICENSE).
