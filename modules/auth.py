import streamlit as st
import pandas as pd
import hashlib
from config.database import get_db_connection, init_db # Import init_db
import sys # For sys.stderr

def get_all_active_users():
    """Retorna todos os usuários ativos"""
    try:
        conn, db_type = get_db_connection() # Get db_type
        users = pd.read_sql_query("""
            SELECT id, nome, email, tipo FROM usuarios 
            WHERE ativo = 1 
            ORDER BY nome
        """, conn)
        conn.close()
        return users
    except Exception as e:
        print(f"Erro ao buscar usuários (get_all_active_users): {e}", file=sys.stderr); sys.stderr.flush()
        return pd.DataFrame()

def authenticate_user(email, senha):
    """Autentica usuário"""
    try:
        conn, db_type = get_db_connection() # Get db_type
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        
        query = """
            SELECT id, nome, email, tipo FROM usuarios 
            WHERE email = ? AND senha = ? AND ativo = 1
        """
        params = [email, senha_hash]

        if db_type == 'postgresql':
            query = query.replace('?', '%s')
            user = pd.read_sql_query(query, conn, params=tuple(params))
        else: # sqlite
            user = pd.read_sql_query(query, conn, params=params)
        
        conn.close()
        
        if not user.empty:
            return user.iloc[0].to_dict()
        return None
    except Exception as e:
        print(f"Erro na autenticação: {e}", file=sys.stderr); sys.stderr.flush()
        return None

def show_user_header():
    """Exibe cabeçalho com informações do usuário logado"""
    if 'user' in st.session_state and st.session_state.user is not None:
        user = st.session_state.user
        
        if hasattr(user, 'to_dict'):
            user = user.to_dict()
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.write(f"👋 Olá, **{user['nome']}** ({user['tipo'].title()})")
        
        with col2:
            st.write(f"📧 {user['email']}")
        
        with col3:
            if st.button("�� Sair", key="logout_button"): # Add a key to avoid duplicate widget error
                logout()

def show_login_page():
    """Exibe página de login"""
    st.title("🏗️ Sistema de Gestão de Obras")
    st.subheader("Controle Financeiro Profissional")
    
    # Verificar se as tabelas existem e se há usuários
    users = get_all_active_users()
    
    if users.empty:
        st.warning("⚠️ Banco de dados não inicializado ou sem usuários!")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔧 Inicializar Banco de Dados e Criar Primeiro Usuário", type="primary"):
                with st.spinner("Inicializando banco de dados..."):
                    try:
                        init_db() # Initializes tables
                        create_first_user() # Creates a default gestor user and categories/config
                        st.success("✅ Banco de dados inicializado e usuário padrão criado! Recarregue a página.")
                        st.info("Para continuar, atualize a página. Se o problema persistir, limpe o cache do navegador.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao inicializar: {e}")
                        print(f"Erro ao inicializar db na tela de login: {e}", file=sys.stderr); sys.stderr.flush()
        with col2:
            st.info("👆 Clique no botão para criar as tabelas do banco de dados e o primeiro usuário.")
        return

    # Se chegou aqui, o banco está OK e tem usuários
    st.markdown("---")
    st.markdown("### 🔒 Login")

    with st.form("login_form"):
        email = st.text_input("�� Email:")
        senha = st.text_input("🔑 Senha:", type="password")
        login_button = st.form_submit_button("Entrar", type="primary")

        if login_button:
            if email and senha:
                user = authenticate_user(email, senha)
                if user:
                    st.session_state.user = user
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Email ou senha incorretos.")
            else:
                st.warning("Por favor, preencha o email e a senha.")
    
    st.markdown("---")
    _show_quick_login(users) # Pass users to quick login

def _show_quick_login(users_df):
    """Exibe login rápido, recebendo users_df como argumento"""
    st.subheader("🚀 Login Rápido (Apenas para Gestores)") # Renomeado para maior clareza
    
    # Certifique-se que users_df não está vazio antes de tentar processá-lo
    if users_df.empty:
        st.warning("Nenhum usuário gestor encontrado para login rápido.")
        return

    # Filtrar apenas usuários do tipo 'gestor' para o login rápido
    gestor_users = users_df[users_df['tipo'] == 'gestor']
    
    if gestor_users.empty:
        st.warning("Nenhum usuário do tipo 'gestor' encontrado. Por favor, faça login com email/senha ou inicialize o banco de dados.")
        return

    user_options = ["Selecione um usuário..."]
    user_data_map = {0: None} # Map index to user object

    for idx, user_row in gestor_users.iterrows():
        label = f"{user_row['nome']} ({user_row['tipo'].title()})"
        user_options.append(label)
        user_data_map[len(user_options) - 1] = user_row.to_dict() # Store as dict

    selected_index = st.selectbox(
        "Selecione seu usuário (Gestor):",
        options=list(user_data_map.keys()),
        format_func=lambda x: user_options[x],
        key="quick_login_user"
    )
    
    if selected_index > 0 and st.button("🚀 Entrar como Gestor", type="secondary"): # Changed button type to secondary
        user = user_data_map[selected_index]
        
        st.session_state.user = user
        st.session_state.authenticated = True
        st.rerun()

