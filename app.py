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
    initial_sidebar_state="expanded"
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
    # Apenas um aviso se demo_data não existe, não é um erro crítico
    print("Aviso ao tentar criar dados de demonstração: Módulo 'demo_data' não encontrado.")
except Exception as e:
    print(f"Aviso ao tentar criar dados de demonstração (erro de execução): {e}")

load_css()

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
    opcoes_menu = ["🏠 Tela Inicial", "💰 Lançamentos", "🖼️ Galeria", "📊 Relatórios", "�� Usuários", "⚙️ Configurações"]
else: # Supondo que 'investidor' ou outro tipo tem acesso limitado
    opcoes_menu = ["🏠 Tela Inicial", "🖼️ Galeria", "📊 Relatórios"]

# Seleção da página na sidebar (corrigido: removida a duplicação)
page = st.sidebar.selectbox("Escolha uma opção:", opcoes_menu, label_visibility="collapsed")

# Sidebar com resumo
st.sidebar.markdown("---")
st.sidebar.markdown("### 📈 Resumo Rápido")

total_gasto, total_previsto_categorias, _, _, _ = get_dados_dashboard()
orcamento_obra = obra_config['orcamento_total']
orcamento_referencia = orcamento_obra if orcamento_obra > 0 else total_previsto_categorias
percentual = (total_gasto / orcamento_referencia * 100) if orcamento_referencia > 0 else 0
restante = orcamento_referencia - total_gasto

# --- Injeção de CSS para diminuir a fonte dos valores das métricas da sidebar ---
st.markdown(
    """
    <style>
    div[data-testid="stSidebar"] div[data-testid="stMetricValue"] {
        font-size: 24px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Usando format_currency_br para os valores monetários ---
st.sidebar.metric("💰 Total Gasto", f"R$ {format_currency_br(total_gasto)}")
st.sidebar.metric("📈 % Executado", f"{percentual:.1f}%")

if percentual > 100:
    st.sidebar.error(f"🚨 Orçamento Estourado em R$ {format_currency_br(abs(restante))}!")
elif percentual > 80:
    st.sidebar.warning(f"⚠️ Atenção ao Orçamento! Restam R$ {format_currency_br(restante)}.")
else:
    st.sidebar.success("✅ Dentro do Orçamento!")

# Roteamento de páginas (corrigido: condições e chamadas)
if page == "🏠 Tela Inicial":
    dashboard.show_dashboard(user, obra_config)
elif page == "💰 Lançamentos" and user['tipo'] == 'gestor':
    lancamentos.show_lancamentos(user)
elif page == "🖼️ Galeria": # Emoji corrigido
    galeria.show_galeria(user)
elif page == "📊 Relatórios":
    relatorios.show_relatorios(user, obra_config)
elif page == "�� Usuários" and user['tipo'] == 'gestor':
    usuarios.show_usuarios(user)
elif page == "⚙️ Configurações" and user['tipo'] == 'gestor': # Corrigido a duplicação e chamada
    configuracoes.show_configuracoes(user, obra_config)

# Footer
st.markdown("---")
st.markdown(f"""
<div class="footer-custom">
    🏗️ <strong>{obra_config['nome_obra']}</strong> | 
    Sistema de Gestão Financeira | 
    Usuário: <strong>{user['nome']}</strong> ({user['tipo'].title()})
</div>
""", unsafe_allow_html=True)
