import streamlit as st
import os
from config.database import get_db_connection
from datetime import datetime # <--- ADICIONADO: Necessário para formatar datas

def get_obra_config():
    """
    Retorna as configurações da obra. Se não existirem, cria configurações padrão.
    """
    conn, db_type = get_db_connection() # Obter db_type aqui
    cursor = conn.cursor()
    
    config = {}
    try:
        cursor.execute("SELECT nome_obra, orcamento_total, data_inicio, data_previsao_fim FROM obra_config LIMIT 1")
        result = cursor.fetchone()
        
        if result:
            config = {
                "nome_obra": result['nome_obra'],
                "orcamento_total": float(result['orcamento_total']),
                "data_inicio": result['data_inicio'],
                "data_previsao_fim": result['data_previsao_fim']
            }
        else:
            # Criar configuração padrão se não existir
            print("DEBUG HELPERS: Criando configuração padrão da obra.", file=sys.stderr); sys.stderr.flush()
            param_placeholder = '%s' if db_type == 'postgresql' else '?'
            insert_query = f"""
                INSERT INTO obra_config (nome_obra, orcamento_total, data_inicio, data_previsao_fim)
                VALUES ({param_placeholder}, {param_placeholder}, {param_placeholder}, {param_placeholder})
            """
            cursor.execute(insert_query, ("Minha Obra Padrão", 1000000.00, "2023-01-01", "2024-12-31"))
            conn.commit()
            config = {
                "nome_obra": "Minha Obra Padrão",
                "orcamento_total": 1000000.00,
                "data_inicio": "2023-01-01",
                "data_previsao_fim": "2024-12-31"
            }
    except Exception as e:
        print(f"DEBUG HELPERS: Erro ao carregar/criar obra_config: {e}", file=sys.stderr); sys.stderr.flush()
        # Retorna uma config vazia ou padrão segura em caso de erro
        config = {
            "nome_obra": "Erro ao Carregar Configuração",
            "orcamento_total": 0.00,
            "data_inicio": "N/A",
            "data_previsao_fim": "N/A"
        }
    finally:
        if conn:
            conn.close()
    return config

def get_dados_dashboard():
    """Retorna dados agregados para o dashboard (total gasto, previsto, etc.)"""
    conn, db_type = get_db_connection()
    cursor = conn.cursor()

    total_gasto = 0.0
    total_previsto_categorias = 0.0
    lancamentos_recents = []
    lancamentos_por_categoria = []
    
    try:
        # Total gasto
        cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM lancamentos")
        total_gasto = float(cursor.fetchone()[0])

        # Total previsto por categorias
        cursor.execute("SELECT COALESCE(SUM(orcamento_previsto), 0) FROM categorias WHERE ativo = TRUE")
        total_previsto_categorias = float(cursor.fetchone()[0])

        # Lançamentos recentes
        cursor.execute("""
            SELECT l.data, l.descricao, l.valor, c.nome as categoria, u.nome as usuario
            FROM lancamentos l
            JOIN categorias c ON l.categoria_id = c.id
            JOIN usuarios u ON l.usuario_id = u.id
            ORDER BY l.data DESC
            LIMIT 5
        """)
        lancamentos_recents = cursor.fetchall()
        
        # Lançamentos por categoria (para gráfico)
        cursor.execute("""
            SELECT c.nome, COALESCE(SUM(l.valor), 0) as total_gasto
            FROM categorias c
            LEFT JOIN lancamentos l ON c.id = l.categoria_id
            WHERE c.ativo = TRUE
            GROUP BY c.nome
            ORDER BY total_gasto DESC
        """)
        lancamentos_por_categoria = cursor.fetchall()

    except Exception as e:
        print(f"DEBUG HELPERS: Erro ao obter dados do dashboard: {e}", file=sys.stderr); sys.stderr.flush()
    finally:
        if conn:
            conn.close()
            
    return total_gasto, total_previsto_categorias, lancamentos_recents, lancamentos_por_categoria, {} # Retorna um dict vazio para outros_dados

def format_currency_br(value):
    """Formata um valor numérico para o formato monetário brasileiro."""
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_date_br(date_str):
    """
    Formata uma string de data (ex: 'YYYY-MM-DD') para o formato brasileiro (DD/MM/YYYY).
    Retorna 'N/A' se a data for inválida ou None.
    """
    if not date_str:
        return "N/A"
    try:
        # Tenta converter a string para um objeto datetime
        date_obj = datetime.strptime(str(date_str), "%Y-%m-%d")
        # Formata o objeto datetime para o formato desejado
        return date_obj.strftime("%d/%m/%Y")
    except ValueError:
        # Se a conversão falhar, retorna a string original ou 'N/A'
        return date_str # Ou "N/A" se preferir uma saída padronizada para erros de formato