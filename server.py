import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from usuarios_crud import CrudUsuarios


usuarios = []
proximo_id = 1


class ServidorUsuarios(BaseHTTPRequestHandler):
    def obtener_crud(self):
        return CrudUsuarios(
            usuarios,
            lambda: proximo_id,
            self.guardar_proximo_id,
        )

    @staticmethod
    def guardar_proximo_id(nuevo_id):
        global proximo_id
        proximo_id = nuevo_id

    def responder(self, estado, datos=None):
        cuerpo = json.dumps(
            {} if datos is None else datos,
            ensure_ascii=False,
        ).encode("utf-8")
        self.send_response(estado)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def leer_json(self):
        try:
            longitud = int(self.headers.get("Content-Length", 0))
            return json.loads(self.rfile.read(longitud))
        except (ValueError, json.JSONDecodeError):
            return None

    def obtener_id(self):
        partes = self.path.strip("/").split("/")
        if len(partes) == 2 and partes[0] == "usuarios":
            try:
                return int(partes[1])
            except ValueError:
                pass
        return None

    def buscar_usuario(self, usuario_id):
        return self.obtener_crud().buscar(usuario_id)

    def email_duplicado(self, email, usuario_id=None):
        return self.obtener_crud().email_duplicado(email, usuario_id)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/usuarios":
            q = parse_qs(url.query).get("q", [None])[0]
            self.responder(200, self.obtener_crud().listar(q))
            return

        usuario = self.buscar_usuario(self.obtener_id())
        if usuario:
            self.responder(200, usuario)
        else:
            self.responder(404, {"error": "Usuario no encontrado"})

    def do_POST(self):
        if self.path != "/usuarios":
            self.responder(404, {"error": "Ruta no encontrada"})
            return

        estado, respuesta = self.obtener_crud().crear(self.leer_json())
        self.responder(estado, respuesta)

    def do_PUT(self):
        datos = self.leer_json()
        estado, respuesta = self.obtener_crud().actualizar(self.obtener_id(), datos)
        self.responder(estado, respuesta)

    def do_DELETE(self):
        estado, respuesta = self.obtener_crud().eliminar(self.obtener_id())
        self.responder(estado, respuesta)


if __name__ == "__main__":
    servidor = HTTPServer(("localhost", 8000), ServidorUsuarios)
    print("Servidor disponible en http://localhost:8000")
    print("Presiona Ctrl+C para detenerlo")
    servidor.serve_forever()
