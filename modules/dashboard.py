import sys
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from utils.helpers import get_dados_dashboard, get_obra_config, format_currency_br, format_date_br
from config.database import get_connection

def show_dashboard():
    """Exibe página do dashboard principal"""
    st.title("📊 Dashboard Financeiro")
    
    # Carrega dados
    dados = get_dados_dashboard()
    obra_config = get_obra_config()
    
    # Métricas principais
    show_main_metrics(dados, obra_config)
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        show_gastos_por_categoria(dados['gastos_por_categoria'])
    
    with col2:
        show_evolucao_gastos()
    
    st.markdown("---")
    
    # Últimos lançamentos e alertas
    col1, col2 = st.columns([2, 1])
    
    with col1:
        show_ultimos_lancamentos(dados['ultimos_lancamentos'])
    
    with col2:
        show_alertas_financeiros(dados)

def show_main_metrics(dados, obra_config):
    """Exibe métricas principais em cards"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💰 Total Gasto",
            value=format_currency_br(dados['total_gasto']),
            delta=None
        )
    
    with col2:
        st.metric(
            label="🎯 Orçamento Total",
            value=format_currency_br(dados['orcamento']),
            delta=None
        )
    
    with col3:
        percentual = dados['percentual_executado']
        delta_color = "normal" if percentual <= 80 else "inverse"
        st.metric(
            label="📈 % Executado",
            value=f"{percentual:.1f}%",
            delta=f"{percentual - 50:.1f}%" if percentual > 50 else None,
            delta_color=delta_color
        )
    
    with col4:
        saldo = dados['saldo_restante']
        delta_color = "normal" if saldo > 0 else "inverse"
        st.metric(
            label="💳 Saldo Restante",
            value=format_currency_br(saldo),
            delta=format_currency_br(saldo - dados['orcamento']/2) if dados['orcamento'] > 0 else None,
            delta_color=delta_color
        )
    
    # Barra de progresso do orçamento
    if dados['orcamento'] > 0:
        progress = min(dados['percentual_executado'] / 100, 1.0)
        st.progress(progress)
        
        # Alerta se estiver próximo do limite
        if dados['percentual_executado'] > 90:
            st.error("🚨 Atenção: Mais de 90% do orçamento já foi utilizado!")
        elif dados['percentual_executado'] > 80:
            st.warning("⚠️ Cuidado: Mais de 80% do orçamento já foi utilizado!")

def show_gastos_por_categoria(gastos_categoria):
    """Exibe gráfico de gastos por categoria"""
    st.subheader("📊 Gastos por Categoria")
    
    if not gastos_categoria:
        st.info("Nenhum gasto registrado ainda.")
        return
    
    # Filtra categorias com gastos > 0
    categorias_com_gastos = [cat for cat in gastos_categoria if cat['valor'] > 0]
    
    if not categorias_com_gastos:
        st.info("Nenhum gasto registrado ainda.")
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
        textinfo='label+percent',
        textposition='auto',
        hovertemplate='<b>%{label}</b><br>' +
                      'Valor: R\$ %{value:,.2f}<br>' +
                      'Percentual: %{percent}<br>' +
                      '<extra></extra>'
    )])
    
    fig.update_layout(
        showlegend=True,
        height=400,
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_evolucao_gastos():
    """Exibe gráfico de evolução dos gastos mensais"""
    st.subheader("📈 Evolução Mensal dos Gastos")
    
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
            st.info("Nenhum dado disponível para o gráfico.")
            return
        
        # Prepara dados
        meses = []
        valores = []
        
        for row in resultados:
            if is_postgres:
                # PostgreSQL retorna datetime
                mes_str = row['mes'].strftime('%Y-%m')
            else:
                # SQLite retorna string
                mes_str = row['mes']
            
            meses.append(mes_str)
            
            # Converte valor para float
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
        df = pd.DataFrame({
            'Mês': meses,
            'Valor': valores
        })
        
        # Converte mês para formato mais legível
        df['Mês_Label'] = pd.to_datetime(df['Mês']).dt.strftime('%b/%Y')
        
        # Cria gráfico de linha
        fig = px.line(
            df, 
            x='Mês_Label', 
            y='Valor',
            title='',
            markers=True
        )
        
        fig.update_traces(
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8, color='#1f77b4')
        )
        
        fig.update_layout(
            xaxis_title="Mês",
            yaxis_title="Valor (R\$)",
            height=400,
            margin=dict(t=20, b=20, l=20, r=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(gridcolor='#404040'),
            yaxis=dict(gridcolor='#404040')
        )
        
        # Formata valores no eixo Y
        fig.update_yaxis(tickformat=',.0f')
        
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

def show_ultimos_lancamentos(lancamentos):
    """Exibe lista dos últimos lançamentos"""
    st.subheader("📋 Últimos Lançamentos")
    
    if not lancamentos:
        st.info("Nenhum lançamento registrado ainda.")
        return
    
    for lancamento in lancamentos:
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.write(f"**{lancamento['descricao']}**")
                st.caption(f"🏷️ {lancamento['categoria_nome']}")
            
            with col2:
                st.write(format_currency_br(lancamento['valor']))
                st.caption(f"📅 {format_date_br(lancamento['data_lancamento'])}")
            
            with col3:
                # Indicador colorido da categoria
                cor = lancamento.get('categoria_cor', '#3498db')
                st.markdown(
                    f'<div style="width: 20px; height: 20px; background-color: {cor}; '
                    f'border-radius: 50%; margin: auto;"></div>',
                    unsafe_allow_html=True
                )
            
            st.divider()

def show_alertas_financeiros(dados):
    """Exibe alertas e notificações financeiras"""
    st.subheader("🚨 Alertas Financeiros")
    
    alertas = []
    
    # Verifica percentual do orçamento
    percentual = dados['percentual_executado']
    
    if percentual > 95:
        alertas.append({
            'tipo': 'error',
            'icone': '🚨',
            'titulo': 'Orçamento Crítico',
            'mensagem': f'Mais de 95% do orçamento utilizado ({percentual:.1f}%)'
        })
    elif percentual > 80:
        alertas.append({
            'tipo': 'warning',
            'icone': '⚠️',
            'titulo': 'Atenção ao Orçamento',
            'mensagem': f'{percentual:.1f}% do orçamento já utilizado'
        })
    
    # Verifica categorias com muito gasto
    for categoria in dados['gastos_por_categoria']:
        if categoria['percentual'] > 40:
            alertas.append({
                'tipo': 'info',
                'icone': '📊',
                'titulo': 'Categoria Dominante',
                'mensagem': f'{categoria["nome"]}: {categoria["percentual"]:.1f}% dos gastos'
            })
    
    # Verifica saldo negativo
    if dados['saldo_restante'] < 0:
        alertas.append({
            'tipo': 'error',
            'icone': '💸',
            'titulo': 'Orçamento Estourado',
            'mensagem': f'Déficit de {format_currency_br(abs(dados["saldo_restante"]))}'
        })
    
    # Exibe alertas
    if alertas:
        for alerta in alertas[:5]:  # Máximo 5 alertas
            if alerta['tipo'] == 'error':
                st.error(f"{alerta['icone']} **{alerta['titulo']}**\n\n{alerta['mensagem']}")
            elif alerta['tipo'] == 'warning':
                st.warning(f"{alerta['icone']} **{alerta['titulo']}**\n\n{alerta['mensagem']}")
            else:
                st.info(f"{alerta['icone']} **{alerta['titulo']}**\n\n{alerta['mensagem']}")
    else:
        st.success("✅ **Tudo em Ordem**\n\nNenhum alerta financeiro no momento.")
    
    # Resumo rápido
    st.markdown("---")
    st.markdown("### 📈 Resumo Rápido")
    
    # Velocidade de queima (burn rate)
    try:
        burn_rate = calculate_burn_rate()
        if burn_rate > 0:
            st.metric("🔥 Burn Rate Mensal", format_currency_br(burn_rate))
        
        # Projeção de dias restantes
        if dados['saldo_restante'] > 0 and burn_rate > 0:
            dias_restantes = (dados['saldo_restante'] / burn_rate) * 30
            st.metric("⏰ Dias de Orçamento", f"{int(dias_restantes)} dias")
    
    except Exception as e:
        print(f"Erro ao calcular métricas avançadas: {repr(e)}", file=sys.stderr)

def calculate_burn_rate():
    """Calcula a velocidade de queima mensal (burn rate)"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Pega gastos dos últimos 30 dias
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        if is_postgres:
            query = """
                SELECT COALESCE(SUM(valor), 0) as total
                FROM lancamentos l
                JOIN obras o ON l.obra_id = o.id
                WHERE o.ativo = TRUE 
                AND data_lancamento >= CURRENT_DATE - INTERVAL '30 days'
            """
        else:
            query = """
                SELECT COALESCE(SUM(valor), 0) as total
                FROM lancamentos l
                JOIN obras o ON l.obra_id = o.id
                WHERE o.ativo = 1 
                AND data_lancamento >= date('now', '-30 days')
            """
        
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result and result['total']:
            from decimal import Decimal
            if isinstance(result['total'], Decimal):
                return float(result['total'])
            else:
                return float(result['total'])
        
        return 0.0
        
    except Exception as e:
        print(f"Erro ao calcular burn rate: {repr(e)}", file=sys.stderr)
        return 0.0
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass