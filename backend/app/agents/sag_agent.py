"""Agente SAG — Monitor del Registro Oficial de Medicamentos Veterinarios.

Hereda de BaseAgent y sigue el pipeline: fetch → process → save → generate_alerts.
"""

from io import BytesIO

import httpx
import pandas as pd
from google.cloud import storage

from .base_agent import BaseAgent

# ── Configuración ─────────────────────────────────────────────────────────────

SAG_EXCEL_URL = (
    "https://medicamentos.sag.gob.cl/ConsultaUsrPublico/BusquedaMedicamentosExcel.asp"
    "?Txt_Numero=|*|&Txt_Tipo=&Txt_NGenerico=|*|&Txt_NComercial=|*|"
    "&Txt_Forma=&Txt_Via=&Txt_Clasificacion=&Txt_Pais=&Txt_Empresa="
    "&Txt_Importador=&Txt_Regimen=&Txt_Especie=&Txt_Principio="
    "&Txt_Condicion=&Txt_Via_Texto=|*|&Txt_Especie_Texto=|*|&Txt_Principio_Texto=|*|"
)

GCS_BUCKET         = "enci-intel-data"
GCS_LATEST_PATH    = "sag/latest.xlsx"
GCS_HISTORICO_PATH = "sag/historico/{fecha}.xlsx"

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

COL_IMPORTADOR   = "Importador o Registrante"
COL_REGISTRO     = "Registro"
COL_NOMBRE_COM   = "Nombre Comercial"
COL_ESPECIES     = "Especies"
COL_PRINCIPIOS   = "Principios Activos"
COL_CLASIFICACION = "Clasificación"


class SagAgent(BaseAgent):
    """Monitorea el registro SAG y detecta nuevos SKUs y cancelaciones."""

    def __init__(self, db):
        super().__init__(agent_id="sag-monitor", db=db)
        self._es_seed: bool = False  # se determina en fetch()

    # ── 1. fetch ──────────────────────────────────────────────────────────────

    async def fetch(self) -> list[dict]:
        """Descarga el Excel completo del SAG via GET directo."""
        self.log.info("sag_downloading")
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            r = await client.get(SAG_EXCEL_URL)

        if r.status_code != 200:
            raise RuntimeError(f"SAG respondió HTTP {r.status_code}")

        content_type = r.headers.get("content-type", "")
        if "html" in content_type.lower():
            raise RuntimeError(
                "SAG devolvió HTML en vez de Excel — posible cambio en la URL."
            )

        self._raw_bytes = r.content
        self.log.info("sag_downloaded", bytes=len(r.content))

        # Guardar en GCS (latest + histórico)
        self._guardar_gcs(r.content)

        # Parsear y filtrar por competidores
        df = self._parsear(r.content)
        return df.to_dict(orient="records")

    # ── 2. process ────────────────────────────────────────────────────────────

    async def process(self, raw_data: list[dict]) -> list[dict]:
        """Determina si es seed o monitor y detecta diferencias."""
        registros_sag = {str(r[COL_REGISTRO]).strip() for r in raw_data}

        # Registros vigentes en Firestore
        docs_stream = self.db.collection("products").where("source", "==", "SAG").stream()
        registros_db = {}
        async for doc in docs_stream:
            registros_db[doc.id] = doc.to_dict()

        # Primera vez → modo seed
        if not registros_db:
            self._es_seed = True
            self.log.info("sag_seed_mode")
            return raw_data  # guarda todo, sin alertas

        # Modo monitor → detectar diferencias
        nuevos     = [r for r in raw_data if f"sag_{str(r[COL_REGISTRO]).strip()}" not in registros_db]
        cancelados = [
            v for k, v in registros_db.items()
            if k.replace("sag_", "") not in registros_sag
        ]

        self._cancelados = cancelados
        self.log.info("sag_diff", nuevos=len(nuevos), cancelados=len(cancelados))
        return nuevos

    # ── 3. save ───────────────────────────────────────────────────────────────

    async def save(self, data: list[dict]) -> None:
        """Guarda productos nuevos en Firestore. Marca cancelados."""
        from datetime import datetime, timezone
        from google.cloud import firestore

        now   = datetime.now(timezone.utc)
        batch = self.db.batch()
        count = 0

        for row in data:
            doc_id  = f"sag_{str(row[COL_REGISTRO]).strip()}"
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

        # Marcar cancelados (no borrar)
        for p in getattr(self, "_cancelados", []):
            doc_id  = f"sag_{str(p.get(COL_REGISTRO, '')).strip()}"
            doc_ref = self.db.collection("products").document(doc_id)
            batch.update(doc_ref, {"cancelado": True, "updated_at": now})

        await batch.commit()
        self.log.info("sag_saved", count=count)

    # ── 4. generate_alerts ────────────────────────────────────────────────────

    async def generate_alerts(self, data: list[dict]) -> int:
        """Crea alertas NEWSKU y CANCELACION. En modo seed no genera alertas."""
        if self._es_seed:
            return 0

        from datetime import datetime, timezone
        now   = datetime.now(timezone.utc)
        batch = self.db.batch()
        count = 0

        for p in data:
            ref = self.db.collection("alerts").document()
            batch.set(ref, {
                "type":     "NEWSKU",
                "source":   "SAG",
                "severity": "medium",
                "title":    f"Nuevo registro SAG: {p.get(COL_NOMBRE_COM, 'Sin nombre')}",
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
                "title":    f"Registro SAG cancelado: {p.get(COL_NOMBRE_COM, 'Sin nombre')}",
                "body":     f"Empresa: {p.get(COL_IMPORTADOR, '')}\nEl producto ya no aparece en el registro oficial SAG.",
                "metadata": p,
                "read":       False,
                "created_at": now,
            })
            count += 1

        await batch.commit()
        return count

    # ── Helpers privados ──────────────────────────────────────────────────────

    def _parsear(self, content: bytes) -> pd.DataFrame:
        df = pd.read_excel(BytesIO(content), dtype=str)
        df.columns = df.columns.str.strip()
        df[COL_IMPORTADOR] = df[COL_IMPORTADOR].str.strip().str.upper()
        df = df[df[COL_IMPORTADOR].isin(COMPETIDORES)].copy()
        return df.fillna("")

    def _guardar_gcs(self, content: bytes) -> None:
        from datetime import datetime, timezone
        try:
            client = storage.Client()
            bucket = client.bucket(GCS_BUCKET)
            fecha  = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            for path in [GCS_LATEST_PATH, GCS_HISTORICO_PATH.format(fecha=fecha)]:
                bucket.blob(path).upload_from_string(
                    content,
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            self.log.info("sag_gcs_saved")
        except Exception as e:
            self.log.warning("sag_gcs_error", error=str(e))
