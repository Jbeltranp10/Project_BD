import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

MONGODB_CONFIG = {
    # Configuración de conexión
    "URI": os.getenv('MONGODB_URI', 'mongodb+srv://jbeltranp3:B3ltr4n96j@cluster0.8i802.mongodb.net/'),
    "DB_NAME": "relatoria",
    "COLLECTION_NAME": "providencias",
    
    # Índices como lista de tuplas de strings
    "INDEXES": [
        ("texto", "text"),          # Índice de texto
        ("providencia", "1"),       # Índice ascendente
        ("tipo", "1"),             # Índice ascendente
        ("anio", "1")              # Índice ascendente
    ]
}
