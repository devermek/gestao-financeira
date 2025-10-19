#!/usr/bin/env python3
"""
Script para inicializar o banco de dados no Render
"""
import sys
import os

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.database import init_db

if __name__ == "__main__":
    print("🚀 Inicializando banco de dados no Render...")
    init_db()
    print("✅ Banco de dados inicializado!")