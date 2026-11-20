from dataclasses import dataclass


# ───────────────────────── Modelos ─────────────────────────
@dataclass
class Usuario:
    id: int
    nome: str
    email: str
    bairro: str
    pontos: int


@dataclass
class Item:
    id: int
    nome: str
    tipo: str
    lixeira: str
    pontos: int
    instrucao: str