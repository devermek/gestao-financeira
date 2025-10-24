import streamlit as st

def load_css():
    """Carrega CSS personalizado para tema escuro"""
    css = """
    <style>
    /* Importa fonte do Google */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Reset e configurações globais */
    .stApp {
        background-color: #0e1117 !important;
        color: #fafafa !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Sidebar */
    .css-1d391kg, .css-1cypcdb {
        background-color: #262730 !important;
    }
    
    /* Containers principais */
    .main .block-container {
        background-color: #0e1117 !important;
        color: #fafafa !important;
        padding-top: 2rem !important;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #fafafa !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
    }
    
    /* Texto geral */
    p, div, span, label {
        color: #fafafa !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Inputs de texto */
    .stTextInput > div > div > input {
        background-color: #262730 !important;
        color: #fafafa !important;
        border: 1px solid #404040 !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #1f77b4 !important;
        box-shadow: 0 0 0 2px rgba(31, 119, 180, 0.2) !important;
    }
    
    /* Text areas */
    .stTextArea > div > div > textarea {
        background-color: #262730 !important;
        color: #fafafa !important;
        border: 1px solid #404040 !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #1f77b4 !important;
        box-shadow: 0 0 0 2px rgba(31, 119, 180, 0.2) !important;
    }
    
    /* Number inputs */
    .stNumberInput > div > div > input {
        background-color: #262730 !important;
        color: #fafafa !important;
        border: 1px solid #404040 !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    .stNumberInput > div > div > input:focus {
        border-color: #1f77b4 !important;
        box-shadow: 0 0 0 2px rgba(31, 119, 180, 0.2) !important;
    }
    
    /* Date inputs */
    .stDateInput > div > div > input {
        background-color: #262730 !important;
        color: #fafafa !important;
        border: 1px solid #404040 !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    .stDateInput > div > div > input:focus {
        border-color: #1f77b4 !important;
        box-shadow: 0 0 0 2px rgba(31, 119, 180, 0.2) !important;
    }
    
    /* Selectbox */
    .stSelectbox > div > div > select {
        background-color: #262730 !important;
        color: #fafafa !important;
        border: 1px solid #404040 !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    .stSelectbox > div > div > div {
        background-color: #262730 !important;
        color: #fafafa !important;
        border: 1px solid #404040 !important;
        border-radius: 8px !important;
    }
    
    /* Multiselect */
    .stMultiSelect > div > div > div {
        background-color: #262730 !important;
        color: #fafafa !important;
        border: 1px solid #404040 !important;
        border-radius: 8px !important;
    }
    
    /* Botões */
    .stButton > button {
        background-color: #1f77b4 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background-color: #1565c0 !important;
        box-shadow: 0 4px 8px rgba(31, 119, 180, 0.3) !important;
        transform: translateY(-1px) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Botões secundários */
    .stButton > button[kind="secondary"] {
        background-color: #404040 !important;
        color: #fafafa !important;
        border: 1px solid #606060 !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background-color: #505050 !important;
    }
    
    /* File uploader */
    .stFileUploader > div > div {
        background-color: #262730 !important;
        border: 2px dashed #404040 !important;
        border-radius: 8px !important;
        color: #fafafa !important;
    }
    
    .stFileUploader > div > div:hover {
        border-color: #1f77b4 !important;
    }
    
    /* Métricas */
    .metric-container {
        background-color: #1e1e1e !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        border: 1px solid #404040 !important;
        margin: 0.5rem 0 !important;
    }
    
    div[data-testid="metric-container"] {
        background-color: #1e1e1e !important;
        border: 1px solid #404040 !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    div[data-testid="metric-container"] > div {
        color: #fafafa !important;
    }
    
    /* Alertas e mensagens */
    .stAlert {
        background-color: #262730 !important;
        color: #fafafa !important;
        border-radius: 8px !important;
        border-left: 4px solid #1f77b4 !important;
    }
    
    .stSuccess {
        background-color: #1b4332 !important;
        color: #d1e7dd !important;
        border-left-color: #198754 !important;
    }
    
    .stWarning {
        background-color: #664d03 !important;
        color: #fff3cd !important;
        border-left-color: #ffc107 !important;
    }
    
    .stError {
        background-color: #58151c !important;
        color: #f8d7da !important;
        border-left-color: #dc3545 !important;
    }
    
    .stInfo {
        background-color: #055160 !important;
        color: #b6effb !important;
        border-left-color: #0dcaf0 !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #262730 !important;
        color: #fafafa !important;
        border-radius: 8px !important;
        border: 1px solid #404040 !important;
    }
    
    .streamlit-expanderContent {
        background-color: #1e1e1e !important;
        color: #fafafa !important;
        border: 1px solid #404040 !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #262730 !important;
        border-radius: 8px !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        color: #fafafa !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1f77b4 !important;
        color: white !important;
    }
    
    /* Dataframe */
    .stDataFrame {
        background-color: #262730 !important;
        color: #fafafa !important;
        border-radius: 8px !important;
    }
    
    /* Checkbox e Radio */
    .stCheckbox > label {
        color: #fafafa !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    .stRadio > label {
        color: #fafafa !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Slider */
    .stSlider > div > div > div {
        background-color: #404040 !important;
    }
    
    /* Sidebar específico */
    .css-1d391kg .stSelectbox > div > div {
        background-color: #1e1e1e !important;
        color: #fafafa !important;
        border: 1px solid #404040 !important;
    }
    
    .css-1d391kg .stButton > button {
        background-color: #1f77b4 !important;
        color: white !important;
        width: 100% !important;
        margin: 0.25rem 0 !important;
    }
    
    /* Scrollbar personalizada */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #262730;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #404040;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #505050;
    }
    
    /* Links */
    a {
        color: #1f77b4 !important;
        text-decoration: none !important;
    }
    
    a:hover {
        color: #1565c0 !important;
        text-decoration: underline !important;
    }
    
    /* Tabelas customizadas */
    .data-table {
        width: 100%;
        border-collapse: collapse;
        background-color: #262730 !important;
        color: #fafafa !important;
        border-radius: 8px !important;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .data-table th {
        background-color: #1f77b4 !important;
        color: white !important;
        padding: 12px !important;
        text-align: left !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    .data-table td {
        padding: 12px !important;
        border-bottom: 1px solid #404040 !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    .data-table tr:hover {
        background-color: #1e1e1e !important;
    }
    
    .data-table tr:last-child td {
        border-bottom: none !important;
    }
    
    /* Animações suaves */
    * {
        transition: background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease !important;
    }
    
    /* Remove outline padrão e adiciona focus customizado */
    *:focus {
        outline: none !important;
    }
    
    /* Melhora a aparência dos elementos de formulário */
    .stForm {
        background-color: #1e1e1e !important;
        padding: 1.5rem !important;
        border-radius: 12px !important;
        border: 1px solid #404040 !important;
        margin: 1rem 0 !important;
    }
    
    /* Estilo para containers de cards */
    .card-container {
        background-color: #1e1e1e !important;
        padding: 1.5rem !important;
        border-radius: 12px !important;
        border: 1px solid #404040 !important;
        margin: 1rem 0 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }
    
    /* Responsividade */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        
        .stButton > button {
            width: 100% !important;
            margin: 0.5rem 0 !important;
        }
    }
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)