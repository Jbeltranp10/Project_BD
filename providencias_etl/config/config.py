import os
from pathlib import Path

# Rutas base
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = BASE_DIR / "logs"

# Asegurar que existan los directorios necesarios
for dir_path in [RAW_DIR, PROCESSED_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Configuración MongoDB
MONGODB_CONFIG = {
    "URI": "mongodb+srv://jbeltranp3:B3ltr4n96j@cluster0.8i802.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
    "DB_NAME": "relatoria",
    "COLLECTION_NAME": "providencias"
}

# Configuración de extracción
EXTRACTION_CONFIG = {
    "BATCH_SIZE": 25,  # Número de archivos por lote
    "N_WORKERS": 25,   # Número de workers para procesamiento paralelo
    "MAX_RETRIES": 3, # Número máximo de intentos para procesar un archivo
    "LANGUAGE": "es-ES"  # Idioma para el reconocimiento de voz
}

# Configuración de logging
LOGGING_CONFIG = {
    "VERSION": 1,
    "HANDLERS": {
        "file": {
            "class": "logging.FileHandler",
            "filename": str(LOGS_DIR / "etl.log"),
            "mode": "a",
            "formatter": "detailed"
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple"
        }
    },
    "FORMATTERS": {
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "simple": {
            "format": "%(levelname)s: %(message)s"
        }
    },
    "ROOT": {
        "level": "INFO",
        "handlers": ["console", "file"]
    }
}

# Configuración de procesamiento de audio
AUDIO_CONFIG = {
    "SAMPLE_RATE": 16000,
    "CHANNELS": 1,
    "TEMP_DIR": PROCESSED_DIR / "temp"
}

# Configuración de índices MongoDB
MONGO_INDEXES = [
    ("texto", "text"),
    ("providencia", 1),
    ("tipo", 1),
    ("anio", 1),
    ("ultima_actualizacion", 1)
]