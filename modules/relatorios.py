import sys
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, date, timedelta
from io import BytesIO
import base64
from config.database import get_connection
from utils.helpers import get_dados_dashboard, get_obra_config, format_currency_br, format_date_br

def show_relatorios():
    """Exibe página de relatórios"""
    st.title("📈 Relatórios Financeiros")
    
    # Tabs para diferentes tipos de relatórios
    tab1, tab2, tab3 = st.tabs(["📊 Resumo Executivo", "📋 Detalhado por Período", "🔍 Análises Avançadas"])
    
    with tab1:
        _show_resumo_executivo()
    
    with tab2:
        _show_relatorio_detalhado()
    
    with tab3:
        _show_analises_avancadas()

def _show_resumo_executivo():
    """Relatório resumo executivo"""
    st.subheader("📊 Resumo Executivo")
    
    # Carrega dados
    dados = get_dados_dashboard()
    obra_config = get_obra_config()
    
    # Informações da obra
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏗️ Informações da Obra")
        st.write(f"**Nome:** {obra_config.get('nome', 'N/A')}")
        st.write(f"**Orçamento:** {format_currency_br(obra_config.get('orcamento', 0))}")
        if obra_config.get('data_inicio'):
            st.write(f"**Início:** {format_date_br(obra_config['data_inicio'])}")
        if obra_config.get('data_fim_prevista'):
            st.write(f"**Previsão de Término:** {format_date_br(obra_config['data_fim_prevista'])}")
    
    with col2:
        st.markdown("### 💰 Situação Financeira")
        st.write(f"**Total Gasto:** {format_currency_br(dados['total_gasto'])}")
        st.write(f"**Percentual Executado:** {dados['percentual_executado']:.1f}%")
        st.write(f"**Saldo Restante:** {format_currency_br(dados['saldo_restante'])}")
        
        # Status financeiro
        if dados['percentual_executado'] > 100:
            st.error("🚨 Orçamento estourado!")
        elif dados['percentual_executado'] > 90:
            st.warning("⚠️ Próximo do limite!")
        else:
            st.success("✅ Dentro do orçamento")
    
    st.markdown("---")
    
    # Gráficos principais
    col1, col2 = st.columns(2)
    
    with col1:
        _create_gastos_categoria_chart(dados['gastos_por_categoria'])
    
    with col2:
        _create_evolucao_mensal_chart()
    
    # Top 5 maiores gastos
    st.markdown("---")
    _show_top_gastos()
    
    # Botão para gerar PDF
    if st.button("📄 Gerar Relatório PDF", use_container_width=True):
        pdf_data = _generate_pdf_report(dados, obra_config)
        if pdf_data:
            st.download_button(
                label="⬇️ Baixar Relatório PDF",
                data=pdf_data,
                file_name=f"relatorio_executivo_{date.today().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )

def _show_relatorio_detalhado():
    """Relatório detalhado por período"""
    st.subheader("📋 Relatório Detalhado por Período")
    
    # Filtros de período
    col1, col2, col3 = st.columns(3)
    
    with col1:
        data_inicio = st.date_input(
            "Data Início",
            value=date.today() - timedelta(days=30)
        )
    
    with col2:
        data_fim = st.date_input(
            "Data Fim",
            value=date.today()
        )
    
    with col3:
        incluir_arquivos = st.checkbox("Incluir informações de arquivos", value=True)
    
    if data_inicio > data_fim:
        st.error("⚠️ A data de início deve ser anterior à data de fim!")
        return
    
    # Busca dados do período
    lancamentos = _get_lancamentos_periodo(data_inicio, data_fim)
    
    if not lancamentos:
        st.info("Nenhum lançamento encontrado no período selecionado.")
        return
    
    # Estatísticas do período
    total_periodo = sum(l['valor'] for l in lancamentos)
    media_diaria = total_periodo / ((data_fim - data_inicio).days + 1)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Total do Período", format_currency_br(total_periodo))
    
    with col2:
        st.metric("📊 Quantidade", f"{len(lancamentos)} lançamentos")
    
    with col3:
        st.metric("📈 Média Diária", format_currency_br(media_diaria))
    
    with col4:
        if lancamentos:
            maior_gasto = max(l['valor'] for l in lancamentos)
            st.metric("🔝 Maior Gasto", format_currency_br(maior_gasto))
    
    # Gráfico de gastos diários
    st.markdown("---")
    _create_gastos_diarios_chart(lancamentos, data_inicio, data_fim)
    
    # Tabela detalhada
    st.markdown("---")
    st.subheader("📋 Lançamentos do Período")
    
    # Converte para DataFrame
    df_lancamentos = pd.DataFrame(lancamentos)
    df_lancamentos['data_lancamento'] = pd.to_datetime(df_lancamentos['data_lancamento'])
    df_lancamentos['valor_formatado'] = df_lancamentos['valor'].apply(format_currency_br)
    df_lancamentos['data_formatada'] = df_lancamentos['data_lancamento'].dt.strftime('%d/%m/%Y')
    
    # Exibe tabela
    st.dataframe(
        df_lancamentos[['data_formatada', 'descricao', 'categoria_nome', 'valor_formatado']].rename(columns={
            'data_formatada': 'Data',
            'descricao': 'Descrição',
            'categoria_nome': 'Categoria',
            'valor_formatado': 'Valor'
        }),
        use_container_width=True,
        hide_index=True
    )
    
    # Exportar para Excel
    if st.button("📊 Exportar para Excel", use_container_width=True):
        excel_data = _generate_excel_report(df_lancamentos)
        if excel_data:
            st.download_button(
                label="⬇️ Baixar Planilha Excel",
                data=excel_data,
                file_name=f"relatorio_detalhado_{data_inicio.strftime('%Y%m%d')}_{data_fim.strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

def _show_analises_avancadas():
    """Análises avançadas e métricas"""
    st.subheader("🔍 Análises Avançadas")
    
    # Análise de tendências
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Análise de Tendências")
        _show_analise_tendencias()
    
    with col2:
        st.markdown("### 🎯 Projeções")
        _show_projecoes()
    
    st.markdown("---")
    
    # Análise por categoria
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏷️ Análise por Categoria")
        _show_analise_categorias()
    
    with col2:
        st.markdown("### ⚡ Métricas de Performance")
        _show_metricas_performance()

def _create_gastos_categoria_chart(gastos_categoria):
    """Cria gráfico de gastos por categoria"""
    st.markdown("### 📊 Distribuição por Categoria")
    
    if not gastos_categoria or not any(cat['valor'] > 0 for cat in gastos_categoria):
        st.info("Nenhum gasto registrado.")
        return
    
    # Filtra categorias com gastos
    categorias_com_gastos = [cat for cat in gastos_categoria if cat['valor'] > 0]
    
    # Cria gráfico
    fig = go.Figure(data=[go.Pie(
        labels=[cat['nome'] for cat in categorias_com_gastos],
        values=[cat['valor'] for cat in categorias_com_gastos],
        marker=dict(colors=[cat['cor'] for cat in categorias_com_gastos]),
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.2f}<br>Percentual: %{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        height=400,
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    
    st.plotly_chart(fig, use_container_width=True)

def _create_evolucao_mensal_chart():
    """Cria gráfico de evolução mensal"""
    st.markdown("### 📈 Evolução Mensal")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        if is_postgres:
            query = """
                SELECT 
                    DATE_TRUNC('month', data_lancamento) as mes,
                    SUM(valor) as total_mes
                FROM lancamentos l
                JOIN obras o ON l.obra_id = o.id
                WHERE o.ativo = TRUE
                GROUP BY DATE_TRUNC('month', data_lancamento)
                ORDER BY mes
            """
        else:
            query = """
                SELECT 
                    strftime('%Y-%m', data_lancamento) as mes,
                    SUM(valor) as total_mes
                FROM lancamentos l
                JOIN obras o ON l.obra_id = o.id
                WHERE o.ativo = 1
                GROUP BY strftime('%Y-%m', data_lancamento)
                ORDER BY mes
            """
        
        cursor.execute(query)
        resultados = cursor.fetchall()
        
        if not resultados:
            st.info("Nenhum dado disponível.")
            return
        
        # Prepara dados
        meses = []
        valores = []
        
        for row in resultados:
            if is_postgres:
                mes_str = row['mes'].strftime('%Y-%m')
            else:
                mes_str = row['mes']
            
            meses.append(mes_str)
            
            # Converte valor
            valor = 0.0
            try:
                if row['total_mes'] is not None:
                    from decimal import Decimal
                    if isinstance(row['total_mes'], Decimal):
                        valor = float(row['total_mes'])
                    else:
                        valor = float(row['total_mes'])
            except (TypeError, ValueError):
                valor = 0.0
            
            valores.append(valor)
        
        # Cria DataFrame
        df = pd.DataFrame({'Mês': meses, 'Valor': valores})
        df['Mês_Label'] = pd.to_datetime(df['Mês']).dt.strftime('%b/%Y')
        
        # Cria gráfico
        fig = px.line(df, x='Mês_Label', y='Valor', markers=True)
        fig.update_traces(line=dict(color='#1f77b4', width=3), marker=dict(size=8))
        fig.update_layout(
            height=400,
            margin=dict(t=20, b=20, l=20, r=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(gridcolor='#404040', title="Mês"),
            yaxis=dict(gridcolor='#404040', title="Valor (R$)", tickformat=',.0f')
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        print(f"Erro ao gerar gráfico de evolução: {repr(e)}", file=sys.stderr)
        st.error("Erro ao carregar dados do gráfico.")
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def _create_gastos_diarios_chart(lancamentos, data_inicio, data_fim):
    """Cria gráfico de gastos diários"""
    st.subheader("📊 Gastos Diários do Período")
    
    # Agrupa por data
    gastos_por_dia = {}
    for lancamento in lancamentos:
        data = lancamento['data_lancamento']
        if isinstance(data, str):
            data = datetime.strptime(data, '%Y-%m-%d').date()
        elif isinstance(data, datetime):
            data = data.date()
        
        if data not in gastos_por_dia:
            gastos_por_dia[data] = 0
        gastos_por_dia[data] += lancamento['valor']
    
    # Cria lista completa de datas (incluindo dias sem gastos)
    current_date = data_inicio
    all_dates = []
    all_values = []
    
    while current_date <= data_fim:
        all_dates.append(current_date)
        all_values.append(gastos_por_dia.get(current_date, 0))
        current_date += timedelta(days=1)
    
    # Cria DataFrame
    df = pd.DataFrame({
        'Data': all_dates,
        'Valor': all_values
    })
    
    # Cria gráfico
    fig = px.bar(df, x='Data', y='Valor')
    fig.update_traces(marker_color='#1f77b4')
    fig.update_layout(
        height=400,
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(gridcolor='#404040', title="Data"),
        yaxis=dict(gridcolor='#404040', title="Valor (R$)", tickformat=',.0f')
    )
    
    st.plotly_chart(fig, use_container_width=True)

def _show_top_gastos():
    """Exibe top 5 maiores gastos"""
    st.subheader("🔝 Top 5 Maiores Gastos")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        query = """
            SELECT 
                l.descricao, l.valor, l.data_lancamento,
                c.nome as categoria_nome, c.cor as categoria_cor
            FROM lancamentos l
            JOIN categorias c ON l.categoria_id = c.id
            JOIN obras o ON l.obra_id = o.id
            WHERE o.ativo = %s
            ORDER BY l.valor DESC
            LIMIT 5
        """ if is_postgres else """
            SELECT 
                l.descricao, l.valor, l.data_lancamento,
                c.nome as categoria_nome, c.cor as categoria_cor
            FROM lancamentos l
            JOIN categorias c ON l.categoria_id = c.id
            JOIN obras o ON l.obra_id = o.id
            WHERE o.ativo = ?
            ORDER BY l.valor DESC
            LIMIT 5
        """
        
        cursor.execute(query, (True if is_postgres else 1,))
        resultados = cursor.fetchall()
        
        if not resultados:
            st.info("Nenhum lançamento encontrado.")
            return
        
        for i, row in enumerate(resultados, 1):
            # Converte valor
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
            
            col1, col2, col3 = st.columns([1, 3, 2])
            
            with col1:
                st.markdown(f"**#{i}**")
            
            with col2:
                st.write(f"**{row['descricao']}**")
                st.caption(f"🏷️ {row['categoria_nome']}")
            
            with col3:
                st.write(format_currency_br(valor))
                st.caption(f"📅 {format_date_br(row['data_lancamento'])}")
        
    except Exception as e:
        print(f"Erro ao buscar top gastos: {repr(e)}", file=sys.stderr)
        st.error("Erro ao carregar dados.")
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def _show_analise_tendencias():
    """Mostra análise de tendências"""
    # Implementação simplificada
    st.info("📈 Análise de tendências em desenvolvimento")

def _show_projecoes():
    """Mostra projeções financeiras"""
    dados = get_dados_dashboard()
    obra_config = get_obra_config()
    
    if dados['total_gasto'] > 0 and obra_config.get('data_fim_prevista'):
        # Calcula projeção simples
        dias_decorridos = (date.today() - obra_config.get('data_inicio', date.today())).days
        dias_totais = (obra_config['data_fim_prevista'] - obra_config.get('data_inicio', date.today())).days
        
        if dias_decorridos > 0 and dias_totais > 0:
            percentual_tempo = dias_decorridos / dias_totais
            gasto_projetado = dados['total_gasto'] / percentual_tempo if percentual_tempo > 0 else 0
            
            st.metric("💰 Gasto Projetado", format_currency_br(gasto_projetado))
            
            if gasto_projetado > obra_config.get('orcamento', 0):
                excesso = gasto_projetado - obra_config.get('orcamento', 0)
                st.error(f"⚠️ Projeção de estouro: {format_currency_br(excesso)}")
            else:
                economia = obra_config.get('orcamento', 0) - gasto_projetado
                st.success(f"✅ Economia projetada: {format_currency_br(economia)}")

def _show_analise_categorias():
    """Análise detalhada por categorias"""
    dados = get_dados_dashboard()
    
    if dados['gastos_por_categoria']:
        categoria_dominante = max(dados['gastos_por_categoria'], key=lambda x: x['valor'])
        st.write(f"**Categoria dominante:** {categoria_dominante['nome']}")
        st.write(f"**Participação:** {categoria_dominante['percentual']:.1f}%")
        st.write(f"**Valor:** {format_currency_br(categoria_dominante['valor'])}")

def _show_metricas_performance():
    """Métricas de performance"""
    # Burn rate
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        # Gastos últimos 30 dias
        if is_postgres:
            query = """
                SELECT COALESCE(SUM(valor), 0) as total
                FROM lancamentos l
                JOIN obras o ON l.obra_id = o.id
                WHERE o.ativo = TRUE AND data_lancamento >= CURRENT_DATE - INTERVAL '30 days'
            """
        else:
            query = """
                SELECT COALESCE(SUM(valor), 0) as total
                FROM lancamentos l
                JOIN obras o ON l.obra_id = o.id
                WHERE o.ativo = 1 AND data_lancamento >= date('now', '-30 days')
            """
        
        cursor.execute(query)
        result = cursor.fetchone()
        
        burn_rate = 0.0
        if result and result['total']:
            from decimal import Decimal
            if isinstance(result['total'], Decimal):
                burn_rate = float(result['total'])
            else:
                burn_rate = float(result['total'])
        
        st.metric("�� Burn Rate (30 dias)", format_currency_br(burn_rate))
        
        # Média por lançamento
        cursor.execute("""
            SELECT COUNT(*) as total_lancamentos, COALESCE(AVG(valor), 0) as media_valor
            FROM lancamentos l
            JOIN obras o ON l.obra_id = o.id
            WHERE o.ativo = %s
        """ if is_postgres else """
            SELECT COUNT(*) as total_lancamentos, COALESCE(AVG(valor), 0) as media_valor
            FROM lancamentos l
            JOIN obras o ON l.obra_id = o.id
            WHERE o.ativo = ?
        """, (True if is_postgres else 1,))
        
        result = cursor.fetchone()
        if result:
            media_valor = 0.0
            try:
                if result['media_valor'] is not None:
                    from decimal import Decimal
                    if isinstance(result['media_valor'], Decimal):
                        media_valor = float(result['media_valor'])
                    else:
                        media_valor = float(result['media_valor'])
            except (TypeError, ValueError):
                media_valor = 0.0
            
            st.metric("📊 Média por Lançamento", format_currency_br(media_valor))
            st.metric("📈 Total de Lançamentos", f"{result['total_lancamentos']}")
        
    except Exception as e:
        print(f"Erro ao calcular métricas: {repr(e)}", file=sys.stderr)
        st.error("Erro ao calcular métricas.")
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def _get_lancamentos_periodo(data_inicio, data_fim):
    """Busca lançamentos de um período"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        query = """
            SELECT 
                l.id, l.descricao, l.valor, l.data_lancamento, l.observacoes,
                c.nome as categoria_nome, c.cor as categoria_cor
            FROM lancamentos l
            JOIN categorias c ON l.categoria_id = c.id
            JOIN obras o ON l.obra_id = o.id
            WHERE o.ativo = %s AND l.data_lancamento BETWEEN %s AND %s
            ORDER BY l.data_lancamento DESC
        """ if is_postgres else """
            SELECT 
                l.id, l.descricao, l.valor, l.data_lancamento, l.observacoes,
                c.nome as categoria_nome, c.cor as categoria_cor
            FROM lancamentos l
            JOIN categorias c ON l.categoria_id = c.id
            JOIN obras o ON l.obra_id = o.id
            WHERE o.ativo = ? AND l.data_lancamento BETWEEN ? AND ?
            ORDER BY l.data_lancamento DESC
        """
        
        cursor.execute(query, (True if is_postgres else 1, data_inicio, data_fim))
        
        lancamentos = []
        for row in cursor.fetchall():
            # Converte valor
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
            
            lancamentos.append({
                'id': row['id'],
                'descricao': row['descricao'],
                'valor': valor,
                'data_lancamento': row['data_lancamento'],
                'observacoes': row['observacoes'],
                'categoria_nome': row['categoria_nome'],
                'categoria_cor': row['categoria_cor']
            })
        
        return lancamentos
        
    except Exception as e:
        print(f"Erro ao buscar lançamentos do período: {repr(e)}", file=sys.stderr)
        return []
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def _generate_pdf_report(dados, obra_config):
    """Gera relatório em PDF (implementação simplificada)"""
    # Por simplicidade, retorna None
    # Em uma implementação completa, usaria bibliotecas como reportlab
    st.info("📄 Geração de PDF em desenvolvimento")
    return None

def _generate_excel_report(df_lancamentos):
    """Gera relatório em Excel"""
    try:
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Aba principal com lançamentos
            df_export = df_lancamentos[['data_formatada', 'descricao', 'categoria_nome', 'valor']].copy()
            df_export.columns = ['Data', 'Descrição', 'Categoria', 'Valor']
            df_export.to_excel(writer, sheet_name='Lançamentos', index=False)
            
            # Aba com resumo por categoria
            resumo_categoria = df_lancamentos.groupby('categoria_nome')['valor'].agg(['sum', 'count', 'mean']).reset_index()
            resumo_categoria.columns = ['Categoria', 'Total', 'Quantidade', 'Média']
            resumo_categoria['Total'] = resumo_categoria['Total'].apply(lambda x: f"R$ {x:,.2f}")
            resumo_categoria['Média'] = resumo_categoria['Média'].apply(lambda x: f"R$ {x:,.2f}")
            resumo_categoria.to_excel(writer, sheet_name='Resumo por Categoria', index=False)
        
        return output.getvalue()
        
    except Exception as e:
        print(f"Erro ao gerar Excel: {repr(e)}", file=sys.stderr)
        st.error("Erro ao gerar arquivo Excel.")
        return None