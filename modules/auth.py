import streamlit as st
import hashlib
import os
from config.database import get_db_connection, get_current_db_type # Importa as funções de conexão e tipo de DB
from utils.helpers import get_obra_config # Para buscar a config da obra no login, se necessário

# --- Funções de Autenticação ---

def hash_password(password):
    """Cria um hash SHA256 da senha."""
    return hashlib.sha256(password.encode()).hexdigest()

def login_user(email, password):
    """
    Tenta autenticar um usuário no banco de dados.
    Retorna o dicionário do usuário se a autenticação for bem-sucedida, caso contrário, None.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        db_type = get_current_db_type()

        # Usar %s para PostgreSQL e ? para SQLite para placeholders
        param_placeholder = '%s' if db_type == 'postgresql' else '?'

        hashed_password = hash_password(password)

        query = f"""
            SELECT id, nome, email, tipo, ativo FROM usuarios
            WHERE email = {param_placeholder} AND senha = {param_placeholder} AND ativo = 1
        """
        
        cursor.execute(query, (email, hashed_password))
        user_data = cursor.fetchone()
        
        if user_data:
            # Converte a tupla ou RealDictRow para um dicionário padrão
            if isinstance(user_data, dict): # Já é um RealDictRow do psycopg2
                return user_data
            else: # sqlite3.Row ou tupla
                return {
                    'id': user_data[0],
                    'nome': user_data[1],
                    'email': user_data[2],
                    'tipo': user_data[3],
                    'ativo': user_data[4]
                }
        return None
    except Exception as e:
        st.error(f"Erro ao tentar login: {e}")
        return None
    finally:
        if conn:
            conn.close()

def show_login_page():
    """Exibe a página de login."""
    st.title("🔐 Login")

    # Campos de input
    email = st.text_input("Email")
    password = st.text_input("Senha", type="password")

    # Botão de login
    if st.button("Entrar", type="primary"):
        if email and password:
            user = login_user(email, password)
            if user:
                st.session_state.user = user
                st.session_state.logged_in = True
                st.success("Login realizado com sucesso!")
                st.rerun() # Recarrega a página para sair do login e ir para o app
            else:
                st.error("Email ou senha incorretos, ou usuário inativo.")
        else:
            st.warning("Por favor, preencha todos os campos.")

# --- Cabeçalho do Usuário Logado ---

def show_user_header(user, obra_config):
    """Exibe o cabeçalho superior da aplicação com informações do usuário e da obra."""
    st.markdown(f"""
        <div style="background-color: #2c3e50; padding: 10px; border-radius: 5px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
            <div style="color: white; font-size: 1.2em; font-weight: bold;">
                🏗️ {obra_config.get('nome_obra', 'Nome da Obra')}
            </div>
            <div style="color: #bdc3c7; font-size: 0.9em;">
                Usuário: <strong>{user.get('nome', 'N/A')}</strong> ({user.get('tipo', 'N/A').title()})
            </div>
        </div>
    """, unsafe_allow_html=True)
    # Você pode adicionar mais elementos de cabeçalho aqui se necessário
    
    # Exemplo de botão de logout
    if st.sidebar.button("Sair", help="Fazer Logout"):
        st.session_state.user = None
        st.session_state.logged_in = False
        st.session_state.current_page = 'login' # Ou outra página inicial
        st.rerun()

# --- Placeholder para outras funções de usuário, se houver ---
# def show_profile_page(user):
#     st.subheader(f"Perfil de {user['nome']}")
#     st.write(f"Email: {user['email']}")
#     st.write(f"Tipo: {user['tipo']}")

# def register_user_page():
#     st.subheader("Registrar Novo Usuário")
#     # ... formulário de registro ...