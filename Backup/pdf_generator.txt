import io
import pandas as pd
#import matplotlib.pyplot as plt
#import matplotlib
#matplotlib.use('Agg')  # Backend para não mostrar janelas
#import seaborn as sns
from datetime import datetime, date
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from config.database import get_db_connection
from utils.helpers import format_date_br, get_dados_dashboard

# Configurar matplotlib para modo escuro
plt.style.use('dark_background')
sns.set_theme(style="darkgrid")

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
            _add_resumo_executivo(story, styles, obra_config, incluir_graficos)
        elif tipo_relatorio == "Detalhado por Período":
            _add_relatorio_detalhado(story, styles, data_inicio, data_fim, incluir_graficos)
        elif tipo_relatorio == "Análise por Categoria":
            _add_analise_categoria(story, styles, incluir_graficos)
        
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
    """Converte gráfico matplotlib para imagem para o PDF"""
    try:
        # Salvar gráfico em buffer
        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        img_buffer.seek(0)
        
        # Criar objeto Image do ReportLab
        img = Image(img_buffer, width=width*inch, height=height*inch)
        
        # Fechar figura para liberar memória
        plt.close(fig)
        
        return img
        
    except Exception as e:
        print(f"Erro ao criar imagem do gráfico: {e}")
        plt.close(fig)
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
        ['Total Gasto', f'R\$ {total_gasto:,.2f}'],
        ['Orçamento Total', f'R\$ {orcamento_referencia:,.2f}'],
        ['% Executado', f'{percentual:.1f}%'],
        ['Saldo Restante', f'R\$ {restante:,.2f}'],
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
    
    # GRÁFICOS - se solicitado
    if incluir_graficos and not gastos_categoria.empty:
        story.append(Paragraph("📊 GRÁFICOS DE ANÁLISE", styles['Heading3']))
        story.append(Spacer(1, 12))
        
        # Gráfico 1: Pizza - Distribuição por categoria
        fig1, ax1 = plt.subplots(figsize=(8, 6))
        
        # Filtrar apenas categorias com gastos
        df_gastos = gastos_categoria[gastos_categoria['gasto'] > 0].copy()
        
        if not df_gastos.empty:
            colors_pie = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
            wedges, texts, autotexts = ax1.pie(
                df_gastos['gasto'], 
                labels=df_gastos['nome'],
                autopct='%1.1f%%',
                startangle=90,
                colors=colors_pie[:len(df_gastos)]
            )
            
            ax1.set_title('Distribuição de Gastos por Categoria', fontsize=14, fontweight='bold', color='black')
            
            # Ajustar cores do texto para preto
            for text in texts:
                text.set_color('black')
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            # Adicionar ao PDF
            chart_img1 = _create_chart_image(fig1)
            if chart_img1:
                story.append(chart_img1)
                story.append(Spacer(1, 20))
        
        # Gráfico 2: Barras - Orçado vs Realizado
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        
        x = range(len(gastos_categoria))
        width = 0.35
        
        bars1 = ax2.bar([i - width/2 for i in x], gastos_categoria['orcamento_previsto'], 
                       width, label='Orçamento Previsto', color='#87CEEB', alpha=0.8)
        bars2 = ax2.bar([i + width/2 for i in x], gastos_categoria['gasto'], 
                       width, label='Gasto Real', color='#4682B4', alpha=0.9)
        
        ax2.set_xlabel('Categorias', fontweight='bold', color='black')
        ax2.set_ylabel('Valor (R\$)', fontweight='bold', color='black')
        ax2.set_title('Orçamento Previsto vs Gasto Real por Categoria', fontweight='bold', color='black')
        ax2.set_xticks(x)
        ax2.set_xticklabels(gastos_categoria['nome'], rotation=45, ha='right', color='black')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Ajustar cores dos eixos
        ax2.tick_params(colors='black')
        ax2.spines['bottom'].set_color('black')
        ax2.spines['left'].set_color('black')
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        
        # Adicionar valores nas barras
        for bar in bars1:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'R\${height:,.0f}', ha='center', va='bottom', fontsize=8, color='black')
        
        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'R\${height:,.0f}', ha='center', va='bottom', fontsize=8, color='black')
        
        plt.tight_layout()
        
        # Adicionar ao PDF
        chart_img2 = _create_chart_image(fig2, width=8, height=5)
        if chart_img2:
            story.append(chart_img2)
            story.append(Spacer(1, 20))
    
    # Gastos por categoria (tabela)
    if not gastos_categoria.empty:
        story.append(Paragraph("💰 GASTOS POR CATEGORIA", styles['Heading3']))
        story.append(Spacer(1, 12))
        
        dados_categoria = [['Categoria', 'Orçamento Previsto', 'Gasto Real', '% Utilizado']]
        
        for _, cat in gastos_categoria.iterrows():
            perc_cat = (cat['gasto'] / cat['orcamento_previsto'] * 100) if cat['orcamento_previsto'] > 0 else 0
            dados_categoria.append([
                cat['nome'],
                f"R\$ {cat['orcamento_previsto']:,.2f}",
                f"R\$ {cat['gasto']:,.2f}",
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
                f"R\$ {lanc['valor']:,.2f}"
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
    story.append(Paragraph("�� RELATÓRIO DETALHADO", styles['Heading2']))
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
    story.append(Paragraph(f"Total do período: R\$ {total_periodo:,.2f}", styles['Heading3']))
    story.append(Paragraph(f"Quantidade de lançamentos: {len(df_lancamentos)}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # GRÁFICO - Evolução diária (se solicitado)
    if incluir_graficos:
        story.append(Paragraph("📊 EVOLUÇÃO NO PERÍODO", styles['Heading3']))
        story.append(Spacer(1, 12))
        
        # Agrupar por data
        df_diario = df_lancamentos.groupby('data')['valor'].sum().reset_index()
        df_diario['data'] = pd.to_datetime(df_diario['data'])
        df_diario = df_diario.sort_values('data')
        
        if len(df_diario) > 1:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            ax.plot(df_diario['data'], df_diario['valor'], marker='o', linewidth=2, 
                   markersize=6, color='#4682B4')
            ax.fill_between(df_diario['data'], df_diario['valor'], alpha=0.3, color='#87CEEB')
            
            ax.set_xlabel('Data', fontweight='bold', color='black')
            ax.set_ylabel('Valor Gasto (R\$)', fontweight='bold', color='black')
            ax.set_title('Evolução dos Gastos no Período', fontweight='bold', color='black')
            ax.grid(True, alpha=0.3)
            
            # Ajustar cores
            ax.tick_params(colors='black')
            ax.spines['bottom'].set_color('black')
            ax.spines['left'].set_color('black')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Adicionar ao PDF
            chart_img = _create_chart_image(fig, width=8, height=5)
            if chart_img:
                story.append(chart_img)
                story.append(Spacer(1, 20))
    
    # Tabela de lançamentos
    dados_lancamentos = [['Data', 'Categoria', 'Descrição', 'Valor', 'Usuário']]
    
    for _, lanc in df_lancamentos.iterrows():
        descricao = lanc['descricao'][:30] + "..." if len(lanc['descricao']) > 30 else lanc['descricao']
        dados_lancamentos.append([
            format_date_br(lanc['data']),
            lanc['categoria'],
            descricao,
            f"R\$ {lanc['valor']:,.2f}",
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
    
    # GRÁFICO - Percentual utilizado por categoria
    if incluir_graficos:
        story.append(Paragraph("📊 ANÁLISE VISUAL", styles['Heading3']))
        story.append(Spacer(1, 12))
        
        # Calcular percentuais
        df_analise['percentual_usado'] = (df_analise['gasto_total'] / df_analise['orcamento_previsto'] * 100).fillna(0)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        bars = ax.barh(df_analise['categoria'], df_analise['percentual_usado'], 
                      color=['#FF6B6B' if x > 100 else '#4ECDC4' if x > 80 else '#96CEB4' 
                            for x in df_analise['percentual_usado']])
        
        ax.set_xlabel('Percentual Utilizado (%)', fontweight='bold', color='black')
        ax.set_ylabel('Categorias', fontweight='bold', color='black')
        ax.set_title('Percentual do Orçamento Utilizado por Categoria', fontweight='bold', color='black')
        ax.grid(True, alpha=0.3, axis='x')
        
        # Linha de referência em 100%
        ax.axvline(x=100, color='red', linestyle='--', alpha=0.7, linewidth=2)
        ax.text(102, len(df_analise)-1, '100%', color='red', fontweight='bold')
        
        # Adicionar valores nas barras
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width + 2, bar.get_y() + bar.get_height()/2,
                   f'{width:.1f}%', ha='left', va='center', fontweight='bold', color='black')
        
        # Ajustar cores
        ax.tick_params(colors='black')
        ax.spines['bottom'].set_color('black')
        ax.spines['left'].set_color('black')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        
        # Adicionar ao PDF
        chart_img = _create_chart_image(fig, width=8, height=6)
        if chart_img:
            story.append(chart_img)
            story.append(Spacer(1, 20))
    
    # Tabela de análise
    dados_analise = [['Categoria', 'Orçamento', 'Gasto', 'Qtd Lanç.', 'Valor Médio', '% Utilizado']]
    
    for _, cat in df_analise.iterrows():
        perc_utilizado = (cat['gasto_total'] / cat['orcamento_previsto'] * 100) if cat['orcamento_previsto'] > 0 else 0
        
        dados_analise.append([
            cat['categoria'],
            f"R\$ {cat['orcamento_previsto']:,.0f}",
            f"R\$ {cat['gasto_total']:,.0f}",
            str(int(cat['quantidade_lancamentos'])),
            f"R\$ {cat['valor_medio']:,.0f}",
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
    • Orçamento total das categorias: R\$ {total_orcamento:,.2f}<br/>
    • Total gasto até o momento: R\$ {total_gasto:,.2f}<br/>
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
        
        story.append(Paragraph(f"Total Gasto: R\$ {total_gasto:,.2f}", styles['Heading2']))
        story.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", styles['Normal']))
        story.append(Paragraph(f"Por: {user['nome']}", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
        
    except Exception as e:
        print(f"Erro ao gerar relatório simples: {e}")
        return None