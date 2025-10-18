import streamlit as st
import sqlite3
import pandas as pd

def authenticate_user(email, senha):
    """Autentica usuário no sistema"""
    conn = sqlite3.connect('obra.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, nome, email, tipo FROM usuarios 
        WHERE email = ? AND senha = ? AND ativo = 1
    """, (email, senha))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            'id': user[0],
            'nome': user[1],
            'email': user[2],
            'tipo': user[3]
        }
    return None

def get_all_active_users():
    """Obtém todos os usuários ativos para login rápido"""
    conn = sqlite3.connect('obra.db')
    users = pd.read_sql_query("""
        SELECT id, nome, email, tipo FROM usuarios 
        WHERE ativo = 1 
        ORDER BY nome
    """, conn)
    conn.close()
    return users

def show_login_page():
    """Exibe página de login melhorada"""
    st.markdown("""
    <div class="login-container">
        <h1 class="login-title">🏗️ Sistema de Gestão de Obras</h1>
        <p class="login-subtitle">Controle Financeiro Profissional</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Login Rápido
    _show_quick_login()
    
    # Login Manual
    _show_manual_login()

def _show_quick_login():
    """Exibe seção de login rápido"""
    st.markdown("""
    <div class="quick-login-container">
        <h3 class="quick-login-title">🚀 Login Rápido</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Buscar usuários ativos
    users = get_all_active_users()
    
    if not users.empty:
        # Criar colunas para os botões de usuário
        num_users = len(users)
        cols = st.columns(min(num_users, 3))  # Máximo 3 colunas
        
        for idx, (_, user) in enumerate(users.iterrows()):
            col_idx = idx % 3
            with cols[col_idx]:
                # Emoji baseado no tipo
                emoji = "👤" if user['tipo'] == 'gestor' else "💼"
                
                # Card do usuário
                st.markdown(f"""
                <div class="info-card">
                    <div style="text-align: center;">
                        <div style="font-size: 2rem;">{emoji}</div>
                        <strong>{user['nome']}</strong><br>
                        <small>{user['tipo'].title()}</small><br>
                        <small style="color: #666;">{user['email']}</small>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Formulário para senha do usuário específico
                with st.form(f"quick_login_{user['id']}"):
                    senha_rapida = st.text_input(
                        "🔒 Senha", 
                        type="password", 
                        key=f"senha_{user['id']}",
                        placeholder="Digite sua senha"
                    )
                    
                    if st.form_submit_button(f"Entrar como {user['nome']}", use_container_width=True):
                        if senha_rapida:
                            auth_user = authenticate_user(user['email'], senha_rapida)
                            if auth_user:
                                st.session_state.user = auth_user
                                st.success(f"✅ Bem-vindo, {auth_user['nome']}!")
                                st.rerun()
                            else:
                                st.error("❌ Senha incorreta!")
                        else:
                            st.error("❌ Digite a senha!")

def _show_manual_login():
    """Exibe formulário de login manual"""
    st.markdown("---")
    
    with st.expander("🔐 Login Manual (Email + Senha)", expanded=False):
        with st.form("manual_login_form"):
            st.subheader("Login Completo")
            
            col1, col2 = st.columns(2)
            
            with col1:
                email = st.text_input("📧 Email", placeholder="seu@email.com")
            
            with col2:
                senha = st.text_input("🔒 Senha", type="password", placeholder="Sua senha")
            
            if st.form_submit_button("🚀 Entrar", use_container_width=True):
                if email and senha:
                    user = authenticate_user(email, senha)
                    if user:
                        st.session_state.user = user
                        st.success(f"✅ Bem-vindo, {user['nome']}!")
                        st.rerun()
                    else:
                        st.error("❌ Email ou senha incorretos!")
                else:
                    st.error("❌ Preencha email e senha!")
    
    # Informação básica sem senhas
    st.markdown("---")
    st.info("""
    💡 **Como usar**: 
    - **Login Rápido**: Selecione seu usuário e digite apenas a senha
    - **Login Manual**: Digite email completo e senha
    """)

def show_user_header(user, obra_config):
    """Exibe cabeçalho com informações do usuário"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"""
        <div class="obra-header">
            <h1>🏗️ {obra_config['nome_obra']}</h1>
            <p>Sistema de Gestão Financeira | Orçamento: R$ {obra_config['orcamento_total']:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="user-info">
            <strong>👤 {user['nome']}</strong><br>
            <small>{user['tipo'].title()}</small><br>
            <small>{user['email']}</small>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Sair", help="Fazer logout do sistema"):
            st.session_state.user = None
            st.rerun()