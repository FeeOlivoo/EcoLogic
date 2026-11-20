import os
import time
from config import LIXEIRAS
from database import Banco
from models import Usuario
from services import AuthService, ReciclagemService


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