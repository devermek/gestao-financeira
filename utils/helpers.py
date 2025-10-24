import sys
from datetime import datetime, date
from decimal import Decimal
from config.database import get_connection

def format_currency_br(value):
    """Formata valor para moeda brasileira"""
    if value is None:
        return "R\$ 0,00"
    
    try:
        # Converte para float se for Decimal
        if isinstance(value, Decimal):
            value = float(value)
        
        # Formata para moeda brasileira
        return f"R\$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (TypeError, ValueError):
        return "R\$ 0,00"

def format_date_br(date_value):
    """Formata data para padrão brasileiro"""
    if date_value is None:
        return ""
    
    try:
        if isinstance(date_value, str):
            # Tenta converter string para date
            if len(date_value) == 10:  # YYYY-MM-DD
                date_value = datetime.strptime(date_value, '%Y-%m-%d').date()
            else:
                return date_value
        
        if isinstance(date_value, datetime):
            date_value = date_value.date()
        
        if isinstance(date_value, date):
            return date_value.strftime('%d/%m/%Y')
        
        return str(date_value)
    except (ValueError, TypeError):
        return str(date_value) if date_value else ""

def get_obra_config():
    """Busca configuração da obra de forma robusta"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verifica se a tabela existe
        try:
            cursor.execute("SELECT COUNT(*) FROM obras WHERE ativo = TRUE")
            if cursor.fetchone()[0] == 0:
                # Não há obra ativa
                return {
                    'id': None,
                    'nome': 'Obra não configurada',
                    'orcamento': 0.0,
                    'data_inicio': None,
                    'data_fim_prevista': None
                }
        except Exception:
            # Tabela não existe
            return {
                'id': None,
                'nome': 'Obra não configurada',
                'orcamento': 0.0,
                'data_inicio': None,
                'data_fim_prevista': None
            }
        
        # Busca a primeira obra ativa
        cursor.execute("""
            SELECT id, nome, orcamento, data_inicio, data_fim_prevista
            FROM obras 
            WHERE ativo = TRUE 
            ORDER BY id 
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        
        if result:
            # Conversão robusta de tipos
            orcamento = 0.0
            try:
                if result['orcamento'] is not None:
                    if isinstance(result['orcamento'], Decimal):
                        orcamento = float(result['orcamento'])
                    else:
                        orcamento = float(result['orcamento'])
            except (TypeError, ValueError):
                orcamento = 0.0
            
            return {
                'id': result['id'],
                'nome': result['nome'] or 'Obra sem nome',
                'orcamento': orcamento,
                'data_inicio': result['data_inicio'],
                'data_fim_prevista': result['data_fim_prevista']
            }
        else:
            return {
                'id': None,
                'nome': 'Obra não configurada',
                'orcamento': 0.0,
                'data_inicio': None,
                'data_fim_prevista': None
            }
            
    except Exception as e:
        print(f"Erro em get_obra_config: {repr(e)}", file=sys.stderr)
        return {
            'id': None,
            'nome': 'Erro ao carregar obra',
            'orcamento': 0.0,
            'data_inicio': None,
            'data_fim_prevista': None
        }
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def get_categorias_ativas():
    """Busca categorias ativas"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, nome, cor
            FROM categorias 
            WHERE ativo = TRUE 
            ORDER BY nome
        """)
        
        categorias = []
        for row in cursor.fetchall():
            categorias.append({
                'id': row['id'],
                'nome': row['nome'],
                'cor': row['cor']
            })
        
        return categorias
        
    except Exception as e:
        print(f"Erro em get_categorias_ativas: {repr(e)}", file=sys.stderr)
        return []
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def get_dados_dashboard():
    """Agrega dados para dashboard e relatórios"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        obra_config = get_obra_config()
        
        # Total gasto
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0) as total_gasto
            FROM lancamentos l
            JOIN obras o ON l.obra_id = o.id
            WHERE o.ativo = TRUE
        """)
        
        result = cursor.fetchone()
        total_gasto = 0.0
        if result and result['total_gasto'] is not None:
            try:
                if isinstance(result['total_gasto'], Decimal):
                    total_gasto = float(result['total_gasto'])
                else:
                    total_gasto = float(result['total_gasto'])
            except (TypeError, ValueError):
                total_gasto = 0.0
        
        # Gastos por categoria
        cursor.execute("""
            SELECT 
                c.nome,
                c.cor,
                COALESCE(SUM(l.valor), 0) as total
            FROM categorias c
            LEFT JOIN lancamentos l ON c.id = l.categoria_id
            LEFT JOIN obras o ON l.obra_id = o.id AND o.ativo = TRUE
            WHERE c.ativo = TRUE
            GROUP BY c.id, c.nome, c.cor
            ORDER BY total DESC
        """)
        
        gastos_por_categoria = []
        for row in cursor.fetchall():
            valor = 0.0
            try:
                if row['total'] is not None:
                    if isinstance(row['total'], Decimal):
                        valor = float(row['total'])
                    else:
                        valor = float(row['total'])
            except (TypeError, ValueError):
                valor = 0.0
            
            percentual = (valor / total_gasto * 100) if total_gasto > 0 else 0
            
            gastos_por_categoria.append({
                'nome': row['nome'],
                'cor': row['cor'],
                'valor': valor,
                'percentual': percentual
            })
        
        # Últimos lançamentos
        cursor.execute("""
            SELECT 
                l.id,
                l.descricao,
                l.valor,
                l.data_lancamento,
                c.nome as categoria_nome,
                c.cor as categoria_cor
            FROM lancamentos l
            JOIN categorias c ON l.categoria_id = c.id
            JOIN obras o ON l.obra_id = o.id
            WHERE o.ativo = TRUE
            ORDER BY l.data_lancamento DESC, l.id DESC
            LIMIT 5
        """)
        
        ultimos_lancamentos = []
        for row in cursor.fetchall():
            valor = 0.0
            try:
                if row['valor'] is not None:
                    if isinstance(row['valor'], Decimal):
                        valor = float(row['valor'])
                    else:
                        valor = float(row['valor'])
            except (TypeError, ValueError):
                valor = 0.0
            
            ultimos_lancamentos.append({
                'id': row['id'],
                'descricao': row['descricao'],
                'valor': valor,
                'data_lancamento': row['data_lancamento'],
                'categoria_nome': row['categoria_nome'],
                'categoria_cor': row['categoria_cor']
            })
        
        # Calcula percentual executado
        orcamento = obra_config.get('orcamento', 0.0)
        percentual_executado = (total_gasto / orcamento * 100) if orcamento > 0 else 0
        saldo_restante = orcamento - total_gasto
        
        return {
            'total_gasto': total_gasto,
            'orcamento': orcamento,
            'percentual_executado': percentual_executado,
            'saldo_restante': saldo_restante,
            'gastos_por_categoria': gastos_por_categoria,
            'ultimos_lancamentos': ultimos_lancamentos
        }
        
    except Exception as e:
        print(f"Erro em get_dados_dashboard: {repr(e)}", file=sys.stderr)
        return {
            'total_gasto': 0.0,
            'orcamento': 0.0,
            'percentual_executado': 0.0,
            'saldo_restante': 0.0,
            'gastos_por_categoria': [],
            'ultimos_lancamentos': []
        }
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass