# Реалізуйте функцію, яка приймає число і повертає його квадрат.
# Створіть функцію, яка приймає два числа і повертає їхню суму.
# Створіть функцію яка приймає 2 числа типу int, виконує операцію ділення
# та повертає цілу частину і залишок.


def sqr_int(a: int | float) -> int | float:
    return a**2


print(sqr_int(222))


def adding(a: int | float, b: int | float):
    return a + b


print(adding(1, 0.3654))


def deviding_part(a: int, b: int) -> tuple:
    return a // b, a % b


print(deviding_part(24, 9))
