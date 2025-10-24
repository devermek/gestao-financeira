import sys
import streamlit as st
from datetime import date, datetime
from config.database import get_connection
from utils.helpers import get_obra_config, get_categorias_ativas, format_currency_br

def show_configuracoes():
    """Exibe página de configurações"""
    st.title("⚙️ Configurações do Sistema")
    
    # Tabs para diferentes configurações
    tab1, tab2 = st.tabs(["🏗️ Configuração da Obra", "🏷️ Gestão de Categorias"])
    
    with tab1:
        _show_obra_config()
    
    with tab2:
        _show_categorias_config()

def _show_obra_config():
    """Configurações da obra"""
    st.subheader("🏗️ Configuração da Obra")
    
    # Carrega configuração atual
    obra_config = get_obra_config()
    
    with st.form("config_obra_form"):
        st.markdown("### Dados Principais")
        
        col1, col2 = st.columns(2)
        
        with col1:
            nome_obra = st.text_input(
                "Nome da Obra",
                value=obra_config.get('nome', '') if obra_config.get('nome') != 'Obra não configurada' else '',
                placeholder="Ex: Construção Casa João"
            )
            
            orcamento = st.number_input(
                "Orçamento Total (R$)",
                min_value=0.0,
                value=float(obra_config.get('orcamento', 0.0)),
                step=1000.0,
                format="%.2f"
            )
        
        with col2:
            data_inicio = st.date_input(
                "Data de Início",
                value=obra_config.get('data_inicio') or date.today()
            )
            
            data_fim = st.date_input(
                "Data de Término Prevista",
                value=obra_config.get('data_fim_prevista') or date.today()
            )
        
        # Validações
        if data_fim < data_inicio:
            st.error("⚠️ A data de término deve ser posterior à data de início!")
        
        submitted = st.form_submit_button("💾 Salvar Configurações", use_container_width=True)
        
        if submitted:
            if not nome_obra.strip():
                st.error("⚠️ O nome da obra é obrigatório!")
            elif orcamento <= 0:
                st.error("⚠️ O orçamento deve ser maior que zero!")
            elif data_fim < data_inicio:
                st.error("⚠️ A data de término deve ser posterior à data de início!")
            else:
                if _save_obra_config(nome_obra, orcamento, data_inicio, data_fim):
                    st.success("✅ Configurações salvas com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar configurações!")
    
    # Exibe informações atuais
    if obra_config.get('id'):
        st.markdown("---")
        st.markdown("### 📊 Informações Atuais")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("💰 Orçamento", format_currency_br(obra_config.get('orcamento', 0)))
        
        with col2:
            if obra_config.get('data_inicio'):
                dias_decorridos = (date.today() - obra_config['data_inicio']).days
                st.metric("�� Dias Decorridos", f"{dias_decorridos} dias")
        
        with col3:
            if obra_config.get('data_fim_prevista'):
                dias_restantes = (obra_config['data_fim_prevista'] - date.today()).days
                st.metric("⏰ Dias Restantes", f"{dias_restantes} dias")

