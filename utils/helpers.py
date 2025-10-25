import sys
from datetime import datetime, date
from config.database import get_connection

def format_currency_br(valor):
    """Formata valor para moeda brasileira"""
    try:
        if valor is None or valor == 0:
            return "R$ 0,00"
        
        # Converte para float se necessário
        if isinstance(valor, str):
            valor = float(valor.replace(',', '.'))
        
        return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return "R$ 0,00"

def format_date_br(data):
    """Formata data para padrão brasileiro"""
    try:
        if data is None:
            return ""
        
        if isinstance(data, str):
            # Tenta diferentes formatos
            for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                try:
                    data = datetime.strptime(data, fmt).date()
                    break
                except:
                    continue
        elif isinstance(data, datetime):
            data = data.date()
        
        if isinstance(data, date):
            return data.strftime('%d/%m/%Y')
        
        return str(data)
    except:
        return ""

def get_obra_config():
    """Retorna configuração da obra ativa"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        # Primeiro verifica se existe alguma obra
        cursor.execute("SELECT COUNT(*) as count FROM obras")
        result = cursor.fetchone()
        obra_count = result['count'] if result else 0
        
        if obra_count == 0:
            print("Nenhuma obra encontrada no banco", file=sys.stderr)
            cursor.close()
            conn.close()
            return {
                'id': None,
                'nome': 'Nenhuma obra configurada',
                'orcamento': 0.0,
                'data_inicio': None,
                'data_fim_prevista': None,
                'created_at': None
            }
        
        if is_postgres:
            query = """
                SELECT id, nome, orcamento, data_inicio, data_fim_prevista, created_at
                FROM obras 
                WHERE ativo = TRUE 
                ORDER BY id DESC 
                LIMIT 1
            """
        else:
            query = """
                SELECT id, nome, orcamento, data_inicio, data_fim_prevista, created_at
                FROM obras 
                WHERE ativo = 1 
                ORDER BY id DESC 
                LIMIT 1
            """
        
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result:
            # Converte orcamento para float
            orcamento = 0.0
            try:
                if result['orcamento'] is not None:
                    from decimal import Decimal
                    if isinstance(result['orcamento'], Decimal):
                        orcamento = float(result['orcamento'])
                    else:
                        orcamento = float(result['orcamento'])
            except (TypeError, ValueError):
                orcamento = 0.0
            
            # Converte datas
            data_inicio = None
            data_fim_prevista = None
            
            try:
                if result['data_inicio']:
                    if isinstance(result['data_inicio'], str):
                        data_inicio = datetime.strptime(result['data_inicio'], '%Y-%m-%d').date()
                    else:
                        data_inicio = result['data_inicio']
            except:
                pass
            
            try:
                if result['data_fim_prevista']:
                    if isinstance(result['data_fim_prevista'], str):
                        data_fim_prevista = datetime.strptime(result['data_fim_prevista'], '%Y-%m-%d').date()
                    else:
                        data_fim_prevista = result['data_fim_prevista']
            except:
                pass
            
            obra_config = {
                'id': result['id'],
                'nome': result['nome'],
                'orcamento': orcamento,
                'data_inicio': data_inicio,
                'data_fim_prevista': data_fim_prevista,
                'created_at': result['created_at']
            }
            
            print(f"Obra encontrada: ID {obra_config['id']}, Nome: {obra_config['nome']}", file=sys.stderr)
            cursor.close()
            conn.close()
            return obra_config
        
        # Se não encontrou obra ativa, pega a primeira disponível
        cursor.execute("SELECT id, nome, orcamento, data_inicio, data_fim_prevista, created_at FROM obras ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        
        if result:
            print(f"Nenhuma obra ativa, usando primeira obra: ID {result['id']}", file=sys.stderr)
            
            # Ativa esta obra
            if is_postgres:
                cursor.execute("UPDATE obras SET ativo = TRUE WHERE id = %s", (result['id'],))
            else:
                cursor.execute("UPDATE obras SET ativo = 1 WHERE id = ?", (result['id'],))
            
            conn.commit()
            
            # Retorna dados da obra
            orcamento = 0.0
            try:
                if result['orcamento'] is not None:
                    from decimal import Decimal
                    if isinstance(result['orcamento'], Decimal):
                        orcamento = float(result['orcamento'])
                    else:
                        orcamento = float(result['orcamento'])
            except (TypeError, ValueError):
                orcamento = 0.0
            
            cursor.close()
            conn.close()
            return {
                'id': result['id'],
                'nome': result['nome'],
                'orcamento': orcamento,
                'data_inicio': result['data_inicio'],
                'data_fim_prevista': result['data_fim_prevista'],
                'created_at': result['created_at']
            }
        
        # Se chegou aqui, não tem obra nenhuma
        cursor.close()
        conn.close()
        return {
            'id': None,
            'nome': 'Obra não configurada',
            'orcamento': 0.0,
            'data_inicio': None,
            'data_fim_prevista': None,
            'created_at': None
        }
        
    except Exception as e:
        print(f"Erro ao buscar configuração da obra: {repr(e)}", file=sys.stderr)
        return {
            'id': None,
            'nome': 'Erro ao carregar obra',
            'orcamento': 0.0,
            'data_inicio': None,
            'data_fim_prevista': None,
            'created_at': None
        }
    finally:
        try:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
        except:
            pass

def get_categorias_ativas():
    """Retorna lista de categorias ativas"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        if is_postgres:
            query = """
                SELECT id, nome, descricao, cor
                FROM categorias 
                WHERE ativo = TRUE 
                ORDER BY nome
            """
        else:
            query = """
                SELECT id, nome, descricao, cor
                FROM categorias 
                WHERE ativo = 1 
                ORDER BY nome
            """
        
        cursor.execute(query)
        
        categorias = []
        for row in cursor.fetchall():
            categorias.append({
                'id': row['id'],
                'nome': row['nome'],
                'descricao': row['descricao'],
                'cor': row['cor']
            })
        
        return categorias
        
    except Exception as e:
        print(f"Erro ao buscar categorias: {repr(e)}", file=sys.stderr)
        return []
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def get_dados_dashboard():
    """Retorna dados para o dashboard"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        # Busca obra ativa
        obra_config = get_obra_config()
        
        # Inicializa dados padrão
        dados = {
            'total_gasto': 0.0,
            'orcamento': obra_config.get('orcamento', 0.0),
            'percentual_executado': 0.0,
            'saldo_restante': obra_config.get('orcamento', 0.0),
            'gastos_por_categoria': [],
            'ultimos_lancamentos': []
        }
        
        if not obra_config.get('id'):
            return dados
        
        # Total gasto
        if is_postgres:
            query_total = """
                SELECT COALESCE(SUM(valor), 0) as total
                FROM lancamentos l
                JOIN obras o ON l.obra_id = o.id
                WHERE o.ativo = TRUE
            """
        else:
            query_total = """
                SELECT COALESCE(SUM(valor), 0) as total
                FROM lancamentos l
                JOIN obras o ON l.obra_id = o.id
                WHERE o.ativo = 1
            """
        
        cursor.execute(query_total)
        result = cursor.fetchone()
        
        if result and result['total']:
            from decimal import Decimal
            if isinstance(result['total'], Decimal):
                dados['total_gasto'] = float(result['total'])
            else:
                dados['total_gasto'] = float(result['total'])
        
        # Calcula percentuais
        if dados['orcamento'] > 0:
            dados['percentual_executado'] = (dados['total_gasto'] / dados['orcamento']) * 100
            dados['saldo_restante'] = dados['orcamento'] - dados['total_gasto']
        
        # Gastos por categoria
        if is_postgres:
            query_categorias = """
                SELECT 
                    c.id, c.nome, c.cor,
                    COALESCE(SUM(l.valor), 0) as valor
                FROM categorias c
                LEFT JOIN lancamentos l ON c.id = l.categoria_id
                LEFT JOIN obras o ON l.obra_id = o.id AND o.ativo = TRUE
                WHERE c.ativo = TRUE
                GROUP BY c.id, c.nome, c.cor
                ORDER BY valor DESC
            """
        else:
            query_categorias = """
                SELECT 
                    c.id, c.nome, c.cor,
                    COALESCE(SUM(l.valor), 0) as valor
                FROM categorias c
                LEFT JOIN lancamentos l ON c.id = l.categoria_id
                LEFT JOIN obras o ON l.obra_id = o.id AND o.ativo = 1
                WHERE c.ativo = 1
                GROUP BY c.id, c.nome, c.cor
                ORDER BY valor DESC
            """
        
        cursor.execute(query_categorias)
        
        for row in cursor.fetchall():
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
            
            percentual = 0.0
            if dados['total_gasto'] > 0:
                percentual = (valor / dados['total_gasto']) * 100
            
            dados['gastos_por_categoria'].append({
                'id': row['id'],
                'nome': row['nome'],
                'cor': row['cor'],
                'valor': valor,
                'percentual': percentual
            })
        
        # Últimos lançamentos
        if is_postgres:
            query_lancamentos = """
                SELECT 
                    l.id, l.descricao, l.valor, l.data_lancamento,
                    c.nome as categoria_nome, c.cor as categoria_cor
                FROM lancamentos l
                JOIN categorias c ON l.categoria_id = c.id
                JOIN obras o ON l.obra_id = o.id
                WHERE o.ativo = TRUE
                ORDER BY l.created_at DESC
                LIMIT 5
            """
        else:
            query_lancamentos = """
                SELECT 
                    l.id, l.descricao, l.valor, l.data_lancamento,
                    c.nome as categoria_nome, c.cor as categoria_cor
                FROM lancamentos l
                JOIN categorias c ON l.categoria_id = c.id
                JOIN obras o ON l.obra_id = o.id
                WHERE o.ativo = 1
                ORDER BY l.created_at DESC
                LIMIT 5
            """
        
        cursor.execute(query_lancamentos)
        
        for row in cursor.fetchall():
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
            
            dados['ultimos_lancamentos'].append({
                'id': row['id'],
                'descricao': row['descricao'],
                'valor': valor,
                'data_lancamento': row['data_lancamento'],
                'categoria_nome': row['categoria_nome'],
                'categoria_cor': row['categoria_cor']
            })
        
        return dados
        
    except Exception as e:
        print(f"Erro ao buscar dados do dashboard: {repr(e)}", file=sys.stderr)
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

def safe_float_conversion(value):
    """Converte valor para float de forma segura"""
    try:
        if value is None:
            return 0.0
        
        from decimal import Decimal
        if isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            return float(value.replace(',', '.'))
        else:
            return 0.0
    except (TypeError, ValueError):
        return 0.0

def safe_date_conversion(date_value):
    """Converte data de forma segura"""
    try:
        if date_value is None:
            return None
        
        if isinstance(date_value, str):
            # Tenta diferentes formatos
            for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                try:
                    return datetime.strptime(date_value, fmt).date()
                except:
                    continue
        elif isinstance(date_value, datetime):
            return date_value.date()
        elif isinstance(date_value, date):
            return date_value
        
        return None
    except:
        return None

def validate_obra_data(nome, orcamento, data_inicio, data_fim_prevista):
    """Valida dados da obra"""
    errors = []
    
    if not nome or not nome.strip():
        errors.append("Nome da obra é obrigatório")
    
    if orcamento is None or orcamento < 0:
        errors.append("Orçamento deve ser maior ou igual a zero")
    
    if data_inicio and data_fim_prevista:
        if data_fim_prevista <= data_inicio:
            errors.append("Data de fim deve ser posterior à data de início")
    
    return errors

def calculate_obra_progress(obra_config, total_gasto):
    """Calcula progresso da obra"""
    try:
        if not obra_config or not obra_config.get('orcamento') or obra_config['orcamento'] <= 0:
            return {
                'percentual_executado': 0.0,
                'saldo_restante': 0.0,
                'status': 'Orçamento não definido'
            }
        
        orcamento = obra_config['orcamento']
        percentual_executado = (total_gasto / orcamento) * 100
        saldo_restante = orcamento - total_gasto
        
        # Define status baseado no percentual
        if percentual_executado < 25:
            status = 'Início'
        elif percentual_executado < 50:
            status = 'Em andamento'
        elif percentual_executado < 75:
            status = 'Avançado'
        elif percentual_executado < 100:
            status = 'Finalizando'
        elif percentual_executado >= 100:
            status = 'Orçamento excedido'
        else:
            status = 'Concluído'
        
        return {
            'percentual_executado': percentual_executado,
            'saldo_restante': saldo_restante,
            'status': status
        }
        
    except Exception as e:
        print(f"Erro ao calcular progresso da obra: {repr(e)}", file=sys.stderr)
        return {
            'percentual_executado': 0.0,
            'saldo_restante': 0.0,
            'status': 'Erro no cálculo'
        }

def get_resumo_categorias():
    """Retorna resumo de gastos por categoria"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        if is_postgres:
            query = """
                SELECT 
                    c.nome,
                    c.cor,
                    COUNT(l.id) as total_lancamentos,
                    COALESCE(SUM(l.valor), 0) as total_valor,
                    COALESCE(AVG(l.valor), 0) as valor_medio
                FROM categorias c
                LEFT JOIN lancamentos l ON c.id = l.categoria_id
                LEFT JOIN obras o ON l.obra_id = o.id AND o.ativo = TRUE
                WHERE c.ativo = TRUE
                GROUP BY c.id, c.nome, c.cor
                ORDER BY total_valor DESC
            """
        else:
            query = """
                SELECT 
                    c.nome,
                    c.cor,
                    COUNT(l.id) as total_lancamentos,
                    COALESCE(SUM(l.valor), 0) as total_valor,
                    COALESCE(AVG(l.valor), 0) as valor_medio
                FROM categorias c
                LEFT JOIN lancamentos l ON c.id = l.categoria_id
                LEFT JOIN obras o ON l.obra_id = o.id AND o.ativo = 1
                WHERE c.ativo = 1
                GROUP BY c.id, c.nome, c.cor
                ORDER BY total_valor DESC
            """
        
        cursor.execute(query)
        
        resumo = []
        for row in cursor.fetchall():
            total_valor = safe_float_conversion(row['total_valor'])
            valor_medio = safe_float_conversion(row['valor_medio'])
            
            resumo.append({
                'nome': row['nome'],
                'cor': row['cor'],
                'total_lancamentos': row['total_lancamentos'],
                'total_valor': total_valor,
                'valor_medio': valor_medio
            })
        
        return resumo
        
    except Exception as e:
        print(f"Erro ao buscar resumo de categorias: {repr(e)}", file=sys.stderr)
        return []
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def format_file_size(size_bytes):
    """Formata tamanho de arquivo"""
    try:
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
        
    except:
        return "0 B"

