import sqlite3
import os
import pandas as pd # Mantido caso você o utilize em outras partes do seu projeto

def get_db_connection():
    """Conecta ao banco de dados (SQLite local ou PostgreSQL no Render)"""
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # Ambiente de produção (PostgreSQL)
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            print(f"🔗 Tentando conectar ao PostgreSQL...", file=sys.stderr); sys.stderr.flush()
            
            # Adicionar configurações SSL para Supabase/Neon
            if 'supabase.co' in database_url or 'neon.tech' in database_url:
                conn = psycopg2.connect(database_url + "?sslmode=require", cursor_factory=RealDictCursor)
            else:
                conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
            
            print("✅ Conectado ao PostgreSQL!", file=sys.stderr); sys.stderr.flush()
            return conn
        except Exception as e:
            print(f"❌ Erro PostgreSQL: {e}", file=sys.stderr); sys.stderr.flush()
            print("🔄 Fallback para SQLite...", file=sys.stderr); sys.stderr.flush()
            # Fallback para SQLite se PostgreSQL falhar
            return get_sqlite_connection()
    else:
        # Ambiente local (SQLite)
        return get_sqlite_connection()

def get_sqlite_connection():
    """Conexão SQLite"""
    print("🔗 Conectando ao SQLite local...", file=sys.stderr); sys.stderr.flush()
    db_path = "obra_database.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row # Permite acessar colunas por nome
    return conn

def get_current_db_type():
    """Retorna o tipo de banco de dados atualmente em uso (PostgreSQL ou SQLite)."""
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return 'postgresql'
    else:
        return 'sqlite'

def init_db():
    """Inicializa o banco de dados com todas as tabelas"""
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        try:
            # PostgreSQL (Render/Supabase/Neon)
            init_postgresql()
        except Exception as e:
            print(f"❌ Erro ao inicializar PostgreSQL: {e}", file=sys.stderr); sys.stderr.flush()
            print("�� Inicializando SQLite como fallback...", file=sys.stderr); sys.stderr.flush()
            init_sqlite()
    else:
        # SQLite (Local)
        init_sqlite()

def init_postgresql():
    """Inicializa banco PostgreSQL"""
    print("🐘 Inicializando PostgreSQL...", file=sys.stderr); sys.stderr.flush()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabela de usuários (com 'ativo' como BOOLEAN e 'updated_at')
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            senha VARCHAR(255) NOT NULL,
            tipo VARCHAR(50) NOT NULL CHECK (tipo IN ('gestor', 'investidor')),
            ativo BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Trigger para atualizar 'updated_at' automaticamente no PostgreSQL
    cursor.execute("""
        CREATE OR REPLACE FUNCTION update_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
           NEW.updated_at = NOW();
           RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    cursor.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_users_updated_at') THEN
                CREATE TRIGGER update_users_updated_at
                BEFORE UPDATE ON usuarios
                FOR EACH ROW
                EXECUTE FUNCTION update_timestamp();
            END IF;
        END $$;
    """)
    
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
    cursor.execute("""
        CREATE OR REPLACE FUNCTION update_categorias_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
        $$ LANGUAGE plpgsql;
    """)
    cursor.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_categorias_updated_at') THEN
                CREATE TRIGGER update_categorias_updated_at
                BEFORE UPDATE ON categorias
                FOR EACH ROW
                EXECUTE FUNCTION update_categorias_timestamp();
            END IF;
        END $$;
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
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (categoria_id) REFERENCES categorias (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)
    cursor.execute("""
        CREATE OR REPLACE FUNCTION update_lancamentos_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
        $$ LANGUAGE plpgsql;
    """)
    cursor.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_lancamentos_updated_at') THEN
                CREATE TRIGGER update_lancamentos_updated_at
                BEFORE UPDATE ON lancamentos
                FOR EACH ROW
                EXECUTE FUNCTION update_lancamentos_timestamp();
            END IF;
        END $$;
    """)
    
    # Tabela de arquivos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS arquivos (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            tipo VARCHAR(100) NOT NULL,
            tamanho INTEGER,
            conteudo BYTEA,
            lancamento_id INTEGER, -- Pode ser NULL se o arquivo não estiver associado a um lançamento
            usuario_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lancamento_id) REFERENCES lancamentos (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)
    cursor.execute("""
        CREATE OR REPLACE FUNCTION update_arquivos_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
        $$ LANGUAGE plpgsql;
    """)
    cursor.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_arquivos_updated_at') THEN
                CREATE TRIGGER update_arquivos_updated_at
                BEFORE UPDATE ON arquivos
                FOR EACH ROW
                EXECUTE FUNCTION update_arquivos_timestamp();
            END IF;
        END $$;
    """)
    
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
    cursor.execute("""
        CREATE OR REPLACE FUNCTION update_obra_config_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
        $$ LANGUAGE plpgsql;
    """)
    cursor.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_obra_config_updated_at') THEN
                CREATE TRIGGER update_obra_config_updated_at
                BEFORE UPDATE ON obra_config
                FOR EACH ROW
                EXECUTE FUNCTION update_obra_config_timestamp();
            END IF;
        END $$;
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ PostgreSQL inicializado com sucesso!", file=sys.stderr); sys.stderr.flush()

def init_sqlite():
    """Inicializa banco SQLite"""
    print("📁 Inicializando SQLite...", file=sys.stderr); sys.stderr.flush()
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    # Tabela de usuários (com 'ativo' como INTEGER e 'updated_at')
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK (tipo IN ('gestor', 'investidor')),
            ativo INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Nota: SQLite não tem ON UPDATE CURRENT_TIMESTAMP nativo no CREATE TABLE para updated_at.
    # O controle de updated_at para SQLite precisaria ser feito na lógica da aplicação
    # ou com um TRIGGER separado se você usar uma versão específica do SQLite.
    
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