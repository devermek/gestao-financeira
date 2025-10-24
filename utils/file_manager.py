import sys
import streamlit as st
from PIL import Image
import io
import base64
from config.database import get_connection

def save_file(lancamento_id, uploaded_file):
    """Salva arquivo anexado a um lançamento"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Lê o conteúdo do arquivo
        file_content = uploaded_file.read()
        file_name = uploaded_file.name
        file_type = uploaded_file.type
        file_size = len(file_content)
        
        # Detecta tipo de banco para usar placeholder correto
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        if is_postgres:
            query = """
                INSERT INTO arquivos (lancamento_id, nome_arquivo, tipo_arquivo, tamanho_arquivo, conteudo_arquivo)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """
        else:
            query = """
                INSERT INTO arquivos (lancamento_id, nome_arquivo, tipo_arquivo, tamanho_arquivo, conteudo_arquivo)
                VALUES (?, ?, ?, ?, ?)
            """
        
        cursor.execute(query, (lancamento_id, file_name, file_type, file_size, file_content))
        
        if is_postgres:
            arquivo_id = cursor.fetchone()[0]
        else:
            arquivo_id = cursor.lastrowid
        
        conn.commit()
        
        print(f"Arquivo salvo com sucesso: {file_name} (ID: {arquivo_id})", file=sys.stderr)
        return arquivo_id
        
    except Exception as e:
        print(f"Erro ao salvar arquivo: {repr(e)}", file=sys.stderr)
        conn.rollback()
        return None
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def get_file_content(arquivo_id):
    """Recupera conteúdo de um arquivo"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT nome_arquivo, tipo_arquivo, conteudo_arquivo
            FROM arquivos
            WHERE id = %s
        """.replace('%s', '?' if not os.getenv('DATABASE_URL') else '%s'), (arquivo_id,))
        
        result = cursor.fetchone()
        
        if result:
            return {
                'nome': result['nome_arquivo'],
                'tipo': result['tipo_arquivo'],
                'conteudo': result['conteudo_arquivo']
            }
        
        return None
        
    except Exception as e:
        print(f"Erro ao recuperar arquivo: {repr(e)}", file=sys.stderr)
        return None
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def delete_file(arquivo_id):
    """Deleta um arquivo"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        query = "DELETE FROM arquivos WHERE id = %s" if is_postgres else "DELETE FROM arquivos WHERE id = ?"
        cursor.execute(query, (arquivo_id,))
        
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"Arquivo deletado com sucesso (ID: {arquivo_id})", file=sys.stderr)
            return True
        else:
            print(f"Arquivo não encontrado (ID: {arquivo_id})", file=sys.stderr)
            return False
            
    except Exception as e:
        print(f"Erro ao deletar arquivo: {repr(e)}", file=sys.stderr)
        conn.rollback()
        return False
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def get_files_by_lancamento(lancamento_id):
    """Busca todos os arquivos de um lançamento"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        query = """
            SELECT id, nome_arquivo, tipo_arquivo, tamanho_arquivo, created_at
            FROM arquivos
            WHERE lancamento_id = %s
            ORDER BY created_at DESC
        """ if is_postgres else """
            SELECT id, nome_arquivo, tipo_arquivo, tamanho_arquivo, created_at
            FROM arquivos
            WHERE lancamento_id = ?
            ORDER BY created_at DESC
        """
        
        cursor.execute(query, (lancamento_id,))
        
        arquivos = []
        for row in cursor.fetchall():
            arquivos.append({
                'id': row['id'],
                'nome': row['nome_arquivo'],
                'tipo': row['tipo_arquivo'],
                'tamanho': row['tamanho_arquivo'],
                'data_upload': row['created_at']
            })
        
        return arquivos
        
    except Exception as e:
        print(f"Erro ao buscar arquivos do lançamento: {repr(e)}", file=sys.stderr)
        return []
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def format_file_size(size_bytes):
    """Formata tamanho do arquivo em formato legível"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def show_file_gallery(lancamento_id):
    """Exibe galeria de arquivos de um lançamento"""
    arquivos = get_files_by_lancamento(lancamento_id)
    
    if not arquivos:
        st.info("📎 Nenhum arquivo anexado a este lançamento.")
        return
    
    st.subheader("📎 Arquivos Anexados")
    
    for arquivo in arquivos:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                st.write(f"**{arquivo['nome']}**")
            
            with col2:
                st.write(f"Tipo: {arquivo['tipo']}")
            
            with col3:
                st.write(f"Tamanho: {format_file_size(arquivo['tamanho'])}")
            
            with col4:
                if st.button("🗑️", key=f"delete_{arquivo['id']}", help="Deletar arquivo"):
                    if delete_file(arquivo['id']):
                        st.success("Arquivo deletado!")
                        st.rerun()
                    else:
                        st.error("Erro ao deletar arquivo!")
            
            # Botão para visualizar/baixar
            col_view, col_download = st.columns(2)
            
            with col_view:
                if st.button("👁️ Visualizar", key=f"view_{arquivo['id']}"):
                    show_file_preview(arquivo['id'])
            
            with col_download:
                file_data = get_file_content(arquivo['id'])
                if file_data:
                    st.download_button(
                        label="⬇️ Baixar",
                        data=file_data['conteudo'],
                        file_name=file_data['nome'],
                        mime=file_data['tipo'],
                        key=f"download_{arquivo['id']}"
                    )
            
            st.divider()

