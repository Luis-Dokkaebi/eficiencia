# Sistema de Rastreo de Personas y Análisis de Eficiencia

Este proyecto es un sistema completo de visión por computadora para rastrear personas, identificar rostros y analizar la eficiencia en zonas específicas utilizando cámaras de seguridad.

## Requisitos Previos

Para ejecutar este proyecto de la manera más sencilla, necesitas tener instalado:

*   **Docker** y **Docker Compose** (Recomendado)
    *   [Descargar Docker Desktop para Windows/Mac/Linux](https://www.docker.com/products/docker-desktop/)
    *   *Nota: Docker Desktop ya incluye Docker Compose.*
*   **Git** (para clonar el repositorio)

Si prefieres ejecutarlo manualmente (sin Docker), necesitarás:
*   Python 3.10+
*   PostgreSQL 15+

---

## 🚀 Ejecución Rápida con Docker (Recomendado)

Sigue estos pasos para levantar todo el sistema (Base de datos, API, Dashboard y Procesamiento de Video).

### 1. Configuración del Entorno

Primero, crea tu archivo de variables de entorno `.env` copiando el ejemplo proporcionado:

```bash
cp .env.example .env
```

Abre el archivo `.env` y asegúrate de configurar las cámaras. Busca la variable `CAMERAS_JSON`:

```ini
# Ejemplo para una cámara RTSP y una webcam local (índice 0)
CAMERAS_JSON='["rtsp://usuario:password@192.168.1.100:554/stream", 0]'
```

### 2. Construir e Iniciar los Servicios

Ejecuta el siguiente comando en la terminal dentro de la carpeta del proyecto:

```bash
docker-compose up --build
```

Esto descargará las imágenes necesarias, compilará el código e iniciará todos los servicios. Verás los logs de cada servicio en la terminal.

### 3. Crear Usuario Administrador

Para acceder a las funciones protegidas de la API y el Dashboard, necesitas crear un usuario administrador. Abre **otra terminal** y ejecuta:

```bash
# Sintaxis: docker-compose exec api python src/auth/create_admin.py <usuario> <contraseña>
docker-compose exec api python src/auth/create_admin.py admin admin123
```

### 4. Acceder al Sistema

Una vez que todo esté corriendo:

*   **Dashboard (Visualización):** [http://localhost:8501](http://localhost:8501)
*   **API (Documentación Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Base de Datos (Postgres):** Puerto `5432`

---

## 🛠 Ejecución Manual (Para Desarrollo)

Si prefieres correr cada componente por separado en tu máquina local:

### 1. Preparar Entorno Python

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno (Windows)
venv\Scripts\activate
# Activar entorno (Linux/Mac)
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Base de Datos

Necesitas tener un servidor PostgreSQL corriendo localmente.
Asegúrate de crear una base de datos llamada `tracking_db` (o cambia el nombre en tu `.env`).

Inicializa las tablas:
```bash
python src/storage/init_db.py
```

Crea el usuario admin:
```bash
python src/auth/create_admin.py admin admin123
```

### 3. Ejecutar Componentes

Necesitarás 3 terminales diferentes:

**Terminal 1: API**
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2: Dashboard**
```bash
streamlit run src/dashboard/app.py
```

**Terminal 3: Procesamiento de Video (Tracker)**
```bash
python src/main.py
```

---

## Solución de Problemas

*   **El Dashboard muestra "No cameras detected":**
    *   Asegúrate de que el contenedor `api` esté corriendo y respondiendo en `http://localhost:8000/cameras`.
    *   Verifica que hayas creado el usuario administrador, ya que la API requiere autenticación. (Nota: Actualmente el dashboard podría requerir ajustes para enviar el token de autenticación correctamente).

*   **Error de conexión a Base de Datos:**
    *   Verifica que las credenciales en `.env` (POSTGRES_USER, POSTGRES_PASSWORD) coincidan con tu configuración de Docker o local.

*   **Cámaras no conectan:**
    *   Revisa la URL RTSP en `CAMERAS_JSON`.
    *   Si usas una webcam local (índice 0) con Docker, necesitas pasar el dispositivo al contenedor (esto requiere configuración extra en `docker-compose.yml`, como `devices: - /dev/video0:/dev/video0`).
