import hashlib
import hmac
import os
import re
import psycopg
from datetime import datetime
from database import Banco
from models import Usuario, Item


# ───────────────────────── Autenticação ─────────────────────────
class AuthService:
    def __init__(self, banco: Banco):
        self.db = banco.conn

    @staticmethod
    def _hash(senha: str, salt: str) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256", senha.encode(), bytes.fromhex(salt), 100_000
        ).hex()

    def cadastrar(self, nome: str, email: str, senha: str, bairro: str) -> Usuario:
        email = email.strip().lower()
        if not nome.strip() or not bairro.strip():
            raise ValueError("Nome e bairro são obrigatórios.")
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValueError("Formato de e-mail inválido.")
        if len(senha) < 6:
            raise ValueError("A senha deve ter pelo menos 6 caracteres.")

        salt = os.urandom(16).hex()
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    "INSERT INTO usuarios (nome, email, senha_hash, salt, bairro) "
                    "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                    (nome.strip(), email, self._hash(senha, salt), salt, bairro.strip()),
                )
                novo_id = cur.fetchone()["id"]
            self.db.commit()
        except psycopg.errors.UniqueViolation:
            self.db.rollback()
            raise ValueError("Já existe uma conta cadastrada com esse e-mail.")
        return Usuario(novo_id, nome.strip(), email, bairro.strip(), 0)

    def login(self, email: str, senha: str) -> Usuario:
        with self.db.cursor() as cur:
            cur.execute(
                "SELECT * FROM usuarios WHERE email = %s", (email.strip().lower(),)
            )
            row = cur.fetchone()
        if row is None or not hmac.compare_digest(
            row["senha_hash"], self._hash(senha, row["salt"])
        ):
            raise ValueError("E-mail ou senha incorretos.")
        return Usuario(row["id"], row["nome"], row["email"], row["bairro"], row["pontos"])


# ───────────────────────── Reciclagem (Regras de Negócio) ─────────────────────────
class ReciclagemService:
    def __init__(self, banco: Banco):
        self.db = banco.conn

    def listar_itens(self) -> list[Item]:
        with self.db.cursor() as cur:
            cur.execute("SELECT * FROM itens ORDER BY id")
            rows = cur.fetchall()
        return [Item(**r) for r in rows]

    def registrar(self, usuario: Usuario, item: Item, quantidade: int) -> int:
        if quantidade < 1:
            raise ValueError("A quantidade deve ser pelo menos 1.")
        pontos = item.pontos * quantidade
        with self.db.cursor() as cur:
            cur.execute(
                "INSERT INTO registros (usuario_id, item_id, quantidade, pontos, data) "
                "VALUES (%s, %s, %s, %s, %s)",
                (usuario.id, item.id, quantidade, pontos,
                 datetime.now().strftime("%d/%m/%Y %H:%M")),
            )
            cur.execute(
                "UPDATE usuarios SET pontos = pontos + %s WHERE id = %s", (pontos, usuario.id)
            )
        self.db.commit()
        usuario.pontos += pontos
        return pontos

    def historico(self, usuario: Usuario, limite: int = 10):
        with self.db.cursor() as cur:
            cur.execute(
                "SELECT i.nome, r.quantidade, r.pontos, r.data FROM registros r "
                "JOIN itens i ON i.id = r.item_id WHERE r.usuario_id = %s "
                "ORDER BY r.id DESC LIMIT %s",
                (usuario.id, limite),
            )
            return cur.fetchall()

    def ranking_bairros(self):
        with self.db.cursor() as cur:
            cur.execute(
                "SELECT bairro, SUM(pontos) AS total, COUNT(*) AS moradores "
                "FROM usuarios GROUP BY bairro ORDER BY total DESC"
            )
            return cur.fetchall()