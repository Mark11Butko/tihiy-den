# Переходы для «Тихого дня»

Исследован [Transitions.dev](https://transitions.dev/) и публичный репозиторий
[Jakubantalik/transitions.dev](https://github.com/Jakubantalik/transitions.dev).
Лицензия разрешает использование переходов внутри личных и коммерческих продуктов,
но запрещает переупаковку библиотеки как отдельного конкурирующего набора.
Библиотека целиком в этот проект не включена.

## Что применено

**Tabs sliding** — одна подложка выбранного периода 24Ч / 7Д / 30Д.
Рецепт: [16-tabs-sliding.md](https://github.com/Jakubantalik/transitions.dev/blob/main/skills/transitions-dev/16-tabs-sliding.md).
Нативная реализация: `src/motion.lua`, Script measure + ActionTimer.
Продолжительность — 256 ms, выход по кубической кривой. Новое нажатие прерывает
предыдущий переход и начинает его с текущего положения. Первый показ — без движения.
Минимум движения включён по умолчанию; цифры, положение всего окна и графики не анимируются.
Нет размытия, вращения, частиц, постоянно работающих таймеров или новых зависимостей.

**Tooltip** — полное название длинной задачи/события и назначение кнопок доступны
через нативные подсказки Rainmeter. Заимствован принцип раскрытия подробностей при наведении;
CSS-рецепт не копировался. **Checkbox** — состояние имеет заливку и контрастную галочку,
поэтому распознаётся без движения и без зависимости только от цвета.

## Что оставлено для будущего веб-интерфейса

- [Panel reveal](https://github.com/Jakubantalik/transitions.dev/blob/main/skills/transitions-dev/07-panel-reveal.md): раскрытие деталей, с отключённым blur и небольшим смещением.
- [Skeleton reveal](https://github.com/Jakubantalik/transitions.dev/blob/main/skills/transitions-dev/14-skeleton-reveal.md): смена пустого состояния на загруженное без изменения размеров.
- [Accordion](https://github.com/Jakubantalik/transitions.dev/blob/main/skills/transitions-dev/21-accordion.md): группы дополнительных настроек.

Это ориентиры, не включённые в сборку CSS/React-компоненты. Rainmeter не исполняет CSS,
поэтому их копирование в скин не добавило бы функций. Любой будущий веб-интерфейс должен
сохранять защиту `prefers-reduced-motion` и работать с выключенными переходами.

## English

The Rainmeter tab interaction is a native adaptation inspired by Transitions.dev's
free tabs-sliding recipe. Only the actually used behavior is shipped. No CSS library
or Pro content is redistributed. Motion is short, on demand, and disabled by default.
