from functools import lru_cache


@lru_cache(maxsize=None)
def termino_fibonacci(n):
    """Calcula el término n de Fibonacci usando memoización."""
    if n < 2:
        return n

    return termino_fibonacci(n - 1) + termino_fibonacci(n - 2)


def fibonacci(cantidad):
    """Devuelve una lista con los primeros términos de Fibonacci."""
    return [termino_fibonacci(n) for n in range(cantidad)]


if __name__ == "__main__":
    try:
        cantidad = int(input("¿Cuántos términos deseas generar? "))

        if cantidad < 0:
            print("La cantidad debe ser mayor o igual a cero.")
        else:
            print("Sucesión de Fibonacci:", *fibonacci(cantidad))
    except ValueError:
        print("Ingresa un número entero válido.")
