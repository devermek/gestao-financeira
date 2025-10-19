import streamlit as st
from config.database import init_db
from utils.styles import load_css
from utils.helpers import get_obra_config, get_dados_dashboard, format_currency_br
from modules.auth import show_login_page, show_user_header
from modules import dashboard, lancamentos, relatorios, usuarios, configuracoes, galeria

# Configuração da página
st.set_page_config(
    page_title="🏗️ Gestão de Obras",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded" # Mantém expandido por padrão (para desktop)
)

# GARANTIR que o banco está inicializado
try:
    init_db()
    print("✅ Banco de dados inicializado com sucesso!")
except Exception as e:
    st.error(f"❌ Erro ao inicializar banco: {e}")
    st.stop()

# Criar dados de demonstração se necessário (apenas na primeira execução)
try:
    from demo_data import create_demo_data
    create_demo_data()
except ImportError:
    print("Aviso ao tentar criar dados de demonstração: Módulo 'demo_data' não encontrado (isso é normal se você não o usa).")
except Exception as e:
    print(f"Aviso ao tentar criar dados de demonstração (erro de execução): {e}")

load_css()

# Injeção de CSS adicional para corrigir problemas de estilo da sidebar
st.markdown(
    """
    <style>
    /* Ajusta o tamanho da fonte para as métricas da sidebar */
    div[data-testid="stSidebar"] div[data-testid="stMetricValue"] {
        font-size: 24px !important;
    }

    /* Força o tema escuro na sidebar e garante texto claro */
    div[data-testid="stSidebar"] {
        background-color: #0E1117 !important; /* Fundo escuro */
        color: #FAFAFA !important; /* Texto claro */
    }

    /* Garante que TODO o conteúdo de texto dentro da sidebar seja visível e claro */
    div[data-testid="stSidebar"] p,
    div[data-testid="stSidebar"] h1,
    div[data-testid="stSidebar"] h2,
    div[data-testid="stSidebar"] h3,
    div[data-testid="stSidebar"] h4,
    div[data-testid="stSidebar"] span,
    div[data-testid="stSidebar"] label,
    div[data-testid="stSidebar"] .stMarkdown,
    div[data-testid="stSidebar"] .stButton > button,
    div[data-testid="stSidebar"] .stMetric,
    div[data-testid="stSidebar"] a { /* Adicionado 'a' para links */
        color: #FAFAFA !important; /* Texto claro para todos os elementos */
    }
    
    /* Ajusta o estilo do selectbox na sidebar */
    div[data-testid="stSidebar"] div.stSelectbox > div > div {
        background-color: #262730 !important; /* Fundo do selectbox ligeiramente mais claro */
        color: #FAFAFA !important;
        border: 1px solid #4B4B4B !important; /* Borda sutil para contraste */
    }
    div[data-testid="stSidebar"] div.stSelectbox > div > div > div > div > span {
        color: #FAFAFA !important; /* Texto da opção selecionada */
    }
    /* Estilo para as opções do selectbox quando abertas (dropdown) */
    .st-emotion-cache-1f190u8 > div > div, .st-emotion-cache-1f190u8 > div > div > div {
        background-color: #262730 !important; /* Fundo do dropdown */
        color: #FAFAFA !important;
    }
    .st-emotion-cache-1f190u8 > div > div:hover {
        background-color: #31333F !important; /* Um tom mais escuro para hover nos itens */
        color: #FAFAFA !important;
    }

    /* Ajusta o cabeçalho e footer para melhor contraste em geral */
    .header-custom, .footer-custom {
        color: #FAFAFA !important;
        background-color: #0E1117 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Sistema de autenticação
if 'user' not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    show_login_page()
    st.stop()

# Usuário logado
user = st.session_state.user
obra_config = get_obra_config()

# Cabeçalho
show_user_header(user, obra_config)

# Sidebar e navegação
st.sidebar.title("📋 Navegação")
st.sidebar.markdown(f"**Usuário:** {user['nome']}")
st.sidebar.markdown(f"**Perfil:** {user['tipo'].title()}")

# Definir opções de menu
if user['tipo'] == 'gestor':
    opcoes_menu = ["�� Tela Inicial", "💰 Lançamentos", "🖼️ Galeria", "📊 Relatórios", "👥 Usuários", "⚙️ Configurações"]
else: # Supondo que 'investidor' ou outro tipo tem acesso limitado
    opcoes_menu = ["🏠 Tela Inicial", "🖼️ Galeria", "📊 Relatórios"]

# Inicializa o estado para rastrear a seleção da sidebar
if 'last_sidebar_selection' not in st.session_state:
    st.session_state.last_sidebar_selection = opcoes_menu[0] # Define um valor inicial

# Seleção da página na sidebar
page = st.sidebar.selectbox("Escolha uma opção:", opcoes_menu, label_visibility="collapsed", key="sidebar_main_selection")

# Verifica se a seleção da sidebar mudou para acionar o JS (auto-colapso)
if page != st.session_state.last_sidebar_selection:
    st.session_state.page_just_selected = True
    st.session_state.last_sidebar_selection = page
else:
    st.session_state.page_just_selected = False


# Sidebar com resumo
st.sidebar.markdown("---")
st.sidebar.markdown("### 📈 Resumo Rápido")

total_gasto, total_previsto_categorias, _, _, _ = get_dados_dashboard()
orcamento_obra = obra_config['orcamento_total']
orcamento_referencia = orcamento_obra if orcamento_obra > 0 else total_previsto_categorias
percentual = (total_gasto / orcamento_referencia * 100) if orcamento_referencia > 0 else 0
restante = orcamento_referencia - total_gasto

# --- Usando format_currency_br para os valores monetários ---
st.sidebar.metric("💰 Total Gasto", f"R$ {format_currency_br(total_gasto)}")
st.sidebar.metric("📈 % Executado", f"{percentual:.1f}%")

if percentual > 100:
    st.sidebar.error(f"🚨 Orçamento Estourado em R$ {format_currency_br(abs(restante))}!")
elif percentual > 80:
    st.sidebar.warning(f"⚠️ Atenção ao Orçamento! Restam R$ {format_currency_br(restante)}.")
else:
    st.sidebar.success("✅ Dentro do Orçamento!")

# Roteamento de páginas
if page == "🏠 Tela Inicial":
    dashboard.show_dashboard(user, obra_config)
elif page == "�� Lançamentos" and user['tipo'] == 'gestor':
    lancamentos.show_lancamentos(user)
elif page == "🖼️ Galeria":
    galeria.show_galeria(user)
elif page == "📊 Relatórios":
    relatorios.show_relatorios(user, obra_config)
elif page == "👥 Usuários" and user['tipo'] == 'gestor':
    usuarios.show_usuarios(user)
elif page == "⚙️ Configurações" and user['tipo'] == 'gestor':
    configuracoes.show_configuracoes(user, obra_config)

# === Injeção de JavaScript para recolher sidebar em mobile após seleção ===
# A condição de disparo agora é 'page_just_selected' que é definida *antes*
# do roteamento, garantindo que o JS seja injetado apenas quando uma nova página é selecionada.
if st.session_state.page_just_selected:
    js_code = """
    <script>
    function collapseSidebarOnMobile() {
        // Verifica se a largura da janela indica um dispositivo móvel (Streamlit usa 768px para mobile)
        if (window.innerWidth <= 768) { 
            const sidebarExpander = window.parent.document.querySelector('[data-testid="stSidebarExpander"]');
            // Se o botão de expandir/recolher existe e a sidebar está expandida (aria-expanded="true")
            if (sidebarExpander && sidebarExpander.getAttribute('aria-expanded') === 'true') {
                sidebarExpander.click(); // Simula um clique para recolher a sidebar
            }
        }
    }
    // Adia a chamada para garantir que o DOM esteja completamente atualizado após o rerun do Streamlit
    // Um atraso um pouco maior para garantir que o clique seja registrado em diferentes dispositivos
    setTimeout(collapseSidebarOnMobile, 200); 
    </script>
    """
    st.markdown(js_code, unsafe_allow_html=True)
# =========================================================================

# Footer
st.markdown("---")
st.markdown(f"""
<div class="footer-custom">
    ��️ <strong>{obra_config['nome_obra']}</strong> | 
    Sistema de Gestão Financeira | 
    Usuário: <strong>{user['nome']}</strong> ({user['tipo'].title()})
</div>
""", unsafe_allow_html=True)