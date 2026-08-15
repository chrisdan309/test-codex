import json
import threading
import unittest
from http.server import HTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import server


class PruebasServidorUsuarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.servidor = HTTPServer(("localhost", 0), server.ServidorUsuarios)
        cls.url = f"http://localhost:{cls.servidor.server_port}"
        cls.hilo = threading.Thread(target=cls.servidor.serve_forever)
        cls.hilo.start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()
        cls.hilo.join()

    def setUp(self):
        server.usuarios.clear()
        server.proximo_id = 1

    def solicitar(self, metodo, ruta, datos=None):
        cuerpo = json.dumps(datos).encode("utf-8") if datos is not None else None
        peticion = Request(
            self.url + ruta,
            data=cuerpo,
            headers={"Content-Type": "application/json"},
            method=metodo,
        )

        try:
            with urlopen(peticion) as respuesta:
                return respuesta.status, json.load(respuesta)
        except HTTPError as error:
            return error.code, json.load(error)

    def crear_usuario(self, nombre="Ana", email="ana@example.com"):
        return self.solicitar(
            "POST", "/usuarios", {"nombre": nombre, "email": email}
        )

    def test_flujo_crud_completo(self):
        estado, usuario = self.crear_usuario()
        self.assertEqual(estado, 201)
        self.assertEqual(usuario, {"id": 1, "nombre": "Ana", "email": "ana@example.com"})

        estado, usuarios = self.solicitar("GET", "/usuarios")
        self.assertEqual(estado, 200)
        self.assertEqual(usuarios, [usuario])

        estado, actualizado = self.solicitar(
            "PUT", "/usuarios/1", {"nombre": "Ana María"}
        )
        self.assertEqual(estado, 200)
        self.assertEqual(actualizado["nombre"], "Ana María")

        estado, respuesta = self.solicitar("DELETE", "/usuarios/1")
        self.assertEqual(estado, 200)
        self.assertEqual(respuesta, {"mensaje": "Usuario eliminado"})

        estado, _ = self.solicitar("GET", "/usuarios/1")
        self.assertEqual(estado, 404)

    def test_crear_usuario_requiere_nombre_y_email(self):
        estado, respuesta = self.solicitar(
            "POST", "/usuarios", {"nombre": "Ana"}
        )
        self.assertEqual(estado, 400)
        self.assertEqual(respuesta, {"error": "Nombre y email son obligatorios"})

    def test_rechaza_email_invalido_al_crear(self):
        estado, respuesta = self.crear_usuario(email="no-es-un-correo")

        self.assertEqual(estado, 400)
        self.assertEqual(respuesta, {"error": "Formato de email inválido"})

    def test_rechaza_email_invalido_al_actualizar(self):
        self.crear_usuario()
        estado, respuesta = self.solicitar(
            "PUT", "/usuarios/1", {"email": "correo-invalido"}
        )

        self.assertEqual(estado, 400)
        self.assertEqual(respuesta, {"error": "Formato de email inválido"})

        _, usuario = self.solicitar("GET", "/usuarios/1")
        self.assertEqual(usuario["email"], "ana@example.com")

    def test_filtra_usuarios_por_nombre(self):
        self.crear_usuario(nombre="Ana María", email="ana@example.com")
        self.crear_usuario(nombre="Mariana", email="mariana@example.com")
        self.crear_usuario(nombre="Luis", email="luis@example.com")

        estado, usuarios = self.solicitar("GET", "/usuarios?q=ANA")

        self.assertEqual(estado, 200)
        self.assertEqual(
            [usuario["nombre"] for usuario in usuarios],
            ["Ana María", "Mariana"],
        )

    def test_filtro_por_nombre_sin_resultados(self):
        self.crear_usuario()

        estado, usuarios = self.solicitar("GET", "/usuarios?q=Pedro")

        self.assertEqual(estado, 200)
        self.assertEqual(usuarios, [])

    def test_rechaza_email_duplicado_al_crear(self):
        self.crear_usuario(email=" Ana@Example.com ")
        estado, respuesta = self.crear_usuario(
            nombre="Otra Ana", email="ana@example.COM"
        )

        self.assertEqual(estado, 409)
        self.assertEqual(respuesta, {"error": "El email ya está registrado"})

    def test_rechaza_email_duplicado_al_actualizar(self):
        self.crear_usuario(email="ana@example.com")
        self.crear_usuario(nombre="Luis", email="luis@example.com")

        estado, respuesta = self.solicitar(
            "PUT", "/usuarios/2", {"email": " ANA@EXAMPLE.COM "}
        )
        self.assertEqual(estado, 409)
        self.assertEqual(respuesta, {"error": "El email ya está registrado"})

        _, usuario = self.solicitar("GET", "/usuarios/2")
        self.assertEqual(usuario["email"], "luis@example.com")

    def test_usuario_puede_conservar_su_email(self):
        self.crear_usuario(email="ana@example.com")
        estado, usuario = self.solicitar(
            "PUT", "/usuarios/1", {"nombre": "Ana María", "email": " ANA@EXAMPLE.COM "}
        )

        self.assertEqual(estado, 200)
        self.assertEqual(usuario["email"], "ANA@EXAMPLE.COM")


if __name__ == "__main__":
    unittest.main()
