Analyzer Machine

Задача: on-demand агент для анализа трафика/конверсий/SEO.
Мультиклиентность: configs лежат в clients/*, секреты — только локально (.env / .env.*), в git не попадают.

## Установка

```bash
pip install -r requirements.txt
```

## Быстрый старт

1. Скопируйте `.env.example` в `.env` и заполните токены:
   - `YANDEX_METRIKA_TOKEN`
   - `YM_WEBMASTER_TOKEN`
   - `GSC_CLIENT_ID`
   - `GSC_REFRESH_TOKEN`
   - при необходимости настройте `HTTP_PROXY` / `HTTPS_PROXY` / `NO_PROXY`.

2. Посмотрите клиентов:

```bash
python -m app.cli clients
```

3. Проверьте конфиг клиента:

```bash
python -m app.cli validate partacademy
```

4. Сгенерируйте отчёты (заглушка печатает полученные данные):

```bash
make reports CLIENT=partacademy
```

5. Запустите тесты:

```bash
make test
```
