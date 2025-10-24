import sqlite3
import os
import pandas as pd
import sys

# Necessário para lidar com tipos de retorno de banco de dados em auth.py
try:
    import psycopg2.extras
    RealDictRow = psycopg2.extras.RealDictRow 
except ImportError:
    RealDictRow = type(None) # Tipo dummy caso psycopg2 não esteja instalado

def get_db_connection():
    """
    Conecta ao banco de dados (SQLite local ou PostgreSQL no Render).
    Retorna uma tupla: (objeto de conexão, string do tipo de banco de dados).
    """
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # Ambiente de produção (PostgreSQL)
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            print(f"🔗 Tentando conectar ao PostgreSQL...", file=sys.stderr); sys.stderr.flush()
            
            dsn_to_connect = database_url
            if 'supabase.co' in database_url or 'neon.tech' in database_url:
                if '?' in database_url:
                    dsn_to_connect = database_url + "&sslmode=require"
                else:
                    dsn_to_connect = database_url + "?sslmode=require"

            conn = psycopg2.connect(dsn_to_connect, cursor_factory=RealDictCursor)
            print("✅ Conectado ao PostgreSQL!", file=sys.stderr); sys.stderr.flush()
            return conn, 'postgresql'
        except Exception as e:
            print(f"❌ Erro PostgreSQL: {e}", file=sys.stderr); sys.stderr.flush()
            print("🔄 Fallback para SQLite...", file=sys.stderr); sys.stderr.flush()
            # Fallback para SQLite se PostgreSQL falhar
            conn = get_sqlite_connection()
            return conn, 'sqlite'
    else:
        # Ambiente local (SQLite)
        conn = get_sqlite_connection()
        return conn, 'sqlite'

def get_sqlite_connection():
    """Conexão SQLite"""
    print("🔗 Conectando ao SQLite local...", file=sys.stderr); sys.stderr.flush()
    db_path = "obra_database.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row # Permite acessar colunas por nome
    return conn

def init_db():
    """Inicializa o banco de dados com todas as tabelas"""
    conn, db_type = get_db_connection() # Obtém a conexão e o tipo de DB real
    conn.close() # Fecha a conexão, pois init_postgresql/sqlite abrirão a sua própria.

    if db_type == 'postgresql':
        try:
            init_postgresql()
        except Exception as e:
            print(f"❌ Erro ao inicializar PostgreSQL: {e}", file=sys.stderr); sys.stderr.flush()
            print("🔄 Inicializando SQLite como fallback...", file=sys.stderr); sys.stderr.flush()
            init_sqlite()
    else:
        init_sqlite()

def init_postgresql():
    """Inicializa banco PostgreSQL"""
    print("🐘 Inicializando PostgreSQL...", file=sys.stderr); sys.stderr.flush()
    conn, _ = get_db_connection()
    cursor = conn.cursor()
    
    def create_update_timestamp_trigger(cursor, table_name, trigger_name_suffix):
        trigger_name = f"update_{table_name}_{trigger_name_suffix}"
        try:
            cursor.execute(f"""
                DROP TRIGGER IF EXISTS {trigger_name} ON {table_name};
            """)
            cursor.execute(f"""
                CREATE TRIGGER {trigger_name}
                BEFORE UPDATE ON {table_name}
                FOR EACH ROW
                EXECUTE FUNCTION update_timestamp();
            """)
        except Exception as e:
            print(f"❌ Erro ao criar trigger '{trigger_name}' para a tabela '{table_name}': {e}", file=sys.stderr); sys.stderr.flush()

    try:
        cursor.execute("""
            CREATE OR REPLACE FUNCTION update_timestamp()
            RETURNS TRIGGER AS $$
            BEGIN
               NEW.updated_at = NOW();
               RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
    except Exception as e:
        print(f"❌ Erro ao criar função 'update_timestamp()': {e}", file=sys.stderr); sys.stderr.flush()

    # Tabela de usuários (tipo 'gestor' apenas)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            senha VARCHAR(255) NOT NULL,
            tipo VARCHAR(50) NOT NULL CHECK (tipo IN ('gestor')), -- Apenas 'gestor'
            ativo BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    create_update_timestamp_trigger(cursor, 'usuarios', 'updated_at')
    
    # Tabela de categorias
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            descricao TEXT,
            orcamento_previsto DECIMAL(15,2) DEFAULT 0,
            ativo BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    create_update_timestamp_trigger(cursor, 'categorias', 'updated_at')

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
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (categoria_id) REFERENCES categorias (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)
    create_update_timestamp_trigger(cursor, 'lancamentos', 'updated_at')
    
    # Tabela de arquivos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS arquivos (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            tipo VARCHAR(100) NOT NULL,
            tamanho INTEGER,
            conteudo BYTEA,
            lancamento_id INTEGER,
            usuario_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lancamento_id) REFERENCES lancamentos (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)
    create_update_timestamp_trigger(cursor, 'arquivos', 'updated_at')
    
    # Tabela de configurações da obra
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS obra_config (
            id SERIAL PRIMARY KEY,
            nome_obra VARCHAR(255),
            orcamento_total DECIMAL(15,2),
            data_inicio DATE,
            data_previsao_fim DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    create_update_timestamp_trigger(cursor, 'obra_config', 'updated_at')

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ PostgreSQL inicializado com sucesso!", file=sys.stderr); sys.stderr.flush()

def init_sqlite():
    """Inicializa banco SQLite"""
    print("✨ Inicializando SQLite...", file=sys.stderr); sys.stderr.flush()
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    # Tabela de usuários (tipo 'gestor' apenas)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK (tipo IN ('gestor')), -- Apenas 'gestor'
            ativo INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela de categorias
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            orcamento_previsto DECIMAL(15,2) DEFAULT 0,
            ativo INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela de lançamentos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lancamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data DATE NOT NULL,
            categoria_id INTEGER NOT NULL,
            descricao TEXT NOT NULL,
            valor DECIMAL(15,2) NOT NULL,
            observacoes TEXT,
            usuario_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (categoria_id) REFERENCES categorias (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)
    
    # Tabela de arquivos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS arquivos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL,
            tamanho INTEGER,
            conteudo BLOB,
            lancamento_id INTEGER,
            usuario_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lancamento_id) REFERENCES lancamentos (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)
    
    # Tabela de configurações da obra
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS obra_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_obra TEXT,
            orcamento_total DECIMAL(15,2),
            data_inicio DATE,
            data_previsao_fim DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ SQLite inicializado com sucesso!", file=sys.stderr); sys.stderr.flush()

if __name__ == "__main__":
    init_db()
