import sqlite3
import os
import sys # Import sys para verificar o psycopg2

# Variável global para armazenar o tipo de banco de dados uma vez detectado.
# Isso evita re-determinar o tipo em cada execução/re-execução do script.
_db_type_cache = None

def get_db_connection():
    """Conecta ao banco de dados (SQLite local ou PostgreSQL no Render)"""
    global _db_type_cache

    # Determina o tipo de DB apenas uma vez por execução do Streamlit
    if _db_type_cache is None:
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            try:
                # Tenta importar psycopg2 para verificar se é PostgreSQL
                import psycopg2
                _db_type_cache = 'postgresql'
            except ImportError:
                # Se DATABASE_URL existe mas psycopg2 não, assume SQLite (erro de config?)
                _db_type_cache = 'sqlite' 
        else:
            _db_type_cache = 'sqlite'
    
    if _db_type_cache == 'postgresql':
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            database_url = os.getenv('DATABASE_URL')
            print(f"🔗 Tentando conectar ao PostgreSQL...")
            if 'supabase.co' in database_url or 'neon.tech' in database_url:
                conn = psycopg2.connect(database_url + "?sslmode=require", cursor_factory=RealDictCursor)
            else:
                conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
            print("✅ Conectado ao PostgreSQL!")
            return conn
        except Exception as e:
            print(f"❌ Erro PostgreSQL ao conectar: {e}")
            print("🔄 Fallback para SQLite...")
            # Se PostgreSQL falhar, muda o cache para SQLite para esta execução e tenta SQLite
            _db_type_cache = 'sqlite' 
            return get_sqlite_connection()
    else: # SQLite
        return get_sqlite_connection()

def get_sqlite_connection():
    """Conexão SQLite"""
    print("🔗 Conectando ao SQLite local...")
    db_path = "obra_database.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_current_db_type():
    """Retorna o tipo de banco de dados atual (PostgreSQL ou SQLite)"""
    global _db_type_cache
    if _db_type_cache is None: # Garante que o tipo seja determinado se ainda não foi
        # Chamar get_db_connection para que ele defina _db_type_cache internamente
        # Mas fechar a conexão imediatamente se não for usada.
        conn = get_db_connection() 
        conn.close()
    return _db_type_cache

def init_db():
    """Inicializa o banco de dados com todas as tabelas (CREATE TABLE IF NOT EXISTS)"""
    current_db_type = get_current_db_type() # Usa a função auxiliar
    
    if current_db_type == 'postgresql':
        try:
            init_postgresql()
        except Exception as e:
            print(f"❌ Erro ao inicializar PostgreSQL: {e}")
            print("🔄 Inicializando SQLite como fallback...")
            init_sqlite()
    else: # SQLite
        init_sqlite()

def init_postgresql():
    """Inicializa banco PostgreSQL"""
    print("🐘 Inicializando PostgreSQL...")
    conn = get_db_connection() # Agora get_db_connection retorna apenas a conexão
    cursor = conn.cursor()
    
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
    print("✅ PostgreSQL inicializado com sucesso!")

def init_sqlite():
    """Inicializa banco SQLite (código original)"""
    print("📁 Inicializando SQLite...")
    conn = get_sqlite_connection() # Agora get_sqlite_connection retorna apenas a conexão
    cursor = conn.cursor()
    
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