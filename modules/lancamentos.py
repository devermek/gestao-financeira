import sys
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from config.database import get_connection
from utils.helpers import get_obra_config, get_categorias_ativas, format_currency_br, format_date_br

def show_lancamentos():
    """Exibe página de lançamentos"""
    st.title("💰 Gestão de Lançamentos")
    
    # Tabs para diferentes funcionalidades
    tab1, tab2, tab3 = st.tabs(["➕ Novo Lançamento", "📋 Listar Lançamentos", "🔍 Buscar/Filtrar"])
    
    with tab1:
        _show_novo_lancamento()
    
    with tab2:
        _show_lista_lancamentos()
    
    with tab3:
        _show_filtros_lancamentos()

def _show_novo_lancamento():
    """Formulário para novo lançamento"""
    st.subheader("➕ Registrar Novo Lançamento")
    
    # Verifica se há obra configurada
    obra_config = get_obra_config()
    
    # Debug: mostra informações da obra
    if st.checkbox("🔍 Debug - Mostrar info da obra", value=False):
        st.json(obra_config)
    
    if not obra_config or not obra_config.get('id'):
        st.error("⚠️ Configure uma obra antes de registrar lançamentos!")
        st.info("Vá para **⚙️ Configurações** para configurar uma obra.")
        
        # Botão para ir direto às configurações
        if st.button("🔧 Ir para Configurações", use_container_width=True):
            st.session_state.current_page = "⚙️ Configurações"
            st.rerun()
        return
    
    # Verifica se há categorias
    categorias = get_categorias_ativas()
    if not categorias:
        st.error("⚠️ Cadastre pelo menos uma categoria antes de registrar lançamentos!")
        st.info("Vá para **⚙️ Configurações > Gestão de Categorias** para adicionar categorias.")
        
        # Botão para ir direto às configurações
        if st.button("🏷️ Ir para Categorias", use_container_width=True):
            st.session_state.current_page = "⚙️ Configurações"
            st.rerun()
        return
    
    # Mostra informações da obra atual
    st.info(f"📋 **Obra Ativa:** {obra_config['nome']} | **Orçamento:** {format_currency_br(obra_config['orcamento'])}")
    
    with st.form("novo_lancamento_form", clear_on_submit=True):
        st.markdown("### 📝 Dados do Lançamento")
        
        col1, col2 = st.columns(2)
        
        with col1:
            descricao = st.text_input(
                "Descrição *",
                placeholder="Ex: Compra de cimento para fundação",
                key="descricao_input"
            )
            
            valor = st.number_input(
                "Valor (R$) *",
                min_value=0.01,
                step=0.01,
                format="%.2f",
                key="valor_input"
            )
        
        with col2:
            # Selectbox para categorias
            categoria_options = {f"{cat['nome']}": cat['id'] for cat in categorias}
            categoria_selecionada = st.selectbox(
                "Categoria *",
                options=list(categoria_options.keys()),
                index=0,
                key="categoria_input"
            )
            
            data_lancamento = st.date_input(
                "Data do Lançamento *",
                value=date.today(),
                max_value=date.today(),
                key="data_input"
            )
        
        observacoes = st.text_area(
            "Observações (opcional)",
            placeholder="Informações adicionais sobre o lançamento...",
            key="observacoes_input"
        )
        
        # Upload de arquivos
        st.markdown("### 📎 Comprovantes (opcional)")
        uploaded_files = st.file_uploader(
            "Anexar comprovantes",
            accept_multiple_files=True,
            type=['pdf', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'txt', 'doc', 'docx', 'xls', 'xlsx'],
            help="Tipos permitidos: PDF, imagens, documentos de texto e planilhas. Máximo 30MB por arquivo.",
            key="arquivos_input"
        )
        
        # Preview dos arquivos selecionados
        if uploaded_files:
            st.markdown("**Arquivos selecionados:**")
            for file in uploaded_files:
                valid, message = validate_file_upload(file)
                if valid:
                    st.success(f"✅ {file.name} ({file.size / 1024:.1f} KB)")
                else:
                    st.error(f"❌ {file.name}: {message}")
        
        submitted = st.form_submit_button("💾 Registrar Lançamento", use_container_width=True)
        
        if submitted:
            # Validações
            if not descricao or not descricao.strip():
                st.error("⚠️ A descrição é obrigatória!")
                return
            elif valor <= 0:
                st.error("⚠️ O valor deve ser maior que zero!")
                return
            elif not categoria_selecionada:
                st.error("⚠️ Selecione uma categoria!")
                return
            
            # Valida arquivos se houver
            arquivos_validos = True
            if uploaded_files:
                for file in uploaded_files:
                    valid, message = validate_file_upload(file)
                    if not valid:
                        st.error(f"❌ {file.name}: {message}")
                        arquivos_validos = False
            
            if arquivos_validos:
                categoria_id = categoria_options[categoria_selecionada]
                
                # Debug: mostra dados que serão salvos
                if st.checkbox("�� Debug - Mostrar dados do lançamento", value=False, key="debug_dados"):
                    st.json({
                        "obra_id": obra_config['id'],
                        "categoria_id": categoria_id,
                        "descricao": descricao,
                        "valor": valor,
                        "data_lancamento": str(data_lancamento),
                        "observacoes": observacoes
                    })
                
                with st.spinner("Salvando lançamento..."):
                    lancamento_id = _save_lancamento(
                        obra_config['id'],
                        categoria_id,
                        descricao,
                        valor,
                        data_lancamento,
                        observacoes
                    )
                
                if lancamento_id:
                    # Salva arquivos se houver
                    arquivos_salvos = 0
                    if uploaded_files:
                        for file in uploaded_files:
                            if save_file(lancamento_id, file):
                                arquivos_salvos += 1
                    
                    st.success(f"✅ Lançamento registrado com sucesso! ID: {lancamento_id}")
                    if arquivos_salvos > 0:
                        st.info(f"📎 {arquivos_salvos} arquivo(s) anexado(s) com sucesso!")
                    
                    st.balloons()
                    
                    # Força atualização do cache
                    if 'dashboard_cache' in st.session_state:
                        del st.session_state['dashboard_cache']
                    
                    # Aguarda um pouco antes de recarregar
                    import time
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("❌ Erro ao registrar lançamento! Verifique os logs para mais detalhes.")

