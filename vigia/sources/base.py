"""
Clase abstracta base para todas las fuentes.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class RawItem:
    """
    Resultado crudo devuelto por una fuente antes de pasar por el extractor.

    El campo `text` contiene todo el texto relevante para aplicar las reglas
    de matching (título + descripción + cuerpo si está disponible).

    El flujo previsto es:
        sources/*.py  →  extractor.py  →  [future enricher.py]  →  notifier.py

    El extractor recibe RawItem y devuelve Item (o None si no hay match).
    El enricher, cuando exista, recibirá Item y devolverá Item enriquecido.
    """
    source: str
    url: str
    title: str
    date: date
    text: str = ""                   # texto adicional para matching (resumen, cuerpo…)
    extra: dict = field(default_factory=dict)  # metadatos opcionales por fuente


class Source(ABC):
    """
    Interfaz común para todas las fuentes de datos.

    Subclases deben implementar únicamente `fetch`.
    """

    name: str = ""  # identificador corto, p.ej. "boe", "bocm"

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"vigia.sources.{self.name}")
        # Errores no bloqueantes detectados durante fetch() (HTTP 4xx/5xx,
        # parsing fallido, etc.). main.py los recoge tras la ejecución y los
        # incluye en la notificación de Telegram para que las caídas de
        # fuentes sean visibles sin tener que mirar los logs de Actions.
        self.last_errors: list[str] = []

    # URL representativa para el probe de salud. Cada fuente activa debe
    # declarar una. Las fuentes-stub (Metro, administracion.gob) la dejan
    # como None y devuelven "skipped" desde probe().
    probe_url: Optional[str] = None

    @abstractmethod
    def fetch(self, since_date: date) -> list[RawItem]:
        """
        Obtiene ítems publicados a partir de `since_date`.

        Debe ser tolerante a fallos: si una operación parcial falla, capturarla
        con `try/except`, hacer `logger.warning(...)` Y añadir un mensaje a
        `self.last_errors` para que sea reportado en la notificación. Solo
        levantar la excepción si el fallo impide cualquier extracción útil.
        """

    def probe(self, timeout: int = 10) -> dict:
        """
        Comprobación ligera de salud de la fuente: hace un HEAD/GET a
        `probe_url` y devuelve un dict con el resultado.

        Útil para detectar URLs caídas o cambiadas sin necesidad de bajar
        contenido pesado ni parsear nada. Se ejecuta como paso del workflow
        diario en GitHub Actions y los resultados quedan en los logs.

        Devuelve:
            {
              "name":   nombre de la fuente,
              "status": "ok" | "error" | "skipped",
              "code":   código HTTP (si aplica),
              "url":    URL probada,
              "detail": mensaje legible,
            }
        """
        if not self.probe_url:
            return {
                "name": self.name,
                "status": "skipped",
                "code": None,
                "url": None,
                "detail": "fuente sin probe_url (stub o cobertura delegada)",
            }

        # Algunos servidores no aceptan HEAD; si HEAD falla con 4xx/5xx no
        # asumimos caída — caemos a un GET ligero con `stream=True` para no
        # bajarnos el cuerpo.
        try:
            resp = requests.head(
                self.probe_url,
                headers=self._default_headers(),
                timeout=timeout,
                allow_redirects=True,
            )
            if resp.status_code >= 400:
                # Reintento con GET (algunos servidores rechazan HEAD).
                resp = requests.get(
                    self.probe_url,
                    headers=self._default_headers(),
                    timeout=timeout,
                    allow_redirects=True,
                    stream=True,
                )
                resp.close()
        except Exception as exc:
            return {
                "name": self.name,
                "status": "error",
                "code": None,
                "url": self.probe_url,
                "detail": str(exc),
            }

        if resp.status_code >= 400:
            return {
                "name": self.name,
                "status": "error",
                "code": resp.status_code,
                "url": self.probe_url,
                "detail": resp.reason,
            }

        # HTTP OK: validación de contenido opcional (anti "probe ≠ runtime",
        # CLAUDE.md regla 9). Si la fuente implementa `probe_content_count()`
        # y devuelve 0, el selector/regex no rinde nada aunque la URL responda
        # 200 → parser roto / estructura cambiada.
        try:
            count = self.probe_content_count()
        except Exception as exc:
            return {
                "name": self.name,
                "status": "error",
                "code": resp.status_code,
                "url": self.probe_url,
                "detail": f"content-check falló: {exc}",
            }
        if count == 0:
            return {
                "name": self.name,
                "status": "error",
                "code": resp.status_code,
                "url": self.probe_url,
                "detail": "HTTP OK pero el selector no devolvió elementos (posible parser roto)",
            }

        return {
            "name": self.name,
            "status": "ok",
            "code": resp.status_code,
            "url": self.probe_url,
            "detail": "",
        }

    def probe_content_count(self) -> Optional[int]:
        """Nº de contenedores CRUDOS que el selector de listado devuelve hoy.

        Override opcional para el health-check reforzado (anti "probe ≠
        runtime"): `None` (default) = el probe solo valida HTTP (comportamiento
        histórico); `0` = el selector no rinde nada (parser roto / estructura
        cambiada) y el probe lo marca `error`. Se cuentan contenedores CRUDOS
        —antes del filtro fast-keyword— para no confundir "parser roto" (0
        filas) con "0 ofertas relevantes hoy".
        """
        return None

    def _probe_count_selector(
        self,
        url: str,
        selector: str,
        exclude_classes: tuple[str, ...] = (),
        timeout: int = 15,
    ) -> int:
        """Helper para `probe_content_count` en fuentes con selector CSS: hace
        GET a `url` y cuenta los elementos que casan `selector`, descartando
        los que lleven alguna de `exclude_classes`."""
        from bs4 import BeautifulSoup

        resp = requests.get(
            url, headers=self._default_headers(), timeout=timeout,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        excl = set(exclude_classes)
        count = 0
        for el in soup.select(selector):
            if excl and (set(el.get("class") or []) & excl):
                continue
            count += 1
        return count

    def _default_headers(self) -> dict[str, str]:
        from vigia.config import USER_AGENT
        return {"User-Agent": USER_AGENT}
