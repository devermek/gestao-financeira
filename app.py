import streamlit as st
import sys
import os

# Configuração da página (deve ser a primeira chamada Streamlit)
st.set_page_config(
    page_title="Sistema de Gestão Financeira - Obras",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Adiciona o diretório raiz ao path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Imports dos módulos
from utils.styles import load_css
from modules.dashboard import show_dashboard
from modules.lancamentos import show_lancamentos
from modules.relatorios import show_relatorios
from modules.configuracoes import show_configuracoes
from config.database import init_db, test_connection

def main():
    """Função principal da aplicação"""
    
    # Carrega estilos CSS
    load_css()
    
    # Inicializa banco se necessário (apenas uma vez por sessão)
    if 'db_initialized' not in st.session_state:
        init_system_if_needed()
        st.session_state.db_initialized = True
    
    # Interface principal
    show_main_interface()

def init_system_if_needed():
    """Inicializa sistema automaticamente se necessário"""
    try:
        # Testa conexão
        if not test_connection():
            st.error("❌ Erro de conexão com banco de dados!")
            return
        
        # Verifica se precisa inicializar
        if is_first_run():
            with st.spinner("🔧 Inicializando sistema pela primeira vez..."):
                init_db()
                create_initial_data()
                st.success("✅ Sistema inicializado com sucesso!")
                # Remove o spinner e não faz rerun
                
    except Exception as e:
        st.error(f"❌ Erro na inicialização: {str(e)}")
        print(f"Erro na inicialização: {repr(e)}", file=sys.stderr)

def is_first_run():
    """Verifica se é a primeira execução"""
    try:
        from config.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verifica se existe tabela obras e se tem dados
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        if is_postgres:
            # Verifica se tabela existe
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'obras'
                )
            """)
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                cursor.close()
                conn.close()
                return True
            
            # Verifica se tem dados
            cursor.execute("SELECT COUNT(*) as count FROM obras")
            result = cursor.fetchone()
            count = result['count'] if result else 0
            
        else:
            # SQLite
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='obras'
            """)
            table_exists = cursor.fetchone()
            
            if not table_exists:
                cursor.close()
                conn.close()
                return True
            
            # Verifica se tem dados
            cursor.execute("SELECT COUNT(*) as count FROM obras")
            result = cursor.fetchone()
            count = result['count'] if result else 0
        
        cursor.close()
        conn.close()
        
        # Se não tem dados, é primeira execução
        return count == 0
            
    except Exception as e:
        print(f"Erro ao verificar primeira execução: {repr(e)}", file=sys.stderr)
        # Em caso de erro, assume que NÃO é primeira execução para evitar loop
        return False

def create_initial_data():
    """Cria dados iniciais do sistema"""
    try:
        from config.database import get_connection
        from datetime import date, timedelta
        
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        # Verifica se já existem dados para evitar duplicação
        cursor.execute("SELECT COUNT(*) as count FROM categorias")
        result = cursor.fetchone()
        categoria_count = result['count'] if result else 0
        
        if categoria_count > 0:
            print("Dados iniciais já existem, pulando criação...", file=sys.stderr)
            cursor.close()
            conn.close()
            return
        
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
        
        # Verifica se já existe obra
        cursor.execute("SELECT COUNT(*) as count FROM obras")
        result = cursor.fetchone()
        obra_count = result['count'] if result else 0
        
        if obra_count == 0:
            # Cria obra padrão
            data_inicio = date.today()
            data_fim = data_inicio + timedelta(days=365)
            
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
        cursor.close()
        conn.close()
        
        print("Dados iniciais criados com sucesso!", file=sys.stderr)
        
    except Exception as e:
        print(f"Erro ao criar dados iniciais: {repr(e)}", file=sys.stderr)
        if 'conn' in locals():
            conn.rollback()
            cursor.close()
            conn.close()

