import streamlit as st
from datetime import date, datetime # Import datetime
from config.database import get_db_connection
from utils.helpers import get_categorias_ativas, format_currency_br # Import format_currency_br

def show_configuracoes(user, obra_config):
    """Exibe página de configurações"""
    st.header("⚙️ Configurações do Sistema")
    
    tab1, tab2, tab3 = st.tabs(["🏗️ Obra", "🏷️ Categorias", "👥 Sistema"])
    
    with tab1:
        _show_obra_config(obra_config)
    
    with tab2:
        _show_categorias_config()
    
    with tab3:
        _show_sistema_config(user)

def _show_obra_config(obra_config):
    """Configurações da obra"""
    st.subheader("��️ Configurações da Obra")
    
    with st.form("config_obra"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome_obra = st.text_input(
                "�� Nome da Obra",
                value=obra_config['nome_obra'],
                help="Nome que aparecerá no cabeçalho do sistema"
            )
            
            orcamento_total = st.number_input(
                "💰 Orçamento Total (R\$)",
                min_value=0.0,
                value=float(obra_config['orcamento_total']), # Ensure float for number_input
                step=1000.0,
                format="%.2f",
                help="Orçamento total previsto para a obra"
            )
        
        with col2:
            # Ensure date object for date_input
            initial_data_inicio = obra_config['data_inicio'] if obra_config['data_inicio'] else date.today()
            if isinstance(initial_data_inicio, str):
                try:
                    initial_data_inicio = datetime.strptime(initial_data_inicio, '%Y-%m-%d').date()
                except ValueError:
                    initial_data_inicio = date.today()

            initial_data_previsao_fim = obra_config['data_previsao_fim']
            if isinstance(initial_data_previsao_fim, str):
                try:
                    initial_data_previsao_fim = datetime.strptime(initial_data_previsao_fim, '%Y-%m-%d').date()
                except ValueError:
                    initial_data_previsao_fim = None

            data_inicio = st.date_input(
                "🗓️ Data de Início",
                value=initial_data_inicio,
                help="Data de início da obra"
            )
            
            data_previsao_fim = st.date_input(
                "🏁 Previsão de Término",
                value=initial_data_previsao_fim,
                help="Data prevista para conclusão da obra"
            )
        
        submitted = st.form_submit_button("💾 Salvar Configurações", type="primary")
        
        if submitted:
            # The 'ID da obra não encontrado' message from here means obra_config['id'] is None
            if obra_config['id'] is None:
                st.info("❌ Erro: ID da obra não encontrado. Criando nova configuração...")
                try:
                    success = _create_obra_config(nome_obra, orcamento_total, data_inicio, data_previsao_fim)
                    if success:
                        st.success("✅ Nova configuração criada com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao criar configuração!")
                except Exception as e:
                    st.error(f"❌ Erro ao criar configuração: {str(e)}")
                    print(f"Erro ao criar configuração: {e}", file=sys.stderr); sys.stderr.flush()
            else:
                success = _update_obra_config(nome_obra, orcamento_total, data_inicio, data_previsao_fim, obra_config['id'])
                if success:
                    st.success("✅ Configurações salvas com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar configurações!")
                    # Added print for better debug if error happens here
                    print(f"Erro ao salvar configuração: {e}", file=sys.stderr); sys.stderr.flush()

def _create_obra_config(nome_obra, orcamento_total, data_inicio, data_previsao_fim):
    """Cria uma nova configuração de obra"""
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            INSERT INTO obra_config (nome_obra, orcamento_total, data_inicio, data_previsao_fim)
            VALUES (?, ?, ?, ?)
        """
        params = (nome_obra, orcamento_total, data_inicio, data_previsao_fim)
        
        if db_type == 'postgresql':
            query = query.replace('?', '%s')
            cursor.execute(query, params)
        else:
            cursor.execute(query, params)
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Erro ao criar configuração de obra: {e}", file=sys.stderr); sys.stderr.flush()
        return False

def _update_obra_config(nome_obra, orcamento_total, data_inicio, data_previsao_fim, obra_id):
    """Atualiza configurações da obra"""
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            UPDATE obra_config 
            SET nome_obra = ?, orcamento_total = ?, data_inicio = ?, data_previsao_fim = ?
            WHERE id = ?
        """
        params = (nome_obra, orcamento_total, data_inicio, data_previsao_fim, obra_id)
        
        if db_type == 'postgresql':
            query = query.replace('?', '%s')
            cursor.execute(query, params)
        else:
            cursor.execute(query, params)
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Erro ao atualizar configuração: {e}", file=sys.stderr); sys.stderr.flush()
        return False

def _show_categorias_config():
    """Configurações de categorias"""
    st.subheader("🏷️ Gestão de Categorias")
    
    categorias_raw = get_categorias_ativas()
    # Ensure all items in categorias are dicts and have an 'id'
    categorias = [cat for cat in categorias_raw if cat and cat.get('id') is not None]
    
    if categorias:
        st.markdown("### �� Categorias Cadastradas")
        for categoria in categorias:
            # Use format_currency_br for display
            with st.expander(f"💰 {categoria['nome']} - {format_currency_br(categoria['orcamento_previsto'])}"):
                with st.form(key=f"edit_categoria_{categoria['id']}"): # Unique key for each form
                    col1, col2 = st.columns(2)
                    with col1:
                        novo_nome = st.text_input(
                            "Nome da Categoria",
                            value=categoria['nome'],
                            key=f"nome_{categoria['id']}" # Unique key
                        )
                        nova_descricao = st.text_area(
                            "Descrição",
                            value=categoria.get('descricao', ''),
                            key=f"desc_{categoria['id']}" # Unique key
                        )
                    with col2:
                        novo_orcamento = st.number_input(
                            "Orçamento Previsto (R\$)",
                            min_value=0.0,
                            value=float(categoria['orcamento_previsto']), # Ensure float
                            step=100.0,
                            format="%.2f",
                            key=f"orc_{categoria['id']}" # Unique key
                        )
                        ativa = st.checkbox(
                            "Categoria Ativa",
                            value=categoria.get('ativo', 1) == 1,
                            key=f"ativa_{categoria['id']}" # Unique key
                        )
                    col_save, col_delete = st.columns(2)
                    with col_save:
                        if st.form_submit_button("💾 Salvar", type="primary", key=f"save_cat_{categoria['id']}"): # Unique key
                            success = _update_categoria(
                                categoria['id'], novo_nome, nova_descricao, 
                                novo_orcamento, 1 if ativa else 0
                            )
                            if success:
                                st.success("✅ Categoria atualizada!")
                                st.rerun()
                            else:
                                st.error("❌ Erro ao atualizar categoria!")
                    with col_delete:
                        if st.form_submit_button("🗑️ Desativar", type="secondary", key=f"deactivate_cat_{categoria['id']}"): # Unique key
                            success = _update_categoria(
                                categoria['id'], novo_nome, nova_descricao, 
                                novo_orcamento, 0 # Deactivate category
                            )
                            if success:
                                st.success("✅ Categoria desativada!")
                                st.rerun()
                            else:
                                st.error("❌ Erro ao desativar categoria!")
    
    st.markdown("---")
    st.markdown("### ➕ Adicionar Nova Categoria")
    with st.form("nova_categoria"):
        col1, col2 = st.columns(2)
        with col1:
            nome_nova = st.text_input("Nome da Nova Categoria", key="new_cat_name") # Unique key
            descricao_nova = st.text_area("Descrição", key="new_cat_desc") # Unique key
        with col2:
            orcamento_nova = st.number_input(
                "Orçamento Previsto (R\$)",
                min_value=0.0,
                step=100.0,
                format="%.2f",
                key="new_cat_orc" # Unique key
            )
        if st.form_submit_button("➕ Criar Categoria", type="primary", key="create_cat_button"): # Unique key
            if nome_nova:
                success = _create_categoria(nome_nova, descricao_nova, orcamento_nova)
                if success:
                    st.rerun()
                # Success/error messages already handled in _create_categoria
            else:
                st.error("❌ Digite um nome para a categoria!")

def _update_categoria(categoria_id, nome, descricao, orcamento, ativo):
    """Atualiza uma categoria"""
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            UPDATE categorias 
            SET nome = ?, descricao = ?, orcamento_previsto = ?, ativo = ?
            WHERE id = ?
        """
        params = (nome, descricao, orcamento, ativo, categoria_id)
        
        if db_type == 'postgresql':
            query = query.replace('?', '%s')
            cursor.execute(query, params)
        else:
            cursor.execute(query, params)
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao atualizar categoria: {e}", file=sys.stderr); sys.stderr.flush()
        return False

def _create_categoria(nome, descricao, orcamento):
    """Cria uma nova categoria"""
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            INSERT INTO categorias (nome, descricao, orcamento_previsto, ativo)
            VALUES (?, ?, ?, 1)
        """
        params = (nome, descricao, orcamento)

        if db_type == 'postgresql':
            query_returning = query.replace('?', '%s') + " RETURNING id"
            cursor.execute(query_returning, params)
            new_id = cursor.fetchone()[0]
        else: # SQLite
            cursor.execute(query, params)
            new_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        if new_id:
            st.success(f"✅ Nova categoria '{nome}' criada com sucesso com ID: {new_id}!")
            return True
        else:
            st.error("❌ Erro ao criar categoria: O ID da nova categoria não foi retornado. Verifique a configuração do banco de dados.")
            return False
        
    except Exception as e:
        st.error(f"❌ Erro ao criar categoria: {str(e)}")
        print(f"Erro ao criar categoria: {e}", file=sys.stderr); sys.stderr.flush()
        return False

def _show_sistema_config(user):
    """Configurações do sistema"""
    st.subheader("👥 Configurações do Sistema")
    
    st.markdown("### 👤 Usuário Atual")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Nome:** {user['nome']}")
        st.info(f"**Email:** {user['email']}")
    with col2:
        st.info(f"**Tipo:** {user['tipo'].title()}")
        st.info(f"**Status:** {'Ativo' if user.get('ativo', 1) else 'Inativo'}")
    
    st.markdown("### 📊 Estatísticas do Sistema")
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE ativo = 1")
        total_usuarios = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM categorias WHERE ativo = 1")
        total_categorias = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM lancamentos")
        total_lancamentos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM arquivos")
        total_arquivos = cursor.fetchone()[0]
        
        conn.close()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("👥 Usuários Ativos", total_usuarios)
        with col2: st.metric("🏷️ Categorias Ativas", total_categorias)
        with col3: st.metric("💰 Lançamentos", total_lancamentos)
        with col4: st.metric("📎 Arquivos", total_arquivos)
        
    except Exception as e:
        st.error(f"❌ Erro ao buscar estatísticas: {e}")
        print(f"Erro ao buscar estatisticas: {e}", file=sys.stderr); sys.stderr.flush()
    
    st.markdown("### 🔧 Manutenção")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Verificar Integridade do Banco", type="secondary", key="check_db_integrity"): # Unique key
            _verificar_integridade_banco()
    with col2:
        if st.button("🔄 Recarregar Sistema", type="secondary", key="reload_system"): # Unique key
            st.rerun()

def _verificar_integridade_banco():
    """Verifica integridade do banco de dados"""
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        if db_type == 'sqlite':
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tabelas = cursor.fetchall()
            st.success(f"✅ Banco SQLite íntegro! {len(tabelas)} tabelas encontradas.")
        else: # PostgreSQL
            cursor.execute("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';")
            tabelas = cursor.fetchall()
            st.success(f"✅ Banco PostgreSQL íntegro! {len(tabelas)} tabelas encontradas.")
        
        cursor.execute("""
            SELECT COUNT(*) FROM lancamentos l
            LEFT JOIN categorias c ON l.categoria_id = c.id
            WHERE c.id IS NULL
        """)
        orfaos_categoria = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM lancamentos l
            LEFT JOIN usuarios u ON l.usuario_id = u.id
            WHERE u.id IS NULL
        """)
        orfaos_usuario = cursor.fetchone()[0]
        
        if orfaos_categoria > 0:
            st.warning(f"⚠️ {orfaos_categoria} lançamento(s) com categoria inválida")
        
        if orfaos_usuario > 0:
            st.warning(f"⚠️ {orfaos_usuario} lançamento(s) com usuário inválido")
        
        if orfaos_categoria == 0 and orfaos_usuario == 0:
            st.success("✅ Nenhum dado órfão encontrado!")
        
        conn.close()
        
    except Exception as e:
        st.error(f"❌ Erro na verificação: {e}")
        print(f"Erro na verificacao de integridade: {e}", file=sys.stderr); sys.stderr.flush()