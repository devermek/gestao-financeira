import streamlit as st

def load_css():
    """Carrega estilos CSS personalizados - Aprimoramento do Tema Escuro do Streamlit"""
    st.markdown("""
    <style>
        /* Importar fonte do Google */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        /* Ajustes gerais para o tema escuro do Streamlit */
        html, body, [data-testid="stAppViewContainer"] {
            background-color: var(--background-color, #0e1117); /* Usa a variável do Streamlit ou fallback */
            color: var(--text-color, #ffffff); /* Usa a variável do Streamlit ou fallback */
            font-family: 'Inter', sans-serif;
            line-height: 1.5; /* Garante que as letras não sejam cortadas */
        }

        /* Container principal do conteúdo */
        .main .block-container, [data-testid="stVerticalBlock"] {
            background-color: var(--background-color, #0e1117);
            color: var(--text-color, #ffffff);
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%) !important;
            color: #ffffff;
        }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1 { /* Título da sidebar */
            color: white;
        }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"], 
        [data-testid="stSidebar"] p, 
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label { /* Texto geral dentro da sidebar */
            color: white;
        }
        
        /* Textos gerais (reforça a cor e line-height) */
        h1, h2, h3, h4, h5, h6, .stMarkdown, .stText, p, span, div, li, a, label {
            color: var(--text-color, #ffffff) !important;
            line-height: 1.5 !important;
        }
        
        /* Títulos */
        h1, h2, h3, h4, h5, h6 {
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
        .metric-card h3, .metric-card p {
            color: #000000;
        }
        
        /* Login Container */
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
        
        /* Login Title & Subtitle */
        .login-title {
            text-align: center;
            color: white;
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            font-family: 'Inter', sans-serif;
        }
        .login-subtitle {
            text-align: center;
            color: rgba(255, 255, 255, 0.9);
            font-size: 1.2rem;
            margin-bottom: 2rem;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
            font-family: 'Inter', sans-serif;
        }
        
        /* Quick Login Buttons */
        .quick-login-container {
            background: rgba(255, 255, 255, 0.1);
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .quick-login-title {
            color: white;
            font-size: 1.3rem;
            font-weight: bold;
            text-align: center;
            margin-bottom: 1rem;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
            font-family: 'Inter', sans-serif;
        }
        
        /* Obra Header */
        .obra-header {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 15px;
            margin-bottom: 1rem;
            text-align: center;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .obra-header h1, .obra-header p {
            color: white;
        }
        
        /* User Info */
        .user-info {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 15px;
            margin-bottom: 1rem;
            border-left: 5px solid #4CAF50;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .user-info strong, .user-info small {
            color: white;
        }
        
        /* Info Cards */
        .info-card {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 1.5rem;
            border-radius: 12px;
            margin: 0.5rem 0;
            border-left: 4px solid #4CAF50;
            color: white;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .info-card strong {
            color: #4CAF50;
        }
        .info-card small {
            color: rgba(255, 255, 255, 0.8);
        }
        .info-card h4 {
            color: #667eea;
            margin-bottom: 1rem;
            border-bottom: 2px solid #667eea;
            padding-bottom: 0.5rem;
        }
        
        /* Metric Containers */
        .metric-container {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 1rem;
            border-radius: 10px;
            border-left: 4px solid #007bff;
            margin: 0.5rem 0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
            color: white;
        }
        
        /* Improved Metrics */
        .stMetric {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        [data-testid="stSidebar"] .stMetric label, [data-testid="stSidebar"] .stMetric [data-testid="metric-value"] {
            color: white;
        }
        [data-testid="stSidebar"] .stMetric [data-testid="metric-value"] {
             color: #4CAF50 !important; /* Cor específica para o valor da métrica na sidebar */
        }
        
        /* Custom Buttons */
        .stButton > button {
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 0.6rem 1.2rem;
            font-weight: 600;
            font-family: 'Inter', sans-serif;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        }
        
        /* Form Submit Button */
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
        
        /* Form Improvements */
        .stNumberInput input:focus,
        .stTextInput input:focus,
        .stTextArea textarea:focus,
        .stSelectbox select:focus {
            border-color: #667eea !important;
            box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.25) !important;
            outline: none !important;
            transition: all 0.3s ease;
        }
        
        /* Visible Placeholder */
        .stNumberInput input::placeholder,
        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder {
            color: rgba(255, 255, 255, 0.7) !important;
            font-style: italic;
        }
        
        /* Upload Section */
        .upload-section {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            margin: 1rem 0;
        }
        
        /* Custom Inputs */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stDateInput > div > div > input {
            background-color: #2c3e50;
            border: 2px solid #3498db;
            color: #ecf0f1;
            border-radius: 8px;
            padding: 0.75rem;
            font-size: 1rem;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        /* Custom Selectbox - Displayed value and dropdown list */
        [data-testid^="stSelectbox"] > div:first-child > div:first-child, /* O valor exibido */
        [data-baseweb="popover"] > div > div[role="listbox"] /* A lista de opções */ {
            background-color: #2c3e50 !important; 
            border: 2px solid #3498db !important;
            color: #ecf0f1 !important;
            border-radius: 8px !important;
        }
        /* Texto dentro do selectbox exibido */
        [data-testid^="stSelectbox"] > div:first-child > div:first-child > div:first-child {
            color: #ecf0f1 !important;
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
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            color: rgba(255, 255, 255, 0.9);
            font-family: 'Inter', sans-serif;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }
        .footer-custom strong {
            color: #667eea;
        }
        
        /* Custom Expander */
        .streamlit-expanderHeader {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 8px;
            font-family: 'Inter', sans-serif;
            font-weight: 500;
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Custom Dataframe */
        .dataframe {
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
            background-color: #1a1a2e;
            color: #ffffff;
        }
        .dataframe th, .dataframe td {
            color: #ffffff;
        }
        
        /* Custom Alerts */
        .stAlert {
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: white;
        }
        /* Alert types */
        .stAlert[data-baseweb="notification"] { background-color: rgba(76, 175, 80, 0.1); border-left: 4px solid #4CAF50; }
        .stAlert[data-baseweb="notification"][kind="error"] { background-color: rgba(244, 67, 54, 0.1); border-left: 4px solid #f44336; }
        .stAlert[data-baseweb="notification"][kind="warning"] { background-color: rgba(255, 152, 0, 0.1); border-left: 4px solid #ff9800; }
        .stAlert[data-baseweb="notification"][kind="info"] { background-color: rgba(33, 150, 243, 0.1); border-left: 4px solid #2196f3; }
        
        /* Forms */
        .stForm {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            color: #ffffff;
        }
        
        /* Custom Tabs */
        .stTabs [data-baseweb="tab-list"] { background-color: #1a1a2e; border-radius: 8px; }
        .stTabs [data-baseweb="tab"] { color: white; background-color: transparent; }
        .stTabs [aria-selected="true"] { background-color: #667eea !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)