import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from config.database import get_db_connection

def show_dashboard(user, obra_config):
    """Exibe o dashboard principal"""
    st.title("📊 Dashboard - Visão Geral da Obra")
    
    # Verificar se obra_config é válido
    if not obra_config or not obra_config.get('nome_obra'):
        st.warning("⚠️ Configure a obra primeiro para visualizar o dashboard completo")
        obra_config = {
            'nome_obra': 'Obra Não Configurada',
            'orcamento_total': 0.0
        }
    
    # Buscar dados
    dados = get_dados_dashboard_local()
    
    # Header com informações da obra
    st.markdown(f"### 🏗️ {obra_config['nome_obra']}")
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 Total Gasto",
            format_currency_local(dados['total_gasto']),
            delta=None
        )
    
    with col2:
        orcamento = obra_config.get('orcamento_total', 0)
        st.metric(
            "🎯 Orçamento Total",
            format_currency_local(orcamento),
            delta=None
        )
    
    with col3:
        if orcamento > 0:
            percentual = (dados['total_gasto'] / orcamento) * 100
            st.metric(
                "📈 % Executado",
                f"{percentual:.1f}%",
                delta=None
            )
        else:
            st.metric("📈 % Executado", "0%", delta=None)
    
    with col4:
        saldo = orcamento - dados['total_gasto']
        st.metric(
            "💳 Saldo Restante",
            format_currency_local(saldo),
            delta=None
        )
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("�� Gastos por Categoria")
        if not dados['gastos_categoria'].empty:
            fig_pie = px.pie(
                dados['gastos_categoria'],
                values='total',
                names='nome',
                title="Distribuição de Gastos"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Nenhum dado de categoria disponível")
    
    with col2:
        st.subheader("📈 Evolução Mensal")
        if not dados['gastos_mensais'].empty:
            fig_line = px.line(
                dados['gastos_mensais'],
                x='mes',
                y='total',
                title="Gastos por Mês"
            )
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Nenhum dado mensal disponível")
    
    # Lançamentos recentes
    st.subheader("📋 Últimos Lançamentos")
    if not dados['lancamentos_recentes'].empty:
        # Formatar dados para exibição
        df_display = dados['lancamentos_recentes'].copy()
        df_display['data'] = pd.to_datetime(df_display['data']).dt.strftime('%d/%m/%Y')
        df_display['valor'] = df_display['valor'].apply(lambda x: format_currency_local(x))
        
        st.dataframe(
            df_display[['data', 'categoria', 'descricao', 'valor']],
            column_config={
                'data': 'Data',
                'categoria': 'Categoria',
                'descricao': 'Descrição',
                'valor': 'Valor'
            },
            use_container_width=True
        )
    else:
        st.info("📝 Nenhum lançamento encontrado")

def get_dados_dashboard_local():
    """Retorna dados para o dashboard (função local)"""
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
            HAVING SUM(l.valor) > 0
            ORDER BY total DESC
        """, conn)
        
        # Lançamentos recentes
        lancamentos_recentes = pd.read_sql_query("""
            SELECT l.data, l.descricao, l.valor, c.nome as categoria
            FROM lancamentos l
            JOIN categorias c ON l.categoria_id = c.id
            ORDER BY l.data DESC, l.id DESC
            LIMIT 10
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

def format_currency_local(value):
    """Formata valor como moeda brasileira (função local)"""
    if value is None:
        value = 0
    return f"R\$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def get_estatisticas_resumo():
    """Retorna estatísticas resumidas"""
    try:
        conn = get_db_connection()
        
        stats = pd.read_sql_query("""
            SELECT 
                COUNT(*) as total_lancamentos,
                COALESCE(SUM(valor), 0) as total_gasto,
                COALESCE(AVG(valor), 0) as media_lancamento
            FROM lancamentos
        """, conn)
        
        conn.close()
        
        if not stats.empty:
            return stats.iloc[0].to_dict()
        else:
            return {
                'total_lancamentos': 0,
                'total_gasto': 0,
                'media_lancamento': 0
            }
            
    except Exception as e:
        print(f"Erro ao buscar estatísticas: {e}")
        return {
            'total_lancamentos': 0,
            'total_gasto': 0,
            'media_lancamento': 0
        }