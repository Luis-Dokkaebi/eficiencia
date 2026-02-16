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

El orden de estas fases obedece a **dependencias técnicas** (ej. no se puede hacer una API sin una Base de Datos estable, y no vale la pena optimizar un sistema que aún no funciona correctamente).

### Fase 1: MVP (Producto Mínimo Viable) - Estabilización y Core
**Tiempo estimado: 4-6 semanas**
El objetivo es tener un sistema que pueda correr 24/7 sin fallos y con datos persistentes confiables.
1.  **Semana 1-2 [Dificultad: Alta]:** Refactorización de `main.py`. Implementar manejo de errores robusto (reconexión automática de cámaras).
    *   *Razón:* Es el cimiento. Si el script se cae, nada más importa.
2.  **Semana 3 [Dificultad: Media]:** Migración de SQLite a PostgreSQL y diseño del esquema de base de datos definitivo.
    *   *Razón:* Necesario para que la API funcione rápido y soporte múltiples usuarios.
3.  **Semana 4 [Dificultad: Media]:** Creación de una API básica (FastAPI) para consultar los datos.
    *   *Razón:* Desacopla el backend del frontend.
4.  **Semana 5-6 [Dificultad: Baja/Media]:** Dashboard web simple (Streamlit o React básico) para ver reportes y estado en tiempo real.
    *   *Razón:* Reemplaza `cv2.imshow` y permite acceso remoto.

### Fase 2: Sistema Completo - Comercialización
**Tiempo estimado: 3-6 meses (post-MVP)**
1.  **Mes 1 [Dificultad: Media]:** Gestión de Usuarios y Roles (Auth), Configuración remota de zonas y cámaras desde la UI.
2.  **Mes 2 [Dificultad: Alta]:** Optimización de rendimiento (TensorRT, multiprocesamiento) para soportar 4-8 cámaras por servidor.
3.  **Mes 3 [Dificultad: Baja]:** Sistema de Alertas (Email/SMS/Telegram) y Reportes Avanzados (PDF/Excel exportables automáticamente).
4.  **Mes 4+ [Dificultad: Alta]:** Aplicación Móvil, Integración con Nube (híbrido Edge-Cloud), Mantenimiento OTA (Over-the-Air updates).

## 3. Siguientes Pasos Técnicos (Priorizados)

A continuación se listan las tareas técnicas inmediatas, ordenadas por una combinación de **"Quick Wins" (Victorias Rápidas)** y **Dependencias Críticas**.

1.  **Configuración Avanzada (Quick Win)**
    *   **Dificultad:** Baja (⭐)
    *   **Acción:** Mover la configuración de `config.py` a variables de entorno (`.env`) o un archivo YAML/JSON.
    *   **Beneficio:** Facilita el despliegue inmediato sin tocar código Python.

2.  **Modularización del Bucle Principal (Cimiento)**
    *   **Dificultad:** Alta (⭐⭐⭐)
    *   **Acción:** Crear `VideoStreamService` (conexión/reconexión asíncrona) y separar la lógica de "Dibujado" (`cv2.rectangle`) de la lógica de negocio.
    *   **Beneficio:** Estabilidad. El sistema no se colgará si la cámara parpadea.

3.  **Implementación de Base de Datos Real (Infraestructura)**
    *   **Dificultad:** Media (⭐⭐)
    *   **Acción:** Levantar contenedor PostgreSQL y actualizar `src/storage/database_manager.py` (SQLAlchemy/psycopg2).
    *   **Beneficio:** Escalabilidad y concurrencia real.

4.  **API REST (Funcionalidad)**
    *   **Dificultad:** Media (⭐⭐)
    *   **Acción:** Crear `src/api/` con endpoints (FastAPI) para `/tracking` y `/reports`.
    *   **Beneficio:** Permite construir cualquier frontend (Web/Móvil) sobre el sistema.

## 4. Fase 3: Post-Lanzamiento y Mantenimiento

Una vez completados todos los pasos de desarrollo y los prompts de ejecución (`PROMPTS_DE_EJECUCION.md`), el ciclo de vida del software continúa. Estos son los pasos a seguir:

1.  **Monitorización y Logs (Observabilidad):**
    -   Implementar un sistema de logs centralizado (ej. Grafana Loki o ELK Stack) para detectar errores en tiempo real sin conectarse al servidor.
    -   Configurar alertas automáticas si la cámara deja de enviar frames o el uso de CPU supera el 90%.

2.  **Ciclo de Feedback (Mejora Continua):**
    -   Instalar el software en un entorno piloto ("beta testers").
    -   Recopilar falsos positivos (ej. detectar un perchero como persona) y falsos negativos.
    -   Usar las herramientas de `src/analysis` para comparar métricas reales vs esperadas.

3.  **Mantenimiento de Modelos IA:**
    -   **Re-entrenamiento (Fine-tuning):** Si el sistema falla en condiciones específicas (ej. poca luz, uniformes de trabajo), capturar esas imágenes, etiquetarlas y re-entrenar YOLO.
    -   Actualizar la galería de Re-identificación (ReID) periódicamente para eliminar perfiles antiguos.

4.  **Auditoría de Seguridad:**
    -   Realizar pruebas de penetración (Pentesting) básico sobre la API y el Dashboard.
    -   Asegurar que los datos biométricos (si se guardan) cumplan con GDPR/Lopd.
