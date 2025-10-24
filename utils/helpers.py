import pandas as pd
import streamlit as st
from datetime import datetime, timedelta, date
from config.database import get_db_connection
import sys
from decimal import Decimal

def get_obra_config():
    """Retorna configurações da obra, com tratamento robusto e debug."""
    conn = None
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
            print("DEBUG: get_obra_config - Tabela 'obra_config' não existe. Retornando configuração padrão.", file=sys.stderr); sys.stderr.flush()
            if conn: conn.close()
            return {
                'id': None, 'nome_obra': 'Obra Não Configurada', 'orcamento_total': 0.0,
                'data_inicio': None, 'data_previsao_fim': None
            }
        # --- Fim da verificação ---

        # Usar cursor explícito para fetchall() e depois converter para DataFrame
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nome_obra, orcamento_total, data_inicio, data_previsao_fim 
            FROM obra_config 
            ORDER BY id DESC 
            LIMIT 1
        """)
        row = cursor.fetchone() # Fetch single row
        cursor.close()
        conn.close() # Fechar a conexão

        if row:
            # Se usar RealDictCursor, row já é um dict-like object
            # Se usar cursor padrão, row é uma tupla, converter manualmente
            if db_type == 'postgresql': # RealDictCursor retorna dict-like
                row_data = dict(row) 
            else: # SQLite com sqlite3.Row retorna dict-like
                row_data = dict(row)
            
            print(f"DEBUG: get_obra_config - Configuração lida do DB (raw): {row_data}", file=sys.stderr); sys.stderr.flush()
            
            # Converte campos numéricos para float de forma defensiva
            for key in ['orcamento_total']:
                if key in row_data and row_data[key] is not None:
                    try:
                        # Ensure it's converted from Decimal or string to float
                        row_data[key] = float(Decimal(row_data[key])) if isinstance(row_data[key], (str, Decimal)) else float(row_data[key])
                    except (ValueError, TypeError) as convert_err:
                        print(f"DEBUG: get_obra_config - Erro de conversão para float em '{key}': Valor='{row_data[key]}' Tipo='{type(row_data[key])}' - {convert_err}", file=sys.stderr); sys.stderr.flush()
                        row_data[key] = 0.0 # Define como 0.0 se a conversão falhar

            # Converte campos de data para objetos date
            for key in ['data_inicio', 'data_previsao_fim']:
                if key in row_data and isinstance(row_data[key], str) and row_data[key]:
                    try:
                        row_data[key] = datetime.strptime(row_data[key], '%Y-%m-%d').date()
                    except ValueError as date_err:
                        print(f"DEBUG: get_obra_config - Erro de conversão de data em '{key}': Valor='{row_data[key]}' - {date_err}", file=sys.stderr); sys.stderr.flush()
                        row_data[key] = None 
                elif key in row_data and (row_data[key] == '' or row_data[key] is None): # Trata string vazia ou None para data
                    row_data[key] = None
                # Se já for um objeto date/datetime, manter.
                elif key in row_data and isinstance(row_data[key], datetime):
                    row_data[key] = row_data[key].date() # Converte datetime para date
                elif key in row_data and not isinstance(row_data[key], date): # Se não for str, date, ou datetime, imprimir aviso
                    print(f"DEBUG: get_obra_config - Data '{key}' não é str, date ou datetime: '{row_data[key]}' (Tipo: {type(row_data[key])})", file=sys.stderr); sys.stderr.flush()
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
        print(f"DEBUG: get_obra_config - Erro CRÍTICO (try/except externo): {repr(e)}", file=sys.stderr); sys.stderr.flush()
        if conn: conn.close()
        return {
            'id': None, 'nome_obra': f'Erro na Config: {repr(e)}', 'orcamento_total': 0.0,
            'data_inicio': None, 'data_previsao_fim': None
        }

def get_dados_dashboard():
    """Retorna dados completos para o dashboard e relatórios, incluindo total previsto por categorias"""
    conn = None
    try:
        conn, db_type = get_db_connection()
        
        # --- Total gasto (Fetch direto) ---
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(valor), 0) as total FROM lancamentos")
        total_gasto = float(Decimal(cursor.fetchone()['total'])) if cursor.rowcount > 0 and cursor.fetchone() is not None else 0.0
        cursor.close()
        
        # Gastos por categoria (usar pd.read_sql_query com RealDictCursor)
        gastos_categoria = pd.read_sql_query("""
            SELECT c.nome, COALESCE(SUM(l.valor), 0) as gasto
            FROM categorias c
            LEFT JOIN lancamentos l ON c.id = l.categoria_id
            WHERE c.ativo = 1
            GROUP BY c.id, c.nome 
            ORDER BY gasto DESC
        """, conn)

        if 'gasto' in gastos_categoria.columns:
            gastos_categoria['gasto'] = pd.to_numeric(gastos_categoria['gasto'], errors='coerce').fillna(0.0)

        # --- Total previsto das categorias ativas (Fetch direto) ---
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(orcamento_previsto), 0) as total FROM categorias WHERE ativo = 1")
        total_previsto_categorias = float(Decimal(cursor.fetchone()['total'])) if cursor.rowcount > 0 and cursor.fetchone() is not None else 0.0
        cursor.close()

        # Lançamentos recentes (pd.read_sql_query com RealDictCursor)
        lancamentos_recentes = pd.read_sql_query("""
            SELECT l.data, l.descricao, l.valor, c.nome as categoria
            FROM lancamentos l
            JOIN categorias c ON l.categoria_id = c.id
            ORDER BY l.data DESC, l.id DESC
            LIMIT 10
        """, conn)
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
        print(f"DEBUG: Erro ao buscar dados do dashboard (get_dados_dashboard): {repr(e)}", file=sys.stderr); sys.stderr.flush()
        if conn: conn.close()
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

def format_date(date_obj):
    """Formata objeto date/datetime para padrão brasileiro"""
    if date_obj is None:
        return "Não definido"
    
    # Se for string, tenta converter para date
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
        except ValueError:
            return date_obj # Retorna a string original se não puder converter
    
    if isinstance(date_obj, (datetime, date)):
        return date_obj.strftime('%d/%m/%Y')
    else:
        print(f"DEBUG: format_date - Objeto não é data nem string formatável: {date_obj} (Tipo: {type(date_obj)})", file=sys.stderr); sys.stderr.flush()
        return str(date_obj)


def format_date_br(date_obj):
    """Alias para format_date (compatibilidade)"""
    return format_date(date_obj)

def get_categorias_ativas():
    """Busca categorias ativas"""
    conn = None
    try:
        conn, db_type = get_db_connection()
        categorias = pd.read_sql_query("""
            SELECT id, nome, descricao, orcamento_previsto 
            FROM categorias 
            WHERE ativo = 1 
            ORDER BY nome
        """, conn)
        conn.close()

        if 'orcamento_previsto' in categorias.columns:
            categorias['orcamento_previsto'] = pd.to_numeric(categorias['orcamento_previsto'], errors='coerce').fillna(0.0)

        return categorias
    except Exception as e:
        print(f"DEBUG: Erro ao buscar categorias (get_categorias_ativas): {repr(e)}", file=sys.stderr); sys.stderr.flush()
        if conn: conn.close()
        return pd.DataFrame()