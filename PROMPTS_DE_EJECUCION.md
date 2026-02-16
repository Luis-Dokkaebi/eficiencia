# Prompts de Ejecución Secuencial

Este documento contiene una serie de **Prompts Maestros** diseñados para ser utilizados secuencialmente con un Agente de IA (como yo). Cada prompt corresponde a una fase crítica del `PLAN_ESTRATEGICO.md` y está optimizado para obtener resultados de código funcionales y robustos, **con especial atención al soporte de múltiples cámaras (5, 10, 20+)**.

## Instrucciones de Uso
Copia y pega el prompt completo en el chat. No saltes pasos, ya que cada uno construye sobre el anterior.

---

## Fase 1: Cimientos y Estabilidad (MVP)

### Paso 1: Configuración Avanzada y Variables de Entorno (Multi-Cámara)
**Objetivo:** Desacoplar la configuración y preparar el sistema para recibir una lista dinámica de cámaras.
**Dificultad:** Baja (⭐)

```markdown
**Rol:** Eres un Ingeniero DevOps Senior especializado en Python.

**Tarea:**
1. Refactoriza el manejo de configuración actual en `config/config.py`.
2. Implementa el uso de `python-dotenv` para cargar variables sensibles desde un archivo `.env`.
3. Crea un archivo `.env.example` que incluya una variable `CAMERAS_JSON` (una lista serializada de strings) para soportar N cámaras, no solo una.
4. Modifica `config.py` para parsear esta lista de cámaras.
5. Asegura que `src/main.py` iteré sobre esta lista de cámaras (aunque por ahora solo procese una o las abra secuencialmente).

**Criterios de Aceptación:**
- El archivo `.env` permite definir `["rtsp://cam1...", "rtsp://cam2...", "rtsp://cam3..."]`.
- El sistema puede leer esta configuración correctamente al inicio.
```

---

### Paso 2: Modularización del Servicio de Video (Multi-Hilo)
**Objetivo:** Evitar que el sistema colapse si una cámara falla y permitir la ingesta paralela de videos.
**Dificultad:** Alta (⭐⭐⭐)

```markdown
**Rol:** Eres un Arquitecto de Software experto en Computer Vision y Concurrencia.

**Tarea:**
1. Crea una clase `VideoStreamService` en `src/acquisition/video_stream.py`.
2. Esta clase debe instanciarse **una vez por cada cámara**.
3. Implementa la lectura de video en un hilo separado (threading) para cada instancia.
4. Implementa lógica de **reconexión automática**: si `cap.read()` falla en una cámara, esa instancia específica debe reintentar conectar sin bloquear a las demás cámaras.
5. Modifica `src/main.py` para manejar una lista de objetos `VideoStreamService`.

**Criterios de Aceptación:**
- Si tengo 5 cámaras y desconecto la cámara 3, las cámaras 1, 2, 4 y 5 siguen procesando sin interrupciones.
- La cámara 3 muestra logs de "Reconectando..." independientemente.
```

---

### Paso 3: Migración a Base de Datos Robusta (PostgreSQL + Identificación de Origen)
**Objetivo:** Preparar el sistema para concurrencia masiva de datos provenientes de múltiples fuentes.
**Dificultad:** Media (⭐⭐)

```markdown
**Rol:** Eres un Ingeniero de Backend especializado en Bases de Datos.

**Tarea:**
1. Crea un archivo `docker-compose.yml` que levante un servicio de PostgreSQL 15.
2. Instala `sqlalchemy` y `psycopg2-binary`.
3. Refactoriza `src/storage/database_manager.py` para usar ORM (SQLAlchemy).
4. Define los modelos (Tablas) en `src/storage/models.py`. **Crucial:** Todos los eventos (`TrackingEvent`, `Snapshot`) deben tener una columna `camera_id` o `source_id` para saber de qué cámara vino el dato.
5. Crea un script de migración para inicializar la DB.

**Criterios de Aceptación:**
- La base de datos guarda el identificador de la cámara junto con cada detección.
- Soporta escrituras concurrentes de múltiples hilos sin bloquearse (Postgres maneja esto mejor que SQLite).
```

---

