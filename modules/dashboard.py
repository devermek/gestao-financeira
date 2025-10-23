import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
from config.database import get_db_connection
from utils.helpers import get_obra_config, format_currency_br, format_date_br, get_dados_dashboard

def show_dashboard(user, obra_config):
    """Exibe o dashboard principal da aplicação"""
    st.header("📊 Dashboard Principal")

    # Verifica se a configuração da obra existe
    if not obra_config or obra_config.get('nome_obra') is None:
        st.warning("⚠️ Por favor, configure os dados da obra na seção 'Configurações' para ter um dashboard completo.")
        # Podemos retornar ou mostrar um dashboard mais simples
        return

    # Obter dados do dashboard da função centralizada em helpers
    # AGORA RETORNA UM DICIONÁRIO, NÃO UMA TUPLA PARA DESCOMPACTAR
    dados = get_dados_dashboard()

    # Extrair os dados do dicionário
    total_gasto = dados['total_gasto']
    total_previsto_categorias = dados['total_previsto_categorias']
    gastos_categoria = dados['gastos_categoria']
    gastos_mensais = dados['gastos_mensais'] # Nome atualizado para corresponder à chave do dicionário
    lancamentos_recentes = dados['lancamentos_recentes'] # Nome atualizado para corresponder à chave do dicionário

    if total_gasto == 0:
        st.info("�� Ainda não há dados para gerar o dashboard. Adicione alguns lançamentos primeiro.")
        return

    # Métricas principais
    orcamento_obra = obra_config['orcamento_total']
    # Se o orçamento da obra for 0, usa o total previsto das categorias para o percentual
    orcamento_referencia = orcamento_obra if orcamento_obra > 0 else total_previsto_categorias
    percentual_executado = (total_gasto / orcamento_referencia * 100) if orcamento_referencia > 0 else 0

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("💰 Total Investido", format_currency_br(total_gasto))
        st.metric("📊 Orçamento Total", format_currency_br(orcamento_referencia))

    with col2:
        st.metric("📈 % Executado", f"{percentual_executado:.1f}%")
        saldo_restante = orcamento_referencia - total_gasto
        st.metric("💵 Saldo Restante", format_currency_br(saldo_restante))
    
    with col3:
        # Buscar estatísticas adicionais (similar ao relatorios.py, mas aqui para o dashboard)
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM lancamentos")
        total_lancamentos_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT categoria_id) FROM lancamentos")
        categorias_usadas_count = cursor.fetchone()[0]
        
        conn.close()
        
        st.metric("�� Total de Lançamentos", total_lancamentos_count)
        st.metric("🏷️ Categorias Utilizadas", categorias_usadas_count)


    # Alertas automáticos
    st.markdown("---")
    if percentual_executado >= 90 and saldo_restante <= 0:
        st.error(f"🚨 ATENÇÃO: Orçamento estourado! {percentual_executado:.1f}% executado. Saldo: {format_currency_br(saldo_restante)}")
    elif percentual_executado >= 80:
        st.warning(f"⚠️ Alerta: {percentual_executado:.1f}% do orçamento executado. Saldo restante: {format_currency_br(saldo_restante)}")
    elif percentual_executado >= 100:
        st.success(f"✅ Orçamento totalmente executado! {percentual_executado:.1f}% executado.")

    st.markdown("---")
    # Gráfico de pizza - Distribuição por categoria
    st.markdown("### 🥧 Distribuição de Gastos por Categoria")
    if not gastos_categoria.empty and not gastos_categoria[gastos_categoria['gasto'] > 0].empty:
        df_gastos_pie = gastos_categoria[gastos_categoria['gasto'] > 0].copy()
        fig_pie = px.pie(
            df_gastos_pie,
            values='gasto',
            names='nome',
            title="Distribuição dos Gastos",
            template="plotly_dark"
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Nenhum gasto registrado em categorias para exibir o gráfico.")

    st.markdown("---")
    # Gráfico de linha - Evolução Mensal de Gastos
    st.markdown("### 📈 Evolução Mensal de Gastos")
    if not gastos_mensais.empty: # Variável atualizada
        fig_line = px.line(
            gastos_mensais, # Variável atualizada
            x='mes',
            y='total',
            title="Gastos por Mês",
            markers=True,
            template="plotly_dark"
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Nenhum dado de evolução mensal para exibir o gráfico.")

    st.markdown("---")
    # Últimos lançamentos em tempo real
    st.markdown("### 📝 Últimos Lançamentos")
    if not lancamentos_recentes.empty: # Variável atualizada
        # Preparar dados para exibição
        df_display = lancamentos_recentes.copy() # Variável atualizada
        df_display['data'] = df_display['data'].apply(format_date_br)
        df_display['valor'] = df_display['valor'].apply(format_currency_br)
        
        # Limitar descrição
        df_display['descricao'] = df_display['descricao'].apply(
            lambda x: x[:50] + "..." if len(x) > 50 else x
        )
        
        # Selecionar colunas para exibição
        colunas_exibir = ['data', 'categoria', 'descricao', 'valor']
        df_display = df_display[colunas_exibir]
        df_display.columns = ['Data', 'Categoria', 'Descrição', 'Valor']

        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum lançamento recente para exibir.")
