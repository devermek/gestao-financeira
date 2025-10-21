import streamlit as st
import hashlib
import os
import sys
import traceback
from config.database import get_db_connection # REMOVIDO: get_current_db_type

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
        conn, db_type = get_db_connection() # <-- AGORA OBTEMOS O TIPO DE DB REAL AQUI
        cursor = conn.cursor()

        param_placeholder = '%s' if db_type == 'postgresql' else '?' # <-- USADO O TIPO DE DB REAL

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
                🏗️ {obra_config.get('nome_obra', 'NOME DA OBRA NÃO CONFIGURADO')}
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

def ensure_first_admin_exists():
    """
    Verifica se existe algum usuário na tabela 'usuarios'.
    Se não houver, cria um usuário 'gestor' padrão.
    """
    conn = None
    try:
        print("DEBUG AUTH: ➡️ Iniciando ensure_first_admin_exists().", file=sys.stderr); sys.stderr.flush()
        conn, db_type = get_db_connection() # <-- AGORA OBTEMOS O TIPO DE DB REAL AQUI
        cursor = conn.cursor()
        
        print(f"DEBUG AUTH: Conectado ao DB. Tipo de DB: {db_type}. Executando COUNT(*) na tabela 'usuarios'.", file=sys.stderr); sys.stderr.flush()
        
        # Primeiro, verificamos se a tabela 'usuarios' existe para evitar um erro se ela não foi criada
        if db_type == 'postgresql':
            cursor.execute("SELECT to_regclass('public.usuarios')")
        else: # sqlite
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'")
        
        table_exists_result = cursor.fetchone()
        table_exists = table_exists_result[0] is not None if db_type == 'postgresql' else table_exists_result is not None
        
        if not table_exists:
            print("DEBUG AUTH: ⚠️ Tabela 'usuarios' NÃO EXISTE. init_db pode ter falhado ou não foi executado corretamente.", file=sys.stderr); sys.stderr.flush()
            st.error("Erro: A tabela de usuários não existe. Contate o administrador. (DEBUG: Tabela 'usuarios' ausente)")
            return # Sai da função se a tabela não existe
        
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        count_result = cursor.fetchone()
        count = count_result[0] if count_result else 0 # Garante 0 se não há resultado

        print(f"DEBUG AUTH: COUNT(*) de usuários retornou: {count}.", file=sys.stderr); sys.stderr.flush()

        if count == 0:
            print("DEBUG AUTH: Nenhum usuário encontrado. Iniciando criação do usuário administrador padrão.", file=sys.stderr); sys.stderr.flush()
            st.warning("Nenhum usuário encontrado. Criando usuário administrador padrão.")
            
            # Credenciais do admin: use variáveis de ambiente para produção, padrões para desenvolvimento
            default_admin_email = os.getenv("ADMIN_EMAIL", "admin@obra.com")
            default_admin_password = os.getenv("ADMIN_PASSWORD", "admin") # Mude isso para algo seguro em produção!
            hashed_default_password = hash_password(default_admin_password)

            param_placeholder_str = '%s' if db_type == 'postgresql' else '?' # <-- USADO O TIPO DE DB REAL

            insert_query = f"""
                INSERT INTO usuarios (nome, email, senha, tipo, ativo)
                VALUES ({param_placeholder_str}, {param_placeholder_str}, {param_placeholder_str}, {param_placeholder_str}, 1)
            """
            print(f"DEBUG AUTH: Executando INSERT do admin: Email='{default_admin_email}' Tipo='gestor'.", file=sys.stderr); sys.stderr.flush()
            cursor.execute(insert_query, ("Administrador", default_admin_email, hashed_default_password, "gestor"))
            conn.commit()
            print("DEBUG AUTH: ✅ INSERT e COMMIT do admin OK. Usuário criado.", file=sys.stderr); sys.stderr.flush()
            st.success(f"Usuário administrador criado: Email '{default_admin_email}', Senha '{default_admin_password}'. Por favor, faça login.")
            st.info("⚠️ Recomendamos alterar a senha após o primeiro login.")
        else:
            print(f"DEBUG AUTH: Usuários já existem ({count}). Nenhuma ação de criação de admin necessária.", file=sys.stderr); sys.stderr.flush()
            
    except Exception as e:
        error_message = f"Erro ao verificar/criar usuário administrador inicial: {e}"
        print(f"DEBUG AUTH: ❌ ERRO CRÍTICO em ensure_first_admin_exists()!", file=sys.stderr)
        print(f"DEBUG AUTH: Mensagem do erro: {error_message}", file=sys.stderr)
        print(f"DEBUG AUTH: Tipo do erro: {type(e)}", file=sys.stderr)
        print(f"DEBUG AUTH: Representação completa do erro: {repr(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr) # Imprimir o traceback COMPLETO
        sys.stderr.flush() # Forçar o flush dos logs imediatamente
        st.error(error_message) # Mostrar o erro detalhado na UI
    finally:
        if conn:
            print("DEBUG AUTH: Fechando conexão com o DB.", file=sys.stderr); sys.stderr.flush()
            conn.close()

if __name__ == "__main__":
    st.set_page_config(layout="centered")
    show_login_page()