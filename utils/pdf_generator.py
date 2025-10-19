import io
import pandas as pd
#import matplotlib.pyplot as plt # Temporariamente desativado
#import matplotlib              # Temporariamente desativado
#matplotlib.use('Agg')          # Temporariamente desativado
#import seaborn as sns          # Temporariamente desativado
from datetime import datetime, date
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from config.database import get_db_connection
from utils.helpers import format_date_br, get_dados_dashboard

# Configurações de estilo de gráfico (temporariamente desativadas)
# plt.style.use('dark_background')
# sns.set_theme(style="darkgrid")

def gerar_relatorio_pdf(obra_config, tipo_relatorio, data_inicio=None, data_fim=None, incluir_graficos=True, user=None):
    """Gera relatório PDF baseado nos parâmetros"""
    try:
        # Criar buffer para o PDF
        buffer = io.BytesIO()

        # Configurar documento
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )

        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )

        # Conteúdo do PDF
        story = []

        # Cabeçalho
        story.append(Paragraph(f"🏗️ {obra_config['nome_obra']}", title_style))
        story.append(Paragraph(f"Relatório: {tipo_relatorio}", heading_style))
        story.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", styles['Normal']))

        if user:
            story.append(Paragraph(f"Usuário: {user['nome']} ({user['tipo'].title()})", styles['Normal']))

        story.append(Spacer(1, 20))

        # Gerar conteúdo baseado no tipo
        if tipo_relatorio == "Resumo Executivo":
            # Passamos False para 'incluir_graficos' para desabilitar a geração nesta etapa
            _add_resumo_executivo(story, styles, obra_config, False)
        elif tipo_relatorio == "Detalhado por Período":
            # Passamos False para 'incluir_graficos' para desabilitar a geração nesta etapa
            _add_relatorio_detalhado(story, styles, data_inicio, data_fim, False)
        elif tipo_relatorio == "Análise por Categoria":
            # Passamos False para 'incluir_graficos' para desabilitar a geração nesta etapa
            _add_analise_categoria(story, styles, False)

        # Rodapé
        story.append(Spacer(1, 30))
        story.append(Paragraph("Sistema de Gestão de Obras - Relatório Automatizado", styles['Normal']))

        # Construir PDF
        doc.build(story)

        # Retornar buffer
        buffer.seek(0)
        return buffer.getvalue()

    except Exception as e:
        print(f"Erro ao gerar PDF: {e}")
        return None

def _create_chart_image(fig, width=6, height=4):
    """Converte gráfico matplotlib para imagem para o PDF (temporariamente desativado)"""
    # Esta função está desativada enquanto os gráficos não são reativados.
    print("Geração de gráficos desativada temporariamente.")
    return None