### Paso 4: Creación de API REST (Backend)
**Objetivo:** Exponer los datos agregados o filtrados por cámara.
**Dificultad:** Media (⭐⭐)

```markdown
**Rol:** Eres un Desarrollador Fullstack experto en FastAPI.

**Tarea:**
1. Crea una nueva estructura de carpetas: `src/api/`.
2. Implementa endpoints en `src/api/main.py`:
   - `GET /cameras`: Lista de cámaras activas y su estado (Online/Offline).
   - `GET /events`: Con filtro opcional `?camera_id=X`.
   - `GET /stats/efficiency`: Reporte agregado por zona o por cámara.
3. Configura `uvicorn` para correr la API.

**Criterios de Aceptación:**
- Puedo consultar los eventos solo de la "Cámara de la Entrada Principal".
- La API responde rápido incluso si hay muchas cámaras escribiendo en la DB.
```

---

### Paso 5: Dashboard Web (Frontend Multi-Vista)
**Objetivo:** Visualizar múltiples fuentes simultáneamente.
**Dificultad:** Baja/Media (⭐⭐)

```markdown
**Rol:** Eres un Desarrollador Frontend experto en Streamlit.

**Tarea:**
1. Crea una aplicación de **Streamlit** en `src/dashboard/app.py`.
2. Implementa un selector en la barra lateral para filtrar por "Todas las Cámaras" o una específica.
3. Si se selecciona "Todas", muestra una cuadrícula (Grid) con los KPIs de cada cámara.
4. Muestra gráficos comparativos de eficiencia entre diferentes cámaras/zonas.

**Criterios de Aceptación:**
- El operador puede ver rápidamente qué cámaras tienen más actividad.
```

---

## Fase 2: Sistema Completo (Comercialización y Escalado Masivo)

### Paso 6: Optimización con Docker para Producción
**Objetivo:** Empaquetar todo.
**Dificultad:** Media (⭐⭐)

```markdown
**Rol:** Eres un Ingeniero DevOps.

**Tarea:**
1. Crea un `Dockerfile` optimizado.
2. Actualiza `docker-compose.yml` para orquestar App, API, DB y Dashboard.
3. Asegura que el contenedor de la aplicación tenga acceso a red para conectarse a cámaras RTSP externas.

**Criterios de Aceptación:**
- Despliegue en un comando.
```

### Paso 7: Optimización de Inferencia (Multiprocessing Obligatorio)
**Objetivo:** Soportar 10-20 cámaras rompiendo el cuello de botella de Python (GIL).
**Dificultad:** Alta (⭐⭐⭐)

```markdown
**Rol:** Eres un Ingeniero de ML Ops y Rendimiento.

**Tarea:**
1. El uso de `threading` (Paso 2) no es suficiente para 20 cámaras haciendo inferencia neuronal.
2. Implementa `multiprocessing`: Cada grupo de N cámaras (ej. cada 4 cámaras) debe correr en un **Proceso independiente** con su propia instancia del modelo YOLO.
3. Usa colas (`multiprocessing.Queue`) para centralizar los resultados y guardarlos en la DB.
4. (Opcional) Implementa "Batch Inference": Agrupar frames de varias cámaras para pasarlos por la GPU en un solo lote.

**Criterios de Aceptación:**
- El sistema utiliza el 100% de todos los núcleos del CPU (o GPU) disponibles.
- Soporta 15+ cámaras con FPS estables (>10 FPS por cámara).
```

### Paso 8: Seguridad y Autenticación
**Objetivo:** Proteger el acceso.
**Dificultad:** Media (⭐⭐)

```markdown
**Rol:** Eres un experto en Ciberseguridad.

**Tarea:**
1. Implementa autenticación JWT y Roles de Usuario.
2. Permite asignar permisos por cámara: "El Usuario X solo puede ver las cámaras del Almacén".

**Criterios de Aceptación:**
- Control de acceso granular a nivel de cámara/zona.
```

---

## Próximos Pasos (Post-Ejecución)

Una vez completados los pasos, revisa la **Sección 4** del archivo `PLAN_ESTRATEGICO.md` para las tareas de mantenimiento a largo plazo.
