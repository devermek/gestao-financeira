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
    tab1, tab2, tab3 = st.tabs(["➕ Novo Lançamento", "📜 Histórico", "🔍 Detalhes"])
    
    with tab1:
        _show_novo_lancamento(user)
    
    with tab2:
        _show_historico_lancamentos(user)
    
    with tab3:
        _show_detalhes_lancamento(user)

def _show_novo_lancamento(user):
    """Formulário para novo lançamento"""
    st.subheader("➕ Adicionar Novo Lançamento")
    
    # O CSS customizado para os campos e botões agora é carregado globalmente via app.py e utils/styles.py
    # O bloco st.markdown com o CSS inline foi REMOVIDO daqui.
    
    # Obtenção e FILTRAGEM das categorias
    categorias_raw = get_categorias_ativas()
    
    # Garante que apenas categorias com nome (não vazio) e ID válido (não None) sejam consideradas
    categorias = [cat for cat in categorias_raw if cat and cat.get('nome') and cat.get('id') is not None]

    if not categorias:
        st.error("❌ **Nenhuma categoria ativa encontrada!** Para adicionar um lançamento, você precisa primeiro criar categorias.")
        st.info("Por favor, vá para a página de **⚙️ Configurações** e adicione novas categorias.")
        return # Retorna para não renderizar o formulário vazio
    
    categoria_opcoes = {cat['nome']: cat['id'] for cat in categorias}
    
    # Adicionalmente, verifica se o dicionário resultante não está vazio.
    if not categoria_opcoes:
        st.error("❌ Nenhuma categoria válida foi processada para seleção. Verifique as categorias ativas e suas propriedades (nome, ID).")
        return
        
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
            # default_index será 0, pois já verificamos que categoria_opcoes não está vazia
            categoria_selecionada = st.selectbox(
                "🏷️ Categoria do Gasto", 
                options=list(categoria_opcoes.keys()),
                index=0, 
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
                "�� Descrição do Gasto", 
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
            "📁 Comprovantes (Opcional)",
            type=['jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx'],
            accept_multiple_files=True
        )
        
        # Botão de salvar
        submitted = st.form_submit_button(
            "�� Salvar Lançamento",
            type="primary",
            use_container_width=True
        )
        
        # PROCESSAMENTO DO FORMULÁRIO
        if submitted:
            # Validação
            erros = []
            categoria_id = None 
            
            if not categoria_selecionada:
                erros.append("⚠️ Selecione uma categoria")
            else:
                # Com a filtragem de categorias, o ID deve ser válido aqui
                categoria_id = categoria_opcoes.get(categoria_selecionada)
                if categoria_id is None:
                    erros.append(f"⚠️ A categoria '{categoria_selecionada}' foi selecionada, mas seu ID não pôde ser recuperado. (Verifique o banco de dados e a função 'get_categorias_ativas').")

            if not valor or valor <= 0:
                erros.append("💰 Digite um valor maior que R$ 0,00")
            
            if not descricao or not descricao.strip():
                erros.append("📝 Digite uma descrição")
            
            if erros:
                st.error("❌ **Corrija os seguintes campos:**")
                for erro in erros:
                    st.error(f"   • {erro}")
                return
            
            # Tentar salvar
            try:
                conn, db_type = get_db_connection() # Obter a conexão e o tipo de DB
                cursor = conn.cursor()
                
                # Preparar dados para inserção
                # Para INSERT, o DEFAULT CURRENT_TIMESTAMP nas colunas created_at e updated_at já funciona.
                dados_insercao = (data, categoria_id, descricao, valor, observacoes, user['id'])
                
                # Executar INSERT
                # Usando %s para PostgreSQL e ? para SQLite. A get_db_connection já cuida da conexão
                # apropriada para o DB.
                if db_type == 'postgresql':
                    cursor.execute("""
                        INSERT INTO lancamentos (data, categoria_id, descricao, valor, observacoes, usuario_id)
                        VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                    """, dados_insercao)
                    lancamento_id = cursor.fetchone()[0]
                else: # SQLite
                    cursor.execute("""
                        INSERT INTO lancamentos (data, categoria_id, descricao, valor, observacoes, usuario_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, dados_insercao)
                    lancamento_id = cursor.lastrowid
                
                # Commit
                conn.commit()
                
                # Fechar conexão
                conn.close()
                
                st.success(f"�� **Lançamento #{lancamento_id} salvo com sucesso!**")
                
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
                        st.success(f"�� {arquivos_salvos} arquivo(s) anexado(s)!")
                
                st.balloons()
                
                # Aguardar um pouco e recarregar
                time.sleep(2)
                st.rerun() # Recarrega a página para limpar o formulário e atualizar o histórico
                
            except Exception as e:
                st.error(f"❌ **Erro ao salvar lançamento:** {str(e)}")
                    
def _show_historico_lancamentos(user):
    """Exibe histórico de lançamentos com visualização melhorada de comprovantes"""
    st.subheader("📜 Histórico de Lançamentos")
    
    # Filtros em linha
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        categorias_raw = get_categorias_ativas()
        # Filtrar categorias para o histórico também, para evitar problemas na lista de opções
        categorias_filtradas = [cat for cat in categorias_raw if cat and cat.get('nome') and cat.get('id') is not None]
        categoria_filtro = st.selectbox(
            "🏷️ Categoria", 
            options=["Todas"] + [cat['nome'] for cat in categorias_filtradas],
            index=0
        )
    
    with col2:
        data_inicio = st.date_input("🗓️ Data Início", value=None)
    
    with col3:
        data_fim = st.date_input("📅 Data Fim", value=None)
    
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("�� Atualizar"):
            st.rerun()
    
    # Buscar lançamentos
    lancamentos = _get_lancamentos_filtrados(categoria_filtro, data_inicio, data_fim)
    
    if lancamentos.empty:
        st.info("ℹ️ Nenhum lançamento encontrado com os filtros aplicados")
        return
    
    # Resumo
    col_resumo1, col_resumo2 = st.columns(2)
    with col_resumo1:
        st.metric("📊 Total de Lançamentos", len(lancamentos))
    with col_resumo2:
        st.metric("💰 Valor Total", format_currency_br(lancamentos['valor'].sum()))
    
    st.markdown("---")
    
    # NOVA VISUALIZAÇÃO: Cards com comprovantes
    st.markdown("### 📄 Lançamentos com Comprovantes")
    
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
                st.markdown(f"**💰 {format_currency_br(lancamento['valor'])}**")
                st.caption(f"👤 {lancamento['usuario']}")
            
            with col_header4:
                if tem_arquivos:
                    st.markdown(f"**📎 {len(arquivos)} arquivo(s)**")
                    # Ícones dos tipos de arquivo
                    tipos_arquivo = set([arq[2] for arq in arquivos])
                    icons = []
                    if 'images' in tipos_arquivo:
                        icons.append("��️")
                    if 'documents' in tipos_arquivo:
                        icons.append("📄")
                    if 'spreadsheets' in tipos_arquivo:
                        icons.append("📊")
                    st.markdown(" ".join(icons))
                else:
                    st.markdown("🔗 Sem anexos")
            
            # SEÇÃO DE COMPROVANTES (expansível)
            if tem_arquivos:
                with st.expander(f"📁 Ver {len(arquivos)} Comprovante(s) - Lançamento #{lancamento['id']}", expanded=False):
                    _show_comprovantes_inline(lancamento['id'], user['id'], user['tipo'])

def _show_comprovantes_inline(lancamento_id, user_id, user_tipo):
    """Mostra comprovantes inline no histórico"""
    arquivos = FileManager.get_files_by_lancamento(lancamento_id)
    
    if not arquivos:
        st.info("🚫 Nenhum arquivo encontrado")
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
        st.markdown("#### 📄 Documentos")
        
        for doc in documentos:
            col_doc1, col_doc2, col_doc3 = st.columns([3, 1, 1])
            
            with col_doc1:
                # Ícone baseado no tipo
                if doc[1].lower().endswith('.pdf'):
                    emoji = "📄"
                elif doc[1].lower().endswith(('.doc', '.docx')):
                    emoji = "📃"
                elif doc[1].lower().endswith(('.xls', '.xlsx', '.csv')):
                    emoji = "��"
                else:
                    emoji = "📁"
                
                st.write(f"{emoji} **{doc[1]}**")
                st.caption(f"👤 {doc[5]} | 📏 {doc[3]} bytes") # Alterado para usar doc[5] (usuario)
            
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
        conn, db_type = get_db_connection() # Obter a conexão e o tipo de DB
        cursor = conn.cursor()
        
        # Ajustar query para PostgreSQL
        if db_type == 'postgresql':
            cursor.execute("""
                SELECT l.id, l.data, l.descricao, l.valor, l.observacoes, l.created_at,
                       c.nome as categoria, u.nome as usuario
                FROM lancamentos l
                LEFT JOIN categorias c ON l.categoria_id = c.id
                LEFT JOIN usuarios u ON l.usuario_id = u.id
                WHERE l.id = %s
            """, (lancamento_id,))
        else: # SQLite
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
                <p><strong>��️ Data:</strong> {format_date_br(lancamento[1])}</p>
                <p><strong>��️ Categoria:</strong> {lancamento[6]}</p>
                <p><strong>💰 Valor:</strong> {format_currency_br(lancamento[3])}</p>
                <p><strong>📝 Descrição:</strong> {lancamento[2]}</p>
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
    conn, db_type = get_db_connection() # Obter a conexão e o tipo de DB
    
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
        query += " AND c.nome = ?" if db_type == 'sqlite' else " AND c.nome = %s"
        params.append(categoria_filtro)
    
    if data_inicio:
        query += " AND l.data >= ?" if db_type == 'sqlite' else " AND l.data >= %s"
        params.append(data_inicio)
    
    if data_fim:
        query += " AND l.data <= ?" if db_type == 'sqlite' else " AND l.data <= %s"
        params.append(data_fim)
    
    query += " ORDER BY l.data DESC, l.id DESC"
    
    # pandas.read_sql_query aceita params como lista, mas psycopg2 prefere tupla para %s
    # Fazemos a conversão condicional
    if db_type == 'postgresql':
        df = pd.read_sql_query(query, conn, params=tuple(params))
    else: # sqlite
        df = pd.read_sql_query(query, conn, params=params)
    
    conn.close()
    
    return df
