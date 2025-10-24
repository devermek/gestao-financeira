import streamlit as st
import pandas as pd
import time
from datetime import date, datetime
from config.database import get_db_connection
from utils.helpers import format_date_br, get_categorias_ativas, format_currency_br
from utils.file_manager import FileManager, show_file_gallery # Assuming show_file_gallery is needed for details tab

def show_lancamentos(user):
    """Exibe página de lançamentos financeiros"""
    st.header("�� Gestão de Lançamentos Financeiros")
    
    tab1, tab2, tab3 = st.tabs(["➕ Novo Lançamento", "📜 Histórico", "�� Detalhes"])
    
    with tab1:
        _show_novo_lancamento(user)
    
    with tab2:
        _show_historico_lancamentos(user)
    
    with tab3:
        _show_detalhes_lancamento(user)

def _show_novo_lancamento(user):
    """Formulário para novo lançamento"""
    st.subheader("➕ Adicionar Novo Lançamento")
    
    # CSS customizado para os campos e botões (garante que está presente)
    # NOTE: This CSS block should ideally be moved to styles.txt and removed here.
    # Leaving for now as it was in original, but for best practice, centralize.
    st.markdown("""
    <style>
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > div:first-child, /* Corrected selector for displayed value */
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
        
        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus,
        .stSelectbox > div > div > div:first-child:focus, /* Corrected selector for displayed value */
        .stDateInput > div > div > input:focus {
            background-color: #3498db !important;
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
        .info-card { /* Moved from styles.txt to here - keep it in styles.txt only */
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
    """, unsafe_allow_html=True) # THIS BLOCK SHOULD BE REMOVED AND RELY ON styles.txt

    categorias_raw = get_categorias_ativas()
    categorias = [cat for cat in categorias_raw if cat and cat.get('nome') and cat.get('id') is not None]

    if not categorias:
        st.error("❌ **Nenhuma categoria ativa encontrada!** Para adicionar um lançamento, você precisa primeiro criar categorias.")
        st.info("Por favor, vá para a página de **⚙️ Configurações** e adicione novas categorias.")
        return
    
    categoria_opcoes = {cat['nome']: cat['id'] for cat in categorias}
    
    if not categoria_opcoes:
        st.error("❌ Nenhuma categoria válida foi processada para seleção. Verifique as categorias ativas e suas propriedades (nome, ID).")
        return
        
    with st.form("novo_lancamento", clear_on_submit=True):
        st.markdown("### 📝 Dados do Lançamento")
        
        col1, col2 = st.columns(2)
        
        with col1:
            data = st.date_input(
                "📅 Data do Lançamento", 
                value=date.today(),
                format="DD/MM/YYYY"
            )
            
            categoria_selecionada = st.selectbox(
                "🏷️ Categoria do Gasto", 
                options=list(categoria_opcoes.keys()),
                index=0, 
                placeholder="Escolha uma categoria...",
                key="lanc_categoria_select" # Added key
            )
        
        with col2:
            valor = st.number_input(
                "💰 Valor em Reais (R$)", 
                min_value=0.01,
                value=1.00,
                step=0.01,
                format="%.2f",
                key="lanc_valor_input" # Added key
            )
            
            descricao = st.text_input(
                "📝 Descrição do Gasto", 
                placeholder="Ex: Compra de cimento Portland 50kg...",
                key="lanc_descricao_input" # Added key
            )
        
        observacoes = st.text_area(
            "📋 Observações (Opcional)", 
            placeholder="Informações extras...",
            height=100,
            key="lanc_observacoes_area" # Added key
        )
        
        uploaded_files = st.file_uploader(
            "�� Comprovantes (Opcional)",
            type=['jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx'],
            accept_multiple_files=True,
            key="lanc_file_uploader" # Added key
        )
        
        submitted = st.form_submit_button(
            "💾 Salvar Lançamento",
            type="primary",
            use_container_width=True,
            key="lanc_submit_button" # Added key
        )
        
        if submitted:
            erros = []
            categoria_id = None 
            
            if not categoria_selecionada:
                erros.append("⚠️ Selecione uma categoria")
            else:
                categoria_id = categoria_opcoes.get(categoria_selecionada)
                if categoria_id is None:
                    erros.append(f"⚠️ A categoria '{categoria_selecionada}' foi selecionada, mas seu ID não pôde ser recuperado. (Verifique o banco de dados e a função 'get_categorias_ativas').")

            if not valor or valor <= 0:
                erros.append("�� Digite um valor maior que R$ 0,00")
            
            if not descricao or not descricao.strip():
                erros.append("📝 Digite uma descrição")
            
            if erros:
                st.error("❌ **Corrija os seguintes campos:**")
                for erro in erros:
                    st.error(f"   • {erro}")
                return
            
            try:
                conn, db_type = get_db_connection() # Get db_type
                cursor = conn.cursor()
                
                query = """
                    INSERT INTO lancamentos (data, categoria_id, descricao, valor, observacoes, usuario_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                params = (data, categoria_id, descricao, valor, observacoes, user['id'])
                
                if db_type == 'postgresql':
                    query_returning = query.replace('?', '%s') + " RETURNING id"
                    cursor.execute(query_returning, params)
                    lancamento_id = cursor.fetchone()[0]
                else:
                    cursor.execute(query, params)
                    lancamento_id = cursor.lastrowid
                
                conn.commit()
                conn.close()
                
                st.success(f"�� **Lançamento #{lancamento_id} salvo com sucesso!**")
                
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
                
                time.sleep(2)
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ **Erro ao salvar lançamento:** {str(e)}")
                print(f"Erro ao salvar lancamento: {e}", file=sys.stderr); sys.stderr.flush()
                    
        
def _show_historico_lancamentos(user):
    """Exibe histórico de lançamentos com visualização melhorada de comprovantes"""
    st.subheader("�� Histórico de Lançamentos")
    
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        categorias_raw = get_categorias_ativas()
        categorias_filtradas = [cat for cat in categorias_raw if cat and cat.get('nome') and cat.get('id') is not None]
        categoria_filtro = st.selectbox(
            "🏷️ Categoria", 
            options=["Todas"] + [cat['nome'] for cat in categorias_filtradas],
            index=0,
            key="hist_cat_filter" # Added key
        )
    
    with col2:
        data_inicio = st.date_input("🗓️ Data Início", value=None, key="hist_data_inicio") # Added key
    
    with col3:
        data_fim = st.date_input("📅 Data Fim", value=None, key="hist_data_fim") # Added key
    
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Atualizar", key="hist_refresh_button"): # Added key
            st.rerun()
    
    lancamentos = _get_lancamentos_filtrados(categoria_filtro, data_inicio, data_fim)
    
    if lancamentos.empty:
        st.info("ℹ️ Nenhum lançamento encontrado com os filtros aplicados")
        return
    
    col_resumo1, col_resumo2 = st.columns(2)
    with col_resumo1:
        st.metric("📊 Total de Lançamentos", len(lancamentos))
    with col_resumo2:
        st.metric("�� Valor Total", format_currency_br(lancamentos['valor'].sum()))
    
    st.markdown("---")
    
    st.markdown("### 📄 Lançamentos com Comprovantes")
    
    for idx, lancamento in lancamentos.iterrows():
        arquivos = FileManager.get_files_by_lancamento(lancamento['id'])
        tem_arquivos = len(arquivos) > 0
        
        with st.container(border=True):
            col_header1, col_header2, col_header3, col_header4 = st.columns([2, 2, 2, 1])
            
            with col_header1:
                st.markdown(f"**🆔 #{lancamento['id']} - {format_date_br(lancamento['data'])}**")
                st.markdown(f"🏷️ {lancamento['categoria']}")
            
            with col_header2:
                st.markdown(f"**📝 {lancamento['descricao']}**")
                if lancamento['observacoes']:
                    st.caption(f"📋 {lancamento['observacoes'][:50]}...")
            
            with col_header3:
                st.markdown(f"**💰 {format_currency_br(lancamento['valor'])}**")
                st.caption(f"👤 {lancamento['usuario']}")
            
            with col_header4:
                if tem_arquivos:
                    st.markdown(f"**📎 {len(arquivos)} arquivo(s)**")
                    tipos_arquivo = set([arq[2] for arq in arquivos])
                    icons = []
                    if 'images' in tipos_arquivo: icons.append("��️")
                    if 'documents' in tipos_arquivo: icons.append("📄")
                    if 'spreadsheets' in tipos_arquivo: icons.append("📊")
                    st.markdown(" ".join(icons))
                else:
                    st.markdown("🔗 Sem anexos")
            
            if tem_arquivos:
                with st.expander(f"📁 Ver {len(arquivos)} Comprovante(s) - Lançamento #{lancamento['id']}", expanded=False):
                    _show_comprovantes_inline(lancamento['id'], user['id'], user['tipo'])

def _show_comprovantes_inline(lancamento_id, user_id, user_tipo):
    """Mostra comprovantes inline no histórico"""
    arquivos = FileManager.get_files_by_lancamento(lancamento_id)
    
    if not arquivos:
        st.info("🤷 Nenhum arquivo encontrado")
        return
    
    imagens = [arq for arq in arquivos if arq[2] == 'images']
    documentos = [arq for arq in arquivos if arq[2] in ['documents', 'spreadsheets']]
    
    if imagens:
        st.markdown("#### 🖼️ Imagens")
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
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            st.download_button(
                                "📥", data=conteudo, file_name=nome, mime=f"image/{nome.split('.')[-1].lower()}",
                                key=f"dl_hist_img_{img[0]}_{i}", # Unique key
                                help="Baixar imagem"
                            )
                        with col_btn2:
                            if user_tipo == 'gestor':
                                if st.button("🗑️", key=f"del_hist_img_{img[0]}_{i}", help="Deletar"): # Unique key
                                    success, message = FileManager.delete_file(img[0], user_id)
                                    if success:
                                        st.success(message)
                                        st.rerun()
                                    else:
                                        st.error(message)
                except Exception as e:
                    st.error(f"❌ Erro ao exibir imagem {img[1]}: {e}")
                    print(f"Erro ao exibir imagem: {e}", file=sys.stderr); sys.stderr.flush()
    
    if documentos:
        st.markdown("#### 📄 Documentos")
        for idx_doc, doc in enumerate(documentos):
            col_doc1, col_doc2, col_doc3 = st.columns([3, 1, 1])
            with col_doc1:
                emoji = ""
                if doc[1].lower().endswith('.pdf'): emoji = "📄"
                elif doc[1].lower().endswith(('.doc', '.docx')): emoji = "📃"
                elif doc[1].lower().endswith(('.xls', '.xlsx', '.csv')): emoji = "📊"
                else: emoji = "��"
                st.write(f"{emoji} **{doc[1]}**")
                st.caption(f"🗓️ {format_date_br(doc[4])} | 👤 {doc[5]} | 📏 {doc[3]} bytes")
            with col_doc2:
                nome, tipo, conteudo = FileManager.get_file_content(doc[0])
                if conteudo:
                    mime_type = 'application/octet-stream'
                    if nome.lower().endswith('.pdf'): mime_type = 'application/pdf'
                    elif nome.lower().endswith('.docx'): mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    elif nome.lower().endswith('.doc'): mime_type = 'application/msword'
                    elif nome.lower().endswith('.xlsx'): mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    elif nome.lower().endswith('.xls'): mime_type = 'application/vnd.ms-excel'
                    elif nome.lower().endswith('.csv'): mime_type = 'text/csv'
                    
                    st.download_button(
                        "📥 Baixar", data=conteudo, file_name=nome, mime=mime_type,
                        key=f"dl_doc_hist_{doc[0]}_{idx_doc}" # Unique key
                    )
            with col_doc3:
                if user_tipo == 'gestor':
                    if st.button("🗑️ Deletar", key=f"del_doc_hist_{doc[0]}_{idx_doc}"): # Unique key
                        success, message = FileManager.delete_file(doc[0], user_id)
                        if success: st.success(message); st.rerun()
                        else: st.error(message)
                            
def _show_detalhes_lancamento(user):
    """Exibe detalhes de um lançamento específico"""
    st.subheader("�� Buscar Lançamento por ID")
    col1, col2 = st.columns([2, 1])
    with col1:
        lancamento_id_input = st.number_input("🆔 ID do Lançamento", min_value=1, step=1, value=None, key="lancamento_id_search")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        buscar = st.button("🔎 Buscar", type="primary", key="search_lanc_button") # Added key
    
    if buscar and lancamento_id_input:
        lancamento_id = int(lancamento_id_input)
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT l.id, l.data, l.descricao, l.valor, l.observacoes, l.created_at,
                   c.nome as categoria, u.nome as usuario
            FROM lancamentos l
            LEFT JOIN categorias c ON l.categoria_id = c.id
            LEFT JOIN usuarios u ON l.usuario_id = u.id
            WHERE l.id = ?
        """
        params = (lancamento_id,)
        if db_type == 'postgresql':
            query = query.replace('?', '%s')
            cursor.execute(query, params)
        else:
            cursor.execute(query, params)
        
        lancamento = cursor.fetchone()
        conn.close()
        
        if lancamento:
            st.success(f"✅ Lançamento #{lancamento[0]} encontrado!")
            st.markdown(f"""
            <div class="info-card">
                <h4>📊 Lançamento #{lancamento[0]}</h4>
                <p><strong>📅 Data:</strong> {format_date_br(lancamento[1])}</p>
                <p><strong>🏷️ Categoria:</strong> {lancamento[6]}</p>
                <p><strong>💰 Valor:</strong> {format_currency_br(lancamento[3])}</p>
                <p><strong>📝 Descrição:</strong> {lancamento[2]}</p>
                <p><strong>👤 Usuário:</strong> {lancamento[7]}</p>
                <p><strong>🕐 Criado em:</strong> {lancamento[5]}</p>
                {f'<p><strong>📋 Observações:</strong> {lancamento[4]}</p>' if lancamento[4] else ''}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            show_file_gallery(lancamento[0], user['id'], user['tipo'])
            
        else:
            st.error(f"❌ Lançamento #{lancamento_id} não encontrado!")

def _get_lancamentos_filtrados(categoria_filtro, data_inicio, data_fim):
    """Busca lançamentos com filtros aplicados"""
    conn, db_type = get_db_connection()
    
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
    
    if db_type == 'postgresql':
        query = query.replace('?', '%s')
        df = pd.read_sql_query(query, conn, params=tuple(params))
    else:
        df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    # Ensure 'valor' column is numeric
    if 'valor' in df.columns:
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0.0)

    return df