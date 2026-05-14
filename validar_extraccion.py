"""
validar_extraccion.py
---------------------
Compara los datos extraídos por Modal (hoja '💾 Datos Crudos' del Excel)
contra el ground_truth.json para medir precisión de la extracción.

Uso:
    python validar_extraccion.py
    (Busca automáticamente el reporte más reciente en reportes/)
"""

import os
import sys
import json
import glob
import pandas as pd

project_root = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def flatten_dict(d, parent_key='', sep='.'):
    """Aplana un dict anidado. Listas se mantienen como están."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def normalizar(val):
    """Normaliza un valor para comparación."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, str):
        v = val.strip()
        if v.lower() in ('', 'nan', 'none', 'n/a'):
            return None
        return v
    return val


def comparar_valor(gt_val, ext_val):
    """Compara GT vs Extraído. Retorna (match: bool, detalle: str)."""
    gt = normalizar(gt_val)
    ext = normalizar(ext_val)

    if gt is None and ext is None:
        return True, "✅ Ambos null"
    if gt is None and ext is not None:
        return False, f"❌ GT=null, Ext={ext}"
    if gt is not None and ext is None:
        return False, f"❌ GT={gt}, Ext=null"

    # Numéricos
    try:
        gt_n = float(gt) if not isinstance(gt, (int, float)) else gt
        ext_n = float(ext) if not isinstance(ext, (int, float)) else ext
        if gt_n == 0:
            match = abs(ext_n) < 0.01
        else:
            match = abs(gt_n - ext_n) / abs(gt_n) <= 0.02  # tolerancia 2%
        if match:
            return True, f"✅ {gt}"
        return False, f"❌ GT={gt}, Ext={ext}"
    except (ValueError, TypeError):
        pass

    # Strings
    gt_s = str(gt).strip().upper()
    ext_s = str(ext).strip().upper()
    if gt_s == ext_s:
        return True, f"✅ {gt}"
    if gt_s in ext_s or ext_s in gt_s:
        return True, f"⚠️ Parcial: GT='{gt}' ≈ Ext='{ext}'"
    return False, f"❌ GT='{gt}', Ext='{ext}'"


# ---------------------------------------------------------------------------
# Encontrar reporte más reciente
# ---------------------------------------------------------------------------

def buscar_reporte_reciente():
    """Busca el Excel más reciente en reportes/."""
    patron = os.path.join(project_root, "reportes", "reporte_facturas_*.xlsx")
    archivos = glob.glob(patron)
    if not archivos:
        return None
    return max(archivos, key=os.path.getmtime)


# ---------------------------------------------------------------------------
# Leer datos del Excel
# ---------------------------------------------------------------------------

def leer_datos_crudos(excel_path, factura_name):
    """Lee la hoja '💾 Datos Crudos' y devuelve la fila de la factura como dict."""
    df = pd.read_excel(excel_path, sheet_name="💾 Datos Crudos")

    # Buscar la fila que corresponde a la factura
    col_archivo = None
    for col in df.columns:
        if 'archivo' in col.lower():
            col_archivo = col
            break

    if col_archivo is None:
        print(f"❌ No se encontró columna 'archivo_origen' en Datos Crudos")
        return None

    mask = df[col_archivo].astype(str).str.contains(factura_name, na=False)
    rows = df[mask]

    if rows.empty:
        print(f"❌ No se encontró '{factura_name}' en la hoja Datos Crudos")
        return None

    # Tomar primera coincidencia, convertir a dict
    row = rows.iloc[0]
    return {col: (None if pd.isna(val) else val) for col, val in row.items()}


# ---------------------------------------------------------------------------
# Validación principal
# ---------------------------------------------------------------------------