def _save_lancamento(obra_id, categoria_id, descricao, valor, data_lancamento, observacoes):
    """Salva novo lançamento com verificação robusta"""
    try:
        print(f"Iniciando salvamento do lançamento: obra_id={obra_id}, categoria_id={categoria_id}, valor={valor}", file=sys.stderr)
        
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        # Verifica se obra existe e está ativa
        if is_postgres:
            cursor.execute("SELECT id, nome FROM obras WHERE id = %s AND ativo = TRUE", (obra_id,))
        else:
            cursor.execute("SELECT id, nome FROM obras WHERE id = ? AND ativo = 1", (obra_id,))
        
        obra = cursor.fetchone()
        if not obra:
            print(f"Erro: Obra {obra_id} não encontrada ou inativa", file=sys.stderr)
            cursor.close()
            conn.close()
            return None
        
        print(f"Obra encontrada: {obra['nome']}", file=sys.stderr)
        
        # Verifica se categoria existe e está ativa
        if is_postgres:
            cursor.execute("SELECT id, nome FROM categorias WHERE id = %s AND ativo = TRUE", (categoria_id,))
        else:
            cursor.execute("SELECT id, nome FROM categorias WHERE id = ? AND ativo = 1", (categoria_id,))
        
        categoria = cursor.fetchone()
        if not categoria:
            print(f"Erro: Categoria {categoria_id} não encontrada ou inativa", file=sys.stderr)
            cursor.close()
            conn.close()
            return None
        
        print(f"Categoria encontrada: {categoria['nome']}", file=sys.stderr)
        
        # Converte data para string se necessário
        if isinstance(data_lancamento, date):
            data_str = data_lancamento.strftime('%Y-%m-%d')
        else:
            data_str = str(data_lancamento)
        
        # Insere o lançamento
        if is_postgres:
            query = """
                INSERT INTO lancamentos (obra_id, categoria_id, descricao, valor, data_lancamento, observacoes, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id
            """
            cursor.execute(query, (obra_id, categoria_id, descricao, valor, data_str, observacoes))
            result = cursor.fetchone()
            lancamento_id = result['id'] if result else None
        else:
            query = """
                INSERT INTO lancamentos (obra_id, categoria_id, descricao, valor, data_lancamento, observacoes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """
            cursor.execute(query, (obra_id, categoria_id, descricao, valor, data_str, observacoes))
            lancamento_id = cursor.lastrowid
        
        if not lancamento_id:
            print("Erro: ID do lançamento não retornado", file=sys.stderr)
            conn.rollback()
            cursor.close()
            conn.close()
            return None
        
        # Confirma a transação
        conn.commit()
        
        # Verifica se foi realmente inserido
        if is_postgres:
            cursor.execute("SELECT COUNT(*) as count FROM lancamentos WHERE id = %s", (lancamento_id,))
        else:
            cursor.execute("SELECT COUNT(*) as count FROM lancamentos WHERE id = ?", (lancamento_id,))
        
        count = cursor.fetchone()['count']
        
        cursor.close()
        conn.close()
        
        if count > 0:
            print(f"Lançamento salvo com sucesso: ID {lancamento_id}", file=sys.stderr)
            return lancamento_id
        else:
            print(f"Erro: Lançamento não foi encontrado após inserção", file=sys.stderr)
            return None
        
    except Exception as e:
        print(f"Erro ao salvar lançamento: {repr(e)}", file=sys.stderr)
        if 'conn' in locals():
            try:
                conn.rollback()
            except:
                pass
        return None
    finally:
        try:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
        except:
            pass

