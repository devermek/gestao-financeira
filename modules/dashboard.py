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
    
    # Carrega dados
    with st.spinner("Carregando dados..."):
        dados = get_dados_dashboard()
        obra_config = get_obra_config()
    
    if not obra_config or not obra_config.get('id'):
        st.warning("⚠️ Configure uma obra para visualizar o painel!")
        if st.button("🔧 Ir para Configurações"):
            st.session_state.current_page = "⚙️ Configurações"
            st.rerun()
        return
    
    # Métricas principais
    _show_metricas_principais(dados)
    
    st.markdown("---")
    
    # ÚLTIMOS LANÇAMENTOS PRIMEIRO
    _show_ultimos_lancamentos_destacados(dados)
    
    st.markdown("---")
    
    # GRÁFICO ÚNICO COMBINADO
    _show_grafico_distribuicao_completo(dados)

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

def _show_ultimos_lancamentos_destacados(dados):
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

def _show_grafico_distribuicao_completo(dados):
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