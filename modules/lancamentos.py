import sys
import streamlit as st
from datetime import date, datetime
import pandas as pd
from config.database import get_connection
from utils.helpers import get_categorias_ativas, get_obra_config, format_currency_br, format_date_br
from utils.file_manager import save_file, show_file_gallery, validate_file_upload

def show_lancamentos():
    """Exibe página de lançamentos"""
    st.title("💰 Gestão de Lançamentos")
    
    # Tabs para diferentes funcionalidades
    tab1, tab2, tab3 = st.tabs(["➕ Novo Lançamento", "📋 Histórico", "🔍 Detalhes"])
    
    with tab1:
        _show_novo_lancamento()
    
    with tab2:
        _show_historico_lancamentos()
    
    with tab3:
        _show_detalhes_lancamento()

def _show_novo_lancamento():
    """Formulário para novo lançamento"""
    st.subheader("➕ Registrar Novo Lançamento")
    
    # Verifica se há obra configurada
    obra_config = get_obra_config()
    if not obra_config.get('id'):
        st.error("⚠️ Configure uma obra antes de registrar lançamentos!")
        st.info("Vá para **Configurações > Configuração da Obra** para configurar.")
        return
    
    # Verifica se há categorias
    categorias = get_categorias_ativas()
    if not categorias:
        st.error("⚠️ Cadastre pelo menos uma categoria antes de registrar lançamentos!")
        st.info("Vá para **Configurações > Gestão de Categorias** para adicionar categorias.")
        return
    
    with st.form("novo_lancamento_form"):
        st.markdown("### 📝 Dados do Lançamento")
        
        col1, col2 = st.columns(2)
        
        with col1:
            descricao = st.text_input(
                "Descrição *",
                placeholder="Ex: Compra de cimento para fundação"
            )
            
            valor = st.number_input(
                "Valor (R$) *",
                min_value=0.01,
                step=0.01,
                format="%.2f"
            )
        
        with col2:
            # Selectbox para categorias
            categoria_options = {f"{cat['nome']}": cat['id'] for cat in categorias}
            categoria_selecionada = st.selectbox(
                "Categoria *",
                options=list(categoria_options.keys()),
                index=0
            )
            
            data_lancamento = st.date_input(
                "Data do Lançamento *",
                value=date.today(),
                max_value=date.today()
            )
        
        observacoes = st.text_area(
            "Observações (opcional)",
            placeholder="Informações adicionais sobre o lançamento..."
        )
        
        # Upload de arquivos
        st.markdown("### 📎 Comprovantes (opcional)")
        uploaded_files = st.file_uploader(
            "Anexar comprovantes",
            accept_multiple_files=True,
            type=['pdf', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'txt', 'doc', 'docx', 'xls', 'xlsx'],
            help="Tipos permitidos: PDF, imagens, documentos de texto e planilhas. Máximo 30MB por arquivo."
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
            if not descricao.strip():
                st.error("⚠️ A descrição é obrigatória!")
            elif valor <= 0:
                st.error("⚠️ O valor deve ser maior que zero!")
            elif not categoria_selecionada:
                st.error("⚠️ Selecione uma categoria!")
            else:
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
                        
                        # Limpa o formulário
                        st.rerun()
                    else:
                        st.error("❌ Erro ao registrar lançamento!")

def _show_historico_lancamentos():
    """Exibe histórico de lançamentos com filtros"""
    st.subheader("📋 Histórico de Lançamentos")
    
    # Filtros
    with st.expander("🔍 Filtros", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtro por período
            data_inicio = st.date_input("Data Início", value=None)
            data_fim = st.date_input("Data Fim", value=None)
        
        with col2:
            # Filtro por categoria
            categorias = get_categorias_ativas()
            categoria_options = {"Todas": None}
            categoria_options.update({cat['nome']: cat['id'] for cat in categorias})
            
            categoria_filtro = st.selectbox("Categoria", options=list(categoria_options.keys()))
        
        with col3:
            # Filtro por valor
            valor_min = st.number_input("Valor Mínimo (R$)", min_value=0.0, value=0.0)
            valor_max = st.number_input("Valor Máximo (R$)", min_value=0.0, value=0.0)
    
    # Busca lançamentos
    lancamentos = _get_lancamentos_filtrados(
        data_inicio, data_fim, 
        categoria_options[categoria_filtro],
        valor_min if valor_min > 0 else None,
        valor_max if valor_max > 0 else None
    )
    
    if not lancamentos:
        st.info("Nenhum lançamento encontrado com os filtros aplicados.")
        return
    
    # Estatísticas do filtro
    total_filtrado = sum(l['valor'] for l in lancamentos)
    st.metric("💰 Total Filtrado", format_currency_br(total_filtrado))
    
    st.markdown(f"**{len(lancamentos)} lançamento(s) encontrado(s)**")
    
    # Lista de lançamentos
    for lancamento in lancamentos:
        with st.expander(
            f"💰 {format_currency_br(lancamento['valor'])} - {lancamento['descricao']} "
            f"({format_date_br(lancamento['data_lancamento'])})",
            expanded=False
        ):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**ID:** {lancamento['id']}")
                st.write(f"**Descrição:** {lancamento['descricao']}")
                st.write(f"**Valor:** {format_currency_br(lancamento['valor'])}")
                st.write(f"**Data:** {format_date_br(lancamento['data_lancamento'])}")
            
            with col2:
                st.write(f"**Categoria:** {lancamento['categoria_nome']}")
                if lancamento['observacoes']:
                    st.write(f"**Observações:** {lancamento['observacoes']}")
                st.write(f"**Criado em:** {format_date_br(lancamento['created_at'])}")
            
            # Exibe arquivos anexados
            show_file_gallery(lancamento['id'])
            
            # Botões de ação
            col_edit, col_delete = st.columns(2)
            
            with col_edit:
                if st.button("✏️ Editar", key=f"edit_{lancamento['id']}", use_container_width=True):
                    st.session_state[f"editing_lancamento_{lancamento['id']}"] = True
                    st.rerun()
            
            with col_delete:
                if st.button("🗑️ Excluir", key=f"delete_{lancamento['id']}", use_container_width=True):
                    if _delete_lancamento(lancamento['id']):
                        st.success("Lançamento excluído com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao excluir lançamento!")

def _show_detalhes_lancamento():
    """Busca e exibe detalhes de um lançamento específico"""
    st.subheader("🔍 Buscar Lançamento")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        lancamento_id = st.number_input("ID do Lançamento", min_value=1, step=1)
    
    with col2:
        if st.button("🔍 Buscar", use_container_width=True):
            lancamento = _get_lancamento_by_id(lancamento_id)
            
            if lancamento:
                st.session_state['lancamento_detalhes'] = lancamento
            else:
                st.error("Lançamento não encontrado!")
    
    # Exibe detalhes se encontrado
    if 'lancamento_detalhes' in st.session_state:
        lancamento = st.session_state['lancamento_detalhes']
        
        st.markdown("---")
        st.markdown("### 📄 Detalhes do Lançamento")
        
        # Card com informações
        with st.container():
            st.markdown(f"""
            <div class="card-container">
                <h4>💰 {format_currency_br(lancamento['valor'])}</h4>
                <p><strong>Descrição:</strong> {lancamento['descricao']}</p>
                <p><strong>Categoria:</strong> {lancamento['categoria_nome']}</p>
                <p><strong>Data:</strong> {format_date_br(lancamento['data_lancamento'])}</p>
                {f"<p><strong>Observações:</strong> {lancamento['observacoes']}</p>" if lancamento['observacoes'] else ""}
                <p><strong>Criado em:</strong> {format_date_br(lancamento['created_at'])}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Arquivos anexados
        show_file_gallery(lancamento['id'])

def _save_lancamento(obra_id, categoria_id, descricao, valor, data_lancamento, observacoes):
    """Salva novo lançamento"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        if is_postgres:
            query = """
                INSERT INTO lancamentos (obra_id, categoria_id, descricao, valor, data_lancamento, observacoes)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """
        else:
            query = """
                INSERT INTO lancamentos (obra_id, categoria_id, descricao, valor, data_lancamento, observacoes)
                VALUES (?, ?, ?, ?, ?, ?)
            """
        
        cursor.execute(query, (obra_id, categoria_id, descricao, valor, data_lancamento, observacoes))
        
        if is_postgres:
            lancamento_id = cursor.fetchone()[0]
        else:
            lancamento_id = cursor.lastrowid
        
        conn.commit()
        
        print(f"Lançamento salvo com sucesso: ID {lancamento_id}", file=sys.stderr)
        return lancamento_id
        
    except Exception as e:
        print(f"Erro ao salvar lançamento: {repr(e)}", file=sys.stderr)
        conn.rollback()
        return None
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def _get_lancamentos_filtrados(data_inicio=None, data_fim=None, categoria_id=None, valor_min=None, valor_max=None):
    """Busca lançamentos com filtros aplicados"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        # Monta query base
        query = """
            SELECT 
                l.id, l.descricao, l.valor, l.data_lancamento, l.observacoes, l.created_at,
                c.nome as categoria_nome, c.cor as categoria_cor
            FROM lancamentos l
            JOIN categorias c ON l.categoria_id = c.id
            JOIN obras o ON l.obra_id = o.id
            WHERE o.ativo = %s
        """ if is_postgres else """
            SELECT 
                l.id, l.descricao, l.valor, l.data_lancamento, l.observacoes, l.created_at,
                c.nome as categoria_nome, c.cor as categoria_cor
            FROM lancamentos l
            JOIN categorias c ON l.categoria_id = c.id
            JOIN obras o ON l.obra_id = o.id
            WHERE o.ativo = ?
        """
        
        params = [True if is_postgres else 1]
        
        # Adiciona filtros
        if data_inicio:
            query += f" AND l.data_lancamento >= {'%s' if is_postgres else '?'}"
            params.append(data_inicio)
        
        if data_fim:
            query += f" AND l.data_lancamento <= {'%s' if is_postgres else '?'}"
            params.append(data_fim)
        
        if categoria_id:
            query += f" AND l.categoria_id = {'%s' if is_postgres else '?'}"
            params.append(categoria_id)
        
        if valor_min:
            query += f" AND l.valor >= {'%s' if is_postgres else '?'}"
            params.append(valor_min)
        
        if valor_max:
            query += f" AND l.valor <= {'%s' if is_postgres else '?'}"
            params.append(valor_max)
        
        query += " ORDER BY l.data_lancamento DESC, l.id DESC"
        
        cursor.execute(query, params)
        
        lancamentos = []
        for row in cursor.fetchall():
            # Converte valor para float
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
                'created_at': row['created_at'],
                'categoria_nome': row['categoria_nome'],
                'categoria_cor': row['categoria_cor']
            })
        
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

def _get_lancamento_by_id(lancamento_id):
    """Busca lançamento por ID"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        query = """
            SELECT 
                l.id, l.descricao, l.valor, l.data_lancamento, l.observacoes, l.created_at,
                c.nome as categoria_nome, c.cor as categoria_cor
            FROM lancamentos l
            JOIN categorias c ON l.categoria_id = c.id
            JOIN obras o ON l.obra_id = o.id
            WHERE l.id = %s AND o.ativo = %s
        """ if is_postgres else """
            SELECT 
                l.id, l.descricao, l.valor, l.data_lancamento, l.observacoes, l.created_at,
                c.nome as categoria_nome, c.cor as categoria_cor
            FROM lancamentos l
            JOIN categorias c ON l.categoria_id = c.id
            JOIN obras o ON l.obra_id = o.id
            WHERE l.id = ? AND o.ativo = ?
        """
        
        cursor.execute(query, (lancamento_id, True if is_postgres else 1))
        row = cursor.fetchone()
        
        if row:
            # Converte valor para float
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
            
            return {
                'id': row['id'],
                'descricao': row['descricao'],
                'valor': valor,
                'data_lancamento': row['data_lancamento'],
                'observacoes': row['observacoes'],
                'created_at': row['created_at'],
                'categoria_nome': row['categoria_nome'],
                'categoria_cor': row['categoria_cor']
            }
        
        return None
        
    except Exception as e:
        print(f"Erro ao buscar lançamento por ID: {repr(e)}", file=sys.stderr)
        return None
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
        
        # Primeiro deleta os arquivos (CASCADE deve cuidar disso, mas garantimos)
        query_files = "DELETE FROM arquivos WHERE lancamento_id = %s" if is_postgres else "DELETE FROM arquivos WHERE lancamento_id = ?"
        cursor.execute(query_files, (lancamento_id,))
        
        # Depois deleta o lançamento
        query_lancamento = "DELETE FROM lancamentos WHERE id = %s" if is_postgres else "DELETE FROM lancamentos WHERE id = ?"
        cursor.execute(query_lancamento, (lancamento_id,))
        
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"Lançamento {lancamento_id} excluído com sucesso", file=sys.stderr)
            return True
        else:
            print(f"Lançamento {lancamento_id} não encontrado", file=sys.stderr)
            return False
        
    except Exception as e:
        print(f"Erro ao excluir lançamento: {repr(e)}", file=sys.stderr)
        conn.rollback()
        return False
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass