class MemoriaFibonacci:
    """Administra los términos calculados en una tabla de dispersión."""

    def __init__(self):
        self._terminos = {0: 0, 1: 1}

    def calcular(self, n):
        """Calcula un término y guarda cada resultado intermedio en la tabla."""
        if n < 0:
            raise ValueError("El índice debe ser mayor o igual a cero.")

        if n not in self._terminos:
            self._terminos[n] = self.calcular(n - 1) + self.calcular(n - 2)

        return self._terminos[n]


_memoria = MemoriaFibonacci()


def termino_fibonacci(n):
    """Calcula el término n usando una tabla de memoización compartida."""
    return _memoria.calcular(n)


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
