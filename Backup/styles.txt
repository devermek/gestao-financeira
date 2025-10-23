import streamlit as st

def load_css():
    """Carrega estilos CSS personalizados - Modo Noturno"""
    st.markdown("""
    <style>
        /* Importar fonte do Google */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        /* Configurações globais - MODO NOTURNO */
        .stApp {
            background-color: #0e1117 !important;
        }
        
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            background-color: #0e1117 !important;
        }
        
        /* Sidebar modo noturno */
        .css-1d391kg {
            background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%) !important;
        }
        
        .css-1d391kg .css-1v0mbdj {
            color: white !important;
        }
        
        /* Textos gerais em modo noturno */
        .stMarkdown, .stText, p, span, div {
            color: #ffffff !important;
        }
        
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            color: #ffffff !important;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
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
        
        /* Cabeçalho da Obra - Mantendo cores vibrantes */
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
        
        /* Informações do Usuário - Mantendo destaque colorido */
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
        
        /* Cards de informação - Fundo escuro com bordas coloridas */
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
        
        /* Containers de métricas - Modo noturno */
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
        
        /* Botões personalizados - Modo noturno */
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
        .stForm .stButton > button {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%) !important;
            color: white !important;
            font-weight: bold;
            font-size: 1.1rem;
            padding: 0.75rem 1.5rem;
            border-radius: 10px;
            border: none;
            box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
        }
        
        .stForm .stButton > button:hover {
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
            transition: all 0.3s ease;
        }
        
        /* Placeholder mais visível */
        .stNumberInput input::placeholder,
        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder {
            color: rgba(255, 255, 255, 0.5) !important;
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
        
        /* Inputs customizados - Modo noturno */
        .stTextInput > div > div > input {
            border-radius: 8px;
            border: 2px solid #2c3e50;
            background-color: #1a1a2e !important;
            color: white !important;
            font-family: 'Inter', sans-serif;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.25);
        }
        
        /* Selectbox customizado - Modo noturno */
        .stSelectbox > div > div > select {
            border-radius: 8px;
            border: 2px solid #2c3e50;
            background-color: #1a1a2e !important;
            color: white !important;
            font-family: 'Inter', sans-serif;
        }
        
        /* Footer customizado - Modo noturno */
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
        
        /* Expander customizado - Modo noturno */
        .streamlit-expanderHeader {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 8px;
            font-family: 'Inter', sans-serif;
            font-weight: 500;
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Dataframe customizado - Modo noturno */
        .dataframe {
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
            background-color: #1a1a2e !important;
        }
        
        /* Sidebar elementos */
        .css-1d391kg .stSelectbox label {
            color: white !important;
        }
        
        .css-1d391kg .stMetric {
            background: rgba(255, 255, 255, 0.1);
            padding: 0.5rem;
            border-radius: 8px;
            margin: 0.25rem 0;
        }
        
        .css-1d391kg .stMetric label {
            color: white !important;
        }
        
        .css-1d391kg .stMetric [data-testid="metric-value"] {
            color: #4CAF50 !important;
        }
        
        /* Alertas customizados */
        .stAlert {
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
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
        }
        
        /* Labels dos inputs */
        .stTextInput label, .stSelectbox label, .stNumberInput label, .stDateInput label, .stTextArea label {
            color: white !important;
            font-family: 'Inter', sans-serif;
            font-weight: 500;
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