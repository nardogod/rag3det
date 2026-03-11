"""
Processamento de elementos visuais dos PDFs 3D&T.
Extrai e referencia imagens, mapas e diagramas.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import fitz  # PyMuPDF
from PIL import Image

from src.rag.hybrid_retriever import HybridRetriever, RetrievedContext


class VisualExtractor:
    """Extrai e indexa elementos visuais dos PDFs."""

    def __init__(self, output_dir: str = "data/visuals") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.visual_index: List[Dict[str, Any]] = []

    def extract_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extrai todas as imagens de um PDF.
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")

        extracted: List[Dict[str, Any]] = []
        doc = fitz.open(pdf_path)

        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                images = page.get_images()

                for img_index, img in enumerate(images, 1):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image.get("ext", "png")

                    img_hash = hashlib.md5(image_bytes).hexdigest()[:12]
                    filename = f"{pdf_path.stem}_p{page_num + 1}_{img_hash}.{image_ext}"
                    img_path = self.output_dir / filename

                    with img_path.open("wb") as f:
                        f.write(image_bytes)

                    context = self._extract_image_context(page, img)

                    info = {
                        "id": img_hash,
                        "source": pdf_path.name,
                        "page": page_num + 1,
                        "filename": filename,
                        "path": str(img_path),
                        "width": img[2],
                        "height": img[3],
                        "context": context,
                        "type": self._classify_image(context, img[2], img[3]),
                    }
                    extracted.append(info)
                    self.visual_index.append(info)
                    self.logger.info(
                        "Imagem extraída: %s (%dx%d) - tipo=%s",
                        filename,
                        img[2],
                        img[3],
                        info["type"],
                    )
        finally:
            doc.close()

        self._save_index()
        return extracted

    def _extract_image_context(self, page: fitz.Page, img: Tuple[Any, ...]) -> str:
        """Extrai texto próximo à imagem para contexto."""
        img_rect = fitz.Rect(img[1])
        expanded = img_rect + (-50, -50, 50, 50)
        text = page.get_text("text", clip=expanded) or ""
        return text.replace("\n", " ").strip()[:500]

    def _classify_image(self, context: str, width: int, height: int) -> str:
        """Classifica tipo de imagem baseado em contexto e dimensões."""
        context_lower = context.lower()

        if any(kw in context_lower for kw in ["mapa", "dungeon", "labirinto", "região", "regiao"]):
            return "map"
        if any(kw in context_lower for kw in ["monstro", "criatura", "inimigo", "besta"]):
            return "monster_illustration"
        if any(kw in context_lower for kw in ["personagem", "npc", "herói", "heroi"]):
            return "character_illustration"
        if any(kw in context_lower for kw in ["arma", "equipamento", "item"]):
            return "equipment_illustration"

        if width > height * 2 or height > width * 2:
            return "banner" if width > 500 else "divider"
        if width < 100 and height < 100:
            return "icon"
        return "illustration"

    def _save_index(self) -> None:
        """Salva índice de imagens em JSON."""
        index_path = self.output_dir / "visual_index.json"
        with index_path.open("w", encoding="utf-8") as f:
            json.dump(self.visual_index, f, indent=2, ensure_ascii=False)

    def search_visuals(self, query: str, visual_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Busca imagens por contexto textual.
        """
        query_lower = query.lower()
        results: List[Dict[str, Any]] = []

        for visual in self.visual_index:
            if visual_type and visual.get("type") != visual_type:
                continue
            context = str(visual.get("context", "")).lower()
            score = sum(1 for word in query_lower.split() if word in context)
            if score > 0:
                v = dict(visual)
                v["relevance_score"] = score
                results.append(v)

        return sorted(results, key=lambda x: x["relevance_score"], reverse=True)

    def get_map_with_annotations(
        self,
        map_filename: str,
        points_of_interest: List[Dict[str, Any]],
    ) -> str:
        """
        Retorna mapa com anotações (referência textual).
        """
        map_path = self.output_dir / map_filename
        if not map_path.exists():
            return f"Mapa {map_filename} não encontrado."

        with Image.open(map_path) as img:
            width, height = img.size

        lines = [
            f"MAPA: {map_filename}",
            f"Dimensões: {width}x{height} pixels",
            "Pontos de interesse:",
        ]
        for i, poi in enumerate(points_of_interest, 1):
            rel_x = (poi["x"] / width) * 100 if width > 0 else 0
            rel_y = (poi["y"] / height) * 100 if height > 0 else 0
            lines.append(
                f"  {i}. {poi.get('label', 'Sem nome')} - "
                f"Posição: {rel_x:.0f}%, {rel_y:.0f}%"
            )
            desc = poi.get("description", "")
            if desc:
                lines.append(f"     {desc}")
        return "\n".join(lines)


