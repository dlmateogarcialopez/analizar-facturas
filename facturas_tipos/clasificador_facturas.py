"""
Clasificador de facturas PDF según ubicación + clase de servicio.
"""
import os
import sys
import shutil
import re
from pathlib import Path

# Configuración de encoding para Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configuración
EJEMPLOS_DIR = Path("E:/programacion/facturas/facturas_tipos/facturas_ejemplos")
CLASIFICADOS_DIR = Path("E:/programacion/facturas/facturas_tipos/facturas_clasificadas")


def extraer_info_factura(texto: str) -> dict:
    """Extrae ubicación y clase de servicio del texto de la factura."""
    info = {"ubicacion": None, "clase_servicio": None, "tipo_formato": None}

    # Detectar tipo de formato
    if "DIAN" in texto or "REPÚBLICA DE COLOMBIA" in texto:
        info["tipo_formato"] = "DIAN"
    elif "documento equivalente" in texto.lower():
        info["tipo_formato"] = "electronica"
    else:
        info["tipo_formato"] = "desconocido"

    # Extraer ubicación (ciudad, departamento)
    ubicacion_match = re.search(
        r"(?:Ciudad|Ubicación|Ubicacion)[:\s]*([A-Za-záéíóúñÁÉÍÓÚÑ\s\.,]+?),?\s*([A-Za-záéíóúñÁÉÍÓÚÑ\s]+)?(?:, Colombia)?",
        texto,
        re.IGNORECASE
    )
    if ubicacion_match:
        ciudad = ubicacion_match.group(1).strip()
        depto = ubicacion_match.group(2).strip() if ubicacion_match.group(2) else ""
        info["ubicacion"] = f"{ciudad}" + (f", {depto}" if depto else "")

    # Si no se encontró con patrón anterior, buscar en patrón específico DIAN
    if not info["ubicacion"]:
        # Patrón para facturas DIAN: "Bogotá D.C., Cundinamarca, Colombia"
        ubicacion_match = re.search(
            r"([A-Za-záéíóúñÁÉÍÓÚÑ\s\.]+(?:\s*D\.?C\.?)?),?\s*([A-Za-záéíóúñÁÉÍÓÚÑ\s]+),?\s*Colombia",
            texto,
            re.IGNORECASE
        )
        if ubicacion_match:
            ciudad = ubicacion_match.group(1).strip()
            depto = ubicacion_match.group(2).strip()
            info["ubicacion"] = f"{ciudad}, {depto}"

    # Extraer clase de servicio
    # Formato DIAN: buscar "Clase de Servicio" o similar
    clase_match = re.search(
        r"(?:Clase?\s*(?:de)?\s*(?:Servicio|Linea))[:\s]*([A-Za-záéíóúñÁÉÍÓÚÑ\s\-]+?)(?:\n|$)",
        texto,
        re.IGNORECASE
    )
    if clase_match:
        info["clase_servicio"] = clase_match.group(1).strip()
    else:
        # Buscar en líneas cerca de "Nacional" o "Exportación"
        if re.search(r"\bNacional\b", texto, re.IGNORECASE):
            info["clase_servicio"] = "Nacional"
        elif re.search(r"\bExportación\b", texto, re.IGNORECASE):
            info["clase_servicio"] = "Exportación"
        elif re.search(r"\bInternacional\b", texto, re.IGNORECASE):
            info["clase_servicio"] = "Internacional"

    # Para facturas electrónicas: buscar tipo de documento equivalente
    if info["tipo_formato"] == "electronica" and not info["clase_servicio"]:
        # Extraer la clase del nombre del documento
        clase_match = re.search(
            r"documento equivalente[:\s]*([A-Za-záéíóúñÁÉÍÓÚÑ\s\-]+?)(?:\n|$)",
            texto,
            re.IGNORECASE
        )
        if clase_match:
            info["clase_servicio"] = clase_match.group(1).strip()
        else:
            info["clase_servicio"] = "Electronica"

    # Limpiar valores
    if info["ubicacion"]:
        info["ubicacion"] = re.sub(r'\s+', ' ', info["ubicacion"]).strip()
    if info["clase_servicio"]:
        info["clase_servicio"] = re.sub(r'\s+', ' ', info["clase_servicio"]).strip()

    return info


