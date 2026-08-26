# WIM — Warehouse Inventory Management

Система учёта складских остатков и управления производством для компании SmartTherm.

Курсовой проект | НИУ ВШЭ, ФКН, БПАД234 | Сайко Максим Витальевич | 2026
Научный руководитель — Воронин Игорь Вадимович

Веб-приложение заменяет устаревший Telegram-бот [@ItemTracker1_bot](https://github.com/AndrewkaKh/ItemTrackerBot)
и покрывает полный цикл: закупка комплектующих → производство по спецификации (BOM) →
отгрузка через маркетплейсы и сайт → возвраты → финансовая аналитика → ИИ-помощник
по складским данным.

---

## Функционал

- **Артикулы и BOM** — единый справочник комплектующих и готовых изделий, спецификация
  состава каждого изделия, проверка достаточности компонентов перед производством.
- **Закупки** — регистрация поступления комплектующих, автообновление остатков.
- **Производство** — списание компонентов по BOM и оприходование готового изделия
  одной атомарной транзакцией.
- **Отгрузки и возвраты** — фиксация канала продаж (Ozon, Яндекс.Маркет, сайт),
  выручки и обратного движения товара.
- **Остатки** — текущие остатки по складам комплектующих и готовой продукции,
  подсветка нулевых и заканчивающихся позиций.
- **Журнал движений** — история всех операций с фильтрами и графиком по дням.
- **Финансы** — выручка и возвраты по каналам продаж, динамика по месяцам.
- **Отчёты** — выгрузка в Excel (остатки, движения, компоненты, готовые изделия).
- **ИИ-помощник** — чат на русском языке, отвечающий на вопросы о дефиците
  компонентов, плане закупок, топе продаж, выручке и доступной прибыли. Все числа
  считает SQL-запрос к базе, локальная модель (Ollama) только формулирует текст.

---

## Стек технологий

| Слой | Технология |
|---|---|
| Бэкенд | Python 3.13, FastAPI, SQLAlchemy 2.0 |
| База данных | PostgreSQL 16 (Docker) |
| Фронтенд | React 18, TypeScript, Ant Design, Recharts |
| ИИ-помощник | Ollama (Llama 3.1 8B) + семантический поиск (sentence-transformers) |
| Авторизация | JWT + bcrypt — реализовано, в этой версии отключено (см. ниже) |
| Инфраструктура | Docker, docker-compose |

---

## Структура проекта

```
smarttherm/
├── app/
│   ├── api/routes/         auth, articles, stock, movements, reports, assistant
│   ├── api/deps.py         текущий пользователь и проверка роли
│   ├── core/                config.py (.env), security.py (JWT, bcrypt)
│   ├── db/session.py        подключение к PostgreSQL
│   ├── models/models.py     таблицы БД
│   ├── schemas/schemas.py   валидация запросов/ответов
│   ├── services/
│   │   ├── assistant.py     логика ИИ-помощника: 5 вопросов, SQL + Ollama
│   │   └── embeddings.py    семантический поиск (RAG)
│   └── main.py               точка входа FastAPI
│
├── scripts/seed_data.py     импорт данных из warehouse_report.xlsx
│
├── wim-frontend/
│   └── src/
│       ├── api/              axios-клиент и все вызовы к API
│       ├── components/layout/AppLayout.tsx
│       └── pages/             Stock, Movements, Articles, Purchases, Production,
│                               Shipments, Returns, Finance, Users, Reports, Assistant
│
├── docker-compose.yml, Dockerfile, requirements.txt
├── .env.example
├── warehouse_report.xlsx    исходные данные для импорта
│
├── WIM_Full_Project_Description.docx   гайд по запуску, разбор каждого файла,
│                                         сверка с ТЗ, настройка ИИ-помощника, changelog
├── WIM_Windows_Full_Guide.docx         пошаговый запуск для Windows/PyCharm
├── Linux_Guide.md                       пошаговый запуск для Linux/WSL
└── ТЗ_на_склад.docx                     техническое задание
```

---

## Быстрый запуск

Нужны: Docker Desktop, Python 3.13+, Node.js 20+.

```bash
git clone <repo>
cd smarttherm
cp .env.example .env

# 1. База данных
docker compose up -d db

# 2. Бэкенд (новый терминал)
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# 3. Импорт данных (один раз)
python scripts/seed_data.py --excel warehouse_report.xlsx

# 4. Фронтенд (новый терминал)
cd wim-frontend
npm install
npm start
```

Подробные пошаговые гайды с разбором ошибок — `WIM_Windows_Full_Guide.docx`
(Windows/PyCharm) и `Linux_Guide.md` (Linux/WSL).

### Адреса после запуска

| URL | Назначение |
|---|---|
| http://localhost:3000 | Фронтенд |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/health | Проверка работоспособности |

### Подключение к БД

| Поле | Значение |
|---|---|
| Host | localhost |
| Port | 5432 |
| Database | smarttherm |
| Username / Password | smarttherm / smarttherm |

### ИИ-помощник (опционально)

Требует запущенную Ollama (локально или на отдельном сервере):

```bash
ollama pull llama3.1:8b
```

В `.env`:

```
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3.1:8b
```

Если Ollama недоступна, ассистент возвращает точные посчитанные данные без
литературной обработки текста. Подробная настройка и «тренировка» —
`WIM_Full_Project_Description.docx`, часть 7.

---

## API

| Метод | URL | Описание |
|---|---|---|
| `POST` | `/api/auth/login` | Вход (сейчас не вызывается фронтендом) |
| `GET` | `/api/stock` | Остатки по складам |
| `GET` | `/api/stock/finished` | Остатки готовых изделий |
| `GET` | `/api/articles` | Справочник артикулов |
| `PUT` | `/api/articles/{code}/bom` | Спецификация изделия |
| `POST` | `/api/movements/receipt` | Поступление |
| `POST` | `/api/movements/shipment` | Отгрузка |
| `POST` | `/api/movements/production` | Производство по BOM |
| `POST` | `/api/movements/return` | Возврат |
| `GET` | `/api/movements` | История движений с фильтрами |
| `GET` | `/api/reports/export` | Excel-отчёт |
| `POST` | `/api/assistant/ask` | Вопрос ИИ-помощнику |

---

## Авторизация

JWT и bcrypt реализованы (`security.py`), но в текущей версии проверка отключена
для демонстрации: `get_current_user()` в `app/api/deps.py` всегда возвращает
системного администратора без чтения токена. Чтобы включить обратно, нужно
переписать `get_current_user()` на декодирование JWT через `security.decode_token()`
и вернуть interceptor в `client.ts` и защищённые маршруты в `App.tsx`.

---

## Документация

| Файл | Содержание |
|---|---|
| `WIM_Full_Project_Description.docx` | Гайд по запуску, стек, построчный разбор файлов, сверка с ТЗ, настройка ИИ-помощника, changelog |
| `WIM_Windows_Full_Guide.docx` | Пошаговый запуск для Windows/PyCharm |
| `Linux_Guide.md` | Пошаговый запуск для Linux/WSL |
| `ТЗ_на_склад.docx` | Техническое задание |
