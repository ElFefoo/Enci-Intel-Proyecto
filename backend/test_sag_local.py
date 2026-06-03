"""
Test local del agente SAG — NO requiere Firestore ni GCS.

Uso:
    cd backend
    pip install httpx pandas openpyxl
    python test_sag_local.py
"""

import asyncio
from io import BytesIO

import httpx
import pandas as pd

# URL principal SAG
SAG_URL_PRINCIPAL = (
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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel, */*",
    "Referer": "https://medicamentos.sag.gob.cl/ConsultaUsrPublico/BusquedaMedicamentos.asp",
}


def intentar_parsear(content: bytes) -> pd.DataFrame | None:
    """Intenta parsear el contenido como Excel con distintos motores."""
    for engine in ["openpyxl", "xlrd"]:
        try:
            df = pd.read_excel(BytesIO(content), dtype=str, engine=engine)
            return df
        except Exception:
            continue
    return None


async def main():
    print("=" * 60)
    print(" DIAGNÓSTICO SAG")
    print("=" * 60)

    headers = HEADERS

    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        print(f"\n[1] GET {SAG_URL_PRINCIPAL[:80]}...")
        r = await client.get(SAG_URL_PRINCIPAL, headers=headers)

    print(f"    HTTP {r.status_code}")
    print(f"    Content-Type: {r.headers.get('content-type', 'N/A')}")
    print(f"    Tamaño: {len(r.content):,} bytes")
    print(f"    Primeros 200 bytes: {r.content[:200]}")

    # Detectar si es HTML
    inicio = r.content[:20].lower()
    if b"<html" in inicio or b"<!doctype" in inicio or len(r.content) < 5000:
        print("\n  ⚠️  La respuesta parece HTML o está vacía, no es un Excel válido.")
        print("  Contenido completo de la respuesta:")
        print("-" * 40)
        try:
            print(r.text)
        except Exception:
            print(r.content)
        print("-" * 40)
        print("\n  → El SAG posiblemente requiere una sesión previa o cambio de URL.")
        print("  Prueba abrir esta URL manualmente en el navegador:")
        print(f"  {SAG_URL_PRINCIPAL}")
        return

    # Intentar parsear
    print("\n[2] Intentando parsear como Excel...")
    df = intentar_parsear(r.content)

    if df is None:
        print("  ❌ No se pudo parsear. Guardando respuesta en 'sag_response.bin' para inspección.")
        with open("sag_response.bin", "wb") as f:
            f.write(r.content)
        print("  Abre 'sag_response.bin' con Excel o un editor hex para ver qué devolvió.")
        return

    df.columns = df.columns.str.strip()
    print(f"  ✅ Parseado OK — {len(df):,} filas, columnas: {list(df.columns)}")

    # Detectar columna importador
    col = next((c for c in df.columns if "importador" in c.lower() or "registrante" in c.lower()), None)
    if col is None:
        print(f"  ⚠️  No se encontró columna de importador. Columnas: {list(df.columns)}")
        return

    print(f"\n[3] Columna importador: '{col}'")
    importadores = sorted(df[col].str.strip().str.upper().dropna().unique())
    print(f"    Total importadores únicos: {len(importadores)}")
    print("\n    IMPORTADORES EN EL SAG (marca ✅ = ya está en COMPETIDORES):")
    for imp in importadores:
        marca = "✅" if imp in COMPETIDORES else "  "
        print(f"    {marca}  {imp}")

    df[col] = df[col].str.strip().str.upper()
    df_comp = df[df[col].isin(COMPETIDORES)]
    print(f"\n[4] Registros de competidores: {len(df_comp):,}")
    if len(df_comp) > 0:
        for empresa, grupo in df_comp.groupby(col):
            print(f"      {empresa}: {len(grupo)} productos")
        print("\n✅ Test completado correctamente")
    else:
        print("  ⚠️  0 registros. Copia los nombres exactos de la lista de arriba a COMPETIDORES.")


if __name__ == "__main__":
    asyncio.run(main())
