# Book Store

[![CI](https://github.com/LesiaLadan/Home_Work/actions/workflows/django.yml/badge.svg)](https://github.com/LesiaLadan/Home_Work/actions/workflows/django.yml)
[![codecov](https://codecov.io/gh/LesiaLadan/Home_Work/branch/main/graph/badge.svg?flag=hw25)](https://codecov.io/gh/LesiaLadan/Home_Work)

A Django online bookstore application: a catalog of books/authors/categories, a shopping cart and checkout with **Stripe** payment, user management (registration/login/delivery addresses), and book ratings/reviews. Logging is structured, via **structlog** (+ `django-structlog`).

## Stack and project structure

- **Django 6.0** (server-rendered views: Class-Based Views + function-based views; DRF is not used)
- **PostgreSQL** (primary database, connected via `psycopg`)
- **Stripe** — online card payment (Checkout Session + webhook)
- **structlog / django-structlog** — structured logging (JSON handler for production, console renderer for development)
- **pytest + pytest-django + factory_boy** — tests

Django apps:

| App | Purpose |
|---|---|
| `shop` | Books, authors, categories, ratings/reviews, main page |
| `order` | Cart, checkout, Stripe payment, webhook |
| `user_management` | Registration, login/logout, custom `User` model, delivery addresses |
| `book_store` | Project settings, root `urls.py`, middleware |

Tests live in `tests/unit` (models, forms, views) and `tests/integration` (end-to-end user flows); shared factories are in `tests/factories.py`.

## Installation (locally, without Docker)

1. Clone the repository and go to the project directory.
2. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Tests additionally require (not included in the main `requirements.txt`):

```bash
pip install pytest pytest-django pytest-cov
```

5. Configure environment variables. There are two env files in the project:
   - **`.env_docker`** — the full set of variables (Postgres credentials, `STRIPE_SECRET_KEY`/`STRIPE_PUBLIC_KEY`/`STRIPE_WEBHOOK_SECRET`, `EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD`), used inside Docker containers.
   - **`.env_local`** — overrides `DB_HOST`/`DB_PORT` to connect to Postgres from the host machine (e.g. when the database is brought up via `docker-compose up db` while Django itself runs locally).

   The project always uses PostgreSQL (the SQLite fallback in `settings.py` is commented out), so a running Postgres instance is required. The simplest approach is to bring up just `db` (and `redis`, if needed) from `docker-compose.yml`:

```bash
docker-compose up -d db redis
```

   and export the variables from both files into your current shell session before starting Django, for example:

```bash
export $(grep -v '^#' .env_docker | xargs)
export $(grep -v '^#' .env_local | xargs)
```

6. Apply migrations and start the development server:

```bash
python manage.py migrate
python manage.py runserver
```

The app will be available at `http://localhost:8000/`.

## Running with Docker

The project already includes a `docker-compose.yml` (services `web`, `db`, `redis`) and a `Dockerfile`. To bring up the whole stack at once (migrations included — run in `docker-entrypoint.sh`):

```bash
docker-compose up --build
```

The app will be available at `http://localhost:8000/`. The `web` container takes its environment variables from `.env_docker`.

## Tests

Pytest configuration is in `pytest.ini` (`DJANGO_SETTINGS_MODULE = book_store.test_settings`).

Run all tests:

```bash
pytest
```

Run with coverage (e.g. for the `shop`, `order`, `user_management` models):

```bash
pytest --cov=shop.models --cov=order.models --cov=user_management.models --cov-report=term-missing
```

HTML coverage report:

```bash
pytest --cov=shop.models --cov=order.models --cov=user_management.models --cov-report=html
# result in htmlcov/index.html
```

## AI Usage

An AI assistant (Claude) was used on this project for code review, model tests, and documentation. The full list of prompts used is in [`AI_PROMPTS.md`](AI_PROMPTS.md); the complete AI code review — original code, recommendations with reasoning, applied/rejected decisions, and final code — is in [`AI_REVIEW.md`](AI_REVIEW.md).

Briefly, what was done with AI assistance:

1. **Code review of the three most complex views** (`order/views.py::PlaceOrderView.post`, `order/views.py::create_checkout_session`/`stripe_webhook`, `shop/views.py::MainPageView.get`) — the AI analyzed error handling, N+1 queries, transaction atomicity, Stripe webhook security, duplicated pricing logic, and edge cases (a race condition on stock decrement, an empty cart, a duplicate webhook delivery), and produced a list of recommendations with reasoning. Which recommendations to apply and which to reject was decided by the project author (details in `AI_REVIEW.md`).
2. **Generating unit tests for models** (`shop.models.Book`, `order.models.Order`/`OrderDetails`, `user_management.models.User`/`DeliveryAddress`/`LastViewedBooks`) — the AI wrote tests for valid/invalid data, `__str__`/`__repr__`, default values, `Meta` constraints (`unique_together`, `isbn` uniqueness), relationships (M2M, FK), and enum-based `choices`, along with the corresponding `factory_boy` factories.
3. **Documentation** — the AI generated Google-style docstrings for all views in `shop/views.py`, `order/views.py`, `user_management/views.py`, as well as this `README.md`.

All AI-generated tests are marked with the comment `# Generated with AI, reviewed and modified` and were reviewed before being accepted.
