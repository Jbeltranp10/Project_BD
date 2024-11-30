# Buscador de Providencias Jurídicas
## Descripción
Aplicación web para la búsqueda, análisis y visualización de relaciones entre providencias jurídicas. El sistema permite realizar búsquedas avanzadas, analizar similitudes entre documentos y visualizar relaciones mediante grafos interactivos.
## Requisitos Previos

Python 3.8 o superior
MongoDB
Neo4j
Navegador web moderno (Chrome, Firefox, Edge)

## Instalación y Configuración
1. Clonar el Repositorio
bashCopygit clone [url-del-repositorio]
cd flaskapi-mongodb-main
2. Configurar Entorno Virtual Python
bashCopy# Crear entorno virtual
python -m venv venv

## Activar entorno virtual
### En Windows:
venv\Scripts\activate
### En Linux/Mac:
source venv/bin/activate

## Instalar dependencias
pip install -r requirements.txt
3. Configurar Bases de Datos
Configuración de MongoDB (config/mongodb_config.py):
pythonCopyMONGODB_CONFIG = {
    "URI": "tu_uri_de_mongodb", 
    "DB_NAME": "relatoria",
    "COLLECTION_NAME": "providencias"
}

## Ejecución de la Aplicación

Asegúrate de que MongoDB está en ejecución
Activa el entorno virtual si no está activado
Ejecuta la aplicación Flask
Accede a la aplicación a través de tu navegador web
