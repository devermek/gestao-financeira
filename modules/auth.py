import streamlit as st
import pandas as pd
import hashlib
from config.database import get_db_connection, init_db

def get_all_active_users():
    """Retorna todos os usuários ativos"""
    try:
        conn = get_db_connection()
        users = pd.read_sql_query("""
            SELECT id, nome, email, tipo FROM usuarios 
            WHERE ativo = 1 
            ORDER BY nome
        """, conn)
        conn.close()
        return users
    except Exception as e:
        print(f"Erro ao buscar usuários: {e}")
        return pd.DataFrame()  # Retorna DataFrame vazio se der erro

def authenticate_user(email, senha):
    """Autentica usuário"""
    try:
        conn = get_db_connection()
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        
        user = pd.read_sql_query("""
            SELECT id, nome, email, tipo FROM usuarios 
            WHERE email = ? AND senha = ? AND ativo = 1
        """, conn, params=[email, senha_hash])
        
        conn.close()
        
        if not user.empty:
            return user.iloc[0].to_dict()
        return None
    except Exception as e:
        print(f"Erro na autenticação: {e}")
        return None

def show_user_header():
    """Exibe cabeçalho com informações do usuário logado"""
    if 'user' in st.session_state and st.session_state.user:
        user = st.session_state.user
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.write(f"👋 Olá, **{user['nome']}** ({user['tipo'].title()})")
        
        with col2:
            st.write(f"📧 {user['email']}")
        
        with col3:
            if st.button("🚪 Sair"):
                logout()

def show_login_page():
    """Exibe página de login"""
    st.title("🏗️ Sistema de Gestão de Obras")
    st.subheader("Controle Financeiro Profissional")
    
    # Verificar se as tabelas existem
    users = get_all_active_users()
    
    if users.empty:
        st.warning("⚠️ Banco de dados não inicializado!")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🔧 Inicializar Banco de Dados", type="primary"):
                with st.spinner("Inicializando banco de dados..."):
                    try:
                        init_db()
                        create_first_user()
                        st.success("✅ Banco de dados inicializado com sucesso!")
                        st.info("🔄 Recarregue a página para continuar")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao inicializar: {e}")
        
        with col2:
            st.info("👆 Clique no botão para criar as tabelas do banco de dados")
        
        return
    
    # Se chegou aqui, o banco está OK
    _show_quick_login()

def _show_quick_login():
    """Exibe login rápido"""
    st.success("🚀 Login rápido")
    
    users = get_all_active_users()
    
    if users.empty:
        st.warning("Nenhum usuário encontrado. Cadastre o primeiro usuário.")
        if st.button("👤 Criar Primeiro Usuário"):
            create_first_user()
            st.success("✅ Usuário criado! Recarregue a página.")
            st.rerun()
        return
    
    # Criar opções para selectbox
    user_options = {}
    for _, user in users.iterrows():
        label = f"{user['nome']} ({user['tipo'].title()})"
        user_options[label] = user
    
    selected_label = st.selectbox(
        "Selecione seu usuário:",
        options=list(user_options.keys()),
        key="quick_login_user"
    )
    
    if selected_label and st.button("🚀 Entrar", type="primary"):
        user = user_options[selected_label]
        st.session_state.user = user
        st.session_state.authenticated = True
        st.rerun()

def create_first_user():
    """Cria o primeiro usuário do sistema"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se já existe usuário
        try:
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            count = cursor.fetchone()[0]
        except:
            # Se der erro, provavelmente a tabela não existe
            count = 0
        
        if count == 0:
            # Criar usuário padrão
            senha_hash = hashlib.sha256("123456".encode()).hexdigest()
            cursor.execute("""
                INSERT INTO usuarios (nome, email, senha, tipo) 
                VALUES (?, ?, ?, ?)
            """, ("Deverson", "deverson@obra.com", senha_hash, "gestor"))
            
            conn.commit()
            print("✅ Usuário padrão criado: deverson@obra.com / 123456")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erro ao criar usuário padrão: {e}")

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