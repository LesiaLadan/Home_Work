# Створіть функцію, яка приймає словник і виводить всі ключі цього словника.
# Реалізуйте функцію, яка приймає два словники і повертає новий словник,
# який є об'єднанням обох словників.


def keys(d: dict) -> list:
    return [key for key in d]


print(
    keys(
        {
            "name": "Olha",
            "age": 25,
            "city": "Kyiv",
            "job": "accountant",
            "country": "Ukraine",
        }
    )
)


def union_dictionaries(a: dict, b: dict) -> dict:
    с = a | b
    return с


a = {"name": "Ivan", "age": 25}
b = {"age": 30, "city": "Kyiv"}
print(union_dictionaries(a, b))
