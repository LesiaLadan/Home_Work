# Напишіть функцію для обчислення середнього значення списку чисел.
# Реалізуйте функцію, яка приймає два списки і повертає список,
# який містить спільні елементи обох списків.


def average(a: list) -> float:
    if not a:
        return 0
    return sum(a) / len(a)


print(average([1, 2, 3, 4, 5]))


def common_el_v1(a: list, b: list) -> list:
    return list(set(a) & set(b))


print(common_el_v1([2, 9, 3, "p", "q", 3], ["p", "Q", 10, 2]))

# OR


def common_el_v2(a: list, b: list) -> list:
    return [x for x in a if x in b]


print(common_el_v2([2, 9, 3, "p", "q", 3], ["p", "Q", 10, 2]))
