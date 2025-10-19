import sqlite3
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd

def get_db_connection():
    """Conecta ao banco de dados (SQLite local ou PostgreSQL no Render)"""
    # Verifica se existe a variável de ambiente DATABASE_URL (Render/Supabase)
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # Ambiente de produção (Render + Supabase/PostgreSQL)
        print("🔗 Conectando ao PostgreSQL (Supabase)...")
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        return conn
    else:
        # Ambiente local (SQLite)
        print("🔗 Conectando ao SQLite local...")
        db_path = "obra_database.db"
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Para retornar dicts
        return conn

def init_db():
    """Inicializa o banco de dados com todas as tabelas"""
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # PostgreSQL (Render/Supabase)
        init_postgresql()
    else:
        # SQLite (Local)
        init_sqlite()

def init_postgresql():
    """Inicializa banco PostgreSQL"""
    print("🐘 Inicializando PostgreSQL...")
    conn = get_db_connection()
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
    print("📁 Inicializando SQLite...")
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
    
    # Tabela de lançamentos
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
    print("✅ SQLite inicializado com sucesso!")

def recriar_banco():
    """Recria o banco do zero (CUIDADO: apaga todos os dados!)"""
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        print("⚠️ Não é possível recriar banco PostgreSQL automaticamente")
        print("Use o painel do Supabase para gerenciar o banco")
    else:
        db_path = "obra_database.db"
        if os.path.exists(db_path):
            os.remove(db_path)
            print("🗑️ Banco SQLite antigo removido")
        init_db()
        print("🆕 Novo banco SQLite criado!")

if __name__ == "__main__":
    init_db()