from flask import Flask, render_template, request, redirect
import json

app = Flask(__name__)


@app.route("/")
def home() -> str:
    return render_template("index.html")


@app.route("/menu", methods=["GET", "POST"])
def menu() -> str:
    with open("data/menu.json", "r") as f:
        menu_items = json.load(f)

    if request.method == "POST":
        item_name = request.form.get("item")
        quantity = int(request.form.get("quantity"))
        item_price = None

        for item in menu_items:
            if item["name"] == item_name:
                item_price = item["price"]
                break

        try:
            with open("data/order.json", "r") as f:
                orders = json.load(f)
        except FileNotFoundError:
            orders = []

        exist = False

        for order in orders:
            if order["item"] == item_name:
                order["quantity"] += quantity
                exist = True

        if not exist:

            orders.append(
                {"item": item_name, "quantity": quantity, "price": item_price}
            )
        with open("data/order.json", "w") as f:
            json.dump(orders, f)
    return render_template("menu.html", menu=menu_items)


@app.route("/delete", methods=["POST"])
def delete_item():

    item_name = request.form.get("item")

    try:
        with open("data/order.json", "r") as f:
            orders = json.load(f)
    except FileNotFoundError:
        orders = []

    # видаляємо товар
    orders = [o for o in orders if o["item"] != item_name]

    with open("data/order.json", "w") as f:
        json.dump(orders, f, indent=4)

    return redirect("/orders")


@app.route("/orders")
def orders() -> str:

    try:
        with open("data/order.json", "r") as f:
            orders = json.load(f)
    except FileNotFoundError:
        orders = []

    total_sum = 0

    for order in orders:
        order["total"] = order["price"] * order["quantity"]
        total_sum += int(order["total"])

    return render_template("orders.html", orders=orders, total_sum=total_sum)


@app.route("/about")
def about_us() -> str:
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True)
