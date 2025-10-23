import streamlit as st
import base64
import io
from PIL import Image
from config.database import get_db_connection
from datetime import datetime

class FileManager:
    """Classe para gerenciar upload e download de arquivos"""
    
    ALLOWED_EXTENSIONS = {
        'images': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'],
        'documents': ['pdf', 'doc', 'docx', 'txt'],
        'spreadsheets': ['xls', 'xlsx', 'csv']
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def is_allowed_file(filename):
        """Verifica se o arquivo é permitido"""
        if not filename:
            return False, "Nome de arquivo inválido"
        
        extension = filename.lower().split('.')[-1]
        all_extensions = []
        for ext_list in FileManager.ALLOWED_EXTENSIONS.values():
            all_extensions.extend(ext_list)
        
        if extension not in all_extensions:
            return False, f"Extensão .{extension} não permitida"
        
        return True, "OK"
    
    @staticmethod
    def get_file_type(filename):
        """Retorna o tipo do arquivo"""
        extension = filename.lower().split('.')[-1]
        
        for file_type, extensions in FileManager.ALLOWED_EXTENSIONS.items():
            if extension in extensions:
                return file_type
        
        return 'unknown'
    
    @staticmethod
    def save_file(file_data, filename, lancamento_id, user_id):
        """Salva arquivo no banco de dados"""
        try:
            # Verificar se arquivo é permitido
            is_allowed, message = FileManager.is_allowed_file(filename)
            if not is_allowed:
                return False, message
            
            # Verificar tamanho
            if len(file_data) > FileManager.MAX_FILE_SIZE:
                return False, f"Arquivo muito grande. Máximo: {FileManager.MAX_FILE_SIZE // (1024*1024)}MB"
            
            conn, db_type = get_db_connection() # Obter a conexão e o tipo de DB
            cursor = conn.cursor()
            
            tipo_arquivo_categoria = FileManager.get_file_type(filename) # 'images', 'documents', 'spreadsheets'
            
            # Inserir no banco com compatibilidade de DB
            if db_type == 'postgresql':
                cursor.execute("""
                    INSERT INTO arquivos (lancamento_id, nome, tipo, tamanho, conteudo, usuario_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (lancamento_id, filename, tipo_arquivo_categoria, len(file_data), file_data, user_id))
            else: # SQLite
                cursor.execute("""
                    INSERT INTO arquivos (lancamento_id, nome, tipo, tamanho, conteudo, usuario_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (lancamento_id, filename, tipo_arquivo_categoria, len(file_data), file_data, user_id))
            
            arquivo_id = cursor.lastrowid # lastrowid funciona para SQLite e psycopg2 (se usar RETURNING id)
            conn.commit()
            conn.close()
            
            return True, f"Arquivo '{filename}' salvo com sucesso!"
            
        except Exception as e:
            return False, f"Erro ao salvar arquivo: {str(e)}"
    
    @staticmethod
    def get_files_by_lancamento(lancamento_id):
        """Busca arquivos de um lançamento"""
        try:
            conn, db_type = get_db_connection() # Obter a conexão e o tipo de DB
            cursor = conn.cursor()
            
            # Buscar arquivos com compatibilidade de DB
            if db_type == 'postgresql':
                cursor.execute("""
                    SELECT a.id, a.nome, a.tipo, a.tamanho, a.created_at, u.nome as usuario
                    FROM arquivos a
                    LEFT JOIN usuarios u ON a.usuario_id = u.id
                    WHERE a.lancamento_id = %s
                    ORDER BY a.created_at DESC
                """, (lancamento_id,))
            else: # SQLite
                cursor.execute("""
                    SELECT a.id, a.nome, a.tipo, a.tamanho, a.created_at, u.nome as usuario
                    FROM arquivos a
                    LEFT JOIN usuarios u ON a.usuario_id = u.id
                    WHERE a.lancamento_id = ?
                    ORDER BY a.created_at DESC
                """, (lancamento_id,))
            
            files = cursor.fetchall()
            conn.close()
            
            return files
            
        except Exception as e:
            st.error(f"Erro ao buscar arquivos: {e}")
            return []
    
    @staticmethod
    def get_file_content(arquivo_id):
        """Busca conteúdo de um arquivo"""
        try:
            conn, db_type = get_db_connection() # Obter a conexão e o tipo de DB
            cursor = conn.cursor()
            
            # Buscar conteúdo com compatibilidade de DB
            if db_type == 'postgresql':
                cursor.execute("""
                    SELECT nome, tipo, conteudo
                    FROM arquivos
                    WHERE id = %s
                """, (arquivo_id,))
            else: # SQLite
                cursor.execute("""
                    SELECT nome, tipo, conteudo
                    FROM arquivos
                    WHERE id = ?
                """, (arquivo_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0], result[1], result[2]  # nome, tipo, conteudo
            
            return None, None, None
            
        except Exception as e:
            st.error(f"Erro ao buscar arquivo: {e}")
            return None, None, None
    
    @staticmethod
    def delete_file(arquivo_id, user_id):
        """Deleta um arquivo"""
        try:
            conn, db_type = get_db_connection() # Obter a conexão e o tipo de DB
            cursor = conn.cursor()
            
            # Verificar se o arquivo existe (para obter o nome para a mensagem de sucesso)
            if db_type == 'postgresql':
                cursor.execute("SELECT nome FROM arquivos WHERE id = %s", (arquivo_id,))
            else: # SQLite
                cursor.execute("SELECT nome FROM arquivos WHERE id = ?", (arquivo_id,))
            
            arquivo = cursor.fetchone()
            
            if not arquivo:
                return False, "Arquivo não encontrado"
            
            # Deletar arquivo com compatibilidade de DB
            if db_type == 'postgresql':
                cursor.execute("DELETE FROM arquivos WHERE id = %s", (arquivo_id,))
            else: # SQLite
                cursor.execute("DELETE FROM arquivos WHERE id = ?", (arquivo_id,))
            
            conn.commit()
            conn.close()
            
            return True, f"Arquivo '{arquivo[0]}' deletado com sucesso!"
            
        except Exception as e:
            return False, f"Erro ao deletar arquivo: {str(e)}"

def show_file_uploader(lancamento_id, user_id):
    """Componente de upload de arquivos"""
    st.markdown("### 📎 Anexar Comprovantes")
    
    # Upload de múltiplos arquivos
    uploaded_files = st.file_uploader(
        "Escolha os arquivos (fotos, PDFs, documentos)",
        type=['jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx'],
        accept_multiple_files=True,
        help="Formatos aceitos: Imagens (JPG, PNG, GIF), Documentos (PDF, DOC, DOCX, TXT), Planilhas (XLS, XLSX)"
    )
    
    if uploaded_files:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"📁 {len(uploaded_files)} arquivo(s) selecionado(s)")
        
        with col2:
            if st.button("💾 Salvar Arquivos", type="primary"):
                success_count = 0
                error_count = 0
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"Salvando: {uploaded_file.name}")
                    
                    # Ler conteúdo do arquivo
                    file_data = uploaded_file.read()
                    
                    # Salvar no banco
                    success, message = FileManager.save_file(
                        file_data, uploaded_file.name, lancamento_id, user_id
                    )
                    
                    if success:
                        success_count += 1
                    else:
                        error_count += 1
                        st.error(f"❌ {uploaded_file.name}: {message}")
                    
                    # Atualizar progresso
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                status_text.empty()
                progress_bar.empty()
                
                if success_count > 0:
                    st.success(f"✅ {success_count} arquivo(s) salvo(s) com sucesso!")
                
                if error_count > 0:
                    st.warning(f"⚠️ {error_count} arquivo(s) com erro")
                
                if success_count > 0:
                    st.rerun()

def show_file_gallery(lancamento_id, user_id, user_tipo):
    """Galeria de arquivos anexados"""
    files = FileManager.get_files_by_lancamento(lancamento_id)
    
    if not files:
        st.info("📁 Nenhum arquivo anexado ainda")
        return
    
    st.markdown("### 📁 Arquivos Anexados")
    
    # Organizar por tipo
    images = [f for f in files if f[2] == 'images'] # f[2] é 'tipo'
    documents = [f for f in files if f[2] in ['documents', 'spreadsheets']] # f[2] é 'tipo'
    
    # Mostrar imagens
    if images:
        st.markdown("#### 🖼️ Imagens")
        
        # Criar grid de imagens
        cols = st.columns(3)
        for i, img_file in enumerate(images):
            with cols[i % 3]:
                try:
                    # Buscar conteúdo da imagem
                    nome, tipo, conteudo = FileManager.get_file_content(img_file[0])
                    
                    if conteudo:
                        # Exibir imagem
                        image = Image.open(io.BytesIO(conteudo))
                        st.image(image, caption=nome, use_container_width=True)
                        
                        # Botões de ação
                        col_download, col_delete = st.columns(2)
                        
                        with col_download:
                            st.download_button(
                                "📥 Baixar",
                                data=conteudo,
                                file_name=nome,
                                mime=f"image/{nome.split('.')[-1]}",
                                key=f"download_img_{img_file[0]}"
                            )
                        
                        with col_delete:
                            if user_tipo == 'gestor':
                                if st.button("��️ Deletar", key=f"delete_img_{img_file[0]}"):
                                    success, message = FileManager.delete_file(img_file[0], user_id)
                                    if success:
                                        st.success(message)
                                        st.rerun()
                                    else:
                                        st.error(message)
                        
                        # Info do arquivo
                        st.caption(f"📅 {img_file[4]} | 👤 {img_file[5]} | �� {img_file[3]} bytes")
                
                except Exception as e:
                    st.error(f"Erro ao exibir imagem: {e}")
    
    # Mostrar documentos
    if documents:
        st.markdown("#### 📄 Documentos")
        
        for doc_file in documents:
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                # Emoji baseado no tipo
                if doc_file[2] == 'documents': # doc_file[2] é 'tipo'
                    if doc_file[1].endswith('.pdf'):
                        emoji = "📕"
                    else:
                        emoji = "📄"
                else:  # spreadsheets
                    emoji = "📊"
                
                st.write(f"{emoji} **{doc_file[1]}**")
                st.caption(f"📅 {doc_file[4]} | �� {doc_file[5]} | 📏 {doc_file[3]} bytes")
            
            with col2:
                # Buscar conteúdo para download
                nome, tipo, conteudo = FileManager.get_file_content(doc_file[0])
                
                if conteudo:
                    # Determinar MIME type
                    if nome.endswith('.pdf'):
                        mime_type = 'application/pdf'
                    elif nome.endswith(('.doc', '.docx')):
                        mime_type = 'application/msword'
                    elif nome.endswith(('.xls', '.xlsx')):
                        mime_type = 'application/vnd.ms-excel'
                    else:
                        mime_type = 'application/octet-stream'
                    
                    st.download_button(
                        "�� Baixar",
                        data=conteudo,
                        file_name=nome,
                        mime=mime_type,
                        key=f"download_doc_{doc_file[0]}"
                    )
            
            with col3:
                if user_tipo == 'gestor':
                    if st.button("🗑️ Deletar", key=f"delete_doc_{doc_file[0]}"):
                        success, message = FileManager.delete_file(doc_file[0], user_id)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
