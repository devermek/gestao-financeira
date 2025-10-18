import streamlit as st
import pandas as pd
import sqlite3

def show_usuarios(user):
    """Exibe página de gestão de usuários"""
    st.header("👥 Gestão de Usuários")
    
    # Listar usuários existentes
    _show_existing_users(user)
    
    # Adicionar novo usuário
    _show_add_user_form()

def _show_existing_users(current_user):
    """Exibe lista de usuários existentes"""
    conn = sqlite3.connect('obra.db')
    usuarios = pd.read_sql_query("SELECT * FROM usuarios WHERE ativo = 1 ORDER BY nome", conn)
    conn.close()
    
    if not usuarios.empty:
        st.subheader("👤 Usuários Cadastrados")
        
        for _, usr in usuarios.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.write(f"**{usr['nome']}**")
                
                with col2:
                    st.write(f"📧 {usr['email']}")
                
                with col3:
                    tipo_emoji = "👤" if usr['tipo'] == 'gestor' else "💼"
                    st.write(f"{tipo_emoji} {usr['tipo'].title()}")
                
                with col4:
                    if usr['id'] != current_user['id']:  # Não pode desativar a si mesmo
                        if st.button("🗑️", key=f"delete_user_{usr['id']}", help="Desativar usuário"):
                            _deactivate_user(usr['id'], usr['nome'])
                            st.rerun()
                
                st.markdown("---")

def _deactivate_user(user_id, user_name):
    """Desativa um usuário"""
    conn = sqlite3.connect('obra.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET ativo = 0 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    st.success(f"✅ Usuário '{user_name}' desativado!")

def _show_add_user_form():
    """Exibe formulário para adicionar novo usuário"""
    st.subheader("➕ Adicionar Novo Usuário")
    
    with st.form("novo_usuario"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome_usuario = st.text_input("Nome Completo", placeholder="Ex: João Silva")
            email_usuario = st.text_input("Email", placeholder="joao@email.com")
        
        with col2:
            senha_usuario = st.text_input("Senha", type="password", placeholder="Mínimo 6 caracteres")
            tipo_usuario = st.selectbox("Tipo de Usuário", ["investidor", "gestor"])
        
        if st.form_submit_button("✅ Adicionar Usuário", use_container_width=True):
            if nome_usuario and email_usuario and senha_usuario:
                if len(senha_usuario) >= 6:
                    if _create_user(nome_usuario, email_usuario, senha_usuario, tipo_usuario):
                        st.success("✅ Usuário adicionado com sucesso!")
                        st.rerun()
                else:
                    st.error("❌ Senha deve ter pelo menos 6 caracteres!")
            else:
                st.error("❌ Preencha todos os campos!")

def _create_user(nome, email, senha, tipo):
    """Cria um novo usuário"""
    conn = sqlite3.connect('obra.db')
    cursor = conn.cursor()
    
    # Verificar se email já existe
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE email = ?", (email,))
    if cursor.fetchone()[0] > 0:
        st.error("❌ Email já cadastrado!")
        conn.close()
        return False
    else:
        cursor.execute("INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)", 
                      (nome, email, senha, tipo))
        conn.commit()
        conn.close()
        return True