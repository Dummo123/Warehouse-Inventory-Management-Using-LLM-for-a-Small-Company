# WIM — Warehouse Inventory Management

> Система учёта складских остатков и управления производством для компании SmartTherm
> Курсовой проект | ВШЭ ФКН | БПАД234 | Сайко Максим Витальевич | 2026

---

## О проекте

Веб-приложение заменяет устаревший Telegram-бот [@ItemTracker1_bot](https://github.com/AndrewkaKh/ItemTrackerBot).
Полный цикл: закупка комплектующих → производство по BOM → отгрузка через маркетплейсы и сайт → возвраты → финансовая аналитика → ИИ-помощник по складским данным.

> ⚠️ **Авторизация в этой версии отключена** (демо-режим, решение от 30.07.2026 —
> подробности в `CHANGES.md`). Сайт открывается сразу, без логина. Код авторизации
> сохранён и легко включается обратно — см. `app/api/deps.py`.

---

## Структура проекта

```
smarttherm/
│
├── app/                               ← бэкенд (FastAPI + PostgreSQL)
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py                авторизация, пользователи (сейчас не вызывается фронтендом)
│   │   │   ├── articles.py            справочник артикулов + BOM
│   │   │   ├── stock.py               текущие остатки
│   │   │   ├── movements.py           поступление, отгрузка, производство, возврат
│   │   │   ├── reports.py             выгрузка Excel
│   │   │   └── assistant.py           ИИ-помощник — POST /api/assistant/ask
│   │   └── deps.py                    проверка токена и роли (сейчас отключена)
│   ├── core/
│   │   ├── config.py                  настройки из .env (включая OLLAMA_URL/MODEL)
│   │   └── security.py                пароли (bcrypt) + JWT-токены
│   ├── db/
│   │   └── session.py                 подключение к PostgreSQL
│   ├── models/
│   │   └── models.py                  таблицы БД
│   ├── schemas/
│   │   └── schemas.py                 валидация входящих/исходящих данных
│   ├── services/
│   │   ├── assistant.py               5 обязательных вопросов: SQL-расчёт + Ollama
│   │   └── embeddings.py              семантический поиск (RAG): распознавание
│   │                                  вопросов + поиск артикула по названию
│   └── main.py                        точка входа FastAPI
│
├── scripts/
│   └── seed_data.py                   импорт из warehouse_report.xlsx (checkpoint-коммиты)
│
├── wim-frontend/                      ← фронтенд (React + TypeScript + Ant Design)
│   ├── public/index.html
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.ts              axios (без токена — авторизация отключена)
│   │   │   └── index.ts               все функции вызовов к API
│   │   ├── hooks/
│   │   │   └── useAuth.ts             не используется, оставлен на будущее
│   │   ├── components/layout/
│   │   │   └── AppLayout.tsx          боковое меню + шапка
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx          не используется, оставлен на будущее
│   │   │   ├── StockPage.tsx          остатки на складах
│   │   │   ├── MovementsPage.tsx      журнал движений + график
│   │   │   ├── ArticlesPage.tsx       справочник + BOM
│   │   │   ├── PurchasesPage.tsx / PurchaseFormPage.tsx      закупки: список / форма
│   │   │   ├── ProductionPage.tsx / ProductionFormPage.tsx   производство: список / форма
│   │   │   ├── ShipmentsPage.tsx / ShipmentFormPage.tsx      отгрузки: список / форма
│   │   │   ├── ReturnsPage.tsx / ReturnFormPage.tsx          возвраты: список / форма
│   │   │   ├── FinancePage.tsx        выручка, возвраты, прибыль по каналам
│   │   │   ├── UsersPage.tsx          управление пользователями
│   │   │   ├── ReportsPage.tsx        скачать Excel-отчёт
│   │   │   └── AssistantPage.tsx      ИИ-помощник — рабочий чат
│   │   ├── App.tsx                    роутер, локаль ru (без защиты страниц)
│   │   └── index.tsx                  точка входа React
│   ├── package.json                   зависимости + proxy на бэкенд
│   └── tsconfig.json
│
├── .env                               ← локальные настройки (не в Git!)
├── .env.example                       шаблон .env (в Git)
├── .gitignore
├── docker-compose.yml                 PostgreSQL в Docker
├── Dockerfile                         образ для бэкенда
├── requirements.txt                   зависимости Python
├── warehouse_report.xlsx              данные для импорта
│
├── GUIDE_RU.md                        основной гайд по запуску
├── LINUX_GUIDE.md                     гайд для Linux/WSL + разбор ошибок
├── AI_ASSISTANT_SETUP.md              установка/проверка ИИ-помощника (Ollama, эмбеддинги)
└── CHANGES.md                         changelog всех правок
```

---

## Стек технологий

| Слой | Технология |
|------|-----------|
| Бэкенд | Python 3.13, FastAPI 0.115, SQLAlchemy 2.0 |
| База данных | PostgreSQL 16 (в Docker) |
| Фронтенд | React 18, TypeScript, Ant Design 5, Recharts |
| Авторизация | JWT (python-jose) + bcrypt (passlib) — **код есть, сейчас отключён** |
| ИИ-помощник | Ollama (Llama 3.1 8B, GPU-сервер) + RAG (sentence-transformers, эмбеддинги) |
| Деплой | Docker + docker-compose |

---

## Запуск (три терминала одновременно)

Подробный пошаговый гайд — в `GUIDE_RU.md` (Windows/PyCharm) и `LINUX_GUIDE.md`
(Linux/WSL, с разбором всех реально встреченных ошибок). Настройка ИИ-помощника —
отдельно в `AI_ASSISTANT_SETUP.md`.

### Требования
- Docker Desktop (запущен)
- Python 3.13+
- Node.js v20+
- (для ИИ-помощника) Ollama — локально или на отдельном GPU-сервере

### Терминал 1 — База данных
```bash
cd smarttherm
docker compose up -d db
```

### Терминал 2 — Бэкенд
```bash
cd smarttherm
python -m venv .venv && source .venv/bin/activate   # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt   # один раз
uvicorn app.main:app --reload
```

### Терминал 3 — Фронтенд
```bash
cd smarttherm/wim-frontend
npm install   # один раз
npm start
```

### Импорт данных (один раз)
```bash
python scripts/seed_data.py --excel warehouse_report.xlsx
```

---

## Адреса после запуска

| URL | Что там |
|-----|---------|
| http://localhost:3000 | Фронтенд — основной интерфейс (без логина) |
| http://localhost:8000/docs | Swagger UI — документация API |
| http://localhost:8000/health | Проверка работоспособности |

---

## Подключение в DBeaver

| Поле | Значение |
|------|---------|
| Host | localhost |
| Port | 5432 |
| Database | smarttherm |
| Username | smarttherm |
| Password | smarttherm |

---

## API — эндпоинты

| Метод | URL | Аналог в боте |
|-------|-----|--------------|
| `POST` | `/api/auth/login` | — (сейчас не вызывается фронтендом) |
| `GET` | `/api/stock` | `/watch_stock` |
| `GET` | `/api/stock/finished` | `/watch_stock` (только FS_*) |
| `GET` | `/api/articles` | — |
| `PUT` | `/api/articles/{code}/bom` | `/add_product` |
| `POST` | `/api/movements/receipt` | `/po` |
| `POST` | `/api/movements/shipment` | `/ot` |
| `POST` | `/api/movements/production` | `/pr` + BOM |
| `POST` | `/api/movements/return` | — |
| `GET` | `/api/movements` | `/filter` |
| `GET` | `/api/reports/export` | `/export_reports` |
| `POST` | `/api/assistant/ask` | — (новое, Чекпоинт #3) |

---

## Страницы фронтенда

| Страница | Маршрут | Что делает |
|---------|---------|-----------|
| Остатки | `/stock` | Таблица всех остатков, фильтры, статистика, подсветка нулей |
| Журнал движений | `/movements` | История всех операций + столбчатый график по дням |
| Артикулы | `/articles` | Справочник + CRUD + просмотр BOM в Drawer |
| Закупки | `/purchases`, `/purchases/new` | Список + отдельная страница формы регистрации |
| Производство | `/production`, `/production/new` | Список + форма с проверкой наличия компонентов (BOM) |
| Отгрузки | `/shipments`, `/shipments/new` | Список + форма с выбором канала продаж |
| Возвраты | `/returns`, `/returns/new` | Список + форма с каналом и датой |
| Финансы | `/finance` | Выручка/возвраты по каналам + тренд по месяцам |
| Участники | `/users` | Управление пользователями |
| Отчёты | `/reports` | Скачать Excel с 4 листами |
| ИИ-помощник | `/assistant` | Рабочий чат — 5 обязательных вопросов из ТЗ |

---

## Авторизация и роли

Роли (`admin`/`operator`/`viewer`) реализованы в БД и коде (`security.py`, `deps.py`),
но **проверка отключена** в этой версии для упрощения демонстрации — все запросы
выполняются от системного администратора без входа. Подробности и как включить
обратно — в `CHANGES.md` и комментариях внутри `app/api/deps.py`.

---

## Что в .gitignore

```
.env                    # реальные пароли
warehouse_report*.xlsx  # данные компании
.venv/                  # виртуальное окружение Python
wim-frontend/node_modules/  # зависимости npm
__pycache__/
*.pyc
.idea/
```

---

## Дорожная карта

- [x] **Чекпоинт #1 (июль, недели 1–2):** бэкенд, БД, API, импорт данных из Excel
- [x] **Чекпоинт #2 (июль, недели 3–4):** React фронтенд — все страницы, формы, графики
- [x] **Чекпоинт #3 (август, недели 5–6):** ИИ-помощник (Ollama + RAG, 5 вопросов из ТЗ) — ядро готово, см. `AI_ASSISTANT_SETUP.md`
- [ ] **Чекпоинт #4 (август, недели 7–8):** деплой на сервер, тесты, финальная документация

---

## Научный руководитель

Воронин Игорь Вадимович — НИУ ВШЭ, ФКН
