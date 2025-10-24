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
from utils.helpers import get_obra_config, format_currency_br # Importar format_currency_br para uso na sidebar
from utils.styles import load_css # Importar a função para carregar CSS

# Configuração da página - REMOVIDO ARGUMENTO 'theme'
st.set_page_config(
    page_title="Sistema de Gestão de Obras",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Carregar CSS personalizado (agora ele é o ÚNICO responsável pelo tema escuro)
load_css()

# Verificar autenticação
if not is_authenticated():
    show_login_page()
else:
    # Usuário autenticado - OBTER DADOS NECESSÁRIOS
    user = get_current_user()
    
    # --- NOVO: Tratamento defensivo para obra_config ---
    obra_config_raw = get_obra_config()
    if not isinstance(obra_config_raw, dict):
        st.error(f"❌ Erro crítico: A configuração da obra não retornou um dicionário. Tipo retornado: {type(obra_config_raw)}")
        st.info("Verifique os logs do Render para mais detalhes. Reinicialize o DB se necessário.")
        st.stop() # Interrompe a execução para evitar o erro de atributo
    obra_config = obra_config_raw
    # --- FIM NOVO ---
    
    # Converter user para dict se necessário (compatibilidade PostgreSQL)
    if hasattr(user, 'to_dict'):
        user = user.to_dict()
    
    # Cabeçalho do usuário
    show_user_header()
    
    # Sidebar de navegação
    st.sidebar.title("🏗️ Menu Principal")
    
    # === SIMPLIFICAÇÃO: Remover lógica de tipo de usuário para o menu ===
    menu_options = {
        "📊 Dashboard": "dashboard",
        "💰 Lançamentos": "lancamentos", 
        "📈 Relatórios": "relatorios",
        "⚙️ Configurações": "configuracoes"
    }
    # === FIM DA SIMPLIFICAÇÃO ===
    
    # Seleção da página
    selected_page = st.sidebar.selectbox(
        "Selecione uma opção:",
        options=list(menu_options.keys()),
        key="main_menu"
    )
    
    # Informações da obra na sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ��️ Informações da Obra")
    if obra_config and obra_config.get('nome_obra'):
        st.sidebar.info(f"**{obra_config['nome_obra']}**")
        
        # GARANTIR QUE ORÇAMENTO SEJA NÚMERO ANTES DE FORMATAR
        orcamento = obra_config.get('orcamento_total', 0.0)
        try:
            orcamento = float(orcamento) # Converte para float, caso seja string ou Decimal
        except (ValueError, TypeError):
            orcamento = 0.0 # Define como 0.0 se a conversão falhar

        st.sidebar.metric("💰 Orçamento", format_currency_br(orcamento)) # Usando a função format_currency_br
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
