import sqlite3
import os
import sys # CRITICAL FOR PRINTING TO STDERR

# Necessary for handling database return types in auth.py
try:
    import psycopg2.extras
    RealDictRow = psycopg2.extras.RealDictRow 
except ImportError:
    RealDictRow = type(None) # Dummy type if psycopg2 is not installed

def get_db_connection():
    """
    Connects to the database (local SQLite or PostgreSQL on Render).
    Returns a tuple: (connection object, database type string).
    Raises an exception if connection fails.
    """
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            print(f"🔗 Attempting to connect to PostgreSQL...", file=sys.stderr); sys.stderr.flush()
            
            dsn_to_connect = database_url
            if 'supabase.co' in database_url or 'neon.tech' in database_url:
                if '?' in database_url:
                    dsn_to_connect = database_url + "&sslmode=require"
                else:
                    dsn_to_connect = database_url + "?sslmode=require"

            conn = psycopg2.connect(dsn_to_connect, cursor_factory=RealDictCursor)
            print("✅ Connected to PostgreSQL!", file=sys.stderr); sys.stderr.flush()
            return conn, 'postgresql'
        except Exception as e:
            # DO NOT FALLBACK HERE. Raise the error for init_db to handle.
            print(f"❌ PostgreSQL Connection Error: {repr(e)}", file=sys.stderr); sys.stderr.flush()
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}") from e
    else:
        # Local environment (SQLite)
        print("🔗 Connecting to local SQLite...", file=sys.stderr); sys.stderr.flush()
        db_path = "obra_database.db"
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row # Allows accessing columns by name (dict-like)
        return conn, 'sqlite'

def init_db():
    """Initializes the database with all tables"""
    print("🔄 Initializing database...", file=sys.stderr); sys.stderr.flush()
    db_type = 'sqlite' # Default to sqlite, will try postgresql first
    try:
        # Attempt to connect to determine DB type first. Connection is short-lived.
        conn, connected_db_type = get_db_connection()
        conn.close() 
        db_type = connected_db_type # If connected, use that type
        print(f"Detected DB type: {db_type}", file=sys.stderr); sys.stderr.flush()
    except ConnectionError as ce:
        print(f"⚠️ Initial DB connection failed (PostgreSQL): {repr(ce)}. Falling back to SQLite.", file=sys.stderr); sys.stderr.flush()
        # db_type remains 'sqlite'
    except Exception as e: # Catch any other unexpected errors during initial connection
        print(f"⚠️ Unexpected error during initial DB connection: {repr(e)}. Falling back to SQLite.", file=sys.stderr); sys.stderr.flush()
        # db_type remains 'sqlite'


    if db_type == 'postgresql':
        try:
            print("Attempting to initialize PostgreSQL...", file=sys.stderr); sys.stderr.flush()
            init_postgresql()
            print("PostgreSQL initialization completed.", file=sys.stderr); sys.stderr.flush()
        except Exception as e:
            print(f"❌ Error initializing PostgreSQL: {repr(e)}", file=sys.stderr); sys.stderr.flush()
            print("🔄 Initializing SQLite as fallback...", file=sys.stderr); sys.stderr.flush()
            init_sqlite() # Fallback to SQLite if PostgreSQL init fails
    else:
        print("Attempting to initialize SQLite...", file=sys.stderr); sys.stderr.flush()
        init_sqlite()
        print("SQLite initialization completed.", file=sys.stderr); sys.stderr.flush()


def init_postgresql():
    """Initializes PostgreSQL database"""
    print("🐘 Initializing PostgreSQL...", file=sys.stderr); sys.stderr.flush()
    conn, _ = get_db_connection()
    cursor = conn.cursor()
    
    # DROP TABLES FIRST - IMPORTANT FOR CLEAN RE-INITIALIZATION
    # This is dangerous for production but necessary for dev with persistent issues
    # BE CAREFUL WITH THIS IN PRODUCTION!
    print("Dropping existing tables for clean re-initialization...", file=sys.stderr); sys.stderr.flush()
    cursor.execute("DROP TABLE IF EXISTS arquivos CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS lancamentos CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS categorias CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS usuarios CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS obra_config CASCADE;")
    cursor.execute("DROP FUNCTION IF EXISTS update_timestamp();")
    conn.commit()
    print("Existing tables dropped.", file=sys.stderr); sys.stderr.flush()


    # Helper to create triggers to simplify and avoid "near OR" error
    def create_update_timestamp_trigger(cursor, table_name, trigger_name_suffix):
        trigger_name = f"update_{table_name}_{trigger_name_suffix}"
        try:
            # DROP TRIGGER IF EXISTS already handled by table drop, but keeping just in case
            cursor.execute(f"""
                CREATE TRIGGER {trigger_name}
                BEFORE UPDATE ON {table_name}
                FOR EACH ROW
                EXECUTE FUNCTION update_timestamp();
            """)
        except Exception as e:
            print(f"❌ Error creating trigger '{trigger_name}' for table '{table_name}': {repr(e)}", file=sys.stderr); sys.stderr.flush()

    # Create trigger function (always the first)
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
        conn.commit() # Commit function creation
    except Exception as e:
        print(f"❌ Error creating function 'update_timestamp()': {repr(e)}", file=sys.stderr); sys.stderr.flush()

    # Users table ('active' as BOOLEAN and 'updated_at')
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            senha VARCHAR(255) NOT NULL,
            tipo VARCHAR(50) NOT NULL CHECK (tipo IN ('gestor')),
            ativo BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    create_update_timestamp_trigger(cursor, 'usuarios', 'updated_at')
    
    # Categories table
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

    # Entries table
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
    
    # Files table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS arquivos (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            tipo VARCHAR(100) NOT NULL,
            tamanho INTEGER,
            conteudo BYTEA,
            lancamento_id INTEGER, # Can be NULL if file is not associated with an entry
            usuario_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lancamento_id) REFERENCES lancamentos (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)
    create_update_timestamp_trigger(cursor, 'arquivos', 'updated_at')
    
    # Project config table
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
    print("✅ PostgreSQL initialized successfully!", file=sys.stderr); sys.stderr.flush()

def init_sqlite():
    """Initializes SQLite database"""
    print("✨ Initializing SQLite...", file=sys.stderr); sys.stderr.flush()
    db_path = "obra_database.db"
    # Delete existing SQLite DB file to force a clean start
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Deleted existing SQLite DB: {db_path}", file=sys.stderr); sys.stderr.flush()

    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    # Users table ('active' as INTEGER and 'updated_at')
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK (tipo IN ('gestor')),
            ativo INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Categories table
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
    
    # Entries table
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
    
    # Files table
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
    
    # Project config table
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
    print("✅ SQLite initialized successfully!", file=sys.stderr); sys.stderr.flush()

if __name__ == "__main__":
    init_db()
