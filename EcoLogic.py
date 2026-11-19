import hashlib
import hmac
import os
import re
import time
import psycopg
from psycopg.rows import dict_row
from dataclasses import dataclass
from datetime import datetime

# COLE AQUI O SEU LINK DO NEON (entre as aspas)
DATABASE_URL = "postgresql://neondb_owner:npg_zhEus4iqD8vS@ep-morning-dream-b6bt283l-pooler.c-2.sa-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

ITENS_INICIAIS = [
    ("Garrafa PET", "Plástico", "Vermelha", 15, "Esvazie e amasse."),
    ("Lata de Alumínio", "Metal", "Amarela", 20, "Amasse para economizar espaço."),
    ("Papelão", "Papel", "Azul", 10, "Guarde seco e dobrado."),
    ("Garrafa de Vidro", "Vidro", "Verde", 12, "Nunca quebre antes de descartar."),
    ("Caixa Tetra Pak", "Plástico+Papel", "Vermelha", 18, "Lave e amasse antes."),
    ("Papel Jornal", "Papel", "Azul", 8, "Não deixe molhar."),
    ("Pilha / Bateria", "Resíduo perigoso", "Laranja", 30, "Leve a farmácias ou supermercados."),
]

LIXEIRAS = [
    ("Azul", "Papel e papelão", "\033[94m"),
    ("Vermelha", "Plástico", "\033[91m"),
    ("Verde", "Vidro", "\033[92m"),
    ("Amarela", "Metal", "\033[93m"),
    ("Marrom", "Orgânico", "\033[33m"),
    ("Cinza", "Rejeito (não recicla)", "\033[90m"),
    ("Laranja", "Resíduos perigosos", "\033[91m"),
]


# ───────────────────────── Cores e Estilo Visual ─────────────────────────
class UI:
    VERDE = "\033[92m"
    CIANO = "\033[96m"
    AMARELO = "\033[93m"
    VERMELHO = "\033[91m"
    NEGRITO = "\033[1m"
    CINZA = "\033[90m"
    RESET = "\033[0m"

    @staticmethod
    def limpar():
        os.system("cls" if os.name == "nt" else "clear")

    @classmethod
    def cabecalho(cls, titulo: str, subtitulo: str = ""):
        cls.limpar()
        largura = 54
        print(f"{cls.VERDE}╔{'═' * largura}╗{cls.RESET}")
        print(f"{cls.VERDE}║{cls.NEGRITO}{titulo.center(largura)}{cls.RESET}{cls.VERDE}║{cls.RESET}")
        if subtitulo:
            print(f"{cls.VERDE}║{cls.CIANO}{subtitulo.center(largura)}{cls.RESET}{cls.VERDE}║{cls.RESET}")
        print(f"{cls.VERDE}╚{'═' * largura}╝{cls.RESET}\n")

    @classmethod
    def sucesso(cls, msg: str):
        print(f"\n{cls.VERDE}✔ {msg}{cls.RESET}")
        time.sleep(1.5)

    @classmethod
    def erro(cls, msg: str):
        print(f"\n{cls.VERMELHO}✖ {msg}{cls.RESET}")
        time.sleep(1.8)

    @classmethod
    def pausar(cls):
        input(f"\n{cls.CINZA}Pressione [ENTER] para voltar ao menu...{cls.RESET}")


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


