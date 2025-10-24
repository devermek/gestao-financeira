import sys
import streamlit as st
from datetime import datetime, date, timedelta
from config.database import get_connection, init_db

def authenticate_user(email, senha):
    """Autentica usuário no sistema"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        if is_postgres:
            query = """
                SELECT id, nome, email, created_at
                FROM usuarios 
                WHERE email = %s AND senha = %s AND ativo = TRUE
            """
        else:
            query = """
                SELECT id, nome, email, created_at
                FROM usuarios 
                WHERE email = ? AND senha = ? AND ativo = 1
            """
        
        cursor.execute(query, (email, senha))
        user = cursor.fetchone()
        
        if user:
            # Log do login
            print(f"Login realizado: {user['email']} (ID: {user['id']})", file=sys.stderr)
            
            return {
                'id': user['id'],
                'nome': user['nome'],
                'email': user['email'],
                'created_at': user['created_at']
            }
        
        print(f"Tentativa de login falhada para: {email}", file=sys.stderr)
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

def create_user(nome, email, senha):
    """Cria novo usuário"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        # Verifica se email já existe
        check_query = "SELECT id FROM usuarios WHERE email = %s" if is_postgres else "SELECT id FROM usuarios WHERE email = ?"
        cursor.execute(check_query, (email,))
        
        if cursor.fetchone():
            return False, "Email já cadastrado no sistema"
        
        # Cria usuário
        if is_postgres:
            query = """
                INSERT INTO usuarios (nome, email, senha, ativo)
                VALUES (%s, %s, %s, TRUE)
                RETURNING id
            """
        else:
            query = """
                INSERT INTO usuarios (nome, email, senha, ativo)
                VALUES (?, ?, ?, 1)
            """
        
        cursor.execute(query, (nome, email, senha))
        
        if is_postgres:
            user_id = cursor.fetchone()[0]
        else:
            user_id = cursor.lastrowid
        
        conn.commit()
        
        print(f"Usuário criado: {email} (ID: {user_id})", file=sys.stderr)
        return True, f"Usuário criado com sucesso! ID: {user_id}"
        
    except Exception as e:
        print(f"Erro ao criar usuário: {repr(e)}", file=sys.stderr)
        conn.rollback()
        return False, f"Erro ao criar usuário: {str(e)}"
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
        cursor.execute("SELECT COUNT(*) as count FROM usuarios")
        result = cursor.fetchone()
        user_count = result['count'] if result else 0
        
        if user_count > 0:
            st.info("Sistema já possui usuários cadastrados.")
            return False
        
        print("Criando dados iniciais do sistema...", file=sys.stderr)
        
        # Cria usuário padrão
        if is_postgres:
            cursor.execute("""
                INSERT INTO usuarios (nome, email, senha, ativo)
                VALUES (%s, %s, %s, TRUE)
            """, ("Deverson", "deverson@obra.com", "123456"))
        else:
            cursor.execute("""
                INSERT INTO usuarios (nome, email, senha, ativo)
                VALUES (?, ?, ?, 1)
            """, ("Deverson", "deverson@obra.com", "123456"))
        
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
                    VALUES (%s, %s, %s, TRUE)
                """, (nome, descricao, cor))
            else:
                cursor.execute("""
                    INSERT INTO categorias (nome, descricao, cor, ativo)
                    VALUES (?, ?, ?, 1)
                """, (nome, descricao, cor))
        
        # Cria obra padrão
        data_inicio = date.today()
        data_fim = data_inicio + timedelta(days=365)  # 1 ano de duração
        
        if is_postgres:
            cursor.execute("""
                INSERT INTO obras (nome, orcamento, data_inicio, data_fim_prevista, ativo)
                VALUES (%s, %s, %s, %s, TRUE)
            """, ("Minha Obra", 100000.00, data_inicio, data_fim))
        else:
            cursor.execute("""
                INSERT INTO obras (nome, orcamento, data_inicio, data_fim_prevista, ativo)
                VALUES (?, ?, ?, ?, 1)
            """, ("Minha Obra", 100000.00, data_inicio, data_fim))
        
        conn.commit()
        
        print("Dados iniciais criados com sucesso!", file=sys.stderr)
        
        st.success("✅ Sistema inicializado com sucesso!")
        st.info("""
        **Dados criados:**
        - 👤 Usuário: deverson@obra.com / 123456
        - ��️ 10 categorias padrão
        - ��️ Obra inicial com orçamento de R\$ 100.000,00
        
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

