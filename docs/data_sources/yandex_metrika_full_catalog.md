# Яндекс.Метрика — полная карта возможностей для Analyzer Machine

**Версия:** Reporting API v1  
**Endpoint:** `https://api-metrika.yandex.net/stat/v1/data`  
**Документация:** [api.yandex.ru/metrika](https://yandex.ru/dev/metrika/)

---

## 1. Dimensions (измерения)

### 1.1 Источники трафика (`ym:s:*`)

| Dimension | Описание | Использование | Приоритет |
|-----------|----------|---------------|-----------|
| `ym:s:lastTrafficSource` | Последний источник перехода | **Реализовано** (C1) | Критично |
| `ym:s:firstTrafficSource` | Первый источник в сессии | Атрибуция first-click | Важно |
| `ym:s:referer` | URL реферера | Детализация Link traffic | Важно |
| `ym:s:lastSearchEngine` | Последняя поисковая система | Разделение Яндекс/Google | Критично |
| `ym:s:firstSearchEngine` | Первая поисковая система | Атрибуция поиска | Средне |
| `ym:s:searchPhrase` | Поисковая фраза | Запросы (если доступно) | Критично |
| `ym:s:lastSearchPhrase` | Последняя поисковая фраза | Запросы (частично) | Критично |
| `ym:s:lastAdvEngine` | Рекламная система | Детализация Ad traffic | Средне |

**Примечание:** `searchPhrase` доступна ограниченно из-за (not provided) в органике. Для полного анализа запросов нужен GSC/Вебмастер.

---

### 1.2 Страницы (`ym:s:*` и `ym:pv:*`)

| Dimension | Описание | Префикс | Использование | Приоритет |
|-----------|----------|---------|---------------|-----------|
| `ym:s:startURL` | Входная страница (landing) | `ym:s:` | **Планируется** (C2, C2.1) | Критично |
| `ym:s:endURL` | Страница выхода | `ym:s:` | Анализ exit pages | Средне |
| `ym:pv:URL` | URL просмотренной страницы | `ym:pv:` | Популярность контента | Средне |
| `ym:s:startURLPath` | Путь входной страницы (без домена) | `ym:s:` | Группировка по разделам | Важно |
| `ym:s:startURLPathLevel1` | 1-й уровень пути | `ym:s:` | Разделы сайта | Важно |
| `ym:s:startURLPathLevel2` | 2-й уровень пути | `ym:s:` | Подразделы | Средне |

**Совместимость:**
- `ym:s:startURL` совместим с `ym:s:*` метриками
- `ym:pv:URL` совместим только с `ym:pv:*` метриками
- **Нельзя** смешивать `ym:s:` и `ym:pv:` в одном запросе

---

### 1.3 Geo (география)

| Dimension | Описание | Использование | Приоритет |
|-----------|----------|---------------|-----------|
| `ym:s:regionCountry` | Страна | Гео-анализ | Средне |
| `ym:s:regionCity` | Город | Детальный гео-анализ | Средне |
| `ym:s:regionArea` | Область/регион | Региональные кампании | Низкий |

**Применение для гипотез:**
- S3 (Яндекс vs Google по регионам)
- Локальные просадки трафика

---

### 1.4 Устройства и технологии

| Dimension | Описание | Использование | Приоритет |
|-----------|----------|---------------|-----------|
| `ym:s:deviceCategory` | Категория устройства (desktop/mobile/tablet) | Анализ по устройствам | Важно |
| `ym:s:mobilePhone` | Модель телефона | Детализация mobile | Низкий |
| `ym:s:operatingSystem` | ОС (Windows, iOS, Android, etc.) | Техпроблемы по ОС | Средне |
| `ym:s:operatingSystemRoot` | Семейство ОС | Группировка ОС | Средне |
| `ym:s:browser` | Браузер | Техпроблемы по браузерам | Средне |
| `ym:s:browserMajorVersion` | Версия браузера | Совместимость | Низкий |

**Применение для гипотез:**
- H8.1 (технические проблемы на mobile/desktop)
- Просадки на конкретных устройствах

---

### 1.5 Время

| Dimension | Описание | Использование | Приоритет |
|-----------|----------|---------------|-----------|
| `ym:s:date` | Дата (YYYY-MM-DD) | Динамика по дням | Важно |
| `ym:s:datePeriod<unit>` | Группировка (day/week/month) | Агрегация | Важно |
| `ym:s:dayOfWeek` | День недели (1-7) | Недельные паттерны | Средне |
| `ym:s:hour` | Час дня (0-23) | Почасовая активность | Низкий |

**Применение:**
- Динамика изменений (тренды)
- Выявление аномалий по дням

---

### 1.6 Посетители

| Dimension | Описание | Использование | Приоритет |
|-----------|----------|---------------|-----------|
| `ym:s:isNewUser` | Новый/возвратный (Yes/No) | New vs Returning анализ | Важно |
| `ym:s:age` | Возраст аудитории | Демография | Низкий |
| `ym:s:gender` | Пол аудитории | Демография | Низкий |
| `ym:s:userID` | ID пользователя (хэш) | Когортный анализ | Низкий |

**Применение для гипотез:**
- H1.1 (изменение микса new/returning)
- Демографический анализ (опционально)

---

## 2. Metrics (метрики)

### 2.1 Базовые метрики визитов (`ym:s:*`)

| Metric | Описание | Тип | Использование | Приоритет |
|--------|----------|-----|---------------|-----------|
| `ym:s:visits` | Визиты | int | **Реализовано** (все capabilities) | Критично |
| `ym:s:users` | Уникальные пользователи | int | **Реализовано** | Критично |
| `ym:s:bounceRate` | Отказность (%) | float | **Реализовано** | Критично |
| `ym:s:pageDepth` | Глубина просмотра | float | **Реализовано** | Критично |
| `ym:s:avgVisitDurationSeconds` | Средняя длительность (сек) | float | **Реализовано** | Критично |

**Примечание:** Эти 5 метрик — основа для анализа качества трафика.

---

### 2.2 Продвинутые метрики поведения

| Metric | Описание | Использование | Приоритет |
|--------|----------|---------------|-----------|
| `ym:s:sumVisitDurationSeconds` | Суммарная длительность | Вовлеченность | Средне |
| `ym:s:percentNewVisitors` | Процент новых посетителей | New vs Returning | Важно |
| `ym:s:pageviews` | Просмотры страниц в визите | Вовлеченность | Средне |

---

### 2.3 Цели (`ym:s:goal<goal_id>*`)

| Metric Pattern | Описание | Параметризация | Использование | Приоритет |
|----------------|----------|----------------|---------------|-----------|
| `ym:s:goal<goal_id>visits` | Конверсионные визиты | `goal_id` из config | **Планируется** (C3) | Критично |
| `ym:s:goal<goal_id>conversionRate` | Конверсия (%) | `goal_id` | **Планируется** (C3) | Критично |
| `ym:s:goal<goal_id>reaches` | Достижения цели | `goal_id` | Детализация | Средне |

**Пример:**
```
goal_id = 123456
metrics = ym:s:visits,ym:s:goal123456visits,ym:s:goal123456conversionRate
```

**Применение для гипотез:**
- H4.1-H4.4 (конверсия упала/стабильна)
- Проверка качества трафика по источникам

---

### 2.4 Ecommerce (`ym:s:ecommerce<goal_id>*`)

**Статус:** Требует валидации доступности в счётчике

| Metric Pattern | Описание | Параметризация | Использование | Приоритет |
|----------------|----------|----------------|---------------|-----------|
| `ym:s:ecommerce<goal_id>Revenue` | Доход | `goal_id` (ecommerce) | **Планируется** (C4) | Важно |
| `ym:s:ecommerce<goal_id>Purchases` | Покупки | `goal_id` | **Планируется** (C4) | Важно |
| `ym:s:ecommerce<goal_id>ConversionRate` | CR в покупку (%) | `goal_id` | **Планируется** (C4) | Важно |

**Расчётные метрики:**
- AOV (Average Order Value) = Revenue / Purchases

**Применение:**
- C4 (ecommerce period compare)
- H4.* (конверсия и выручка)

---

### 2.5 Просмотры страниц (`ym:pv:*`)

| Metric | Описание | Префикс | Использование | Приоритет |
|--------|----------|---------|---------------|-----------|
| `ym:pv:pageviews` | Просмотры страниц | `ym:pv:` | Популярность контента | Средне |
| `ym:pv:users` | Пользователи (по просмотрам) | `ym:pv:` | Охват контента | Средне |

**Совместимость:** Только с `ym:pv:*` dimensions (URL, Title, etc.)

---

## 3. Filters (сегментация)

### 3.1 Синтаксис фильтров

**Операторы:**
- `==` — точное совпадение
- `!=` — не равно
- `=@` — содержит (substring)
- `!@` — не содержит
- `=~` — регулярное выражение
- `!~` — не соответствует regex
- `>`, `<`, `>=`, `<=` — числовые сравнения

**Логика:**
- `;` — AND (и)
- `,` — OR (или)

---

### 3.2 Примеры фильтров для capabilities

#### C2.1: Landing pages by source (фильтр по источнику)

```
filters=ym:s:lastTrafficSource=='Search engine traffic'
dimensions=ym:s:startURL
metrics=ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:pageDepth
```

**Использование:**
- Какие страницы упали в органике
- H2.1 (кластеры страниц)

---

#### C2.2: Landing pages by device

```
filters=ym:s:deviceCategory=='mobile'
dimensions=ym:s:startURL
metrics=ym:s:visits,ym:s:bounceRate
```

**Использование:**
- Техпроблемы на mobile
- H8.1 (техническая деградация)

---

#### C2.3: Landing pages by traffic source AND device

```
filters=ym:s:lastTrafficSource=='Search engine traffic';ym:s:deviceCategory=='mobile'
dimensions=ym:s:startURL
metrics=ym:s:visits,ym:s:bounceRate
```

**Использование:**
- Органика на mobile (комбинированный анализ)

---

#### C3.1: Goals by source (конверсии по источникам)

```
dimensions=ym:s:lastTrafficSource
metrics=ym:s:visits,ym:s:goal<goal_id>visits,ym:s:goal<goal_id>conversionRate
```

**Использование:**
- Проверка качества трафика по источникам
- H4.2 (микс трафика изменился)

---

#### C3.2: Goals by landing page

```
dimensions=ym:s:startURL
metrics=ym:s:visits,ym:s:goal<goal_id>visits,ym:s:goal<goal_id>conversionRate
```

**Использование:**
- Какие страницы конвертируют/не конвертируют
- H5.3 (изменения на странице)

---

#### C3.3: Goals by source + landing page (двойная детализация)

```
dimensions=ym:s:lastTrafficSource,ym:s:startURL
metrics=ym:s:visits,ym:s:goal<goal_id>visits,ym:s:goal<goal_id>conversionRate
```

**Использование:**
- Конверсия по источнику × страница
- Глубокий анализ качества

---

### 3.3 Фильтры по URL (regex)

**Пример 1:** Только страницы блога

```
filters=ym:s:startURL=~'.*\/blog\/.*'
```

**Пример 2:** Только категории товаров

```
filters=ym:s:startURL=~'.*\/category\/.*'
```

**Применение:**
- Анализ падения по разделам сайта
- H5.1, H5.2 (падение в нескольких страницах)

---

## 4. Совместимость dimensions × metrics

### 4.1 Таблица совместимости

| Prefix | Dimensions | Metrics | Можно миксовать? |
|--------|-----------|---------|------------------|
| `ym:s:` | Визиты | `ym:s:visits`, `ym:s:users`, `ym:s:bounceRate`, etc. | ✅ Да (между собой) |
| `ym:pv:` | Просмотры | `ym:pv:pageviews`, `ym:pv:users` | ✅ Да (между собой) |
| `ym:s:` + `ym:pv:` | Микс | Микс | ❌ НЕТ (в одном запросе) |

**Правило:**
- В одном запросе `metrics` и `dimensions` должны иметь **одинаковый префикс** (`ym:s:` или `ym:pv:`)
- Исключение: в `filters` можно использовать другой префикс

---

### 4.2 Проверенные комбинации для агента

#### ✅ Комбинация 1: Источники + базовые метрики (C1)
```
dimensions=ym:s:lastTrafficSource
metrics=ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:pageDepth,ym:s:avgVisitDurationSeconds
```

#### ✅ Комбинация 2: Landing pages + базовые метрики (C2)
```
dimensions=ym:s:startURL
metrics=ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:pageDepth,ym:s:avgVisitDurationSeconds
```

#### ✅ Комбинация 3: Landing pages + источник + базовые метрики (C2.1)
```
dimensions=ym:s:startURL
filters=ym:s:lastTrafficSource=='Search engine traffic'
metrics=ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:pageDepth,ym:s:avgVisitDurationSeconds
```

#### ✅ Комбинация 4: Источники + цели (C3)
```
dimensions=ym:s:lastTrafficSource
metrics=ym:s:visits,ym:s:goal<goal_id>visits,ym:s:goal<goal_id>conversionRate
```

#### ✅ Комбинация 5: Источники + поисковая система (S3)
```
dimensions=ym:s:lastTrafficSource,ym:s:lastSearchEngine
filters=ym:s:lastTrafficSource=='Search engine traffic'
metrics=ym:s:visits,ym:s:users
```

#### ✅ Комбинация 6: New vs Returning по источникам
```
dimensions=ym:s:lastTrafficSource,ym:s:isNewUser
metrics=ym:s:visits,ym:s:users,ym:s:bounceRate
```

#### ✅ Комбинация 7: Устройства × источники
```
dimensions=ym:s:deviceCategory,ym:s:lastTrafficSource
metrics=ym:s:visits,ym:s:bounceRate,ym:s:pageDepth
```

#### ❌ Неправильная комбинация: микс префиксов
```
dimensions=ym:s:startURL,ym:pv:URL  # ОШИБКА!
metrics=ym:s:visits,ym:pv:pageviews  # ОШИБКА!
```

---

## 5. Ограничения API

### 5.1 Лимиты

| Параметр | Значение | Комментарий |
|----------|----------|-------------|
| `limit` | 1-100,000 | По умолчанию 100, рекомендуется ≤10,000 |
| Metrics в запросе | ≤20 | Максимум 20 метрик одновременно |
| Dimensions в запросе | ≤10 | Максимум 10 измерений одновременно |
| Запросов в минуту | ~120 | Rate limit (зависит от тарифа) |

**Рекомендация для агента:**
- `limit=50-100` для топов (достаточно для анализа драйверов)
- Если нужно больше — пагинация через `offset`

---

### 5.2 Семплирование (accuracy)

| Значение `accuracy` | Описание | Использование |
|---------------------|----------|---------------|
| `low` | Низкая точность, быстро | Черновики |
| `medium` | Средняя точность (по умолчанию) | Обычный анализ |
| `high` | Высокая точность | Спорные выводы |
| `full` | Полные данные (100%) | Критичные проверки |
| `0.01-1.0` | Доля выборки | Кастомная точность |

**Рекомендация для агента:**
- По умолчанию: `accuracy=full` (для точных расчётов)
- При больших объёмах: `accuracy=high`

---

## 6. Capabilities, использующие Метрику

### Реализовано

| Capability | Dimensions | Metrics | Filters |
|------------|-----------|---------|---------|
| **C1** (sources) | `lastTrafficSource` | visits, users, bounceRate, pageDepth, avgVisitDuration | — |

### Планируется (Tier 1-2)

| Capability | Dimensions | Metrics | Filters | Приоритет |
|------------|-----------|---------|---------|-----------|
| **C2** (pages) | `startURL` | visits, users, bounceRate, pageDepth, avgVisitDuration | — | Tier 1 |
| **C2.1** (pages by source) | `startURL` | visits, users, bounceRate, pageDepth | `lastTrafficSource=='...'` | **Tier 1** |
| **C3** (goals by source) | `lastTrafficSource` | visits, goal visits, goal CR | — | Tier 2 |
| **C3.1** (goals by page) | `startURL` | visits, goal visits, goal CR | — | Tier 2 |
| **C4** (ecommerce) | `lastTrafficSource` | visits, ecommerce Revenue, Purchases, CR | — | Tier 3 |

---

## 7. Примеры запросов для новых capabilities

### C2.1: Landing pages by source

**Запрос (органика):**
```
GET /stat/v1/data
?ids=41010869
&dimensions=ym:s:startURL
&metrics=ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:pageDepth,ym:s:avgVisitDurationSeconds
&filters=ym:s:lastTrafficSource=='Search engine traffic'
&date1=2024-12-01
&date2=2024-12-31
&sort=-ym:s:visits
&limit=50
&accuracy=full
```

**Артефакты:**
- `data_cache/<client>/metrika_pages_by_source_raw_SearchEngine_2024-12-01_2024-12-31.json`
- `data_cache/<client>/metrika_pages_by_source_norm_SearchEngine_2024-12-01_2024-12-31.json`

---

### C3: Goals by source

**Запрос:**
```
GET /stat/v1/data
?ids=41010869
&dimensions=ym:s:lastTrafficSource
&metrics=ym:s:visits,ym:s:goal123456visits,ym:s:goal123456conversionRate
&date1=2024-12-01
&date2=2024-12-31
&sort=-ym:s:goal123456visits
&limit=50
&accuracy=full
```

**Артефакты:**
- `data_cache/<client>/metrika_goals_by_source_raw_<goal_id>_2024-12-01_2024-12-31.json`
- `data_cache/<client>/metrika_goals_by_source_norm_<goal_id>_2024-12-01_2024-12-31.json`

---

## 8. Приоритизация для агента

### Критично (необходимо для профессионального анализа)
1. `ym:s:lastTrafficSource` ✅ Реализовано
2. `ym:s:startURL` + filters by source → **C2.1** (Tier 1)
3. `ym:s:lastSearchEngine` → разделение Яндекс/Google (Tier 1)
4. Goals метрики → **C3** (Tier 2)

### Важно (расширение анализа)
5. `ym:s:deviceCategory` → анализ по устройствам
6. `ym:s:isNewUser` → new vs returning
7. Ecommerce метрики → **C4** (Tier 3)

### Средне (дополнительные срезы)
8. Geo dimensions
9. `ym:s:date` → динамика по дням
10. `ym:pv:URL` → популярность контента

---

## 9. Выводы для агента

**Текущее покрытие:**
- Источники трафика (C1): ✅ 100%
- Landing pages overall (C2): ⚠️ В планах
- Landing pages by source (C2.1): ❌ Критично не хватает
- Goals: ❌ Не реализовано
- Ecommerce: ❌ Не реализовано

**Блокеры профессионального анализа:**
1. **C2.1 отсутствует** → невозможно найти конкретные страницы-драйверы в органике
2. **Goals не настроены** → невозможно проверить качество трафика
3. **Нет разделения Яндекс/Google** → невозможно проверить гипотезы H3.*

**Next Steps:**
1. Реализовать C2.1 (Tier 1, критично)
2. Добавить `lastSearchEngine` для разделения ПС
3. Реализовать C3 (Goals)