# ───────────────────────── Interface de Console Estilizada ─────────────────────────
class AppConsole:
    def __init__(self):
        UI.limpar()
        print(f"{UI.CIANO}⏳ Conectando ao banco de dados na nuvem...{UI.RESET}")
        self.banco = Banco()
        self.auth = AuthService(self.banco)
        self.servico = ReciclagemService(self.banco)
        self.usuario: Usuario | None = None

    def executar(self):
        while True:
            if self.usuario is None:
                if not self._menu_inicial():
                    break
            else:
                self._menu_principal()
        self.banco.fechar()
        UI.limpar()
        print(f"{UI.VERDE}Obrigado por ajudar o meio ambiente. Até logo!{UI.RESET}\n")

    def _menu_inicial(self) -> bool:
        UI.cabecalho("ECOCONECTA", "Plataforma de Reciclagem Digital")
        print(f"  {UI.VERDE}[1]{UI.RESET} Entrar na conta")
        print(f"  {UI.VERDE}[2]{UI.RESET} Criar nova conta")
        print(f"  {UI.VERMELHO}[0]{UI.RESET} Sair do sistema\n")
        
        op = input(f"{UI.NEGRITO}Escolha uma opção > {UI.RESET}").strip()
        if op == "1":
            self._tela_login()
        elif op == "2":
            self._tela_cadastro()
        elif op == "0":
            return False
        else:
            UI.erro("Opção inválida.")
        return True

    def _tela_login(self):
        UI.cabecalho("ACESSAR CONTA", "Informe suas credenciais")
        email = input("E-mail: ")
        senha = input("Senha:  ")
        try:
            self.usuario = self.auth.login(email, senha)
            UI.sucesso(f"Bem-vindo(a) de volta, {self.usuario.nome}!")
        except ValueError as e:
            UI.erro(str(e))

    def _tela_cadastro(self):
        UI.cabecalho("CRIAR NOVA CONTA", "Preencha seus dados")
        nome = input("Nome completo: ")
        email = input("E-mail:        ")
        senha = input("Senha (mín. 6): ")
        bairro = input("Seu Bairro:    ")
        try:
            self.usuario = self.auth.cadastrar(nome, email, senha, bairro)
            UI.sucesso("Conta criada com sucesso! Entrando...")
        except ValueError as e:
            UI.erro(str(e))

    def _menu_principal(self):
        u = self.usuario
        nivel = (u.pontos // 100) + 1
        status = f"{u.nome} | Bairro: {u.bairro} | Nível {nivel} ({u.pontos} pts)"
        UI.cabecalho("PAINEL PRINCIPAL", status)

        print(f"  {UI.VERDE}[1]{UI.RESET} Registrar item reciclado")
        print(f"  {UI.CIANO}[2]{UI.RESET} Meu histórico de descartes")
        print(f"  {UI.AMARELO}[3]{UI.RESET} Ranking de bairros")
        print(f"  {UI.VERDE}[4]{UI.RESET} Guia das lixeiras")
        print(f"  {UI.VERMELHO}[0]{UI.RESET} Sair da conta\n")

        op = input(f"{UI.NEGRITO}O que deseja fazer? > {UI.RESET}").strip()
        if op == "1":
            self._tela_registrar()
        elif op == "2":
            self._tela_historico()
        elif op == "3":
            self._tela_ranking()
        elif op == "4":
            self._tela_guia()
        elif op == "0":
            self.usuario = None
            UI.sucesso("Você saiu da conta.")
        else:
            UI.erro("Opção inválida.")

    def _tela_registrar(self):
        UI.cabecalho("REGISTRAR DESCARTE", "Selecione o material reciclado")
        itens = self.servico.listar_itens()
        
        print(f"{UI.CINZA}{'Nº':<4} {'MATERIAL':<20} {'CATEGORIA':<18} {'PONTOS'}{UI.RESET}")
        print("─" * 54)
        for n, it in enumerate(itens, 1):
            print(f"{UI.VERDE}[{n}]{UI.RESET}  {it.nome:<20} {it.tipo:<18} {UI.AMARELO}+{it.pontos} pts{UI.RESET}")
        print("─" * 54)

        try:
            escolha = int(input("\nNúmero do item (ou 0 para cancelar): "))
            if escolha == 0:
                return
            item = itens[escolha - 1]
            qtd = int(input(f"Quantidade de '{item.nome}': "))
            pontos = self.servico.registrar(self.usuario, item, qtd)
        except (ValueError, IndexError):
            UI.erro("Entrada inválida. Digite apenas números da lista.")
            return

        print(f"\n{UI.VERDE}✔ Descarte registrado! Você ganhou +{pontos} pontos.{UI.RESET}")
        print(f"{UI.CIANO}💡 Dica (Lixeira {item.lixeira}): {item.instrucao}{UI.RESET}")
        UI.pausar()

    def _tela_historico(self):
        UI.cabecalho("MEU HISTÓRICO", f"Últimos registros de {self.usuario.nome}")
        linhas = self.servico.historico(self.usuario)
        if not linhas:
            print(f"  {UI.CINZA}Você ainda não registrou nenhum descarte.{UI.RESET}")
        else:
            print(f"{UI.CINZA}{'DATA':<18} {'ITEM':<20} {'QTD':<6} {'PONTOS'}{UI.RESET}")
            print("─" * 54)
            for r in linhas:
                print(f"{r['data']:<18} {r['nome']:<20} {r['quantidade']}x     {UI.VERDE}+{r['pontos']} pts{UI.RESET}")
        UI.pausar()

    def _tela_ranking(self):
        UI.cabecalho("RANKING DE BAIRROS", "Comunidades mais sustentáveis")
        ranking = self.servico.ranking_bairros()
        if not ranking:
            print(f"  {UI.CINZA}Nenhum bairro pontuou ainda.{UI.RESET}")
        else:
            print(f"{UI.CINZA}{'POS':<5} {'BAIRRO':<22} {'MORADORES':<12} {'TOTAL'}{UI.RESET}")
            print("─" * 54)
            for pos, r in enumerate(ranking, 1):
                cor = UI.AMARELO if pos == 1 else UI.RESET
                medalha = "🏆" if pos == 1 else f"{pos}º"
                print(f"{cor}{medalha:<5} {r['bairro']:<22} {r['moradores']:<12} {r['total']} pts{UI.RESET}")
        UI.pausar()

    def _tela_guia(self):
        UI.cabecalho("GUIA DE COLETA SELETIVA", "Cores padrão das lixeiras")
        for cor, tipo, codigo_cor in LIXEIRAS:
            print(f"  {codigo_cor}■ Lixeira {cor:<10}{UI.RESET} ➔  {tipo}")
        UI.pausar()


if __name__ == "__main__":
    AppConsole().executar()