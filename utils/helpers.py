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

def get_estatisticas_obra():
    """Retorna estatísticas gerais da obra"""
    try:
        conn = get_db_connection()
        
        # Estatísticas básicas
        stats = pd.read_sql_query("""
            SELECT 
                COUNT(*) as total_lancamentos,
                COALESCE(SUM(valor), 0) as total_gasto,
                COALESCE(AVG(valor), 0) as media_lancamento,
                MIN(data) as primeira_data,
                MAX(data) as ultima_data
            FROM lancamentos
        """, conn)
        
        # Orçamento total
        orcamento = pd.read_sql_query("""
            SELECT COALESCE(orcamento_total, 0) as orcamento_total
            FROM obra_config
            ORDER BY id DESC
            LIMIT 1
        """, conn)
        
        conn.close()
        
        if not stats.empty:
            resultado = stats.iloc[0].to_dict()
            if not orcamento.empty:
                resultado['orcamento_total'] = orcamento.iloc[0]['orcamento_total']
            else:
                resultado['orcamento_total'] = 0
            
            # Calcular percentual gasto
            if resultado['orcamento_total'] > 0:
                resultado['percentual_gasto'] = (resultado['total_gasto'] / resultado['orcamento_total']) * 100
            else:
                resultado['percentual_gasto'] = 0
                
            return resultado
        else:
            return {
                'total_lancamentos': 0,
                'total_gasto': 0,
                'media_lancamento': 0,
                'primeira_data': None,
                'ultima_data': None,
                'orcamento_total': 0,
                'percentual_gasto': 0
            }
            
    except Exception as e:
        print(f"Erro ao buscar estatísticas: {e}")
        return {
            'total_lancamentos': 0,
            'total_gasto': 0,
            'media_lancamento': 0,
            'primeira_data': None,
            'ultima_data': None,
            'orcamento_total': 0,
            'percentual_gasto': 0
        }

def format_currency(value):
    """Formata valor como moeda brasileira"""
    if value is None:
        value = 0
    return f"R\$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

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

def get_periodo_options():
    """Retorna opções de período para relatórios"""
    hoje = datetime.now().date()
    
    return {
        "Últimos 7 dias": (hoje - timedelta(days=7), hoje),
        "Últimos 30 dias": (hoje - timedelta(days=30), hoje),
        "Últimos 90 dias": (hoje - timedelta(days=90), hoje),
        "Este mês": (hoje.replace(day=1), hoje),
        "Este ano": (hoje.replace(month=1, day=1), hoje),
        "Personalizado": None
    }

def calcular_progresso_obra():
    """Calcula o progresso da obra baseado no orçamento"""
    try:
        stats = get_estatisticas_obra()
        
        if stats['orcamento_total'] > 0:
            percentual = (stats['total_gasto'] / stats['orcamento_total']) * 100
            return min(percentual, 100)  # Máximo 100%
        return 0
        
    except Exception as e:
        print(f"Erro ao calcular progresso: {e}")
        return 0

def get_categorias_com_gastos():
    """Retorna categorias com seus gastos totais"""
    try:
        conn = get_db_connection()
        
        categorias = pd.read_sql_query("""
            SELECT 
                c.id,
                c.nome,
                c.orcamento_previsto,
                COALESCE(SUM(l.valor), 0) as gasto_real,
                COUNT(l.id) as total_lancamentos
            FROM categorias c
            LEFT JOIN lancamentos l ON c.id = l.categoria_id
            WHERE c.ativo = 1
            GROUP BY c.id, c.nome, c.orcamento_previsto
            ORDER BY c.nome
        """, conn)
        
        conn.close()
        
        # Calcular percentual gasto por categoria
        if not categorias.empty:
            categorias['percentual_gasto'] = categorias.apply(
                lambda row: (row['gasto_real'] / row['orcamento_previsto'] * 100) 
                if row['orcamento_previsto'] > 0 else 0, 
                axis=1
            )
        
        return categorias
        
    except Exception as e:
        print(f"Erro ao buscar categorias com gastos: {e}")
        return pd.DataFrame()

def validar_valor_monetario(valor):
    """Valida se um valor monetário é válido"""
    try:
        valor_float = float(valor)
        return valor_float > 0
    except:
        return False

def gerar_relatorio_resumo():
    """Gera um resumo executivo da obra"""
    try:
        obra_config = get_obra_config()
        stats = get_estatisticas_obra()
        categorias = get_categorias_com_gastos()
        
        resumo = {
            'obra': obra_config,
            'estatisticas': stats,
            'categorias_resumo': {
                'total_categorias': len(categorias),
                'categoria_maior_gasto': categorias.loc[categorias['gasto_real'].idxmax()]['nome'] if not categorias.empty else 'N/A',
                'categoria_maior_percentual': categorias.loc[categorias['percentual_gasto'].idxmax()]['nome'] if not categorias.empty else 'N/A'
            }
        }
        
        return resumo
        
    except Exception as e:
        print(f"Erro ao gerar resumo: {e}")
        return None