def clasificar_facturas():
    """Clasifica todos los PDFs en carpetas por ubicación + clase de servicio."""
    # Crear directorio de destino
    CLASIFICADOS_DIR.mkdir(parents=True, exist_ok=True)

    pdfs = list(EJEMPLOS_DIR.glob("*.pdf"))
    print(f"Encontrados {len(pdfs)} PDFs\n")

    resultados = {}
    errores = []

    for pdf_path in pdfs:
        try:
            # Leer PDF (solo texto)
            texto = leer_pdf_texto(str(pdf_path))

            if not texto:
                errores.append({"archivo": pdf_path.name, "error": "No se pudo extraer texto"})
                continue

            # Extraer información
            info = extraer_info_factura(texto)

            # Crear nombre de carpeta
            ubicacion = info["ubicacion"] or "sin_ubicacion"
            clase = info["clase_servicio"] or "sin_clase"
            carpeta = f"{ubicacion}___{clase}"

            if carpeta not in resultados:
                resultados[carpeta] = {"archivos": [], "info": info}

            resultados[carpeta]["archivos"].append(pdf_path.name)

        except Exception as e:
            errores.append({"archivo": pdf_path.name, "error": str(e)})

    # Crear carpetas y mover archivos
    for carpeta, data in resultados.items():
        carpeta_path = CLASIFICADOS_DIR / carpeta
        carpeta_path.mkdir(parents=True, exist_ok=True)

        for archivo in data["archivos"]:
            src = EJEMPLOS_DIR / archivo
            dst = carpeta_path / archivo
            shutil.copy2(src, dst)

    # Mostrar resultados
    print("=" * 70)
    print("CLASIFICACIÓN DE FACTURAS")
    print("=" * 70)

    for carpeta, data in sorted(resultados.items()):
        print(f"\n📁 {carpeta}")
        print(f"   Tipo: {data['info']['tipo_formato']}")
        print(f"   Archivos ({len(data['archivos'])}):")
        for archivo in data["archivos"]:
            print(f"      - {archivo}")

    if errores:
        print(f"\n⚠️  ERRORES ({len(errores)}):")
        for err in errores:
            print(f"   - {err['archivo']}: {err['error']}")

    # Crear archivo de reporte
    reporte_path = CLASIFICADOS_DIR / "reporte_clasificacion.txt"
    with open(reporte_path, "w", encoding="utf-8") as f:
        f.write("CLASIFICACIÓN DE FACTURAS\n")
        f.write("=" * 70 + "\n\n")
        for carpeta, data in sorted(resultados.items()):
            f.write(f"{carpeta}\n")
            f.write(f"  Tipo: {data['info']['tipo_formato']}\n")
            f.write(f"  Archivos:\n")
            for archivo in data["archivos"]:
                f.write(f"    - {archivo}\n")
            f.write("\n")
        if errores:
            f.write(f"\nERRORES:\n")
            for err in errores:
                f.write(f"  - {err['archivo']}: {err['error']}\n")

    print(f"\n✅ Reporte guardado en: {reporte_path}")
    print(f"📂 Archivos copiados a: {CLASIFICADOS_DIR}")
    print(f"\nTotal carpetas creadas: {len(resultados)}")
    print(f"Total PDFs procesados: {sum(len(d['archivos']) for d in resultados.values())}")
    print(f"Total errores: {len(errores)}")


def leer_pdf_texto(pdf_path: str) -> str:
    """Lee un PDF y retorna el texto extraído."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        texto = ""
        for page in doc:
            texto += page.get_text()
        doc.close()
        return texto
    except ImportError:
        # Fallback: usar pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                texto = ""
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        texto += t
                return texto
        except ImportError:
            raise ImportError("Instala PyMuPDF o pdfplumber para procesar PDFs")


if __name__ == "__main__":
    clasificar_facturas()
