# Integración de D4RT (Google DeepMind) en el Sistema de Rastreo

Este documento detalla ideas conceptuales sobre cómo el modelo **D4RT (Dynamic 4D Reconstruction and Tracking)** de Google DeepMind podría potenciar nuestro sistema actual de visión por computadora.

D4RT es un modelo unificado que permite reconstruir escenas dinámicas en 4 dimensiones (espacio 3D + tiempo) a partir de video, lo cual representa un salto cualitativo respecto al rastreo 2D tradicional.

---

## 1. Rastreo 4D Mejorado (Reemplazo de ByteTrack)

**Problema Actual:**
Nuestro sistema usa `ByteTrack`, que opera en 2D (plano de la imagen). Cuando una persona se oculta detrás de un objeto (oclusión) o cruza con otra, el rastreador a menudo pierde el ID o lo confunde, ya que solo ve "cajas" planas superpuestas.

**Idea con D4RT:**
D4RT entiende la profundidad y el tiempo como un continuo. Podríamos usarlo para predecir la trayectoria de una persona **en el espacio 3D**, no solo en los píxeles de la imagen.

*   **Beneficio:** Si una persona pasa detrás de una columna, D4RT sabe que sigue existiendo en el espacio 3D y puede mantener su ID activo hasta que reaparezca, reduciendo drásticamente la fragmentación de identidades.
*   **Implementación Conceptual:** Sustituir el módulo `PersonTracker` actual. En lugar de alimentar detecciones 2D (cajas) a un filtro de Kalman, alimentaríamos los frames de video al modelo D4RT para obtener coordenadas (x, y, z, t) de cada entidad.

## 2. Fusión Multi-Cámara (Global Scene Representation)

**Problema Actual:**
El sistema actual trata cada cámara como un mundo aislado. La re-identificación (ReID) entre cámaras se hace comparando vectores de características de apariencia (ropa, cara), lo cual falla si la iluminación o el ángulo cambian drásticamente.

**Idea con D4RT:**
D4RT genera una **Representación Global de la Escena**. Si tenemos múltiples cámaras con campos de visión solapados, podríamos alimentar todas las vistas al modelo.

*   **Beneficio:** El sistema entendería que la "Persona A" vista desde la Cámara 1 y la Cámara 2 ocupa el mismo punto físico (x, y, z) en el mundo real en el mismo instante (t). Esto haría la re-identificación casi perfecta en zonas de solapamiento, sin depender tanto de la ropa.
*   **Implementación Conceptual:** Crear un "Super-Tracker" centralizado que reciba los streams de todas las cámaras, construya un mapa 3D unificado en tiempo real y asigne IDs basados en la posición espacial absoluta, no relativa a la cámara.

## 3. Análisis de Comportamiento y Anomalías (4D)

**Problema Actual:**
Detectar comportamientos anómalos (ej. correr, caerse, merodear) en 2D es difícil debido a la perspectiva. Una persona que camina hacia la cámara parece "crecer", lo que puede confundirse con movimiento rápido si no se calibra bien.

**Idea con D4RT:**
Al tener una reconstrucción 4D, podemos medir **velocidad y aceleración real** en metros/segundo, independientemente de la distancia a la cámara.

*   **Beneficio:** Alertas mucho más precisas. Podríamos definir reglas como "Si la velocidad > 3 m/s en el Pasillo A, generar alerta", eliminando falsos positivos causados por la perspectiva.
*   **Implementación Conceptual:** Un módulo de análisis post-procesamiento que tome las trayectorias 4D generadas por D4RT y calcule vectores de física básica (velocidad, dirección) para detectar eventos de seguridad.

## Consideraciones Técnicas

*   **Recursos Computacionales:** D4RT es significativamente más pesado que modelos como YOLOv8. Requeriría hardware dedicado potente (GPUs de servidor, probablemente NVIDIA A100 o similar) para correr en tiempo real, o bien usarlo en modo "batch" para análisis forense post-evento.
*   **Disponibilidad:** Actualmente D4RT es un proyecto de investigación. La integración real dependería de la liberación del código fuente o de una API por parte de Google DeepMind.
