import sys
import streamlit as st
from config.database import get_connection, init_db

def authenticate_user(email, senha):
    """Autentica usuário no sistema"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        query = """
            SELECT id, nome, email
            FROM usuarios 
            WHERE email = %s AND senha = %s AND ativo = TRUE
        """ if is_postgres else """
            SELECT id, nome, email
            FROM usuarios 
            WHERE email = ? AND senha = ? AND ativo = 1
        """
        
        cursor.execute(query, (email, senha))
        user = cursor.fetchone()
        
        if user:
            return {
                'id': user['id'],
                'nome': user['nome'],
                'email': user['email']
            }
        
        return None
        
    except Exception as e:
        print(f"Erro na autenticação: {repr(e)}", file=sys.stderr)
        return None
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def create_first_user():
    """Cria primeiro usuário e dados iniciais do sistema"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        # Verifica se já existe usuário
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        user_count = cursor.fetchone()[0]
        
        if user_count > 0:
            st.info("Sistema já possui usuários cadastrados.")
            return False
        
        # Cria usuário padrão
        if is_postgres:
            cursor.execute("""
                INSERT INTO usuarios (nome, email, senha, ativo)
                VALUES (%s, %s, %s, %s)
            """, ("Deverson", "deverson@obra.com", "123456", True))
        else:
            cursor.execute("""
                INSERT INTO usuarios (nome, email, senha, ativo)
                VALUES (?, ?, ?, ?)
            """, ("Deverson", "deverson@obra.com", "123456", 1))
        
        # Cria categorias padrão
        categorias_padrao = [
            ("Material de Construção", "Materiais básicos como cimento, areia, brita", "#e74c3c"),
            ("Mão de Obra", "Pagamentos de funcionários e prestadores", "#3498db"),
            ("Ferramentas e Equipamentos", "Compra e aluguel de ferramentas", "#f39c12"),
            ("Elétrica", "Material e serviços elétricos", "#9b59b6"),
            ("Hidráulica", "Material e serviços hidráulicos", "#1abc9c"),
            ("Acabamento", "Materiais de acabamento e pintura", "#34495e"),
            ("Documentação", "Taxas, licenças e documentos", "#95a5a6"),
            ("Transporte", "Fretes e transportes diversos", "#e67e22"),
            ("Alimentação", "Alimentação da equipe", "#27ae60"),
            ("Outros", "Gastos diversos não categorizados", "#7f8c8d")
        ]
        
        for nome, descricao, cor in categorias_padrao:
            if is_postgres:
                cursor.execute("""
                    INSERT INTO categorias (nome, descricao, cor, ativo)
                    VALUES (%s, %s, %s, %s)
                """, (nome, descricao, cor, True))
            else:
                cursor.execute("""
                    INSERT INTO categorias (nome, descricao, cor, ativo)
                    VALUES (?, ?, ?, ?)
                """, (nome, descricao, cor, 1))
        
        # Cria obra padrão
        from datetime import date, timedelta
        
        data_inicio = date.today()
        data_fim = data_inicio + timedelta(days=365)  # 1 ano de duração
        
        if is_postgres:
            cursor.execute("""
                INSERT INTO obras (nome, orcamento, data_inicio, data_fim_prevista, ativo)
                VALUES (%s, %s, %s, %s, %s)
            """, ("Minha Obra", 100000.00, data_inicio, data_fim, True))
        else:
            cursor.execute("""
                INSERT INTO obras (nome, orcamento, data_inicio, data_fim_prevista, ativo)
                VALUES (?, ?, ?, ?, ?)
            """, ("Minha Obra", 100000.00, data_inicio, data_fim, 1))
        
        conn.commit()
        
        st.success("✅ Sistema inicializado com sucesso!")
        st.info("""
        **Dados criados:**
        - Usuário: deverson@obra.com / 123456
        - 10 categorias padrão
        - Obra inicial com orçamento de R\$ 100.000,00
        
        **Agora você pode fazer login!**
        """)
        
        return True
        
    except Exception as e:
        print(f"Erro ao criar primeiro usuário: {repr(e)}", file=sys.stderr)
        conn.rollback()
        st.error(f"Erro ao inicializar sistema: {str(e)}")
        return False
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def show_login_page():
    """Exibe página de login"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1>🏗️ Sistema de Gestão Financeira</h1>
        <h3>Controle Financeiro para Obras</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Container centralizado para login
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.container():
            st.markdown("""
            <div class="card-container">
            """, unsafe_allow_html=True)
            
            st.subheader("🔐 Login")
            
            with st.form("login_form"):
                email = st.text_input("📧 Email", placeholder="seu@email.com")
                senha = st.text_input("🔒 Senha", type="password", placeholder="Sua senha")
                
                col_login, col_init = st.columns(2)
                
                with col_login:
                    login_button = st.form_submit_button("🚀 Entrar", use_container_width=True)
                
                with col_init:
                    init_button = st.form_submit_button("🔧 Inicializar Sistema", use_container_width=True)
            
            # Botão de login rápido para desenvolvimento
            if st.button("⚡ Login Rápido (Dev)", use_container_width=True):
                user = authenticate_user("deverson@obra.com", "123456")
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Usuário padrão não encontrado. Inicialize o sistema primeiro.")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Processa login
            if login_button:
                if not email or not senha:
                    st.error("⚠️ Por favor, preencha email e senha.")
                else:
                    user = authenticate_user(email, senha)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.success(f"✅ Bem-vindo, {user['nome']}!")
                        st.rerun()
                    else:
                        st.error("❌ Email ou senha incorretos.")
            
            # Processa inicialização
            if init_button:
                with st.spinner("Inicializando banco de dados..."):
                    try:
                        # Primeiro inicializa as tabelas
                        init_db()
                        st.success("✅ Tabelas criadas com sucesso!")
                        
                        # Depois cria os dados iniciais
                        if create_first_user():
                            st.balloons()
                        
                    except Exception as e:
                        st.error(f"❌ Erro na inicialização: {str(e)}")
                        print(f"Erro na inicialização: {repr(e)}", file=sys.stderr)
    
    # Informações do sistema
    st.markdown("---")
    
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.markdown("""
        ### 📋 Funcionalidades
        - 📊 Dashboard com métricas
        - 💰 Controle de lançamentos
        - �� Upload de comprovantes
        - 📈 Relatórios detalhados
        - ⚙️ Configurações flexíveis
        """)
    
    with col_info2:
        st.markdown("""
        ### 🔧 Primeiro Acesso
        1. Clique em "Inicializar Sistema"
        2. Aguarde a criação das tabelas
        3. Use: deverson@obra.com / 123456
        4. Configure sua obra nas Configurações
        """)

def logout():
    """Realiza logout do usuário"""
    if 'authenticated' in st.session_state:
        del st.session_state.authenticated
    if 'user' in st.session_state:
        del st.session_state.user
    st.rerun()

def check_authentication():
    """Verifica se usuário está autenticado"""
    return st.session_state.get('authenticated', False)

def get_current_user():
    """Retorna dados do usuário atual"""
    return st.session_state.get('user', None)

def show_user_header():
    """Exibe cabeçalho com informações do usuário"""
    user = get_current_user()
    if user:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### 👋 Olá, **{user['nome']}**!")
        
        with col2:
            if st.button("🚪 Sair", use_container_width=True):
                logout()

def require_auth(func):
    """Decorator para páginas que requerem autenticação"""
    def wrapper(*args, **kwargs):
        if not check_authentication():
            show_login_page()
            return
        return func(*args, **kwargs)
    return wrapper