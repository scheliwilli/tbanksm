# T-Путешествия: планировщик маршрутов

Проект содержит:
- `API.py` — backend на FastAPI с поиском маршрутов, фильтрами и сортировкой.
- React frontend (Vite) — интерфейс под макеты Т-Путешествий.

## Что реализовано

### Backend
- Полный rewrite `API.py`.
- Эндпоинты:
  - `GET /` — статус и версия сервиса.
  - `GET /health` — healthcheck.
  - `GET /cities` — список доступных городов.
  - `GET /routes` — поиск маршрутов.
  - `GET /flights/{city}` — исходящие рейсы из города.
- Поддержка дат в форматах `DD.MM.YYYY` и `YYYY-MM-DD`.
- Сортировка маршрутов:
  - `cost`
  - `duration`
  - `transfers`
  - `departure`
  - `closest_time`
- Фильтры:
  - `transport` (`plane`, `train`, `electrictrain`)
  - `max_transfers`
  - `min_cost`, `max_cost`
  - `min_duration`, `max_duration`
- CORS включен для интеграции с frontend.

### Frontend
- React + Vite.
- Используются ассеты из корня проекта:
  - `logo.svg`, `calendar.svg`, `sort.svg`, `strelki.svg`, `rzd.svg`, `s7.svg`.
- Цвета/типографика по ТЗ:
  - Yellow `#FFDD2D`
  - Black `#313132`
  - Gray text `#6F7071`
  - Field/background `#F2F4F7`
  - Font `Inter`
- Экран поиска, выбор типа билета (с затемнением выбранного баннера), выдача билетов, модальные фильтры цены/длительности, сортировка.
- Адаптив под desktop и mobile.

## Быстрый старт

## 1) Backend

Установите зависимости (если еще не установлены):

```bash
pip install fastapi uvicorn
```

Запуск:

```bash
uvicorn API:app --reload --host 0.0.0.0 --port 8000
```

API будет доступно на `http://127.0.0.1:8000`.

## 2) Frontend

Установите зависимости:

```bash
npm install
```

Запуск dev-сервера:

```bash
npm run dev
```

По умолчанию frontend обращается к backend по `http://127.0.0.1:8000`.

Если backend на другом адресе, задайте переменную:

```bash
VITE_API_BASE=http://<host>:<port>
```

## Пример запроса

```http
GET /routes?origin=Moscow&destination=Novosibirsk&date=2027-01-01&sort_by=cost&transport=plane
```
