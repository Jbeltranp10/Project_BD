from flask import Blueprint, jsonify, request, current_app
from utils.helpers import format_response
import logging

similitudes_bp = Blueprint('similitudes', __name__)
logger = logging.getLogger(__name__)

def get_graph_data(driver, providencia_id, min_score=0):
    """Obtiene datos del grafo desde Neo4j."""
    try:
        with driver.session() as session:
            query = """
            MATCH path = (p1:Providencia {nombre: $providencia})-[r:SIMILAR_A]->(p2:Providencia)
            WHERE r.index_simm >= $min_score
            WITH p1, p2, r, path
            RETURN 
                collect(distinct {
                    id: id(p1),
                    nombre: p1.nombre,
                    tipo: p1.tipo,
                    anio: p1.anio
                }) + collect(distinct {
                    id: id(p2),
                    nombre: p2.nombre,
                    tipo: p2.tipo,
                    anio: p2.anio
                }) as nodes,
                collect(distinct {
                    source: id(p1),
                    target: id(p2),
                    score: r.index_simm,
                    type: type(r)
                }) as relationships,
                count(r) as total_relations,
                avg(r.index_simm) as avg_similarity,
                max(r.index_simm) as max_similarity
            """
            logger(query)
            result = session.run(query, 
                               providencia=providencia_id,
                               min_score=float(min_score))
            
            record = result.single()
            
            if not record or not record['nodes']:
                return None
                
            return {
                'nodes': record['nodes'],
                'relationships': record['relationships'],
                'stats': {
                    'totalRelations': record['total_relations'],
                    'avgSimilarity': record['avg_similarity'] * 100 if record['avg_similarity'] else 0,
                    'maxSimilarity': record['max_similarity'] * 100 if record['max_similarity'] else 0
                }
            }
            
    except Exception as e:
        logger.error(f"Error en consulta: {str(e)}", exc_info=True)
        raise

def format_node(node):
    """Formatea un nodo para la respuesta."""
    return {
        'id': str(node.id),
        'nombre': node.get('nombre', ''),
        'tipo': node.get('tipo', 'Desconocido')
    }

def format_relationship(rel):
    """Formatea una relación para la respuesta."""
    return {
        'source': str(rel.start_node.id),
        'target': str(rel.end_node.id),
        'score': float(rel.get('index_simm', 0))
    }

@similitudes_bp.route('/api/graph/<providencia>')
def get_graph(providencia):
    try:
        driver = current_app.config.get('NEO4J_DRIVER')
        if not driver:
            return jsonify(format_response("Neo4j no disponible", False)), 503

        # Convertir el score mínimo a decimal
        min_score = float(request.args.get('min_score', 0)) 
        logger.info(f"Buscando grafo para: {providencia} con similitud mínima de {min_score}")

        if not providencia.strip():
            query = """
            MATCH (p1:Providencia)-[r:SIMILAR_A]->(p2:Providencia)
            WHERE toFloat(r.index_simm) >= $min_score
            WITH DISTINCT p1, p2, r
            RETURN 
                collect(DISTINCT {
                    id: elementId(p1),
                    nombre: p1.nombre
                }) + collect(DISTINCT {
                    id: elementId(p2),
                    nombre: p2.nombre
                }) as nodes,
                collect(DISTINCT {
                    source: elementId(p1),
                    target: elementId(p2),
                    score: toFloat(r.index_simm)
                }) as relationships,
                count(DISTINCT r) as total_relations
            """
            params = {"min_score": min_score}
        else:
            query = """
            MATCH path = (p1:Providencia {nombre: $providencia})-[r:SIMILAR_A]->(p2:Providencia)
            WHERE toFloat(r.index_simm) >= $min_score
            WITH DISTINCT p1, p2, r
            RETURN 
                collect(DISTINCT {
                    id: elementId(p1),
                    nombre: p1.nombre
                }) + collect(DISTINCT {
                    id: elementId(p2),
                    nombre: p2.nombre
                }) as nodes,
                collect(DISTINCT {
                    source: elementId(p1),
                    target: elementId(p2),
                    score: toFloat(r.index_simm)
                }) as relationships,
                count(DISTINCT r) as total_relations
            """
            params = {"providencia": providencia, "min_score": min_score}

        with driver.session() as session:
            logger.info(f"Ejecutando consulta con parámetros: {params}")
            result = session.run(query, params)
            record = result.single()
            
            if not record or not record['nodes']:
                # Devolver una respuesta exitosa con datos vacíos en lugar de error 404
                return jsonify(format_response({
                    'nodes': [],
                    'relationships': [],
                    'stats': {
                        'totalRelations': 0,
                        'totalNodes': 0
                    }
                }))

            # El resto del código permanece igual
            nodes = list({node['id']: node for node in record['nodes']}.values())
            relationships = []
            seen = set()
            
            for rel in record['relationships']:
                key = f"{rel['source']}-{rel['target']}"
                if key not in seen:
                    seen.add(key)
                    rel['score'] = float(rel['score'])
                    if rel['score'] >= min_score:
                        relationships.append(rel)

            logger.info(f"Filtrado completado: {len(relationships)} relaciones cumplen el criterio de similitud")

            return jsonify(format_response({
                'nodes': nodes,
                'relationships': relationships,
                'stats': {
                    'totalRelations': len(relationships),
                    'totalNodes': len(nodes)
                }
            }))
            
    except Exception as e:
        logger.error(f"Error procesando solicitud: {str(e)}", exc_info=True)
        return jsonify(format_response(str(e), False)), 500