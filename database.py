import psycopg
from psycopg.rows import dict_row
from config import DATABASE_URL, ITENS_INICIAIS


# ───────────────────────── Banco (PostgreSQL na Nuvem) ─────────────────────────
class Banco:
    def __init__(self, url: str = DATABASE_URL):
        self.conn = psycopg.connect(url, row_factory=dict_row)
        self._criar_tabelas()
        self._popular_itens()

    def _criar_tabelas(self):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS usuarios (
                    id         SERIAL PRIMARY KEY,
                    nome       TEXT NOT NULL,
                    email      TEXT NOT NULL UNIQUE,
                    senha_hash TEXT NOT NULL,
                    salt       TEXT NOT NULL,
                    bairro     TEXT NOT NULL,
                    pontos     INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS itens (
                    id        SERIAL PRIMARY KEY,
                    nome      TEXT NOT NULL UNIQUE,
                    tipo      TEXT NOT NULL,
                    lixeira   TEXT NOT NULL,
                    pontos    INTEGER NOT NULL,
                    instrucao TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS registros (
                    id         SERIAL PRIMARY KEY,
                    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
                    item_id    INTEGER NOT NULL REFERENCES itens(id),
                    quantidade INTEGER NOT NULL,
                    pontos     INTEGER NOT NULL,
                    data       TEXT NOT NULL
                );
                """
            )
        self.conn.commit()

    def _popular_itens(self):
        with self.conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO itens (nome, tipo, lixeira, pontos, instrucao) "
                "VALUES (%s, %s, %s, %s, %s) ON CONFLICT (nome) DO NOTHING",
                ITENS_INICIAIS,
            )
        self.conn.commit()

    def fechar(self):
        self.conn.close()