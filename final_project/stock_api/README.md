# stock_api

Внутрішній сервіс складу (ProjectB). Зберігає залишки книг за їхнім `isbn` і бронює/списує їх на запит **store_api** під час оформлення замовлення. У цього сервісу немає власного інтерфейсу для покупців — тільки REST API для store_api та адмінка Django для співробітників складу.

## Модель

- `StockItem` — `isbn`, `title`, `quantity` (скільки всього), `reserved` (скільки заброньовано). `available = quantity - reserved`.
- `Reservation` — бронь під конкретне замовлення store_api: `order_reference`, `status` (`pending` / `confirmed` / `canceled`), `items` (список `{"isbn", "quantity"}`).

Життєвий цикл брони: **PENDING** (щойно заброньовано) → **CONFIRMED** (оплата пройшла, залишок списано назавжди) або **CANCELED** (оплата не відбулась/бронь протухла — залишок повернуто).

## API

Усі ендпоінти вимагають заголовок `Authorization: Service <STOCK_API_TOKEN>` — це єдиний клієнт (store_api), тому JWT тут не потрібен.

| Метод + шлях | Що робить |
|---|---|
| `POST /api/reservations/` | Забронювати позиції `{order_reference, items: [{isbn, quantity}]}`. Все-або-нічого: якщо хоч одного `isbn` не вистачає — 409, нічого не бронюється. |
| `GET /api/reservations/<id>/` | Статус брони. |
| `POST /api/reservations/<id>/confirm/` | Підтвердити (списати остаточно). Ідемпотентно. |
| `POST /api/reservations/<id>/cancel/` | Скасувати (повернути залишок). Ідемпотентно. |

Swagger: `/api/docs/`.

## Хто керує залишками

Кількість книг на складі (`StockItem.quantity`) правиться вручну через **`/admin/`**, групою `warehouse_staff` (створюється автоматично міграцією `0002_warehouse_staff_group`, права: `view/add/change` на `StockItem`). Окремого API для цього немає — рахунок веде тільки склад.

## Celery

`cancel_expired_reservations` (раз на 15 хв) — скасовує брони, що висять у `PENDING` довше `RESERVATION_EXPIRY_HOURS` (типово 24 год.), і повертає залишок.

## Запуск окремо (без store_api)

```bash
docker compose up --build
```

`web` на `http://localhost:8001/`. Дивись `.env.example` для потрібних змінних середовища (`.env_docker`/`.env_local` — свої, у git не потрапляють).

## Тести

```bash
pip install -r requirements-dev.txt
pytest --cov=warehouse --cov-report=term-missing
```
