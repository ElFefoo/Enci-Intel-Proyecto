"""Agente SAG — Monitor del Registro Oficial de Medicamentos Veterinarios.

Hereda de BaseAgent y sigue el pipeline: fetch → process → save → generate_alerts.

El SAG usa sesiones ASP clásicas: primero hay que visitar la página de búsqueda
para obtener las cookies de sesión, y luego hacer el request al Excel dentro
de la misma sesión HTTP.
"""

from io import BytesIO
from html import unescape
import re

import httpx
import pandas as pd

from .base_agent import BaseAgent

# ── URLs SAG ────────────────────────────────────────────────────────────

SAG_BASE       = "https://medicamentos.sag.gob.cl/ConsultaUsrPublico"
SAG_BUSQUEDA   = f"{SAG_BASE}/BusquedaMedicamentos.asp"
SAG_EXCEL_URL  = (
    f"{SAG_BASE}/BusquedaMedicamentosExcel.asp"
    "?Txt_Numero=|*|&Txt_Tipo=&Txt_NGenerico=|*|&Txt_NComercial=|*|"
    "&Txt_Forma=&Txt_Via=&Txt_Clasificacion=&Txt_Pais=&Txt_Empresa="
    "&Txt_Importador=&Txt_Regimen=&Txt_Especie=&Txt_Principio="
    "&Txt_Condicion=&Txt_Via_Texto=|*|&Txt_Especie_Texto=|*|&Txt_Principio_Texto=|*|"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml,*/*",
    "Accept-Language": "es-CL,es;q=0.9",
}

# ── GCS ─────────────────────────────────────────────────────────────────────

GCS_BUCKET         = "enci-intel-data"
GCS_LATEST_PATH    = "sag/latest.xlsx"
GCS_HISTORICO_PATH = "sag/historico/{fecha}.xlsx"

# ── Competidores ───────────────────────────────────────────────────────────

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

COL_IMPORTADOR    = "Importador o Registrante"
COL_REGISTRO      = "Registro"
COL_NOMBRE_COM    = "Nombre Comercial"
COL_NOMBRE_COM2   = "Nombre comercial"   # variante en el HTML
COL_ESPECIES      = "Especies"
COL_PRINCIPIOS    = "Principios Activos"
COL_CLASIFICACION = "Clasificación"


class SagAgent(BaseAgent):
    """Monitorea el registro SAG y detecta nuevos SKUs y cancelaciones."""

    def __init__(self, db):
        super().__init__(agent_id="sag-monitor", db=db)
        self._es_seed: bool = False

    # ── 1. fetch ──────────────────────────────────────────────────────────────

    async def fetch(self) -> list[dict]:
        """Establece sesión ASP, luego descarga el Excel del SAG."""
        self.log.info("sag_downloading")

        async with httpx.AsyncClient(
            timeout=60, follow_redirects=True, headers=HEADERS
        ) as client:
            # Paso 1: visitar la página principal para obtener cookies de sesión
            await client.get(SAG_BUSQUEDA)

            # Paso 2: descargar el Excel dentro de la misma sesión
            r = await client.get(SAG_EXCEL_URL)

        if r.status_code != 200:
            raise RuntimeError(f"SAG respondió HTTP {r.status_code}")

        content = r.content
        self.log.info("sag_downloaded", bytes=len(content))

        # El SAG devuelve HTML con Content-Type: application/vnd.ms-excel
        # Detectar si es HTML y parsearlo como tabla, o si es Excel binario
        es_html = content[:20].lower().lstrip().startswith(b"<")
        if es_html:
            df = self._parsear_html(content)
        else:
            df = self._parsear_excel(content)

        if df.empty:
            raise RuntimeError("SAG devolvió respuesta vacía o sin datos válidos.")

        self.log.info("sag_parsed", total_filas=len(df))

        # Guardar raw en GCS (falla silenciosamente en desarrollo)
        self._guardar_gcs(content)

        # Filtrar por competidores
        df = self._filtrar_competidores(df)
        self.log.info("sag_filtered", competidores=len(df))
        return df.to_dict(orient="records")

    # ── 2. process ────────────────────────────────────────────────────────────

    async def process(self, raw_data: list[dict]) -> list[dict]:
        """Determina si es seed o monitor y detecta diferencias."""
        registros_sag = {str(r.get(COL_REGISTRO, "")).strip() for r in raw_data}

        docs_stream = self.db.collection("products").where("source", "==", "SAG").stream()
        registros_db = {}
        async for doc in docs_stream:
            registros_db[doc.id] = doc.to_dict()

        if not registros_db:
            self._es_seed = True
            self.log.info("sag_seed_mode")
            return raw_data

        nuevos = [r for r in raw_data if f"sag_{str(r.get(COL_REGISTRO, '')).strip()}" not in registros_db]
        cancelados = [
            v for k, v in registros_db.items()
            if k.replace("sag_", "") not in registros_sag
        ]
        self._cancelados = cancelados
        self.log.info("sag_diff", nuevos=len(nuevos), cancelados=len(cancelados))
        return nuevos

    # ── 3. save ───────────────────────────────────────────────────────────────

    async def save(self, data: list[dict]) -> None:
        from datetime import datetime, timezone
        now   = datetime.now(timezone.utc)
        batch = self.db.batch()
        count = 0

        for row in data:
            doc_id  = f"sag_{str(row.get(COL_REGISTRO, '')).strip()}"
            doc_ref = self.db.collection("products").document(doc_id)
            batch.set(doc_ref, {
                **row,
                "source":     "SAG",
                "cancelado":  False,
                "created_at": now,
                "updated_at": now,
            })
            count += 1
            if count % 499 == 0:
                await batch.commit()
                batch = self.db.batch()

        for p in getattr(self, "_cancelados", []):
            doc_id  = f"sag_{str(p.get(COL_REGISTRO, '')).strip()}"
            doc_ref = self.db.collection("products").document(doc_id)
            batch.update(doc_ref, {"cancelado": True, "updated_at": now})

        await batch.commit()
        self.log.info("sag_saved", count=count)

    # ── 4. generate_alerts ────────────────────────────────────────────────────

    async def generate_alerts(self, data: list[dict]) -> int:
        if self._es_seed:
            return 0

        from datetime import datetime, timezone
        now   = datetime.now(timezone.utc)
        batch = self.db.batch()
        count = 0

        nombre_col = COL_NOMBRE_COM if COL_NOMBRE_COM in (data[0] if data else {}) else COL_NOMBRE_COM2

        for p in data:
            ref = self.db.collection("alerts").document()
            batch.set(ref, {
                "type":     "NEWSKU",
                "source":   "SAG",
                "severity": "medium",
                "title":    f"Nuevo registro SAG: {p.get(nombre_col, p.get(COL_NOMBRE_COM2, 'Sin nombre'))}",
                "body": (
                    f"Empresa: {p.get(COL_IMPORTADOR, '')}\n"
                    f"Especie: {p.get(COL_ESPECIES, '')}\n"
                    f"Principio activo: {p.get(COL_PRINCIPIOS, '')}\n"
                    f"Clasificación: {p.get(COL_CLASIFICACION, '')}"
                ),
                "metadata": p,
                "read":       False,
                "created_at": now,
            })
            count += 1

        for p in getattr(self, "_cancelados", []):
            ref = self.db.collection("alerts").document()
            batch.set(ref, {
                "type":     "CANCELACION",
                "source":   "SAG",
                "severity": "high",
                "title":    f"Registro SAG cancelado: {p.get(COL_NOMBRE_COM, p.get(COL_NOMBRE_COM2, 'Sin nombre'))}",
                "body":     f"Empresa: {p.get(COL_IMPORTADOR, '')}\nEl producto ya no aparece en el registro oficial SAG.",
                "metadata": p,
                "read":       False,
                "created_at": now,
            })
            count += 1

        await batch.commit()
        return count

    # ── Helpers privados ──────────────────────────────────────────────────────

    def _parsear_html(self, content: bytes) -> pd.DataFrame:
        """Parsea la tabla HTML que devuelve el SAG (formato real)."""
        try:
            dfs = pd.read_html(BytesIO(content), encoding="utf-8", flavor="lxml")
        except Exception:
            dfs = pd.read_html(BytesIO(content), encoding="utf-8")
        if not dfs:
            return pd.DataFrame()
        df = dfs[0].copy()
        df.columns = df.columns.str.strip()
        return df.fillna("").astype(str)

    def _parsear_excel(self, content: bytes) -> pd.DataFrame:
        """Parsea un Excel binario real (.xls/.xlsx)."""
        for engine in ["openpyxl", "xlrd"]:
            try:
                df = pd.read_excel(BytesIO(content), dtype=str, engine=engine)
                df.columns = df.columns.str.strip()
                return df.fillna("")
            except Exception:
                continue
        return pd.DataFrame()

    def _filtrar_competidores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filtra el DataFrame por la lista de competidores."""
        col = next(
            (c for c in df.columns if "importador" in c.lower() or "registrante" in c.lower()),
            None,
        )
        if col is None:
            self.log.warning("sag_col_importador_no_encontrada", columns=list(df.columns))
            return pd.DataFrame()
        df[col] = df[col].str.strip().str.upper()
        return df[df[col].isin(COMPETIDORES)].copy()

    def _guardar_gcs(self, content: bytes) -> None:
        from datetime import datetime, timezone
        try:
            from google.cloud import storage  # lazy import
            client = storage.Client()
            bucket = client.bucket(GCS_BUCKET)
            fecha  = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            for path in [GCS_LATEST_PATH, GCS_HISTORICO_PATH.format(fecha=fecha)]:
                bucket.blob(path).upload_from_string(content)
            self.log.info("sag_gcs_saved")
        except Exception as e:
            self.log.warning("sag_gcs_error", error=str(e))
