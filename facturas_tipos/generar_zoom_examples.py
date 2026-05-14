import fitz
import os

pdf_path = r'e:\programacion\facturas\facturas_tipos\tipo_factura_1.pdf'
out_dir = r'e:\programacion\facturas\facturas_tipos\tipos_zoom'
os.makedirs(out_dir, exist_ok=True)

zooms = [1.0, 1.5, 2.0, 3.0]

doc = fitz.open(pdf_path)
page = doc.load_page(0) # Solo la página 1

print(f"Generando ejemplos de zoom para: {os.path.basename(pdf_path)}")

for z in zooms:
    # Definimos la matriz de zoom
    mat = fitz.Matrix(z, z)
    pix = page.get_pixmap(matrix=mat)
    
    out_file = os.path.join(out_dir, f"factura_zoom_{z}.png")
    pix.save(out_file)
    print(f"  - Guardado zoom {z}: {out_file} ({pix.width}x{pix.height})")

doc.close()
print("\n¡Listo! Revisa la carpeta tipos_zoom.")
