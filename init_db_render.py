#!/usr/bin/env python3
"""
Script para inicializar o banco de dados no Render
"""
import sys
import os

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.database import init_db
from modules.auth import create_first_user

if __name__ == "__main__":
    print("🚀 Inicializando banco de dados no Render...")
    
    try:
        # Inicializar tabelas
        init_db()
        print("✅ Tabelas criadas!")
        
        # Criar usuário padrão
        create_first_user()
        print("✅ Usuário padrão criado!")
        
        print("🎉 Inicialização completa!")
        
    except Exception as e:
        print(f"❌ Erro na inicialização: {e}")
        sys.exit(1)