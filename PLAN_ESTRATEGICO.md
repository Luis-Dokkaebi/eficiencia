# Plan Estratégico de Desarrollo: Software de Tracking y Eficiencia

Este documento detalla la hoja de ruta para transformar el prototipo actual en un producto comercial robusto y escalable.

## 1. Comercialización y Escalabilidad

Para llevar el software de un script de investigación (`src/main.py`) a un producto comercial, necesitamos abordar las siguientes áreas clave:

### A. Arquitectura de Software
Actualmente, el sistema es monolítico (captura, procesamiento, lógica y visualización ocurren en un solo bucle). Para escalar:
- **Desacoplamiento:** Separar la ingesta de video, el procesamiento de IA (YOLO/ReID) y la interfaz de usuario.
- **Microservicios (o Módulos Independientes):**
    - *Servicio de Ingesta:* Lee RTSP/Webcam y pone frames en una cola (Redis/RabbitMQ/ZeroMQ).
    - *Servicio de Procesamiento:* Consume frames, ejecuta YOLO/FaceRec, y publica resultados.
    - *API Server:* Gestiona la base de datos y sirve datos al frontend.
    - *Frontend:* Interfaz Web (React/Vue) para dashboard, eliminando `cv2.imshow`.

### B. Despliegue (Deployment)
- **Dockerización:** Crear contenedores Docker para cada servicio. Esto asegura que el software funcione igual en el entorno de desarrollo que en el del cliente.
- **Orquestación:** Usar Docker Compose para despliegues simples (1 servidor) o Kubernetes (K8s) para escalado horizontal (múltiples servidores/cámaras).

### C. Base de Datos
- **Migración:** Pasar de SQLite (`local_tracking.db`) a PostgreSQL. SQLite no soporta bien la concurrencia de múltiples cámaras escribiendo simultáneamente.
- **Series Temporales:** Para el tracking de alta frecuencia, considerar TimescaleDB (extensión de Postgres) o InfluxDB.

### D. Hardware y Optimización
- **Aceleración:** Utilizar TensorRT para optimizar los modelos YOLO en hardware NVIDIA (Jetson Orin/Xavier).
- **Edge Computing:** Procesar en el borde (en el sitio del cliente) para reducir ancho de banda y latencia.

## 2. Tiempos Estimados

### Fase 1: MVP (Producto Mínimo Viable) - Estabilización y Core
**Tiempo estimado: 4-6 semanas**
El objetivo es tener un sistema que pueda correr 24/7 sin fallos y con datos persistentes confiables.
1.  **Semana 1-2:** Refactorización de `main.py`. Implementar manejo de errores robusto (reconexión automática de cámaras).
2.  **Semana 3:** Migración de SQLite a PostgreSQL y diseño del esquema de base de datos definitivo.
3.  **Semana 4:** Creación de una API básica (FastAPI) para consultar los datos.
4.  **Semana 5-6:** Dashboard web simple (Streamlit o React básico) para ver reportes y estado en tiempo real (reemplazando `cv2.imshow`).

### Fase 2: Sistema Completo - Comercialización
**Tiempo estimado: 3-6 meses (post-MVP)**
1.  **Mes 1:** Gestión de Usuarios y Roles (Auth), Configuración remota de zonas y cámaras desde la UI.
2.  **Mes 2:** Optimización de rendimiento (TensorRT, multiprocesamiento) para soportar 4-8 cámaras por servidor.
3.  **Mes 3:** Sistema de Alertas (Email/SMS/Telegram) y Reportes Avanzados (PDF/Excel exportables automáticamente).
4.  **Mes 4+:** Aplicación Móvil, Integración con Nube (híbrido Edge-Cloud), Mantenimiento OTA (Over-the-Air updates).

## 3. Siguientes Pasos Técnicos (Inmediatos)

Basado en el análisis del código actual (`src/main.py` y `config/config.py`), estos son los pasos concretos a seguir:

1.  **Modularización del Bucle Principal:**
    - Crear una clase `VideoStreamService` que maneje la conexión y reconexión de la cámara de forma asíncrona.
    - Separar la lógica de "Dibujado" (`cv2.rectangle`, `cv2.text`) de la lógica de negocio. El servidor no debe gastar CPU dibujando en frames si nadie los está viendo.

2.  **Implementación de Base de Datos Real:**
    - Levantar un contenedor de PostgreSQL.
    - Actualizar `src/storage/database_manager.py` para usar `SQLAlchemy` o `psycopg2` en lugar de `sqlite3`.

3.  **API REST (FastAPI):**
    - Crear un nuevo directorio `src/api/`.
    - Implementar endpoints como `/api/v1/tracking/current` y `/api/v1/reports/efficiency`.
    - Esto permitirá que cualquier frontend (Web o Móvil) consuma los datos.

4.  **Configuración Avanzada:**
    - Mover la configuración de `config.py` a variables de entorno (`.env`) o un archivo YAML/JSON para facilitar el despliegue sin tocar código Python.
