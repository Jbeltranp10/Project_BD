from flask import Flask, render_template
from routes.search import search_bp
from routes.similitudes import similitudes_bp
from config.mongodb_config import MONGODB_CONFIG
from config.neo4j_config import URI,AUTH
from pymongo import MongoClient, ASCENDING, TEXT
from neo4j import GraphDatabase
import logging
import os
from datetime import datetime
import pandas as pd

# Crear directorio para logs
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Configurar logging
log_filename = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('BigMongoData')

app = Flask(__name__)
app.register_blueprint(search_bp)
app.register_blueprint(similitudes_bp)

def init_mongodb():
    """Inicializa la conexión con MongoDB y crea los índices necesarios."""
    try:
        logger.info("Iniciando conexión con MongoDB...")
        client = MongoClient(MONGODB_CONFIG["URI"])
        db = client[MONGODB_CONFIG["DB_NAME"]]
        collection = db[MONGODB_CONFIG["COLLECTION_NAME"]]
        
        logger.info("Comenzando creación de índices en MongoDB...")
        indices_creados = []
        
        # Crear índices
        collection.create_index([("texto", TEXT)])
        collection.create_index([("providencia", ASCENDING)])
        collection.create_index([("tipo", ASCENDING)])
        collection.create_index([("anio", ASCENDING)])
        collection.create_index([
            ("tipo", ASCENDING),
            ("anio", ASCENDING)
        ])
        
        logger.info("Índices creados correctamente")
        db.command('ping')
        return True
        
    except Exception as e:
        logger.error(f"Error inicializando MongoDB: {str(e)}", exc_info=True)
        return False

def init_neo4j():
    """Inicializa la conexión con Neo4j."""
    try:
        logger.info("Iniciando conexión con Neo4j...")
        
        with GraphDatabase.driver(URI,auth=AUTH) as driver:
            logger.info(driver)
        
            # Verificar conectividad de manera más robusta
            try:
                driver.verify_connectivity()
                logger.info("Verificación de conectividad exitosa")
                
                # Realizar una prueba adicional con una consulta simple
                with driver.session() as session:
                    result = session.run("RETURN 1 as test")
                    test_value = result.single()
                    if test_value and test_value.get('test') == 1:
                        logger.info("Prueba de consulta exitosa")
                        return driver
                    else:
                        raise Exception("La prueba de consulta no retornó el valor esperado")
                        
            except Exception as inner_e:
                logger.error(f"Error en verificación de conectividad: {str(inner_e)}")
                if driver:
                    driver.close()
                raise
            
    except Exception as e:
        logger.error(f"Error inicializando Neo4j: {str(e)}")
        return None

@app.route('/')
def home():
    """Ruta principal de la aplicación."""
    logger.info("Acceso a la página principal")
    try:
        return render_template('pages/index.html')
    except Exception as e:
        logger.error(f"Error renderizando template: {str(e)}", exc_info=True)
        return "Error interno del servidor", 500

def verificar_estado_conexiones():
    """Verifica el estado de las conexiones a las bases de datos."""
    status = {
        'mongodb': False,
        'neo4j': False
    }
    
    try:
        # Verificar MongoDB
        client = MongoClient(MONGODB_CONFIG["URI"], serverSelectionTimeoutMS=5000)
        client.server_info()
        status['mongodb'] = True
        logger.info("Conexión MongoDB verificada")
    except Exception as e:
        logger.error(f"Error verificando MongoDB: {str(e)}")

    try:
        # Verificar Neo4j como en Colab
        if app.config.get('NEO4J_DRIVER'):
            with app.config['NEO4J_DRIVER'].session() as session:
                # Consulta de prueba simple
                result = session.run("RETURN 1 as test")
                test_value = result.single()['test']  # Usar nombre de columna en lugar de índice
                if test_value == 1:
                    status['neo4j'] = True
                    logger.info("Conexión Neo4j verificada")
    except Exception as e:
        logger.error(f"Error verificando Neo4j: {str(e)}")

    # Log del estado general de las conexiones
    logger.info(f"Estado de conexiones - MongoDB: {status['mongodb']}, Neo4j: {status['neo4j']}")
    return status

@app.before_request
def check_db_status():
    """Verifica el estado de las bases de datos antes de cada petición."""
    status = verificar_estado_conexiones()
    if not all(status.values()):
        logger.error("Una o más bases de datos no están disponibles")

if __name__ == '__main__':
    logger.info("Iniciando aplicación BigMongoData...")
    
    # Inicializar MongoDB
    mongo_ok = init_mongodb()
    if not mongo_ok:
        logger.critical("Error crítico - MongoDB no disponible")
        exit(1)
        
    # Inicializar Neo4j
    neo4j_driver = init_neo4j()
    if not neo4j_driver:
        logger.critical("Error crítico - Neo4j no disponible")
        exit(1)
        
    # Compartir conexión Neo4j con blueprint de similitudes
    app.config['NEO4J_DRIVER'] = neo4j_driver
    
    try:
        logger.info("Iniciando servidor Flask...")
        app.run(debug=True)
    finally:
        logger.info("Cerrando conexiones...")
        if neo4j_driver:
            neo4j_driver.close()