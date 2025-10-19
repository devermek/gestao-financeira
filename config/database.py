import sqlite3
import os
import pandas as pd
import psycopg2 # Garante que o psycopg2 está importado se necessário para fallback

def get_db_connection():
    """Conecta ao banco de dados (SQLite local ou PostgreSQL no Render)"""
    database_url = os.getenv('DATABASE_URL')

    if database_url:
        print(f"DEBUG DB: DATABASE_URL encontrada no ambiente. Tentando conectar ao PostgreSQL.")
        try:
            # Certifica-se que psycopg2 está disponível e importado localmente na função para melhor controle
            import psycopg2
            from psycopg2.extras import RealDictCursor
            print(f"DEBUG DB: Conectando ao PostgreSQL usando DATABASE_URL fornecida...")

            # Adicionar configurações SSL para Supabase/Neon
            if 'supabase.co' in database_url or 'neon.tech' in database_url:
                conn = psycopg2.connect(database_url + "?sslmode=require", cursor_factory=RealDictCursor)
            else:
                conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)

            print("DEBUG DB: ✅ Conectado ao PostgreSQL com sucesso!")
            return conn
        except Exception as e:
            print(f"DEBUG DB: ❌ Erro PostgreSQL ao conectar: {e}")
            print("DEBUG DB: 🔄 Fallback para SQLite após falha na conexão PostgreSQL...")
            # Fallback para SQLite se PostgreSQL falhar
            return get_sqlite_connection()
    else:
        print("DEBUG DB: DATABASE_URL NÃO encontrada no ambiente. Conectando ao SQLite local...")
        # Ambiente local (SQLite)
        return get_sqlite_connection()

def get_sqlite_connection():
    """Conexão SQLite"""
    print("DEBUG DB: 🔗 Conectando ao SQLite local (função dedicada).")
    db_path = "obra_database.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa o banco de dados com todas as tabelas (CREATE TABLE IF NOT EXISTS)"""
    database_url = os.getenv('DATABASE_URL')

    if database_url:
        print(f"DEBUG DB: Iniciando init_db com DATABASE_URL. Tentando inicializar esquema PostgreSQL.")
        try:
            init_postgresql()
        except Exception as e:
            print(f"DEBUG DB: ❌ Erro ao inicializar PostgreSQL em init_db: {e}")
            print("DEBUG DB: 🔄 Inicializando SQLite como fallback em init_db...")
            init_sqlite()
    else:
        print("DEBUG DB: Iniciando init_db SEM DATABASE_URL. Inicializando esquema SQLite.")
        init_sqlite()

def init_postgresql():
    """Inicializa esquema PostgreSQL (cria tabelas se não existirem)"""
    print("DEBUG DB: 🐘 Inicializando esquema PostgreSQL...")
    conn = get_db_connection() # Obtém a conexão que *deveria* ser PostgreSQL
    cursor = conn.cursor()

    # Adicionar todas as tabelas com CREATE TABLE IF NOT EXISTS
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
    print("DEBUG DB: ✅ Esquema PostgreSQL inicializado com sucesso (ou já existia)!")

def init_sqlite():
    """Inicializa esquema SQLite (cria tabelas se não existirem)"""
    print("DEBUG DB: 📁 Inicializando esquema SQLite...")
    conn = get_sqlite_connection()
    cursor = conn.cursor()

    # Adicionar todas as tabelas com CREATE TABLE IF NOT EXISTS
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
    print("DEBUG DB: ✅ Esquema SQLite inicializado com sucesso (ou já existia)!")

def get_current_db_type():
    """Retorna o tipo de banco de dados atualmente conectado ('postgresql' ou 'sqlite')"""
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return 'postgresql'
    else:
        return 'sqlite'

if __name__ == "__main__":
    init_db()