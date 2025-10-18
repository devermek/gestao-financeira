import sqlite3

def verificar_estrutura():
    conn = sqlite3.connect('obra_database.db')
    cursor = conn.cursor()
    
    # Verificar estrutura da tabela arquivos
    cursor.execute("PRAGMA table_info(arquivos)")
    colunas = cursor.fetchall()
    
    print("🗃️ Estrutura atual da tabela 'arquivos':")
    for coluna in colunas:
        print(f"  - {coluna[1]} ({coluna[2]})")
    
    conn.close()

if __name__ == "__main__":
    verificar_estrutura()