import streamlit as st
from datetime import date, datetime # Importar datetime para updated_at no SQLite
from config.database import get_db_connection # Remover get_current_db_type
from utils.helpers import get_categorias_ativas

def show_configuracoes(user, obra_config):
    """Exibe página de configurações"""
    st.header("⚙️ Configurações do Sistema")
    
    # Tabs para organizar
    tab1, tab2, tab3 = st.tabs(["🏗️ Obra", "🏷️ Categorias", "👥 Sistema"])
    
    with tab1:
        _show_obra_config(obra_config)
    
    with tab2:
        _show_categorias_config()
    
    with tab3:
        _show_sistema_config(user)

def _show_obra_config(obra_config):
    """Configurações da obra"""
    st.subheader("🏗️ Configurações da Obra")
    
    with st.form("config_obra"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome_obra = st.text_input(
                "🏗️ Nome da Obra",
                value=obra_config['nome_obra'],
                help="Nome que aparecerá no cabeçalho do sistema"
            )
            
            orcamento_total = st.number_input(
                "💰 Orçamento Total (R$)",
                min_value=0.0,
                value=float(obra_config['orcamento_total']),
                step=1000.0,
                format="%.2f",
                help="Orçamento total previsto para a obra"
            )
        
        with col2:
            data_inicio = st.date_input(
                "🗓️ Data de Início",
                value=obra_config['data_inicio'] if obra_config['data_inicio'] else date.today(),
                help="Data de início da obra"
            )
            
            data_previsao_fim = st.date_input(
                "🏁 Previsão de Término",
                value=obra_config['data_previsao_fim'] if obra_config['data_previsao_fim'] else None,
                help="Data prevista para conclusão da obra"
            )
        
        submitted = st.form_submit_button("💾 Salvar Configurações", type="primary")
        
        if submitted:
            # VERIFICAR SE TEM ID
            if obra_config['id'] is None:
                st.error("❌ Erro: ID da obra não encontrado. Criando nova configuração...")
                
                # Criar nova configuração
                try:
                    conn, db_type = get_db_connection() # Obter a conexão e o tipo de DB
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        INSERT INTO obra_config (nome_obra, orcamento_total, data_inicio, data_previsao_fim)
                        VALUES (?, ?, ?, ?)
                    """, (nome_obra, orcamento_total, data_inicio, data_previsao_fim))
                    
                    conn.commit()
                    conn.close()
                    
                    st.success("✅ Nova configuração criada com sucesso!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erro ao criar configuração: {str(e)}")
            else:
                # Atualizar configuração existente
                success = _update_obra_config(nome_obra, orcamento_total, data_inicio, data_previsao_fim, obra_config['id'])
                
                if success:
                    st.success("✅ Configurações salvas com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar configurações!")

def _update_obra_config(nome_obra, orcamento_total, data_inicio, data_previsao_fim, obra_id):
    """Atualiza configurações da obra"""
    try:
        conn, db_type = get_db_connection() # Obter a conexão e o tipo de DB
        cursor = conn.cursor()
        
        # Lógica para atualizar updated_at no SQLite, já que não tem triggers automáticos
        if db_type == 'sqlite':
            cursor.execute("""
                UPDATE obra_config 
                SET nome_obra = ?, orcamento_total = ?, data_inicio = ?, data_previsao_fim = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (nome_obra, orcamento_total, data_inicio, data_previsao_fim, obra_id))
        else: # PostgreSQL
            cursor.execute("""
                UPDATE obra_config 
                SET nome_obra = ?, orcamento_total = ?, data_inicio = ?, data_previsao_fim = ?
                WHERE id = ?
            """, (nome_obra, orcamento_total, data_inicio, data_previsao_fim, obra_id))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Erro ao atualizar configuração: {e}")
        return False

