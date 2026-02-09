import cv2
import os
import json

class ZoneEditor:
    def __init__(self, output_path="data/zonas/zonas.json"):
        # Determina la raíz del proyecto a partir de la ubicación del archivo actual
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.abspath(os.path.join(script_dir, "../.."))
        self.output_path = os.path.join(self.project_root, output_path)
        self.points = []

    def click_event(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            print(f"🟢 Punto agregado: ({x}, {y})")
            self.points.append((x, y))

    def save_zone(self, zone_name):
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

        data = {}
        if os.path.exists(self.output_path):
            with open(self.output_path, 'r') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}

        data[zone_name] = self.points

        with open(self.output_path, 'w') as f:
            json.dump(data, f, indent=4)

        print(f"✅ Zona '{zone_name}' guardada en {self.output_path}")

    def run(self, image_path, zone_name):
        absolute_image_path = os.path.abspath(os.path.join(self.project_root, image_path))
        print("📂 Ruta absoluta resuelta:", absolute_image_path)
        print("🧭 Cargando imagen desde:", absolute_image_path)

        image = cv2.imread(absolute_image_path)
        if image is None:
            print("❌ La imagen no se pudo cargar. Verifica la ruta o el archivo.")
            return
        print("✅ Imagen cargada correctamente. Tamaño:", image.shape)

        clone = image.copy()
        cv2.namedWindow("Seleccione puntos (presione 's' para guardar)", cv2.WINDOW_NORMAL)
        cv2.setMouseCallback("Seleccione puntos (presione 's' para guardar)", self.click_event)

        while True:
            for point in self.points:
                cv2.circle(image, point, 3, (0, 255, 0), -1)

            cv2.imshow("Seleccione puntos (presione 's' para guardar)", image)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("s"):
                break

            image = clone.copy()

        cv2.destroyAllWindows()
        self.save_zone(zone_name)

# 💖 Bloque de ejecución directa
if __name__ == "__main__":
    editor = ZoneEditor()
    editor.run("data/zonas/frame_referencia.jpg", "Zona")
