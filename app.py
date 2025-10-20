import streamlit as st
import os, sys, logging, traceback # Adicionado para logging detalhado
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
    initial_sidebar_state="expanded"
)

# Configurar logging para stderr logo no início
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
print("BOOT: ✅ app.py iniciado. Carregando configurações e inicializando DB.", file=sys.stderr); sys.stderr.flush()

# GARANTIR que o banco está inicializado
try:
    print("BOOT: Chamando init_db()", file=sys.stderr); sys.stderr.flush()
    init_db()
    print("BOOT: ✅ Banco de dados inicializado com sucesso!", file=sys.stderr); sys.stderr.flush()
except Exception as e:
    print(f"BOOT: ❌ ERRO CRÍTICO ao inicializar banco: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr); sys.stderr.flush()
    st.error(f"❌ Erro crítico ao inicializar o banco de dados: {e}")
    st.stop()

# Criar dados de demonstração se necessário (apenas na primeira execução)
try:
    print("BOOT: Tentando importar e criar dados de demonstração (se houver).", file=sys.stderr); sys.stderr.flush()
    from demo_data import create_demo_data
    create_demo_data()
    print("BOOT: ✅ Dados de demonstração processados.", file=sys.stderr); sys.stderr.flush()
except ImportError:
    print("Aviso ao tentar criar dados de demonstração: Módulo 'demo_data' não encontrado (isso é normal se você não o usa).", file=sys.stderr); sys.stderr.flush()
except Exception as e:
    print(f"Aviso ao tentar criar dados de demonstração (erro de execução): {e}", file=sys.stderr); sys.stderr.flush()

load_css()

# Injeção de CSS adicional para corrigir problemas de estilo da sidebar (removido para focar no erro principal)
# O código CSS é grande e desnecessário para o debug inicial.
# Se a app funcionar sem ele, depois podemos reintroduzir.
st.markdown(
    """
    <style>
    /* Estilo mínimo para evitar crashes inesperados de CSS */
    div[data-testid="stSidebar"] {
        background-color: var(--secondary-background, #262730) !important;
        color: var(--text-color, #FAFAFA) !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Sistema de autenticação
if 'user' not in st.session_state:
    st.session_state.user = None

# AQUI ESTÁ O BLOCO CRÍTICO ONDE A FALHA OCORRE AGORA
if st.session_state.user is None:
    print("BOOT: Usuário não logado. Chamando show_login_page().", file=sys.stderr); sys.stderr.flush()
    try:
        show_login_page()
    except Exception as e:
        print(f"BOOT: ❌ ERRO CRÍTICO na chamada de show_login_page(): {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr); sys.stderr.flush()
        st.error(f"❌ Erro crítico na página de login: {e}")
        st.stop() # Interrompe o Streamlit para não continuar em loop de erro
    st.stop() # Este st.stop() é para o fluxo normal de não-logado

# Se chegou até aqui, o usuário está logado
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
    opcoes_menu = ["🏠 Tela Inicial", "🖼️ Galeria", "�� Relatórios"]

# Inicializa o estado para rastrear a seleção da sidebar
if 'last_sidebar_selection' not in st.session_state:
    st.session_state.last_sidebar_selection = opcoes_menu[0]

# Seleção da página na sidebar
page = st.sidebar.selectbox("Escolha uma opção:", opcoes_menu, label_visibility="collapsed", key="sidebar_main_selection")

# Verifica se a seleção da sidebar mudou
if st.session_state.sidebar_main_selection != st.session_state.last_sidebar_selection:
    st.session_state.page_just_selected = True
    st.session_state.last_sidebar_selection = st.session_state.sidebar_main_selection
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
st.sidebar.metric("📊 % Executado", f"{percentual:.1f}%")

if percentual > 100:
    st.sidebar.error(f"🚨 Orçamento Estourado em R$ {format_currency_br(abs(restante))}!")
elif percentual > 80:
    st.sidebar.warning(f"⚠️ Atenção ao Orçamento! Restam R$ {format_currency_br(restante)}.")
else:
    st.sidebar.success("✅ Dentro do Orçamento!")

# Roteamento de páginas
if page == "🏠 Tela Inicial":
    dashboard.show_dashboard(user, obra_config)
elif page == "💰 Lançamentos" and user['tipo'] == 'gestor':
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
if st.session_state.page_just_selected:
    js_code = """
    <script>
    function collapseSidebarOnMobile() {
        if (window.innerWidth < 768) { 
            const sidebarExpander = window.parent.document.querySelector('[data-testid="stSidebarExpander"]');
            if (sidebarExpander && sidebarExpander.getAttribute('aria-expanded') === 'true') {
                sidebarExpander.click();
            }
        }
    }
    setTimeout(collapseSidebarOnMobile, 100); 
    </script>
    """
    st.markdown(js_code, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(f"""
<div class="footer-custom">
    🏠 <strong>{obra_config['nome_obra']}</strong> | 
    Sistema de Gestão Financeira | 
    Usuário: <strong>{user['nome']}</strong> ({user['tipo'].title()})
</div>
""", unsafe_allow_html=True)