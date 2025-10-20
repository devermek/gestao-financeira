import streamlit as st
import hashlib
import os
from config.database import get_db_connection
import sys
import traceback

# --- Funções de Autenticação ---

def hash_password(password):
    """Cria um hash SHA256 da senha."""
    return hashlib.sha256(password.encode()).hexdigest()

def login_user(email, password):
    """
    Tenta autenticar um usuário no banco de dados.
    Retorna o dicionário do usuário se a autenticação for bem-sucedida, caso contrário, None.
    """
    print(f"DEBUG AUTH LOGIN: Tentando login para {email}", file=sys.stderr)
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        hashed_password = hash_password(password)

        query = """
            SELECT id, nome, email, tipo, ativo FROM usuarios
            WHERE email = %s AND senha = %s AND ativo = 1
        """
        
        cursor.execute(query, (email, hashed_password))
        user_data = cursor.fetchone()
        
        if user_data:
            if isinstance(user_data, dict): 
                print(f"DEBUG AUTH LOGIN: Sucesso (dict) para {email}", file=sys.stderr)
                return user_data
            else: # sqlite3.Row ou tupla de SQLite
                print(f"DEBUG AUTH LOGIN: Sucesso (tupla/Row) para {email}", file=sys.stderr)
                try:
                    return {
                        'id': user_data['id'],
                        'nome': user_data['nome'],
                        'email': user_data['email'],
                        'tipo': user_data['tipo'],
                        'ativo': user_data['ativo']
                    }
                except (KeyError, TypeError): # Fallback para tupla por índice
                     return {
                        'id': user_data[0],
                        'nome': user_data[1],
                        'email': user_data[2],
                        'tipo': user_data[3],
                        'ativo': user_data[4]
                    }
        print(f"DEBUG AUTH LOGIN: Falha para {email} (credenciais inválidas ou inativo)", file=sys.stderr)
        return None
    except Exception as e:
        print(f"DEBUG AUTH LOGIN ERROR: Erro ao tentar login para {email}: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return None
    finally:
        if conn:
            conn.close()

def show_login_page():
    """Exibe a página de login."""
    st.title("🔐 Login")

    # Garante que um admin inicial exista
    # Removendo st.error/warning daqui para evitar que o Streamlit engula logs de erro
    admin_setup_success = ensure_first_admin_exists()
    # if not admin_setup_success: # Comentado para evitar st.error aqui
    #     st.error("⚠️ Não foi possível verificar ou criar o usuário administrador inicial. Por favor, verifique os logs do servidor.")


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
        st.rerun() 

def ensure_first_admin_exists():
    """
    Verifica se existe algum usuário na tabela 'usuarios'.
    Se não houver, cria um usuário 'gestor' padrão.
    Retorna True se a operação foi bem-sucedida, False caso contrário.
    """
    print("DEBUG AUTH ensure_first_admin_exists: --- INICIANDO ---", file=sys.stderr)
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("DEBUG AUTH ensure_first_admin_exists: Conexão e cursor obtidos.", file=sys.stderr)

        # Verifica se já existe algum usuário
        print("DEBUG AUTH ensure_first_admin_exists: Executando COUNT(*)", file=sys.stderr)
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        
        # Torna a leitura do count mais robusta para evitar None[0]
        count_result = cursor.fetchone()
        count = count_result[0] if count_result else 0 
        print(f"DEBUG AUTH ensure_first_admin_exists: Total de usuários: {count}", file=sys.stderr)

        if count == 0:
            # st.warning("Nenhum usuário encontrado. Criando usuário administrador padrão.", icon="⚠️") # REMOVIDO
            print("DEBUG AUTH ensure_first_admin_exists: Nenhum usuário encontrado. Criando admin.", file=sys.stderr)
            default_email = "admin@obra.com"
            default_password = "admin" 
            hashed_default_password = hash_password(default_password)

            insert_query = """
                INSERT INTO usuarios (nome, email, senha, tipo, ativo)
                VALUES (%s, %s, %s, %s, 1)
            """
            print(f"DEBUG AUTH ensure_first_admin_exists: Executando INSERT para {default_email}", file=sys.stderr)
            cursor.execute(insert_query, ("Administrador", default_email, hashed_default_password, "gestor"))
            conn.commit()
            print("DEBUG AUTH ensure_first_admin_exists: COMMIT realizado.", file=sys.stderr)
            # st.success(f"Usuário administrador criado: Email '{default_email}', Senha '{default_password}'. Por favor, faça login.", icon="✅") # REMOVIDO
            # st.info("⚠️ Recomendamos alterar a senha após o primeiro login.", icon="ℹ️") # REMOVIDO
            print("DEBUG AUTH ensure_first_admin_exists: Admin criado com sucesso (sem feedback UI).", file=sys.stderr)
        else:
            print(f"DEBUG AUTH ensure_first_admin_exists: Já existem {count} usuários. Nenhuma ação necessária.", file=sys.stderr)
            
    except Exception as e:
        print(f"DEBUG AUTH ensure_first_admin_exists ERROR: {e}", file=sys.stderr)
        print("DEBUG AUTH ensure_first_admin_exists ERROR: Traceback completo abaixo:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr) 
        print("DEBUG AUTH ensure_first_admin_exists ERROR: --- FIM DO TRACEBACK ---", file=sys.stderr)
        return False
    finally:
        if conn:
            conn.close()
            print("DEBUG AUTH ensure_first_admin_exists: Conexão fechada.", file=sys.stderr)
    print("DEBUG AUTH ensure_first_admin_exists: --- FINALIZANDO ---", file=sys.stderr)
    return True

if __name__ == "__main__":
    st.set_page_config(layout="centered")
    show_login_page()