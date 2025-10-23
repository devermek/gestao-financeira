import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from config.database import get_db_connection

def get_obra_config():
    """Retorna configurações da obra"""
    try:
        conn = get_db_connection()
        
        # Buscar configuração da obra
        config = pd.read_sql_query("""
            SELECT nome_obra, orcamento_total, data_inicio, data_previsao_fim 
            FROM obra_config 
            ORDER BY id DESC 
            LIMIT 1
        """, conn)
        
        conn.close()
        
        if not config.empty:
            # Converter para dict se for Series
            if hasattr(config.iloc[0], 'to_dict'):
                return config.iloc[0].to_dict()
            return config.iloc[0]
        else:
            # Retornar configuração padrão se não existir
            return {
                'nome_obra': 'Obra Não Configurada',
                'orcamento_total': 0.0,
                'data_inicio': None,
                'data_previsao_fim': None
            }
    except Exception as e:
        print(f"Erro ao buscar configuração da obra: {e}")
        return {
            'nome_obra': 'Erro na Configuração',
            'orcamento_total': 0.0,
            'data_inicio': None,
            'data_previsao_fim': None
        }

def get_dados_dashboard():
    """Retorna dados para o dashboard"""
    try:
        conn = get_db_connection()
        
        # Total gasto
        total_gasto = pd.read_sql_query("""
            SELECT COALESCE(SUM(valor), 0) as total
            FROM lancamentos
        """, conn)
        
        # Gastos por categoria
        gastos_categoria = pd.read_sql_query("""
            SELECT c.nome, COALESCE(SUM(l.valor), 0) as total
            FROM categorias c
            LEFT JOIN lancamentos l ON c.id = l.categoria_id
            WHERE c.ativo = 1
            GROUP BY c.id, c.nome
            ORDER BY total DESC
        """, conn)
        
        # Lançamentos recentes
        lancamentos_recentes = pd.read_sql_query("""
            SELECT l.data, l.descricao, l.valor, c.nome as categoria
            FROM lancamentos l
            JOIN categorias c ON l.categoria_id = c.id
            ORDER BY l.data DESC, l.id DESC
            LIMIT 5
        """, conn)
        
        # Gastos por mês
        gastos_mensais = pd.read_sql_query("""
            SELECT 
                strftime('%Y-%m', data) as mes,
                SUM(valor) as total
            FROM lancamentos
            GROUP BY strftime('%Y-%m', data)
            ORDER BY mes
        """, conn)
        
        conn.close()
        
        return {
            'total_gasto': total_gasto.iloc[0]['total'] if not total_gasto.empty else 0,
            'gastos_categoria': gastos_categoria,
            'lancamentos_recentes': lancamentos_recentes,
            'gastos_mensais': gastos_mensais
        }
        
    except Exception as e:
        print(f"Erro ao buscar dados do dashboard: {e}")
        return {
            'total_gasto': 0,
            'gastos_categoria': pd.DataFrame(),
            'lancamentos_recentes': pd.DataFrame(),
            'gastos_mensais': pd.DataFrame()
        }

def format_currency(value):
    """Formata valor como moeda brasileira"""
    if value is None:
        value = 0
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
        conn = get_db_connection()
        categorias = pd.read_sql_query("""
            SELECT id, nome, descricao, orcamento_previsto 
            FROM categorias 
            WHERE ativo = 1 
            ORDER BY nome
        """, conn)
        conn.close()
        return categorias
    except Exception as e:
        print(f"Erro ao buscar categorias: {e}")
        return pd.DataFrame()