def _add_resumo_executivo(story, styles, obra_config, incluir_graficos):
    """Adiciona resumo executivo ao PDF"""
    story.append(Paragraph("📊 RESUMO EXECUTIVO", styles['Heading2']))
    story.append(Spacer(1, 12))

    # Buscar dados
    total_gasto, total_previsto_categorias, gastos_categoria, evolucao, ultimos = get_dados_dashboard()

    # Métricas principais
    orcamento_obra = obra_config['orcamento_total']
    orcamento_referencia = orcamento_obra if orcamento_obra > 0 else total_previsto_categorias
    percentual = (total_gasto / orcamento_referencia * 100) if orcamento_referencia > 0 else 0
    restante = orcamento_referencia - total_gasto

    # Tabela de métricas
    dados_metricas = [
        ['Métrica', 'Valor'],
        ['Total Gasto', f'R$ {total_gasto:,.2f}'],
        ['Orçamento Total', f'R$ {orcamento_referencia:,.2f}'],
        ['% Executado', f'{percentual:.1f}%'],
        ['Saldo Restante', f'R$ {restante:,.2f}'],
    ]

    tabela_metricas = Table(dados_metricas, colWidths=[3*inch, 2*inch])
    tabela_metricas.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(tabela_metricas)
    story.append(Spacer(1, 20))

    # GRÁFICOS - se solicitado (Temporariamente desativado)
    if incluir_graficos and not gastos_categoria.empty:
        story.append(Paragraph("🚫 Geração de gráficos desativada temporariamente 🚫", styles['Normal']))
        story.append(Spacer(1, 20))
        # Todo o código de geração de gráficos foi comentado/removido para evitar erros de importação.
        # Será reativado em uma etapa futura.

    # Gastos por categoria (tabela)
    if not gastos_categoria.empty:
        story.append(Paragraph("�� GASTOS POR CATEGORIA", styles['Heading3']))
        story.append(Spacer(1, 12))

        dados_categoria = [['Categoria', 'Orçamento Previsto', 'Gasto Real', '% Utilizado']]

        for _, cat in gastos_categoria.iterrows():
            perc_cat = (cat['gasto'] / cat['orcamento_previsto'] * 100) if cat['orcamento_previsto'] > 0 else 0
            dados_categoria.append([
                cat['nome'],
                f"R$ {cat['orcamento_previsto']:,.2f}",
                f"R$ {cat['gasto']:,.2f}",
                f"{perc_cat:.1f}%"
            ])

        tabela_categoria = Table(dados_categoria, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1*inch])
        tabela_categoria.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(tabela_categoria)
        story.append(Spacer(1, 20))

    # Últimos lançamentos
    if not ultimos.empty:
        story.append(Paragraph("📋 ÚLTIMOS LANÇAMENTOS", styles['Heading3']))
        story.append(Spacer(1, 12))

        dados_ultimos = [['Data', 'Categoria', 'Descrição', 'Valor']]

        for _, lanc in ultimos.head(10).iterrows():
            descricao = lanc['descricao'][:40] + "..." if len(lanc['descricao']) > 40 else lanc['descricao']
            dados_ultimos.append([
                format_date_br(lanc['data']),
                lanc['categoria'],
                descricao,
                f"R$ {lanc['valor']:,.2f}"
            ])

        tabela_ultimos = Table(dados_ultimos, colWidths=[1*inch, 1.5*inch, 2.5*inch, 1*inch])
        tabela_ultimos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(tabela_ultimos)

def _add_relatorio_detalhado(story, styles, data_inicio, data_fim, incluir_graficos):
    """Adiciona relatório detalhado por período"""
    story.append(Paragraph("📄 RELATÓRIO DETALHADO", styles['Heading2']))
    story.append(Spacer(1, 12))

    if data_inicio and data_fim:
        story.append(Paragraph(f"Período: {format_date_br(data_inicio)} a {format_date_br(data_fim)}", styles['Normal']))
        story.append(Spacer(1, 12))

    # Buscar lançamentos do período
    conn = get_db_connection()

    query = """
        SELECT
            l.data,
            l.descricao,
            l.valor,
            l.observacoes,
            c.nome as categoria,
            u.nome as usuario
        FROM lancamentos l
        LEFT JOIN categorias c ON l.categoria_id = c.id
        LEFT JOIN usuarios u ON l.usuario_id = u.id
    """
    params = []

    if data_inicio and data_fim:
        query += " WHERE l.data BETWEEN ? AND ?"
        params = [data_inicio, data_fim]

    query += " ORDER BY l.data DESC"

    df_lancamentos = pd.read_sql_query(query, conn, params=params)
    conn.close()

    if df_lancamentos.empty:
        story.append(Paragraph("Nenhum lançamento encontrado no período.", styles['Normal']))
        return

    # Resumo do período
    total_periodo = df_lancamentos['valor'].sum()
    story.append(Paragraph(f"Total do período: R$ {total_periodo:,.2f}", styles['Heading3']))
    story.append(Paragraph(f"Quantidade de lançamentos: {len(df_lancamentos)}", styles['Normal']))
    story.append(Spacer(1, 12))

    # GRÁFICO - Evolução diária (se solicitado) (Temporariamente desativado)
    if incluir_graficos:
        story.append(Paragraph("🚫 Geração de gráficos desativada temporariamente 🚫", styles['Normal']))
        story.append(Spacer(1, 20))
        # Todo o código de geração de gráficos foi comentado/removido para evitar erros de importação.
        # Será reativado em uma etapa futura.

    # Tabela de lançamentos
    dados_lancamentos = [['Data', 'Categoria', 'Descrição', 'Valor', 'Usuário']]

    for _, lanc in df_lancamentos.iterrows():
        descricao = lanc['descricao'][:30] + "..." if len(lanc['descricao']) > 30 else lanc['descricao']
        dados_lancamentos.append([
            format_date_br(lanc['data']),
            lanc['categoria'],
            descricao,
            f"R$ {lanc['valor']:,.2f}",
            lanc['usuario']
        ])

    tabela_lancamentos = Table(dados_lancamentos, colWidths=[0.8*inch, 1.2*inch, 2*inch, 1*inch, 1*inch])
    tabela_lancamentos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(tabela_lancamentos)

