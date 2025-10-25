import sys
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, date, timedelta
from utils.helpers import get_dados_dashboard, get_obra_config, format_currency_br, format_date_br

def show_dashboard():
    """Exibe dashboard principal"""
    
    # Botão mobile para abrir sidebar
    if st.button("📱 Menu", key="mobile_menu", help="Abrir menu de navegação"):
        st.sidebar.write("") # Força abertura da sidebar
    
    st.title("📊 Dashboard Financeiro")
    
    # Carrega dados
    with st.spinner("Carregando dados..."):
        dados = get_dados_dashboard()
        obra_config = get_obra_config()
    
    if not obra_config or not obra_config.get('id'):
        st.warning("⚠️ Configure uma obra para visualizar o dashboard!")
        if st.button("🔧 Ir para Configurações"):
            st.session_state.current_page = "⚙️ Configurações"
            st.rerun()
        return
    
    # Informações da obra
    st.info(f"🏗️ **Obra:** {obra_config['nome']} | **Orçamento:** {format_currency_br(obra_config['orcamento'])}")
    
    # Métricas principais
    _show_metricas_principais(dados)
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        _show_grafico_categorias(dados)
    
    with col2:
        _show_progresso_orcamento(dados)
    
    st.markdown("---")
    
    # Últimos lançamentos e evolução
    col3, col4 = st.columns([1, 1])
    
    with col3:
        _show_ultimos_lancamentos(dados)
    
    with col4:
        _show_evolucao_gastos()

def _show_metricas_principais(dados):
    """Exibe métricas principais"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💰 Total Gasto",
            value=format_currency_br(dados['total_gasto']),
            delta=None
        )
    
    with col2:
        st.metric(
            label="🎯 Orçamento",
            value=format_currency_br(dados['orcamento']),
            delta=None
        )
    
    with col3:
        percentual = dados['percentual_executado']
        delta_color = "normal" if percentual <= 100 else "inverse"
        st.metric(
            label="📈 % Executado",
            value=f"{percentual:.1f}%",
            delta=f"{percentual - 100:.1f}%" if percentual > 100 else None,
            delta_color=delta_color
        )
    
    with col4:
        saldo = dados['saldo_restante']
        delta_color = "normal" if saldo >= 0 else "inverse"
        st.metric(
            label="💵 Saldo Restante",
            value=format_currency_br(saldo),
            delta=None,
            delta_color=delta_color
        )

def _show_grafico_categorias(dados):
    """Gráfico de gastos por categoria"""
    st.subheader("🏷️ Gastos por Categoria")
    
    if not dados['gastos_por_categoria']:
        st.info("📝 Nenhum gasto registrado ainda.")
        return
    
    # Filtra categorias com valor > 0
    categorias_com_gastos = [cat for cat in dados['gastos_por_categoria'] if cat['valor'] > 0]
    
    if not categorias_com_gastos:
        st.info("📝 Nenhum gasto registrado ainda.")
        return
    
    # Prepara dados para o gráfico
    nomes = [cat['nome'] for cat in categorias_com_gastos]
    valores = [cat['valor'] for cat in categorias_com_gastos]
    cores = [cat['cor'] for cat in categorias_com_gastos]
    
    # Cria gráfico de pizza
    fig = go.Figure(data=[go.Pie(
        labels=nomes,
        values=valores,
        marker=dict(colors=cores),
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.2f}<br>Percentual: %{percent}<extra></extra>',
        textinfo='label+percent',
        textposition='auto'
    )])
    
    fig.update_layout(
        title="Distribuição de Gastos por Categoria",
        showlegend=True,
        height=400,
        margin=dict(t=50, b=50, l=50, r=50)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def _show_progresso_orcamento(dados):
    """Gráfico de progresso do orçamento"""
    st.subheader("🎯 Progresso do Orçamento")
    
    if dados['orcamento'] <= 0:
        st.info("📝 Configure um orçamento para visualizar o progresso.")
        return
    
    # Calcula valores
    gasto = dados['total_gasto']
    orcamento = dados['orcamento']
    restante = max(0, orcamento - gasto)
    excesso = max(0, gasto - orcamento)
    
    # Prepara dados
    if excesso > 0:
        labels = ['Gasto dentro do orçamento', 'Excesso']
        values = [orcamento, excesso]
        colors = ['#28a745', '#dc3545']
    else:
        labels = ['Gasto', 'Restante']
        values = [gasto, restante]
        colors = ['#007bff', '#e9ecef']
    
    # Cria gráfico
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors),
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.2f}<br>Percentual: %{percent}<extra></extra>',
        textinfo='label+percent',
        textposition='auto'
    )])
    
    fig.update_layout(
        title="Execução do Orçamento",
        showlegend=True,
        height=400,
        margin=dict(t=50, b=50, l=50, r=50)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Barra de progresso
    percentual = min(100, (gasto / orcamento) * 100)
    st.progress(percentual / 100)
    
    if excesso > 0:
        st.error(f"⚠️ Orçamento excedido em {format_currency_br(excesso)}")
    else:
        st.success(f"✅ Dentro do orçamento. Restam {format_currency_br(restante)}")

def _show_ultimos_lancamentos(dados):
    """Lista dos últimos lançamentos"""
    st.subheader("📋 Últimos Lançamentos")
    
    if not dados['ultimos_lancamentos']:
        st.info("📝 Nenhum lançamento registrado ainda.")
        return
    
    for lancamento in dados['ultimos_lancamentos']:
        with st.container():
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"**{lancamento['descricao']}**")
                st.caption(f"🏷️ {lancamento['categoria_nome']}")
            
            with col2:
                st.write(f"**{format_currency_br(lancamento['valor'])}**")
            
            with col3:
                st.write(f"📅 {format_date_br(lancamento['data_lancamento'])}")
            
            st.markdown("---")

def _show_evolucao_gastos():
    """Gráfico de evolução dos gastos"""
    st.subheader("📈 Evolução dos Gastos")
    
    try:
        # Busca dados de evolução
        dados_evolucao = _get_dados_evolucao()
        
        if not dados_evolucao:
            st.info("📝 Dados insuficientes para gerar gráfico de evolução.")
            return
        
        # Converte para DataFrame
        df = pd.DataFrame(dados_evolucao)
        df['data'] = pd.to_datetime(df['data'])
        df = df.sort_values('data')
        
        # Calcula acumulado
        df['valor_acumulado'] = df['valor'].cumsum()
        
        # Cria gráfico
        fig = go.Figure()
        
        # Linha de gastos acumulados
        fig.add_trace(go.Scatter(
            x=df['data'],
            y=df['valor_acumulado'],
            mode='lines+markers',
            name='Gastos Acumulados',
            line=dict(color='#007bff', width=3),
            marker=dict(size=6),
            hovertemplate='Data: %{x}<br>Valor Acumulado: R$ %{y:,.2f}<extra></extra>'
        ))
        
        # Barras de gastos diários
        fig.add_trace(go.Bar(
            x=df['data'],
            y=df['valor'],
            name='Gastos Diários',
            marker_color='rgba(0, 123, 255, 0.3)',
            hovertemplate='Data: %{x}<br>Valor: R$ %{y:,.2f}<extra></extra>'
        ))
        
        fig.update_layout(
            title="Evolução dos Gastos ao Longo do Tempo",
            xaxis_title="Data",
            yaxis_title="Valor (R$)",
            hovermode='x unified',
            height=400,
            margin=dict(t=50, b=50, l=50, r=50),
            showlegend=True
        )
        
        # Atualiza eixos corretamente
        fig.update_xaxes(showgrid=True, gridcolor='#f0f0f0')
        fig.update_yaxes(showgrid=True, gridcolor='#f0f0f0', tickformat=',.0f')
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        print(f"Erro ao gerar gráfico de evolução: {repr(e)}", file=sys.stderr)
        st.error("❌ Erro ao carregar gráfico de evolução.")

def _get_dados_evolucao():
    """Busca dados para gráfico de evolução"""
    try:
        from config.database import get_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        if is_postgres:
            query = """
                SELECT 
                    l.data_lancamento as data,
                    SUM(l.valor) as valor
                FROM lancamentos l
                JOIN obras o ON l.obra_id = o.id
                WHERE o.ativo = TRUE
                GROUP BY l.data_lancamento
                ORDER BY l.data_lancamento
            """
        else:
            query = """
                SELECT 
                    l.data_lancamento as data,
                    SUM(l.valor) as valor
                FROM lancamentos l
                JOIN obras o ON l.obra_id = o.id
                WHERE o.ativo = 1
                GROUP BY l.data_lancamento
                ORDER BY l.data_lancamento
            """
        
        cursor.execute(query)
        
        dados = []
        for row in cursor.fetchall():
            valor = 0.0
            try:
                if row['valor'] is not None:
                    from decimal import Decimal
                    if isinstance(row['valor'], Decimal):
                        valor = float(row['valor'])
                    else:
                        valor = float(row['valor'])
            except (TypeError, ValueError):
                valor = 0.0
            
            dados.append({
                'data': row['data'],
                'valor': valor
            })
        
        return dados
        
    except Exception as e:
        print(f"Erro ao buscar dados de evolução: {repr(e)}", file=sys.stderr)
        return []
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def _show_resumo_categorias():
    """Resumo detalhado por categorias"""
    st.subheader("📊 Resumo por Categorias")
    
    try:
        from utils.helpers import get_resumo_categorias
        
        resumo = get_resumo_categorias()
        
        if not resumo:
            st.info("📝 Nenhum dado disponível.")
            return
        
        # Cria tabela
        for categoria in resumo:
            if categoria['total_valor'] > 0:  # Só mostra categorias com gastos
                with st.expander(f"🏷️ {categoria['nome']} - {format_currency_br(categoria['total_valor'])}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total de Lançamentos", categoria['total_lancamentos'])
                    
                    with col2:
                        st.metric("Valor Total", format_currency_br(categoria['total_valor']))
                    
                    with col3:
                        st.metric("Valor Médio", format_currency_br(categoria['valor_medio']))
        
    except Exception as e:
        print(f"Erro ao mostrar resumo de categorias: {repr(e)}", file=sys.stderr)
        st.error("❌ Erro ao carregar resumo de categorias.")

def show_mobile_navigation():
    """Navegação especial para mobile"""
    st.markdown("### 📱 Navegação Rápida")
    
    # Botões grandes para mobile
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💰 Novo Lançamento", use_container_width=True, key="mobile_lancamento"):
            st.session_state.current_page = "💰 Lançamentos"
            st.rerun()
        
        if st.button("📈 Relatórios", use_container_width=True, key="mobile_relatorios"):
            st.session_state.current_page = "📈 Relatórios"
            st.rerun()
    
    with col2:
        if st.button("⚙️ Configurações", use_container_width=True, key="mobile_config"):
            st.session_state.current_page = "⚙️ Configurações"
            st.rerun()
        
        if st.button("🔄 Atualizar", use_container_width=True, key="mobile_refresh"):
            st.rerun()

# Adiciona CSS para melhorar mobile
def add_mobile_css():
    """CSS específico para mobile"""
    st.markdown("""
    <style>
    /* Mobile-first approach */
    @media (max-width: 768px) {
        .stButton > button {
            font-size: 16px !important;
            padding: 12px 16px !important;
            margin: 4px 0 !important;
        }
        
        .metric-container {
            margin: 8px 0 !important;
        }
        
        .plotly-graph-div {
            height: 300px !important;
        }
        
        /* Força sidebar a ser visível */
        .css-1d391kg {
            position: relative !important;
            width: 100% !important;
            min-width: 100% !important;
        }
        
        /* Botão de menu mobile */
        .mobile-menu-btn {
            position: fixed;
            top: 10px;
            left: 10px;
            z-index: 999;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            font-size: 20px;
        }
    }
    
    /* Melhora geral da interface */
    .stMetric {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    
    .stPlotlyChart {
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        padding: 1rem;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Chama CSS no início do dashboard
add_mobile_css()