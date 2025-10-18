import sqlite3
import os

def get_db_connection():
    """Conecta ao banco de dados SQLite"""
    db_path = "obra_database.db"
    conn = sqlite3.connect(db_path)
    return conn

def init_db():
    """Inicializa o banco de dados com todas as tabelas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabela de usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK (tipo IN ('gestor', 'investidor')),
            ativo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela de categorias
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            descricao TEXT,
            orcamento_previsto REAL DEFAULT 0,
            ativo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela de lançamentos - VERIFICAR ESTRUTURA
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lancamentos (
            id INTEGER PRIMARY KEY,
            data DATE NOT NULL,
            categoria_id INTEGER NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            observacoes TEXT,
            usuario_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (categoria_id) REFERENCES categorias (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)
    
    # Tabela de arquivos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS arquivos (
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL,
            tamanho INTEGER,
            conteudo BLOB,
            lancamento_id INTEGER NOT NULL,
            usuario_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lancamento_id) REFERENCES lancamentos (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)
    
    # Tabela de configurações da obra
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS obra_config (
            id INTEGER PRIMARY KEY,
            nome_obra TEXT,
            orcamento_total REAL,
            data_inicio DATE,
            data_previsao_fim DATE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados inicializado com sucesso!")

def recriar_banco():
    """Recria o banco do zero (CUIDADO: apaga todos os dados!)"""
    db_path = "obra_database.db"
    
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️ Banco antigo removido")
    
    init_db()
    print("🆕 Novo banco criado!")

if __name__ == "__main__":
    # Para recriar o banco, descomente a linha abaixo:
    # recriar_banco()
    init_db()