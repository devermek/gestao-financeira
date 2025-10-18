import streamlit as st
import pandas as pd
import time
from datetime import date, datetime
from config.database import get_db_connection
from utils.helpers import format_date_br, get_categorias_ativas, format_currency_br
from utils.file_manager import FileManager, show_file_gallery

def show_lancamentos(user):
    """Exibe página de lançamentos financeiros"""
    st.header("📊 Gestão de Lançamentos Financeiros")
    
    # Tabs para organizar
    tab1, tab2, tab3 = st.tabs(["➕ Novo Lançamento", "�� Histórico", "🔍 Detalhes"])
    
    with tab1:
        _show_novo_lancamento(user)
    
    with tab2:
        _show_historico_lancamentos(user)
    
    with tab3:
        _show_detalhes_lancamento(user)

def _show_novo_lancamento(user):
    """Formulário para novo lançamento"""
    st.subheader("➕ Adicionar Novo Lançamento")
    
    # CSS customizado para os campos e botões
    st.markdown("""
    <style>
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > select,
        .stDateInput > div > div > input {
            background-color: #3498db !important;
            border: 2px solid #5dade2 !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            padding: 0.75rem !important;
            font-size: 1rem !important;
            font-weight: 500 !important;
            transition: all 0.3s ease !important;
        }
        
        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus,
        .stSelectbox > div > div > select:focus,
        .stDateInput > div > div > input:focus {
            background-color: #5dade2 !important;
            border-color: #85c1e9 !important;
            box-shadow: 0 0 0 3px rgba(133, 193, 233, 0.4) !important;
            outline: none !important;
        }
        
        .stNumberInput input::-webkit-outer-spin-button,
        .stNumberInput input::-webkit-inner-spin-button {
            -webkit-appearance: none !important;
            margin: 0 !important;
        }
        
        .stNumberInput input[type=number] {
            -moz-appearance: textfield !important;
        }
        
        .stForm button[kind="primary"] {
            background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%) !important;
            border: none !important;
            padding: 1rem 2rem !important;
            font-size: 1.2rem !important;
            font-weight: bold !important;
            border-radius: 10px !important;
            color: white !important;
            box-shadow: 0 6px 20px rgba(46, 204, 113, 0.4) !important;
            width: 100% !important;
        }
        .info-card {
            background-color: #2c3e50;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        .info-card h4 {
            color: #ecf0f1;
            margin-top: 0;
        }
        .info-card p {
            color: #bdc3c7;
            margin-bottom: 5px;
        }
        .info-card strong {
            color: #ecf0f1;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Obtenção das categorias
    categorias = get_categorias_ativas()
    
    if not categorias:
        st.error("❌ **Nenhuma categoria ativa encontrada!** Para adicionar um lançamento, você precisa primeiro criar categorias.")
        st.info("Por favor, vá para a página de **⚙️ Configurações** e adicione novas categorias.")
        return # Retorna para não renderizar o formulário vazio
    
    categoria_opcoes = {cat['nome']: cat['id'] for cat in categorias}
    
    with st.form("novo_lancamento", clear_on_submit=True):
        st.markdown("### 📝 Dados do Lançamento")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Data
            data = st.date_input(
                "📅 Data do Lançamento", 
                value=date.today(),
                format="DD/MM/YYYY"
            )
            
            # Categoria
            default_index = 0 if categoria_opcoes else None 
            categoria_selecionada = st.selectbox(
                "��️ Categoria do Gasto", 
                options=list(categoria_opcoes.keys()),
                index=default_index,
                placeholder="Escolha uma categoria..."
            )
        
        with col2:
            # Valor
            valor = st.number_input(
                "💰 Valor em Reais (R$)", 
                min_value=0.01,
                value=1.00,
                step=0.01,
                format="%.2f"
            )
            
            # Descrição
            descricao = st.text_input(
                "📝 Descrição do Gasto", 
                placeholder="Ex: Compra de cimento Portland 50kg..."
            )
        
        # Observações
        observacoes = st.text_area(
            "📋 Observações (Opcional)", 
            placeholder="Informações extras...",
            height=100
        )
        
        # Upload
        uploaded_files = st.file_uploader(
            "📸 Comprovantes (Opcional)",
            type=['jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx'],
            accept_multiple_files=True
        )
        
        # Botão de salvar
        submitted = st.form_submit_button(
            "💾 Salvar Lançamento",
            type="primary",
            use_container_width=True
        )
        
        # PROCESSAMENTO DO FORMULÁRIO
        if submitted:
            # Validação
            erros = []
            
            if not categoria_selecionada:
                erros.append("⚠️ Selecione uma categoria")
            
            if not valor or valor <= 0:
                erros.append("💰 Digite um valor maior que R$ 0,00")
            
            if not descricao or not descricao.strip():
                erros.append("�� Digite uma descrição")
            
            if erros:
                st.error("❌ **Corrija os seguintes campos:**")
                for erro in erros:
                    st.error(f"   • {erro}")
                return
            
            # Tentar salvar
            try:
                # Buscar ID da categoria
                categoria_id = categoria_opcoes[categoria_selecionada]
                
                # Conectar ao banco
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Preparar dados para inserção
                dados_insercao = (data, categoria_id, descricao, valor, observacoes, user['id'])
                
                # Executar INSERT
                cursor.execute("""
                    INSERT INTO lancamentos (data, categoria_id, descricao, valor, observacoes, usuario_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, dados_insercao)
                
                # Obter ID do lançamento
                lancamento_id = cursor.lastrowid
                
                # Commit
                conn.commit()
                
                # Fechar conexão
                conn.close()
                
                st.success(f"🎉 **Lançamento #{lancamento_id} salvo com sucesso!**")
                
                # Salvar arquivos se houver
                if uploaded_files:
                    arquivos_salvos = 0
                    for uploaded_file in uploaded_files:
                        file_data = uploaded_file.read()
                        success, message = FileManager.save_file(
                            file_data, uploaded_file.name, lancamento_id, user['id']
                        )
                        if success:
                            arquivos_salvos += 1
                        else:
                            st.error(f"❌ Erro no arquivo {uploaded_file.name}: {message}")
                    
                    if arquivos_salvos > 0:
                        st.success(f"📎 {arquivos_salvos} arquivo(s) anexado(s)!")
                
                st.balloons()
                
                # Aguardar um pouco e recarregar
                time.sleep(2)
                st.rerun() # Recarrega a página para limpar o formulário e atualizar o histórico
                
            except Exception as e:
                st.error(f"❌ **Erro ao salvar lançamento:** {str(e)}")
                # Para debug mais aprofundado, pode-se reativar o traceback abaixo:
                # import traceback
                # st.code(traceback.format_exc())
                    
        
def _show_historico_lancamentos(user):
    """Exibe histórico de lançamentos com visualização melhorada de comprovantes"""
    st.subheader("�� Histórico de Lançamentos")
    
    # Filtros em linha
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        categorias = get_categorias_ativas()
        categoria_filtro = st.selectbox(
            "🏷️ Categoria", 
            options=["Todas"] + [cat['nome'] for cat in categorias],
            index=0
        )
    
    with col2:
        data_inicio = st.date_input("�� Data Início", value=None)
    
    with col3:
        data_fim = st.date_input("📅 Data Fim", value=None)
    
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Atualizar"):
            st.rerun()
    
    # Buscar lançamentos
    lancamentos = _get_lancamentos_filtrados(categoria_filtro, data_inicio, data_fim)
    
    if lancamentos.empty:
        st.info(" Nenhum lançamento encontrado com os filtros aplicados")
        return
    
    # Resumo
    col_resumo1, col_resumo2 = st.columns(2)
    with col_resumo1:
        st.metric("📊 Total de Lançamentos", len(lancamentos))
    with col_resumo2:
        st.metric("💰 Valor Total", f"R$ {format_currency_br(lancamentos['valor'].sum())}")
    
    st.markdown("---")
    
    # NOVA VISUALIZAÇÃO: Cards com comprovantes
    st.markdown("### 📋 Lançamentos com Comprovantes")
    
    for _, lancamento in lancamentos.iterrows():
        # Verificar se tem arquivos anexados
        arquivos = FileManager.get_files_by_lancamento(lancamento['id'])
        tem_arquivos = len(arquivos) > 0
        
        # Container do lançamento
        with st.container(border=True):
            # Cabeçalho do card
            col_header1, col_header2, col_header3, col_header4 = st.columns([2, 2, 2, 1])
            
            with col_header1:
                st.markdown(f"**🆔 #{lancamento['id']} - {format_date_br(lancamento['data'])}**")
                st.markdown(f"🏷️ {lancamento['categoria']}")
            
            with col_header2:
                st.markdown(f"**📝 {lancamento['descricao']}**")
                if lancamento['observacoes']:
                    st.caption(f"📋 {lancamento['observacoes'][:50]}...")
            
            with col_header3:
                st.markdown(f"**💰 R$ {format_currency_br(lancamento['valor'])}**")
                st.caption(f" {lancamento['usuario']}")
            
            with col_header4:
                if tem_arquivos:
                    st.markdown(f"**📎 {len(arquivos)} arquivo(s)**")
                    # Ícones dos tipos de arquivo
                    tipos_arquivo = set([arq[2] for arq in arquivos])
                    icons = []
                    if 'images' in tipos_arquivo:
                        icons.append("🖼️")
                    if 'documents' in tipos_arquivo:
                        icons.append("��")
                    if 'spreadsheets' in tipos_arquivo:
                        icons.append("📊")
                    st.markdown(" ".join(icons))
                else:
                    st.markdown("�� Sem anexos")
            
            # SEÇÃO DE COMPROVANTES (expansível)
            if tem_arquivos:
                with st.expander(f"�� Ver {len(arquivos)} Comprovante(s) - Lançamento #{lancamento['id']}", expanded=False):
                    _show_comprovantes_inline(lancamento['id'], user['id'], user['tipo'])

def _show_comprovantes_inline(lancamento_id, user_id, user_tipo):
    """Mostra comprovantes inline no histórico"""
    arquivos = FileManager.get_files_by_lancamento(lancamento_id)
    
    if not arquivos:
        st.info("📁 Nenhum arquivo encontrado")
        return
    
    # Separar por tipo
    imagens = [arq for arq in arquivos if arq[2] == 'images']
    documentos = [arq for arq in arquivos if arq[2] in ['documents', 'spreadsheets']]
    
    # Mostrar imagens em grid
    if imagens:
        st.markdown("#### 🖼️ Imagens")
        
        # Grid de 4 colunas para imagens
        cols = st.columns(4)
        for i, img in enumerate(imagens):
            with cols[i % 4]:
                try:
                    nome, tipo, conteudo = FileManager.get_file_content(img[0])
                    
                    if conteudo:
                        from PIL import Image
                        import io
                        
                        image = Image.open(io.BytesIO(conteudo))
                        st.image(image, caption=nome, use_container_width=True)
                        
                        # Botões compactos
                        col_btn1, col_btn2 = st.columns(2)
                        
                        with col_btn1:
                            st.download_button(
                                "📥",
                                data=conteudo,
                                file_name=nome,
                                mime=f"image/{nome.split('.')[-1].lower()}",
                                key=f"dl_hist_img_{img[0]}",
                                help="Baixar imagem"
                            )
                        
                        with col_btn2:
                            if user_tipo == 'gestor':
                                if st.button("🗑️", key=f"del_hist_img_{img[0]}", help="Deletar"):
                                    success, message = FileManager.delete_file(img[0], user_id)
                                    if success:
                                        st.success(message)
                                        st.rerun()
                                    else:
                                        st.error(message)
                
                except Exception as e:
                    st.error(f"❌ Erro ao exibir imagem {img[1]}: {e}")
    
    # Mostrar documentos em lista
    if documentos:
        st.markdown("####  Documentos")
        
        for doc in documentos:
            col_doc1, col_doc2, col_doc3 = st.columns([3, 1, 1])
            
            with col_doc1:
                # Ícone baseado no tipo
                if doc[1].lower().endswith('.pdf'):
                    emoji = "📄"
                elif doc[1].lower().endswith(('.doc', '.docx')):
                    emoji = ""
                elif doc[1].lower().endswith(('.xls', '.xlsx', '.csv')):
                    emoji = "📊"
                else:
                    emoji = "📎"
                
                st.write(f"{emoji} **{doc[1]}**")
                st.caption(f"📅 {doc[4]} | 📏 {doc[3]} bytes")
            
            with col_doc2:
                nome, tipo, conteudo = FileManager.get_file_content(doc[0])
                
                if conteudo:
                    # Detecção mais robusta do MIME type
                    if nome.lower().endswith('.pdf'):
                        mime_type = 'application/pdf'
                    elif nome.lower().endswith(('.doc', '.docx')):
                        mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' if nome.lower().endswith('.docx') else 'application/msword'
                    elif nome.lower().endswith(('.xls', '.xlsx')):
                        mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if nome.lower().endswith('.xlsx') else 'application/vnd.ms-excel'
                    elif nome.lower().endswith('.csv'):
                        mime_type = 'text/csv'
                    else:
                        mime_type = 'application/octet-stream'
                    
                    st.download_button(
                        "📥 Baixar",
                        data=conteudo,
                        file_name=nome,
                        mime=mime_type,
                        key=f"dl_doc_hist_{doc[0]}"
                    )
            
            with col_doc3:
                if user_tipo == 'gestor':
                    if st.button("🗑️ Deletar", key=f"del_doc_hist_{doc[0]}"):
                        success, message = FileManager.delete_file(doc[0], user_id)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                            
def _show_detalhes_lancamento(user):
    """Exibe detalhes de um lançamento específico"""
    st.subheader("�� Buscar Lançamento por ID")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        lancamento_id_input = st.number_input("🆔 ID do Lançamento", min_value=1, step=1, value=None, key="lancamento_id_search")
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        buscar = st.button("🔎 Buscar", type="primary")
    
    if buscar and lancamento_id_input:
        lancamento_id = int(lancamento_id_input)
        # Buscar lançamento
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT l.id, l.data, l.descricao, l.valor, l.observacoes, l.created_at,
                   c.nome as categoria, u.nome as usuario
            FROM lancamentos l
            LEFT JOIN categorias c ON l.categoria_id = c.id
            LEFT JOIN usuarios u ON l.usuario_id = u.id
            WHERE l.id = ?
        """, (lancamento_id,))
        
        lancamento = cursor.fetchone()
        conn.close()
        
        if lancamento:
            st.success(f"✅ Lançamento #{lancamento[0]} encontrado!")
            
            # Exibir detalhes em card
            st.markdown(f"""
            <div class="info-card">
                <h4>📊 Lançamento #{lancamento[0]}</h4>
                <p><strong> Data:</strong> {format_date_br(lancamento[1])}</p>
                <p><strong>🏷️ Categoria:</strong> {lancamento[6]}</p>
                <p><strong>💰 Valor:</strong> R$ {format_currency_br(lancamento[3])}</p>
                <p><strong> Descrição:</strong> {lancamento[2]}</p>
                <p><strong>�� Usuário:</strong> {lancamento[7]}</p>
                <p><strong>🕐 Criado em:</strong> {lancamento[5]}</p>
                {f'<p><strong>📋 Observações:</strong> {lancamento[4]}</p>' if lancamento[4] else ''}
            </div>
            """, unsafe_allow_html=True)
            
            # Galeria de arquivos
            st.markdown("---")
            show_file_gallery(lancamento[0], user['id'], user['tipo'])
            
        else:
            st.error(f"❌ Lançamento #{lancamento_id} não encontrado!")

def _get_lancamentos_filtrados(categoria_filtro, data_inicio, data_fim):
    """Busca lançamentos com filtros aplicados"""
    conn = get_db_connection()
    
    query = """
        SELECT l.id, l.data, l.descricao, l.valor, l.observacoes,
               c.nome as categoria, u.nome as usuario
        FROM lancamentos l
        LEFT JOIN categorias c ON l.categoria_id = c.id
        LEFT JOIN usuarios u ON l.usuario_id = u.id
        WHERE 1=1
    """
    params = []
    
    if categoria_filtro != "Todas":
        query += " AND c.nome = ?"
        params.append(categoria_filtro)
    
    if data_inicio:
        query += " AND l.data >= ?"
        params.append(data_inicio)
    
    if data_fim:
        query += " AND l.data <= ?"
        params.append(data_fim)
    
    query += " ORDER BY l.data DESC, l.id DESC"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return df