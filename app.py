import streamlit as st
import sys
import os

# Adicionar src ao path
sys.path.append(os.path.dirname(__file__))

from modules.auth import show_login_page, show_user_header, is_authenticated, get_current_user
from modules.dashboard import show_dashboard
from modules.lancamentos import show_lancamentos
from modules.relatorios import show_relatorios
from modules.configuracoes import show_configuracoes
from utils.helpers import get_obra_config

# Configuração da página
st.set_page_config(
    page_title="Sistema de Gestão de Obras",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79, #2e86de);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #2e86de;
    }
</style>
""", unsafe_allow_html=True)

# Verificar autenticação
if not is_authenticated():
    show_login_page()
else:
    # Usuário autenticado - OBTER DADOS NECESSÁRIOS
    user = get_current_user()
    obra_config = get_obra_config()
    
    # Converter user para dict se necessário (compatibilidade PostgreSQL)
    if hasattr(user, 'to_dict'):
        user = user.to_dict()
    
    # Cabeçalho do usuário
    show_user_header()
    
    # Sidebar de navegação
    st.sidebar.title("🏗️ Menu Principal")
    
    # Opções do menu baseadas no tipo de usuário
    if user['tipo'] == 'gestor':
        menu_options = {
            "📊 Dashboard": "dashboard",
            "💰 Lançamentos": "lancamentos", 
            "📈 Relatórios": "relatorios",
            "⚙️ Configurações": "configuracoes"
        }
    else:  # investidor
        menu_options = {
            "📊 Dashboard": "dashboard",
            "📈 Relatórios": "relatorios"
        }
    
    # Seleção da página
    selected_page = st.sidebar.selectbox(
        "Selecione uma opção:",
        options=list(menu_options.keys()),
        key="main_menu"
    )
    
    # Informações da obra na sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🏗️ Informações da Obra")
    if obra_config and obra_config.get('nome_obra'):
        st.sidebar.info(f"**{obra_config['nome_obra']}**")
        orcamento = obra_config.get('orcamento_total', 0)
        st.sidebar.metric("💰 Orçamento", f"R\$ {orcamento:,.2f}")
    else:
        st.sidebar.warning("Configure a obra primeiro")
    
    # Roteamento das páginas - PASSAR OS ARGUMENTOS CORRETOS
    page_key = menu_options[selected_page]
    
    try:
        if page_key == "dashboard":
            show_dashboard(user, obra_config)
        elif page_key == "lancamentos":
            show_lancamentos(user)
        elif page_key == "relatorios":
            show_relatorios(user, obra_config)
        elif page_key == "configuracoes":
            show_configuracoes(user, obra_config)
    except Exception as e:
        st.error(f"❌ Erro ao carregar a página: {e}")
        st.info("🔄 Tente recarregar a página ou entre em contato com o suporte.")