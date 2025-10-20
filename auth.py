import hashlib
import streamlit as st
from config.database import get_db_connection
import sys
import traceback

def hash_password(password):
    """Gera hash da senha usando SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def ensure_first_admin_exists():
    """Garante que existe pelo menos um usuário administrador no sistema"""
    print("DEBUG AUTH: === INICIANDO ensure_first_admin_exists ===", file=sys.stderr)
    
    try:
        print("DEBUG AUTH: Tentando obter conexão com banco", file=sys.stderr)
        conn = get_db_connection()
        print(f"DEBUG AUTH: Conexão obtida: {type(conn)}", file=sys.stderr)
        
        cursor = conn.cursor()
        print("DEBUG AUTH: Cursor criado", file=sys.stderr)
        
        # Verificar se existem usuários
        print("DEBUG AUTH: Executando query COUNT", file=sys.stderr)
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        count_result = cursor.fetchone()
        print(f"DEBUG AUTH: Resultado COUNT raw: {count_result}", file=sys.stderr)
        
        # Tratamento robusto do resultado
        if count_result is None:
            user_count = 0
            print("DEBUG AUTH: count_result é None, definindo user_count = 0", file=sys.stderr)
        else:
            # Para PostgreSQL (RealDictRow) e SQLite (tuple/Row)
            if hasattr(count_result, '__getitem__'):
                user_count = count_result[0]
            else:
                user_count = int(count_result)
            print(f"DEBUG AUTH: user_count extraído: {user_count}", file=sys.stderr)
        
        print(f"DEBUG AUTH: Total de usuários encontrados: {user_count}", file=sys.stderr)
        
        if user_count == 0:
            print("DEBUG AUTH: Nenhum usuário encontrado, criando admin inicial", file=sys.stderr)
            
            # Dados do admin padrão
            admin_data = {
                'nome': 'Administrador',
                'email': 'admin@obra.com',
                'senha': hash_password('admin123'),
                'tipo': 'admin'
            }
            print(f"DEBUG AUTH: Dados do admin preparados: {admin_data['nome']}, {admin_data['email']}, tipo: {admin_data['tipo']}", file=sys.stderr)
            
            # Inserir usuário admin
            insert_query = """
                INSERT INTO usuarios (nome, email, senha, tipo) 
                VALUES (%s, %s, %s, %s)
            """
            print(f"DEBUG AUTH: Executando INSERT com query: {insert_query}", file=sys.stderr)
            
            cursor.execute(insert_query, (
                admin_data['nome'],
                admin_data['email'], 
                admin_data['senha'],
                admin_data['tipo']
            ))
            print("DEBUG AUTH: INSERT executado com sucesso", file=sys.stderr)
            
            conn.commit()
            print("DEBUG AUTH: COMMIT realizado", file=sys.stderr)
            
            print("DEBUG AUTH: ✅ Usuário administrador criado com sucesso!", file=sys.stderr)
        else:
            print(f"DEBUG AUTH: ✅ Já existem {user_count} usuários no sistema", file=sys.stderr)
        
        cursor.close()
        conn.close()
        print("DEBUG AUTH: Conexão fechada com sucesso", file=sys.stderr)
        print("DEBUG AUTH: === FINALIZANDO ensure_first_admin_exists COM SUCESSO ===", file=sys.stderr)
        
        return True
        
    except Exception as e:
        print(f"DEBUG AUTH ERROR: Exception in ensure_first_admin_exists", file=sys.stderr)
        print(f"DEBUG AUTH ERROR: Tipo da exceção: {type(e).__name__}", file=sys.stderr)
        print(f"DEBUG AUTH ERROR: Mensagem: {str(e)}", file=sys.stderr)
        print("DEBUG AUTH ERROR: Traceback completo:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print("DEBUG AUTH ERROR: === FIM DO TRACEBACK ===", file=sys.stderr)
        return False

def login_user(email, senha):
    """Autentica usuário no sistema"""
    print(f"DEBUG AUTH: Tentativa de login para email: {email}", file=sys.stderr)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        senha_hash = hash_password(senha)
        
        cursor.execute(
            "SELECT id, nome, email, tipo FROM usuarios WHERE email = %s AND senha = %s",
            (email, senha_hash)
        )
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            print(f"DEBUG AUTH: Login bem-sucedido para: {email}", file=sys.stderr)
            # Tratamento compatível para diferentes tipos de resultado
            if hasattr(user, '_asdict'):  # RealDictRow
                return dict(user)
            elif hasattr(user, 'keys'):  # sqlite3.Row
                return dict(user)
            else:  # tuple
                return {
                    'id': user[0],
                    'nome': user[1], 
                    'email': user[2],
                    'tipo': user[3]
                }
        else:
            print(f"DEBUG AUTH: Login falhou para: {email}", file=sys.stderr)
            return None
            
    except Exception as e:
        print(f"DEBUG AUTH ERROR: Erro no login: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return None

def logout_user():
    """Remove dados do usuário da sessão"""
    keys_to_remove = ['user_id', 'user_name', 'user_email', 'user_type', 'authenticated']
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]

def is_authenticated():
    """Verifica se usuário está autenticado"""
    return st.session_state.get('authenticated', False)

def get_current_user():
    """Retorna dados do usuário atual da sessão"""
    if is_authenticated():
        return {
            'id': st.session_state.get('user_id'),
            'nome': st.session_state.get('user_name'),
            'email': st.session_state.get('user_email'),
            'tipo': st.session_state.get('user_type')
        }
    return None

def is_admin():
    """Verifica se usuário atual é administrador"""
    user = get_current_user()
    return user and user.get('tipo') == 'admin'