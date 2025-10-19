import pandas as pd
from datetime import datetime, date
from config.database import get_db_connection, get_current_db_type # Import get_current_db_type
import streamlit as st # Mantido para st.error em blocos except para feedback ao usuário

def format_date_br(data):
    """Formata data para padrão brasileiro"""
    if isinstance(data, str):
        try:
            data = datetime.strptime(data, '%Y-%m-%d').date()
        except ValueError:
            return data # Retorna a string original se o formato não for YYYY-MM-DD
    
    if isinstance(data, (date, datetime)):
        return data.strftime('%d/%m/%Y')
    
    return str(data)

def format_currency_br(valor):
    """
    Formata um valor numérico para o padrão monetário brasileiro (R$ X.XXX,XX).
    Usa ponto como separador de milhares e vírgula como separador decimal.
    """
    if valor is None or not isinstance(valor, (int, float)):
        return "0,00"
    
    s = f"{valor:,.2f}" 
    s = s.replace(",", "X") # Troca vírgula por um caractere temporário
    s = s.replace(".", ",") # Troca ponto por vírgula (separador decimal brasileiro)
    s = s.replace("X", ".") # Troca caractere temporário por ponto (separador de milhares brasileiro)
    return s

def get_obra_config():
    """Busca configurações da obra. Se não existir, cria uma padrão."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        db_type = get_current_db_type()
        # No PostgreSQL, os parâmetros são $1, $2, etc. No SQLite, são ?.
        param_char = '$' if db_type == 'postgresql' else '?'

        cursor.execute(f"""
            SELECT id, nome_obra, orcamento_total, data_inicio, data_previsao_fim
            FROM obra_config 
            ORDER BY id DESC 
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        conn.close() # Fecha a conexão após a consulta
        
        if result:
            return {
                'id': result[0],
                'nome_obra': result[1] or 'Obra Sem Nome',
                'orcamento_total': result[2] or 0.0,
                'data_inicio': result[3] or None,
                'data_previsao_fim': result[4] or None
            }
        else:
            # Se não houver configuração, cria uma padrão
            conn = get_db_connection() # Reabre a conexão para a inserção
            cursor = conn.cursor()
            
            if db_type == 'postgresql':
                cursor.execute(f"""
                    INSERT INTO obra_config (nome_obra, orcamento_total, data_inicio, data_previsao_fim)
                    VALUES (%s, %s, %s, %s) RETURNING id
                """, ("Nova Obra", 0.0, None, None))
                obra_id = cursor.fetchone()[0]
            else:
                cursor.execute(f"""
                    INSERT INTO obra_config (nome_obra, orcamento_total, data_inicio, data_previsao_fim)
                    VALUES (?, ?, ?, ?)
                """, ("Nova Obra", 0.0, None, None))
                obra_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            return {
                'id': obra_id,
                'nome_obra': 'Nova Obra',
                'orcamento_total': 0.0,
                'data_inicio': None,
                'data_previsao_fim': None
            }
            
    except Exception as e:
        st.error(f"❌ Erro ao buscar/criar configuração da obra: {e}") 
        return {
            'id': None,
            'nome_obra': 'Erro na Configuração',
            'orcamento_total': 0.0,
            'data_inicio': None,
            'data_previsao_fim': None
        }
        
def get_categorias_ativas():
    """Busca todas as categorias ativas"""
    try:
        conn = get_db_connection()
        query = """
            SELECT id, nome, orcamento_previsto, ativo
            FROM categorias 
            WHERE ativo = 1 
            ORDER BY nome
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return [] # Retorna lista vazia se não houver categorias
        
        categorias = []
        for _, row in df.iterrows():
            categorias.append({
                'id': row['id'],
                'nome': row['nome'],
                'orcamento_previsto': row['orcamento_previsto']
            })
        
        return categorias
        
    except Exception as e:
        st.error(f"❌ **ERRO em get_categorias_ativas():** {e}") 
        return []

def get_categoria_by_id(categoria_id):
    """Busca uma categoria pelo ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        db_type = get_current_db_type()
        param_char = '%s' if db_type == 'postgresql' else '?'

        cursor.execute(f"SELECT id, nome, orcamento_previsto FROM categorias WHERE id = {param_char} AND ativo = 1", (categoria_id,))
        categoria = cursor.fetchone()
        conn.close()
        
        if categoria:
            return {
                'id': categoria[0],
                'nome': categoria[1],
                'orcamento_previsto': categoria[2]
            }
        
        return None
        
    except Exception as e:
        st.error(f"❌ Erro ao buscar categoria por ID: {e}")
        return None

def get_dados_dashboard():
    """Busca dados para o dashboard"""
    try:
        conn = get_db_connection()
        db_type = get_current_db_type()

        # Diferença de funções de data entre SQLite e PostgreSQL
        if db_type == 'postgresql':
            strftime_func = "to_char(data, 'YYYY-MM')"
            date_ago_func = "NOW() - INTERVAL '6 months'"
        else: # sqlite
            strftime_func = "strftime('%Y-%m', data)"
            date_ago_func = "date('now', '-6 months')"


        total_gasto_query = "SELECT COALESCE(SUM(valor), 0) FROM lancamentos"
        total_gasto = conn.execute(total_gasto_query).fetchone()[0]
        
        gastos_categoria = pd.read_sql_query(f"""
            SELECT 
                c.id,
                c.nome,
                c.orcamento_previsto,
                COALESCE(SUM(l.valor), 0) as gasto
            FROM categorias c
            LEFT JOIN lancamentos l ON c.id = l.categoria_id
            WHERE c.ativo = 1
            GROUP BY c.id, c.nome, c.orcamento_previsto
            ORDER BY c.nome
        """, conn)
        
        total_previsto_categorias = gastos_categoria['orcamento_previsto'].sum()
        
        evolucao = pd.read_sql_query(f"""
            SELECT 
                {strftime_func} as mes,
                SUM(valor) as total
            FROM lancamentos
            WHERE data >= {date_ago_func}
            GROUP BY {strftime_func}
            ORDER BY mes
        """, conn)
        
        ultimos = pd.read_sql_query("""
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
            ORDER BY l.created_at DESC, l.id DESC
            LIMIT 10
        """, conn)
        
        conn.close()
        
        return total_gasto, total_previsto_categorias, gastos_categoria, evolucao, ultimos
    except Exception as e:
        st.error(f"❌ Erro ao buscar dados do dashboard: {e}")
        return 0, 0, pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
