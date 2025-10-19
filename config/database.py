import sqlite3
import os
import pandas as pd

def get_db_connection():
    """Conecta ao banco de dados (SQLite local ou PostgreSQL no Render)"""
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # Ambiente de produção (PostgreSQL)
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            print(f"🔗 Tentando conectar ao PostgreSQL...")
            
            # Adicionar configurações SSL para Supabase/Neon
            if 'supabase.co' in database_url or 'neon.tech' in database_url:
                conn = psycopg2.connect(database_url + "?sslmode=require", cursor_factory=RealDictCursor)
            else:
                conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
            
            print("✅ Conectado ao PostgreSQL!")
            return conn, 'postgresql' # Retorna a conexão e o tipo
        except Exception as e:
            print(f"❌ Erro PostgreSQL ao conectar: {e}")
            print("🔄 Fallback para SQLite...")
            # Fallback para SQLite se PostgreSQL falhar
            return get_sqlite_connection() # Retorna a tupla (conn, 'sqlite')
    else:
        # Ambiente local (SQLite)
        return get_sqlite_connection() # Retorna a tupla (conn, 'sqlite')

def get_sqlite_connection():
    """Conexão SQLite"""
    print("🔗 Conectando ao SQLite local...")
    db_path = "obra_database.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn, 'sqlite' # Retorna a conexão e o tipo

def init_db():
    """Inicializa o banco de dados com todas as tabelas"""
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        try:
            # PostgreSQL (Render/Supabase/Neon)
            init_postgresql()
        except Exception as e:
            print(f"❌ Erro ao inicializar PostgreSQL: {e}")
            print("🔄 Inicializando SQLite como fallback...")
            init_sqlite()
    else:
        # SQLite (Local)
        init_sqlite()

def init_postgresql():
    """Inicializa banco PostgreSQL"""
    print("🐘 Inicializando PostgreSQL...")
    conn, _ = get_db_connection() # Desempacota a tupla, ignorando o db_type para este uso
    cursor = conn.cursor()
    
    # Tabela de usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            senha VARCHAR(255) NOT NULL,
            tipo VARCHAR(50) NOT NULL CHECK (tipo IN ('gestor', 'investidor')),
            ativo INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela de categorias
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            descricao TEXT,
            orcamento_previsto DECIMAL(15,2) DEFAULT 0,
            ativo INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela de lançamentos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lancamentos (
            id SERIAL PRIMARY KEY,
            data DATE NOT NULL,
            categoria_id INTEGER NOT NULL,
            descricao TEXT NOT NULL,
            valor DECIMAL(15,2) NOT NULL,
            observacoes TEXT,
            usuario_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (categoria_id) REFERENCES categorias (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)
    
    # Tabela de arquivos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS arquivos (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            tipo VARCHAR(100) NOT NULL,
            tamanho INTEGER,
            conteudo BYTEA,
            lancamento_id INTEGER NOT NULL,
            usuario_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lancamento_id) REFERENCES lancamentos (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)
    
    # Tabela de configurações da obra
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS obra_config (
            id SERIAL PRIMARY KEY,
            nome_obra VARCHAR(255),
            orcamento_total DECIMAL(15,2),
            data_inicio DATE,
            data_previsao_fim DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ PostgreSQL inicializado com sucesso!")

def init_sqlite():
    """Inicializa banco SQLite (código original)"""
    print("�� Inicializando SQLite...")
    conn, _ = get_sqlite_connection() # Desempacota a tupla, ignorando o db_type para este uso
    cursor = conn.cursor()
    
    # Código SQLite original (assumindo que estas são as definições padrão)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK (tipo IN ('gestor', 'investidor')),
            ativo INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            orcamento_previsto REAL DEFAULT 0,
            ativo INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lancamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data DATE NOT NULL,
            categoria_id INTEGER NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            observacoes TEXT,
            usuario_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (categoria_id) REFERENCES categorias (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS arquivos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL,
            tamanho INTEGER,
            conteudo BLOB,
            lancamento_id INTEGER NOT NULL,
            usuario_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lancamento_id) REFERENCES lancamentos (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS obra_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_obra TEXT,
            orcamento_total REAL,
            data_inicio DATE,
            data_previsao_fim DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("✅ SQLite inicializado com sucesso!")

if __name__ == "__main__":
    init_db()
