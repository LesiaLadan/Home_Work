# AI Prompts Log

A list of the actual requests made to the AI assistant (Claude) while working on this project.

## Goal
Perform an AI code review (analysis only, no code changes) of the three most complex views in the project: `order/views.py::PlaceOrderView.post`, `order/views.py::create_checkout_session`+`stripe_webhook`, `shop/views.py::MainPageView.get`. Assess error handling, N+1 queries, transaction atomicity, Stripe webhook security (signature verification, `csrf_exempt`), duplicated pricing logic (wholesale/regular) across `CartView`/`CheckoutView`/`PlaceOrderView`, readability, typing, logging, and edge cases (empty cart, race condition on `in_stock` decrement, duplicate webhook).

**Result (brief):** Recorded the original code "as is" and 9–11 numbered recommendations with reasoning for each of the three views in a draft `AI_REVIEW.md` ("Step A" section). No code file was modified at this step.

---

## Goal
Apply the recommendations confirmed by the author: all points for `PlaceOrderView.post` and for `create_checkout_session`/`stripe_webhook`, all points except #3 (ranking algorithm) and #4 (caching) for `MainPageView.get`. Confirm the project and the existing tests (`tests/unit/test_views.py`, `tests/integration/test_user_flows.py`) still pass.

**Result (brief):** Rewrote `order/views.py`: race-safe stock decrement via a conditional `UPDATE ... WHERE in_stock >= quantity` + `InsufficientStockError`, moved `send_mail` out of `transaction.atomic()` and wrapped it in `try/except`, added a check for cart items that disappeared, a shared `get_price_for_user()` helper (also used in `CartView`/`CheckoutView`), `DeliveryAddress.objects.get_or_create`, idempotent Stripe webhook handling (checking `payment_status == COMPLETED`), safe `metadata.get("order_id")` reads, `ROUND_HALF_UP` rounding, structured logging (`structlog`), and removed the unused `from psycopg import logger` import. Rewrote `shop/views.py::MainPageView.get`: the five independent queries now run concurrently via `asyncio.gather`, added `prefetch_related("author", "category")` on three querysets, `HOMEPAGE_LIST_LIMIT` instead of a magic number, and a `try/except` with logging. All 46 (later 87) tests pass; additionally manually verified (via test client + factories) the stock race condition, the wholesale-price `None` fallback, `DeliveryAddress` deduplication, Stripe amount rounding, and webhook idempotency. `AI_REVIEW.md` was updated with "Applied"/"Rejected" statuses and "Final code" sections.

---

## Goal
Generate/extend unit tests for `shop.models.Book`, `order.models.Order`/`OrderDetails`, `user_management.models.User`/`DeliveryAddress`/`LastViewedBooks` using pytest + factory_boy, without duplicating existing tests in `tests/unit/test_models.py`. Cover valid/invalid data, `__str__`/`__repr__`, default values, `Meta` constraints (`unique_together` on `LastViewedBooks`, `isbn` uniqueness on `Book`), relationships (M2M `author`/`category`, FK on `Order`), and enum-based `choices` (`PaymentMethod`, `PaymentStatus`, `OrderStatus`). Reach at least 60% coverage for the three model modules.

**Result (brief):** Added factories `DeliveryAddressFactory`, `OrderFactory`, `OrderDetailsFactory`, `LastViewedBooksFactory` to `tests/factories.py` and 42 new tests (each marked with the comment `# Generated with AI, reviewed and modified`) in `tests/unit/test_models.py`. Fixed two test failures (`full_clean()` on unsaved FK objects and on a blank `password`) via an explicit `exclude=[...]`. Reached **100%** coverage for `order/models.py`, `shop/models.py`, `user_management/models.py` (well above the 60% floor); the report was saved to `coverage_report.txt` and `htmlcov/`. Full test suite: 87 passed.

---

## Goal
Move on to Part 3: add Google-style docstrings to all views in `shop/views.py`, `order/views.py`, `user_management/views.py` (classes — a short description plus a description of `get_queryset`/`form_valid`/`get_context_data` where relevant; function-based views — a detailed description of parameters and behavior); create a `README.md` from scratch (project description, installation instructions, running with Docker, running tests) with an "AI Usage" section; create `AI_PROMPTS.md`.

**Result (brief):** Added docstrings to 9 views in `shop/views.py` (`BooksListView`, `BookDetailView`, `AuthorsListView`, `AuthorDetailView`, `CategoriesListView`, `CategoryBooksListView`, `AddFeedbackView`, `UpdateFeedbackView`, `DeleteFeedbackView` — `MainPageView` already had docstrings from Step B) and to 3 functions in `user_management/views.py` (`user_registration`, `user_login`, `user_logout`); `order/views.py` was already fully documented during Step B. Created `README.md` (project description, stack, local/Docker installation, running tests and coverage, an "AI Usage" section linking to `AI_REVIEW.md` and this file). Created `AI_PROMPTS.md` (this file). Verified the full test suite (87) still passes.
