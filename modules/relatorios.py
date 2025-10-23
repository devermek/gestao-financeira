import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
from utils.helpers import get_dados_dashboard, format_date_br, format_currency_br # Adicionado format_currency_br
from utils.pdf_generator import gerar_relatorio_pdf
from config.database import get_db_connection

def show_relatorios(user, obra_config):
    """Exibe página de relatórios"""
    st.header("📊 Relatórios e Análises")
    
    # Tabs para diferentes tipos de relatório
    tab1, tab2, tab3, tab4 = st.tabs(["�� Resumo Executivo", "📋 Detalhado", "📊 Análises", "�� PDF"])
    
    with tab1:
        _show_resumo_executivo(obra_config)
    
    with tab2:
        _show_relatorio_detalhado()
    
    with tab3:
        _show_analises_avancadas()
    
    with tab4:
        _show_geracao_pdf(user, obra_config)

def _show_resumo_executivo(obra_config):
    """Exibe resumo executivo da obra"""
    st.subheader("�� Resumo Executivo")
    
    # Buscar dados do dashboard usando a função centralizada que retorna um dicionário
    dados = get_dados_dashboard()
    
    # Extrair os dados necessários do dicionário
    total_gasto = dados['total_gasto']
    total_previsto_categorias = dados['total_previsto_categorias']
    gastos_categoria = dados['gastos_categoria']
    # 'gastos_mensais' e 'lancamentos_recentes' não são usados diretamente aqui no resumo,
    # mas estão disponíveis em 'dados' se necessário em outras partes ou no gerador de PDF.
    
    if total_gasto == 0:
        st.info("📊 Ainda não há dados para gerar relatórios. Adicione alguns lançamentos primeiro.")
        return
    
    # Métricas principais
    orcamento_obra = obra_config['orcamento_total']
    orcamento_referencia = orcamento_obra if orcamento_obra > 0 else total_previsto_categorias
    percentual = (total_gasto / orcamento_referencia * 100) if orcamento_referencia > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💰 Total Investido", format_currency_br(total_gasto))
        st.metric("�� Orçamento Total", format_currency_br(orcamento_referencia))
    
    with col2:
        st.metric("📈 % Executado", f"{percentual:.1f}%")
        restante = orcamento_referencia - total_gasto
        st.metric("�� Saldo Restante", format_currency_br(restante))
    
    with col3:
        # Buscar estatísticas adicionais
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM lancamentos")
        total_lancamentos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT categoria_id) FROM lancamentos")
        categorias_usadas = cursor.fetchone()[0]
        
        conn.close()
        
        st.metric("📝 Total de Lançamentos", total_lancamentos)
        st.metric("🏷️ Categorias Utilizadas", categorias_usadas)
    
    # Gráfico de pizza - Distribuição por categoria
    st.markdown("### 🥧 Distribuição de Gastos por Categoria")
    
    if not gastos_categoria.empty:
        # Filtrar apenas categorias com gastos (coluna 'gasto' em vez de 'total' agora)
        df_gastos = gastos_categoria[gastos_categoria['gasto'] > 0].copy()
        
        if not df_gastos.empty:
            fig = px.pie(
                df_gastos,
                values='gasto', # Coluna 'gasto'
                names='nome',
                title="Distribuição dos Gastos",
                template="plotly_dark"
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhum gasto registrado ainda")
    
    # Top 5 maiores gastos
    st.markdown("### 🔝 Top 5 Maiores Gastos")
    
    conn, db_type = get_db_connection()
    top_gastos = pd.read_sql_query("""
        SELECT 
            l.descricao,
            l.valor,
            l.data,
            c.nome as categoria
        FROM lancamentos l
        LEFT JOIN categorias c ON l.categoria_id = c.id
        ORDER BY l.valor DESC
        LIMIT 5
    """, conn)
    conn.close()
    
    if not top_gastos.empty:
        for i, gasto in top_gastos.iterrows():
            col1, col2, col3 = st.columns([3, 2, 2])
            
            with col1:
                st.write(f"**{gasto['descricao']}**")
            
            with col2:
                st.write(f"🏷️ {gasto['categoria']}")
            
            with col3:
                st.write(f"**💰 {format_currency_br(gasto['valor'])}**") # Usando format_currency_br
                st.caption(f"📅 {format_date_br(gasto['data'])}")

def _show_relatorio_detalhado():
    """Exibe relatório detalhado com filtros"""
    st.subheader("📋 Relatório Detalhado")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        data_inicio = st.date_input("📅 Data Início", value=date.today() - timedelta(days=30))
    
    with col2:
        data_fim = st.date_input("📅 Data Fim", value=date.today())
    
    with col3:
        # Buscar categorias
        conn, db_type = get_db_connection()
        categorias = pd.read_sql_query("SELECT nome FROM categorias WHERE ativo = 1", conn)
        categoria_filtro = st.selectbox(
            "🏷️ Categoria",
            options=["Todas"] + categorias['nome'].tolist()
        )
        conn.close()
    
    # Buscar dados filtrados
    conn, db_type = get_db_connection()
    
    query = """
        SELECT 
            l.id,
            l.data,
            l.descricao,
            l.valor,
            l.observacoes,
            c.nome as categoria,
            u.nome as usuario,
            l.created_at
        FROM lancamentos l
        LEFT JOIN categorias c ON l.categoria_id = c.id
        LEFT JOIN usuarios u ON l.usuario_id = u.id
        WHERE l.data BETWEEN ? AND ?
    """
    params = [data_inicio, data_fim]
    
    if categoria_filtro != "Todas":
        query += " AND c.nome = ?"
        params.append(categoria_filtro)
    
    query += " ORDER BY l.data DESC"
    
    # Ajustar placeholders para PostgreSQL se necessário
    if db_type == 'postgresql':
        query = query.replace('?', '%s')
        df_lancamentos = pd.read_sql_query(query, conn, params=tuple(params))
    else: # sqlite
        df_lancamentos = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    if df_lancamentos.empty:
        st.info("📭 Nenhum lançamento encontrado no período selecionado")
        return
    
    # Resumo do período
    total_periodo = df_lancamentos['valor'].sum()
    media_diaria = total_periodo / ((data_fim - data_inicio).days + 1)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("�� Total do Período", format_currency_br(total_periodo)) # Usando format_currency_br
    with col2:
        st.metric("📊 Média Diária", format_currency_br(media_diaria)) # Usando format_currency_br
    with col3:
        st.metric("📝 Lançamentos", len(df_lancamentos))
    
    # Tabela detalhada
    st.markdown("### 📋 Lançamentos do Período")
    
    # Preparar dados para exibição
    df_display = df_lancamentos.copy()
    df_display['data'] = df_display['data'].apply(format_date_br)
    df_display['valor'] = df_display['valor'].apply(format_currency_br) # Usando format_currency_br
    
    # Limitar descrição
    df_display['descricao'] = df_display['descricao'].apply(
        lambda x: x[:60] + "..." if len(x) > 60 else x
    )
    
    # Selecionar colunas para exibição
    colunas_exibir = ['data', 'categoria', 'descricao', 'valor', 'usuario']
    df_display = df_display[colunas_exibir]
    df_display.columns = ['Data', 'Categoria', 'Descrição', 'Valor', 'Usuário']
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)

