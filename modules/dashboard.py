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
    
    st.title("🏠 Início")
    
    # Botão de debug para forçar atualização
    if st.button("🔍 Debug & Atualizar", help="Força atualização e mostra logs"):
        from utils.helpers import debug_database_state, force_refresh_dashboard
        debug_database_state()
        force_refresh_dashboard()
        st.rerun()
    
    # Carrega dados SEM CACHE
    with st.spinner("Carregando dados..."):
        dados = get_dados_dashboard()
        obra_config = get_obra_config()
    
    # Debug info
    if st.checkbox("🐛 Mostrar Debug Info", value=False):
        st.json({
            "obra_config": obra_config,
            "total_gasto": dados['total_gasto'],
            "orcamento": dados['orcamento'],
            "num_categorias": len(dados['gastos_por_categoria']),
            "num_lancamentos": len(dados['ultimos_lancamentos'])
        })
    
    if not obra_config or not obra_config.get('id'):
        st.warning("⚠️ Configure uma obra para visualizar o painel!")
        if st.button("🔧 Ir para Configurações"):
            st.session_state.current_page = "⚙️ Configurações"
            st.rerun()
        return
    
    # Métricas principais
    show_metricas_principais(dados)
    
    st.markdown("---")
    
    # ÚLTIMOS LANÇAMENTOS PRIMEIRO
    show_ultimos_lancamentos_destacados(dados)
    
    st.markdown("---")
    
    # GRÁFICO ÚNICO COMBINADO
    show_grafico_distribuicao_completo(dados)

def show_metricas_principais(dados):
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

