import sys
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from config.database import get_connection
from utils.helpers import get_obra_config, get_categorias_ativas, format_currency_br, format_date_br

def show_lancamentos():
    """Exibe página de lançamentos"""
    st.title("💰 Gestão de Lançamentos")
    
    # Tabs para diferentes funcionalidades
    tab1, tab2, tab3 = st.tabs(["➕ Novo Lançamento", "📋 Listar Lançamentos", "🔍 Buscar/Filtrar"])
    
    with tab1:
        show_novo_lancamento()
    
    with tab2:
        show_lista_lancamentos()
    
    with tab3:
        show_filtros_lancamentos()

def show_novo_lancamento():
    """Formulário para novo lançamento - SEM RECARREGAR"""
    st.subheader("➕ Registrar Novo Lançamento")
    
    # Verifica se há obra configurada
    obra_config = get_obra_config()
    
    if not obra_config or not obra_config.get('id'):
        st.error("⚠️ Configure uma obra antes de registrar lançamentos!")
        if st.button("🔧 Ir para Configurações", use_container_width=True):
            st.session_state.current_page = "⚙️ Configurações"
            st.rerun()
        return
    
    # Verifica se há categorias
    categorias = get_categorias_ativas()
    if not categorias:
        st.error("⚠️ Cadastre pelo menos uma categoria antes de registrar lançamentos!")
        if st.button("🏷️ Ir para Categorias", use_container_width=True):
            st.session_state.current_page = "⚙️ Configurações"
            st.rerun()
        return
    
    # Mostra informações da obra atual
    st.info(f"📋 **Obra Ativa:** {obra_config['nome']} | **Orçamento:** {format_currency_br(obra_config['orcamento'])}")
    
    # INICIALIZA DADOS NO SESSION STATE
    if 'form_descricao' not in st.session_state:
        st.session_state.form_descricao = ""
    if 'form_valor' not in st.session_state:
        st.session_state.form_valor = 0.01
    if 'form_categoria' not in st.session_state:
        st.session_state.form_categoria = 0
    if 'form_data' not in st.session_state:
        st.session_state.form_data = date.today()
    if 'form_observacoes' not in st.session_state:
        st.session_state.form_observacoes = ""
    
    st.markdown("### 📝 Dados do Lançamento")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Campo descrição com callback
        descricao = st.text_input(
            "Descrição *",
            value=st.session_state.form_descricao,
            placeholder="Ex: Compra de cimento para fundação",
            key="input_descricao",
            on_change=update_form_descricao
        )
        
        # Campo valor com callback
        valor = st.number_input(
            "Valor (R$) *",
            min_value=0.01,
            step=0.01,
            format="%.2f",
            value=st.session_state.form_valor,
            key="input_valor",
            on_change=update_form_valor
        )
    
    with col2:
        # Selectbox para categorias
        categoria_options = [f"{cat['nome']}" for cat in categorias]
        categoria_ids = [cat['id'] for cat in categorias]
        
        categoria_index = st.selectbox(
            "Categoria *",
            options=range(len(categoria_options)),
            format_func=lambda x: categoria_options[x],
            index=st.session_state.form_categoria,
            key="input_categoria",
            on_change=update_form_categoria
        )
        
        # Campo data com callback
        data_lancamento = st.date_input(
            "Data do Lançamento *",
            value=st.session_state.form_data,
            max_value=date.today(),
            key="input_data",
            on_change=update_form_data
        )
    
    # Campo observações com callback
    observacoes = st.text_area(
        "Observações (opcional)",
        value=st.session_state.form_observacoes,
        placeholder="Informações adicionais sobre o lançamento...",
        key="input_observacoes",
        on_change=update_form_observacoes
    )
    
    # Mostra preview dos dados
    with st.expander("👁️ Preview dos Dados", expanded=False):
        st.write(f"**Descrição:** {st.session_state.form_descricao}")
        st.write(f"**Valor:** R$ {st.session_state.form_valor:.2f}")
        if categoria_index < len(categoria_options):
            st.write(f"**Categoria:** {categoria_options[categoria_index]}")
        st.write(f"**Data:** {st.session_state.form_data}")
        st.write(f"**Observações:** {st.session_state.form_observacoes}")
    
    # Botões de ação
    col_save, col_clear = st.columns(2)
    
    with col_save:
        if st.button("💾 REGISTRAR LANÇAMENTO", use_container_width=True, type="primary"):
            print(f"=== BOTÃO REGISTRAR CLICADO ===", file=sys.stderr)
            
            # Pega dados do session state
            desc = st.session_state.form_descricao
            val = st.session_state.form_valor
            cat_idx = st.session_state.form_categoria
            data = st.session_state.form_data
            obs = st.session_state.form_observacoes
            
            print(f"Dados do form: desc='{desc}', valor={val}, categoria_idx={cat_idx}", file=sys.stderr)
            
            # Validações
            erro = False
            
            if not desc or not desc.strip():
                st.error("⚠️ A descrição é obrigatória!")
                erro = True
            
            if val <= 0:
                st.error("⚠️ O valor deve ser maior que zero!")
                erro = True
            
            if cat_idx >= len(categoria_ids):
                st.error("⚠️ Categoria inválida!")
                erro = True
            
            if erro:
                return
            
            # Pega ID da categoria
            categoria_id = categoria_ids[cat_idx]
            categoria_nome = categoria_options[cat_idx]
            
            print(f"Salvando: categoria_id={categoria_id}, categoria_nome='{categoria_nome}'", file=sys.stderr)
            
            # Tenta salvar
            with st.spinner("Salvando lançamento..."):
                lancamento_id = save_lancamento_direto(
                    obra_config['id'],
                    categoria_id,
                    desc,
                    val,
                    data,
                    obs
                )
            
            if lancamento_id:
                st.success(f"✅ Lançamento registrado com sucesso! ID: {lancamento_id}")
                st.balloons()
                
                # Limpa formulário
                clear_form()
                
                # Limpa cache
                cache_keys = ['dashboard_cache', 'lancamentos_cache']
                for key in cache_keys:
                    if key in st.session_state:
                        del st.session_state[key]
                
                print("✅ Lançamento salvo, cache limpo", file=sys.stderr)
                
                # Aguarda e recarrega
                import time
                time.sleep(2)
                st.rerun()
            else:
                st.error("❌ Erro ao registrar lançamento!")
    
    with col_clear:
        if st.button("🗑️ LIMPAR FORMULÁRIO", use_container_width=True):
            clear_form()
            st.rerun()

