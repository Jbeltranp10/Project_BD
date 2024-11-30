from pymongo import MongoClient, UpdateOne, ASCENDING, TEXT
from typing import List, Dict
import logging
from datetime import datetime
from config.config import MONGODB_CONFIG, LOGS_DIR

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MongoLoader:
    def __init__(self, mongodb_uri):
        self.client = MongoClient(mongodb_uri)
        self.db = self.client[MONGODB_CONFIG["DB_NAME"]]
        self.collection = self.db[MONGODB_CONFIG["COLLECTION_NAME"]]
        self.metrics = {
            "start_time": None,
            "end_time": None,
            "successful": 0,
            "failed": 0
        }

    def prepare_document(self, doc: Dict) -> Dict:
        """
        Prepara el documento para MongoDB en el formato requerido.
        """
        return {
            "providencia": doc["providencia"],
            "tipo": doc["tipo"],
            "anio": (f'20{doc["anio"]}'),
            "texto": doc["texto"]
        }

    def load_documents(self, documents: List[Dict], batch_size: int = 100):
        """
        Carga documentos en MongoDB usando procesamiento por lotes.
        """
        self.metrics["start_time"] = datetime.now()
        
        try:
            # Preparar documentos
            processed_docs = [self.prepare_document(doc) for doc in documents]
            
            # Crear operaciones de bulk
            operations = [
                UpdateOne(
                    {"providencia": doc["providencia"]},
                    {"$set": doc},
                    upsert=True
                )
                for doc in processed_docs
            ]
            
            # Procesar en lotes
            for i in range(0, len(operations), batch_size):
                batch = operations[i:i + batch_size]
                try:
                    result = self.collection.bulk_write(batch, ordered=False)
                    self.metrics["successful"] += result.upserted_count + result.modified_count
                except Exception as e:
                    logger.error(f"Error en lote: {str(e)}")
                    self.metrics["failed"] += len(batch)
            
            self.metrics["end_time"] = datetime.now()
            duration = (self.metrics["end_time"] - self.metrics["start_time"]).total_seconds()
            
            logger.info(
                f"Carga completada en {duration:.2f}s: "
                f"{self.metrics['successful']} exitosos, "
                f"{self.metrics['failed']} fallidos"
            )
            
        except Exception as e:
            logger.error(f"Error en carga: {str(e)}")
            raise

    def create_indexes(self):
        """
        Crea índices necesarios si no existen.
        """
        try:
            # Índices básicos
            self.collection.create_index([("texto", TEXT)])
            self.collection.create_index([
                ("tipo", ASCENDING), 
                ("anio", ASCENDING)
            ])
            logger.info("Índices creados exitosamente")
        except Exception as e:
            logger.error(f"Error creando índices: {str(e)}")

    def close_connection(self):
        """
        Cierra la conexión con MongoDB.
        """
        self.client.close()
        logger.info("Conexión cerrada")