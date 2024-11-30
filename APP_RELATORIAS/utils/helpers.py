import re
from datetime import datetime
from typing import Dict, Any, Union
import logging
logger = logging.getLogger(__name__)

def validate_providencia_format(providencia: str) -> bool:
    """
    Valida que el formato de la providencia sea correcto.
    Formatos válidos: 
    - AXXX-YY (Autos, sin guion después de A)
    - C-XXX-YY (Constitucionalidad)
    - T-XXX-YY (Tutela)
    donde:
    - XXX es el número de providencia (1-4 dígitos)
    - YY es el año (2 dígitos)
    """
    if not providencia:
        return False

    try:
        # Caso especial para Autos
        if providencia.startswith('A'):
            # Format: AXXX-YY
            parts = providencia.split('-')
            if len(parts) != 2:
                return False
                
            # Validar número después de A
            numero = parts[0][1:]  # Obtener números después de A
            if not numero.isdigit() or len(numero) > 4:
                return False
                
            # Validar año
            if not parts[1].isdigit() or len(parts[1]) != 2:
                return False
                
            return True
            
        # Para C y T (mantienen el formato con dos guiones)
        else:
            parts = providencia.split('-')
            if len(parts) != 3:
                return False
                
            # Validar primera letra
            if parts[0] not in ['C', 'T']:
                return False
                
            # Validar número de providencia
            if not parts[1].isdigit() or len(parts[1]) > 4:
                return False
                
            # Validar año
            if not parts[2].isdigit() or len(parts[2]) != 2:
                return False
                
            return True
            
    except Exception as e:
        logger.error(f"Error validando formato de providencia: {str(e)}")
        return False

def format_response(data: Any, success: bool = True) -> Dict:
    """
    Formatea la respuesta de la API de manera consistente.
    Args:
        data: Datos a retornar
        success: Indica si la operación fue exitosa
    Returns:
        Diccionario con formato estándar de respuesta
    """
    return {
        "success": success,
        "timestamp": datetime.now().isoformat(),
        "data": data if success else None,
        "error": data if not success else None
    }

def clean_query_params(params: Dict) -> Dict:
    """
    Limpia y valida los parámetros de búsqueda.
    Elimina parámetros inválidos y valida los valores.
    Args:
        params: Diccionario de parámetros de búsqueda
    Returns:
        Diccionario con parámetros limpios y validados
    """
    cleaned = {}
    
    # Validar tipo de providencia
    if 'tipo' in params and params['tipo'] and params['tipo'] != 'Todos los tipos':
        cleaned['tipo'] = params['tipo']
    
    # Validar año
    if 'anio' in params and params['anio']:
        try:
            year = int(params['anio'])
            current_year = 2024  # Año máximo permitido
            if 1900 <= year <= current_year:
                cleaned['anio'] = str(year)
            else:
                # Si el año es mayor a 2024, no incluimos el parámetro
                # esto hará que la búsqueda no retorne resultados
                pass
        except ValueError:
            pass
    
    # Validar texto de búsqueda
    if 'texto' in params and params['texto'] and len(params['texto'].strip()) >= 3:
        cleaned['texto'] = params['texto'].strip()
    
    return cleaned

def calculate_similarity_score(texto1: str, texto2: str) -> float:
    """
    Calcula un score de similitud entre dos textos.
    Implementación básica basada en superposición de palabras.
    """
    if not texto1 or not texto2:
        return 0.0
        
    # Convertir textos a conjuntos de palabras
    words1 = set(texto1.lower().split())
    words2 = set(texto2.lower().split())
    
    # Calcular intersección y unión
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    # Retornar coeficiente de Jaccard
    return intersection / union if union > 0 else 0.0