# Prompts de Ejecución Secuencial

Este documento contiene una serie de **Prompts Maestros** diseñados para ser utilizados secuencialmente con un Asente de IA (como yo). Cada prompt corresponde a una fase crítica del `PLAN_ESTRATEGICO.md` y está optimizado para obtener resultados de código funcionales y robustos.

## Instrucciones de Uso
Copia y pega el prompt completo en el chat. No saltes pasos, ya que cada uno construye sobre el anterior.

---

## Fase 1: Cimientos y Estabilidad (MVP)

### Paso 1: Configuración Avanzada y Variables de Entorno
**Objetivo:** Desacoplar la configuración del código fuente para facilitar despliegues.
**Dificultad:** Baja (⭐)

```markdown
**Rol:** Eres un Ingeniero DevOps Senior especializado en Python.

**Tarea:**
1. Refactoriza el manejo de configuración actual en `config/config.py`.
2. Implementa el uso de `python-dotenv` para cargar variables sensibles desde un archivo `.env`.
3. Crea un archivo `.env.example` con todas las variables necesarias (cámaras, base de datos, thresholds).
4. Modifica `config.py` para leer de `os.getenv` con valores por defecto sensatos.
5. Asegura que `src/main.py` siga funcionando sin cambios mayores, importando la nueva configuración.

**Criterios de Aceptación:**
- El archivo `.env` no debe subirse al repo (.gitignore).
- El sistema debe iniciar correctamente leyendo las variables de entorno.
- Si falta el `.env`, debe usar defaults seguros.
```

---

### Paso 2: Modularización del Servicio de Video
**Objetivo:** Evitar que el sistema colapse si una cámara falla y separar la lógica de visión de la lógica de UI.
**Dificultad:** Alta (⭐⭐⭐)

```markdown
**Rol:** Eres un Arquitecto de Software experto en Computer Vision y Concurrencia.

**Tarea:**
1. Crea una clase `VideoStreamService` en `src/acquisition/video_stream.py`.
2. Implementa la lectura de video en un hilo separado (threading) para que el buffer no se llene y cause lag.
3. Implementa lógica de **reconexión automática**: si `cap.read()` falla, debe reintentar conectar cada X segundos sin matar el programa principal.
4. Modifica `src/main.py` para usar `VideoStreamService` en lugar de `cv2.VideoCapture` directo.

**Criterios de Aceptación:**
- El bucle principal no debe bloquearse si la cámara se desconecta.
- Debe mostrar un log "Reconectando..." y recuperar la imagen automáticamente cuando la cámara vuelva.
```

---

### Paso 3: Migración a Base de Datos Robusta (PostgreSQL)
**Objetivo:** Preparar el sistema para concurrencia y persistencia real.
**Dificultad:** Media (⭐⭐)

```markdown
**Rol:** Eres un Ingeniero de Backend especializado en Bases de Datos.

**Tarea:**
1. Crea un archivo `docker-compose.yml` que levante un servicio de PostgreSQL 15.
2. Instala `sqlalchemy` y `psycopg2-binary`.
3. Refactoriza `src/storage/database_manager.py` para usar ORM (SQLAlchemy) en lugar de SQL crudo con `sqlite3`.
4. Define los modelos (Tablas) en `src/storage/models.py`: `TrackingEvent`, `Snapshot`, `EfficiencyReport`.
5. Crea un script de migración para inicializar la DB.

**Criterios de Aceptación:**
- El sistema debe poder escribir eventos en PostgreSQL corriendo en Docker.
- `src/main.py` debe seguir funcionando, guardando datos en la nueva DB de forma transparente.
```

---

### Paso 4: Creación de API REST (Backend)
**Objetivo:** Exponer los datos al mundo exterior (Frontend/Móvil).
**Dificultad:** Media (⭐⭐)