def show_file_preview(arquivo_id):
    """Exibe preview de um arquivo"""
    file_data = get_file_content(arquivo_id)
    
    if not file_data:
        st.error("Arquivo não encontrado!")
        return
    
    file_type = file_data['tipo']
    file_content = file_data['conteudo']
    file_name = file_data['nome']
    
    st.subheader(f"📄 Preview: {file_name}")
    
    try:
        # Imagens
        if file_type.startswith('image/'):
            image = Image.open(io.BytesIO(file_content))
            st.image(image, caption=file_name, use_column_width=True)
        
        # PDFs
        elif file_type == 'application/pdf':
            # Encode para base64 para exibir no iframe
            base64_pdf = base64.b64encode(file_content).decode('utf-8')
            pdf_display = f"""
                <iframe 
                    src="data:application/pdf;base64,{base64_pdf}" 
                    width="100%" 
                    height="600px" 
                    type="application/pdf">
                </iframe>
            """
            st.markdown(pdf_display, unsafe_allow_html=True)
        
        # Arquivos de texto
        elif file_type.startswith('text/'):
            try:
                text_content = file_content.decode('utf-8')
                st.text_area("Conteúdo do arquivo:", text_content, height=400, disabled=True)
            except UnicodeDecodeError:
                st.warning("Não foi possível decodificar o arquivo de texto.")
        
        # Outros tipos
        else:
            st.info(f"Preview não disponível para arquivos do tipo: {file_type}")
            st.write(f"**Nome:** {file_name}")
            st.write(f"**Tipo:** {file_type}")
            st.write(f"**Tamanho:** {format_file_size(len(file_content))}")
    
    except Exception as e:
        st.error(f"Erro ao exibir preview: {str(e)}")
        print(f"Erro no preview do arquivo {arquivo_id}: {repr(e)}", file=sys.stderr)

def validate_file_upload(uploaded_file, max_size_mb=30):
    """Valida arquivo antes do upload"""
    if not uploaded_file:
        return False, "Nenhum arquivo selecionado."
    
    # Verifica tamanho
    file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return False, f"Arquivo muito grande. Máximo permitido: {max_size_mb}MB"
    
    # Tipos permitidos
    allowed_types = [
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp',
        'application/pdf',
        'text/plain', 'text/csv',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ]
    
    if uploaded_file.type not in allowed_types:
        return False, f"Tipo de arquivo não permitido: {uploaded_file.type}"
    
    return True, "Arquivo válido."