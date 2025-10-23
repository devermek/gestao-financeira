import streamlit as st
import pandas as pd
from datetime import datetime, date
from config.database import get_db_connection

def show_lancamentos(user):
    """Exibe módulo de lançamentos"""
    st.title("💰 Lançamentos Financeiros")
    
    # Buscar categorias ativas
    categorias = get_categorias_ativas_local()
    
    if categorias.empty:
        st.warning("⚠️ Nenhuma categoria encontrada. Configure as categorias primeiro.")
        if st.button("⚙️ Ir para Configurações"):
            st.session_state.page = "configuracoes"
            st.rerun()
        return
    
    # Formulário de novo lançamento
    with st.expander("➕ Novo Lançamento", expanded=True):
        with st.form("novo_lancamento"):
            col1, col2 = st.columns(2)
            
            with col1:
                data = st.date_input("📅 Data", value=datetime.now().date())
                
                # Criar opções do selectbox com ID e nome
                categoria_options = ["Selecione uma categoria..."]
                categoria_ids = [None]
                
                for _, cat in categorias.iterrows():
                    categoria_options.append(f"{cat['nome']} (R\$ {cat['orcamento_previsto']:,.2f})")
                    categoria_ids.append(cat['id'])
                
                categoria_index = st.selectbox(
                    "🏷️ Categoria",
                    options=range(len(categoria_options)),
                    format_func=lambda x: categoria_options[x],
                    key="categoria_lancamento"
                )
                
            with col2:
                valor = st.number_input(
                    "💰 Valor (R\$)",
                    min_value=0.01,
                    step=0.01,
                    format="%.2f"
                )
                
                descricao = st.text_input("📝 Descrição")
            
            observacoes = st.text_area("📋 Observações (opcional)")
            
            if st.form_submit_button("💾 Salvar Lançamento", type="primary"):
                # Validações
                categoria_id = categoria_ids[categoria_index] if categoria_index > 0 else None
                
                if not categoria_id:
                    st.error("⚠️ Selecione uma categoria")
                elif valor <= 0:
                    st.error("⚠️ Valor deve ser maior que zero")
                elif not descricao.strip():
                    st.error("⚠️ Descrição é obrigatória")
                else:
                    # Salvar lançamento
                    sucesso = salvar_lancamento_local(
                        data=data,
                        categoria_id=categoria_id,
                        descricao=descricao.strip(),
                        valor=valor,
                        observacoes=observacoes.strip() if observacoes else "",
                        usuario_id=user['id']
                    )
                    
                    if sucesso:
                        st.success("✅ Lançamento salvo com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao salvar lançamento")
    
    # Mostrar lançamentos existentes
    st.markdown("---")
    st.subheader("📋 Lançamentos Recentes")
    
    lancamentos = get_lancamentos_recentes_local(user['id'])
    
    if not lancamentos.empty:
        # Formatar para exibição
        df_display = lancamentos.copy()
        df_display['data'] = pd.to_datetime(df_display['data']).dt.strftime('%d/%m/%Y')
        df_display['valor'] = df_display['valor'].apply(lambda x: f"R\$ {x:,.2f}")
        
        st.dataframe(
            df_display[['data', 'categoria_nome', 'descricao', 'valor']],
            column_config={
                'data': 'Data',
                'categoria_nome': 'Categoria',
                'descricao': 'Descrição',
                'valor': 'Valor'
            },
            use_container_width=True
        )
    else:
        st.info("📝 Nenhum lançamento encontrado")

def get_categorias_ativas_local():
    """Busca categorias ativas (função local)"""
    try:
        conn = get_db_connection()
        categorias = pd.read_sql_query("""
            SELECT id, nome, descricao, orcamento_previsto 
            FROM categorias 
            WHERE ativo = 1 
            ORDER BY nome
        """, conn)
        conn.close()
        return categorias
    except Exception as e:
        print(f"Erro ao buscar categorias: {e}")
        return pd.DataFrame()

def get_lancamentos_recentes_local(usuario_id, limit=10):
    """Busca lançamentos recentes do usuário (função local)"""
    try:
        conn = get_db_connection()
        lancamentos = pd.read_sql_query("""
            SELECT l.*, c.nome as categoria_nome
            FROM lancamentos l
            JOIN categorias c ON l.categoria_id = c.id
            WHERE l.usuario_id = ?
            ORDER BY l.data DESC, l.id DESC
            LIMIT ?
        """, conn, params=[usuario_id, limit])
        conn.close()
        return lancamentos
    except Exception as e:
        print(f"Erro ao buscar lançamentos: {e}")
        return pd.DataFrame()

def salvar_lancamento_local(data, categoria_id, descricao, valor, observacoes, usuario_id):
    """Salva um novo lançamento (função local)"""
    try:
        # Debug
        print(f"DEBUG - Salvando: categoria_id={categoria_id}, valor={valor}, desc={descricao}")
        
        if categoria_id is None:
            print("ERRO: categoria_id é None!")
            return False
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO lancamentos (data, categoria_id, descricao, valor, observacoes, usuario_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (data, categoria_id, descricao, valor, observacoes, usuario_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Lançamento salvo com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao salvar lançamento: {e}")
        return False