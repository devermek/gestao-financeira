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
        </style>
        <div class="sidebar-content">
        """, unsafe_allow_html=True)
        
        st.markdown("### 🧭 Navegação")
        
        # Menu de navegação com ícones mais visíveis
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
        
        # Botões de navegação alternativos para mobile
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
        
        # Links úteis
        st.markdown("### 🔗 Links Úteis")
        st.markdown("""
        <div style="color: #333;">
        📚 <a href="https://github.com" target="_blank" style="color: #1f77b4;">Documentação</a><br>
        🐛 <a href="https://github.com" target="_blank" style="color: #1f77b4;">Reportar Bug</a><br>
        💡 <a href="https://github.com" target="_blank" style="color: #1f77b4;">Sugestões</a>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Container principal
    with st.container():
        # Roteamento de páginas
        current_page = st.session_state.get('current_page', "📊 Dashboard")
        
        if current_page == "📊 Dashboard":
            show_dashboard()
        elif current_page == "💰 Lançamentos":
            show_lancamentos()
        elif current_page == "📈 Relatórios":
            show_relatorios()
        elif current_page == "⚙️ Configurações":
            show_configuracoes()
    
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
    problematic_keys = ['show_user_config', 'editing_lancamento_', 'authenticated', 'user']
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

if __name__ == "__main__":
    # Inicializa estado da sessão
    init_session_state()
    
    # Executa aplicação com tratamento de erros
    handle_errors()