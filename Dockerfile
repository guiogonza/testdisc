# Imagen base de Python
FROM python:3.11-slim

# Metadatos
LABEL maintainer="Recursos Humanos"
LABEL description="Plataforma de Evaluaciones Psicométricas (DISC y VALANTI)"

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema para matplotlib y reportlab
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libfreetype6-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar archivos de la aplicación
COPY app.py valanti_app.py disc_style.py database.py ./
COPY questions_es.json questions.json ./
COPY disc_descriptions_es.json disc_descriptions.json ./
COPY streangths.json ./

# Crear directorio para la base de datos
RUN mkdir -p /app/data

# Exponer puerto de Streamlit
EXPOSE 8501

# Comando para ejecutar la aplicación
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.fileWatcherType=none", \
     "--browser.gatherUsageStats=false"]
