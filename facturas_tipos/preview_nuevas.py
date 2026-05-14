import fitz
import os

pdf_dir = r'e:\programacion\facturas\facturas_tipos\facturas_ejemplos'
out_dir = r'e:\programacion\facturas\facturas_tipos\previews_nuevas'
os.makedirs(out_dir, exist_ok=True)

pdfs_to_check = [
    "207470622_Ciclo18_202304.pdf",
    "ds089080012802125112688025_1111944_202510.pdf",
    "294408011_Ciclo23_202409.pdf",
    "330674371_Ciclo13_202305.pdf",
    "ds089080012802125113413032_1113713_202511.pdf"
]

for pdf_name in pdfs_to_check:
    path = os.path.join(pdf_dir, pdf_name)
    if not os.path.exists(path):
        print(f"Skipping {pdf_name}, not found.")
        continue
    doc = fitz.open(path)
    for i in range(min(len(doc), 2)):
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
        base = pdf_name.replace(".pdf", "")
        out_path = os.path.join(out_dir, f'{base}_p{i+1}.png')
        pix.save(out_path)
        print(f'Saved: {out_path}')
    doc.close()

print("Done!")
