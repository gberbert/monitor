import sys
import os

# Adiciona o diretório atual ao path para importar o módulo corretamente
sys.path.append(os.getcwd())

try:
    from desktop_app import database
    
    print("Inicializando Banco de Dados...")
    database.init_db()
    
    print("Cadastrando Evento de Natal (Confetes)...")
    # upsert_event(day_key, title, media_url, interval_min, icon_start, icon_end)
    database.upsert_event(
        "24/12", 
        "Feliz Véspera de Natal!", 
        "", # Vazio = Confetes
        2,  # Intervalo de 2 min para testar facil
        "🎄", 
        "🎅"
    )
    print("Sucesso! Evento cadastrado.")
except Exception as e:
    print(f"Erro: {e}")
