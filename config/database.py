import os
import sys
import psycopg2
import psycopg2.extras
import sqlite3
from datetime import datetime

def get_connection():
    """Conecta ao banco de dados (PostgreSQL no Neon ou SQLite local)"""
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # PostgreSQL (Neon)
        try:
            conn = psycopg2.connect(
                database_url,
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            return conn
        except Exception as e:
            print(f"Erro ao conectar PostgreSQL: {repr(e)}", file=sys.stderr)
            raise
    else:
        # SQLite (local)
        try:
            conn = sqlite3.connect('obra_financeira.db')
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            print(f"Erro ao conectar SQLite: {repr(e)}", file=sys.stderr)
            raise

def init_db():
    """Inicializa o banco de dados com todas as tabelas"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Detecta tipo de banco
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        # Para desenvolvimento: limpa banco se necessário
        if not is_postgres:
            # SQLite - remove arquivo se existir
            if os.path.exists('obra_financeira.db'):
                conn.close()
                os.remove('obra_financeira.db')
                conn = get_connection()
                cursor = conn.cursor()
        
        # Cria tabelas
        if is_postgres:
            # PostgreSQL
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    senha VARCHAR(255) NOT NULL,
                    ativo BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS obras (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(200) NOT NULL,
                    orcamento DECIMAL(15,2) DEFAULT 0,
                    data_inicio DATE,
                    data_fim_prevista DATE,
                    ativo BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categorias (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(100) NOT NULL,
                    descricao TEXT,
                    cor VARCHAR(7) DEFAULT '#3498db',
                    ativo BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lancamentos (
                    id SERIAL PRIMARY KEY,
                    obra_id INTEGER REFERENCES obras(id),
                    categoria_id INTEGER REFERENCES categorias(id),
                    descricao TEXT NOT NULL,
                    valor DECIMAL(15,2) NOT NULL,
                    data_lancamento DATE NOT NULL,
                    observacoes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS arquivos (
                    id SERIAL PRIMARY KEY,
                    lancamento_id INTEGER REFERENCES lancamentos(id) ON DELETE CASCADE,
                    nome_arquivo VARCHAR(255) NOT NULL,
                    tipo_arquivo VARCHAR(50),
                    tamanho_arquivo INTEGER,
                    conteudo_arquivo BYTEA,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Triggers para updated_at
            cursor.execute("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            """)
            
            tables = ['usuarios', 'obras', 'categorias', 'lancamentos']
            for table in tables:
                cursor.execute(f"""
                    DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};
                    CREATE TRIGGER update_{table}_updated_at
                        BEFORE UPDATE ON {table}
                        FOR EACH ROW
                        EXECUTE FUNCTION update_updated_at_column();
                """)
        
        else:
            # SQLite
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    senha TEXT NOT NULL,
                    ativo BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS obras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    orcamento REAL DEFAULT 0,
                    data_inicio DATE,
                    data_fim_prevista DATE,
                    ativo BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    descricao TEXT,
                    cor TEXT DEFAULT '#3498db',
                    ativo BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lancamentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    obra_id INTEGER REFERENCES obras(id),
                    categoria_id INTEGER REFERENCES categorias(id),
                    descricao TEXT NOT NULL,
                    valor REAL NOT NULL,
                    data_lancamento DATE NOT NULL,
                    observacoes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS arquivos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lancamento_id INTEGER REFERENCES lancamentos(id) ON DELETE CASCADE,
                    nome_arquivo TEXT NOT NULL,
                    tipo_arquivo TEXT,
                    tamanho_arquivo INTEGER,
                    conteudo_arquivo BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
        conn.commit()
        print("Banco de dados inicializado com sucesso!", file=sys.stderr)
        
    except Exception as e:
        conn.rollback()
        print(f"Erro ao inicializar banco: {repr(e)}", file=sys.stderr)
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    init_db()