def create_first_user():
    """Cria o primeiro usuário do sistema e dados iniciais"""
    try:
        conn, db_type = get_db_connection() # Get db_type
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            count = cursor.fetchone()[0]
        except Exception as e:
            print(f"Erro ao contar usuários: {e}", file=sys.stderr); sys.stderr.flush()
            count = 0
        
        if count == 0:
            senha_hash = hashlib.sha256("123456".encode()).hexdigest()
            query = """
                INSERT INTO usuarios (nome, email, senha, tipo) 
                VALUES (?, ?, ?, ?)
            """
            params = ("Deverson", "deverson@obra.com", senha_hash, "gestor")

            if db_type == 'postgresql':
                query = query.replace('?', '%s')
                cursor.execute(query, params)
            else:
                cursor.execute(query, params)
            
            print("✅ Usuário padrão criado: deverson@obra.com / 123456")
        
        try:
            cursor.execute("SELECT COUNT(*) FROM categorias")
            cat_count = cursor.fetchone()[0]
        except Exception as e:
            print(f"Erro ao contar categorias: {e}", file=sys.stderr); sys.stderr.flush()
            cat_count = 0
            
        if cat_count == 0:
            categorias_padrao = [
                ("Material de Construção", "Cimento, areia, brita, tijolos", 50000.00),
                ("Mão de Obra", "Pedreiros, serventes, eletricistas", 30000.00),
                ("Ferramentas", "Equipamentos e ferramentas", 5000.00),
                ("Transporte", "Frete e transporte de materiais", 3000.00),
                ("Diversos", "Gastos diversos da obra", 2000.00)
            ]
            
            for nome, desc, orcamento in categorias_padrao:
                query = """
                    INSERT INTO categorias (nome, descricao, orcamento_previsto) 
                    VALUES (?, ?, ?)
                """
                params = (nome, desc, orcamento)
                if db_type == 'postgresql':
                    query = query.replace('?', '%s')
                    cursor.execute(query, params)
                else:
                    cursor.execute(query, params)
            
            print("✅ Categorias padrão criadas!")
        
        try:
            cursor.execute("SELECT COUNT(*) FROM obra_config")
            obra_count = cursor.fetchone()[0]
        except Exception as e:
            print(f"Erro ao contar obra_config: {e}", file=sys.stderr); sys.stderr.flush()
            obra_count = 0
            
        if obra_count == 0:
            query = """
                INSERT INTO obra_config (nome_obra, orcamento_total, data_inicio) 
                VALUES (?, ?, DATE('now'))
            """
            params = ("Minha Obra", 90000.00)
            if db_type == 'postgresql':
                # DATE('now') for SQLite, CURRENT_DATE for PostgreSQL
                query = query.replace("DATE('now')", "CURRENT_DATE").replace('?', '%s')
                cursor.execute(query, params)
            else:
                cursor.execute(query, params)
            
            print("✅ Configuração da obra criada!")
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erro ao criar dados iniciais: {e}", file=sys.stderr); sys.stderr.flush()

def logout():
    """Faz logout do usuário"""
    for key in ['user', 'authenticated']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

def is_authenticated():
    """Verifica se o usuário está autenticado"""
    return 'authenticated' in st.session_state and st.session_state.authenticated

def get_current_user():
    """Retorna o usuário atual"""
    if 'user' in st.session_state:
        return st.session_state.user
    return None

def require_auth():
    """Decorator para páginas que requerem autenticação"""
    if not is_authenticated():
        st.error("🔒 Acesso negado. Faça login primeiro.")
        st.stop()

def check_user_type(required_type):
    """Verifica se o usuário tem o tipo necessário"""
    user = get_current_user()
    if not user or user['tipo'] != required_type:
        st.error(f"🚫 Acesso restrito para {required_type}s")
        st.stop()