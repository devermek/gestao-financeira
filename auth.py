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
        
        # O tipo de DB já é detectado em get_db_connection, e o cursor já é RealDictCursor para PG ou sqlite3.Row para SQLite
        # Então podemos simplificar a lógica de placeholder e acesso a dados.

        hashed_password = hash_password(password)

        # Usando placeholders '%s' para psycopg2 (PostgreSQL) e '?' para sqlite3 (SQLite)
        # Assumindo que get_db_connection já retorna o tipo de conexão ou configura o cursor
        # para ser compatível (RealDictRow para PG).
        # Vamos assumir que se conectou, usaremos o placeholder correto.
        # A forma mais segura é passar o param_placeholder explicitamente, mas se o cursor já for adaptado,
        # o psycopg2 vai esperar %s.
        
        # Simplificação: Usaremos '%s' aqui e vamos corrigir a chamada se for SQLite.
        # O ideal é que get_db_connection informe o tipo de DB ou normalize a execução.
        # POR ENQUANTO, vamos testar com '%s' assumindo PostgreSQL.
        # Se você estiver usando SQLite, precisaríamos adaptar essa linha.
        # No seu `database.txt`, `get_db_connection` já retorna um `cursor_factory=RealDictCursor` para PG
        # e `conn.row_factory = sqlite3.Row` para SQLite, então o acesso é um pouco diferente.

        query = """
            SELECT id, nome, email, tipo, ativo FROM usuarios
            WHERE email = %s AND senha = %s AND ativo = 1
        """
        
        cursor.execute(query, (email, hashed_password))
        user_data = cursor.fetchone()
        
        if user_data:
            # Converte a tupla ou RealDictRow para um dicionário padrão
            # Se for RealDictRow (PostgreSQL), user_data já se comporta como um dicionário
            if isinstance(user_data, dict): 
                print(f"DEBUG AUTH LOGIN: Sucesso (dict) para {email}", file=sys.stderr)
                return user_data
            else: # sqlite3.Row ou tupla de SQLite
                print(f"DEBUG AUTH LOGIN: Sucesso (tupla/Row) para {email}", file=sys.stderr)
                # O cursor.fetchone() para sqlite3.Row permite acesso por chave e índice
                # E o seu código original já tentava acessar por chave. Vamos usar o original, mas mais robusto.
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
    # A função ensure_first_admin_exists deve retornar True/False para sucesso
    # E vamos capturar se falhou para exibir uma mensagem específica.
    admin_setup_success = ensure_first_admin_exists()
    if not admin_setup_success:
        st.error("⚠️ Não foi possível verificar ou criar o usuário administrador inicial. Por favor, verifique os logs do servidor.")


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
                ��️ {obra_config.get('nome_obra', 'Nome da Obra')}
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
        st.rerun() # Reinicia a aplicação, que vai parar na tela de login

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
        count = cursor.fetchone()[0] # Isso pode falhar se fetchone() for None ou não tiver índice 0
        print(f"DEBUG AUTH ensure_first_admin_exists: Total de usuários: {count}", file=sys.stderr)

        if count == 0:
            st.warning("Nenhum usuário encontrado. Criando usuário administrador padrão.", icon="⚠️")
            default_email = "admin@obra.com"
            default_password = "admin" 
            hashed_default_password = hash_password(default_password)

            # Inserir o usuário gestor padrão
            # Para PostgreSQL (psycopg2), os placeholders são %s. Para SQLite, são ?.
            # Assumimos que o banco é PostgreSQL, dada a configuração no Render.
            insert_query = """
                INSERT INTO usuarios (nome, email, senha, tipo, ativo)
                VALUES (%s, %s, %s, %s, 1)
            """
            print(f"DEBUG AUTH ensure_first_admin_exists: Executando INSERT para {default_email}", file=sys.stderr)
            cursor.execute(insert_query, ("Administrador", default_email, hashed_default_password, "gestor"))
            conn.commit()
            print("DEBUG AUTH ensure_first_admin_exists: COMMIT realizado.", file=sys.stderr)
            st.success(f"Usuário administrador criado: Email '{default_email}', Senha '{default_password}'. Por favor, faça login.", icon="✅")
            st.info("⚠️ Recomendamos alterar a senha após o primeiro login.", icon="ℹ️")
        else:
            print(f"DEBUG AUTH ensure_first_admin_exists: Já existem {count} usuários. Nenhuma ação necessária.", file=sys.stderr)
            
    except Exception as e:
        # st.error(f"Erro ao verificar/criar usuário administrador inicial: {e}") # Comentado para evitar spam
        print(f"DEBUG AUTH ensure_first_admin_exists ERROR: {e}", file=sys.stderr)
        print("DEBUG AUTH ensure_first_admin_exists ERROR: Traceback completo abaixo:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr) # Imprime o traceback completo no sys.stderr
        print("DEBUG AUTH ensure_first_admin_exists ERROR: --- FIM DO TRACEBACK ---", file=sys.stderr)
        return False
    finally:
        if conn:
            conn.close()
            print("DEBUG AUTH ensure_first_admin_exists: Conexão fechada.", file=sys.stderr)
    print("DEBUG AUTH ensure_first_admin_exists: --- FINALIZANDO ---", file=sys.stderr)
    return True

# O bloco if __name__ == "__main__": não será executado no Render,
# mas é mantido para testar localmente se necessário.
if __name__ == "__main__":
    st.set_page_config(layout="centered")
    show_login_page()