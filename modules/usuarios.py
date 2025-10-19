import streamlit as st
import pandas as pd
from config.database import get_db_connection, get_current_db_type
from modules.auth import hash_password # Reutiliza a função de hashing de senha

def show_usuarios(current_user):
    """Exibe a página de gestão de usuários."""
    st.header("�� Gestão de Usuários")
    st.success(f"DEBUG: show_usuarios chamado. Usuário logado: {current_user.get('nome', 'N/A')} ({current_user.get('tipo', 'N/A')})") # DEBUG LINE

    # Apenas usuários do tipo 'gestor' podem gerenciar outros usuários
    if current_user['tipo'] != 'gestor':
        st.warning("Você não tem permissão para gerenciar usuários. Por favor, contate o administrador.")
        st.success("DEBUG: Usuário NÃO é gestor, retornando.") # DEBUG LINE
        return

    st.success("DEBUG: Usuário é gestor, renderizando abas.") # DEBUG LINE
    # Abas para organizar o conteúdo
    tab1, tab2 = st.tabs(["📋 Listar Usuários", "➕ Adicionar Novo Usuário"])

    with tab1:
        st.success("DEBUG: Entrando na aba 'Listar Usuários'.") # DEBUG LINE
        _show_listar_usuarios(current_user)
    
    with tab2:
        st.success("DEBUG: Entrando na aba 'Adicionar Novo Usuário'.") # DEBUG LINE
        _show_adicionar_usuario()

def _show_listar_usuarios(current_user):
    """Exibe a lista de usuários cadastrados com opções de edição/desativação."""
    st.subheader("📋 Usuários Cadastrados")
    st.success("DEBUG: _show_listar_usuarios chamado.") # DEBUG LINE
    
    conn = None # Initialize conn
    try:
        conn = get_db_connection()
        query = "SELECT id, nome, email, tipo, ativo, created_at FROM usuarios ORDER BY nome"
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            st.info("Nenhum usuário cadastrado além do administrador padrão.")
            st.success("DEBUG: Nenhum usuário adicional cadastrado.") # DEBUG LINE
            return

        st.success(f"DEBUG: {len(df)} usuários encontrados para listar.") # DEBUG LINE
        # Exibe cada usuário em um expander para detalhes e edição
        for index, user in df.iterrows():
            user_status = "Ativo" if user['ativo'] == 1 else "Inativo"
            status_emoji = "✅" if user['ativo'] == 1 else "❌"
            
            with st.expander(f"{status_emoji} {user['nome']} ({user['tipo'].title()}) - {user['email']}"):
                st.write(f"**ID:** {user['id']}")
                st.write(f"**Email:** {user['email']}")
                st.write(f"**Tipo:** {user['tipo'].title()}")
                st.write(f"**Status:** {user_status}")
                st.write(f"**Criado em:** {user['created_at']}")

                # Formulário para editar este usuário específico
                with st.form(key=f"edit_user_form_{user['id']}"):
                    st.markdown("##### Editar Usuário")
                    col1, col2 = st.columns(2)
                    with col1:
                        new_name = st.text_input("Nome", value=user['nome'], key=f"edit_name_{user['id']}")
                        new_email = st.text_input("Email", value=user['email'], key=f"edit_email_{user['id']}")
                    with col2:
                        # Index para o selectbox
                        tipo_index = 0 if user['tipo'] == "gestor" else 1
                        new_type = st.selectbox("Tipo", ["gestor", "investidor"], index=tipo_index, key=f"edit_type_{user['id']}")
                        new_status = st.checkbox("Ativo", value=user['ativo'] == 1, key=f"edit_status_{user['id']}")
                    
                    st.info("Deixe o campo de senha em branco para não alterar a senha atual.")
                    new_password = st.text_input("Nova Senha", type="password", key=f"edit_password_{user['id']}")
                    confirm_new_password = st.text_input("Confirmar Nova Senha", type="password", key=f"confirm_edit_password_{user['id']}")

                    col_buttons = st.columns([1, 1, 1]) # 3 colunas para os botões
                    with col_buttons[0]:
                        if st.form_submit_button("💾 Salvar Alterações", type="primary", key=f"save_edit_{user['id']}"):
                            _update_user(user['id'], new_name, new_email, new_type, 1 if new_status else 0, new_password, confirm_new_password)
                    with col_buttons[1]:
                        # Botão para alternar status (Ativar/Desativar)
                        btn_label = "❌ Desativar Usuário" if user['ativo'] == 1 else "✅ Ativar Usuário"
                        if st.form_submit_button(btn_label, type="secondary", key=f"toggle_status_{user['id']}"):
                            if current_user['id'] == user['id']:
                                st.error("Você não pode desativar sua própria conta.")
                            else:
                                _toggle_user_status(user['id'], 1 if user['ativo'] == 0 else 0) # Inverte o status
                    with col_buttons[2]:
                        # Botão de exclusão
                        if st.form_submit_button("🗑️ Excluir Usuário", type="secondary", key=f"delete_user_{user['id']}"):
                            if current_user['id'] == user['id']:
                                st.error("Você não pode excluir sua própria conta enquanto estiver logado.")
                            else:
                                # Confirmação antes de excluir
                                st.warning(f"Tem certeza que deseja excluir o usuário '{user['nome']}'? Esta ação é irreversível.")
                                if st.button(f"Sim, Excluir {user['nome']}", key=f"confirm_delete_{user['id']}"):
                                    _delete_user(user['id'])

    except Exception as e:
        st.error(f"❌ Erro ao listar usuários: {e}")
        st.error(f"DEBUG: Erro em _show_listar_usuarios: {e}") # DEBUG LINE
        # import traceback
        # st.code(traceback.format_exc()) # Descomente para debug mais aprofundado
    finally:
        if conn:
            conn.close()

