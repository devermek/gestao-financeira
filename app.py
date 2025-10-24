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
from modules.auth import check_authentication, show_login_page, show_user_header, logout
from modules.dashboard import show_dashboard
from modules.lancamentos import show_lancamentos
from modules.relatorios import show_relatorios
from modules.configuracoes import show_configuracoes

def main():
    """Função principal da aplicação"""
    
    # Carrega estilos CSS
    load_css()
    
    # Verifica autenticação
    if not check_authentication():
        show_login_page()
        return
    
    # Interface principal para usuários autenticados
    show_main_interface()

def show_main_interface():
    """Interface principal do sistema"""
    
    # Cabeçalho com informações do usuário
    show_user_header()
    
    # Sidebar com navegação
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🧭 Navegação")
        
        # Menu de navegação
        page = st.selectbox(
            "Selecione uma página:",
            options=[
                "📊 Dashboard",
                "💰 Lançamentos", 
                "📈 Relatórios",
                "⚙️ Configurações"
            ],
            index=0
        )
        
        st.markdown("---")
        
        # Informações do sistema
        st.markdown("### ℹ️ Sistema")
        st.caption("🏗️ **Gestão Financeira de Obras**")
        st.caption("📱 **Versão:** 1.0.0")
        st.caption("👨‍💻 **Desenvolvido por:** Deverson")
        
        st.markdown("---")
        
        # Botão de logout
        if st.button("🚪 Sair do Sistema", use_container_width=True):
            logout()
        
        # Links úteis
        st.markdown("---")
        st.markdown("### 🔗 Links Úteis")
        st.markdown("📚 [Documentação](https://github.com)", unsafe_allow_html=True)
        st.markdown("🐛 [Reportar Bug](https://github.com)", unsafe_allow_html=True)
        st.markdown("💡 [Sugestões](https://github.com)", unsafe_allow_html=True)
    
    # Container principal
    with st.container():
        # Roteamento de páginas
        if page == "📊 Dashboard":
            show_dashboard()
        elif page == "💰 Lançamentos":
            show_lancamentos()
        elif page == "�� Relatórios":
            show_relatorios()
        elif page == "⚙️ Configurações":
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
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    # Outras variáveis de sessão conforme necessário
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Dashboard"

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
            st.rerun()

if __name__ == "__main__":
    # Inicializa estado da sessão
    init_session_state()
    
    # Executa aplicação com tratamento de erros
    handle_errors()