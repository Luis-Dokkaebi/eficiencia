# Falcon Plant Resources: Estrategia de Demostración (Proof of Concept - PoC)

Para vender la integración de Inteligencia Artificial a Falcon Plant Resources, la mejor estrategia es construir Pruebas de Concepto (PoCs) funcionales sin necesidad de datos reales de la empresa. Podemos utilizar nuestro entorno actual (Python, Streamlit, YOLO) y datos sintéticos o públicos.

## 1. "Falcon Sentinel" (Seguridad EPP en tiempo real)
*   **¿Cómo lo hacemos sin estar en la planta?**
    *   Utilizamos videos de fuentes públicas (YouTube) de trabajadores de construcción o refinerías.
    *   Descargamos un modelo YOLO pre-entrenado específico para detección de EPP (Personal Protective Equipment) de código abierto (ej. Roboflow).
*   **El Demo:**
    *   Procesamos el video con nuestro sistema actual (`src/main.py`). La interfaz muestra en tiempo real cuadros delimitadores (bounding boxes) verdes para técnicos con EPP completo (casco, chaleco) y alertas rojas para quienes incumplen las normas de seguridad.

## 2. "Falcon Predict" (Dashboard de Mantenimiento Predictivo)
*   **¿Cómo lo hacemos sin datos reales de equipos mecánicos?**
    *   Generamos un **dataset sintético** en Python simulando datos históricos de sensores (vibración, temperatura) de una bomba industrial durante meses, introduciendo anomalías progresivas.
*   **El Demo:**
    *   Integramos una nueva pestaña interactiva en nuestro Dashboard de `Streamlit` (`src/dashboard/app.py`).
    *   Mostramos gráficas de series de tiempo de la "salud" del equipo simulado, con alertas predictivas generadas por modelos de Machine Learning (ej. Isolation Forest) indicando la probabilidad de fallo.

## 3. "Falcon Vision" (Inspección de Calidad de Soldadura)
*   **¿Cómo lo hacemos sin fotos de sus técnicos?**
    *   Utilizamos datasets públicos (ej. Kaggle) de "Weld Defect Images", que contienen miles de radiografías o fotografías de soldaduras etiquetadas (con y sin defectos).
*   **El Demo:**
    *   Construimos una aplicación web sencilla en el Dashboard donde el usuario sube una imagen de soldadura.
    *   Un modelo de clasificación de imágenes (PyTorch/TensorFlow) analiza la foto y devuelve un diagnóstico instantáneo (ej. *Defecto Detectado: Porosidad - 95% confianza*).

## 4. "Falcon Integrity" (Digitalización de Servicios Controlados)
*   **¿Cómo lo hacemos sin herramientas de torque Bluetooth?**
    *   El objetivo es demostrar la **trazabilidad digital**, no la conexión física del hardware.
*   **El Demo:**
    *   Creamos una vista "móvil" en Streamlit simulando la interfaz de una tablet de campo.
    *   Mostramos un diagrama interactivo de una brida (ej. 8 pernos). El usuario hace clic en cada perno para simular el ingreso de valores de torque. Si un valor simulado está fuera del rango tolerado, el sistema genera una alerta al supervisor.

---

## Recomendación Táctica
Se recomienda priorizar la construcción de los **Demos 1 (EPP)** y **2 (Dashboard Predictivo Simulado)**. Estos ofrecen el mayor impacto visual inmediato y reutilizan la infraestructura de Visión Artificial y Análisis de Datos (Dashboards) ya implementada en este repositorio.