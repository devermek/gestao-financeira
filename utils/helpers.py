import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from config.database import get_db_connection
import sys # Necessário para sys.stderr
from decimal import Decimal # Importar Decimal para tratamento

def get_obra_config():
    """Retorna configurações da obra, com tratamento robusto e debug."""
    conn, db_type = None, None # Inicializa para evitar UnboundLocalError
    try:
        conn, db_type = get_db_connection()
        
        # --- Verificação da existência da tabela obra_config ---
        table_exists = False
        cursor = conn.cursor()
        if db_type == 'postgresql':
            cursor.execute("SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'obra_config');")
            table_exists = cursor.fetchone()[0]
        elif db_type == 'sqlite':
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='obra_config';")
            table_exists = cursor.fetchone() is not None
        cursor.close()

        if not table_exists:
            print("DEBUG: Tabela 'obra_config' não existe. Retornando configuração padrão.", file=sys.stderr); sys.stderr.flush()
            if conn: conn.close()
            return {
                'id': None, 'nome_obra': 'Obra Não Configurada', 'orcamento_total': 0.0,
                'data_inicio': None, 'data_previsao_fim': None
            }
        # --- Fim da verificação ---

        config = pd.read_sql_query("""
            SELECT id, nome_obra, orcamento_total, data_inicio, data_previsao_fim 
            FROM obra_config 
            ORDER BY id DESC 
            LIMIT 1
        """, conn)
        
        conn.close() # Fecha a conexão após a query
        
        if not config.empty:
            row_data = dict(config.iloc[0]) # Converte para um dicionário padrão do Python
            print(f"DEBUG: get_obra_config - Configuração lida do DB: {row_data}", file=sys.stderr); sys.stderr.flush()
            
            # Converte campos numéricos para float de forma defensiva
            for key in ['orcamento_total']:
                if key in row_data and row_data[key] is not None:
                    try:
                        row_data[key] = float(row_data[key])
                    except (ValueError, TypeError, Decimal) as convert_err:
                        print(f"DEBUG: get_obra_config - Erro de conversão para float em '{key}': {row_data[key]} - {convert_err}", file=sys.stderr); sys.stderr.flush()
                        row_data[key] = 0.0 # Define como 0.0 se a conversão falhar

            # Converte campos de data para objetos date
            for key in ['data_inicio', 'data_previsao_fim']:
                if key in row_data and isinstance(row_data[key], str) and row_data[key]:
                    try:
                        row_data[key] = datetime.strptime(row_data[key], '%Y-%m-%d').date()
                    except ValueError as date_err:
                        print(f"DEBUG: get_obra_config - Erro de conversão de data em '{key}': {row_data[key]} - {date_err}", file=sys.stderr); sys.stderr.flush()
                        # Mantém como string ou None se a conversão falhar (para exibição bruta se necessário)
                        row_data[key] = None 
                elif key in row_data and row_data[key] == '': # Trata string vazia para data
                    row_data[key] = None
            
            print(f"DEBUG: get_obra_config - Configuração processada antes de retornar: {row_data}", file=sys.stderr); sys.stderr.flush()
            return row_data
        else:
            print("DEBUG: get_obra_config - Nenhuma configuração encontrada no DB. Retornando padrão.", file=sys.stderr); sys.stderr.flush()
            return {
                'id': None, 'nome_obra': 'Obra Não Configurada', 'orcamento_total': 0.0,
                'data_inicio': None, 'data_previsao_fim': None
            }
    except Exception as e:
        print(f"DEBUG: get_obra_config - Erro CRÍTICO (try/except externo): {e}", file=sys.stderr); sys.stderr.flush()
        if conn: conn.close() # Garante que a conexão seja fechada em caso de erro
        # Retorna um dicionário válido mesmo que um erro ocorra, para evitar o atributo 'get' em str
        return {
            'id': None, 'nome_obra': f'Erro na Config: {e}', 'orcamento_total': 0.0,
            'data_inicio': None, 'data_previsao_fim': None
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
        total_gasto = float(total_gasto_df.iloc[0]['total']) if not total_gasto_df.empty else 0.0
        
        # Gastos por categoria
        gastos_categoria = pd.read_sql_query("""
            SELECT c.nome, COALESCE(SUM(l.valor), 0) as gasto
            FROM categorias c
            LEFT JOIN lancamentos l ON c.id = l.categoria_id
            WHERE c.ativo = 1
            GROUP BY c.id, c.nome 
            ORDER BY gasto DESC
        """, conn)

        # Garante que a coluna 'gasto' seja numérica
        if 'gasto' in gastos_categoria.columns:
            gastos_categoria['gasto'] = pd.to_numeric(gastos_categoria['gasto'], errors='coerce').fillna(0.0)

        # Total previsto das categorias ativas
        total_previsto_categorias_df = pd.read_sql_query("""
            SELECT COALESCE(SUM(orcamento_previsto), 0) as total
            FROM categorias
            WHERE ativo = 1
        """, conn)
        total_previsto_categorias = float(total_previsto_categorias_df.iloc[0]['total']) if not total_previsto_categorias_df.empty else 0.0

        # Lançamentos recentes (Limitado para 10 para dashboard)
        lancamentos_recentes = pd.read_sql_query("""
            SELECT l.data, l.descricao, l.valor, c.nome as categoria
            FROM lancamentos l
            JOIN categorias c ON l.categoria_id = c.id
            ORDER BY l.data DESC, l.id DESC
            LIMIT 10
        """, conn)
        # Garante que a coluna 'valor' seja numérica
        if 'valor' in lancamentos_recentes.columns:
            lancamentos_recentes['valor'] = pd.to_numeric(lancamentos_recentes['valor'], errors='coerce').fillna(0.0)
        
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
        # Garante que a coluna 'total' seja numérica
        if 'total' in gastos_mensais.columns:
            gastos_mensais['total'] = pd.to_numeric(gastos_mensais['total'], errors='coerce').fillna(0.0)
        
        conn.close()
        
        return {
            'total_gasto': total_gasto,
            'total_previsto_categorias': total_previsto_categorias, 
            'gastos_categoria': gastos_categoria,
            'lancamentos_recentes': lancamentos_recentes,
            'gastos_mensais': gastos_mensais
        }
        
    except Exception as e:
        print(f"DEBUG: Erro ao buscar dados do dashboard (get_dados_dashboard): {e}", file=sys.stderr); sys.stderr.flush()
        # st.error(f"Erro ao buscar dados do dashboard: {e}") # Descomentar para debug no Streamlit
        return {
            'total_gasto': 0.0,
            'total_previsto_categorias': 0.0, 
            'gastos_categoria': pd.DataFrame(),
            'lancamentos_recentes': pd.DataFrame(),
            'gastos_mensais': pd.DataFrame()
        }

def format_currency(value):
    """Formata valor como moeda brasileira"""
    if value is None:
        value = 0.0
    return f"R\$ {float(value):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

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
    except Exception as e:
        print(f"DEBUG: Erro ao formatar data '{date_str}': {e}", file=sys.stderr); sys.stderr.flush()
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

        # Garante que 'orcamento_previsto' seja float
        if 'orcamento_previsto' in categorias.columns:
            categorias['orcamento_previsto'] = pd.to_numeric(categorias['orcamento_previsto'], errors='coerce').fillna(0.0)

        return categorias
    except Exception as e:
        print(f"DEBUG: Erro ao buscar categorias (get_categorias_ativas): {e}", file=sys.stderr); sys.stderr.flush()
        # st.error(f"Erro ao buscar categorias: {e}") # Descomentar para debug no Streamlit
        return pd.DataFrame()