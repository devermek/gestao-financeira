import streamlit as st

def load_css():
    """Carrega estilos CSS personalizados - Modo Noturno"""
    st.markdown("""
    <style>
        /* Importar fonte do Google */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        /* Configurações globais - MODO NOTURNO (Mais abrangente) */
        body {
            background-color: #0e1117 !important;
            color: #ffffff !important;
            font-family: 'Inter', sans-serif;
            line-height: 1.5; /* Ajuste para letras cortadas */
        }
        .stApp {
            background-color: #0e1117 !important;
            color: #ffffff !important;
        }
        
        /* Containers principais do Streamlit */
        .main .block-container, .st-emotion-cache-z5fcl4 { /* Seletor comum para o container principal do conteúdo */
            padding-top: 2rem;
            padding-bottom: 2rem;
            background-color: #0e1117 !important;
            color: #ffffff !important;
        }
        
        /* Sidebar modo noturno */
        .css-1d391kg, .st-emotion-cache-l9rwms { /* Seletores para a sidebar */
            background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%) !important;
            color: #ffffff !important;
        }
        .css-1d391kg .css-1v0mbdj, .st-emotion-cache-1v0mbdj { /* Título da sidebar */
            color: white !important;
        }
        .css-1d391kg .st-emotion-cache-1r6dm1s { /* Texto geral dentro da sidebar */
            color: white !important;
        }
        
        /* Textos gerais em modo noturno (incluindo li e a, reforçando a cor) */
        .stMarkdown, .stText, p, span, div, li, a, label {
            color: #ffffff !important;
            line-height: 1.5 !important; /* Reforçando line-height para todos os textos */
        }
        
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            color: #ffffff !important;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
        }
        
        /* Estilos do cabeçalho principal da aplicação */
        .main-header {
            background: linear-gradient(90deg, #1f4e79, #2e86de);
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            color: white;
        }

        /* Card de métrica inicial */
        .metric-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #2e86de;
            color: #000000;
        }
        .metric-card h3 {
            color: #000000 !important;
        }
        .metric-card p {
            color: #333333 !important;
        }
        
        /* Container de Login */
        .login-container {
            max-width: 600px;
            margin: 2rem auto;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5);
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Título do Login */
        .login-title {
            text-align: center;
            color: white !important;
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            font-family: 'Inter', sans-serif;
        }
        
        /* Subtítulo do Login */
        .login-subtitle {
            text-align: center;
            color: rgba(255, 255, 255, 0.9) !important;
            font-size: 1.2rem;
            margin-bottom: 2rem;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
            font-family: 'Inter', sans-serif;
        }
        
        /* Botões de Login Rápido */
        .quick-login-container {
            background: rgba(255, 255, 255, 0.1);
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .quick-login-title {
            color: white !important;
            font-size: 1.3rem;
            font-weight: bold;
            text-align: center;
            margin-bottom: 1rem;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
            font-family: 'Inter', sans-serif;
        }
        
        /* Cabeçalho da Obra */
        .obra-header {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white !important;
            padding: 1.5rem;
            border-radius: 15px;
            margin-bottom: 1rem;
            text-align: center;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .obra-header h1 {
            color: white !important;
            margin: 0;
            font-size: 2.2rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            font-family: 'Inter', sans-serif;
            font-weight: 700;
        }
        
        .obra-header p {
            color: rgba(255, 255, 255, 0.95) !important;
            margin: 0.5rem 0 0 0;
            font-size: 1.1rem;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
            font-family: 'Inter', sans-serif;
            font-weight: 500;
        }
        
        /* Informações do Usuário */
        .user-info {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 15px;
            margin-bottom: 1rem;
            border-left: 5px solid #4CAF50;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .user-info strong {
            color: white !important;
            font-size: 1.1rem;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
        }
        
        .user-info small {
            color: rgba(255, 255, 255, 0.9) !important;
            font-weight: 500;
            font-family: 'Inter', sans-serif;
        }
        
        /* Cards de informação */
        .info-card {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 1.5rem;
            border-radius: 12px;
            margin: 0.5rem 0;
            border-left: 4px solid #4CAF50;
            color: white !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .info-card strong {
            color: #4CAF50 !important;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
        }
        
        .info-card small {
            color: rgba(255, 255, 255, 0.8) !important;
            font-family: 'Inter', sans-serif;
        }
        
        /* Cards de informação melhorados */
        .info-card h4 {
            color: #667eea !important;
            margin-bottom: 1rem;
            border-bottom: 2px solid #667eea;
            padding-bottom: 0.5rem;
        }
        
        /* Containers de métricas */
        .metric-container {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 1rem;
            border-radius: 10px;
            border-left: 4px solid #007bff;
            margin: 0.5rem 0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
            color: white !important;
        }
        
        /* Metrics melhorados */
        .stMetric {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Botões personalizados */
        .stButton > button {
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 0.6rem 1.2rem;
            font-weight: 600;
            font-family: 'Inter', sans-serif;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        }
        
        /* Form submit button */
        .stForm .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%) !important;
            color: white !important;
            font-weight: bold;
            font-size: 1.1rem;
            padding: 0.75rem 1.5rem;
            border-radius: 10px;
            border: none;
            box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
        }
        
        .stForm .stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #45a049 0%, #4CAF50 100%) !important;
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
        }
        
        /* Melhorias para formulários */
        .stNumberInput input:focus,
        .stTextInput input:focus,
        .stTextArea textarea:focus,
        .stSelectbox select:focus {
            border-color: #667eea !important;
            box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.25) !important;
            outline: none !important;
            transition: all 0.3s ease;
        }
        
        /* Placeholder mais visível */
        .stNumberInput input::placeholder,
        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder {
            color: rgba(255, 255, 255, 0.7) !important;
            font-style: italic;
        }
        
        /* Upload section */
        .upload-section {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            margin: 1rem 0;
        }
        
        /* Inputs customizados */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stDateInput > div > div > input {
            background-color: #2c3e50 !important;
            border: 2px solid #3498db !important;
            color: #ecf0f1 !important;
            border-radius: 8px !important;
            padding: 0.75rem !important;
            font-size: 1rem !important;
            font-weight: 500 !important;
            transition: all 0.3s ease !important;
        }

        /* Selectbox customizado - Fundo do selectbox e texto selecionado */
        /* Seletor do componente selectbox em si */
        div.stSelectbox > div[data-testid="stForm"] > div > div > div:first-child,
        div.stSelectbox > div > div > div:first-child { 
            background-color: #2c3e50 !important; 
            border: 2px solid #3498db !important;
            color: #ecf0f1 !important;
            border-radius: 8px !important;
            padding: 0.75rem !important;
            min-height: 38px;
            display: flex;
            align-items: center;
        }
        /* Texto exibido dentro do selectbox */
        div.stSelectbox > div > div > div:first-child > div {
            color: #ecf0f1 !important;
        }
        
        /* Selectbox Dropdown (lista de opções) - Seletor mais robusto */
        div[data-baseweb="popover"] > div > div[role="listbox"] {
            background-color: #1a1a2e !important;
            border: 1px solid #3498db !important;
            border-radius: 8px !important;
            color: #ecf0f1 !important; /* Cor padrão para as opções */
        }
        
        /* Opções individuais dentro do dropdown */
        div[data-baseweb="popover"] > div > div[role="listbox"] > div[role="option"] {
            color: #ecf0f1 !important;
            background-color: transparent !important;
            padding: 10px 15px !important;
            line-height: 1.5 !important; /* Ajuste para letras cortadas em opções */
        }
        
        /* Efeito hover nas opções do dropdown */
        div[data-baseweb="popover"] > div > div[role="listbox"] > div[role="option"]:hover {
            background-color: #34495e !important;
            color: white !important;
        }
        
        /* Remover setas de spin do number input */
        .stNumberInput input::-webkit-outer-spin-button,
        .stNumberInput input::-webkit-inner-spin-button {
            -webkit-appearance: none !important;
            margin: 0 !important;
        }
        
        .stNumberInput input[type=number] {
            -moz-appearance: textfield !important;
        }
        
        /* Footer customizado */
        .footer-custom {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            color: rgba(255, 255, 255, 0.9) !important;
            font-family: 'Inter', sans-serif;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }
        
        .footer-custom strong {
            color: #667eea !important;
        }
        
        /* Expander customizado */
        .streamlit-expanderHeader {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 8px;
            font-family: 'Inter', sans-serif;
            font-weight: 500;
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Dataframe customizado */
        .dataframe {
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
            background-color: #1a1a2e !important;
            color: #ffffff !important; /* Garantir que o texto no dataframe seja branco */
        }
        .dataframe th, .dataframe td { /* Cabeçalho e células do dataframe */
            color: #ffffff !important;
        }
        
        /* Sidebar elementos */
        .css-1d391kg .stSelectbox label, .st-emotion-cache-1r6dm1s .stSelectbox label {
            color: white !important;
        }
        
        .css-1d391kg .stMetric, .st-emotion-cache-1r6dm1s .stMetric {
            background: rgba(255, 255, 255, 0.1);
            padding: 0.5rem;
            border-radius: 8px;
            margin: 0.25rem 0;
        }
        
        .css-1d391kg .stMetric label, .st-emotion-cache-1r6dm1s .stMetric label {
            color: white !important;
        }
        
        .css-1d391kg .stMetric [data-testid="metric-value"] {
            color: #4CAF50 !important;
        }
        
        /* Alertas customizados */
        .stAlert {
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: white !important; /* Garantir que o texto dos alertas seja branco */
        }
        
        /* Success alert */
        .stAlert[data-baseweb="notification"] {
            background-color: rgba(76, 175, 80, 0.1) !important;
            border-left: 4px solid #4CAF50;
        }
        
        /* Error alert */
        .stAlert[data-baseweb="notification"][kind="error"] {
            background-color: rgba(244, 67, 54, 0.1) !important;
            border-left: 4px solid #f44336;
        }
        
        /* Warning alert */
        .stAlert[data-baseweb="notification"][kind="warning"] {
            background-color: rgba(255, 152, 0, 0.1) !important;
            border-left: 4px solid #ff9800;
        }
        
        /* Info alert */
        .stAlert[data-baseweb="notification"][kind="info"] {
            background-color: rgba(33, 150, 243, 0.1) !important;
            border-left: 4px solid #2196f3;
        }
        
        /* Formulários */
        .stForm {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            color: #ffffff !important; /* Garantir que o texto do formulário seja branco */
        }
        
        /* Tabs customizadas */
        .stTabs [data-baseweb="tab-list"] {
            background-color: #1a1a2e;
            border-radius: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            color: white !important;
            background-color: transparent;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #667eea !important;
            color: white !important;
        }
    </style>
    """, unsafe_allow_html=True)