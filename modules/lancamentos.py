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
        show_novo_lancamento()
    
    with tab2:
        show_lista_lancamentos()
    
    with tab3:
        show_filtros_lancamentos()

def show_novo_lancamento():
    """Formulário para novo lançamento - VERSÃO SIMPLIFICADA"""
    st.subheader("➕ Registrar Novo Lançamento")
    
    # Verifica se há obra configurada
    obra_config = get_obra_config()
    
    if not obra_config or not obra_config.get('id'):
        st.error("⚠️ Configure uma obra antes de registrar lançamentos!")
        if st.button("🔧 Ir para Configurações", use_container_width=True):
            st.session_state.current_page = "⚙️ Configurações"
            st.rerun()
        return
    
    # Verifica se há categorias
    categorias = get_categorias_ativas()
    if not categorias:
        st.error("⚠️ Cadastre pelo menos uma categoria antes de registrar lançamentos!")
        if st.button("🏷️ Ir para Categorias", use_container_width=True):
            st.session_state.current_page = "⚙️ Configurações"
            st.rerun()
        return
    
    # Mostra informações da obra atual
    st.info(f"📋 **Obra Ativa:** {obra_config['nome']} | **Orçamento:** {format_currency_br(obra_config['orcamento'])}")
    
    # FORMULÁRIO DIRETO SEM FORM WRAPPER
    st.markdown("### 📝 Dados do Lançamento")
    
    col1, col2 = st.columns(2)
    
    with col1:
        descricao = st.text_input(
            "Descrição *",
            placeholder="Ex: Compra de cimento para fundação",
            key="desc_novo"
        )
        
        valor = st.number_input(
            "Valor (R$) *",
            min_value=0.01,
            step=0.01,
            format="%.2f",
            key="valor_novo"
        )
    
    with col2:
        # Selectbox para categorias
        categoria_options = {f"{cat['nome']}": cat['id'] for cat in categorias}
        categoria_selecionada = st.selectbox(
            "Categoria *",
            options=list(categoria_options.keys()),
            index=0,
            key="cat_nova"
        )
        
        data_lancamento = st.date_input(
            "Data do Lançamento *",
            value=date.today(),
            max_value=date.today(),
            key="data_nova"
        )
    
    observacoes = st.text_area(
        "Observações (opcional)",
        placeholder="Informações adicionais sobre o lançamento...",
        key="obs_nova"
    )
    
    # Botão de salvar FORA do form
    if st.button("💾 REGISTRAR LANÇAMENTO", use_container_width=True, type="primary"):
        print(f"=== BOTÃO CLICADO - FORMULÁRIO SUBMETIDO ===", file=sys.stderr)
        print(f"Descrição: '{descricao}'", file=sys.stderr)
        print(f"Valor: {valor}", file=sys.stderr)
        print(f"Categoria: '{categoria_selecionada}'", file=sys.stderr)
        print(f"Data: {data_lancamento}", file=sys.stderr)
        
        # Validações básicas
        erro = False
        
        if not descricao or not descricao.strip():
            st.error("⚠️ A descrição é obrigatória!")
            print("ERRO: Descrição vazia", file=sys.stderr)
            erro = True
        
        if valor <= 0:
            st.error("⚠️ O valor deve ser maior que zero!")
            print(f"ERRO: Valor inválido: {valor}", file=sys.stderr)
            erro = True
        
        if not categoria_selecionada:
            st.error("⚠️ Selecione uma categoria!")
            print("ERRO: Categoria não selecionada", file=sys.stderr)
            erro = True
        
        if erro:
            print("ERRO: Validação falhou", file=sys.stderr)
            return
        
        print("✅ Validações passaram", file=sys.stderr)
        
        # Pega ID da categoria
        categoria_id = categoria_options[categoria_selecionada]
        print(f"ID da categoria: {categoria_id}", file=sys.stderr)
        
        # Tenta salvar
        with st.spinner("Salvando lançamento..."):
            lancamento_id = save_lancamento_direto(
                obra_config['id'],
                categoria_id,
                descricao,
                valor,
                data_lancamento,
                observacoes
            )
        
        print(f"Resultado do salvamento: {lancamento_id}", file=sys.stderr)
        
        if lancamento_id:
            st.success(f"✅ Lançamento registrado com sucesso! ID: {lancamento_id}")
            st.balloons()
            
            # Limpa campos
            for key in ['desc_novo', 'valor_novo', 'cat_nova', 'data_nova', 'obs_nova']:
                if key in st.session_state:
                    del st.session_state[key]
            
            # Limpa cache
            cache_keys = ['dashboard_cache', 'lancamentos_cache']
            for key in cache_keys:
                if key in st.session_state:
                    del st.session_state[key]
            
            print("✅ Cache limpo, recarregando em 2 segundos...", file=sys.stderr)
            import time
            time.sleep(2)
            st.rerun()
        else:
            st.error("❌ Erro ao registrar lançamento! Verifique os logs.")
            print("ERRO: Lançamento não foi salvo", file=sys.stderr)

