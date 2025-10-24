#!/usr/bin/env python3
"""
Script para migrar/corrigir o banco de dados PostgreSQL
Execute: python migrate_db.py
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

def migrate_database():
    """Migra o banco de dados para corrigir tipos de dados"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL não encontrada. Este script é apenas para PostgreSQL.")
        return False
    
    try:
        print("🔧 Conectando ao PostgreSQL...")
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor, sslmode='require')
        cursor = conn.cursor()
        
        print("🗑️ Removendo tabelas existentes...")
        
        # Remove tabelas na ordem correta (devido às foreign keys)
        tables_to_drop = ['arquivos', 'lancamentos', 'categorias', 'obras', 'usuarios']
        
        for table in tables_to_drop:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                print(f"   ✅ Tabela {table} removida")
            except Exception as e:
                print(f"   ⚠️ Erro ao remover {table}: {e}")
        
        print("\n🏗️ Criando tabelas com tipos corretos...")
        
        # Cria tabela de usuários
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
        print("   ✅ Tabela usuarios criada")
        
        # Cria tabela de obras
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
        print("   ✅ Tabela obras criada")
        
        # Cria tabela de categorias
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
        print("   ✅ Tabela categorias criada")
        
        # Cria tabela de lançamentos
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
        print("   ✅ Tabela lancamentos criada")
        
        # Cria tabela de arquivos
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
        print("   ✅ Tabela arquivos criada")
        
        # Cria função para updated_at
        cursor.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """)
        print("   ✅ Função update_updated_at_column criada")
        
        # Cria triggers
        tables_with_updated_at = ['usuarios', 'obras', 'categorias', 'lancamentos']
        for table in tables_with_updated_at:
            cursor.execute(f"""
                CREATE TRIGGER update_{table}_updated_at
                    BEFORE UPDATE ON {table}
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column();
            """)
            print(f"   ✅ Trigger para {table} criado")
        
        # Cria índices
        indexes = [
            "CREATE INDEX idx_lancamentos_obra_id ON lancamentos(obra_id);",
            "CREATE INDEX idx_lancamentos_categoria_id ON lancamentos(categoria_id);",
            "CREATE INDEX idx_lancamentos_data ON lancamentos(data_lancamento);",
            "CREATE INDEX idx_arquivos_lancamento_id ON arquivos(lancamento_id);",
            "CREATE INDEX idx_usuarios_email ON usuarios(email);"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        print("   ✅ Índices criados")
        
        print("\n📊 Inserindo dados iniciais...")
        
        # Insere usuário padrão
        cursor.execute("""
            INSERT INTO usuarios (nome, email, senha, ativo)
            VALUES (%s, %s, %s, %s)
        """, ("Deverson", "deverson@obra.com", "123456", True))
        print("   ✅ Usuário padrão criado")
        
        # Insere categorias padrão
        categorias_padrao = [
            ("Material de Construção", "Materiais básicos como cimento, areia, brita", "#e74c3c"),
            ("Mão de Obra", "Pagamentos de funcionários e prestadores", "#3498db"),
            ("Ferramentas e Equipamentos", "Compra e aluguel de ferramentas", "#f39c12"),
            ("Elétrica", "Material e serviços elétricos", "#9b59b6"),
            ("Hidráulica", "Material e serviços hidráulicos", "#1abc9c"),
            ("Acabamento", "Materiais de acabamento e pintura", "#34495e"),
            ("Documentação", "Taxas, licenças e documentos", "#95a5a6"),
            ("Transporte", "Fretes e transportes diversos", "#e67e22"),
            ("Alimentação", "Alimentação da equipe", "#27ae60"),
            ("Outros", "Gastos diversos não categorizados", "#7f8c8d")
        ]
        
        for nome, descricao, cor in categorias_padrao:
            cursor.execute("""
                INSERT INTO categorias (nome, descricao, cor, ativo)
                VALUES (%s, %s, %s, %s)
            """, (nome, descricao, cor, True))
        print("   ✅ Categorias padrão criadas")
        
        # Insere obra padrão
        from datetime import date, timedelta
        data_inicio = date.today()
        data_fim = data_inicio + timedelta(days=365)
        
        cursor.execute("""
            INSERT INTO obras (nome, orcamento, data_inicio, data_fim_prevista, ativo)
            VALUES (%s, %s, %s, %s, %s)
        """, ("Minha Obra", 100000.00, data_inicio, data_fim, True))
        print("   ✅ Obra padrão criada")
        
        conn.commit()
        
        print("\n🎉 Migração concluída com sucesso!")
        print("\n📋 Dados criados:")
        print("   👤 Usuário: deverson@obra.com / 123456")
        print("   🏷️ 10 categorias padrão")
        print("   🏗️ Obra inicial com orçamento de R$ 100.000,00")
        print("\n✅ Sistema pronto para uso!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na migração: {repr(e)}")
        if 'conn' in locals():
            conn.rollback()
        return False
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

if __name__ == "__main__":
    print("🚀 Iniciando migração do banco de dados PostgreSQL...")
    
    if migrate_database():
        print("\n✅ Migração concluída! Agora você pode usar o sistema normalmente.")
    else:
        print("\n❌ Migração falhou! Verifique os logs acima.")
        sys.exit(1)