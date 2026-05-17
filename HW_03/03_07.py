# Функція приймає параметр (число) і якщо парне, видає слово “парне”,
# якщо ні - то “не парне”.


even_odd = lambda a: "even" if a % 2 == 0 else "odd"

print(even_odd(46))
print(even_odd(99))
