#!/usr/bin/env python3
"""
Script para inicializar o banco de dados
Execute: python init_db.py
"""

import sys
import os

# Adiciona o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import init_db

if __name__ == "__main__":
    print("🔧 Inicializando banco de dados...")
    
    try:
        init_db()
        print("✅ Banco de dados inicializado com sucesso!")
        print("\n📋 Próximos passos:")
        print("1. Execute: streamlit run app.py")
        print("2. Acesse o sistema no navegador")
        print("3. Clique em 'Inicializar Sistema' se for o primeiro acesso")
        print("4. Use: deverson@obra.com / 123456 para login")
        
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {repr(e)}")
        sys.exit(1)