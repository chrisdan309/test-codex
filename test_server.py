import json
import threading
import unittest
from http.server import HTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import server


class PruebasAPIUsuarios(unittest.TestCase):
    """Pruebas de contrato realizadas exclusivamente mediante HTTP."""

    @classmethod
    def setUpClass(cls):
        cls.servidor = HTTPServer(("localhost", 0), server.ServidorUsuarios)
        cls.url = f"http://localhost:{cls.servidor.server_port}"
        cls.hilo = threading.Thread(target=cls.servidor.serve_forever, daemon=True)
        cls.hilo.start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()
        cls.hilo.join()

    def setUp(self):
        # El estado se limpia usando la propia API para no acoplar las pruebas a
        # variables, repositorios ni otros componentes internos del servidor.
        estado, usuarios, _ = self.solicitar("GET", "/usuarios")
        self.assertEqual(estado, 200)
        for usuario in usuarios:
            self.solicitar("DELETE", f"/usuarios/{usuario['id']}")

    def solicitar(self, metodo, ruta, datos=None, cuerpo=None):
        if cuerpo is None and datos is not None:
            cuerpo = json.dumps(datos).encode("utf-8")
        elif isinstance(cuerpo, str):
            cuerpo = cuerpo.encode("utf-8")

        peticion = Request(
            self.url + ruta,
            data=cuerpo,
            headers={"Content-Type": "application/json"},
            method=metodo,
        )
        try:
            respuesta = urlopen(peticion)
        except HTTPError as error:
            respuesta = error

        with respuesta:
            return (
                respuesta.status,
                json.load(respuesta),
                dict(respuesta.headers.items()),
            )

    def crear_usuario(self, nombre="Ana", email="ana@example.com"):
        return self.solicitar(
            "POST", "/usuarios", {"nombre": nombre, "email": email}
        )

    def test_flujo_crud_completo(self):
        estado, usuario, cabeceras = self.crear_usuario()
        self.assertEqual(estado, 201)
        self.assertEqual(usuario["nombre"], "Ana")
        self.assertEqual(usuario["email"], "ana@example.com")
        self.assertIsInstance(usuario["id"], int)
        self.assertEqual(cabeceras["Content-Type"], "application/json; charset=utf-8")

        usuario_id = usuario["id"]
        estado, usuarios, _ = self.solicitar("GET", "/usuarios")
        self.assertEqual((estado, usuarios), (200, [usuario]))

        estado, obtenido, _ = self.solicitar("GET", f"/usuarios/{usuario_id}")
        self.assertEqual((estado, obtenido), (200, usuario))

        estado, actualizado, _ = self.solicitar(
            "PUT", f"/usuarios/{usuario_id}", {"nombre": "Ana María"}
        )
        self.assertEqual(estado, 200)
        self.assertEqual(actualizado, {**usuario, "nombre": "Ana María"})

        estado, respuesta, _ = self.solicitar("DELETE", f"/usuarios/{usuario_id}")
        self.assertEqual((estado, respuesta), (200, {"mensaje": "Usuario eliminado"}))

        estado, respuesta, _ = self.solicitar("GET", f"/usuarios/{usuario_id}")
        self.assertEqual((estado, respuesta), (404, {"error": "Usuario no encontrado"}))

    def test_post_valida_el_cuerpo(self):
        casos = (
            ({"nombre": "Ana"}, None, "Nombre y email son obligatorios"),
            ({"nombre": "  ", "email": "ana@example.com"}, None,
             "Nombre y email son obligatorios"),
            (None, "{json roto", "JSON inválido"),
            (None, "[]", "JSON inválido"),
        )
        for datos, cuerpo, mensaje in casos:
            with self.subTest(datos=datos, cuerpo=cuerpo):
                estado, respuesta, _ = self.solicitar(
                    "POST", "/usuarios", datos=datos, cuerpo=cuerpo
                )
                self.assertEqual((estado, respuesta), (400, {"error": mensaje}))

    def test_email_es_unico_sin_distinguir_mayusculas(self):
        self.crear_usuario(email=" Ana@Example.com ")
        estado, respuesta, _ = self.crear_usuario(
            nombre="Otra Ana", email="ana@example.COM"
        )
        self.assertEqual(
            (estado, respuesta),
            (409, {"error": "El email ya está registrado"}),
        )

    def test_put_parcial_valida_datos_y_evita_email_duplicado(self):
        _, ana, _ = self.crear_usuario(email="ana@example.com")
        _, luis, _ = self.crear_usuario(nombre="Luis", email="luis@example.com")

        estado, respuesta, _ = self.solicitar(
            "PUT", f"/usuarios/{luis['id']}", {"email": " ANA@EXAMPLE.COM "}
        )
        self.assertEqual((estado, respuesta), (409, {"error": "El email ya está registrado"}))

        estado, respuesta, _ = self.solicitar(
            "PUT", f"/usuarios/{ana['id']}", {"nombre": " "}
        )
        self.assertEqual(
            (estado, respuesta),
            (400, {"error": "Nombre y email no pueden estar vacíos"}),
        )

        _, sin_cambios, _ = self.solicitar("GET", f"/usuarios/{luis['id']}")
        self.assertEqual(sin_cambios, luis)

    def test_rutas_e_identificadores_inexistentes(self):
        for metodo, ruta, datos, mensaje in (
            ("GET", "/desconocida", None, "Ruta no encontrada"),
            ("POST", "/desconocida", {}, "Ruta no encontrada"),
            ("PUT", "/usuarios/no-numerico", {}, "Ruta no encontrada"),
            ("DELETE", "/usuarios/no-numerico", None, "Ruta no encontrada"),
            ("GET", "/usuarios/999999", None, "Usuario no encontrado"),
            ("DELETE", "/usuarios/999999", None, "Usuario no encontrado"),
        ):
            with self.subTest(metodo=metodo, ruta=ruta):
                estado, respuesta, _ = self.solicitar(metodo, ruta, datos)
                self.assertEqual((estado, respuesta), (404, {"error": mensaje}))


if __name__ == "__main__":
    unittest.main()