def _show_analises_avancadas():
    """Exibe análises avançadas"""
    st.subheader("📊 Análises Avançadas")
    
    # Buscar dados
    conn, db_type = get_db_connection()
    
    # Análise por dia da semana
    # Ajuste para compatibilidade de strftime entre SQLite e PostgreSQL
    if db_type == 'sqlite':
        day_of_week_sql = """
            SELECT 
                CASE strftime('%w', data)
                    WHEN '0' THEN 'Domingo'
                    WHEN '1' THEN 'Segunda'
                    WHEN '2' THEN 'Terça'
                    WHEN '3' THEN 'Quarta'
                    WHEN '4' THEN 'Quinta'
                    WHEN '5' THEN 'Sexta'
                    WHEN '6' THEN 'Sábado'
                END as dia_semana,
                COUNT(*) as quantidade,
                SUM(valor) as total
            FROM lancamentos
            GROUP BY strftime('%w', data)
            ORDER BY strftime('%w', data)
        """
        month_sql = """
            SELECT 
                strftime('%Y-%m', data) as mes,
                COUNT(*) as quantidade,
                SUM(valor) as total,
                AVG(valor) as media
            FROM lancamentos
            GROUP BY strftime('%Y-%m', data)
            ORDER BY mes DESC
            LIMIT 12
        """
    else: # PostgreSQL
        day_of_week_sql = """
            SELECT 
                CASE EXTRACT(DOW FROM data)
                    WHEN 0 THEN 'Domingo'
                    WHEN 1 THEN 'Segunda'
                    WHEN 2 THEN 'Terça'
                    WHEN 3 THEN 'Quarta'
                    WHEN 4 THEN 'Quinta'
                    WHEN 5 THEN 'Sexta'
                    WHEN 6 THEN 'Sábado'
                END as dia_semana,
                COUNT(*) as quantidade,
                SUM(valor) as total
            FROM lancamentos
            GROUP BY EXTRACT(DOW FROM data)
            ORDER BY EXTRACT(DOW FROM data)
        """
        month_sql = """
            SELECT 
                TO_CHAR(data, 'YYYY-MM') as mes,
                COUNT(*) as quantidade,
                SUM(valor) as total,
                AVG(valor) as media
            FROM lancamentos
            GROUP BY TO_CHAR(data, 'YYYY-MM')
            ORDER BY mes DESC
            LIMIT 12
        """

    df_dias = pd.read_sql_query(day_of_week_sql, conn)
    df_mensal = pd.read_sql_query(month_sql, conn)
    
    conn.close()
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        if not df_dias.empty:
            st.markdown("#### �� Gastos por Dia da Semana")
            fig = px.bar(
                df_dias,
                x='dia_semana',
                y='total',
                title="Total por Dia da Semana",
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if not df_mensal.empty:
            st.markdown("#### �� Evolução Mensal")
            fig = px.line(
                df_mensal,
                x='mes',
                y='total',
                title="Gastos por Mês",
                markers=True,
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Tabela de análise mensal
    if not df_mensal.empty:
        st.markdown("#### 📊 Resumo Mensal")
        
        df_mensal_display = df_mensal.copy()
        df_mensal_display['mes'] = df_mensal_display['mes'].apply(
            lambda x: datetime.strptime(x, '%Y-%m').strftime('%B/%Y')
        )
        df_mensal_display['total'] = df_mensal_display['total'].apply(format_currency_br) # Usando format_currency_br
        df_mensal_display['media'] = df_mensal_display['media'].apply(format_currency_br) # Usando format_currency_br
        
        df_mensal_display.columns = ['Mês', 'Qtd Lançamentos', 'Total Gasto', 'Média por Lançamento']
        
        st.dataframe(df_mensal_display, use_container_width=True, hide_index=True)

def _show_geracao_pdf(user, obra_config):
    """Exibe opções para gerar PDF"""
    st.subheader("📄 Gerar Relatório PDF")
    
    # Opções de relatório
    col1, col2 = st.columns(2)
    
    with col1:
        tipo_relatorio = st.selectbox(
            "�� Tipo de Relatório",
            ["Resumo Executivo", "Detalhado por Período", "Análise por Categoria"]
        )
    
    with col2:
        incluir_graficos = st.checkbox("📊 Incluir Gráficos", value=True)
    
    # Filtros para relatório detalhado
    if tipo_relatorio == "Detalhado por Período":
        col1, col2 = st.columns(2)
        
        with col1:
            data_inicio = st.date_input("📅 Data Início", value=date.today() - timedelta(days=30))
        
        with col2:
            data_fim = st.date_input("📅 Data Fim", value=date.today())
    else:
        data_inicio = None
        data_fim = None
    
    # Botão para gerar PDF
    if st.button("📄 Gerar Relatório PDF", type="primary"):
        try:
            with st.spinner("Gerando relatório PDF..."):
                pdf_buffer = gerar_relatorio_pdf(
                    obra_config,
                    tipo_relatorio,
                    data_inicio,
                    data_fim,
                    incluir_graficos,
                    user
                )
            
            if pdf_buffer:
                st.success("✅ Relatório gerado com sucesso!")
                
                # Download do PDF
                st.download_button(
                    label="📥 Baixar Relatório PDF",
                    data=pdf_buffer,
                    file_name=f"relatorio_obra_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("❌ Erro ao gerar relatório PDF")
                
        except Exception as e:
            st.error(f"❌ Erro ao gerar PDF: {str(e)}")
