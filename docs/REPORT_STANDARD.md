# Стандарт оформления HTML-отчётов

## Обязательные требования

Все HTML-отчёты должны следовать единому стандарту оформления для обеспечения консистентности и профессионального вида.

### 1. Структура HTML

**Обязательная структура:**
```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 512 512'><defs><linearGradient id='grad' x1='0%25' y1='0%25' x2='100%25' y2='100%25'><stop offset='0%25' style='stop-color:%23ffd700;stop-opacity:1'/><stop offset='100%25' style='stop-color:%23ff8c00;stop-opacity:1'/></linearGradient></defs><rect x='20' y='180' width='140' height='312' rx='15' fill='url(%23grad)'/><rect x='186' y='80' width='140' height='412' rx='15' fill='url(%23grad)'/><rect x='352' y='20' width='140' height='472' rx='15' fill='url(%23grad)'/></svg>">
    <title>Название отчёта</title>
    <link rel="stylesheet" href="../common.css">
</head>
<body>
    <div class="container">
        <h1>Название отчёта</h1>
        <div class="subtitle">Подзаголовок отчёта</div>
        <div class="meta">
            <strong>Дата:</strong> ...<br>
            <strong>Период:</strong> ...<br>
            <!-- другая мета-информация -->
        </div>
        
        <!-- Навигация (опционально) -->
        <nav class="nav">
            <ul>
                <li><a href="#section1">Раздел 1</a></li>
                <!-- ... -->
            </ul>
        </nav>
        
        <!-- Контент отчёта -->
        <!-- ... -->
    </div>
    
    <!-- Scroll to top button (опционально) -->
    <div class="scroll-top" id="scrollTop">↑</div>
    
    <!-- JavaScript для scroll to top (опционально) -->
    <script>
        // ... код для scroll to top
    </script>
</body>
</html>
```

### 2. Обязательные элементы

#### Favicon
**Всегда используй одинаковый favicon:**
```html
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 512 512'><defs><linearGradient id='grad' x1='0%25' y1='0%25' x2='100%25' y2='100%25'><stop offset='0%25' style='stop-color:%23ffd700;stop-opacity:1'/><stop offset='100%25' style='stop-color:%23ff8c00;stop-opacity:1'/></linearGradient></defs><rect x='20' y='180' width='140' height='312' rx='15' fill='url(%23grad)'/><rect x='186' y='80' width='140' height='412' rx='15' fill='url(%23grad)'/><rect x='352' y='20' width='140' height='472' rx='15' fill='url(%23grad)'/></svg>">
```

#### Стили
**Всегда используй общий файл стилей:**
```html
<link rel="stylesheet" href="../common.css">
```

**НЕ создавай индивидуальные файлы стилей!** Все стили должны быть в `docs/reports/common.css`.

#### Структура контейнера
- **НЕ используй** обёртки `<header>`, `<div class="content">` вокруг основного контента
- Структура должна быть: `container` → `h1` → `subtitle` → `meta` → контент

### 3. Использование CSS-классов

Все отчёты должны использовать классы из `common.css`:

- `.executive-summary` — для executive summary с градиентом
- `.key-metrics` — для карточек метрик
- `.metric-card` — для отдельных карточек метрик
- `.alert`, `.alert-danger`, `.alert-warning`, `.alert-info`, `.alert-success` — для предупреждений
- `.highlight-box` — для выделенных блоков
- `.insight` — для инсайтов
- `.checklist` — для чек-листов
- `.section-number` — для нумерации секций
- `.priority-badge` — для приоритетных бейджей
- `.positive`, `.negative`, `.neutral` — для цветового выделения значений

### 4. Запрещено

❌ **НЕ создавай** индивидуальные файлы стилей (`styles.css` в папке клиента)  
❌ **НЕ используй** встроенные стили (`<style>` в HTML)  
❌ **НЕ используй** обёртки `<header>`, `<div class="content">`  
❌ **НЕ используй** markdown-контент внутри HTML (всегда правильный HTML)

### 5. Расположение файлов

Все HTML-отчёты должны находиться в:
```
docs/reports/<client_name>/index.html
```

Общий файл стилей:
```
docs/reports/common.css
```

### 6. Примеры

Смотри образцы оформления в:
- `docs/reports/makevibe/index.html` — эталонный пример
- `docs/reports/partacademy/index.html` — пример с навигацией
- `docs/reports/trisystems/index.html` — пример стратегического отчёта

### 7. Проверка перед публикацией

Перед публикацией отчёта проверь:
- [ ] Используется `common.css`
- [ ] Есть favicon
- [ ] Структура соответствует стандарту (нет лишних обёрток)
- [ ] Все CSS-классы из `common.css`
- [ ] Нет встроенных стилей
- [ ] Нет индивидуальных файлов стилей

---

**Версия стандарта:** 1.0  
**Дата создания:** 29 декабря 2025  
**Обновлено:** 29 декабря 2025

