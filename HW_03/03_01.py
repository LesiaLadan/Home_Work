# Напишіть функцію, яка приймає рядок і повертає його довжину.
# Створіть функцію, яка приймає два рядки і повертає об'єднаний рядок.


def string_len(string: str) -> int:
    return len(string)


print(string_len("Extended Smoke"))


def united_strings_v1(*args: str) -> str:
    return "".join(args)


print(united_strings_v1("Hello", "World"))

# OR


def united_strings_v2(a: str, b: str) -> str:
    return f"{a}{b}"


print(united_strings_v2("Hello", "World"))
