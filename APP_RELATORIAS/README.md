# Buscador de Providencias Jurídicas

## Descripción
Aplicación web para la búsqueda, análisis y visualización de relaciones entre providencias jurídicas. El sistema permite realizar búsquedas avanzadas, analizar similitudes entre documentos y visualizar las relaciones mediante grafos interactivos.

## Requisitos Previos
- Python 3.8 o superior
- MongoDB
- Neo4j
- Navegador web moderno (Chrome, Firefox, Edge)

## Instalación y Configuración

### 1. Clonar el Repositorio
```bash
git clone https://github.com/Jbeltranp10/Project_BD/tree/main/APP_RELATORIAS
cd flaskapi-mongodb-main
```

### 2. Configurar Entorno Virtual Python
```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar Bases de Datos

#### Configuración de MongoDB (`config/mongodb_config.py`):
```python
MONGODB_CONFIG = {
    "URI": "tu_uri_de_mongodb",  # Ejemplo: mongodb+srv://usuario:contraseña@cluster0.ejemplo.mongodb.net/
    "DB_NAME": "relatoria",
    "COLLECTION_NAME": "providencias"
}
```

#### Configuración de Neo4j (`config/neo4j_config.py`):
```python
URI = "tu_uri_de_neo4j"  # Ejemplo: neo4j+s://ejemplo.databases.neo4j.io
AUTH = ("tu_usuario_neo4j", "tu_contraseña_neo4j")
```

### 4. Ejecutar la Aplicación
```bash
python app.py
```
La aplicación estará disponible en: `http://localhost:5000`

## Uso de la Aplicación

### Búsqueda de Providencias

1. **Filtros Disponibles:**
   - **Tipo de Providencia:** Seleccionar entre Auto, Constitucionalidad o Tutela
   - **Año:** Ingresar año (hasta 2024)
   - **ID Providencia:** Buscar una providencia específica
   - **Buscar en contenido:** Búsqueda por palabras clave

2. **Visualización de Resultados:**
   - Lista de providencias encontradas
   - Metadatos de cada providencia (tipo, año)
   - Extracto del contenido

3. **Análisis de Similitudes:**
   - Grafo interactivo de relaciones entre providencias
   - Control deslizante para ajustar el porcentaje mínimo de similitud
   - Visualización de las conexiones entre documentos relacionados

### Funcionalidades Principales

#### Búsqueda General
- Utiliza los filtros en la parte superior
- Los resultados se actualizan automáticamente
- Se muestra el número total de documentos encontrados

#### Búsqueda por ID
- Ingresar el ID exacto de la providencia
- Formato: [Letra]-[Número]-[Año]
- Ejemplos: C-123-23, T-456-24, A-789-23

#### Visualización de Similitudes
- Seleccionar una providencia para ver sus relaciones
- Ajustar el porcentaje de similitud con el control deslizante
- Los nodos representan providencias
- Las líneas muestran el porcentaje de similitud


## Solución de Problemas Comunes

### 1. Error de Conexión a MongoDB
- Verificar URI en `mongodb_config.py`
- Comprobar credenciales
- Verificar acceso a la red/VPN si es necesario

### 2. Error de Conexión a Neo4j
- Verificar URI y credenciales en `neo4j_config.py`
- Comprobar que el servidor Neo4j esté activo
- Verificar permisos de usuario

### 3. Problemas con la Búsqueda
- Verificar formato correcto de ID de providencia
- Año debe ser 2024 o anterior
- Mínimo 3 caracteres para búsqueda en contenido

### 4. Visualización del Grafo
- Limpiar caché del navegador si no se muestra
- Verificar que no haya bloqueadores de JavaScript
- Usar navegador compatible (Chrome recomendado)

## Notas Importantes
- La aplicación limita las búsquedas al año 2024 y anteriores
- Las búsquedas por contenido requieren mínimo 3 caracteres
- El grafo se actualiza automáticamente al ajustar el porcentaje de similitud
- Los resultados se actualizan en tiempo real al modificar los filtros

