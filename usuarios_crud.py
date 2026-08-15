"""Reglas de negocio y persistencia en memoria para el CRUD de usuarios."""

import re


PATRON_EMAIL = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


class CrudUsuarios:
    """Gestiona usuarios sin depender de detalles del servidor HTTP."""

    def __init__(self, usuarios, obtener_proximo_id, guardar_proximo_id):
        self.usuarios = usuarios
        self._obtener_proximo_id = obtener_proximo_id
        self._guardar_proximo_id = guardar_proximo_id

    def listar(self, q=None):
        if q is None:
            return self.usuarios

        consulta = q.lower()
        return [
            usuario
            for usuario in self.usuarios
            if consulta in usuario["nombre"].lower()
        ]

    def buscar(self, usuario_id):
        return next(
            (usuario for usuario in self.usuarios if usuario["id"] == usuario_id),
            None,
        )

    def email_duplicado(self, email, usuario_id=None):
        email_normalizado = email.strip().lower()
        return any(
            usuario["email"].strip().lower() == email_normalizado
            and usuario["id"] != usuario_id
            for usuario in self.usuarios
        )

    @staticmethod
    def email_valido(email):
        return isinstance(email, str) and PATRON_EMAIL.fullmatch(email) is not None

    def crear(self, datos):
        if not datos or not datos.get("nombre") or not datos.get("email"):
            return 400, {"error": "Nombre y email son obligatorios"}

        email = datos["email"]
        if not isinstance(email, str):
            return 400, {"error": "Formato de email inválido"}

        email = email.strip()
        if not self.email_valido(email):
            return 400, {"error": "Formato de email inválido"}
        if self.email_duplicado(email):
            return 409, {"error": "El email ya está registrado"}

        proximo_id = self._obtener_proximo_id()
        usuario = {
            "id": proximo_id,
            "nombre": datos["nombre"],
            "email": email,
        }
        self.usuarios.append(usuario)
        self._guardar_proximo_id(proximo_id + 1)
        return 201, usuario

    def actualizar(self, usuario_id, datos):
        usuario = self.buscar(usuario_id)
        if not usuario:
            return 404, {"error": "Usuario no encontrado"}
        if not datos:
            return 400, {"error": "JSON inválido"}

        email = datos.get("email", usuario["email"])
        if not isinstance(email, str):
            return 400, {"error": "Formato de email inválido"}

        email = email.strip()
        if not self.email_valido(email):
            return 400, {"error": "Formato de email inválido"}
        if self.email_duplicado(email, usuario["id"]):
            return 409, {"error": "El email ya está registrado"}

        usuario["nombre"] = datos.get("nombre", usuario["nombre"])
        usuario["email"] = email
        return 200, usuario

    def eliminar(self, usuario_id):
        usuario = self.buscar(usuario_id)
        if not usuario:
            return 404, {"error": "Usuario no encontrado"}

        self.usuarios.remove(usuario)
        return 200, {"mensaje": "Usuario eliminado"}
