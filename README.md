# Análisis de Mortalidad en Colombia 2019

## Introducción del proyecto

Esta aplicación web dinámica analiza los datos de mortalidad en Colombia para el año 2019, utilizando herramientas avanzadas de visualización interactiva con Plotly y Dash en Python. La aplicación permite explorar patrones demográficos y regionales a través de diversos gráficos interactivos.

## Objetivo

Proporcionar una herramienta accesible para identificar patrones, tendencias y correlaciones clave en los datos de mortalidad de Colombia, facilitando el análisis visual intuitivo de la información.

## Estructura del proyecto

```
├── app.py                 # Archivo principal de la aplicación Dash
├── requirements.txt       # Dependencias del proyecto
├── README.md             # Documentación del proyecto
├── Anexos/               # Datos fuente
│   ├── Anexo1.NoFetal2019_CE_15-03-23.xlsx    # Datos de mortalidad
│   ├── Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx # Códigos de causas
│   └── Divipola_CE_.xlsx                      # División político-administrativa
├── css/                  # Archivos de estilo (no utilizados en esta versión)
├── js/                   # Archivos JavaScript (no utilizados en esta versión)
├── data/                 # Datos procesados (JSON)
└── screenshots/          # Capturas de pantalla de las visualizaciones
```

## Requisitos

- Python 3.8+
- Librerías especificadas en `requirements.txt`:
  - dash==3.2.0
  - plotly==6.4.0
  - pandas==2.3.3
  - openpyxl==3.1.5
  - numpy==2.2.6
  - gunicorn==21.2.0

## Despliegue

La aplicación puede ser desplegada en diversos servicios en la nube que soporten Python. Para Render:

1. Crear cuenta gratuita en Render
2. Subir el repositorio a GitHub
3. Conectar el repositorio a Render
4. Render detectará automáticamente la configuración desde `render.yaml`
5. La aplicación estará disponible en una URL gratuita

## Software

- **Python**: Lenguaje de programación principal
- **Dash**: Framework para aplicaciones web
- **Plotly**: Librería de visualización interactiva
- **Pandas**: Manipulación y análisis de datos
- **OpenPyXL**: Lectura de archivos Excel

## Instalación

1. Clona el repositorio:
   ```bash
   git clone <url-del-repositorio>
   cd Act04_web-analisis-mortalidad-colombia
   ```

2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Ejecuta la aplicación localmente:
   ```bash
   python app.py
   ```

4. Abre tu navegador en `http://localhost:8050`

## Visualizaciones

La aplicación incluye las siguientes visualizaciones interactivas:

### 1. Mapa de Departamentos
![Mapa Departamentos](screenshots/mapa_departamentos.png)
*Visualización de la distribución total de muertes por departamento en Colombia para el año 2019. Permite identificar las regiones con mayor concentración de mortalidad.*

### 2. Gráfico de Líneas - Muertes por Mes
![Muertes por Mes](screenshots/muertes_mensuales.png)
*Representación del total de muertes por mes en Colombia, mostrando variaciones a lo largo del año. Ayuda a identificar patrones estacionales en la mortalidad.*

### 3. Ciudades Más Violentas
![Ciudades Violentas](screenshots/ciudades_violentas.png)
*Visualización de las 5 ciudades más violentas de Colombia, considerando homicidios. Destaca las áreas con mayor índice de violencia.*

### 4. Ciudades con Menor Mortalidad
![Menor Mortalidad](screenshots/ciudades_seguras.png)
*Muestra las 10 ciudades con menor índice de mortalidad, proporcionando una perspectiva de las zonas más seguras.*

### 5. Tabla de Principales Causas
![Tabla Causas](screenshots/tabla_causas.png)
*Listado de las 10 principales causas de muerte en Colombia, incluyendo código, nombre y total de casos.*

### 6. Gráfico de Barras Apiladas - Muertes por Sexo y Departamento
*Comparación del total de muertes por sexo en cada departamento, para analizar diferencias significativas entre géneros.*

### 7. Histograma - Distribución por Grupos de Edad
*Distribución de muertes agrupando por rangos de edad para identificar patrones de mortalidad a lo largo del ciclo de vida.*

## Datos

Los datos utilizados provienen del DANE (Departamento Administrativo Nacional de Estadística) - Estadísticas Vitales 2019:

- **NoFetal2019.xlsx**: Datos de mortalidad no fetal
- **CodigosDeMuerte.xlsx**: Clasificación internacional de enfermedades
- **Divipola.xlsx**: División político-administrativa de Colombia

## Resultados y Hallazgos

### Estadísticas Generales
- **Total de registros analizados**: 244,355 muertes en 2019
- **Departamentos con mayor mortalidad**: Cundinamarca, Antioquia, Valle del Cauca
- **Principales causas**: Enfermedades cardiovasculares, cáncer, accidentes
- **Distribución por género**: Análisis de diferencias entre hombres y mujeres
- **Grupos etarios más afectados**: Adultos mayores (60+ años) y población infantil