def update_user_password(user_id, nova_senha):
    """Atualiza senha do usuário"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        if is_postgres:
            query = """
                UPDATE usuarios 
                SET senha = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
        else:
            query = """
                UPDATE usuarios 
                SET senha = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
        
        cursor.execute(query, (nova_senha, user_id))
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"Senha atualizada para usuário ID: {user_id}", file=sys.stderr)
            return True
        else:
            print(f"Usuário não encontrado: {user_id}", file=sys.stderr)
            return False
        
    except Exception as e:
        print(f"Erro ao atualizar senha: {repr(e)}", file=sys.stderr)
        conn.rollback()
        return False
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def get_user_by_id(user_id):
    """Busca usuário por ID"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        query = """
            SELECT id, nome, email, ativo, created_at, updated_at
            FROM usuarios
            WHERE id = %s
        """ if is_postgres else """
            SELECT id, nome, email, ativo, created_at, updated_at
            FROM usuarios
            WHERE id = ?
        """
        
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
        
        if user:
            return {
                'id': user['id'],
                'nome': user['nome'],
                'email': user['email'],
                'ativo': bool(user['ativo']),
                'created_at': user['created_at'],
                'updated_at': user['updated_at']
            }
        
        return None
        
    except Exception as e:
        print(f"Erro ao buscar usuário: {repr(e)}", file=sys.stderr)
        return None
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
        <p style="color: #888; margin-top: 1rem;">
            Gerencie todos os gastos da sua obra de forma organizada e eficiente
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Container centralizado para login
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.container():
            st.markdown("""
            <div class="card-container">
            """, unsafe_allow_html=True)
            
            st.subheader("🔐 Acesso ao Sistema")
            
            # Tabs para Login e Cadastro
            tab1, tab2 = st.tabs(["🚪 Login", "👤 Cadastro"])
            
            with tab1:
                _show_login_form()
            
            with tab2:
                _show_register_form()
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Informações do sistema
    st.markdown("---")
    
    col_info1, col_info2, col_info3 = st.columns(3)
    
    with col_info1:
        st.markdown("""
        ### 📋 Funcionalidades
        - 📊 Dashboard com métricas
        - 💰 Controle de lançamentos
        - 📎 Upload de comprovantes
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
    
    with col_info3:
        st.markdown("""
        ### 🛡️ Segurança
        - ✅ Dados protegidos
        - ✅ Backup automático
        - ✅ Acesso controlado
        - ✅ Logs de auditoria
        """)

def _show_login_form():
    """Formulário de login"""
    with st.form("login_form"):
        email = st.text_input("📧 Email", placeholder="seu@email.com")
        senha = st.text_input("🔒 Senha", type="password", placeholder="Sua senha")
        
        col_login, col_init = st.columns(2)
        
        with col_login:
            login_button = st.form_submit_button("🚀 Entrar", use_container_width=True)
        
        with col_init:
            init_button = st.form_submit_button("🔧 Inicializar Sistema", use_container_width=True)
    
    # Botão de login rápido para desenvolvimento
    if st.button("⚡ Login Rápido (Dev)", use_container_width=True, help="Login automático para desenvolvimento"):
        user = authenticate_user("deverson@obra.com", "123456")
        if user:
            st.session_state.authenticated = True
            st.session_state.user = user
            st.success("Login realizado com sucesso!")
            st.rerun()
        else:
            st.error("Usuário padrão não encontrado. Inicialize o sistema primeiro.")
    
    # Processa login
    if login_button:
        if not email or not senha:
            st.error("⚠️ Por favor, preencha email e senha.")
        else:
            with st.spinner("Autenticando..."):
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

def _show_register_form():
    """Formulário de cadastro"""
    st.info("💡 Cadastro de novos usuários disponível após login do administrador")
    
    with st.form("register_form"):
        nome = st.text_input("👤 Nome Completo", placeholder="Seu nome completo")
        email = st.text_input("📧 Email", placeholder="seu@email.com")
        senha = st.text_input("🔒 Senha", type="password", placeholder="Mínimo 6 caracteres")
        confirma_senha = st.text_input("🔒 Confirmar Senha", type="password", placeholder="Repita a senha")
        
        register_button = st.form_submit_button("👤 Criar Conta", use_container_width=True)
    
    if register_button:
        # Validações
        if not all([nome, email, senha, confirma_senha]):
            st.error("⚠️ Todos os campos são obrigatórios.")
        elif len(senha) < 6:
            st.error("⚠️ A senha deve ter pelo menos 6 caracteres.")
        elif senha != confirma_senha:
            st.error("⚠️ As senhas não coincidem.")
        elif "@" not in email or "." not in email:
            st.error("⚠️ Email inválido.")
        else:
            with st.spinner("Criando conta..."):
                success, message = create_user(nome, email, senha)
                if success:
                    st.success(f"✅ {message}")
                    st.info("Agora você pode fazer login!")
                else:
                    st.error(f"❌ {message}")