```markdown
**Rol:** Eres un Desarrollador Fullstack experto en FastAPI.

**Tarea:**
1. Crea una nueva estructura de carpetas: `src/api/`.
2. Implementa una aplicación básica con FastAPI en `src/api/main.py`.
3. Crea endpoints para:
   - `GET /health`: Estado del sistema.
   - `GET /events/latest`: Últimos 10 eventos de tracking.
   - `GET /stats/efficiency`: Reporte agregado de eficiencia (simulado o real desde DB).
4. Configura `uvicorn` para correr la API.

**Criterios de Aceptación:**
- Puedo hacer `curl http://localhost:8000/events/latest` y recibir un JSON con datos.
- La API corre independientemente del script de procesamiento de video (pueden ser dos procesos distintos).
```

---

### Paso 5: Dashboard Web (Frontend MVP)
**Objetivo:** Reemplazar `cv2.imshow` y permitir monitoreo remoto.
**Dificultad:** Baja/Media (⭐⭐)

```markdown
**Rol:** Eres un Desarrollador Frontend experto en Streamlit (o React si prefieres complejidad).

**Tarea:**
1. Crea una aplicación de **Streamlit** en `src/dashboard/app.py`.
2. La app debe conectarse a la Base de Datos (o consumir la API del paso anterior) para mostrar:
   - Gráfico de ocupación por zona en tiempo real.
   - Lista de últimas alertas/eventos con fotos (si las hay).
   - KPIs de eficiencia.
3. Agrega un botón de "Auto-refresh".

**Criterios de Aceptación:**
- Al correr `streamlit run src/dashboard/app.py`, veo un dashboard interactivo en el navegador.
- Los datos coinciden con lo que está detectando el sistema.
```

---

## Fase 2: Sistema Completo (Comercialización)

### Paso 6: Optimización con Docker para Producción
**Objetivo:** Empaquetar todo para instalarlo en el cliente con un solo comando.
**Dificultad:** Media (⭐⭐)

```markdown
**Rol:** Eres un Ingeniero DevOps.

**Tarea:**
1. Crea un `Dockerfile` optimizado para la aplicación (multi-stage build para reducir tamaño).
2. Actualiza `docker-compose.yml` para incluir:
   - Servicio `app` (Procesamiento Video).
   - Servicio `api` (Backend).
   - Servicio `db` (PostgreSQL).
   - Servicio `dashboard` (Streamlit/Frontend).
3. Configura volúmenes para persistir datos y snapshots fuera de los contenedores.

**Criterios de Aceptación:**
- Ejecutando `docker-compose up -d` se levanta todo el sistema.
- Los servicios se comunican entre sí correctamente usando nombres de host de Docker.
```

### Paso 7: Optimización de Inferencia (TensorRT/Multiprocessing)
**Objetivo:** Soportar múltiples cámaras en un solo servidor.
**Dificultad:** Alta (⭐⭐⭐)

```markdown
**Rol:** Eres un Ingeniero de ML Ops y Rendimiento.

**Tarea:**
1. Implementa `multiprocessing` para que cada cámara corra en su propio proceso de CPU, evitando el GIL de Python.
2. (Opcional si hay GPU) Exporta el modelo YOLO a formato TensorRT (.engine) para inferencia ultra-rápida.
3. Implementa un patrón Productor-Consumidor: Un proceso lee frames y los pone en una cola; otro proceso hace inferencia.

**Criterios de Aceptación:**
- El FPS del sistema no cae linealmente al agregar una segunda cámara (escalabilidad horizontal en CPU/GPU).
```

### Paso 8: Seguridad y Autenticación
**Objetivo:** Proteger el acceso a los datos.
**Dificultad:** Media (⭐⭐)

```markdown
**Rol:** Eres un experto en Ciberseguridad.

**Tarea:**
1. Implementa autenticación JWT en la API (FastAPI).
2. Crea una tabla de `Users` en la base de datos con contraseñas hasheadas (bcrypt).
3. Protege los endpoints del Dashboard para que requieran login.

**Criterios de Aceptación:**
- No se puede acceder a `/api/events` sin un token Bearer válido.
- El dashboard pide usuario y contraseña al entrar.
```

---

## Próximos Pasos (Post-Ejecución)

Una vez hayas completado los 8 pasos anteriores, el sistema estará funcional y listo para vender. Sin embargo, el trabajo no termina ahí. Consulta la **Sección 4** del archivo `PLAN_ESTRATEGICO.md` para detalles sobre:
1.  Monitorización y Logs (Grafana/Loki).
2.  Ciclo de Feedback con Clientes (Beta Testing).
3.  Mantenimiento de Modelos (Re-entrenamiento).
4.  Auditorías de Seguridad periódicas.