def _show_adicionar_usuario():
    """Exibe o formulário para adicionar um novo usuário."""
    st.subheader("➕ Adicionar Novo Usuário")
    st.success("DEBUG: _show_adicionar_usuario chamado.") # DEBUG LINE
    with st.form("add_user_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome Completo", key="add_user_name")
            email = st.text_input("Email", key="add_user_email")
        with col2:
            tipo = st.selectbox("Tipo de Usuário", ["gestor", "investidor"], key="add_user_type")
            status_ativo = st.checkbox("Ativo", value=True, key="add_user_active")
        
        password = st.text_input("Senha", type="password", key="add_user_password")
        confirm_password = st.text_input("Confirmar Senha", type="password", key="add_user_confirm_password")

        if st.form_submit_button("✅ Criar Usuário", type="primary"):
            _add_new_user(nome, email, tipo, 1 if status_ativo else 0, password, confirm_password)

def _add_new_user(nome, email, tipo, ativo, password, confirm_password):
    """Lógica para adicionar um novo usuário ao banco de dados."""
    st.success("DEBUG: _add_new_user chamado para adicionar.") # DEBUG LINE
    # Validação básica
    if not nome or not email or not password or not confirm_password:
        st.error("❌ Todos os campos obrigatórios (Nome, Email, Senha, Confirmação) devem ser preenchidos.")
        st.success("DEBUG: Validação falhou: Campos obrigatórios ausentes.") # DEBUG LINE
        return
    if password != confirm_password:
        st.error("❌ A senha e a confirmação de senha não coincidem.")
        st.success("DEBUG: Validação falhou: Senhas não coincidem.") # DEBUG LINE
        return
    if len(password) < 6: # Exemplo de política de senha
        st.error("❌ A senha deve ter no mínimo 6 caracteres.")
        st.success("DEBUG: Validação falhou: Senha muito curta.") # DEBUG LINE
        return
    
    # Validação de formato de email (pode ser mais robusta com regex)
    if "@" not in email or "." not in email:
        st.error("❌ Formato de email inválido.")
        st.success("DEBUG: Validação falhou: Email inválido.") # DEBUG LINE
        return

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        db_type = get_current_db_type()
        param_placeholder = '%s' if db_type == 'postgresql' else '?'

        # Verificar se o email já existe
        cursor.execute(f"SELECT COUNT(*) FROM usuarios WHERE email = {param_placeholder}", (email,))
        if cursor.fetchone()[0] > 0:
            st.error(f"❌ Já existe um usuário com o email '{email}'.")
            st.success(f"DEBUG: Validação falhou: Email '{email}' já existe.") # DEBUG LINE
            return

        hashed_password = hash_password(password)

        insert_query = f"""
            INSERT INTO usuarios (nome, email, senha, tipo, ativo)
            VALUES ({param_placeholder}, {param_placeholder}, {param_placeholder}, {param_placeholder}, {param_placeholder})
        """
        cursor.execute(insert_query, (nome, email, hashed_password, tipo, ativo))
        conn.commit()
        st.success(f"🎉 Usuário '{nome}' ({email}) criado com sucesso!")
        st.success("DEBUG: Usuário adicionado com sucesso. Recarregando.") # DEBUG LINE
        st.rerun() # Atualiza a página para mostrar o novo usuário na lista
    except Exception as e:
        st.error(f"❌ Erro ao criar usuário: {e}")
        st.error(f"DEBUG: Erro ao adicionar usuário: {e}") # DEBUG LINE
        # import traceback
        # st.code(traceback.format_exc()) # Descomente para debug
    finally:
        if conn:
            conn.close()