class CharacterSheetOCR:
    """OCR para fichas de personagem escaneadas."""

    def __init__(self) -> None:
        try:
            import pytesseract  # type: ignore[import-not-found]

            self.has_tesseract = True
        except ImportError:
            self.has_tesseract = False
            logging.warning("pytesseract não instalado. OCR indisponível.")

    def process_sheet(self, image_path: str) -> Dict[str, Any]:
        """
        Extrai dados de ficha de personagem de uma imagem.
        """
        if not self.has_tesseract:
            return {"erro": "OCR não disponível. Instale pytesseract."}

        import re

        try:
            import pytesseract  # type: ignore[import-not-found]
        except ImportError:
            return {"erro": "pytesseract não disponível no ambiente."}

        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang="por")

        extracted: Dict[str, Any] = {
            "nome": self._extract_field(text, r"[Nn]ome[:\s]+([^\n]+)"),
            "raca": self._extract_field(text, r"[Rr]a[çc]a[:\s]+([^\n]+)"),
            "nivel": self._extract_number(text, r"[Nn][íi]vel[:\s]+(\d+)"),
            "forca": self._extract_number(text, r"[Ff]or[çc]a?[:\s]+(\d+)"),
            "habilidade": self._extract_number(text, r"[Hh]abilidade[:\s]+(\d+)"),
            "resistencia": self._extract_number(text, r"[Rr]esist[êe]ncia[:\s]+(\d+)"),
            "armadura": self._extract_number(text, r"[Aa]rmadura[:\s]+(\d+)"),
            "pv": self._extract_number(text, r"PV[:\s]+(\d+)"),
            "pm": self._extract_number(text, r"PM[:\s]+(\d+)"),
            "raw_text": text[:1000],
        }
        extracted["validacao"] = self._validate_sheet(extracted)
        return extracted

    @staticmethod
    def _extract_field(text: str, pattern: str) -> Optional[str]:
        import re

        match = re.search(pattern, text)
        return match.group(1).strip() if match else None

    def _extract_number(self, text: str, pattern: str) -> Optional[int]:
        val = self._extract_field(text, pattern)
        return int(val) if val and val.isdigit() else None

    def _validate_sheet(self, data: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []

        required = ["nome", "forca", "habilidade", "resistencia", "pv"]
        for field in required:
            if not data.get(field):
                errors.append(f"Campo obrigatório ausente: {field}")

        ranges = {
            "forca": (1, 20),
            "habilidade": (1, 20),
            "resistencia": (1, 20),
            "armadura": (0, 10),
            "pv": (1, 100),
            "pm": (0, 50),
        }
        for field, (min_v, max_v) in ranges.items():
            val = data.get(field)
            if isinstance(val, int) and not (min_v <= val <= max_v):
                warnings.append(f"{field}={val} fora do range típico [{min_v}-{max_v}]")

        if data.get("resistencia") and data.get("pv"):
            pv_expected = data["resistencia"] * 5
            if abs(data["pv"] - pv_expected) > 10:
                warnings.append(
                    f"PV ({data['pv']}) diferente do esperado ({pv_expected}) baseado em Resistência"
                )

        return {"valido": len(errors) == 0, "erros": errors, "avisos": warnings}


def integrate_visuals_with_rag(
    retriever_cls: type[HybridRetriever],
    visual_extractor: VisualExtractor,
) -> type[HybridRetriever]:
    """
    Cria uma subclasse de HybridRetriever que também adiciona contexto visual.
    """

    class VisualEnhancedRetriever(retriever_cls):  # type: ignore[misc]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self.visual = visual_extractor

        def query(self, query_text: str, top_k: int = 10) -> List[RetrievedContext]:
            text_results = super().query(query_text, top_k=top_k - 2)
            visual_results = self.visual.search_visuals(query_text)

            visual_contexts: List[RetrievedContext] = []
            for v in visual_results[:2]:
                ctx_text = f"[IMAGEM: {v['filename']}]\nContexto: {str(v.get('context', ''))[:200]}..."
                score = float(v.get("relevance_score", 0)) / 10.0
                visual_contexts.append(
                    RetrievedContext(
                        content=ctx_text,
                        source=f"visual_{v.get('type', 'unknown')}",
                        score=score,
                        metadata=v,
                        entity_name=None,
                    )
                )

            combined = text_results + visual_contexts
            combined_sorted = sorted(combined, key=lambda x: x.score, reverse=True)
            return combined_sorted[:top_k]

    return VisualEnhancedRetriever

