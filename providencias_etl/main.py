import logging
import json
import time
from pathlib import Path
from datetime import datetime
from src.extract import AudioExtractor
from src.transform import ProvidenciaTransformer
from src.load import MongoLoader
from config.config import MONGODB_CONFIG

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='etl_pipeline.log'
)
logger = logging.getLogger(__name__)

class ETLPipeline:
    def __init__(self, audio_dir: str, mongodb_uri: str):
        self.audio_dir = audio_dir
        self.mongodb_uri = mongodb_uri
        self.start_time = None
        self.end_time = None

    def _save_metrics(self, extracted_count, transformed_count, loaded_count):
        """
        Guarda métricas de rendimiento del pipeline.
        """
        metrics = {
            "fecha_ejecucion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tiempo_total": f"{self.end_time - self.start_time:.2f} segundos",
            "archivos_extraidos": extracted_count,
            "registros_transformados": transformed_count,
            "documentos_cargados": loaded_count,
            "tasa_exito": f"{(loaded_count/extracted_count)*100:.2f}%"
        }

        with open('etl_metrics.json', 'w') as f:
            json.dump(metrics, f, indent=4)

    def run(self):
        """
        Ejecuta el pipeline ETL con métricas y manejo de errores mejorado.
        """
        try:
            self.start_time = time.time()
            
            # Inicializar componentes
            extractor = AudioExtractor(self.audio_dir)
            transformer = ProvidenciaTransformer()
            loader = MongoLoader(self.mongodb_uri)
            
            logger.info("Iniciando pipeline ETL")
            
            # Extract
            logger.info("Iniciando extracción...")
            extracted_records = extractor.process_all_files()
            extracted_count = len(extracted_records)
            logger.info(f"Extracción completada. {extracted_count} registros extraídos")
            
            # Transform
            logger.info("Iniciando transformación...")
            transformed_records = transformer.transform_records(extracted_records)
            transformed_count = len(transformed_records)
            logger.info(f"Transformación completada. {transformed_count} registros transformados")
            
            # Load
            logger.info("Iniciando carga...")
            loader.load_documents(transformed_records)
            loader.create_indexes()
            loaded_count = transformed_count  # Asumiendo que todos se cargan exitosamente
            logger.info("Carga completada")
            
            # Limpieza y métricas
            loader.close_connection()
            self.end_time = time.time()
            self._save_metrics(extracted_count, transformed_count, loaded_count)
            
            logger.info("Pipeline ETL completado exitosamente")
            print(f"\nPipeline completado exitosamente!")
            print(f"Tiempo total: {self.end_time - self.start_time:.2f} segundos")
            print(f"Ver etl_metrics.json para más detalles")
            
        except Exception as e:
            logger.error(f"Error en el pipeline ETL: {str(e)}")
            raise

def main():
    # Configuración
    AUDIO_DIR = "C:/Users/JsBeltran/OneDrive - ucentral.edu.co/Bigdata/DataSet"
    MONGODB_URI = "mongodb+srv://jbeltranp3:B3ltr4n96j@cluster0.8i802.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    
    pipeline = ETLPipeline(AUDIO_DIR, MONGODB_URI)
    pipeline.run()

if __name__ == "__main__":
    main()
