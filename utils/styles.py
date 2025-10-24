import streamlit as st

def load_css():
    """Carrega estilos CSS customizados"""
    st.markdown("""
    <style>
    /* Reset e configurações gerais */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa !important;
    }
    
    .sidebar .sidebar-content {
        background-color: #f8f9fa !important;
        color: #333 !important;
    }
    
    /* Força cor do texto na sidebar */
    .sidebar .sidebar-content * {
        color: #333 !important;
    }
    
    .sidebar .sidebar-content .stSelectbox label {
        color: #333 !important;
        font-weight: bold !important;
        font-size: 14px !important;
    }
    
    .sidebar .sidebar-content .stSelectbox > div > div {
        background-color: white !important;
        color: #333 !important;
        border: 1px solid #ddd !important;
    }
    
    .sidebar .sidebar-content .stButton button {
        background-color: #007bff !important;
        color: white !important;
        border: none !important;
        border-radius: 5px !important;
        font-weight: bold !important;
    }
    
    .sidebar .sidebar-content .stButton button:hover {
        background-color: #0056b3 !important;
    }
    
    /* Cards personalizados */
    .card-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
        color: white;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #007bff;
        margin: 0.5rem 0;
    }
    
    .metric-card h3 {
        color: #333;
        margin: 0 0 0.5rem 0;
        font-size: 1.1rem;
    }
    
    .metric-card .metric-value {
        color: #007bff;
        font-size: 2rem;
        font-weight: bold;
        margin: 0;
    }
    
    /* Botões customizados */
    .stButton > button {
        background: linear-gradient(90deg, #007bff, #0056b3);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        background: linear-gradient(90deg, #0056b3, #004085);
    }
    
    /* Formulários */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select,
    .stNumberInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e9ecef;
        padding: 0.75rem;
        font-size: 1rem;
        transition: border-color 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #007bff;
        box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
    }
    
    /* Tabelas */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .data-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        font-size: 0.9rem;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .data-table thead th {
        background: linear-gradient(90deg, #007bff, #0056b3);
        color: white;
        font-weight: bold;
        padding: 12px 15px;
        text-align: left;
        border: none;
    }
    
    .data-table tbody td {
        padding: 12px 15px;
        border-bottom: 1px solid #e9ecef;
        background: white;
    }
    
    .data-table tbody tr:hover {
        background-color: #f8f9fa;
    }
    
    .data-table tbody tr:last-child td {
        border-bottom: none;
    }
    
    /* Alertas e notificações */
    .stAlert {
        border-radius: 10px;
        border: none;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    /* Métricas do Streamlit */
    [data-testid="metric-container"] {
        background: white;
        border: 1px solid #e9ecef;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        border-left: 4px solid #007bff;
    }
    
    [data-testid="metric-container"] > label {
        color: #6c757d !important;
        font-size: 0.875rem !important;
        font-weight: 600 !important;
    }
    
    [data-testid="metric-container"] > div {
        color: #007bff !important;
        font-size: 1.5rem !important;
        font-weight: bold !important;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #28a745, #20c997);
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background: linear-gradient(90deg, #f8f9fa, #e9ecef);
        border-radius: 8px;
        border: 1px solid #dee2e6;
    }
    
    /* File uploader */
    .stFileUploader > div {
        border: 2px dashed #007bff;
        border-radius: 10px;
        background: #f8f9ff;
        padding: 2rem;
        text-align: center;
    }
    
    /* Responsividade para mobile */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        .card-container {
            padding: 1rem;
            margin: 0.5rem 0;
        }
        
        .metric-card {
            padding: 1rem;
        }
        
        .metric-card .metric-value {
            font-size: 1.5rem;
        }
        
        /* Força sidebar visível em mobile */
        .css-1d391kg {
            width: 100% !important;
            min-width: 100% !important;
        }
        
        /* Botões maiores em mobile */
        .stButton > button {
            padding: 0.75rem 1rem;
            font-size: 1rem;
            width: 100%;
        }
    }
    
    /* Correções específicas para sidebar */
    .css-1d391kg .sidebar-content {
        color: #333 !important;
    }
    
    .css-1d391kg .sidebar-content h1,
    .css-1d391kg .sidebar-content h2,
    .css-1d391kg .sidebar-content h3,
    .css-1d391kg .sidebar-content h4,
    .css-1d391kg .sidebar-content h5,
    .css-1d391kg .sidebar-content h6,
    .css-1d391kg .sidebar-content p,
    .css-1d391kg .sidebar-content span,
    .css-1d391kg .sidebar-content div,
    .css-1d391kg .sidebar-content label {
        color: #333 !important;
    }
    
    /* Força cor escura no selectbox */
    .css-1d391kg .stSelectbox label {
        color: #333 !important;
        font-weight: bold !important;
    }
    
    .css-1d391kg .stSelectbox > div > div {
        background-color: white !important;
        color: #333 !important;
    }
    
    /* Animações suaves */
    * {
        transition: all 0.3s ease;
    }
    
    /* Esconde elementos desnecessários */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Melhora contraste */
    .stMarkdown {
        color: #333;
    }
    
    /* Força visibilidade do texto */
    .sidebar .sidebar-content .stMarkdown {
        color: #333 !important;
    }
    
    .sidebar .sidebar-content .stMarkdown h1,
    .sidebar .sidebar-content .stMarkdown h2,
    .sidebar .sidebar-content .stMarkdown h3,
    .sidebar .sidebar-content .stMarkdown h4,
    .sidebar .sidebar-content .stMarkdown h5,
    .sidebar .sidebar-content .stMarkdown h6,
    .sidebar .sidebar-content .stMarkdown p,
    .sidebar .sidebar-content .stMarkdown span,
    .sidebar .sidebar-content .stMarkdown div,
    .sidebar .sidebar-content .stMarkdown strong {
        color: #333 !important;
    }
    </style>
    """, unsafe_allow_html=True)