# WIM — Warehouse Inventory Management

Система учёта складских остатков и управления производством для малого предприятия  
Курсовой проект | ВШЭ ФКН | БПАД234 | Сайко Максим Витальевич | 2026

\---

## О проекте

Веб-приложение заменяет устаревший Telegram-бот [@ItemTracker1\_bot](https://github.com/AndrewkaKh/ItemTrackerBot), который больше не поддерживается. Реализует полный цикл производственного учёта в соответствии с ТЗ: от закупки комплектующих до отгрузки готовой продукции и финансовой аналитики.

**Функциональность (по ТЗ):**

* Единый справочник артикулов (комплектующие + готовая продукция)
* BOM-спецификации: при производстве автоматически списываются все компоненты
* Два склада: комплектующие/полуфабрикаты и готовая продукция
* Журнал движений: поступления (/po), отгрузки (/ot), производство (/pr), возвраты
* Многоканальные продажи (маркетплейс 1, маркетплейс 2, сайт)
* Экспорт отчётов в Excel
* REST API с JWT-авторизацией и ролями
* *(в разработке)* LLM-помощник (Ollama + RAG) — 5 обязательных вопросов по ТЗ

\---

## Стек технологий

|Слой|Технология|
|-|-|
|Backend|Python 3.11, FastAPI, SQLAlchemy 2.0|
|База данных|PostgreSQL 16|
|Frontend|React + TypeScript + Ant Design *(планируется)*|
|LLM|Ollama (Llama 3.1 8B) + RAG *(планируется)*|
|Деплой|Docker + docker-compose|

\---

## Структура проекта

```
wim/
│
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py          # JWT-авторизация, управление пользователями
│   │   │   ├── articles.py      # Артикулы + BOM-спецификации
│   │   │   ├── stock.py         # Текущие остатки на складах
│   │   │   ├── movements.py     # /po /ot /pr + возвраты
│   │   │   └── reports.py       # Экспорт Excel-отчётов
│   │   └── deps.py              # JWT-зависимости, роли
│   ├── core/
│   │   ├── config.py            # Настройки из .env
│   │   └── security.py          # Хэширование паролей, JWT
│   ├── db/
│   │   └── session.py           # SQLAlchemy engine, get\_db()
│   ├── models/
│   │   └── models.py            # ORM-модели всех таблиц
│   ├── schemas/
│   │   └── schemas.py           # Pydantic-схемы (request/response)
│   └── main.py                  # FastAPI app, CORS, роутеры
│
├── scripts/
│   └── seed\_data.py             # Импорт данных из warehouse\_report.xlsx
│
├── frontend/                    # ← в разработке (React)
├── llm/                         # ← в разработке (Ollama + RAG)
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

\---

## Быстрый старт

### Требования

* Docker Desktop (для PostgreSQL)
* Python 3.11+

### 1\. Клонировать репозиторий

```bash
git clone https://github.com/<username>/wim.git
cd wim
cp .env.example .env
```

### 2\. Поднять базу данных

```bash
docker-compose up -d db
```

### 3\. Установить зависимости и запустить API

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 4\. Импортировать данные из Excel

```bash
python scripts/seed\_data.py --excel warehouse\_report.xlsx
```

### 5\. Открыть документацию

```
http://localhost:8000/docs
```

Логин: `admin` / `admin123`

> В DBeaver: host `localhost`, port `5432`, db `smarttherm`, user/pass `smarttherm/smarttherm`

\---

## API — эндпоинты

|Метод|URL|Аналог в боте|
|-|-|-|
|`POST`|`/api/auth/login`|—|
|`GET`|`/api/stock`|`/watch\_stock`|
|`GET`|`/api/stock/finished`|`/watch\_stock` (только FS\_\*)|
|`GET`|`/api/articles`|—|
|`GET`|`/api/articles/{code}/bom`|—|
|`PUT`|`/api/articles/{code}/bom`|`/add\_product`|
|`POST`|`/api/movements/receipt`|`/po`|
|`POST`|`/api/movements/shipment`|`/ot`|
|`POST`|`/api/movements/production`|`/pr` + BOM-логика|
|`POST`|`/api/movements/return`|— (новое)|
|`GET`|`/api/movements`|`/filter`|
|`GET`|`/api/reports/export`|`/export\_reports`|

\---

## Роли пользователей (по ТЗ)

|Роль|Права|
|-|-|
|`admin`|Полный доступ, управление пользователями|
|`operator`|Ввод движений, просмотр данных (кладовщик / производственник / менеджер)|
|`viewer`|Только чтение (руководитель — до добавления дашбордов)|

\---

## Дорожная карта

* \[x] **Недели 10–14 (июль):** БД, ORM-модели, FastAPI бэкенд, импорт данных из Excel — **чекпоинт #1**
* \[ ] **Недели 24–28 (июль):** React фронтенд — таблицы, формы, графики движений
* \[ ] **Недели 7–10 (август):** LLM-помощник (Ollama + RAG, 5 вопросов по ТЗ)
* \[ ] **Недели 20–24 (август):** Тестирование, деплой на сервер, финансовый модуль, документация

