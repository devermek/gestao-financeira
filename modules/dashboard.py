import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
from utils.helpers import get_dados_dashboard, format_date_br, get_estatisticas_obra
from config.database import get_db_connection

# --- NOVA FUNÇÃO: Formatação de moeda BRL ---
def format_currency_brl(value):
    """
    Formata um valor numérico para o padrão monetário brasileiro (R$ X.XXX,XX).
    Usa ponto como separador de milhares e vírgula como separador decimal.
    """
    # Formata o número para duas casas decimais com ponto como separador decimal padrão
    s = f"{value:,.2f}" 
    # Troca o separador de milhar (,) por um caractere temporário (X)
    s = s.replace(",", "X")
    # Troca o separador decimal (.) por vírgula (,)
    s = s.replace(".", ",")
    # Troca o caractere temporário (X) pelo ponto (.)
    s = s.replace("X", ".")
    return s

def show_dashboard(user, obra_config):
    """Exibe dashboard principal"""
    # --- ALTERAÇÃO AQUI: "Dashboard" para "Tela Inicial" ---
    st.header(f"🏠 Tela Inicial - {obra_config['nome_obra']}")
    
    # Buscar dados atualizados
    total_gasto, total_previsto_categorias, gastos_categoria, evolucao, ultimos = get_dados_dashboard()
    
    # Verificar se há dados
    if total_gasto == 0:
        st.info("📊 Ainda não há lançamentos registrados. Vá em 'Lançamentos' para adicionar gastos.")
        return
    
    # Métricas principais
    _show_metricas_principais(total_gasto, total_previsto_categorias, obra_config)
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        _show_grafico_categorias(gastos_categoria)
    
    with col2:
        _show_grafico_evolucao(evolucao)
    
    # Alertas e lançamentos recentes
    _show_alertas_e_recentes(total_gasto, total_previsto_categorias, obra_config, ultimos)