def _save_obra_config(nome, orcamento, data_inicio, data_fim):
    """Salva configuração da obra"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        # Verifica se já existe uma obra
        cursor.execute("SELECT id FROM obras WHERE ativo = %s" if is_postgres else "SELECT id FROM obras WHERE ativo = ?", 
                      (True if is_postgres else 1,))
        
        existing_obra = cursor.fetchone()
        
        if existing_obra:
            # Atualiza obra existente
            if is_postgres:
                query = """
                    UPDATE obras 
                    SET nome = %s, orcamento = %s, data_inicio = %s, data_fim_prevista = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """
            else:
                query = """
                    UPDATE obras 
                    SET nome = ?, orcamento = ?, data_inicio = ?, data_fim_prevista = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """
            
            cursor.execute(query, (nome, orcamento, data_inicio, data_fim, existing_obra['id']))
        else:
            # Cria nova obra
            if is_postgres:
                query = """
                    INSERT INTO obras (nome, orcamento, data_inicio, data_fim_prevista, ativo)
                    VALUES (%s, %s, %s, %s, %s)
                """
            else:
                query = """
                    INSERT INTO obras (nome, orcamento, data_inicio, data_fim_prevista, ativo)
                    VALUES (?, ?, ?, ?, ?)
                """
            
            cursor.execute(query, (nome, orcamento, data_inicio, data_fim, True if is_postgres else 1))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Erro ao salvar configuração da obra: {repr(e)}", file=sys.stderr)
        conn.rollback()
        return False
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def _show_categorias_config():
    """Gestão de categorias"""
    st.subheader("🏷️ Gestão de Categorias")
    
    # Formulário para nova categoria
    with st.expander("➕ Adicionar Nova Categoria", expanded=False):
        with st.form("nova_categoria_form"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                nome_categoria = st.text_input("Nome da Categoria", placeholder="Ex: Material Elétrico")
                descricao_categoria = st.text_area("Descrição (opcional)", placeholder="Descrição da categoria...")
            
            with col2:
                cor_categoria = st.color_picker("Cor da Categoria", value="#3498db")
                st.write("**Preview:**")
                st.markdown(
                    f'<div style="background-color: {cor_categoria}; color: white; padding: 10px; '
                    f'border-radius: 5px; text-align: center;">{nome_categoria or "Nome da Categoria"}</div>',
                    unsafe_allow_html=True
                )
            
            submitted = st.form_submit_button("➕ Adicionar Categoria", use_container_width=True)
            
            if submitted:
                if not nome_categoria.strip():
                    st.error("⚠️ O nome da categoria é obrigatório!")
                else:
                    if _save_categoria(nome_categoria, descricao_categoria, cor_categoria):
                        st.success("✅ Categoria adicionada com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao adicionar categoria!")
    
    # Lista de categorias existentes
    st.markdown("### 📋 Categorias Existentes")
    
    categorias = _get_all_categorias()
    
    if not categorias:
        st.info("Nenhuma categoria cadastrada ainda.")
        return
    
    for categoria in categorias:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            
            with col1:
                # Nome com indicador de cor
                st.markdown(
                    f'<div style="display: flex; align-items: center;">'
                    f'<div style="width: 20px; height: 20px; background-color: {categoria["cor"]}; '
                    f'border-radius: 50%; margin-right: 10px;"></div>'
                    f'<strong>{categoria["nome"]}</strong></div>',
                    unsafe_allow_html=True
                )
                if categoria['descricao']:
                    st.caption(categoria['descricao'])
            
            with col2:
                # Status
                status = "✅ Ativa" if categoria['ativo'] else "❌ Inativa"
                st.write(status)
            
            with col3:
                # Botão editar
                if st.button("✏️", key=f"edit_{categoria['id']}", help="Editar categoria"):
                    st.session_state[f"editing_{categoria['id']}"] = True
                    st.rerun()
            
            with col4:
                # Botão ativar/desativar
                if categoria['ativo']:
                    if st.button("🚫", key=f"deactivate_{categoria['id']}", help="Desativar categoria"):
                        if _toggle_categoria_status(categoria['id'], False):
                            st.success("Categoria desativada!")
                            st.rerun()
                else:
                    if st.button("✅", key=f"activate_{categoria['id']}", help="Ativar categoria"):
                        if _toggle_categoria_status(categoria['id'], True):
                            st.success("Categoria ativada!")
                            st.rerun()
            
            # Formulário de edição (se ativo)
            if st.session_state.get(f"editing_{categoria['id']}", False):
                with st.form(f"edit_categoria_{categoria['id']}"):
                    st.markdown("**Editando Categoria:**")
                    
                    edit_col1, edit_col2 = st.columns([2, 1])
                    
                    with edit_col1:
                        novo_nome = st.text_input("Nome", value=categoria['nome'], key=f"nome_{categoria['id']}")
                        nova_descricao = st.text_area("Descrição", value=categoria['descricao'] or "", key=f"desc_{categoria['id']}")
                    
                    with edit_col2:
                        nova_cor = st.color_picker("Cor", value=categoria['cor'], key=f"cor_{categoria['id']}")
                    
                    edit_col1, edit_col2 = st.columns(2)
                    
                    with edit_col1:
                        if st.form_submit_button("💾 Salvar", use_container_width=True):
                            if _update_categoria(categoria['id'], novo_nome, nova_descricao, nova_cor):
                                st.success("Categoria atualizada!")
                                del st.session_state[f"editing_{categoria['id']}"]
                                st.rerun()
                            else:
                                st.error("Erro ao atualizar categoria!")
                    
                    with edit_col2:
                        if st.form_submit_button("❌ Cancelar", use_container_width=True):
                            del st.session_state[f"editing_{categoria['id']}"]
                            st.rerun()
            
            st.divider()

def _save_categoria(nome, descricao, cor):
    """Salva nova categoria"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        if is_postgres:
            query = """
                INSERT INTO categorias (nome, descricao, cor, ativo)
                VALUES (%s, %s, %s, %s)
            """
        else:
            query = """
                INSERT INTO categorias (nome, descricao, cor, ativo)
                VALUES (?, ?, ?, ?)
            """
        
        cursor.execute(query, (nome, descricao, cor, True if is_postgres else 1))
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Erro ao salvar categoria: {repr(e)}", file=sys.stderr)
        conn.rollback()
        return False
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def _get_all_categorias():
    """Busca todas as categorias (ativas e inativas)"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, nome, descricao, cor, ativo, created_at
            FROM categorias
            ORDER BY ativo DESC, nome ASC
        """)
        
        categorias = []
        for row in cursor.fetchall():
            categorias.append({
                'id': row['id'],
                'nome': row['nome'],
                'descricao': row['descricao'],
                'cor': row['cor'],
                'ativo': bool(row['ativo']),
                'created_at': row['created_at']
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

def _update_categoria(categoria_id, nome, descricao, cor):
    """Atualiza categoria existente"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        if is_postgres:
            query = """
                UPDATE categorias 
                SET nome = %s, descricao = %s, cor = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
        else:
            query = """
                UPDATE categorias 
                SET nome = ?, descricao = ?, cor = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
        
        cursor.execute(query, (nome, descricao, cor, categoria_id))
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Erro ao atualizar categoria: {repr(e)}", file=sys.stderr)
        conn.rollback()
        return False
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def _toggle_categoria_status(categoria_id, ativo):
    """Ativa/desativa categoria"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        if is_postgres:
            query = """
                UPDATE categorias 
                SET ativo = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
        else:
            query = """
                UPDATE categorias 
                SET ativo = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
        
        cursor.execute(query, (ativo if is_postgres else (1 if ativo else 0), categoria_id))
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Erro ao alterar status da categoria: {repr(e)}", file=sys.stderr)
        conn.rollback()
        return False
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass