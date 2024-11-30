from flask import Blueprint, request, jsonify
from bson.json_util import dumps
import json
import logging
from config.mongodb_config import MONGODB_CONFIG
from pymongo import MongoClient
from utils.helpers import validate_providencia_format, format_response, clean_query_params

# Configuración del logger
logger = logging.getLogger(__name__)

# Crear blueprint para las rutas de búsqueda
search_bp = Blueprint('search', __name__)

# Inicializar conexión con MongoDB
client = MongoClient(MONGODB_CONFIG["URI"])
db = client[MONGODB_CONFIG["DB_NAME"]]
collection = db[MONGODB_CONFIG["COLLECTION_NAME"]]
logger.info("Conexión a MongoDB inicializada")

@search_bp.route('/api/providencia/<id>')
def get_providencia(id):
    """
    Endpoint para buscar una providencia específica por su ID.
    Si el ID está vacío, devuelve todos los documentos sin filtro.
    """
    logger.info(f"Búsqueda de providencia específica: {id}")
    try:
        # Si el ID es vacío, devuelve todos los documentos
        if not id.strip():
            logger.info("ID vacío, devolviendo todos los documentos")
            results = list(collection.find({}, {"_id": False}))
            return dumps(format_response(results)), 200

        # Validar formato de ID
        if not validate_providencia_format(id):
            logger.warning(f"Formato de ID inválido: {id}")
            return jsonify(format_response("Formato de ID inválido", False)), 400

        # Buscar documento específico
        result = collection.find_one(
            {"providencia": id},
            {
                "providencia": True,
                "tipo": True,
                "anio": True,
                "texto": True,
                "_id": False
            }
        )
        if result:
            logger.info(f"Providencia encontrada: {id}")
        else:
            logger.info(f"Providencia no encontrada: {id}")
        return dumps(format_response(result))
    except Exception as e:
        logger.error(f"Error buscando providencia {id}: {str(e)}", exc_info=True)
        return jsonify(format_response(str(e), False)), 500

@search_bp.route('/api/search')
def search():
    """
    Endpoint para búsqueda general con múltiples criterios.
    Soporta búsqueda por tipo, año, texto y maneja formatos especiales de providencias.
    """
    logger.info("Iniciando búsqueda general")
    try:
        # Registrar parámetros recibidos
        logger.debug(f"Parámetros recibidos: {request.args}")
        
        # Limpiar y validar parámetros
        query_params = clean_query_params(request.args.to_dict())
        logger.info(f"Parámetros limpios: {query_params}")
        
        # Definir proyección base
        projection = {
            "providencia": True,
            "tipo": True,
            "anio": True,
            "texto": True,
            "_id": False
        }
        
        query = {}
        
        # Construir query
        if 'tipo' in query_params and query_params['tipo']:
            if query_params['tipo'] == 'Auto':
                query['providencia'] = {'$regex': '^A[0-9]{1,4}-[0-9]{2}$'}
            elif query_params['tipo'] == 'Constitucionalidad':
                query['providencia'] = {'$regex': '^C-[0-9]{1,4}-[0-9]{2}$'}
            elif query_params['tipo'] == 'Tutela':
                query['providencia'] = {'$regex': '^T-[0-9]{1,4}-[0-9]{2}$'}
            query['tipo'] = query_params['tipo']
            logger.debug(f"Añadido filtro de tipo: {query_params['tipo']}")
            
        if 'anio' in query_params and query_params['anio']:
            # Convertir a string para comparación consistente
            query['anio'] = str(query_params['anio'])
            logger.debug(f"Añadido filtro de año: {query_params['anio']}")
            
        if 'texto' in query_params and query_params['texto']:
            query['$text'] = {'$search': query_params['texto']}
            projection['score'] = {'$meta': 'textScore'}
            logger.debug(f"Añadida búsqueda de texto: {query_params['texto']}")
        
        logger.info(f"Query final: {query}")
        
        # Ejecutar búsqueda
        results = collection.find(query, projection)
        
        # Ordenar por score si hay búsqueda de texto
        if 'texto' in query_params and query_params['texto']:
            results = results.sort([('score', {'$meta': 'textScore'})])
        else:
            # Ordenar por providencia por defecto
            results = results.sort('providencia', 1)
        
        results_list = list(results)
        logger.info(f"Búsqueda completada. Resultados encontrados: {len(results_list)}")
        
        return dumps(format_response(results_list)),len(results_list)
        
    except Exception as e:
        logger.error("Error en búsqueda general", exc_info=True)
        return jsonify(format_response(str(e), False)), 500

@search_bp.route('/api/stats')
def get_stats():
    """
    Endpoint para obtener estadísticas de la colección.
    Incluye total de documentos, distribución por tipo y por año.
    """
    logger.info("Obteniendo estadísticas")
    try:
        stats = {
            'total': collection.count_documents({}),
            'por_tipo': {},
            'por_anio': {}
        }
        
        logger.debug(f"Total de documentos: {stats['total']}")
        
        # Estadísticas por tipo
        pipeline_tipo = [
            {'$group': {'_id': '$tipo', 'count': {'$sum': 1}}},
            {'$sort': {'_id': 1}}
        ]
        for tipo_stat in collection.aggregate(pipeline_tipo):
            stats['por_tipo'][tipo_stat['_id']] = tipo_stat['count']
            logger.debug(f"Conteo para {tipo_stat['_id']}: {tipo_stat['count']}")
            
        # Estadísticas por año
        pipeline_anio = [
            {'$group': {'_id': '$anio', 'count': {'$sum': 1}}},
            {'$sort': {'_id': 1}}
        ]
        for anio_stat in collection.aggregate(pipeline_anio):
            stats['por_anio'][anio_stat['_id']] = anio_stat['count']
            logger.debug(f"Año {anio_stat['_id']}: {anio_stat['count']} documentos")
            
        logger.info("Estadísticas generadas exitosamente")
        return jsonify(format_response(stats))
        
    except Exception as e:
        logger.error("Error generando estadísticas", exc_info=True)
        return jsonify(format_response(str(e), False)), 500

# Asegurar índices al iniciar
def ensure_indexes():
    """
    Crea los índices necesarios en la colección de MongoDB
    """
    try:
        logger.info("Creando índices en MongoDB...")
        
        # Índice de texto para búsqueda en contenido
        collection.create_index([("texto", "text")])
        
        # Índices para campos comunes de búsqueda
        collection.create_index([("providencia", 1)])
        collection.create_index([("tipo", 1)])
        collection.create_index([("anio", 1)])
        
        logger.info("Índices creados exitosamente")
    except Exception as e:
        logger.error(f"Error creando índices: {str(e)}", exc_info=True)

# Crear índices al iniciar la aplicación
ensure_indexes()