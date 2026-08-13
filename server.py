import json
from http.server import BaseHTTPRequestHandler, HTTPServer


usuarios = []
proximo_id = 1


class ServidorUsuarios(BaseHTTPRequestHandler):
    def responder(self, estado, datos=None):
        cuerpo = json.dumps(datos or {}, ensure_ascii=False).encode("utf-8")
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
        partes = self.path.split("?", 1)[0].strip("/").split("/")
        if len(partes) == 2 and partes[0] == "usuarios":
            try:
                return int(partes[1])
            except ValueError:
                pass
        return None

    def buscar_usuario(self, usuario_id):
        return next((u for u in usuarios if u["id"] == usuario_id), None)

    def email_duplicado(self, email, usuario_id=None):
        email_normalizado = email.strip().lower()
        return any(
            u["email"].strip().lower() == email_normalizado
            and u["id"] != usuario_id
            for u in usuarios
        )

    def do_GET(self):
        if self.path == "/usuarios":
            self.responder(200, usuarios)
            return

        usuario_id = self.obtener_id()
        if usuario_id is None:
            self.responder(404, {"error": "Ruta no encontrada"})
            return

        usuario = self.buscar_usuario(usuario_id)
        if usuario:
            self.responder(200, usuario)
        else:
            self.responder(404, {"error": "Usuario no encontrado"})

    def do_POST(self):
        global proximo_id

        if self.path != "/usuarios":
            self.responder(404, {"error": "Ruta no encontrada"})
            return

        datos = self.leer_json()
        if not isinstance(datos, dict):
            self.responder(400, {"error": "JSON inválido"})
            return

        nombre = datos.get("nombre")
        email = datos.get("email")
        if (
            not isinstance(nombre, str)
            or not nombre.strip()
            or not isinstance(email, str)
            or not email.strip()
        ):
            self.responder(400, {"error": "Nombre y email son obligatorios"})
            return

        nombre = nombre.strip()
        email = email.strip()
        if self.email_duplicado(email):
            self.responder(409, {"error": "El email ya está registrado"})
            return

        usuario = {
            "id": proximo_id,
            "nombre": nombre,
            "email": email,
        }
        usuarios.append(usuario)
        proximo_id += 1
        self.responder(201, usuario)

    def do_PUT(self):
        usuario_id = self.obtener_id()
        if usuario_id is None:
            self.responder(404, {"error": "Ruta no encontrada"})
            return

        usuario = self.buscar_usuario(usuario_id)

        if not usuario:
            self.responder(404, {"error": "Usuario no encontrado"})
            return

        datos = self.leer_json()
        if not isinstance(datos, dict) or not datos:
            self.responder(400, {"error": "JSON inválido"})
            return

        nombre = datos.get("nombre", usuario["nombre"])
        email = datos.get("email", usuario["email"])
        if (
            not isinstance(nombre, str)
            or not nombre.strip()
            or not isinstance(email, str)
            or not email.strip()
        ):
            self.responder(400, {"error": "Nombre y email no pueden estar vacíos"})
            return

        nombre = nombre.strip()
        email = email.strip()
        if self.email_duplicado(email, usuario["id"]):
            self.responder(409, {"error": "El email ya está registrado"})
            return

        usuario["nombre"] = nombre
        usuario["email"] = email
        self.responder(200, usuario)

    def do_DELETE(self):
        usuario_id = self.obtener_id()
        if usuario_id is None:
            self.responder(404, {"error": "Ruta no encontrada"})
            return

        usuario = self.buscar_usuario(usuario_id)
        if not usuario:
            self.responder(404, {"error": "Usuario no encontrado"})
            return

        usuarios.remove(usuario)
        self.responder(200, {"mensaje": "Usuario eliminado"})


if __name__ == "__main__":
    servidor = HTTPServer(("localhost", 8000), ServidorUsuarios)
    print("Servidor disponible en http://localhost:8000")
    print("Presiona Ctrl+C para detenerlo")
    servidor.serve_forever()
