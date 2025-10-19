import streamlit as st
import hashlib
import os
from config.database import get_db_connection, get_current_db_type

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
                    'id': user_data['id'] if isinstance(user_data, st.connections.SQLConnection) else user_data[0],
                    'nome': user_data['nome'] if isinstance(user_data, st.connections.SQLConnection) else user_data[1],
                    'email': user_data['email'] if isinstance(user_data, st.connections.SQLConnection) else user_data[2],
                    'tipo': user_data['tipo'] if isinstance(user_data, st.connections.SQLConnection) else user_data[3],
                    'ativo': user_data['ativo'] if isinstance(user_data, st.connections.SQLConnection) else user_data[4]
                }
        return None
    except Exception as e:
        # st.error(f"Erro ao tentar login: {e}") # Comentar para evitar spam na tela
        print(f"Erro ao tentar login: {e}") # Imprimir no console para debug
        return None
    finally:
        if conn:
            conn.close()

def show_login_page():
    """Exibe a página de login."""
    st.title("🔐 Login")

    # Garante que um admin inicial exista
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
                st.rerun() # Recarrega a página para sair do login e ir para o app
            else:
                st.error("Email ou senha incorretos, ou usuário inativo.")
        else:
            st.warning("Por favor, preencha todos os campos.")

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
    
    # Botão de logout na sidebar
    if st.sidebar.button("Sair", help="Fazer Logout"):
        st.session_state.user = None
        st.session_state.logged_in = False
        # Redireciona para a página de login para que o show_login_page seja chamado
        st.rerun() # Reinicia a aplicação, que vai parar na tela de login

def ensure_first_admin_exists():
    """
    Verifica se existe algum usuário na tabela 'usuarios'.
    Se não houver, cria um usuário 'gestor' padrão.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        db_type = get_current_db_type()

        # Verifica se já existe algum usuário
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        count = cursor.fetchone()[0]

        if count == 0:
            st.warning("Nenhum usuário encontrado. Criando usuário administrador padrão.")
            default_email = "admin@obra.com"
            default_password = "admin" # Senha fácil para o primeiro login
            hashed_default_password = hash_password(default_password)

            # Usar %s para PostgreSQL e ? para SQLite para placeholders
            param_placeholder_str = '%s' if db_type == 'postgresql' else '?'

            # Inserir o usuário gestor padrão
            insert_query = f"""
                INSERT INTO usuarios (nome, email, senha, tipo, ativo)
                VALUES ({param_placeholder_str}, {param_placeholder_str}, {param_placeholder_str}, {param_placeholder_str}, 1)
            """
            cursor.execute(insert_query, ("Administrador", default_email, hashed_default_password, "gestor"))
            conn.commit()
            st.success(f"Usuário administrador criado: Email '{default_email}', Senha '{default_password}'. Por favor, faça login.")
            st.info("⚠️ Recomendamos alterar a senha após o primeiro login.")
        else:
            # st.info(f"Usuários encontrados: {count}. O sistema está pronto para login.") # Apenas para debug
            pass # Não mostra nada se já tem usuários
            
    except Exception as e:
        st.error(f"Erro ao verificar/criar usuário administrador inicial: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Este bloco é executado apenas se 'auth.py' for o script principal,
    # o que não é o caso quando é importado por 'app.py'.
    # É útil para testar funções isoladamente, mas não afetará o fluxo do app.
    st.set_page_config(layout="centered")
    show_login_page()
