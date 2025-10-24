import streamlit as st

def load_css():
    """Carrega estilos CSS personalizados - Tema Escuro Forçado e Visibilidade Garantida"""
    st.markdown("""
    <style>
        /* Importar fonte do Google */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        /* Tema Escuro Global - O MAIS AGRESSIVO POSSÍVEL */
        html, body {
            background-color: #0e1117 !important; /* Fundo principal escuro */
            color: #ffffff !important; /* Cor do texto padrão branca */
            font-family: 'Inter', sans-serif !important;
            line-height: 1.5 !important; /* Evita letras cortadas */
        }

        /* Aplica o fundo escuro e cor de texto a todos os containers principais do Streamlit */
        .stApp, .main, [data-testid="stAppViewContainer"], [data-testid="stVerticalBlock"], 
        .block-container, .st-emotion-cache-z5fcl4 {
            background-color: #0e1117 !important;
            color: #ffffff !important;
        }

        /* Sidebar */
        [data-testid="stSidebar"], .css-1d391kg, .st-emotion-cache-l9rwms {
            background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%) !important;
            color: #ffffff !important;
        }
        /* Aplica cor branca a TODOS os elementos dentro da sidebar, exceto métricas */
        [data-testid="stSidebar"] *, .css-1d391kg *, .st-emotion-cache-l9rwms * { 
            color: #ffffff !important;
        }
        
        /* Textos gerais (reforça a cor e line-height em qualquer elemento de texto) */
        h1, h2, h3, h4, h5, h6, .stMarkdown, .stText, p, span, div, li, a, label, strong, small {
            color: #ffffff !important;
            line-height: 1.5 !important;
        }
        
        /* Títulos */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
        }
        
        /* Estilos do cabeçalho principal da aplicação */
        .main-header {
            background: linear-gradient(90deg, #1f4e79, #2e86de) !important;
            padding: 1rem !important;
            border-radius: 10px !important;
            margin-bottom: 2rem !important;
            color: white !important;
        }

        /* Card de métrica inicial (mantém o fundo branco para contraste, se necessário) */
        .metric-card {
            background: white !important;
            padding: 1rem !important;
            border-radius: 8px !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
            border-left: 4px solid #2e86de !important;
            color: #000000 !important;
        }
        .metric-card h3, .metric-card p {
            color: #000000 !important;
        }
        
        /* Login Container */
        .login-container {
            max-width: 600px !important;
            margin: 2rem auto !important;
            padding: 2rem !important;
            border-radius: 15px !important;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5) !important;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        
        /* Login Title & Subtitle */
        .login-title {
            text-align: center !important;
            color: white !important;
            font-size: 2.5rem !important;
            font-weight: bold !important;
            margin-bottom: 0.5rem !important;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5) !important;
            font-family: 'Inter', sans-serif !important;
        }
        .login-subtitle {
            text-align: center !important;
            color: rgba(255, 255, 255, 0.9) !important;
            font-size: 1.2rem !important;
            margin-bottom: 2rem !important;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5) !important;
            font-family: 'Inter', sans-serif !important;
        }
        
        /* Quick Login Buttons */
        .quick-login-container {
            background: rgba(255, 255, 255, 0.1) !important;
            padding: 1.5rem !important;
            border-radius: 10px !important;
            margin: 1rem 0 !important;
            backdrop-filter: blur(10px) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }
        .quick-login-title {
            color: white !important;
            font-size: 1.3rem !important;
            font-weight: bold !important;
            text-align: center !important;
            margin-bottom: 1rem !important;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5) !important;
            font-family: 'Inter', sans-serif !important;
        }
        
        /* Obra Header */
        .obra-header {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%) !important;
            color: white !important;
            padding: 1.5rem !important;
            border-radius: 15px !important;
            margin-bottom: 1rem !important;
            text-align: center !important;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        .obra-header h1, .obra-header p {
            color: white !important;
        }
        
        /* User Info */
        .user-info {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            padding: 1rem !important;
            border-radius: 15px !important;
            margin-bottom: 1rem !important;
            border-left: 5px solid #4CAF50 !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }
        .user-info strong, .user-info small {
            color: white !important;
        }
        
        /* Info Cards */
        .info-card {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%) !important;
            padding: 1.5rem !important;
            border-radius: 12px !important;
            margin: 0.5rem 0 !important;
            border-left: 4px solid #4CAF50 !important;
            color: white !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        .info-card strong {
            color: #4CAF50 !important;
        }
        .info-card small {
            color: rgba(255, 255, 255, 0.8) !important;
        }
        .info-card h4 {
            color: #667eea !important;
            margin-bottom: 1rem !important;
            border-bottom: 2px solid #667eea !important;
            padding-bottom: 0.5rem !important;
        }
        
        /* Metric Containers */
        .metric-container {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%) !important;
            padding: 1rem !important;
            border-radius: 10px !important;
            border-left: 4px solid #007bff !important;
            margin: 0.5rem 0 !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
            color: white !important;
        }
        
        /* Improved Metrics */
        .stMetric {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%) !important;
            padding: 1rem !important;
            border-radius: 8px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        [data-testid="stSidebar"] .stMetric label, [data-testid="stSidebar"] .stMetric [data-testid="metric-value"] {
            color: white !important;
        }
        [data-testid="stSidebar"] .stMetric [data-testid="metric-value"] {
             color: #4CAF50 !important;
        }
        
        /* Custom Buttons */
        .stButton > button {
            border-radius: 10px !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            padding: 0.6rem 1.2rem !important;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
        }
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4) !important;
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
        }
        
        /* Form Submit Button */
        .stForm .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%) !important;
            color: white !important;
            font-weight: bold !important;
            font-size: 1.1rem !important;
            padding: 0.75rem 1.5rem !important;
            border-radius: 10px !important;
            border: none !important;
            box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3) !important;
        }
        .stForm .stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #45a049 0%, #4CAF50 100%) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4) !important;
        }
        
        /* Form Improvements */
        .stNumberInput input:focus,
        .stTextInput input:focus,
        .stTextArea textarea:focus,
        .stSelectbox select:focus {
            border-color: #667eea !important;
            box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.25) !important;
            outline: none !important;
            transition: all 0.3s ease !important;
        }
        
        /* Visible Placeholder */
        .stNumberInput input::placeholder,
        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder {
            color: rgba(255, 255, 255, 0.7) !important;
            font-style: italic !important;
        }
        
        /* Upload Section */
        .upload-section {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%) !important;
            padding: 1rem !important;
            border-radius: 10px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            margin: 1rem 0 !important;
        }
        
        /* Custom Inputs (Base styling) */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stDateInput > div > div > input {
            background-color: #2c3e50 !important;
            border: 2px solid #3498db !important;
            border-radius: 8px !important;
            padding: 0.75rem !important;
            font-size: 1rem !important;
            font-weight: 500 !important;
            transition: all 0.3s ease !important;
        }

        /* Custom Selectbox - Displayed value and dropdown list */
        [data-testid^="stSelectbox"] > div:first-child > div:first-child, /* O valor exibido */
        [data-baseweb="popover"] > div > div[role="listbox"] /* A lista de opções */ {
            background-color: #2c3e50 !important; 
            border: 2px solid #3498db !important;
            border-radius: 8px !important;
        }
        /* Texto dentro do selectbox exibido */
        [data-testid^="stSelectbox"] > div:first-child > div:first-child > div:first-child {
            color: #ecf0f1 !important; /* COR BRANCA/CINZA CLARO PARA O TEXTO EXIBIDO DO SELECTBOX */
        }
        /* Texto dentro dos inputs */
        .stTextInput input, .stNumberInput input, .stTextArea textarea, .stDateInput input {
            color: #ecf0f1 !important; /* COR BRANCA/CINZA CLARO PARA O TEXTO DIGITADO NOS INPUTS */
        }

        /* Opções individuais dentro do dropdown */
        [data-baseweb="popover"] > div > div[role="listbox"] > div[role="option"] {
            color: #ecf0f1 !important;
            background-color: transparent !important;
            padding: 10px 15px !important;
            line-height: 1.5 !important;
        }
        /* Efeito hover nas opções do dropdown */
        [data-baseweb="popover"] > div > div[role="listbox"] > div[role="option"]:hover {
            background-color: #34495e !important;
            color: white !important;
        }
        
        /* Remove spin arrows from number input */
        .stNumberInput input::-webkit-outer-spin-button,
        .stNumberInput input::-webkit-inner-spin-button {
            -webkit-appearance: none !important;
            margin: 0 !important;
        }
        .stNumberInput input[type=number] {
            -moz-appearance: textfield !important;
        }
        
        /* Custom Footer */
        .footer-custom {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%) !important;
            padding: 1rem !important;
            border-radius: 10px !important;
            text-align: center !important;
            color: rgba(255, 255, 255, 0.9) !important;
            font-family: 'Inter', sans-serif !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
        }
        .footer-custom strong {
            color: #667eea !important;
        }
        
        /* Custom Expander */
        .streamlit-expanderHeader {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%) !important;
            border-radius: 8px !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 500 !important;
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        
        /* Custom Dataframe */
        .dataframe {
            border-radius: 8px !important;
            overflow: hidden !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
            background-color: #1a1a2e !important;
            color: #ffffff !important;
        }
        .dataframe th, .dataframe td {
            color: #ffffff !important;
        }
        
        /* Custom Alerts */
        .stAlert {
            border-radius: 8px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: white !important;
        }
        /* Alert types */
        .stAlert[data-baseweb="notification"] { background-color: rgba(76, 175, 80, 0.1) !important; border-left: 4px solid #4CAF50 !important; }
        .stAlert[data-baseweb="notification"][kind="error"] { background-color: rgba(244, 67, 54, 0.1) !important; border-left: 4px solid #f44336 !important; }
        .stAlert[data-baseweb="notification"][kind="warning"] { background-color: rgba(255, 152, 0, 0.1) !important; border-left: 4px solid #ff9800 !important; }
        .stAlert[data-baseweb="notification"][kind="info"] { background-color: rgba(33, 150, 243, 0.1) !important; border-left: 4px solid #2196f3 !important; }
        
        /* Forms */
        .stForm {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%) !important;
            padding: 1.5rem !important;
            border-radius: 12px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
            color: #ffffff !important;
        }
        
        /* Custom Tabs */
        .stTabs [data-baseweb="tab-list"] { background-color: #1a1a2e !important; border-radius: 8px !important; }
        .stTabs [data-baseweb="tab"] { color: white !important; background-color: transparent !important; }
        .stTabs [aria-selected="true"] { background-color: #667eea !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)