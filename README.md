# FOPilot

**Вебзастосунок обліку та фінансової аналітики для ФОП**, що працює за КВЕД 62.01
(комп'ютерне програмування).

Проєкт навчальної практики (КНУ ім. Тараса Шевченка, спеціальність «Інженерія програмного
забезпечення»). Один виконавець, монолітний застосунок.

## Що вміє

- Облік клієнтів, проєктів, відпрацьованих годин (треклог) та інвойсів.
- Генерація інвойсів із оплачуваних годин треклогу.
- Імпорт банківської виписки з CSV: автовизначення кодування, конфігуровані YAML-профілі під
  різні банки, дедуплікація, звіт про результат.
- Автоматичний матчинг надходжень до інвойсів (сума, дата, номер у призначенні платежу);
  спірні збіги — на ручне підтвердження.
- Перерахунок валютних інвойсів у гривню за курсом НБУ (з кешуванням курсів у БД).
- Аналітика: виручка по періодах, utilization rate, концентрація доходу по клієнтах, прогноз
  досягнення річного ліміту єдиного податку.
- Дашборд: 4 графіки + таблиця останніх транзакцій.

## Стек

Python 3.12 · FastAPI · Pydantic v2 · PostgreSQL 16 · SQLAlchemy 2 · Alembic · pandas ·
React · TypeScript · Vite · Recharts · pytest · ruff · Docker Compose · GitHub Actions.

## Запуск

```bash
cp .env.example .env        # за потреби відредагувати
docker compose up --build   # Postgres + бекенд + фронт
```

> **Примітка.** Повний `docker compose up` працює починаючи з етапу з міграціями Alembic
> (коміт «feat(db): ORM models and initial migration»). У самому scaffold-коміті Alembic ще не
> налаштований, тож команда бекенду `alembic upgrade head` впаде — це очікувано.

Після старту:

- Бекенд (API + Swagger): http://localhost:8000/docs
- Фронтенд (дашборд): http://localhost:5173

### Локальна розробка (бекенд)

```bash
cd backend
pip install -e ".[dev]"
alembic upgrade head
python scripts/seed.py        # тестові дані
uvicorn app.main:app --reload

ruff check . && ruff format --check .
pytest
```

## Документація

- [`docs/plan.md`](docs/plan.md) — ER-модель, структура репозиторію, план робіт.
- [`docs/architecture-decisions.md`](docs/architecture-decisions.md) — журнал архітектурних
  рішень (що обрали, чому, які альтернативи відкинули).

## Структура

```
backend/    FastAPI-застосунок (api → services → repositories → models)
frontend/   React + Vite дашборд
docs/       план і журнал рішень
```