def get_usuarios_ativos():
    """Busca todos os usuários ativos"""
    try:
        conn = get_db_connection()
        query = """
            SELECT id, nome, email, tipo, ativo, created_at
            FROM usuarios 
            WHERE ativo = 1 
            ORDER BY nome
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
        
    except Exception as e:
        st.error(f"❌ Erro ao buscar usuários: {e}")
        return pd.DataFrame()

def get_lancamentos_recentes(limite=10):
    """Busca lançamentos mais recentes"""
    try:
        conn = get_db_connection()
        db_type = get_current_db_type()
        param_char = '%s' if db_type == 'postgresql' else '?'

        df = pd.read_sql_query(f"""
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
            ORDER BY l.created_at DESC
            LIMIT {param_char}
        """, conn, params=[limite])
        conn.close()
        return df
        
    except Exception as e:
        st.error(f"❌ Erro ao buscar lançamentos recentes: {e}")
        return pd.DataFrame()

def get_estatisticas_obra():
    """Calcula estatísticas gerais da obra"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        total_lancamentos_query = "SELECT COALESCE(SUM(valor), 0) FROM lancamentos"
        total_lancamentos = conn.execute(total_lancamentos_query).fetchone()[0]
        
        total_gasto_query = "SELECT COALESCE(SUM(valor), 0) FROM lancamentos"
        total_gasto = conn.execute(total_gasto_query).fetchone()[0]
        
        media_lancamento = total_gasto / total_lancamentos if total_lancamentos > 0 else 0
        
        cursor.execute("""
            SELECT c.nome, SUM(l.valor) as total
            FROM lancamentos l
            LEFT JOIN categorias c ON l.categoria_id = c.id
            GROUP BY c.nome
            ORDER BY total DESC
            LIMIT 1
        """)
        categoria_top = cursor.fetchone()
        
        cursor.execute("""
            SELECT data FROM lancamentos 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        ultimo_lancamento = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_lancamentos': total_lancamentos,
            'total_gasto': total_gasto,
            'media_lancamento': media_lancamento,
            'categoria_top': categoria_top[0] if categoria_top else 'N/A',
            'categoria_top_valor': categoria_top[1] if categoria_top else 0,
            'ultimo_lancamento': ultimo_lancamento[0] if ultimo_lancamento else None
        }
        
    except Exception as e:
        st.error(f"❌ Erro ao calcular estatísticas: {e}")
        return {
            'total_lancamentos': 0,
            'total_gasto': 0,
            'media_lancamento': 0,
            'categoria_top': 'N/A',
            'categoria_top_valor': 0,
            'ultimo_lancamento': None
        }

def validar_email(email):
    """Valida formato de email"""
    import re
    # Padrão de regex corrigido e completo
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def calcular_percentual_categoria(gasto, orcamento_previsto):
    """Calcula percentual gasto de uma categoria"""
    if orcamento_previsto <= 0:
        return 0
    return (gasto / orcamento_previsto) * 100

def get_status_categoria(percentual):
    """Retorna status baseado no percentual gasto"""
    if percentual > 100:
        return "🔴 Estourado", "error"
    elif percentual > 90:
        return "⚠️ Atenção", "warning"
    elif percentual > 80:
        return "🟠 Cuidado", "warning"
    else:
        return "🟢 Normal", "success"

def formatar_tamanho_arquivo(tamanho_bytes):
    """Formata tamanho de arquivo em bytes para formato legível"""
    if tamanho_bytes < 1024:
        return f"{tamanho_bytes} B"
    elif tamanho_bytes < 1024 * 1024:
        return f"{tamanho_bytes / 1024:.1f} KB"
    else:
        return f"{tamanho_bytes / (1024 * 1024):.1f} MB"

def get_extensao_arquivo(nome_arquivo):
    """Extrai extensão do arquivo"""
    return nome_arquivo.lower().split('.')[-1] if '.' in nome_arquivo else ''

def is_imagem(nome_arquivo):
    """Verifica se arquivo é uma imagem"""
    extensoes_imagem = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
    extensao = get_extensao_arquivo(nome_arquivo)
    return extensao in extensoes_imagem

def get_emoji_arquivo(nome_arquivo):
    """Retorna emoji baseado no tipo de arquivo"""
    extensao = get_extensao_arquivo(nome_arquivo)
    
    if extensao in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
        return "🖼️"
    elif extensao == 'pdf':
        return "📄" # Alterado para um emoji mais comum para PDF/documentos
    elif extensao in ['doc', 'docx']:
        return "📝"
    elif extensao in ['xls', 'xlsx', 'csv']:
        return "��"
    elif extensao == 'txt':
        return "📝"
    else:
        return "📎"