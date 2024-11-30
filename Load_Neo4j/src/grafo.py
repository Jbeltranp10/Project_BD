import json
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de Neo4j
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USUARIO = os.getenv('NEO4J_USUARIO')
NEO4J_CONTRASEÑA = os.getenv('NEO4J_CONTRASEÑA')

def cargar_grafo_desde_json():
    # Conexión a Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USUARIO, NEO4J_CONTRASEÑA))

    try:
        # Leer el archivo JSON
        ruta_json = os.path.join(os.path.dirname(__file__), "../data/Similitud.json")
        with open(ruta_json, 'r', encoding='utf-8') as archivo:
            datos = json.load(archivo)

        # Crear relaciones en el grafo
        def crear_grafo(tx, providencia1, providencia2, index_simm):
            tx.run("""
                MERGE (p1:Providencia {nombre: $providencia1})
                MERGE (p2:Providencia {nombre: $providencia2})
                MERGE (p1)-[r:SIMILITUD {valor: $index_simm}]->(p2)
            """, providencia1=providencia1, providencia2=providencia2, index_simm=index_simm)

        with driver.session() as session:
            for documento in datos:
                providencia1 = documento['providencia1']
                providencia2 = documento['providencia2']
                index_simm = documento['index_simm']
                session.execute_write(crear_grafo, providencia1, providencia2, index_simm)
                print(f"Relación creada entre {providencia1} y {providencia2} con índice {index_simm}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == '__main__':
    cargar_grafo_desde_json()