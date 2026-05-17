# Напишіть функцію, яка приймає дві множини і повертає їхнє об'єднання.
# Створіть функцію, яка перевіряє, чи є одна множина підмножиною іншої.


def common(a: set, b: set) -> set:
    return a & b


a = {"kiwi", "apple", "banana", "cherry"}
b = {"banana", "kiwi", "mango"}
print(common(a, b))


def subset(x: set, y: set) -> bool:
    return x.issubset(y)


x = {"kiwi", "banana"}
y = {"banana", "kiwi", "mango"}

print(subset(x, y))
print(subset(a, b))