def logout():
    """Realiza logout do usuário"""
    user = st.session_state.get('user')
    if user:
        print(f"Logout realizado: {user['email']}", file=sys.stderr)
    
    # Limpa dados da sessão
    keys_to_clear = ['authenticated', 'user', 'current_page']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
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
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"### �� Olá, **{user['nome']}**!")
            st.caption(f"📧 {user['email']}")
        
        with col2:
            # Botão de configurações do usuário
            if st.button("⚙️ Perfil", use_container_width=True):
                st.session_state['show_user_config'] = True
        
        with col3:
            if st.button("🚪 Sair", use_container_width=True):
                logout()
        
        # Modal de configurações do usuário
        if st.session_state.get('show_user_config', False):
            _show_user_config_modal()

def _show_user_config_modal():
    """Modal para configurações do usuário"""
    with st.expander("👤 Configurações do Usuário", expanded=True):
        user = get_current_user()
        
        st.subheader("🔒 Alterar Senha")
        
        with st.form("change_password_form"):
            nova_senha = st.text_input("Nova Senha", type="password", placeholder="Mínimo 6 caracteres")
            confirma_nova_senha = st.text_input("Confirmar Nova Senha", type="password")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.form_submit_button("💾 Alterar Senha", use_container_width=True):
                    if not nova_senha or not confirma_nova_senha:
                        st.error("⚠️ Preencha todos os campos.")
                    elif len(nova_senha) < 6:
                        st.error("⚠️ A senha deve ter pelo menos 6 caracteres.")
                    elif nova_senha != confirma_nova_senha:
                        st.error("⚠️ As senhas não coincidem.")
                    else:
                        if update_user_password(user['id'], nova_senha):
                            st.success("✅ Senha alterada com sucesso!")
                            st.session_state['show_user_config'] = False
                            st.rerun()
                        else:
                            st.error("❌ Erro ao alterar senha.")
            
            with col2:
                if st.form_submit_button("❌ Cancelar", use_container_width=True):
                    st.session_state['show_user_config'] = False
                    st.rerun()

def require_auth(func):
    """Decorator para páginas que requerem autenticação"""
    def wrapper(*args, **kwargs):
        if not check_authentication():
            show_login_page()
            return
        return func(*args, **kwargs)
    return wrapper

def get_user_stats():
    """Retorna estatísticas do usuário atual"""
    try:
        user = get_current_user()
        if not user:
            return None
        
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        # Estatísticas básicas
        stats = {
            'total_lancamentos': 0,
            'valor_total': 0.0,
            'ultimo_acesso': user.get('created_at'),
            'dias_no_sistema': 0
        }
        
        # Total de lançamentos do usuário (assumindo que há relação com obras)
        query = """
            SELECT COUNT(*) as total, COALESCE(SUM(valor), 0) as soma
            FROM lancamentos l
            JOIN obras o ON l.obra_id = o.id
            WHERE o.ativo = %s
        """ if is_postgres else """
            SELECT COUNT(*) as total, COALESCE(SUM(valor), 0) as soma
            FROM lancamentos l
            JOIN obras o ON l.obra_id = o.id
            WHERE o.ativo = ?
        """
        
        cursor.execute(query, (True if is_postgres else 1,))
        result = cursor.fetchone()
        
        if result:
            stats['total_lancamentos'] = result['total']
            
            # Converte valor
            try:
                if result['soma'] is not None:
                    from decimal import Decimal
                    if isinstance(result['soma'], Decimal):
                        stats['valor_total'] = float(result['soma'])
                    else:
                        stats['valor_total'] = float(result['soma'])
            except (TypeError, ValueError):
                stats['valor_total'] = 0.0
        
        # Calcula dias no sistema
        if user.get('created_at'):
            try:
                if isinstance(user['created_at'], str):
                    created_date = datetime.strptime(user['created_at'][:10], '%Y-%m-%d').date()
                else:
                    created_date = user['created_at'].date() if hasattr(user['created_at'], 'date') else user['created_at']
                
                stats['dias_no_sistema'] = (date.today() - created_date).days
            except:
                stats['dias_no_sistema'] = 0
        
        cursor.close()
        conn.close()
        
        return stats
        
    except Exception as e:
        print(f"Erro ao obter estatísticas do usuário: {repr(e)}", file=sys.stderr)
        return None

# Função para verificar se é primeiro acesso
def is_first_access():
    """Verifica se é o primeiro acesso ao sistema"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM usuarios")
        result = cursor.fetchone()
        user_count = result['count'] if result else 0
        
        cursor.close()
        conn.close()
        
        return user_count == 0
        
    except Exception as e:
        print(f"Erro ao verificar primeiro acesso: {repr(e)}", file=sys.stderr)
        return True  # Assume primeiro acesso em caso de erro