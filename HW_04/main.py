from __future__ import annotations
from pathlib import Path
import csv


class Product:
    def __init__(
            self, name: str, category: str, price: float, quantity: int
            ) -> None:
        "Represents a product in the store"
        self.name = name
        self.category = category
        self.price = price
        self.quantity = quantity

    def set_price(self, price: float) -> None:
        """Updates product price"""
        self.price = price

    def set_quantity(self, quantity: int) -> None:
        """Updates product stock quantity"""
        self.quantity = quantity

    def __str__(self) -> str:
        return (
            f"{self.name} | {self.category} | "
            f"{self.price}$ | in stock: {self.quantity}"
        )

    def __repr__(self) -> str:
        return str(self)


class Customer:
    def __init__(self, name: str, email: str) -> None:
        """Represents a customer"""
        self.name = name
        self.email = email
        self.order_list = []

    def add_order(self, order: Order) -> None:
        """Adds order to customer history"""
        self.order_list.append(order)

    def __str__(self) -> str:
        return f"{self.name} | {self.email}"

    def __repr__(self) -> str:
        return str(self)


class Order:
    def __init__(self) -> None:
        """Represents a customer order"""
        self.product_list = {}

    def add_product(self, product: Product, quantity: int = 1) -> None:
        """Adds product to order and decreases stock"""
        if product.quantity < quantity:
            raise Exception(f"Not enough {product.name} in stock")

        product.quantity -= quantity

        if product in self.product_list:
            self.product_list[product] += quantity
        else:
            self.product_list[product] = quantity

    def remove_product(self, product: Product, quantity: int = 1) -> None:
        """Remove product from order and increases stock"""
        if product not in self.product_list:
            raise Exception(f"{product.name} not found in order")

        if self.product_list[product] < quantity:
            raise Exception(f"Cannot remove {quantity} items")

        product.quantity += quantity
        self.product_list[product] -= quantity

        if self.product_list[product] == 0:
            del self.product_list[product]

    def calculate_total(self) -> float:
        """Calculates total order price"""
        total_price = 0
        for product, quantity in self.product_list.items():
            total_price += product.price * quantity
        return total_price

    def __str__(self) -> str:
        products_info = []

        for product, quantity in self.product_list.items():
            products_info.append(
                f"{product.name} x {quantity} = {product.price * quantity}$"
            )

        return (
            "Order:\n"
            + "\n".join(products_info)
            + f"\nTotal: {self.calculate_total()}$"
        )

    def __repr__(self) -> str:
        return str(self)


ROOT = Path(__file__).resolve().parent
products_file = ROOT / "products.csv"
customers_file = ROOT / "customers.csv"
products = []
customers = []

try:
    with products_file.open("r", newline="", encoding="utf-8") as p_f:
        reader = csv.reader(p_f)

        for line in list(reader)[1:]:
            name, category, price, quantity = line
            product = Product(name, category, float(price), int(quantity))
            products.append(product)

except Exception as err:
    print(f"Error opening CSV file: {err}")


try:
    with customers_file.open("r", newline="", encoding="utf-8") as c_f:
        reader = csv.reader(c_f)

        for line in list(reader)[1:]:
            name, email = line
            customer = Customer(name, email)
            customers.append(customer)
except Exception as err:
    print(f"Error opening CSV file: {err}")


if __name__ == "__main__":
    customer = customers[0]
    print(customer)
    order = Order()
    actions = [
        (order.add_product, products[0], 3),
        (order.add_product, products[1], 1),
        (order.add_product, products[6], 6),
        (order.remove_product, products[7], 6),
        (order.remove_product, products[0], 1)
    ]

    for func, product, qty in actions:
        try:
            func(product, qty)
        except Exception as err:
            print("Error:", err)

    customer.add_order(order)

    print("\nCustomer orders:\n")

    for order in customer.order_list:
        print(order)

    print("\nProducts in stock after purchase:\n")

    for product in products:
        print(product)