def _show_lista_lancamentos():
    """Lista todos os lançamentos"""
    st.subheader("📋 Lista de Lançamentos")
    
    # Botão para forçar atualização
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Atualizar", use_container_width=True):
            if 'lancamentos_cache' in st.session_state:
                del st.session_state['lancamentos_cache']
            st.rerun()
    
    # Busca lançamentos
    lancamentos = _get_lancamentos()
    
    if not lancamentos:
        st.info("📝 Nenhum lançamento registrado ainda.")
        
        # Botão para ir direto ao formulário
        if st.button("➕ Registrar Primeiro Lançamento", use_container_width=True):
            st.session_state.current_page = "💰 Lançamentos"
            st.rerun()
        return
    
    # Estatísticas rápidas
    total_lancamentos = len(lancamentos)
    total_valor = sum(l['valor'] for l in lancamentos)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Total de Lançamentos", total_lancamentos)
    
    with col2:
        st.metric("💰 Valor Total", format_currency_br(total_valor))
    
    with col3:
        if total_lancamentos > 0:
            media = total_valor / total_lancamentos
            st.metric("📈 Valor Médio", format_currency_br(media))
    
    st.markdown("---")
    
    # Tabela de lançamentos
    for i, lancamento in enumerate(lancamentos):
        with st.expander(f"🧾 {lancamento['descricao']} - {format_currency_br(lancamento['valor'])}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**📅 Data:** {format_date_br(lancamento['data_lancamento'])}")
                st.write(f"**🏷️ Categoria:** {lancamento['categoria_nome']}")
                st.write(f"**�� Valor:** {format_currency_br(lancamento['valor'])}")
            
            with col2:
                if lancamento['observacoes']:
                    st.write(f"**📝 Observações:** {lancamento['observacoes']}")
                
                # Arquivos anexados
                arquivos = _get_arquivos_lancamento(lancamento['id'])
                if arquivos:
                    st.write(f"**📎 Arquivos:** {len(arquivos)} anexo(s)")
                    for arquivo in arquivos:
                        if st.button(f"📄 {arquivo['nome_arquivo']}", key=f"arquivo_{arquivo['id']}"):
                            # Download do arquivo
                            download_file(arquivo['id'])
            
            # Botões de ação
            col_edit, col_delete = st.columns(2)
            
            with col_edit:
                if st.button(f"✏️ Editar", key=f"edit_{lancamento['id']}", use_container_width=True):
                    st.session_state[f'editing_lancamento_{lancamento["id"]}'] = True
                    st.rerun()
            
            with col_delete:
                if st.button(f"🗑️ Excluir", key=f"delete_{lancamento['id']}", use_container_width=True):
                    if _delete_lancamento(lancamento['id']):
                        st.success("✅ Lançamento excluído com sucesso!")
                        # Limpa cache
                        if 'lancamentos_cache' in st.session_state:
                            del st.session_state['lancamentos_cache']
                        if 'dashboard_cache' in st.session_state:
                            del st.session_state['dashboard_cache']
                        st.rerun()
                    else:
                        st.error("❌ Erro ao excluir lançamento!")
            
            # Modal de edição
            if st.session_state.get(f'editing_lancamento_{lancamento["id"]}', False):
                _show_edit_lancamento_modal(lancamento)