def _add_analise_categoria(story, styles, incluir_graficos):
    """Adiciona análise por categoria"""
    story.append(Paragraph("📊 ANÁLISE POR CATEGORIA", styles['Heading2']))
    story.append(Spacer(1, 12))

    # Buscar dados por categoria
    conn = get_db_connection()

    df_analise = pd.read_sql_query("""
        SELECT
            c.nome as categoria,
            c.orcamento_previsto,
            COALESCE(SUM(l.valor), 0) as gasto_total,
            COUNT(l.id) as quantidade_lancamentos,
            COALESCE(AVG(l.valor), 0) as valor_medio
        FROM categorias c
        LEFT JOIN lancamentos l ON c.id = l.categoria_id
        WHERE c.ativo = 1
        GROUP BY c.id, c.nome, c.orcamento_previsto
        ORDER BY gasto_total DESC
    """, conn)
    conn.close()

    if df_analise.empty:
        story.append(Paragraph("Nenhum dado disponível para análise.", styles['Normal']))
        return

    # GRÁFICO - Percentual utilizado por categoria (Temporariamente desativado)
    if incluir_graficos:
        story.append(Paragraph("🚫 Geração de gráficos desativada temporariamente 🚫", styles['Normal']))
        story.append(Spacer(1, 20))
        # Todo o código de geração de gráficos foi comentado/removido para evitar erros de importação.
        # Será reativado em uma etapa futura.

    # Tabela de análise
    dados_analise = [['Categoria', 'Orçamento', 'Gasto', 'Qtd Lanç.', 'Valor Médio', '% Utilizado']]

    for _, cat in df_analise.iterrows():
        perc_utilizado = (cat['gasto_total'] / cat['orcamento_previsto'] * 100) if cat['orcamento_previsto'] > 0 else 0

        dados_analise.append([
            cat['categoria'],
            f"R$ {cat['orcamento_previsto']:,.0f}",
            f"R$ {cat['gasto_total']:,.0f}",
            str(int(cat['quantidade_lancamentos'])),
            f"R$ {cat['valor_medio']:,.0f}",
            f"{perc_utilizado:.1f}%"
        ])

    tabela_analise = Table(dados_analise, colWidths=[1.5*inch, 1*inch, 1*inch, 0.7*inch, 1*inch, 0.8*inch])
    tabela_analise.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(tabela_analise)
    story.append(Spacer(1, 20))

    # Resumo da análise
    total_orcamento = df_analise['orcamento_previsto'].sum()
    total_gasto = df_analise['gasto_total'].sum()
    categoria_mais_gasta = df_analise.loc[df_analise['gasto_total'].idxmax(), 'categoria']

    story.append(Paragraph("📈 RESUMO DA ANÁLISE", styles['Heading3']))
    story.append(Spacer(1, 8))

    resumo_texto = f"""
    • Orçamento total das categorias: R$ {total_orcamento:,.2f}<br/>
    • Total gasto até o momento: R$ {total_gasto:,.2f}<br/>
    • Percentual geral utilizado: {(total_gasto/total_orcamento*100):.1f}%<br/>
    • Categoria com maior gasto: {categoria_mais_gasta}<br/>
    • Número total de categorias: {len(df_analise)}
    """

    story.append(Paragraph(resumo_texto, styles['Normal']))

def gerar_relatorio_simples(obra_config, user):
    """Gera relatório simples para download rápido"""
    try:
        buffer = io.BytesIO()

        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Título
        story.append(Paragraph(f"Relatório Rápido - {obra_config['nome_obra']}", styles['Title']))
        story.append(Spacer(1, 12))

        # Dados básicos
        total_gasto, _, gastos_categoria, _, ultimos = get_dados_dashboard()

        story.append(Paragraph(f"Total Gasto: R$ {total_gasto:,.2f}", styles['Heading2']))
        story.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", styles['Normal']))
        story.append(Paragraph(f"Por: {user['nome']}", styles['Normal']))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    except Exception as e:
        print(f"Erro ao gerar relatório simples: {e}")
        return None