def show_ultimos_lancamentos_destacados(dados):
    """Lista dos últimos lançamentos com destaque especial"""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 1.5rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    ">
        <h2 style="
            color: white;
            font-size: 2.2rem;
            font-weight: bold;
            margin: 0 0 1.5rem 0;
            text-align: center;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        ">📋 Últimos Lançamentos</h2>
    </div>
    """, unsafe_allow_html=True)
    
    if not dados['ultimos_lancamentos']:
        st.markdown("""
        <div style="
            background: #f8f9fa;
            padding: 2rem;
            border-radius: 10px;
            text-align: center;
            border: 2px dashed #dee2e6;
        ">
            <h3 style="color: #6c757d; margin: 0;">📝 Nenhum lançamento registrado ainda</h3>
            <p style="color: #6c757d; margin: 0.5rem 0 0 0;">Adicione seu primeiro lançamento para começar!</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Container com fundo escuro para os lançamentos
    for i, lancamento in enumerate(dados['ultimos_lancamentos']):
        # Cores alternadas para melhor visualização
        bg_color = "#2c3e50" if i % 2 == 0 else "#34495e"
        
        st.markdown(f"""
        <div style="
            background: {bg_color};
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
            border-left: 5px solid {lancamento.get('categoria_cor', '#007bff')};
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 200px;">
                    <h3 style="
                        color: white;
                        font-size: 1.4rem;
                        font-weight: bold;
                        margin: 0 0 0.5rem 0;
                        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
                    ">{lancamento['descricao']}</h3>
                    <p style="
                        color: #ecf0f1;
                        font-size: 1.1rem;
                        margin: 0;
                        display: flex;
                        align-items: center;
                        gap: 0.5rem;
                    ">
                        <span style="
                            background: {lancamento.get('categoria_cor', '#007bff')};
                            padding: 0.3rem 0.8rem;
                            border-radius: 20px;
                            font-size: 0.9rem;
                            font-weight: 600;
                        ">🏷️ {lancamento['categoria_nome']}</span>
                    </p>
                </div>
                <div style="text-align: right; min-width: 150px;">
                    <h2 style="
                        color: #2ecc71;
                        font-size: 1.8rem;
                        font-weight: bold;
                        margin: 0 0 0.3rem 0;
                        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
                    ">{format_currency_br(lancamento['valor'])}</h2>
                    <p style="
                        color: #bdc3c7;
                        font-size: 1.1rem;
                        margin: 0;
                        font-weight: 500;
                    ">📅 {format_date_br(lancamento['data_lancamento'])}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def show_grafico_distribuicao_completo(dados):
    """Gráfico único com distribuição de gastos por categoria com % do orçamento total"""
    st.subheader("📊 Distribuição de Gastos por Categoria")
    
    if not dados['gastos_por_categoria']:
        st.info("📝 Nenhum gasto registrado ainda.")
        return
    
    # Filtra categorias com valor > 0
    categorias_com_gastos = [cat for cat in dados['gastos_por_categoria'] if cat['valor'] > 0]
    
    if not categorias_com_gastos:
        st.info("📝 Nenhum gasto registrado ainda.")
        return
    
    # Prepara dados para o gráfico
    orcamento_total = dados['orcamento']
    
    # Calcula percentuais em relação ao orçamento total
    for categoria in categorias_com_gastos:
        if orcamento_total > 0:
            categoria['percentual_orcamento'] = (categoria['valor'] / orcamento_total) * 100
        else:
            categoria['percentual_orcamento'] = 0
    
    nomes = [cat['nome'] for cat in categorias_com_gastos]
    valores = [cat['valor'] for cat in categorias_com_gastos]
    cores = [cat['cor'] for cat in categorias_com_gastos]
    percentuais_orcamento = [cat['percentual_orcamento'] for cat in categorias_com_gastos]
    
    # Cria gráfico de pizza com informações detalhadas
    fig = go.Figure(data=[go.Pie(
        labels=nomes,
        values=valores,
        marker=dict(colors=cores),
        hovertemplate='<b>%{label}</b><br>' +
                     'Valor: R$ %{value:,.2f}<br>' +
                     'Do Total Gasto: %{percent}<br>' +
                     'Do Orçamento Total: %{customdata:.1f}%<extra></extra>',
        customdata=percentuais_orcamento,
        textinfo='label+percent',
        textposition='auto',
        textfont=dict(size=12, color='white')
    )])
    
    fig.update_layout(
        title={
            'text': "Distribuição de Gastos por Categoria<br><sub>Percentuais em relação ao total gasto</sub>",
            'x': 0.5,
            'xanchor': 'center'
        },
        showlegend=True,
        height=500,
        margin=dict(t=80, b=50, l=50, r=50),
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabela detalhada abaixo do gráfico
    st.markdown("### 📋 Detalhamento por Categoria")
    
    # Cria tabela com informações detalhadas
    for categoria in categorias_com_gastos:
        with st.expander(f"🏷️ {categoria['nome']} - {format_currency_br(categoria['valor'])}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Valor Gasto",
                    format_currency_br(categoria['valor'])
                )
            
            with col2:
                st.metric(
                    "% do Total Gasto",
                    f"{categoria['percentual']:.1f}%"
                )
            
            with col3:
                st.metric(
                    "% do Orçamento Total",
                    f"{categoria['percentual_orcamento']:.1f}%"
                )
    
    # Resumo final
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Gasto",
            format_currency_br(dados['total_gasto'])
        )
    
    with col2:
        st.metric(
            "Orçamento Total",
            format_currency_br(dados['orcamento'])
        )
    
    with col3:
        percentual_usado = (dados['total_gasto'] / dados['orcamento'] * 100) if dados['orcamento'] > 0 else 0
        st.metric(
            "% Orçamento Usado",
            f"{percentual_usado:.1f}%"
        )

def show_grafico_categorias(dados):
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

def show_progresso_orcamento(dados):
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

def show_evolucao_gastos():
    """Gráfico de evolução dos gastos"""
    st.subheader("📈 Evolução dos Gastos")
    
    try:
        # Busca dados de evolução
        dados_evolucao = get_dados_evolucao()
        
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

def get_dados_evolucao():
    """Busca dados para gráfico de evolução"""
    try:
        from config.database import get_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        # Busca obra ativa
        obra_config = get_obra_config()
        if not obra_config.get('id'):
            return []
        
        obra_id = obra_config['id']
        
        if is_postgres:
            query = """
                SELECT 
                    l.data_lancamento as data,
                    SUM(CAST(l.valor AS DECIMAL)) as valor
                FROM lancamentos l
                WHERE l.obra_id = %s
                GROUP BY l.data_lancamento
                ORDER BY l.data_lancamento
            """
            cursor.execute(query, (obra_id,))
        else:
            query = """
                SELECT 
                    l.data_lancamento as data,
                    SUM(CAST(l.valor AS REAL)) as valor
                FROM lancamentos l
                WHERE l.obra_id = ?
                GROUP BY l.data_lancamento
                ORDER BY l.data_lancamento
            """
            cursor.execute(query, (obra_id,))
        
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

def show_resumo_categorias():
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
            height: 400px !important;
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