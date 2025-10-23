import streamlit as st
import sys
import os

# Adicionar src ao path (ajustado para ser mais robusto, considerando que app.py está na raiz)
# Se 'gestao-obras' é o diretório raiz e app.py está lá, este append garantirá que
# módulos em 'modules' e 'utils' sejam encontrados.
# Caso a estrutura seja: C:\gestao-obras\src\app.py, então o ajuste seria outro.
# Assumindo a estrutura padrão do seu resumo: C:\gestao-obras\app.py
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

# Importações dos módulos da aplicação
from modules.auth import show_login_page, show_user_header, is_authenticated, get_current_user
from modules.dashboard import show_dashboard
from modules.lancamentos import show_lancamentos
from modules.relatorios import show_relatorios
from modules.configuracoes import show_configuracoes
from utils.helpers import get_obra_config
from utils.styles import load_css # <-- Nova importação para os estilos

# Configuração da página
st.set_page_config(
    page_title="Sistema de Gestão de Obras",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Carregar CSS personalizado a partir de utils/styles.py
load_css() # <-- Chamada da função para aplicar os estilos globais

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
            # relatorios.py recebe user e obra_config, conforme sua análise
            show_relatorios(user, obra_config) 
        elif page_key == "configuracoes":
            show_configuracoes(user, obra_config)
    except Exception as e:
        st.error(f"❌ Erro ao carregar a página: {e}")
        st.info("🔄 Tente recarregar a página ou entre em contato com o suporte.")