def save_lancamento_direto(obra_id, categoria_id, descricao, valor, data_lancamento, observacoes):
    """Salva lançamento de forma mais direta"""
    try:
        print(f"=== SALVAMENTO DIRETO INICIADO ===", file=sys.stderr)
        print(f"Obra: {obra_id}, Categoria: {categoria_id}", file=sys.stderr)
        print(f"Descrição: {descricao}", file=sys.stderr)
        print(f"Valor: {valor} (tipo: {type(valor)})", file=sys.stderr)
        print(f"Data: {data_lancamento}", file=sys.stderr)
        
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        # Converte data
        if isinstance(data_lancamento, date):
            data_str = data_lancamento.strftime('%Y-%m-%d')
        else:
            data_str = str(data_lancamento)
        
        # Converte valor
        valor_float = float(valor)
        
        print(f"Dados convertidos - Data: {data_str}, Valor: {valor_float}", file=sys.stderr)
        
        # Query mais simples
        if is_postgres:
            query = """
                INSERT INTO lancamentos (obra_id, categoria_id, descricao, valor, data_lancamento, observacoes)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            params = (obra_id, categoria_id, descricao, valor_float, data_str, observacoes)
        else:
            query = """
                INSERT INTO lancamentos (obra_id, categoria_id, descricao, valor, data_lancamento, observacoes)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (obra_id, categoria_id, descricao, valor_float, data_str, observacoes)
        
        print(f"Executando query: {query}", file=sys.stderr)
        print(f"Parâmetros: {params}", file=sys.stderr)
        
        cursor.execute(query, params)
        
        # Pega ID
        if is_postgres:
            result = cursor.fetchone()
            lancamento_id = result['id'] if result else None
        else:
            lancamento_id = cursor.lastrowid
        
        print(f"ID obtido: {lancamento_id}", file=sys.stderr)
        
        if lancamento_id:
            conn.commit()
            print(f"✅ COMMIT realizado - Lançamento {lancamento_id} salvo", file=sys.stderr)
            
            # Verifica se foi salvo
            if is_postgres:
                cursor.execute("SELECT COUNT(*) as total FROM lancamentos WHERE obra_id = %s", (obra_id,))
            else:
                cursor.execute("SELECT COUNT(*) as total FROM lancamentos WHERE obra_id = ?", (obra_id,))
            
            total = cursor.fetchone()['total']
            print(f"Total de lançamentos na obra agora: {total}", file=sys.stderr)
            
            cursor.close()
            conn.close()
            return lancamento_id
        else:
            print("ERRO: ID não retornado", file=sys.stderr)
            conn.rollback()
            cursor.close()
            conn.close()
            return None
            
    except Exception as e:
        print(f"ERRO CRÍTICO no salvamento: {repr(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        
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

def show_lista_lancamentos():
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
    lancamentos = get_lancamentos()
    
    if not lancamentos:
        st.info("📝 Nenhum lançamento registrado ainda.")
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
    
    # Lista de lançamentos
    for lancamento in lancamentos:
        with st.expander(f"🧾 {lancamento['descricao']} - {format_currency_br(lancamento['valor'])}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**📅 Data:** {format_date_br(lancamento['data_lancamento'])}")
                st.write(f"**��️ Categoria:** {lancamento['categoria_nome']}")
                st.write(f"**💰 Valor:** {format_currency_br(lancamento['valor'])}")
            
            with col2:
                if lancamento['observacoes']:
                    st.write(f"**📝 Observações:** {lancamento['observacoes']}")
            
            # Botão de excluir
            if st.button(f"🗑️ Excluir", key=f"delete_{lancamento['id']}", use_container_width=True):
                if delete_lancamento(lancamento['id']):
                    st.success("✅ Lançamento excluído!")
                    # Limpa cache
                    if 'lancamentos_cache' in st.session_state:
                        del st.session_state['lancamentos_cache']
                    if 'dashboard_cache' in st.session_state:
                        del st.session_state['dashboard_cache']
                    st.rerun()
                else:
                    st.error("❌ Erro ao excluir!")

def get_lancamentos():
    """Busca todos os lançamentos"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        # Busca obra ativa
        obra_config = get_obra_config()
        if not obra_config.get('id'):
            return []
        
        obra_id = obra_config['id']
        
        if is_postgres:
            query = """
                SELECT 
                    l.id, l.descricao, l.valor, l.data_lancamento, l.observacoes,
                    c.nome as categoria_nome, c.cor as categoria_cor
                FROM lancamentos l
                JOIN categorias c ON l.categoria_id = c.id
                WHERE l.obra_id = %s
                ORDER BY l.data_lancamento DESC, l.id DESC
            """
            cursor.execute(query, (obra_id,))
        else:
            query = """
                SELECT 
                    l.id, l.descricao, l.valor, l.data_lancamento, l.observacoes,
                    c.nome as categoria_nome, c.cor as categoria_cor
                FROM lancamentos l
                JOIN categorias c ON l.categoria_id = c.id
                WHERE l.obra_id = ?
                ORDER BY l.data_lancamento DESC, l.id DESC
            """
            cursor.execute(query, (obra_id,))
        
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
        
        print(f"Encontrados {len(lancamentos)} lançamentos na listagem", file=sys.stderr)
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

def delete_lancamento(lancamento_id):
    """Exclui lançamento"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        import os
        is_postgres = os.getenv('DATABASE_URL') is not None
        
        if is_postgres:
            cursor.execute("DELETE FROM lancamentos WHERE id = %s", (lancamento_id,))
        else:
            cursor.execute("DELETE FROM lancamentos WHERE id = ?", (lancamento_id,))
        
        conn.commit()
        rows_affected = cursor.rowcount
        
        cursor.close()
        conn.close()
        
        print(f"Lançamento {lancamento_id} excluído. Linhas afetadas: {rows_affected}", file=sys.stderr)
        return rows_affected > 0
        
    except Exception as e:
        print(f"Erro ao excluir lançamento: {repr(e)}", file=sys.stderr)
        return False
    finally:
        try:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
        except:
            pass

def show_filtros_lancamentos():
    """Filtros e busca de lançamentos"""
    st.subheader("🔍 Buscar e Filtrar Lançamentos")
    st.info("Funcionalidade em desenvolvimento...")

# Funções auxiliares vazias para compatibilidade
def validate_file_upload(file):
    return True, "OK"

def save_file(lancamento_id, file):
    return True

def download_file(arquivo_id):
    pass