from pydub import AudioSegment
import json
import time
import speech_recognition as sr
from pathlib import Path
import logging
from tqdm import tqdm
import multiprocessing as mp
from functools import reduce
import os
from datetime import datetime
from config.config import EXTRACTION_CONFIG, AUDIO_CONFIG, LOGS_DIR

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=str(LOGS_DIR / 'extraction.log')
)
logger = logging.getLogger(__name__)

class AudioExtractor:
    def __init__(self, audio_dir):
        self.audio_dir = Path(audio_dir)
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.pause_threshold = 0.8
        self.recognizer.dynamic_energy_threshold = True
        
        self.metrics = {
            "start_time": None,
            "end_time": None,
            "total_files": 0,
            "successful_extractions": 0,
            "failed_extractions": 0
        }

    def map_chunk(self, chunk_data):
        """
        Función Map: Procesa un chunk individual y retorna su texto.
        """
        chunk, chunk_number, total_chunks, file_name = chunk_data
        temp_path = None
        try:
            # Guardar chunk temporalmente
            temp_path = f"temp_chunk_{file_name}_{chunk_number}.wav"
            chunk.export(
                temp_path, 
                format="wav", 
                parameters=["-ar", "16000"]
            )
            
            # Procesar con speech recognition
            with sr.AudioFile(temp_path) as source:
                audio_recorded = self.recognizer.record(source)
                text = self.recognizer.recognize_google(
                    audio_recorded,
                    language="es-ES"
                )
                return {
                    'chunk_number': chunk_number,
                    'text': text,
                    'success': True
                }
                
        except Exception as e:
            logger.error(f"Error en chunk {chunk_number} de {file_name}: {str(e)}")
            return {
                'chunk_number': chunk_number,
                'text': "",
                'success': False
            }
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    @staticmethod
    def reduce_chunks(results):
        """
        Función Reduce: Combina los resultados de los chunks.
        """
        # Ordenar por número de chunk
        sorted_results = sorted(results, key=lambda x: x['chunk_number'])
        # Concatenar textos
        combined_text = " ".join(r['text'] for r in sorted_results if r['success'])
        # Calcular métricas
        success_count = sum(1 for r in results if r['success'])
        return {
            'text': combined_text,
            'total_chunks': len(results),
            'successful_chunks': success_count
        }

    def process_file_mapreduce(self, audio_path):
        """
        Procesa un archivo usando MapReduce.
        """
        try:
            # Cargar y preparar audio
            audio = AudioSegment.from_wav(str(audio_path))
            if audio.channels > 1:
                audio = audio.set_channels(1)
            audio = audio.normalize()
            
            # Dividir en chunks
            chunk_length_ms = 300000  # 5 minutos
            chunks = [
                audio[i:i + chunk_length_ms]
                for i in range(0, len(audio), chunk_length_ms)
            ]
            
            file_name = Path(audio_path).stem
            total_chunks = len(chunks)
            
            # Preparar datos para map
            chunk_data = [
                (chunk, i+1, total_chunks, file_name)
                for i, chunk in enumerate(chunks)
            ]
            
            # Fase Map: Procesar chunks en paralelo
            with mp.Pool(processes=mp.cpu_count()-1) as pool:
                map_results = list(tqdm(
                    pool.imap(self.map_chunk, chunk_data),
                    total=len(chunk_data),
                    desc=f"Procesando {file_name}"
                ))
            
            # Fase Reduce: Combinar resultados
            reduced_result = self.reduce_chunks(map_results)
            
            # Guardar resultado
            if reduced_result['text']:
                output_file = LOGS_DIR / f"texto_{file_name}.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(reduced_result['text'])
                
                return {
                    "filename": file_name,
                    "raw_text": reduced_result['text'],
                    "total_chunks": reduced_result['total_chunks'],
                    "successful_chunks": reduced_result['successful_chunks']
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error procesando {audio_path}: {str(e)}")
            return None

    def process_all_files(self):
        """
        Procesa todos los archivos usando MapReduce.
        """
        try:
            self.metrics["start_time"] = datetime.now()
            
            audio_files = list(self.audio_dir.glob('*.wav'))
            self.metrics["total_files"] = len(audio_files)
            
            if not audio_files:
                return []
            
            results = []
            
            # Procesar archivos secuencialmente, pero chunks en paralelo
            for audio_file in tqdm(audio_files, desc="Procesando archivos"):
                logger.info(f"Procesando: {audio_file.name}")
                result = self.process_file_mapreduce(audio_file)
                
                if result:
                    results.append((result["filename"], result["raw_text"]))
                    self.metrics["successful_extractions"] += 1
                else:
                    self.metrics["failed_extractions"] += 1
            
            self.metrics["end_time"] = datetime.now()
            
            # Guardar métricas
            self._save_metrics()
            
            return results
            
        except Exception as e:
            logger.error(f"Error en extracción: {str(e)}")
            return []

    def _save_metrics(self):
        """
        Guarda métricas del proceso.
        """
        metrics_file = LOGS_DIR / "extraction_metrics.json"
        
        try:
            tasa_exito = (
                self.metrics["successful_extractions"] / 
                self.metrics["total_files"] * 100
            ) if self.metrics["total_files"] > 0 else 0
        except ZeroDivisionError:
            tasa_exito = 0
        
        metrics = {
            "fecha_ejecucion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tiempo_total": str(self.metrics["end_time"] - self.metrics["start_time"]),
            "total_archivos": self.metrics["total_files"],
            "extracciones_exitosas": self.metrics["successful_extractions"],
            "extracciones_fallidas": self.metrics["failed_extractions"],
            "tasa_exito": f"{tasa_exito:.2f}%"
        }

        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=4, ensure_ascii=False)