def _show_categorias_config():
    """Configurações de categorias"""
    st.subheader("🏷️ Gestão de Categorias")
    
    # Mostrar categorias existentes
    categorias_raw = get_categorias_ativas()
    
    # FILTRO ESSENCIAL: Garantir que apenas categorias com ID válido sejam processadas
    categorias = [cat for cat in categorias_raw if cat and cat.get('id') is not None]
    
    if categorias:
        st.markdown("### 📋 Categorias Cadastradas")
        
        for categoria in categorias:
            # A chave do formulário agora está segura, pois categoria['id'] não será None
            with st.expander(f"✨ {categoria['nome']} - R$ {categoria['orcamento_previsto']:,.2f}"):
                with st.form(key=f"edit_categoria_{categoria['id']}"): 
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        novo_nome = st.text_input(
                            "Nome da Categoria",
                            value=categoria['nome'],
                            key=f"nome_{categoria['id']}"
                        )
                        
                        nova_descricao = st.text_area(
                            "Descrição",
                            value=categoria.get('descricao', ''),
                            key=f"desc_{categoria['id']}"
                        )
                    
                    with col2:
                        novo_orcamento = st.number_input(
                            "Orçamento Previsto (R$)",
                            min_value=0.0,
                            value=float(categoria['orcamento_previsto']),
                            step=100.0,
                            format="%.2f",
                            key=f"orc_{categoria['id']}"
                        )
                        
                        ativa = st.checkbox(
                            "Categoria Ativa",
                            value=categoria.get('ativo', 1) == 1,
                            key=f"ativa_{categoria['id']}"
                        )
                    
                    col_save, col_delete = st.columns(2)
                    
                    with col_save:
                        if st.form_submit_button("�� Salvar", type="primary"):
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
                        # Este botão agora desativa a categoria (seta ativo=0)
                        if st.form_submit_button("🗑️ Desativar", type="secondary"):
                            success = _update_categoria(
                                categoria['id'], novo_nome, nova_descricao, 
                                novo_orcamento, 0 # Desativa a categoria
                            )
                            if success:
                                st.success("✅ Categoria desativada!")
                                st.rerun()
                            else:
                                st.error("❌ Erro ao desativar categoria!")
    
    # Adicionar nova categoria
    st.markdown("---")
    st.markdown("### ➕ Adicionar Nova Categoria")
    
    with st.form("nova_categoria"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome_nova = st.text_input("Nome da Nova Categoria")
            descricao_nova = st.text_area("Descrição")
        
        with col2:
            orcamento_nova = st.number_input(
                "Orçamento Previsto (R$)",
                min_value=0.0,
                step=100.0,
                format="%.2f"
            )
        
        if st.form_submit_button("➕ Criar Categoria", type="primary"):
            if nome_nova:
                success = _create_categoria(nome_nova, descricao_nova, orcamento_nova)
                if success:
                    st.rerun() # Recarregar para mostrar a nova categoria
                # Mensagens de sucesso/erro já estão dentro de _create_categoria
            else:
                st.error("❌ Digite um nome para a categoria!")

def _update_categoria(categoria_id, nome, descricao, orcamento, ativo):
    """Atualiza uma categoria"""
    try:
        conn, db_type = get_db_connection() # Obter a conexão e o tipo de DB
        cursor = conn.cursor()
        
        # Lógica para atualizar updated_at no SQLite
        if db_type == 'sqlite':
            cursor.execute("""
                UPDATE categorias 
                SET nome = ?, descricao = ?, orcamento_previsto = ?, ativo = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (nome, descricao, orcamento, ativo, categoria_id))
        else: # PostgreSQL
            cursor.execute("""
                UPDATE categorias 
                SET nome = ?, descricao = ?, orcamento_previsto = ?, ativo = ?
                WHERE id = ?
            """, (nome, descricao, orcamento, ativo, categoria_id))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Erro ao atualizar categoria: {e}")
        return False

def _create_categoria(nome, descricao, orcamento):
    """Cria uma nova categoria"""
    try:
        conn, db_type = get_db_connection() # Obter a conexão e o tipo de DB
        cursor = conn.cursor()
        
        if db_type == 'postgresql':
            # Para PostgreSQL, use RETURNING id
            cursor.execute("""
                INSERT INTO categorias (nome, descricao, orcamento_previsto, ativo)
                VALUES (%s, %s, %s, 1) RETURNING id
            """, (nome, descricao, orcamento))
            new_id = cursor.fetchone()[0] # Pega o ID retornado
        else: # SQLite
            # Para SQLite, use cursor.lastrowid
            cursor.execute("""
                INSERT INTO categorias (nome, descricao, orcamento_previsto, ativo)
                VALUES (?, ?, ?, 1)
            """, (nome, descricao, orcamento))
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
        return False

def _show_sistema_config(user):
    """Configurações do sistema"""
    st.subheader("�� Configurações do Sistema")
    
    # Informações do usuário atual
    st.markdown("### 👤 Usuário Atual")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Nome:** {user['nome']}")
        st.info(f"**Email:** {user['email']}")
    
    with col2:
        st.info(f"**Tipo:** {user['tipo'].title()}")
        st.info(f"**Status:** {'Ativo' if user.get('ativo', 1) else 'Inativo'}")
    
    # Estatísticas do sistema
    st.markdown("### 📊 Estatísticas do Sistema")
    
    try:
        conn, db_type = get_db_connection() # Obter a conexão e o tipo de DB
        cursor = conn.cursor()
        
        # Contar registros
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
        
        with col1:
            st.metric("👥 Usuários Ativos", total_usuarios)
        
        with col2:
            st.metric("🏷️ Categorias Ativas", total_categorias)
        
        with col3:
            st.metric("💰 Lançamentos", total_lancamentos)
        
        with col4:
            st.metric("�� Arquivos", total_arquivos)
        
    except Exception as e:
        st.error(f"❌ Erro ao buscar estatísticas: {e}")
    
    # Backup e manutenção
    st.markdown("### 🔧 Manutenção")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Verificar Integridade do Banco", type="secondary"):
            _verificar_integridade_banco()
    
    with col2:
        if st.button("🔄 Recarregar Sistema", type="secondary"):
            st.rerun()

def _verificar_integridade_banco():
    """Verifica integridade do banco de dados"""
    try:
        conn, db_type = get_db_connection() # Obter a conexão e o tipo de DB
        cursor = conn.cursor()
        
        if db_type == 'sqlite':
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tabelas = cursor.fetchall()
            st.success(f"✅ Banco SQLite íntegro! {len(tabelas)} tabelas encontradas.")
        else: # PostgreSQL
            cursor.execute("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';")
            tabelas = cursor.fetchall()
            st.success(f"✅ Banco PostgreSQL íntegro! {len(tabelas)} tabelas encontradas.")
        
        # Verificar dados órfãos
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
