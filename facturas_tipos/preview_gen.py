import fitz
import os

pdf_dir = r'e:\programacion\facturas\facturas_tipos'
out_dir = os.path.join(pdf_dir, 'previews')
os.makedirs(out_dir, exist_ok=True)

for pdf_name in ['tipo_factura_1.pdf', 'tipo_factura_2.pdf', 'tipo_factura_3.pdf', 'tipo_factura_4.pdf']:
    doc = fitz.open(os.path.join(pdf_dir, pdf_name))
    for i in range(min(len(doc), 2)):
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        base = pdf_name.replace(".pdf", "")
        out_path = os.path.join(out_dir, f'{base}_p{i+1}.png')
        pix.save(out_path)
        print(f'Saved: {out_path} ({pix.width}x{pix.height})')
    doc.close()

print("Done!")
