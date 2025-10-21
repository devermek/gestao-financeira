import streamlit as st
import hashlib
import os
import sys
import traceback
from config.database import get_db_connection, get_current_db_type

# ADICIONADO para lidar com tipos de retorno de banco de dados
import sqlite3 # Necessário para referenciar sqlite3.Row
try:
    import psycopg2.extras
    RealDictRow = psycopg2.extras.RealDictRow # Necessário para referenciar RealDictRow
except ImportError:
    # Define um tipo dummy caso psycopg2 não esteja instalado (ex: ambiente SQLite)
    RealDictRow = type(None) 
# FIM DAS LINHAS A SEREM ADICIONADAS

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
        print(f"DEBUG AUTH: Tentando login para email: {email}", file=sys.stderr); sys.stderr.flush()
        conn = get_db_connection()
        cursor = conn.cursor()
        db_type = get_current_db_type()

        param_placeholder = '%s' if db_type == 'postgresql' else '?'

        hashed_password = hash_password(password)

        query = f"""
            SELECT id, nome, email, tipo, ativo FROM usuarios
            WHERE email = {param_placeholder} AND senha = {param_placeholder} AND ativo = 1
        """
        
        cursor.execute(query, (email, hashed_password))
        user_data = cursor.fetchone()
        
        if user_data:
            if isinstance(user_data, (dict, RealDictRow)) or (hasattr(user_data, 'keys') and hasattr(user_data, '__getitem__')):
                return {
                    'id': user_data['id'],
                    'nome': user_data['nome'],
                    'email': user_data['email'],
                    'tipo': user_data['tipo'],
                    'ativo': user_data['ativo']
                }
            elif isinstance(user_data, sqlite3.Row):
                return {
                    'id': user_data['id'],
                    'nome': user_data['nome'],
                    'email': user_data['email'],
                    'tipo': user_data['tipo'],
                    'ativo': user_data['ativo']
                }
            else:
                return {
                    'id': user_data[0],
                    'nome': user_data[1],
                    'email': user_data[2],
                    'tipo': user_data[3],
                    'ativo': user_data[4]
                }
        print(f"DEBUG AUTH: Login falhou para email: {email} (credenciais incorretas ou inativo).", file=sys.stderr); sys.stderr.flush()
        return None
    except Exception as e:
        print(f"DEBUG AUTH: ERRO CRÍTICO ao tentar login para email {email}: {e}", file=sys.stderr);
        traceback.print_exc(file=sys.stderr); sys.stderr.flush()
        return None
    finally:
        if conn:
            conn.close()

def show_login_page():
    """Exibe a página de login."""
    st.title("🔐 Login")

    # A função original ensure_first_admin_exists() foi substituída
    # por uma versão de TESTE para isolar o problema.
    ensure_first_admin_exists()

    # Campos de input
    email = st.text_input("Email", key="login_email_input")
    password = st.text_input("Senha", type="password", key="login_password_input")

    # Botão de login
    if st.button("Entrar", type="primary"):
        if email and password:
            user = login_user(email, password)
            if user:
                st.session_state.user = user
                st.session_state.logged_in = True
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Email ou senha incorreta, ou usuário inativo.")
        else:
            st.warning("Por favor, preencha todos os campos.")

def show_user_header(user, obra_config):
    """Exibe o cabeçalho superior da aplicação com informações do usuário e da obra."""
    st.markdown(f"""
        <div style="background-color: #2c3e50; padding: 10px; border-radius: 5px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
            <div style="color: white; font-size: 1.2em; font-weight: bold;">
                ��️ {obra_config.get('nome_obra', 'NOME DA OBRA NÃO CONFIGURADO')}
            </div>
            <div style="color: #bdc3c7; font-size: 0.9em;">
                Usuário: <strong>{user.get('nome', 'N/A')}</strong> ({user.get('tipo', 'N/A').title()})
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("Sair", help="Fazer Logout"):
        st.session_state.user = None
        st.session_state.logged_in = False
        st.rerun()

# ESTA É A VERSÃO "DUMMY" (FALSA) DA FUNÇÃO ensure_first_admin_exists()
# Ela substituirá a lógica original para nos ajudar a depurar o problema.
def ensure_first_admin_exists():
    """
    Função ensure_first_admin_exists() temporariamente substituída para depuração.
    Ela apenas exibirá uma mensagem de sucesso na interface do Streamlit.
    """
    print("DEBUG AUTH: ensure_first_admin_exists() foi substituída para depuração.", file=sys.stderr)
    st.info("Atenção: A verificação/criação inicial de admin foi TEMPORARIAMENTE desativada para depuração.")
    sys.stderr.flush()
    # Nenhuma lógica de banco de dados será executada aqui nesta versão.

if __name__ == "__main__":
    st.set_page_config(layout="centered")
    show_login_page()