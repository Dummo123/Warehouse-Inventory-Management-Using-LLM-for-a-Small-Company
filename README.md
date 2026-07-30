# WIM — Warehouse Inventory Management

> Система учёта складских остатков и управления производством для компании SmartTherm  
> Курсовой проект | ВШЭ ФКН | БПАД234 | Сайко Максим Витальевич | 2026

---

## О проекте

Веб-приложение заменяет устаревший Telegram-бот [@ItemTracker1_bot](https://github.com/AndrewkaKh/ItemTrackerBot).  
Полный цикл: закупка комплектующих → производство по BOM → отгрузка через маркетплейсы и сайт → возвраты → финансовая аналитика.

---

## Структура проекта

```
D:\smarttherm\
│
├── app\                              ← бэкенд (FastAPI + PostgreSQL)
│   ├── api\
│   │   ├── routes\
│   │   │   ├── auth.py               авторизация, пользователи
│   │   │   ├── articles.py           справочник артикулов + BOM
│   │   │   ├── stock.py              текущие остатки
│   │   │   ├── movements.py          поступление, отгрузка, производство, возврат
│   │   │   └── reports.py            выгрузка Excel
│   │   └── deps.py                   проверка токена и роли
│   ├── core\
│   │   ├── config.py                 настройки из .env
│   │   └── security.py               пароли (bcrypt) + JWT-токены
│   ├── db\
│   │   └── session.py                подключение к PostgreSQL
│   ├── models\
│   │   └── models.py                 таблицы БД
│   ├── schemas\
│   │   └── schemas.py                валидация входящих/исходящих данных
│   └── main.py                       точка входа FastAPI
│
├── scripts\
│   └── seed_data.py                  разовый импорт из warehouse_report.xlsx
│
├── wim-frontend\                     ← фронтенд (React + TypeScript + Ant Design)
│   ├── public\index.html
│   ├── src\
│   │   ├── api\
│   │   │   ├── client.ts             axios + interceptors (токен, редирект 401)
│   │   │   └── index.ts              все функции вызовов к API
│   │   ├── hooks\
│   │   │   └── useAuth.ts            логика входа и выхода
│   │   ├── components\layout\
│   │   │   └── AppLayout.tsx         боковое меню + шапка
│   │   ├── pages\
│   │   │   ├── LoginPage.tsx         страница входа
│   │   │   ├── StockPage.tsx         остатки на складах
│   │   │   ├── MovementsPage.tsx     журнал движений + график
│   │   │   ├── ArticlesPage.tsx      справочник + BOM
│   │   │   ├── PurchasesPage.tsx     закупки (поступления)
│   │   │   ├── ProductionPage.tsx    производство + проверка компонентов
│   │   │   ├── ShipmentsPage.tsx     отгрузки по каналам
│   │   │   ├── ReturnsPage.tsx       возвраты от клиентов
│   │   │   ├── FinancePage.tsx       выручка, возвраты, прибыль по каналам
│   │   │   ├── UsersPage.tsx         управление пользователями
│   │   │   ├── ReportsPage.tsx       скачать Excel-отчёт
│   │   │   └── AssistantPage.tsx     ИИ-помощник (Чекпоинт #3)
│   │   ├── App.tsx                   роутер, защита страниц, локаль ru
│   │   └── index.tsx                 точка входа React
│   ├── package.json                  зависимости + proxy на бэкенд
│   └── tsconfig.json
│
├── .env                              ← локальные настройки (не в Git!)
├── .env.example                      шаблон .env (в Git)
├── .gitignore
├── docker-compose.yml                PostgreSQL в Docker
├── Dockerfile                        образ для бэкенда
└── requirements.txt                  зависимости Python
```

---

## Стек технологий

| Слой | Технология |
|------|-----------|
| Бэкенд | Python 3.13, FastAPI 0.115, SQLAlchemy 2.0 |
| База данных | PostgreSQL 16 (в Docker) |
| Фронтенд | React 18, TypeScript, Ant Design 5, Recharts |
| Авторизация | JWT (python-jose) + bcrypt (passlib) |
| Деплой | Docker + docker-compose |
| LLM *(план)* | Ollama (Llama 3.1 8B) + RAG — Чекпоинт #3 |

---

## Запуск (три терминала одновременно)

### Требования
- Docker Desktop (запущен — иконка кита в трее)
- Python 3.13+
- Node.js v24 LTS

### Терминал 1 — База данных
```powershell
cd D:\smarttherm
docker-compose up -d db
```

### Терминал 2 — Бэкенд
```powershell
cd D:\smarttherm
.\.venv\Scripts\activate
pip install -r requirements.txt   # один раз
uvicorn app.main:app --reload
```

### Терминал 3 — Фронтенд
```powershell
cd D:\smarttherm\wim-frontend
npm install   # один раз
npm start
```

### Импорт данных (один раз)
```powershell
# В отдельной вкладке терминала 2:
python scripts/seed_data.py --excel warehouse_report.xlsx
```

---

## Адреса после запуска

| URL | Что там |
|-----|---------|
| http://localhost:3000 | Фронтенд — основной интерфейс |
| http://localhost:8000/docs | Swagger UI — документация API |
| http://localhost:8000/health | Проверка работоспособности |

**Логин:** `admin` / `admin123`

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
| `POST` | `/api/auth/login` | — |
| `GET` | `/api/stock` | `/watch_stock` |
| `GET` | `/api/stock/finished` | `/watch_stock` (только FS_*) |
| `GET` | `/api/articles` | — |
| `PUT` | `/api/articles/{code}/bom` | `/add_product` |
| `POST` | `/api/movements/receipt` | `/po` |
| `POST` | `/api/movements/shipment` | `/ot` |
| `POST` | `/api/movements/production` | `/pr` + BOM |
| `POST` | `/api/movements/return` | — (новое) |
| `GET` | `/api/movements` | `/filter` |
| `GET` | `/api/reports/export` | `/export_reports` |

---

## Страницы фронтенда

| Страница | Маршрут | Что делает |
|---------|---------|-----------|
| Вход | `/login` | JWT-авторизация |
| Остатки | `/stock` | Таблица всех остатков, фильтры, статистика, подсветка нулей |
| Журнал движений | `/movements` | История всех операций + столбчатый график по дням |
| Артикулы | `/articles` | Справочник + CRUD + просмотр BOM в Drawer |
| Закупки | `/purchases` | История поступлений + форма регистрации |
| Производство | `/production` | Запуск производства + проверка наличия компонентов |
| Отгрузки | `/shipments` | История + форма с выбором канала продаж |
| Возвраты | `/returns` | История + форма с каналом и датой |
| Финансы | `/finance` | Выручка/возвраты по каналам + тренд по месяцам |
| Участники | `/users` | Управление пользователями (только admin) |
| Отчёты | `/reports` | Скачать Excel с 4 листами |
| ИИ-помощник | `/assistant` | Заглушка — 5 вопросов из ТЗ, активируется в Чекпоинте #3 |

---

## Роли пользователей

| Роль | Права |
|------|-------|
| `admin` | Полный доступ + управление пользователями |
| `operator` | Все складские операции + просмотр |
| `viewer` | Только просмотр |

---

## Что в .gitignore

```
.env                    # реальные пароли
warehouse_report*.xlsx  # данные компании
.venv/                  # виртуальное окружение Python
wim-frontend/node_modules/  # зависимости npm (300+ МБ)
__pycache__/
*.pyc
.idea/
```

---

## Дорожная карта

- [x] **Чекпоинт #1 (июль, недели 1–2):** бэкенд, БД, API, импорт данных из Excel
- [x] **Чекпоинт #2 (июль, недели 3–4):** React фронтенд — все страницы, формы, графики
- [ ] **Чекпоинт #3 (август, недели 5–6):** LLM-помощник (Ollama + RAG, 5 вопросов из ТЗ)
- [ ] **Чекпоинт #4 (август, недели 7–8):** деплой на сервер, тесты, финальная документация

---

## Научный руководитель

Воронин Игорь Вадимович — НИУ ВШЭ, ФКН
