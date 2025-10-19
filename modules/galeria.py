import streamlit as st
import base64
from config.database import get_db_connection
from utils.file_manager import FileManager # Assumindo que você tem um FileManager

def show_galeria(user):
    st.header("🖼️ Galeria de Comprovantes")
    st.markdown("Visualize todos os comprovantes de lançamentos aqui. Apenas arquivos de imagem podem ser visualizados diretamente na página. Outros documentos são listados para download.")
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Obter todos os arquivos de todos os lançamentos
        # ou apenas os arquivos do usuário logado se ele não for gestor
        if user['tipo'] == 'gestor':
            query = """
                SELECT a.id, a.nome, a.tipo, a.tamanho, a.lancamento_id, l.descricao as lancamento_descricao
                FROM arquivos a
                JOIN lancamentos l ON a.lancamento_id = l.id
                ORDER BY a.created_at DESC
            """
            cursor.execute(query)
        else:
            query = """
                SELECT a.id, a.nome, a.tipo, a.tamanho, a.lancamento_id, l.descricao as lancamento_descricao
                FROM arquivos a
                JOIN lancamentos l ON a.lancamento_id = l.id
                WHERE a.usuario_id = ?
                ORDER BY a.created_at DESC
            """
            cursor.execute(query, (user['id'],))

        arquivos = cursor.fetchall() # Usar fetchall() pois o conn.row_factory retorna linhas como dicionários/mapas

        if not arquivos:
            st.info("Nenhum comprovante encontrado na galeria.")
            return

        st.subheader("Imagens")
        # Filtra por tipo MIME que começa com 'image/'
        imagens = [arq for arq in arquivos if arq['tipo'].startswith('image/')] 
        if imagens:
            # Grid para imagens (3 colunas)
            cols = st.columns(3)
            for i, img_meta in enumerate(imagens):
                with cols[i % 3]:
                    try:
                        # Recupera o conteúdo do arquivo usando FileManager
                        nome, mime_type, conteudo_blob = FileManager.get_file_content(img_meta['id'])
                        if conteudo_blob:
                            # Encode para base64 para incorporar diretamente na tag HTML <img>
                            img_base64 = base64.b64encode(conteudo_blob).decode('utf-8')
                            st.image(f"data:{mime_type};base64,{img_base64}", caption=f"{nome} (Lançamento #{img_meta['lancamento_id']})", use_container_width=True)
                            st.caption(f"Descrição Lançamento: {img_meta['lancamento_descricao']}")
                            
                            # Botão de Download
                            st.download_button(
                                label="📥 Baixar",
                                data=conteudo_blob,
                                file_name=nome,
                                mime=mime_type,
                                key=f"download_galeria_img_{img_meta['id']}"
                            )
                            # Botão de Excluir (apenas para gestor)
                            if user['tipo'] == 'gestor':
                                if st.button("🗑️ Excluir", key=f"delete_galeria_img_{img_meta['id']}", type="secondary"):
                                    success, message = FileManager.delete_file(img_meta['id'], user['id'])
                                    if success:
                                        st.success(message)
                                        st.rerun() # Recarrega a página para atualizar a lista
                                    else:
                                        st.error(message)
                        else:
                            st.warning(f"Não foi possível carregar o conteúdo da imagem: {img_meta['nome']}")
                    except Exception as e:
                        st.error(f"Erro ao exibir imagem {img_meta['nome']}: {e}")
                        # import traceback
                        # st.code(traceback.format_exc())
        else:
            st.info("Nenhuma imagem encontrada.")

        st.subheader("Outros Documentos (PDFs, Word, Excel, etc.)")
        # Filtra por tipos que NÃO são imagem
        documentos = [arq for arq in arquivos if not arq['tipo'].startswith('image/')]
        if documentos:
            for doc_meta in documentos:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    # Ícone baseado no tipo MIME
                    emoji = "📎"
                    if 'pdf' in doc_meta['tipo']: emoji = "📄"
                    elif 'wordprocessingml' in doc_meta['tipo'] or 'msword' in doc_meta['tipo']: emoji = "📝" # .doc, .docx
                    elif 'spreadsheetml' in doc_meta['tipo'] or 'excel' in doc_meta['tipo'] or 'csv' in doc_meta['tipo']: emoji = "📊" # .xls, .xlsx, .csv
                    st.write(f"{emoji} **{doc_meta['nome']}** (Lançamento #{doc_meta['lancamento_id']})")
                    st.caption(f"Descrição Lançamento: {doc_meta['lancamento_descricao']}")
                    
                with col2:
                    # Botão de Download
                    nome, mime_type, conteudo_blob = FileManager.get_file_content(doc_meta['id'])
                    if conteudo_blob:
                        st.download_button(
                            label="📥 Baixar",
                            data=conteudo_blob,
                            file_name=nome,
                            mime=mime_type,
                            key=f"download_galeria_doc_{doc_meta['id']}"
                        )
                    else:
                        st.warning("Conteúdo não disponível.")
                with col3:
                    # Botão de Excluir (apenas para gestor)
                    if user['tipo'] == 'gestor':
                        if st.button("��️ Excluir", key=f"delete_galeria_doc_{doc_meta['id']}", type="secondary"):
                            success, message = FileManager.delete_file(doc_meta['id'], user['id'])
                            if success:
                                st.success(message)
                                st.rerun() # Recarrega a página para atualizar a lista
                            else:
                                st.error(message)
        else:
            st.info("Nenhum outro documento encontrado.")

    except Exception as e:
        st.error(f"❌ Erro ao carregar galeria: {e}")
        st.error(f"Detalhes do erro: {e}") # Para debug
        # import traceback
        # st.code(traceback.format_exc()) # Descomente para debug completo
    finally:
        if conn:
            conn.close()