def _get_lancamentos():
    """Busca todos os lançamentos com cache"""
    # Verifica cache
    if 'lancamentos_cache' in st.session_state:
        return st.session_state['lancamentos_cache']
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        if is_postgres:
            query = """
                SELECT 
                    l.id, l.descricao, l.valor, l.data_lancamento, l.observacoes, l.created_at,
                    c.nome as categoria_nome, c.cor as categoria_cor,
                    o.nome as obra_nome
                FROM lancamentos l
                JOIN categorias c ON l.categoria_id = c.id
                JOIN obras o ON l.obra_id = o.id
                WHERE o.ativo = TRUE
                ORDER BY l.data_lancamento DESC, l.created_at DESC
            """
        else:
            query = """
                SELECT 
                    l.id, l.descricao, l.valor, l.data_lancamento, l.observacoes, l.created_at,
                    c.nome as categoria_nome, c.cor as categoria_cor,
                    o.nome as obra_nome
                FROM lancamentos l
                JOIN categorias c ON l.categoria_id = c.id
                JOIN obras o ON l.obra_id = o.id
                WHERE o.ativo = 1
                ORDER BY l.data_lancamento DESC, l.created_at DESC
            """
        
        cursor.execute(query)
        
        lancamentos = []
        for row in cursor.fetchall():
            # Converte valor
            valor = 0.0
            try:
                if row['valor'] is not None:
                    from decimal import Decimal
                    if isinstance(row['valor'], Decimal):
                        valor = float(row['valor'])
                    else:
                        valor = float(row['valor'])
            except (TypeError, ValueError):
                valor = 0.0
            
            lancamentos.append({
                'id': row['id'],
                'descricao': row['descricao'],
                'valor': valor,
                'data_lancamento': row['data_lancamento'],
                'observacoes': row['observacoes'],
                'categoria_nome': row['categoria_nome'],
                'categoria_cor': row['categoria_cor'],
                'obra_nome': row['obra_nome'],
                'created_at': row['created_at']
            })
        
        # Salva no cache
        st.session_state['lancamentos_cache'] = lancamentos
        
        print(f"Encontrados {len(lancamentos)} lançamentos", file=sys.stderr)
        return lancamentos
        
    except Exception as e:
        print(f"Erro ao buscar lançamentos: {repr(e)}", file=sys.stderr)
        return []
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def _show_filtros_lancamentos():
    """Filtros e busca de lançamentos"""
    st.subheader("🔍 Buscar e Filtrar Lançamentos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Filtro por período
        st.markdown("### 📅 Filtro por Período")
        data_inicio = st.date_input("Data Início", value=date.today() - timedelta(days=30))
        data_fim = st.date_input("Data Fim", value=date.today())
        
        # Filtro por categoria
        st.markdown("### 🏷️ Filtro por Categoria")
        categorias = get_categorias_ativas()
        categoria_names = ["Todas"] + [cat['nome'] for cat in categorias]
        categoria_filtro = st.selectbox("Categoria", categoria_names)
    
    with col2:
        # Filtro por valor
        st.markdown("### 💰 Filtro por Valor")
        valor_min = st.number_input("Valor Mínimo (R$)", min_value=0.0, value=0.0)
        valor_max = st.number_input("Valor Máximo (R$)", min_value=0.0, value=0.0)
        
        # Busca por texto
        st.markdown("### 🔍 Busca por Texto")
        texto_busca = st.text_input("Buscar na descrição", placeholder="Digite para buscar...")
    
    if st.button("🔍 Aplicar Filtros", use_container_width=True):
        # Busca com filtros
        lancamentos_filtrados = _get_lancamentos_filtrados(
            data_inicio, data_fim, categoria_filtro, valor_min, valor_max, texto_busca
        )
        
        if lancamentos_filtrados:
            st.success(f"✅ Encontrados {len(lancamentos_filtrados)} lançamento(s)")
            
            # Mostra resultados
            for lancamento in lancamentos_filtrados:
                with st.expander(f"🧾 {lancamento['descricao']} - {format_currency_br(lancamento['valor'])}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**�� Data:** {format_date_br(lancamento['data_lancamento'])}")
                        st.write(f"**🏷️ Categoria:** {lancamento['categoria_nome']}")
                    
                    with col2:
                        st.write(f"**�� Valor:** {format_currency_br(lancamento['valor'])}")
                        if lancamento['observacoes']:
                            st.write(f"**📝 Observações:** {lancamento['observacoes']}")
        else:
            st.info("📝 Nenhum lançamento encontrado com os filtros aplicados.")

def _get_lancamentos_filtrados(data_inicio, data_fim, categoria, valor_min, valor_max, texto_busca):
    """Busca lançamentos com filtros"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        # Constrói query dinamicamente
        where_conditions = []
        params = []
        
        if is_postgres:
            base_query = """
                SELECT 
                    l.id, l.descricao, l.valor, l.data_lancamento, l.observacoes,
                    c.nome as categoria_nome, c.cor as categoria_cor
                FROM lancamentos l
                JOIN categorias c ON l.categoria_id = c.id
                JOIN obras o ON l.obra_id = o.id
                WHERE o.ativo = TRUE
            """
            param_placeholder = "%s"
        else:
            base_query = """
                SELECT 
                    l.id, l.descricao, l.valor, l.data_lancamento, l.observacoes,
                    c.nome as categoria_nome, c.cor as categoria_cor
                FROM lancamentos l
                JOIN categorias c ON l.categoria_id = c.id
                JOIN obras o ON l.obra_id = o.id
                WHERE o.ativo = 1
            """
            param_placeholder = "?"
        
        # Filtro por data
        if data_inicio:
            where_conditions.append(f"l.data_lancamento >= {param_placeholder}")
            params.append(data_inicio)
        
        if data_fim:
            where_conditions.append(f"l.data_lancamento <= {param_placeholder}")
            params.append(data_fim)
        
        # Filtro por categoria
        if categoria and categoria != "Todas":
            where_conditions.append(f"c.nome = {param_placeholder}")
            params.append(categoria)
        
        # Filtro por valor
        if valor_min > 0:
            where_conditions.append(f"l.valor >= {param_placeholder}")
            params.append(valor_min)
        
        if valor_max > 0:
            where_conditions.append(f"l.valor <= {param_placeholder}")
            params.append(valor_max)
        
        # Filtro por texto
        if texto_busca:
            if is_postgres:
                where_conditions.append(f"l.descricao ILIKE {param_placeholder}")
                params.append(f"%{texto_busca}%")
            else:
                where_conditions.append(f"l.descricao LIKE {param_placeholder}")
                params.append(f"%{texto_busca}%")
        
        # Monta query final
        if where_conditions:
            query = base_query + " AND " + " AND ".join(where_conditions)
        else:
            query = base_query
        
        query += " ORDER BY l.data_lancamento DESC, l.created_at DESC"
        
        cursor.execute(query, params)
        
        lancamentos = []
        for row in cursor.fetchall():
            # Converte valor
            valor = 0.0
            try:
                if row['valor'] is not None:
                    from decimal import Decimal
                    if isinstance(row['valor'], Decimal):
                        valor = float(row['valor'])
                    else:
                        valor = float(row['valor'])
            except (TypeError, ValueError):
                valor = 0.0
            
            lancamentos.append({
                'id': row['id'],
                'descricao': row['descricao'],
                'valor': valor,
                'data_lancamento': row['data_lancamento'],
                'observacoes': row['observacoes'],
                'categoria_nome': row['categoria_nome'],
                'categoria_cor': row['categoria_cor']
            })
        
        return lancamentos
        
    except Exception as e:
        print(f"Erro ao buscar lançamentos filtrados: {repr(e)}", file=sys.stderr)
        return []
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def _delete_lancamento(lancamento_id):
    """Exclui lançamento"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        # Primeiro exclui arquivos relacionados
        if is_postgres:
            cursor.execute("DELETE FROM arquivos WHERE lancamento_id = %s", (lancamento_id,))
        else:
            cursor.execute("DELETE FROM arquivos WHERE lancamento_id = ?", (lancamento_id,))
        
        # Depois exclui o lançamento
        if is_postgres:
            query = "DELETE FROM lancamentos WHERE id = %s"
        else:
            query = "DELETE FROM lancamentos WHERE id = ?"
        
        cursor.execute(query, (lancamento_id,))
        conn.commit()
        
        rows_affected = cursor.rowcount
        cursor.close()
        conn.close()
        
        print(f"Lançamento {lancamento_id} excluído. Linhas afetadas: {rows_affected}", file=sys.stderr)
        return rows_affected > 0
        
    except Exception as e:
        print(f"Erro ao excluir lançamento: {repr(e)}", file=sys.stderr)
        if 'conn' in locals():
            try:
                conn.rollback()
            except:
                pass
        return False
    finally:
        try:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
        except:
            pass

def _show_edit_lancamento_modal(lancamento):
    """Modal para editar lançamento"""
    st.markdown("---")
    st.subheader(f"✏️ Editando: {lancamento['descricao']}")
    
    categorias = get_categorias_ativas()
    categoria_options = {cat['nome']: cat['id'] for cat in categorias}
    
    with st.form(f"edit_lancamento_{lancamento['id']}"):
        col1, col2 = st.columns(2)
        
        with col1:
            nova_descricao = st.text_input("Descrição", value=lancamento['descricao'])
            novo_valor = st.number_input("Valor (R$)", value=lancamento['valor'], min_value=0.01, step=0.01)
        
        with col2:
            # Encontra categoria atual
            categoria_atual = lancamento['categoria_nome']
            categoria_index = list(categoria_options.keys()).index(categoria_atual) if categoria_atual in categoria_options else 0
            
            nova_categoria = st.selectbox("Categoria", list(categoria_options.keys()), index=categoria_index)
            
            # Converte data
            if isinstance(lancamento['data_lancamento'], str):
                data_atual = datetime.strptime(lancamento['data_lancamento'], '%Y-%m-%d').date()
            else:
                data_atual = lancamento['data_lancamento']
            
            nova_data = st.date_input("Data", value=data_atual)
        
        novas_observacoes = st.text_area("Observações", value=lancamento['observacoes'] or "")
        
        col_save, col_cancel = st.columns(2)
        
        with col_save:
            if st.form_submit_button("💾 Salvar Alterações", use_container_width=True):
                if _update_lancamento(
                    lancamento['id'], nova_descricao, novo_valor, 
                    categoria_options[nova_categoria], nova_data, novas_observacoes
                ):
                    st.success("✅ Lançamento atualizado com sucesso!")
                    del st.session_state[f'editing_lancamento_{lancamento["id"]}']
                    # Limpa cache
                    if 'lancamentos_cache' in st.session_state:
                        del st.session_state['lancamentos_cache']
                    if 'dashboard_cache' in st.session_state:
                        del st.session_state['dashboard_cache']
                    st.rerun()
                else:
                    st.error("❌ Erro ao atualizar lançamento!")
        
        with col_cancel:
            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                del st.session_state[f'editing_lancamento_{lancamento["id"]}']
                st.rerun()

def _update_lancamento(lancamento_id, descricao, valor, categoria_id, data_lancamento, observacoes):
    """Atualiza lançamento"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        # Converte data para string se necessário
        if isinstance(data_lancamento, date):
            data_str = data_lancamento.strftime('%Y-%m-%d')
        else:
            data_str = str(data_lancamento)
        
        if is_postgres:
            query = """
                UPDATE lancamentos 
                SET descricao = %s, valor = %s, categoria_id = %s, 
                    data_lancamento = %s, observacoes = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
        else:
            query = """
                UPDATE lancamentos 
                SET descricao = ?, valor = ?, categoria_id = ?, 
                    data_lancamento = ?, observacoes = ?, updated_at = datetime('now')
                WHERE id = ?
            """
        
        cursor.execute(query, (descricao, valor, categoria_id, data_str, observacoes, lancamento_id))
        conn.commit()
        
        rows_affected = cursor.rowcount
        cursor.close()
        conn.close()
        
        print(f"Lançamento {lancamento_id} atualizado. Linhas afetadas: {rows_affected}", file=sys.stderr)
        return rows_affected > 0
        
    except Exception as e:
        print(f"Erro ao atualizar lançamento: {repr(e)}", file=sys.stderr)
        if 'conn' in locals():
            try:
                conn.rollback()
            except:
                pass
        return False
    finally:
        try:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
        except:
            pass

def _get_arquivos_lancamento(lancamento_id):
    """Busca arquivos de um lançamento"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        if is_postgres:
            query = """
                SELECT id, nome_arquivo, tipo_arquivo, tamanho_arquivo
                FROM arquivos 
                WHERE lancamento_id = %s
                ORDER BY created_at
            """
        else:
            query = """
                SELECT id, nome_arquivo, tipo_arquivo, tamanho_arquivo
                FROM arquivos 
                WHERE lancamento_id = ?
                ORDER BY created_at
            """
        
        cursor.execute(query, (lancamento_id,))
        
        arquivos = []
        for row in cursor.fetchall():
            arquivos.append({
                'id': row['id'],
                'nome_arquivo': row['nome_arquivo'],
                'tipo_arquivo': row['tipo_arquivo'],
                'tamanho_arquivo': row['tamanho_arquivo']
            })
        
        return arquivos
        
    except Exception as e:
        print(f"Erro ao buscar arquivos: {repr(e)}", file=sys.stderr)
        return []
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def validate_file_upload(file):
    """Valida arquivo para upload"""
    # Tamanho máximo: 30MB
    max_size = 30 * 1024 * 1024  # 30MB em bytes
    
    if file.size > max_size:
        return False, f"Arquivo muito grande. Máximo: 30MB. Atual: {file.size / 1024 / 1024:.1f}MB"
    
    # Tipos permitidos
    allowed_types = [
        'application/pdf',
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp',
        'text/plain',
        'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ]
    
    if file.type not in allowed_types:
        return False, f"Tipo de arquivo não permitido: {file.type}"
    
    return True, "Arquivo válido"

def save_file(lancamento_id, file):
    """Salva arquivo no banco de dados"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        # Lê conteúdo do arquivo
        file_content = file.read()
        
        if is_postgres:
            query = """
                INSERT INTO arquivos (lancamento_id, nome_arquivo, tipo_arquivo, tamanho_arquivo, conteudo_arquivo, created_at)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """
        else:
            query = """
                INSERT INTO arquivos (lancamento_id, nome_arquivo, tipo_arquivo, tamanho_arquivo, conteudo_arquivo, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """
        
        cursor.execute(query, (lancamento_id, file.name, file.type, file.size, file_content))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print(f"Arquivo {file.name} salvo para lançamento {lancamento_id}", file=sys.stderr)
        return True
        
    except Exception as e:
        print(f"Erro ao salvar arquivo: {repr(e)}", file=sys.stderr)
        if 'conn' in locals():
            try:
                conn.rollback()
            except:
                pass
        return False
    finally:
        try:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
        except:
            pass

def download_file(arquivo_id):
    """Download de arquivo"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        if is_postgres:
            query = """
                SELECT nome_arquivo, tipo_arquivo, conteudo_arquivo
                FROM arquivos 
                WHERE id = %s
            """
        else:
            query = """
                SELECT nome_arquivo, tipo_arquivo, conteudo_arquivo
                FROM arquivos 
                WHERE id = ?
            """
        
        cursor.execute(query, (arquivo_id,))
        result = cursor.fetchone()
        
        if result:
            st.download_button(
                label=f"⬇️ Baixar {result['nome_arquivo']}",
                data=result['conteudo_arquivo'],
                file_name=result['nome_arquivo'],
                mime=result['tipo_arquivo']
            )
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erro ao fazer download: {repr(e)}", file=sys.stderr)
        st.error("❌ Erro ao baixar arquivo!")
    finally:
        try:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
        except:
            pass