def validar(gt_data, ext_data, factura_name):
    """Compara GT contra datos extraídos del Excel."""
    ignorar = {'_factura', '_tipo', '_notas', 'archivo_origen'}

    # Aplanar GT (sin listas)
    gt_escalares = {}
    gt_listas = {}
    for k, v in gt_data.items():
        if k in ignorar:
            continue
        if isinstance(v, list):
            gt_listas[k] = v
        elif isinstance(v, dict):
            flat = flatten_dict(v, k)
            gt_escalares.update(flat)
        else:
            gt_escalares[k] = v

    # --- ESCALARES ---
    print(f"\n{'='*70}")
    print(f"📋 CAMPOS ESCALARES — {factura_name}")
    print(f"{'='*70}")

    total, aciertos, errores, parciales = 0, 0, [], []

    for campo_gt, gt_val in gt_escalares.items():
        total += 1
        ext_val = ext_data.get(campo_gt)
        match, detalle = comparar_valor(gt_val, ext_val)
        if match:
            aciertos += 1
            if "Parcial" in detalle:
                parciales.append(f"  {campo_gt}: {detalle}")
        else:
            errores.append(f"  {campo_gt}: {detalle}")

    pct = (aciertos / total * 100) if total > 0 else 0
    print(f"\n  Evaluados: {total} | Aciertos: {aciertos} | Errores: {len(errores)} | Parciales: {len(parciales)}")
    print(f"  Precisión escalares: {pct:.1f}%")

    if errores:
        print("\n  🔴 ERRORES:")
        for e in errores:
            print(f"    {e}")
    if parciales:
        print("\n  🟡 PARCIALES:")
        for p in parciales:
            print(f"    {p}")

    # --- LISTAS ---
    total_lista, aciertos_lista = 0, 0
    errores_lista = []

    for campo_lista, gt_list in gt_listas.items():
        if gt_list is None:
            continue

        print(f"\n{'='*70}")
        print(f"📊 LISTA: {campo_lista}")
        print(f"{'='*70}")

        # En Datos Crudos, las listas se serializan como string
        ext_raw = ext_data.get(campo_lista)
        if ext_raw is None:
            # Intentar buscar columna que empiece con el nombre de la lista
            for col, val in ext_data.items():
                if col == campo_lista:
                    ext_raw = val
                    break

        ext_list = None
        if isinstance(ext_raw, str):
            try:
                ext_list = json.loads(ext_raw.replace("'", '"'))
            except (json.JSONDecodeError, ValueError):
                try:
                    import ast
                    ext_list = ast.literal_eval(ext_raw)
                except:
                    pass
        elif isinstance(ext_raw, list):
            ext_list = ext_raw

        if ext_list is None:
            print(f"  ❌ No se pudo parsear la lista del Excel")
            total_lista += len(gt_list) * 3  # estimado
            continue

        for i, gt_item in enumerate(gt_list):
            if i >= len(ext_list):
                campos_item = len(gt_item) if isinstance(gt_item, dict) else 1
                total_lista += campos_item
                errores_lista.append(f"  {campo_lista}[{i}]: faltante en extracción")
                continue

            ext_item = ext_list[i]
            if isinstance(gt_item, dict) and isinstance(ext_item, dict):
                for key in gt_item:
                    total_lista += 1
                    if key in ext_item:
                        match, det = comparar_valor(gt_item[key], ext_item[key])
                        if match:
                            aciertos_lista += 1
                        else:
                            errores_lista.append(f"  {campo_lista}[{i}].{key}: {det}")
                    else:
                        errores_lista.append(f"  {campo_lista}[{i}].{key}: campo faltante")

        pct_l = (aciertos_lista / total_lista * 100) if total_lista > 0 else 0
        if errores_lista:
            err_count = sum(1 for e in errores_lista if campo_lista in e)
            print(f"  Errores en esta lista: {err_count}")
            for e in errores_lista:
                if campo_lista in e and "❌" in e:
                    print(f"    {e}")

    # --- RESUMEN FINAL ---
    total_global = total + total_lista
    aciertos_global = aciertos + aciertos_lista
    pct_global = (aciertos_global / total_global * 100) if total_global > 0 else 0

    print(f"\n{'='*70}")
    print(f"📈 RESUMEN FINAL — {factura_name}")
    print(f"{'='*70}")
    print(f"  Escalares:  {aciertos}/{total} ({pct:.1f}%)")
    if total_lista > 0:
        pct_l = (aciertos_lista / total_lista * 100)
        print(f"  Listas:     {aciertos_lista}/{total_lista} ({pct_l:.1f}%)")
    print(f"  ─────────────────────────────")
    print(f"  TOTAL:      {aciertos_global}/{total_global} ({pct_global:.1f}%)")
    print(f"{'='*70}\n")

    return {"total": total_global, "aciertos": aciertos_global, "precision": pct_global}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    gt_path = os.path.join(project_root, "facturas_tipos", "ground_truth.json")

    # Cargar ground truth
    with open(gt_path, 'r', encoding='utf-8') as f:
        all_gt = json.load(f)

    # Buscar reporte más reciente
    excel_path = buscar_reporte_reciente()
    if not excel_path:
        print("❌ No se encontró ningún reporte en reportes/")
        return

    print(f"📂 Reporte: {os.path.basename(excel_path)}")
    print(f"   Ruta:    {excel_path}\n")

    # Validar solo factura 1 (o todas si se desea)
    factura_target = "tipo_factura_1.pdf"

    gt = None
    for item in all_gt:
        if item.get("_factura") == factura_target:
            gt = item
            break

    if not gt:
        print(f"❌ Ground truth no encontrado para '{factura_target}'")
        return

    ext_data = leer_datos_crudos(excel_path, factura_target)
    if not ext_data:
        return

    validar(gt, ext_data, factura_target)


if __name__ == "__main__":
    main()