def _update_user(user_id, new_name, new_email, new_type, new_status_int, new_password, confirm_new_password):
    """Lógica para atualizar um usuário existente."""
    st.success(f"DEBUG: _update_user chamado para ID {user_id}.") # DEBUG LINE
    # Validação similar à adição, mas para atualização
    if not new_name or not new_email:
        st.error("❌ Nome e Email são campos obrigatórios.")
        st.success("DEBUG: Validação falhou: Nome/Email ausentes na atualização.") # DEBUG LINE
        return
    if new_password and new_password != confirm_new_password:
        st.error("❌ A nova senha e a confirmação de senha não coincidem.")
        st.success("DEBUG: Validação falhou: Senhas não coincidem na atualização.") # DEBUG LINE
        return
    if new_password and len(new_password) < 6:
        st.error("❌ A nova senha deve ter no mínimo 6 caracteres.")
        st.success("DEBUG: Validação falhou: Senha muito curta na atualização.") # DEBUG LINE
        return
    if "@" not in new_email or "." not in new_email:
        st.error("❌ Formato de email inválido.")
        st.success("DEBUG: Validação falhou: Email inválido na atualização.") # DEBUG LINE
        return

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        db_type = get_current_db_type()
        param_placeholder = '%s' if db_type == 'postgresql' else '?'

        # Verificar se o novo email já existe para outro usuário (excluindo o usuário atual)
        cursor.execute(f"SELECT COUNT(*) FROM usuarios WHERE email = {param_placeholder} AND id != {param_placeholder}", (new_email, user_id))
        if cursor.fetchone()[0] > 0:
            st.error(f"❌ Já existe outro usuário com o email '{new_email}'.")
            st.success(f"DEBUG: Validação falhou: Email '{new_email}' já existe para outro usuário.") # DEBUG LINE
            return

        update_fields = ["nome", "email", "tipo", "ativo"]
        update_values = [new_name, new_email, new_type, new_status_int]
        
        if new_password: # Se uma nova senha foi fornecida
            update_fields.append("senha")
            update_values.append(hash_password(new_password))

        # Constrói a query dinamicamente
        update_query = f"UPDATE usuarios SET {', '.join([f'{field} = {param_placeholder}' for field in update_fields])} WHERE id = {param_placeholder}"
        cursor.execute(update_query, tuple(update_values + [user_id]))
        conn.commit()
        st.success(f"🎉 Usuário ID {user_id} atualizado com sucesso!")
        st.success("DEBUG: Usuário atualizado com sucesso. Recarregando.") # DEBUG LINE
        st.rerun()
    except Exception as e:
        st.error(f"❌ Erro ao atualizar usuário: {e}")
        st.error(f"DEBUG: Erro ao atualizar usuário: {e}") # DEBUG LINE
        # import traceback
        # st.code(traceback.format_exc()) # Descomente para debug
    finally:
        if conn:
            conn.close()

def _toggle_user_status(user_id, new_status_int):
    """Lógica para ativar ou desativar um usuário."""
    st.success(f"DEBUG: _toggle_user_status chamado para ID {user_id}, novo status: {new_status_int}.") # DEBUG LINE
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        db_type = get_current_db_type()
        param_placeholder = '%s' if db_type == 'postgresql' else '?'
        
        cursor.execute(f"UPDATE usuarios SET ativo = {param_placeholder} WHERE id = {param_placeholder}", (new_status_int, user_id))
        conn.commit()
        status_text = "ativado" if new_status_int == 1 else "desativado"
        st.success(f"�� Usuário ID {user_id} {status_text} com sucesso!")
        st.success("DEBUG: Status do usuário alterado com sucesso. Recarregando.") # DEBUG LINE
        st.rerun()
    except Exception as e:
        st.error(f"❌ Erro ao alternar status do usuário: {e}")
        st.error(f"DEBUG: Erro ao alternar status do usuário: {e}") # DEBUG LINE
        # import traceback
        # st.code(traceback.format_exc()) # Descomente para debug
    finally:
        if conn:
            conn.close()

def _delete_user(user_id):
    """Lógica para excluir um usuário."""
    st.success(f"DEBUG: _delete_user chamado para ID {user_id}.") # DEBUG LINE
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        db_type = get_current_db_type()
        param_placeholder = '%s' if db_type == 'postgresql' else '?'

        # Antes de deletar o usuário, é importante deletar quaisquer lançamentos
        # ou arquivos associados para evitar erros de FOREIGN KEY, ou configurar CASCADE DELETE na tabela.
        # Por simplicidade, aqui vamos focar apenas no delete do usuário,
        # mas em um sistema real, essa lógica de integridade é crucial.

        cursor.execute(f"DELETE FROM usuarios WHERE id = {param_placeholder}", (user_id,))
        conn.commit()
        st.success(f"🎉 Usuário ID {user_id} excluído permanentemente com sucesso!")
        st.success("DEBUG: Usuário excluído com sucesso. Recarregando.") # DEBUG LINE
        st.rerun()
    except Exception as e:
        st.error(f"❌ Erro ao excluir usuário: {e}")
        st.info("Verifique se há lançamentos ou arquivos associados a este usuário que precisam ser tratados primeiro.")
        st.error(f"DEBUG: Erro ao excluir usuário: {e}") # DEBUG LINE
        # import traceback
        # st.code(traceback.format_exc()) # Descomente para debug
    finally:
        if conn:
            conn.close()
