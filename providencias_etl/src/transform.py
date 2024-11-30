import logging
from typing import List, Tuple, Dict
from datetime import datetime
import json
from pathlib import Path
import re
from config.config import PROCESSED_DIR, LOGS_DIR

logger = logging.getLogger(__name__)

class ProvidenciaTransformer:
    def __init__(self):
        self.transformation_metrics = {
            "start_time": None,
            "end_time": None,
            "total_processed": 0,
            "successful_transformations": 0,
            "failed_transformations": 0,
            "tipos_encontrados": {}
        }

    def get_tipo_providencia(self, filename: str) -> str:
        """
        Determina el tipo de providencia basado en el prefijo.
        """
        prefix = filename[0].upper()
        tipos = {
            'C': 'Constitucionalidad',
            'A': 'Auto',
            'T': 'Tutela'
        }
        tipo = tipos.get(prefix, 'Desconocido')
        
        # Actualizar métricas
        self.transformation_metrics["tipos_encontrados"][tipo] = \
            self.transformation_metrics["tipos_encontrados"].get(tipo, 0) + 1
            
        return tipo

    def extract_metadata(self, filename: str) -> Dict:
        """
        Extrae metadata del nombre del archivo.
        Ejemplo: A742-24 -> tipo: Auto, numero: 742, anio: 24
        """
        try:
            pattern = r"([CAT])-?(\d+)-(\d+)"
            match = re.match(pattern, filename)
            
            if match:
                tipo_prefix, numero, anio = match.groups()
                return {
                    "tipo": self.get_tipo_providencia(filename),
                    "numero": numero,
                    "anio": anio
                }
            else:
                # Si el formato no coincide, intentar extraer partes
                parts = re.split(r'[-_]', filename)
                return {
                    "tipo": self.get_tipo_providencia(parts[0]),
                    "numero": parts[1] if len(parts) > 1 else "0000",
                    "anio": parts[2] if len(parts) > 2 else "0000"
                }
        except Exception as e:
            logger.error(f"Error extrayendo metadata de {filename}: {str(e)}")
            return {
                "tipo": "Desconocido",
                "numero": "0000",
                "anio": "0000"
            }

    def clean_text(self, text: str) -> str:
        """
        Limpia y normaliza el texto extraído.
        """
        if not text:
            return ""
            
        try:
            # Limpieza básica
            text = text.strip()
            text = ' '.join(text.split())
            
            # Normalizar caracteres especiales
            replacements = {
                '"': '"',
                '"': '"',
                ''': "'",
                ''': "'",
                '…': '...',
                '\u200b': '',
                '\xa0': ' ',
                '´': "'",
                '`': "'"
            }
            
            for old, new in replacements.items():
                text = text.replace(old, new)
            
            return text
            
        except Exception as e:
            logger.error(f"Error en limpieza de texto: {str(e)}")
            return text

    def transform_record(self, record: Tuple[str, str]) -> Dict:
        """
        Transforma un registro al formato requerido:
        { 
            "providencia": "C-411-22",
            "tipo": "Constitucionalidad",
            "anio": "2022",
            "texto": "Texto extraído..."
        }
        """
        filename, text = record
        
        try:
            metadata = self.extract_metadata(filename)
            cleaned_text = self.clean_text(text)
            
            # Crear documento en el formato requerido
            transformed = {
                "providencia": filename,
                "tipo": metadata["tipo"],
                "anio": metadata["anio"],
                "texto": cleaned_text
            }
            
            self.transformation_metrics["successful_transformations"] += 1
            return transformed
            
        except Exception as e:
            logger.error(f"Error transformando registro {filename}: {str(e)}")
            self.transformation_metrics["failed_transformations"] += 1
            return None

    def transform_records(self, records: List[Tuple[str, str]]) -> List[Dict]:
        """
        Transforma todos los registros.
        """
        self.transformation_metrics["start_time"] = datetime.now()
        self.transformation_metrics["total_processed"] = len(records)
        
        transformed_records = []
        
        for record in records:
            transformed = self.transform_record(record)
            if transformed:
                transformed_records.append(transformed)
        
        self.transformation_metrics["end_time"] = datetime.now()
        self._save_metrics()
        
        logger.info(f"Transformación completada: {len(transformed_records)} registros exitosos")
        return transformed_records

    def _save_metrics(self):
        """
        Guarda las métricas de transformación.
        """
        metrics_file = LOGS_DIR / "transformation_metrics.json"
        
        metrics = {
            "fecha_ejecucion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tiempo_total": str(self.transformation_metrics["end_time"] - 
                              self.transformation_metrics["start_time"]),
            "total_procesados": self.transformation_metrics["total_processed"],
            "transformaciones_exitosas": self.transformation_metrics["successful_transformations"],
            "transformaciones_fallidas": self.transformation_metrics["failed_transformations"],
            "tipos_encontrados": self.transformation_metrics["tipos_encontrados"],
            "tasa_exito": (
                self.transformation_metrics["successful_transformations"] /
                self.transformation_metrics["total_processed"] * 100
                if self.transformation_metrics["total_processed"] > 0 else 0
            )
        }
        
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=4, ensure_ascii=False)