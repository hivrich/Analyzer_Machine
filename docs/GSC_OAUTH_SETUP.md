# Настройка Google Search Console OAuth для вашего аккаунта

**Проблема:** GSC credentials в системе привязаны к другому Google аккаунту.  
**Решение:** Получить новый `refresh_token` от вашего аккаунта (у которого есть доступ к makevibe.ru).

---

## 🎯 Что нужно сделать

### Вариант 1: Использовать существующие credentials (если есть)

Если у вас уже есть OAuth credentials от Google Cloud Console:

```bash
cd /Users/hivr/Analyzer\ Machine
python3 scripts/get_gsc_refresh_token.py
```

Скрипт запросит:
- `CLIENT_ID` (из Google Cloud Console)
- `CLIENT_SECRET` (из Google Cloud Console)

Затем:
1. Откроется браузер для авторизации
2. Выберите **ваш Google аккаунт** (у которого есть makevibe.ru в Search Console)
3. Разрешите доступ
4. Скрипт выведет `refresh_token`

---

### Вариант 2: Создать новые credentials (если нет)

#### Шаг 1: Создать проект в Google Cloud Console

1. Зайдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Назовите проект, например: "Analyzer Machine"

#### Шаг 2: Включить Search Console API

1. В меню → **APIs & Services** → **Library**
2. Найдите: **"Google Search Console API"**
3. Нажмите **Enable**

#### Шаг 3: Настроить OAuth Consent Screen

1. В меню → **APIs & Services** → **OAuth consent screen**
2. Выберите **External** (или Internal, если у вас Google Workspace)
3. Заполните:
   - **App name:** Analyzer Machine
   - **User support email:** ваш email
   - **Developer contact:** ваш email
4. **Scopes:** можно пропустить (добавим позже)
5. **Test users:** добавьте ваш email (если External)
6. Сохраните

#### Шаг 4: Создать OAuth 2.0 Credentials

1. В меню → **APIs & Services** → **Credentials**
2. Нажмите **+ Create Credentials** → **OAuth client ID**
3. Выберите тип: **Desktop app**
4. Название: "Analyzer Machine Desktop"
5. Нажмите **Create**
6. Скопируйте:
   - **Client ID** (начинается с цифр, заканчивается на `.apps.googleusercontent.com`)
   - **Client secret** (случайная строка)

#### Шаг 5: Получить refresh_token

```bash
cd /Users/hivr/Analyzer\ Machine
python3 scripts/get_gsc_refresh_token.py
```

Введите:
- `CLIENT_ID` (из шага 4)
- `CLIENT_SECRET` (из шага 4)

Скрипт:
1. Откроет браузер → выберите **ваш аккаунт с makevibe.ru**
2. Разрешите доступ к Search Console
3. Выведет три строки для `.env` файла

#### Шаг 6: Обновить .env

Скрипт создаст файл `gsc_credentials.txt` с содержимым:

```
GSC_CLIENT_ID=ваш_client_id
GSC_CLIENT_SECRET=ваш_client_secret
GSC_REFRESH_TOKEN=ваш_refresh_token
```

**Скопируйте эти строки в ваш `.env` файл** (заменив старые значения).

---

## ✅ Проверка

После обновления `.env`:

```bash
cd /Users/hivr/Analyzer\ Machine

# Проверка доступа к makevibe.ru
python3 -m app.cli analyze-gsc-queries makevibe \
    2025-12-01 2025-12-27 \
    2024-12-01 2024-12-27 \
    --limit 5
```

**Ожидаемый результат:**
```
✅ Таблица с поисковыми запросами makevibe.ru
✅ Workbook сохранен в data_cache/makevibe/
```

---

## 🔧 Troubleshooting

### Ошибка: "redirect_uri_mismatch"

**Решение:** В Google Cloud Console → Credentials → Edit OAuth client:
- Добавьте Authorized redirect URI: `http://localhost:8080`

### Ошибка: "refresh_token not found"

**Причина:** Приложение уже было авторизовано ранее.

**Решение:**
1. Зайдите на https://myaccount.google.com/permissions
2. Найдите "Analyzer Machine" и отзовите доступ
3. Запустите скрипт снова

### Ошибка: "Access blocked: This app's request is invalid"

**Причина:** OAuth consent screen не настроен или app не в режиме Testing.

**Решение:**
1. Google Cloud Console → OAuth consent screen
2. Добавьте ваш email в "Test users"
3. Или переключите в режим "Production" (требует верификации)

---

## 📝 Итоговый чеклист

- [ ] Создан проект в Google Cloud Console
- [ ] Включен Search Console API
- [ ] Настроен OAuth consent screen
- [ ] Созданы OAuth 2.0 credentials (Desktop app)
- [ ] Запущен `get_gsc_refresh_token.py`
- [ ] Авторизован в нужном Google аккаунте
- [ ] Получен `refresh_token`
- [ ] Обновлен `.env` файл
- [ ] Проверен доступ командой `analyze-gsc-queries`

---

**Время выполнения:** 10-15 минут  
**Сложность:** Средняя  
**Результат:** Полный доступ к GSC для makevibe.ru ✅

