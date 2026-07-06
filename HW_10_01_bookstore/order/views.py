from datetime import datetime

from django.shortcuts import render, redirect

from order.forms import NewOrderForm
from order.models import Order


def new_order(request):
    if request.method == "POST":
        order_form = NewOrderForm(request.POST)

        if order_form.is_valid():
            order = order_form.save(commit=False)
            order.owner = request.user
            order.order_date = datetime.now()
            order.save()

            return redirect("order:order_success")

    else:
        order_form = NewOrderForm()

    return render(request, "order/new_order.html", {"order_form": order_form})


def order_success(request):
    return render(request, "order/success.html")


def order_list(request):
    orders = Order.objects.filter(owner=request.user)
    return render(request, "order/order_list.html", {"orders": orders})


def order_detail(request, order_id):
    order = Order.objects.get(id=order_id)

    return render(request, "order/order_detail.html", {
        "order": order
    })