def _show_metricas_principais(total_gasto, total_previsto_categorias, obra_config):
    """Exibe métricas principais"""
    
    # Injeção de CSS para diminuir a fonte dos valores das métricas (mantido da correção anterior)
    st.markdown(
        """
        <style>
        /* Altera o tamanho da fonte dos valores dentro dos componentes st.metric */
        div[data-testid="stMetricValue"] {
            font-size: 24px !important; /* Ajuste este valor conforme necessário */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    orcamento_obra = obra_config['orcamento_total']
    orcamento_referencia = orcamento_obra if orcamento_obra > 0 else total_previsto_categorias
    
    if orcamento_referencia > 0:
        percentual = (total_gasto / orcamento_referencia) * 100
        restante = orcamento_referencia - total_gasto
    else:
        percentual = 0
        restante = 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 Total Gasto",
            # --- ALTERAÇÃO AQUI: Usando a nova função de formatação ---
            f"R$ {format_currency_brl(total_gasto)}",
            delta=None
        )
    
    with col2:
        st.metric(
            "📊 Orçamento Total",
            # --- ALTERAÇÃO AQUI: Usando a nova função de formatação ---
            f"R$ {format_currency_brl(orcamento_referencia)}",
            delta=None
        )
    
    with col3:
        cor_percentual = "normal" if percentual <= 80 else "inverse"
        st.metric(
            "📈 % Executado",
            f"{percentual:.1f}%",
            delta=None,
            delta_color=cor_percentual
        )
    
    with col4:
        cor_restante = "normal" if restante >= 0 else "inverse"
        st.metric(
            "💵 Restante",
            # --- ALTERAÇÃO AQUI: Usando a nova função de formatação ---
            f"R$ {format_currency_brl(restante)}",
            delta=None,
            delta_color=cor_restante
        )

def _show_grafico_categorias(gastos_categoria):
    """Exibe gráfico de gastos por categoria"""
    st.markdown("### 📊 Gastos por Categoria")
    
    if gastos_categoria.empty:
        st.info("Nenhum dado disponível")
        return
    
    # Preparar dados
    df_grafico = gastos_categoria.copy()
    df_grafico['percentual'] = (df_grafico['gasto'] / df_grafico['orcamento_previsto'] * 100).fillna(0)
    
    # Gráfico de barras
    fig = go.Figure()
    
    # Barras de orçamento previsto
    fig.add_trace(go.Bar(
        name='Orçamento Previsto',
        x=df_grafico['nome'],
        y=df_grafico['orcamento_previsto'],
        marker_color='lightblue',
        opacity=0.6
    ))
    
    # Barras de gasto real
    fig.add_trace(go.Bar(
        name='Gasto Real',
        x=df_grafico['nome'],
        y=df_grafico['gasto'],
        marker_color='darkblue'
    ))
    
    fig.update_layout(
        barmode='overlay',
        height=400,
        title="Previsto vs Realizado",
        xaxis_title="Categorias",
        yaxis_title="Valor (R$)",
        template="plotly_dark"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def _show_grafico_evolucao(evolucao):
    """Exibe gráfico de evolução mensal"""
    st.markdown("### 📈 Evolução Mensal")
    
    if evolucao.empty:
        st.info("Dados insuficientes para evolução mensal")
        return
    
    # Converter mês para formato legível
    evolucao['mes_nome'] = evolucao['mes'].apply(lambda x: 
        datetime.strptime(x, '%Y-%m').strftime('%b/%Y') if x else 'N/A'
    )
    
    fig = px.line(
        evolucao,
        x='mes_nome',
        y='total',
        title='Gastos Mensais',
        markers=True,
        template="plotly_dark"
    )
    
    fig.update_layout(
        height=400,
        xaxis_title="Mês",
        yaxis_title="Valor (R$)"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def _show_alertas_e_recentes(total_gasto, total_previsto_categorias, obra_config, ultimos):
    """Exibe alertas e lançamentos recentes - VERSÃO CORRIGIDA"""
    orcamento_obra = obra_config['orcamento_total']
    orcamento_referencia = orcamento_obra if orcamento_obra > 0 else total_previsto_categorias
    
    if orcamento_referencia > 0:
        percentual = (total_gasto / orcamento_referencia) * 100
        restante = orcamento_referencia - total_gasto
    else:
        percentual = 0
        restante = 0
    
    # Alertas
    st.markdown("### 🚨 Status do Orçamento")
    _show_alerts(percentual, restante)
    
    # Lançamentos recentes - CORRIGIDO
    st.markdown("### 📋 Últimos Lançamentos")
    
    if ultimos.empty:
        st.info("📭 Nenhum lançamento encontrado")
        
        # Debug - verificar se há dados no banco
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM lancamentos")
        total_lancamentos = cursor.fetchone()[0]
        conn.close()
        
        if total_lancamentos > 0:
            st.warning(f"⚠️ Há {total_lancamentos} lançamento(s) no banco, mas não aparecem aqui. Verificando...")
            
            # Buscar diretamente
            conn = get_db_connection()
            df_debug = pd.read_sql_query("""
                SELECT l.id, l.data, l.descricao, l.valor, c.nome as categoria, u.nome as usuario
                FROM lancamentos l
                LEFT JOIN categorias c ON l.categoria_id = c.id
                LEFT JOIN usuarios u ON l.usuario_id = u.id
                ORDER BY l.id DESC
                LIMIT 5
            """, conn)
            conn.close()
            
            if not df_debug.empty:
                st.markdown("**🔍 Lançamentos encontrados diretamente:**")
                for _, lanc in df_debug.iterrows():
                    # --- ALTERAÇÃO AQUI: Usando a nova função de formatação ---
                    st.write(f"• #{lanc['id']} - {lanc['descricao']} - R$ {format_currency_brl(lanc['valor'])}")
        
        return
    
    # Exibir últimos lançamentos
    for _, lancamento in ultimos.head(5).iterrows():
        with st.container():
            col1, col2, col3 = st.columns([2, 3, 2])
            
            with col1:
                st.write(f"**📅 {format_date_br(lancamento['data'])}**")
                st.caption(f"🆔 #{lancamento['id']}")
            
            with col2:
                st.write(f"📝 {lancamento['descricao']}")
                st.caption(f"🏷️ {lancamento['categoria']}")
            
            with col3:
                # --- ALTERAÇÃO AQUI: Usando a nova função de formatação ---
                st.write(f"**💰 R$ {format_currency_brl(lancamento['valor'])}**")
                st.caption(f"�� {lancamento['usuario']}")
            
            st.markdown("---")
            
def _show_alerts(percentual, restante):
    """Exibe alertas baseados no percentual gasto"""
    if percentual > 100:
        # --- ALTERAÇÃO AQUI: Usando a nova função de formatação ---
        st.error(f"🚨 **ATENÇÃO CRÍTICA**: Orçamento estourado em R$ {format_currency_brl(abs(restante))}!")
        st.markdown("""
        <div style="background: linear-gradient(135deg, #d32f2f 0%, #f44336 100%); 
                    padding: 1rem; border-radius: 8px; color: white; margin: 1rem 0;">
            <strong>⚠️ AÇÃO NECESSÁRIA:</strong> Revisar gastos imediatamente!
        </div>
        """, unsafe_allow_html=True)
    elif percentual > 90:
        # --- ALTERAÇÃO AQUI: Usando a nova função de formatação ---
        st.warning(f"⚠️ **CUIDADO**: Restam apenas R$ {format_currency_brl(restante)} do orçamento!")
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f57c00 0%, #ff9800 100%); 
                    padding: 1rem; border-radius: 8px; color: white; margin: 1rem 0;">
            <strong>📊 MONITORAMENTO:</strong> Acompanhar gastos de perto!
        </div>
        """, unsafe_allow_html=True)
    elif percentual > 80:
        st.info(f"💡 **ATENÇÃO**: Você já utilizou {percentual:.1f}% do orçamento.")
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1976d2 0%, #2196f3 100%); 
                    padding: 1rem; border-radius: 8px; color: white; margin: 1rem 0;">
            <strong>�� STATUS:</strong> Planejamento dentro do esperado!
        </div>
        """, unsafe_allow_html=True)
    else:
        st.success(f"✅ **EXCELENTE**: Apenas {percentual:.1f}% do orçamento utilizado!")
        st.markdown("""
        <div style="background: linear-gradient(135deg, #388e3c 0%, #4caf50 100%); 
                    padding: 1rem; border-radius: 8px; color: white; margin: 1rem 0;">
            <strong>🎯 PARABÉNS:</strong> Gestão financeira eficiente!
        </div>
        """, unsafe_allow_html=True)