def show_main_interface():
    """Interface principal do sistema"""
    
    # Cabeçalho principal
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; background: linear-gradient(90deg, #1f77b4, #2ca02c); color: white; border-radius: 10px; margin-bottom: 2rem;">
        <h1 style="margin: 0;">🏗️ Sistema de Gestão Financeira</h1>
        <p style="margin: 0; opacity: 0.9;">Controle completo dos gastos da sua obra</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar com navegação
    with st.sidebar:
        # CSS específico para sidebar
        st.markdown("""
        <style>
        .sidebar-content {
            color: #333 !important;
        }
        .sidebar-content .stSelectbox label {
            color: #333 !important;
            font-weight: bold !important;
        }
        .sidebar-content .stSelectbox > div > div {
            background-color: white !important;
            color: #333 !important;
        }
        
        /* Mobile: força sidebar visível */
        @media (max-width: 768px) {
            .css-1d391kg {
                position: relative !important;
                width: 100% !important;
                min-width: 100% !important;
                transform: none !important;
            }
            
            .css-1d391kg .sidebar-content {
                padding: 1rem !important;
            }
            
            .stButton > button {
                font-size: 16px !important;
                padding: 12px 16px !important;
                margin: 4px 0 !important;
                width: 100% !important;
            }
        }
        </style>
        <div class="sidebar-content">
        """, unsafe_allow_html=True)
        
        # Header da sidebar
        st.markdown("### 🧭 Navegação")
        
        # Detecta se é mobile (aproximação)
        is_mobile = st.checkbox("📱 Modo Mobile", value=False, help="Ative para melhor experiência mobile")
        
        if is_mobile:
            # Navegação simplificada para mobile
            st.markdown("#### Acesso Rápido")
            
            if st.button("📊 Dashboard", use_container_width=True, key="nav_dashboard"):
                st.session_state.current_page = "📊 Dashboard"
                st.rerun()
            
            if st.button("💰 Lançamentos", use_container_width=True, key="nav_lancamentos"):
                st.session_state.current_page = "💰 Lançamentos"
                st.rerun()
            
            if st.button("📈 Relatórios", use_container_width=True, key="nav_relatorios"):
                st.session_state.current_page = "�� Relatórios"
                st.rerun()
            
            if st.button("⚙️ Configurações", use_container_width=True, key="nav_config"):
                st.session_state.current_page = "⚙️ Configurações"
                st.rerun()
        
        else:
            # Navegação normal para desktop
            page_options = [
                "📊 Dashboard",
                "💰 Lançamentos", 
                "📈 Relatórios",
                "⚙️ Configurações"
            ]
            
            # Usa session state para manter seleção
            if 'current_page' not in st.session_state:
                st.session_state.current_page = "📊 Dashboard"
            
            # Seletor de página
            selected_page = st.selectbox(
                "Selecione uma página:",
                options=page_options,
                index=page_options.index(st.session_state.current_page) if st.session_state.current_page in page_options else 0,
                key="page_selector"
            )
            
            # Atualiza session state
            st.session_state.current_page = selected_page
            
            st.markdown("---")
            
            # Botões de navegação alternativos
            st.markdown("### 📱 Navegação Rápida")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📊", help="Dashboard", use_container_width=True):
                    st.session_state.current_page = "📊 Dashboard"
                    st.rerun()
                if st.button("💰", help="Lançamentos", use_container_width=True):
                    st.session_state.current_page = "💰 Lançamentos"
                    st.rerun()
            
            with col2:
                if st.button("📈", help="Relatórios", use_container_width=True):
                    st.session_state.current_page = "📈 Relatórios"
                    st.rerun()
                if st.button("⚙️", help="Configurações", use_container_width=True):
                    st.session_state.current_page = "⚙️ Configurações"
                    st.rerun()
        
        st.markdown("---")
        
        # Informações do sistema
        st.markdown("### ℹ️ Sistema")
        st.markdown("""
        <div style="color: #333;">
        🏗️ <strong>Gestão Financeira de Obras</strong><br>
        📱 <strong>Versão:</strong> 1.0.0<br>
        👨‍💻 <strong>Desenvolvido por:</strong> Deverson
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Botão de reset/reinicialização
        if st.button("🔄 Reinicializar Sistema", use_container_width=True, help="Limpa cache e reinicia"):
            # Limpa session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        # Botão para forçar re-inicialização do banco
        if st.button("🗃️ Recriar Banco", use_container_width=True, help="Recria todas as tabelas"):
            try:
                with st.spinner("Recriando banco de dados..."):
                    init_db()
                    create_initial_data()
                    # Limpa flag de inicialização
                    if 'db_initialized' in st.session_state:
                        del st.session_state['db_initialized']
                    st.success("✅ Banco recriado com sucesso!")
            except Exception as e:
                st.error(f"❌ Erro ao recriar banco: {str(e)}")
        
        # Status do sistema
        st.markdown("### 🔧 Status do Sistema")
        
        # Verifica conexão com banco
        if test_connection():
            st.success("🟢 Banco conectado")
        else:
            st.error("🔴 Erro no banco")
        
        # Informações da obra atual
        try:
            from utils.helpers import get_obra_config
            obra = get_obra_config()
            if obra and obra.get('id'):
                st.info(f"🏗️ Obra: {obra['nome']}")
            else:
                st.warning("⚠️ Nenhuma obra configurada")
        except:
            st.error("❌ Erro ao carregar obra")
        
        st.markdown("---")
        
        # Links úteis
        st.markdown("### 🔗 Links Úteis")
        st.markdown("""
        <div style="color: #333;">
        📚 <a href="https://github.com"  style="color: #1f77b4;">Documentação</a><br>
        🐛 <a href="https://github.com"  style="color: #1f77b4;">Reportar Bug</a><br>
        💡 <a href="https://github.com"  style="color: #1f77b4;">Sugestões</a>
        </div>
        """, unsafe_allow_html=True)
        
        # Debug info (apenas em desenvolvimento)
        if os.getenv('DEBUG', 'False').lower() == 'true':
            st.markdown("---")
            st.markdown("### 🐛 Debug Info")
            st.json({
                "session_state_keys": list(st.session_state.keys()),
                "current_page": st.session_state.get('current_page', 'None'),
                "db_initialized": st.session_state.get('db_initialized', False),
                "database_url_exists": bool(os.getenv('DATABASE_URL'))
            })
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Container principal
    with st.container():
        # Roteamento de páginas
        current_page = st.session_state.get('current_page', "📊 Dashboard")
        
        # Adiciona CSS mobile global
        st.markdown("""
        <style>
        /* CSS Mobile Global */
        @media (max-width: 768px) {
            .main .block-container {
                padding: 1rem 0.5rem;
                max-width: 100%;
            }
            
            .stButton > button {
                font-size: 16px !important;
                padding: 12px 16px !important;
                margin: 4px 0 !important;
                width: 100% !important;
            }
            
            .stSelectbox > div > div {
                font-size: 16px !important;
            }
            
            .stTextInput > div > div > input {
                font-size: 16px !important;
                padding: 12px !important;
            }
            
            .stNumberInput > div > div > input {
                font-size: 16px !important;
                padding: 12px !important;
            }
            
            .stTextArea > div > div > textarea {
                font-size: 16px !important;
                padding: 12px !important;
            }
            
            /* Força sidebar sempre visível em mobile */
            .css-1d391kg {
                position: relative !important;
                width: 100% !important;
                min-width: 100% !important;
                transform: none !important;
                left: 0 !important;
            }
            
            /* Melhora métricas em mobile */
            [data-testid="metric-container"] {
                margin: 8px 0 !important;
                padding: 12px !important;
            }
            
            /* Melhora gráficos em mobile */
            .js-plotly-plot {
                width: 100% !important;
            }
            
            .plotly-graph-div {
                width: 100% !important;
            }
        }
        
        /* Melhora geral da interface */
        .stMetric {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 0.5rem 0;
        }
        
        .stAlert {
            border-radius: 8px;
            margin: 0.5rem 0;
        }
        
        /* Botão flutuante para mobile */
        .mobile-nav-btn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 999;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            font-size: 24px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Navegação de páginas
        try:
            if current_page == "📊 Dashboard":
                show_dashboard()
            elif current_page == "💰 Lançamentos":
                show_lancamentos()
            elif current_page == "�� Relatórios":
                show_relatorios()
            elif current_page == "⚙️ Configurações":
                show_configuracoes()
            else:
                # Página padrão
                st.session_state.current_page = "📊 Dashboard"
                show_dashboard()
                
        except Exception as e:
            st.error("🚨 Erro ao carregar página!")
            
            # Em desenvolvimento, mostra detalhes do erro
            if os.getenv('DEBUG', 'False').lower() == 'true':
                st.exception(e)
            else:
                st.info("Por favor, tente navegar para outra página ou recarregue o sistema.")
            
            # Log do erro
            print(f"Erro ao carregar página {current_page}: {repr(e)}", file=sys.stderr)
            
            # Botão para voltar ao dashboard
            if st.button("🏠 Voltar ao Dashboard"):
                st.session_state.current_page = "📊 Dashboard"
                st.rerun()
    
    # Footer
    show_footer()

def show_footer():
    """Exibe rodapé da aplicação"""
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🏗️ Sistema de Gestão Financeira")
        st.caption("Controle completo dos gastos da sua obra")
    
    with col2:
        st.markdown("### 📊 Funcionalidades")
        st.caption("✅ Dashboard interativo")
        st.caption("✅ Controle de lançamentos")
        st.caption("✅ Upload de comprovantes")
        st.caption("✅ Relatórios detalhados")
    
    with col3:
        st.markdown("### 🔧 Suporte")
        st.caption("📧 suporte@sistema.com")
        st.caption("📱 (11) 99999-9999")
        st.caption("🌐 www.sistema.com")
    
    # Copyright
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #888; font-size: 0.8em;'>"
        "© 2024 Sistema de Gestão Financeira para Obras. Todos os direitos reservados."
        "</div>",
        unsafe_allow_html=True
    )

def init_session_state():
    """Inicializa variáveis de sessão"""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "📊 Dashboard"
    
    # Remove estados problemáticos se existirem
    problematic_keys = ['show_user_config', 'authenticated', 'user']
    for key in list(st.session_state.keys()):
        if any(prob_key in key for prob_key in problematic_keys):
            del st.session_state[key]

def handle_errors():
    """Manipulador global de erros"""
    try:
        main()
    except Exception as e:
        st.error("🚨 Ocorreu um erro inesperado no sistema!")
        
        # Em desenvolvimento, mostra detalhes do erro
        if os.getenv('DEBUG', 'False').lower() == 'true':
            st.exception(e)
        else:
            st.info("Por favor, recarregue a página ou entre em contato com o suporte.")
        
        # Log do erro
        print(f"Erro na aplicação: {repr(e)}", file=sys.stderr)
        
        # Botão para recarregar
        if st.button("🔄 Recarregar Página"):
            # Limpa session state problemático
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

def show_mobile_menu():
    """Menu especial para dispositivos móveis"""
    st.markdown("""
    <div class="mobile-nav-btn" onclick="document.querySelector('.css-1d391kg').style.display = 'block';">
        📱
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    # Inicializa estado da sessão
    init_session_state()
    
    # Executa aplicação com tratamento de erros
    handle_errors()