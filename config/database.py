import os
import sys
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    """Retorna conexão com o banco de dados (SQLite local ou PostgreSQL no Render)"""
    try:
        # Verifica se está no ambiente de produção (Render)
        database_url = os.getenv('DATABASE_URL')
        
        if database_url:
            # PostgreSQL (Render/Produção)
            print("Conectando ao PostgreSQL...", file=sys.stderr)
            conn = psycopg2.connect(
                database_url,
                cursor_factory=RealDictCursor,
                sslmode='require'
            )
            conn.autocommit = False
            return conn
        else:
            # SQLite (Desenvolvimento local)
            print("Conectando ao SQLite local...", file=sys.stderr)
            conn = sqlite3.connect(
                'obra_financeira.db',
                check_same_thread=False,
                timeout=30.0
            )
            conn.row_factory = sqlite3.Row
            
            # Habilita foreign keys no SQLite
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            
            return conn
            
    except Exception as e:
        print(f"Erro ao conectar com banco de dados: {repr(e)}", file=sys.stderr)
        raise

def init_db():
    """Inicializa o banco de dados com todas as tabelas"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Detecta tipo de banco
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        print(f"Inicializando banco de dados ({'PostgreSQL' if is_postgres else 'SQLite'})...", file=sys.stderr)
        
        if is_postgres:
            # PostgreSQL - Auto-migração
            print("Executando auto-migração PostgreSQL...", file=sys.stderr)
            
            # Remove tabelas se existirem (para reset completo)
            tables_to_drop = ['arquivos', 'lancamentos', 'categorias', 'obras', 'usuarios']
            for table in tables_to_drop:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
            
            # Tabela de usuarios
            cursor.execute("""
                CREATE TABLE usuarios (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    senha VARCHAR(255) NOT NULL,
                    ativo BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Tabela de obras
            cursor.execute("""
                CREATE TABLE obras (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(200) NOT NULL,
                    orcamento DECIMAL(15,2) DEFAULT 0,
                    data_inicio DATE,
                    data_fim_prevista DATE,
                    ativo BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Tabela de categorias
            cursor.execute("""
                CREATE TABLE categorias (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(100) NOT NULL,
                    descricao TEXT,
                    cor VARCHAR(7) DEFAULT '#3498db',
                    ativo BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Tabela de lançamentos
            cursor.execute("""
                CREATE TABLE lancamentos (
                    id SERIAL PRIMARY KEY,
                    obra_id INTEGER NOT NULL REFERENCES obras(id) ON DELETE CASCADE,
                    categoria_id INTEGER NOT NULL REFERENCES categorias(id) ON DELETE RESTRICT,
                    descricao TEXT NOT NULL,
                    valor DECIMAL(15,2) NOT NULL CHECK (valor > 0),
                    data_lancamento DATE NOT NULL,
                    observacoes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Tabela de arquivos
            cursor.execute("""
                CREATE TABLE arquivos (
                    id SERIAL PRIMARY KEY,
                    lancamento_id INTEGER NOT NULL REFERENCES lancamentos(id) ON DELETE CASCADE,
                    nome_arquivo VARCHAR(255) NOT NULL,
                    tipo_arquivo VARCHAR(100),
                    tamanho_arquivo INTEGER,
                    conteudo_arquivo BYTEA,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Função para atualizar updated_at
            cursor.execute("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            """)
            
            # Triggers para updated_at
            tables_with_updated_at = ['usuarios', 'obras', 'categorias', 'lancamentos']
            for table in tables_with_updated_at:
                cursor.execute(f"""
                    CREATE TRIGGER update_{table}_updated_at
                        BEFORE UPDATE ON {table}
                        FOR EACH ROW
                        EXECUTE FUNCTION update_updated_at_column();
                """)
            
            # Índices para performance
            cursor.execute("CREATE INDEX idx_lancamentos_obra_id ON lancamentos(obra_id);")
            cursor.execute("CREATE INDEX idx_lancamentos_categoria_id ON lancamentos(categoria_id);")
            cursor.execute("CREATE INDEX idx_lancamentos_data ON lancamentos(data_lancamento);")
            cursor.execute("CREATE INDEX idx_arquivos_lancamento_id ON arquivos(lancamento_id);")
            cursor.execute("CREATE INDEX idx_usuarios_email ON usuarios(email);")
            
        else:
            # SQLite - Desenvolvimento
            print("Criando tabelas SQLite...", file=sys.stderr)
            
            # Tabela de usuarios
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    senha TEXT NOT NULL,
                    ativo INTEGER DEFAULT 1 CHECK (ativo IN (0, 1)),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de obras
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS obras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    orcamento REAL DEFAULT 0 CHECK (orcamento >= 0),
                    data_inicio DATE,
                    data_fim_prevista DATE,
                    ativo INTEGER DEFAULT 1 CHECK (ativo IN (0, 1)),
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
                    cor TEXT DEFAULT '#3498db',
                    ativo INTEGER DEFAULT 1 CHECK (ativo IN (0, 1)),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de lançamentos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lancamentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    obra_id INTEGER NOT NULL REFERENCES obras(id) ON DELETE CASCADE,
                    categoria_id INTEGER NOT NULL REFERENCES categorias(id) ON DELETE RESTRICT,
                    descricao TEXT NOT NULL,
                    valor REAL NOT NULL CHECK (valor > 0),
                    data_lancamento DATE NOT NULL,
                    observacoes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de arquivos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS arquivos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lancamento_id INTEGER NOT NULL REFERENCES lancamentos(id) ON DELETE CASCADE,
                    nome_arquivo TEXT NOT NULL,
                    tipo_arquivo TEXT,
                    tamanho_arquivo INTEGER,
                    conteudo_arquivo BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Triggers para updated_at no SQLite
            tables_with_updated_at = ['usuarios', 'obras', 'categorias', 'lancamentos']
            for table in tables_with_updated_at:
                cursor.execute(f"""
                    CREATE TRIGGER IF NOT EXISTS update_{table}_updated_at
                    AFTER UPDATE ON {table}
                    FOR EACH ROW
                    BEGIN
                        UPDATE {table} SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                    END;
                """)
            
            # Índices para performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_lancamentos_obra_id ON lancamentos(obra_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_lancamentos_categoria_id ON lancamentos(categoria_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_lancamentos_data ON lancamentos(data_lancamento);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_arquivos_lancamento_id ON arquivos(lancamento_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);")
        
        conn.commit()
        print("✅ Todas as tabelas criadas com sucesso!", file=sys.stderr)
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao inicializar banco: {repr(e)}", file=sys.stderr)
        raise
    finally:
        cursor.close()
        conn.close()

def test_connection():
    """Testa a conexão com o banco de dados"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Teste simples
        if os.getenv('DATABASE_URL'):
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ PostgreSQL conectado: {version}", file=sys.stderr)
        else:
            cursor.execute("SELECT sqlite_version();")
            version = cursor.fetchone()[0]
            print(f"✅ SQLite conectado: versão {version}", file=sys.stderr)
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar conexão: {repr(e)}", file=sys.stderr)
        return False