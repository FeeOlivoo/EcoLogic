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