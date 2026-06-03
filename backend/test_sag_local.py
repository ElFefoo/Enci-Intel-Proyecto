"""
Test local del agente SAG — NO requiere Firestore ni GCS.

Uso:
    cd backend
    pip install structlog httpx pandas openpyxl
    python test_sag_local.py

Qué hace:
  1. Descarga el Excel del SAG directamente (sin pasar por el agente)
  2. Muestra todos los importadores únicos encontrados
  3. Filtra por los competidores configurados y muestra cuántos registros hay
  4. Imprime los primeros 3 registros de cada competidor encontrado
"""

import asyncio
from io import BytesIO

import httpx
import pandas as pd

SAG_EXCEL_URL = (
    "https://medicamentos.sag.gob.cl/ConsultaUsrPublico/BusquedaMedicamentosExcel.asp"
    "?Txt_Numero=|*|&Txt_Tipo=&Txt_NGenerico=|*|&Txt_NComercial=|*|"
    "&Txt_Forma=&Txt_Via=&Txt_Clasificacion=&Txt_Pais=&Txt_Empresa="
    "&Txt_Importador=&Txt_Regimen=&Txt_Especie=&Txt_Principio="
    "&Txt_Condicion=&Txt_Via_Texto=|*|&Txt_Especie_Texto=|*|&Txt_Principio_Texto=|*|"
)

COMPETIDORES = [
    "ZOETIS DE CHILE S.A.",
    "DRAG PHARMA CHILE INVETEC S.A.",
    "AGROVET SPA",
    "ELANCO CHILE SPA",
    "BOEHRINGER INGELHEIM LTDA.",
    "CENTROVET LTDA.",
    "INTERVET CHILE LTDA.",
    "CEVA SALUD ANIMAL CHILE SPA",
    "MSD SALUD ANIMAL CHILE S.A.",
    "VETERQUÍMICA S.A.",
]

COL_IMPORTADOR = "Importador o Registrante"


async def main():
    print("=" * 60)
    print(" TEST SAG LOCAL (sin Firestore ni GCS)")
    print("=" * 60)

    # 1. Descargar
    print("\n[1] Descargando Excel del SAG...")
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        r = await client.get(SAG_EXCEL_URL)

    print(f"    HTTP {r.status_code} — {len(r.content):,} bytes")
    assert r.status_code == 200, f"Error HTTP: {r.status_code}"
    assert "html" not in r.headers.get("content-type", "").lower(), "SAG devolvió HTML"
    print("    ✅ Descarga OK")

    # 2. Parsear
    print("\n[2] Parseando Excel...")
    df = pd.read_excel(BytesIO(r.content), dtype=str)
    df.columns = df.columns.str.strip()
    print(f"    Total filas: {len(df):,}")
    print(f"    Columnas: {list(df.columns)}")

    # 3. Importadores únicos — útil para verificar nombres exactos
    col = None
    for c in df.columns:
        if "importador" in c.lower() or "registrante" in c.lower():
            col = c
            break

    if col is None:
        print("\n  ⚠️  No se encontró columna de importador. Columnas disponibles:")
        for c in df.columns:
            print(f"       - {c}")
        return

    print(f"\n[3] Columna detectada: '{col}'")
    importadores = sorted(df[col].str.strip().str.upper().dropna().unique())
    print(f"    Total importadores únicos: {len(importadores)}")
    print("\n    --- TODOS LOS IMPORTADORES EN EL SAG ---")
    for imp in importadores:
        en_lista = "✅" if imp in COMPETIDORES else "  "
        print(f"    {en_lista}  {imp}")

    # 4. Filtrar por competidores configurados
    df[col] = df[col].str.strip().str.upper()
    df_comp = df[df[col].isin(COMPETIDORES)]
    print(f"\n[4] Registros de competidores configurados: {len(df_comp):,}")

    if len(df_comp) == 0:
        print("\n  ⚠️  NINGUNO encontrado. Revisa los nombres en COMPETIDORES arriba.")
        print("       Copia los nombres exactos de la lista de importadores mostrada arriba.")
        return

    print("\n    Por empresa:")
    for empresa, grupo in df_comp.groupby(col):
        print(f"      {empresa}: {len(grupo)} productos")

    print("\n✅ Test completado correctamente")


if __name__ == "__main__":
    asyncio.run(main())