# Funções de callback para atualizar session state
def update_form_descricao():
    st.session_state.form_descricao = st.session_state.input_descricao

def update_form_valor():
    st.session_state.form_valor = st.session_state.input_valor

def update_form_categoria():
    st.session_state.form_categoria = st.session_state.input_categoria

def update_form_data():
    st.session_state.form_data = st.session_state.input_data

def update_form_observacoes():
    st.session_state.form_observacoes = st.session_state.input_observacoes

def clear_form():
    """Limpa todos os campos do formulário"""
    st.session_state.form_descricao = ""
    st.session_state.form_valor = 0.01
    st.session_state.form_categoria = 0
    st.session_state.form_data = date.today()
    st.session_state.form_observacoes = ""
    
    # Limpa também os inputs
    form_keys = ['input_descricao', 'input_valor', 'input_categoria', 'input_data', 'input_observacoes']
    for key in form_keys:
        if key in st.session_state:
            del st.session_state[key]

def save_lancamento_direto(obra_id, categoria_id, descricao, valor, data_lancamento, observacoes):
    """Salva lançamento de forma mais direta"""
    try:
        print(f"=== SALVAMENTO DIRETO INICIADO ===", file=sys.stderr)
        print(f"Obra: {obra_id}, Categoria: {categoria_id}", file=sys.stderr)
        print(f"Descrição: '{descricao}'", file=sys.stderr)
        print(f"Valor: {valor} (tipo: {type(valor)})", file=sys.stderr)
        print(f"Data: {data_lancamento}", file=sys.stderr)
        
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        # Converte data
        if isinstance(data_lancamento, date):
            data_str = data_lancamento.strftime('%Y-%m-%d')
        else:
            data_str = str(data_lancamento)
        
        # Converte valor
        valor_float = float(valor)
        
        # Prepara observações
        obs_final = observacoes if observacoes and observacoes.strip() else None
        
        print(f"Dados convertidos - Data: {data_str}, Valor: {valor_float}, Obs: {obs_final}", file=sys.stderr)
        
        # Query mais simples
        if is_postgres:
            query = """
                INSERT INTO lancamentos (obra_id, categoria_id, descricao, valor, data_lancamento, observacoes, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id
            """
            params = (obra_id, categoria_id, descricao, valor_float, data_str, obs_final)
        else:
            query = """
                INSERT INTO lancamentos (obra_id, categoria_id, descricao, valor, data_lancamento, observacoes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """
            params = (obra_id, categoria_id, descricao, valor_float, data_str, obs_final)
        
        print(f"Executando query: {query}", file=sys.stderr)
        print(f"Parâmetros: {params}", file=sys.stderr)
        
        cursor.execute(query, params)
        
        # Pega ID
        if is_postgres:
            result = cursor.fetchone()
            lancamento_id = result['id'] if result else None
        else:
            lancamento_id = cursor.lastrowid
        
        print(f"ID obtido: {lancamento_id}", file=sys.stderr)
        
        if lancamento_id:
            conn.commit()
            print(f"✅ COMMIT realizado - Lançamento {lancamento_id} salvo", file=sys.stderr)
            
            # Verifica se foi salvo
            if is_postgres:
                cursor.execute("SELECT COUNT(*) as total FROM lancamentos WHERE obra_id = %s", (obra_id,))
            else:
                cursor.execute("SELECT COUNT(*) as total FROM lancamentos WHERE obra_id = ?", (obra_id,))
            
            total = cursor.fetchone()['total']
            print(f"Total de lançamentos na obra agora: {total}", file=sys.stderr)
            
            cursor.close()
            conn.close()
            return lancamento_id
        else:
            print("ERRO: ID não retornado", file=sys.stderr)
            conn.rollback()
            cursor.close()
            conn.close()
            return None
            
    except Exception as e:
        print(f"ERRO CRÍTICO no salvamento: {repr(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        
        if 'conn' in locals():
            try:
                conn.rollback()
            except:
                pass
        
        return None
    finally:
        try:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
        except:
            pass

def show_lista_lancamentos():
    """Lista todos os lançamentos"""
    st.subheader("📋 Lista de Lançamentos")
    
    # Botão para forçar atualização
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Atualizar", use_container_width=True):
            if 'lancamentos_cache' in st.session_state:
                del st.session_state['lancamentos_cache']
            st.rerun()
    
    # Busca lançamentos
    lancamentos = get_lancamentos()
    
    if not lancamentos:
        st.info("📝 Nenhum lançamento registrado ainda.")
        return
    
    # Estatísticas rápidas
    total_lancamentos = len(lancamentos)
    total_valor = sum(l['valor'] for l in lancamentos)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Total de Lançamentos", total_lancamentos)
    
    with col2:
        st.metric("�� Valor Total", format_currency_br(total_valor))
    
    with col3:
        if total_lancamentos > 0:
            media = total_valor / total_lancamentos
            st.metric("📈 Valor Médio", format_currency_br(media))
    
    st.markdown("---")
    
    # Lista de lançamentos
    for lancamento in lancamentos:
        with st.expander(f"🧾 {lancamento['descricao']} - {format_currency_br(lancamento['valor'])}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**📅 Data:** {format_date_br(lancamento['data_lancamento'])}")
                st.write(f"**🏷️ Categoria:** {lancamento['categoria_nome']}")
                st.write(f"**💰 Valor:** {format_currency_br(lancamento['valor'])}")
            
            with col2:
                if lancamento['observacoes']:
                    st.write(f"**📝 Observações:** {lancamento['observacoes']}")
            
            # Botão de excluir
            if st.button(f"🗑️ Excluir", key=f"delete_{lancamento['id']}", use_container_width=True):
                if delete_lancamento(lancamento['id']):
                    st.success("✅ Lançamento excluído!")
                    # Limpa cache
                    if 'lancamentos_cache' in st.session_state:
                        del st.session_state['lancamentos_cache']
                    if 'dashboard_cache' in st.session_state:
                        del st.session_state['dashboard_cache']
                    st.rerun()
                else:
                    st.error("❌ Erro ao excluir!")

def get_lancamentos():
    """Busca todos os lançamentos"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        # Busca obra ativa
        obra_config = get_obra_config()
        if not obra_config.get('id'):
            return []
        
        obra_id = obra_config['id']
        
        if is_postgres:
            query = """
                SELECT 
                    l.id, l.descricao, l.valor, l.data_lancamento, l.observacoes,
                    c.nome as categoria_nome, c.cor as categoria_cor
                FROM lancamentos l
                JOIN categorias c ON l.categoria_id = c.id
                WHERE l.obra_id = %s
                ORDER BY l.data_lancamento DESC, l.id DESC
            """
            cursor.execute(query, (obra_id,))
        else:
            query = """
                SELECT 
                    l.id, l.descricao, l.valor, l.data_lancamento, l.observacoes,
                    c.nome as categoria_nome, c.cor as categoria_cor
                FROM lancamentos l
                JOIN categorias c ON l.categoria_id = c.id
                WHERE l.obra_id = ?
                ORDER BY l.data_lancamento DESC, l.id DESC
            """
            cursor.execute(query, (obra_id,))
        
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
        
        print(f"Encontrados {len(lancamentos)} lançamentos na listagem", file=sys.stderr)
        return lancamentos
        
    except Exception as e:
        print(f"Erro ao buscar lançamentos: {repr(e)}", file=sys.stderr)
        return []
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def delete_lancamento(lancamento_id):
    """Exclui lançamento"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        if is_postgres:
            cursor.execute("DELETE FROM lancamentos WHERE id = %s", (lancamento_id,))
        else:
            cursor.execute("DELETE FROM lancamentos WHERE id = ?", (lancamento_id,))
        
        conn.commit()
        rows_affected = cursor.rowcount
        
        cursor.close()
        conn.close()
        
        print(f"Lançamento {lancamento_id} excluído. Linhas afetadas: {rows_affected}", file=sys.stderr)
        return rows_affected > 0
        
    except Exception as e:
        print(f"Erro ao excluir lançamento: {repr(e)}", file=sys.stderr)
        return False
    finally:
        try:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
        except:
            pass

def show_filtros_lancamentos():
    """Filtros e busca de lançamentos"""
    st.subheader("🔍 Buscar e Filtrar Lançamentos")
    st.info("Funcionalidade em desenvolvimento...")

# Funções auxiliares vazias para compatibilidade
def validate_file_upload(file):
    return True, "OK"

def save_file(lancamento_id, file):
    return True

def download_file(arquivo_id):
    pass