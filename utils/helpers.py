import pandas as pd
import streamlit as st # Adicionei st para poder usar st.error para debug se necessário.
from datetime import datetime, timedelta
from config.database import get_db_connection
import sys # Necessário para sys.stderr

def get_obra_config():
    """Retorna configurações da obra"""
    try:
        conn, db_type = get_db_connection() # Obter a conexão e o tipo de DB
        
        # Buscar configuração da obra
        config = pd.read_sql_query("""
            SELECT id, nome_obra, orcamento_total, data_inicio, data_previsao_fim 
            FROM obra_config 
            ORDER BY id DESC 
            LIMIT 1
        """, conn) # Adicionado 'id' para uso posterior
        
        conn.close()
        
        if not config.empty:
            # sqlite3.Row não tem to_dict(), mas pandas lida com isso.
            # RealDictRow de psycopg2 tem to_dict().
            # Garante que o retorno seja sempre um dicionário padrão.
            if isinstance(config.iloc[0], dict): 
                return config.iloc[0]
            else: 
                return dict(config.iloc[0])
        else:
            # Retornar configuração padrão se não existir
            return {
                'id': None, # Adicionado 'id' aqui também para consistência
                'nome_obra': 'Obra Não Configurada',
                'orcamento_total': 0.0,
                'data_inicio': None,
                'data_previsao_fim': None
            }
    except Exception as e:
        print(f"Erro ao buscar configuração da obra (get_obra_config): {e}", file=sys.stderr); sys.stderr.flush()
        # st.error(f"Erro ao buscar configuração da obra: {e}") # Descomentar para debug no Streamlit
        return {
            'id': None, 
            'nome_obra': 'Erro na Configuração',
            'orcamento_total': 0.0,
            'data_inicio': None,
            'data_previsao_fim': None
        }

def get_dados_dashboard():
    """Retorna dados completos para o dashboard e relatórios, incluindo total previsto por categorias"""
    try:
        conn, db_type = get_db_connection() # Obter a conexão e o tipo de DB
        
        # Total gasto
        total_gasto_df = pd.read_sql_query("""
            SELECT COALESCE(SUM(valor), 0) as total
            FROM lancamentos
        """, conn)
        total_gasto = total_gasto_df.iloc[0]['total'] if not total_gasto_df.empty else 0
        
        # Gastos por categoria
        gastos_categoria = pd.read_sql_query("""
            SELECT c.nome, COALESCE(SUM(l.valor), 0) as gasto
            FROM categorias c
            LEFT JOIN lancamentos l ON c.id = l.categoria_id
            WHERE c.ativo = 1
            -- Adicionado para garantir que todas as categorias ativas apareçam, mesmo sem gastos
            GROUP BY c.id, c.nome 
            ORDER BY gasto DESC
        """, conn)

        # Total previsto das categorias ativas
        total_previsto_categorias_df = pd.read_sql_query("""
            SELECT COALESCE(SUM(orcamento_previsto), 0) as total
            FROM categorias
            WHERE ativo = 1
        """, conn)
        total_previsto_categorias = total_previsto_categorias_df.iloc[0]['total'] if not total_previsto_categorias_df.empty else 0

        # Lançamentos recentes (Limitado para 10 para dashboard)
        lancamentos_recentes = pd.read_sql_query("""
            SELECT l.data, l.descricao, l.valor, c.nome as categoria
            FROM lancamentos l
            JOIN categorias c ON l.categoria_id = c.id
            ORDER BY l.data DESC, l.id DESC
            LIMIT 10
        """, conn)
        
        # Gastos por mês
        if db_type == 'sqlite':
            gastos_mensais = pd.read_sql_query("""
                SELECT 
                    strftime('%Y-%m', data) as mes,
                    SUM(valor) as total
                FROM lancamentos
                GROUP BY strftime('%Y-%m', data)
                ORDER BY mes
            """, conn)
        else: # PostgreSQL
            gastos_mensais = pd.read_sql_query("""
                SELECT 
                    TO_CHAR(data, 'YYYY-MM') as mes,
                    SUM(valor) as total
                FROM lancamentos
                GROUP BY TO_CHAR(data, 'YYYY-MM')
                ORDER BY mes
            """, conn)
        
        conn.close()
        
        return {
            'total_gasto': total_gasto,
            'total_previsto_categorias': total_previsto_categorias, 
            'gastos_categoria': gastos_categoria,
            'lancamentos_recentes': lancamentos_recentes,
            'gastos_mensais': gastos_mensais
        }
        
    except Exception as e:
        print(f"Erro ao buscar dados do dashboard (get_dados_dashboard): {e}", file=sys.stderr); sys.stderr.flush()
        # st.error(f"Erro ao buscar dados do dashboard: {e}") # Descomentar para debug no Streamlit
        return {
            'total_gasto': 0,
            'total_previsto_categorias': 0, 
            'gastos_categoria': pd.DataFrame(),
            'lancamentos_recentes': pd.DataFrame(),
            'gastos_mensais': pd.DataFrame()
        }

def format_currency(value):
    """Formata valor como moeda brasileira"""
    if value is None:
        value = 0
    # Usar .replace(',', 'X').replace('.', ',').replace('X', '.') para formatar corretamente no BR
    return f"R\$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def format_currency_br(value):
    """Formata valor como moeda brasileira (alias)"""
    return format_currency(value)

def format_date(date_str):
    """Formata data para padrão brasileiro"""
    if not date_str:
        return "Não definido"
    
    try:
        if isinstance(date_str, str):
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        else:
            date_obj = date_str
        return date_obj.strftime('%d/%m/%Y')
    except:
        return str(date_str)

def format_date_br(date_str):
    """Alias para format_date (compatibilidade)"""
    return format_date(date_str)

def get_categorias_ativas():
    """Busca categorias ativas"""
    try:
        conn, db_type = get_db_connection() # Obter a conexão e o tipo de DB
        categorias = pd.read_sql_query("""
            SELECT id, nome, descricao, orcamento_previsto 
            FROM categorias 
            WHERE ativo = 1 
            ORDER BY nome
        """, conn)
        conn.close()
        return categorias
    except Exception as e:
        print(f"Erro ao buscar categorias (get_categorias_ativas): {e}", file=sys.stderr); sys.stderr.flush()
        # st.error(f"Erro ao buscar categorias: {e}") # Descomentar para debug no Streamlit
        return pd.DataFrame()