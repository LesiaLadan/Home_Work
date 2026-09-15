# stock_api

Internal warehouse service. Keeps track of book stock by `isbn` and reserves/deducts it on request from **store_api** when an order is placed. This service has no UI of its own for customers — only a REST API for store_api and a Django admin for warehouse staff.

## Model

- `StockItem` — `isbn`, `title`, `quantity` (total on hand), `reserved` (how much is reserved). `available = quantity - reserved`.
- `Reservation` — a hold for one specific store_api order: `order_reference`, `status` (`pending` / `confirmed` / `canceled`), `items` (a list of `{"isbn", "quantity"}`).

Reservation lifecycle: **PENDING** (just reserved) → **CONFIRMED** (payment succeeded, stock permanently deducted) or **CANCELED** (payment failed / reservation expired — stock returned).

## API

Every endpoint requires the header `Authorization: Service <STOCK_API_TOKEN>` — there's only one client (store_api), so JWT isn't needed here.

| Method + path | What it does |
|---|---|
| `POST /api/reservations/` | Reserve items `{order_reference, items: [{isbn, quantity}]}`. All-or-nothing: if even one `isbn` is short — 409, nothing gets reserved. |
| `GET /api/reservations/<id>/` | Reservation status. |
| `POST /api/reservations/<id>/confirm/` | Confirm (deduct for good). Idempotent. |
| `POST /api/reservations/<id>/cancel/` | Cancel (return the stock). Idempotent. |

Swagger: `/api/docs/`.

## Who manages stock

The number of books on hand (`StockItem.quantity`) is edited manually via **`/admin/`**, by the `warehouse_staff` group (created automatically by migration `0002_warehouse_staff_group`, with `view/add/change` rights on `StockItem`). There's no separate API for this — only the warehouse keeps the count.

## Celery

`cancel_expired_reservations` (every 10 min) — cancels reservations stuck in `PENDING` longer than `RESERVATION_EXPIRY_HOURS` (24h by default), and returns the stock.

## Running standalone (without store_api)

```bash
docker compose up --build
```

`web` on `http://localhost:8001/`. See `.env.example` for the required environment variables (`.env_docker`/`.env_local` are your own and are gitignored).

## Tests

```bash
pip install -r requirements-dev.txt
pytest --cov=warehouse --cov-report=term-missing
```
