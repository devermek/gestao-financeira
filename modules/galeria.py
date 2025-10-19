import streamlit as st
import pandas as pd
from datetime import date, datetime
from PIL import Image
import io
from config.database import get_db_connection
from utils.file_manager import FileManager
from utils.helpers import format_date_br

def show_galeria(user):
    """Exibe galeria de fotos do progresso da obra"""
    st.header("📸 Galeria de Progresso da Obra")
    
    # Tabs para organizar
    tab1, tab2, tab3 = st.tabs(["📷 Adicionar Fotos", "🖼️ Galeria", "📊 Timeline"])
    
    with tab1:
        _show_upload_progresso(user)
    
    with tab2:
        _show_galeria_fotos()
    
    with tab3:
        _show_timeline_progresso()

def _show_upload_progresso(user):
    """Upload de fotos de progresso"""
    st.subheader("📷 Adicionar Fotos do Progresso")
    
    with st.form("upload_progresso"):
        col1, col2 = st.columns(2)
        
        with col1:
            data_foto = st.date_input("📅 Data da Foto", value=date.today())
            etapa = st.selectbox(
                "🏗️ Etapa da Obra",
                [
                    "Preparação do Terreno",
                    "Fundação",
                    "Estrutura",
                    "Alvenaria",
                    "Cobertura",
                    "Instalações Elétricas",
                    "Instalações Hidráulicas",
                    "Revestimentos",
                    "Pintura",
                    "Acabamentos",
                    "Paisagismo",
                    "Entrega"
                ]
            )
        
        with col2:
            descricao = st.text_input(
                "📝 Descrição",
                placeholder="Ex: Concretagem da laje do térreo"
            )
            observacoes = st.text_area(
                "📋 Observações",
                placeholder="Detalhes sobre o progresso, problemas encontrados, etc."
            )
        
        # Upload de fotos
        fotos = st.file_uploader(
            "📸 Selecione as Fotos",
            type=['jpg', 'jpeg', 'png'],
            accept_multiple_files=True,
            help="Formatos aceitos: JPG, PNG (máximo 10MB por foto)"
        )
        
        # Preview das fotos
        if fotos:
            st.markdown("#### 👀 Preview das Fotos:")
            cols = st.columns(min(len(fotos), 4))
            
            for i, foto in enumerate(fotos):
                with cols[i % 4]:
                    try:
                        image = Image.open(foto)
                        st.image(image, caption=foto.name, use_container_width=True)  # CORRIGIDO
                        foto.seek(0)  # Reset file pointer
                    except Exception as e:
                        st.error(f"Erro ao carregar {foto.name}: {e}")
        
        # Botão de salvar
        submitted = st.form_submit_button(
            "💾 Salvar Progresso + Fotos",
            type="primary",
            use_container_width=True
        )
        
        if submitted:
            if not etapa or not descricao:
                st.error("❌ Preencha etapa e descrição!")
                return
            
            if not fotos:
                st.error("❌ Selecione pelo menos uma foto!")
                return
            
            # Salvar registro de progresso
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Criar tabela se não existir
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS progresso_obra (
                        id INTEGER PRIMARY KEY,
                        data_foto DATE,
                        etapa TEXT,
                        descricao TEXT,
                        observacoes TEXT,
                        usuario_id INTEGER,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Inserir registro
                cursor.execute("""
                    INSERT INTO progresso_obra (data_foto, etapa, descricao, observacoes, usuario_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (data_foto, etapa, descricao, observacoes, user['id']))
                
                progresso_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                # Salvar fotos
                fotos_salvas = 0
                fotos_erro = 0
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, foto in enumerate(fotos):
                    status_text.text(f"Salvando foto: {foto.name}")
                    
                    # Ler conteúdo da foto
                    foto_data = foto.read()
                    
                    # Salvar usando FileManager (vinculado ao progresso)
                    success, message = FileManager.save_file(
                        foto_data, foto.name, progresso_id, user['id']
                    )
                    
                    if success:
                        fotos_salvas += 1
                    else:
                        fotos_erro += 1
                        st.error(f"❌ {foto.name}: {message}")
                    
                    # Atualizar progresso
                    progress_bar.progress((i + 1) / len(fotos))
                
                progress_bar.empty()
                status_text.empty()
                
                # Mensagem de sucesso
                if fotos_salvas > 0:
                    st.success(f"✅ Progresso #{progresso_id} salvo com {fotos_salvas} foto(s)!")
                
                if fotos_erro > 0:
                    st.warning(f"⚠️ {fotos_erro} foto(s) com erro")
                
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Erro ao salvar progresso: {str(e)}")

def _show_galeria_fotos():
    """Exibe galeria de fotos organizadas"""
    st.subheader("🖼️ Galeria de Fotos")
    
    # Verificar se tabela existe
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='progresso_obra'
    """)
    
    if not cursor.fetchone():
        conn.close()
        st.info("📸 Ainda não há fotos de progresso. Adicione algumas na aba 'Adicionar Fotos'.")
        return
    
    # Buscar registros de progresso
    df_progresso = pd.read_sql_query("""
        SELECT 
            p.id,
            p.data_foto,
            p.etapa,
            p.descricao,
            p.observacoes,
            u.nome as usuario,
            p.created_at
        FROM progresso_obra p
        LEFT JOIN usuarios u ON p.usuario_id = u.id
        ORDER BY p.data_foto DESC, p.created_at DESC
    """, conn)
    conn.close()
    
    if df_progresso.empty:
        st.info("📸 Ainda não há registros de progresso.")
        return
    
    # Filtros
    col1, col2 = st.columns(2)
    
    with col1:
        etapas_disponiveis = df_progresso['etapa'].unique().tolist()
        etapa_filtro = st.selectbox(
            "🏗️ Filtrar por Etapa",
            options=["Todas"] + etapas_disponiveis
        )
    
    with col2:
        ordenacao = st.selectbox(
            "📅 Ordenação",
            options=["Mais Recentes", "Mais Antigas", "Por Etapa"]
        )
    
    # Aplicar filtros
    df_filtrado = df_progresso.copy()
    
    if etapa_filtro != "Todas":
        df_filtrado = df_filtrado[df_filtrado['etapa'] == etapa_filtro]
    
    if ordenacao == "Mais Antigas":
        df_filtrado = df_filtrado.sort_values(['data_foto', 'created_at'])
    elif ordenacao == "Por Etapa":
        df_filtrado = df_filtrado.sort_values(['etapa', 'data_foto'])
    
    # Exibir registros
    for _, registro in df_filtrado.iterrows():
        with st.container():
            # Cabeçalho do registro
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.markdown(f"### 🏗️ {registro['etapa']}")
                st.write(f"**📝 {registro['descricao']}**")
            
            with col2:
                st.write(f"**📅 Data:** {format_date_br(registro['data_foto'])}")
                st.write(f"**👤 Usuário:** {registro['usuario']}")
            
            with col3:
                st.write(f"**🆔 ID:** {registro['id']}")
            
            # Observações se houver
            if registro['observacoes']:
                st.write(f"**�� Observações:** {registro['observacoes']}")
            
            # Buscar e exibir fotos
            fotos = FileManager.get_files_by_lancamento(registro['id'])
            fotos_imagem = [f for f in fotos if f[2] == 'images']
            
            if fotos_imagem:
                # Exibir fotos em grid
                cols = st.columns(min(len(fotos_imagem), 4))
                
                for i, foto in enumerate(fotos_imagem):
                    with cols[i % 4]:
                        try:
                            nome, tipo, conteudo = FileManager.get_file_content(foto[0])
                            
                            if conteudo:
                                image = Image.open(io.BytesIO(conteudo))
                                st.image(image, caption=nome, use_container_width=True)  # CORRIGIDO
                                
                                # Botão de download
                                st.download_button(
                                    "📥 Baixar",
                                    data=conteudo,
                                    file_name=nome,
                                    mime=f"image/{nome.split('.')[-1]}",
                                    key=f"download_prog_{foto[0]}"
                                )
                        
                        except Exception as e:
                            st.error(f"Erro ao carregar foto: {e}")
            else:
                st.info("📷 Nenhuma foto encontrada para este registro")
            
            st.markdown("---")

def _show_timeline_progresso():
    """Exibe timeline do progresso"""
    st.subheader("📊 Timeline do Progresso")
    
    # Verificar se tabela existe
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='progresso_obra'
    """)
    
    if not cursor.fetchone():
        conn.close()
        st.info("📊 Ainda não há dados de progresso para timeline.")
        return
    
    # Buscar dados para timeline
    df_timeline = pd.read_sql_query("""
        SELECT 
            data_foto,
            etapa,
            COUNT(*) as quantidade_fotos,
            GROUP_CONCAT(descricao, ' | ') as descricoes
        FROM progresso_obra
        GROUP BY data_foto, etapa
        ORDER BY data_foto
    """, conn)
    conn.close()
    
    if df_timeline.empty:
        st.info("📊 Ainda não há dados para timeline.")
        return
    
    # Estatísticas gerais
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_registros = len(df_timeline)
        st.metric("📝 Total de Registros", total_registros)
    
    with col2:
        etapas_concluidas = df_timeline['etapa'].nunique()
        st.metric("🏗️ Etapas Registradas", etapas_concluidas)
    
    with col3:
        total_fotos = df_timeline['quantidade_fotos'].sum()
        st.metric("📸 Total de Fotos", total_fotos)
    
    # Timeline visual
    st.markdown("### 📅 Timeline do Progresso")
    
    for _, item in df_timeline.iterrows():
        col1, col2 = st.columns([1, 4])
        
        with col1:
            st.write(f"**�� {format_date_br(item['data_foto'])}**")
        
        with col2:
            st.write(f"🏗️ **{item['etapa']}**")
            st.write(f"�� {item['quantidade_fotos']} foto(s)")
            
            # Mostrar descrições (limitadas)
            descricoes = item['descricoes'][:100] + "..." if len(item['descricoes']) > 100 else item['descricoes']
            st.caption(f"📝 {descricoes}")
        
        st.markdown("---")