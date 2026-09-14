from shop.models import Book


class Cart:
    def __init__(self, request):
        self.session = request.session
        self.cart = self.session.setdefault("cart", {})

    def add(self, book_id):
        book_id = str(book_id)

        if book_id in self.cart:
            self.cart[book_id] += 1
        else:
            self.cart[book_id] = 1

        self.save()

    def remove(self, book_id):
        self.cart.pop(str(book_id), None)
        self.save()

    def clear(self):
        self.session.pop("cart", None)
        self.session.pop("cart_total", None)
        self.session.modified = True

    def save(self):
        self.session["cart"] = self.cart
        self.session.modified = True

    def get_books(self):
        return Book.objects.filter(pk__in=self.cart.keys())

    def get_quantity(self, book_id):
        return self.cart.get(str(book_id), 0)

    def set_total(self, total):
        self.session["cart_total"] = float(total)
        self.session.modified = True

    def get_total(self):
        return self.session.get("cart_total", 0.0)

    def is_empty(self):
        return len(self.cart) == 0