def get_estatisticas_gerais():
    """Retorna estatísticas gerais do sistema"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        # Conta total de lançamentos
        if is_postgres:
            cursor.execute("""
                SELECT COUNT(*) as total FROM lancamentos l
                JOIN obras o ON l.obra_id = o.id WHERE o.ativo = TRUE
            """)
        else:
            cursor.execute("""
                SELECT COUNT(*) as total FROM lancamentos l
                JOIN obras o ON l.obra_id = o.id WHERE o.ativo = 1
            """)
        
        total_lancamentos = cursor.fetchone()['total']
        
        # Conta total de categorias ativas
        if is_postgres:
            cursor.execute("SELECT COUNT(*) as total FROM categorias WHERE ativo = TRUE")
        else:
            cursor.execute("SELECT COUNT(*) as total FROM categorias WHERE ativo = 1")
        
        total_categorias = cursor.fetchone()['total']
        
        # Conta total de obras
        cursor.execute("SELECT COUNT(*) as total FROM obras")
        total_obras = cursor.fetchone()['total']
        
        # Conta total de arquivos
        cursor.execute("SELECT COUNT(*) as total FROM arquivos")
        total_arquivos = cursor.fetchone()['total']
        
        return {
            'total_lancamentos': total_lancamentos,
            'total_categorias': total_categorias,
            'total_obras': total_obras,
            'total_arquivos': total_arquivos
        }
        
    except Exception as e:
        print(f"Erro ao buscar estatísticas gerais: {repr(e)}", file=sys.stderr)
        return {
            'total_lancamentos': 0,
            'total_categorias': 0,
            'total_obras': 0,
            'total_arquivos': 0
        }
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass