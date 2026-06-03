"""
Test local del agente SAG — NO requiere Firestore ni GCS.

Uso:
    cd backend
    pip install httpx pandas openpyxl lxml
    python test_sag_local.py
"""

import asyncio
from io import BytesIO

import httpx
import pandas as pd

SAG_BASE     = "https://medicamentos.sag.gob.cl/ConsultaUsrPublico"
SAG_BUSQUEDA = f"{SAG_BASE}/BusquedaMedicamentos.asp"
SAG_EXCEL    = (
    f"{SAG_BASE}/BusquedaMedicamentosExcel.asp"
    "?Txt_Numero=|*|&Txt_Tipo=&Txt_NGenerico=|*|&Txt_NComercial=|*|"
    "&Txt_Forma=&Txt_Via=&Txt_Clasificacion=&Txt_Pais=&Txt_Empresa="
    "&Txt_Importador=&Txt_Regimen=&Txt_Especie=&Txt_Principio="
    "&Txt_Condicion=&Txt_Via_Texto=|*|&Txt_Especie_Texto=|*|&Txt_Principio_Texto=|*|"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "es-CL,es;q=0.9",
}

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


async def main():
    print("=" * 60)
    print(" TEST SAG LOCAL")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=60, follow_redirects=True, headers=HEADERS) as client:
        # Paso 1: obtener cookies de sesión ASP
        print("\n[1] Iniciando sesión en SAG...")
        r0 = await client.get(SAG_BUSQUEDA)
        print(f"    HTTP {r0.status_code} — cookies: {dict(client.cookies)}")

        # Paso 2: descargar datos
        print("\n[2] Descargando datos del SAG...")
        r = await client.get(SAG_EXCEL)

    print(f"    HTTP {r.status_code} — {len(r.content):,} bytes")
    print(f"    Content-Type: {r.headers.get('content-type', 'N/A')}")

    if r.status_code != 200:
        print(f"  ❌ Error HTTP {r.status_code}")
        return

    # Parsear: el SAG devuelve HTML con Content-Type vnd.ms-excel
    content = r.content
    es_html = content[:50].lower().lstrip().startswith(b"<")
    print(f"\n[3] Formato detectado: {'HTML' if es_html else 'Excel binario'}")

    if es_html:
        try:
            dfs = pd.read_html(BytesIO(content), encoding="utf-8")
            df = dfs[0]
        except Exception as e:
            print(f"  ❌ No se pudo parsear HTML como tabla: {e}")
            print("  Primeros 500 chars:", r.text[:500])
            return
    else:
        df = pd.read_excel(BytesIO(content), dtype=str)

    df.columns = df.columns.str.strip()
    df = df.fillna("").astype(str)
    print(f"  ✅ Parseado OK — {len(df):,} filas")
    print(f"  Columnas: {list(df.columns)}")

    # Detectar columna importador
    col = next((c for c in df.columns if "importador" in c.lower() or "registrante" in c.lower()), None)
    if not col:
        print("  ⚠️  No se encontró columna de importador")
        return

    print(f"\n[4] Columna importador: '{col}'")
    df[col] = df[col].str.strip().str.upper()
    importadores = sorted(df[col].dropna().unique())
    print(f"  Total importadores únicos: {len(importadores)}")

    df_comp = df[df[col].isin(COMPETIDORES)]
    print(f"\n[5] Registros de competidores: {len(df_comp):,}")
    for empresa, grupo in df_comp.groupby(col):
        print(f"  ✅  {empresa}: {len(grupo)} productos")

    if len(df_comp) == 0:
        print("  ⚠️  Ninguno encontrado. Importadores en el SAG:")
        for imp in importadores[:30]:
            print(f"       - {imp}")

    print("\n✅ Test completado")


if __name__ == "__main__":
    asyncio.run(main())
