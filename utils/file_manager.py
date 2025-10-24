import streamlit as st
import base64
import io
from PIL import Image
from config.database import get_db_connection
from datetime import datetime
import sys # For sys.stderr

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
            is_allowed, message = FileManager.is_allowed_file(filename)
            if not is_allowed:
                return False, message
            
            if len(file_data) > FileManager.MAX_FILE_SIZE:
                return False, f"Arquivo muito grande. Máximo: {FileManager.MAX_FILE_SIZE // (1024*1024)}MB"
            
            conn, db_type = get_db_connection() # Get db_type
            cursor = conn.cursor()
            
            tipo_arquivo_categoria = FileManager.get_file_type(filename)
            
            query = """
                INSERT INTO arquivos (lancamento_id, nome, tipo, tamanho, conteudo, usuario_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (lancamento_id, filename, tipo_arquivo_categoria, len(file_data), file_data, user_id)
            
            if db_type == 'postgresql':
                query = query.replace('?', '%s')
                cursor.execute(query, params)
            else:
                cursor.execute(query, params)
            
            arquivo_id = cursor.lastrowid # This will only work reliably for SQLite if using INTEGER PRIMARY KEY AUTOINCREMENT
                                         # For PostgreSQL, use RETURNING id if needed, but not strictly needed here for just saving
            conn.commit()
            conn.close()
            
            return True, f"Arquivo '{filename}' salvo com sucesso!"
            
        except Exception as e:
            print(f"Erro ao salvar arquivo: {e}", file=sys.stderr); sys.stderr.flush()
            return False, f"Erro ao salvar arquivo: {str(e)}"
    
    @staticmethod
    def get_files_by_lancamento(lancamento_id):
        """Busca arquivos de um lançamento"""
        try:
            conn, db_type = get_db_connection() # Get db_type
            cursor = conn.cursor()
            
            query = """
                SELECT a.id, a.nome, a.tipo, a.tamanho, a.created_at, u.nome as usuario
                FROM arquivos a
                LEFT JOIN usuarios u ON a.usuario_id = u.id
                WHERE a.lancamento_id = ?
                ORDER BY a.created_at DESC
            """
            params = (lancamento_id,)
            if db_type == 'postgresql':
                query = query.replace('?', '%s')
                cursor.execute(query, params)
            else:
                cursor.execute(query, params)
            
            files = cursor.fetchall()
            conn.close()
            
            return files
            
        except Exception as e:
            st.error(f"Erro ao buscar arquivos: {e}")
            print(f"Erro ao buscar arquivos: {e}", file=sys.stderr); sys.stderr.flush()
            return []
    
    @staticmethod
    def get_file_content(arquivo_id):
        """Busca conteúdo de um arquivo"""
        try:
            conn, db_type = get_db_connection() # Get db_type
            cursor = conn.cursor()
            
            query = """
                SELECT nome, tipo, conteudo
                FROM arquivos
                WHERE id = ?
            """
            params = (arquivo_id,)
            if db_type == 'postgresql':
                query = query.replace('?', '%s')
                cursor.execute(query, params)
            else:
                cursor.execute(query, params)
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0], result[1], result[2]
            
            return None, None, None
            
        except Exception as e:
            st.error(f"Erro ao buscar arquivo: {e}")
            print(f"Erro ao buscar arquivo: {e}", file=sys.stderr); sys.stderr.flush()
            return None, None, None
    
    @staticmethod
    def delete_file(arquivo_id, user_id):
        """Deleta um arquivo"""
        try:
            conn, db_type = get_db_connection() # Get db_type
            cursor = conn.cursor()
            
            query_select = "SELECT nome FROM arquivos WHERE id = ?"
            params_select = (arquivo_id,)
            if db_type == 'postgresql':
                query_select = query_select.replace('?', '%s')
                cursor.execute(query_select, params_select)
            else:
                cursor.execute(query_select, params_select)
            
            arquivo = cursor.fetchone()
            
            if not arquivo:
                conn.close()
                return False, "Arquivo não encontrado"
            
            query_delete = "DELETE FROM arquivos WHERE id = ?"
            params_delete = (arquivo_id,)
            if db_type == 'postgresql':
                query_delete = query_delete.replace('?', '%s')
                cursor.execute(query_delete, params_delete)
            else:
                cursor.execute(query_delete, params_delete)

            conn.commit()
            conn.close()
            
            return True, f"Arquivo '{arquivo[0]}' deletado com sucesso!"
            
        except Exception as e:
            print(f"Erro ao deletar arquivo: {e}", file=sys.stderr); sys.stderr.flush()
            return False, f"Erro ao deletar arquivo: {str(e)}"

def show_file_uploader(lancamento_id, user_id):
    """Componente de upload de arquivos"""
    st.markdown("### 📎 Anexar Comprovantes")
    
    uploaded_files = st.file_uploader(
        "Escolha os arquivos (fotos, PDFs, documentos)",
        type=['jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx'],
        accept_multiple_files=True,
        key="file_uploader_main", # Added key
        help="Formatos aceitos: Imagens (JPG, PNG, GIF), Documentos (PDF, DOC, DOCX, TXT), Planilhas (XLS, XLSX)"
    )
    
    if uploaded_files:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"�� {len(uploaded_files)} arquivo(s) selecionado(s)")
        with col2:
            if st.button("💾 Salvar Arquivos", type="primary", key="save_uploaded_files"): # Added key
                success_count = 0
                error_count = 0
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"Salvando: {uploaded_file.name}")
                    file_data = uploaded_file.read()
                    success, message = FileManager.save_file(
                        file_data, uploaded_file.name, lancamento_id, user_id
                    )
                    if success:
                        success_count += 1
                    else:
                        error_count += 1
                        st.error(f"❌ {uploaded_file.name}: {message}")
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                status_text.empty()
                progress_bar.empty()
                
                if success_count > 0: st.success(f"✅ {success_count} arquivo(s) salvo(s) com sucesso!")
                if error_count > 0: st.warning(f"⚠️ {error_count} arquivo(s) com erro")
                if success_count > 0: st.rerun()

def show_file_gallery(lancamento_id, user_id, user_tipo):
    """Galeria de arquivos anexados"""
    files = FileManager.get_files_by_lancamento(lancamento_id)
    
    if not files:
        st.info("📁 Nenhum arquivo anexado ainda")
        return
    
    st.markdown("### �� Arquivos Anexados")
    imagens = [f for f in files if f[2] == 'images']
    documentos = [f for f in files if f[2] in ['documents', 'spreadsheets']]
    
    if imagens:
        st.markdown("#### 🖼️ Imagens")
        cols = st.columns(3)
        for i, img_file in enumerate(imagens):
            with cols[i % 3]:
                try:
                    nome, tipo, conteudo = FileManager.get_file_content(img_file[0])
                    if conteudo:
                        image = Image.open(io.BytesIO(conteudo))
                        st.image(image, caption=nome, use_container_width=True)
                        col_download, col_delete = st.columns(2)
                        with col_download:
                            st.download_button(
                                "📥 Baixar", data=conteudo, file_name=nome, mime=f"image/{nome.split('.')[-1]}",
                                key=f"download_img_{img_file[0]}_{i}" # Unique key
                            )
                        with col_delete:
                            if user_tipo == 'gestor':
                                if st.button("🗑️ Deletar", key=f"delete_img_{img_file[0]}_{i}"): # Unique key
                                    success, message = FileManager.delete_file(img_file[0], user_id)
                                    if success: st.success(message); st.rerun()
                                    else: st.error(message)
                except Exception as e:
                    st.error(f"Erro ao exibir imagem: {e}")
                    print(f"Erro ao exibir imagem: {e}", file=sys.stderr); sys.stderr.flush()
    
    if documentos:
        st.markdown("#### 📄 Documentos")
        for idx_doc, doc_file in enumerate(documentos):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                emoji = ""
                if doc_file[2] == 'documents':
                    if doc_file[1].endswith('.pdf'): emoji = "��"
                    else: emoji = "📄"
                else: emoji = "📊"
                st.write(f"{emoji} **{doc_file[1]}**")
                st.caption(f"📅 {format_date_br(doc_file[4])} | 👤 {doc_file[5]} | 📏 {doc_file[3]} bytes")
            with col2:
                nome, tipo, conteudo = FileManager.get_file_content(doc_file[0])
                if conteudo:
                    mime_type = 'application/octet-stream'
                    if nome.endswith('.pdf'): mime_type = 'application/pdf'
                    elif nome.endswith(('.doc', '.docx')): mime_type = 'application/msword'
                    elif nome.endswith(('.xls', '.xlsx')): mime_type = 'application/vnd.ms-excel'
                    st.download_button(
                        "�� Baixar", data=conteudo, file_name=nome, mime=mime_type,
                        key=f"download_doc_{doc_file[0]}_{idx_doc}" # Unique key
                    )
            with col3:
                if user_tipo == 'gestor':
                    if st.button("��️ Deletar", key=f"delete_doc_{doc_file[0]}_{idx_doc}"): # Unique key
                        success, message = FileManager.delete_file(doc_file[0], user_id)
                        if success: st.success(message); st.rerun()
                        else: st.error(message)