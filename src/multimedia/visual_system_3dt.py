"""
NIVEL 7: MULTIMODAL - Processamento de Imagens, Mapas e OCR
Extrai e integra elementos visuais dos PDFs do 3D&T ao sistema.
"""

from __future__ import annotations

import hashlib
import io
import json
import logging
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    logging.warning("PyMuPDF nao instalado. Extracao de imagens limitada.")

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    logging.warning("Pillow nao instalado. Processamento de imagens indisponivel.")

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False
    logging.warning("Tesseract nao instalado. OCR indisponivel.")


class TipoVisual(Enum):
    """Tipos de elemento visual em RPGs."""
    ILUSTRACAO_MONSTRO = "ilustracao_monstro"
    ILUSTRACAO_PERSONAGEM = "ilustracao_personagem"
    ILUSTRACAO_EQUIPAMENTO = "ilustracao_equipamento"
    MAPA_DUNGEON = "mapa_dungeon"
    MAPA_REGIAO = "mapa_regiao"
    MAPA_COMBATE = "mapa_combate"
    FICHA_PERSONAGEM = "ficha_personagem"
    FICHA_MONSTRO = "ficha_monstro"
    DIAGRAMA = "diagrama"
    TABELA_IMAGEM = "tabela_imagem"
    DECORATIVO = "decorativo"
    DESCONHECIDO = "desconhecido"


@dataclass
class ElementoVisual:
    """Elemento visual extraido de PDF."""
    id: str
    tipo: TipoVisual
    source: str
    pagina: int
    dimensoes: Tuple[int, int]
    formato: str
    tamanho_bytes: int
    path: Path
    contexto_texto: str
    entidades_relacionadas: List[str]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tipo": self.tipo.value,
            "source": self.source,
            "pagina": self.pagina,
            "dimensoes": list(self.dimensoes),
            "formato": self.formato,
            "tamanho_bytes": self.tamanho_bytes,
            "tamanho_kb": round(self.tamanho_bytes / 1024, 2),
            "path": str(self.path),
            "contexto": (self.contexto_texto or "")[:200],
            "entidades": self.entidades_relacionadas,
            "metadata": self.metadata,
        }


@dataclass
class MapaProcessado:
    """Mapa com metadados de processamento."""
    id: str
    nome: str
    tipo: TipoVisual
    dimensoes_pixels: Tuple[int, int]
    escala: Optional[str]
    pontos_interesse: List[Dict[str, Any]]
    conexoes: List[Dict[str, Any]]
    areas_perigosas: List[Dict[str, Any]]
    notas_mestre: str
    imagem_path: Path

    def gerar_descricao_textual(self) -> str:
        """Gera descricao textual do mapa para RAG."""
        linhas = [
            f"MAPA: {self.nome}",
            f"Tipo: {self.tipo.value}",
            f"Dimensoes: {self.dimensoes_pixels[0]}x{self.dimensoes_pixels[1]} pixels",
            f"Escala: {self.escala or 'Nao especificada'}",
            "",
            "PONTOS DE INTERESSE:",
        ]
        for poi in self.pontos_interesse:
            linhas.append(
                f"  - {poi.get('label', '?')} "
                f"({poi.get('x')}, {poi.get('y')}): {poi.get('descricao', '')}"
            )
        if self.areas_perigosas:
            linhas.extend(["", "AREAS PERIGOSAS:"])
            for area in self.areas_perigosas:
                linhas.append(f"  - {area.get('nome', '?')}: {area.get('descricao', '')}")
        if self.conexoes:
            linhas.extend(["", "CONEXOES:"])
            for conn in self.conexoes:
                linhas.append(
                    f"  - {conn.get('de', '?')} -> {conn.get('para', '?')} "
                    f"({conn.get('tipo', 'caminho')})"
                )
        return "\n".join(linhas)


@dataclass
class FichaOCR:
    """Resultado de OCR em ficha de personagem."""
    nome_jogador: Optional[str]
    nome_personagem: Optional[str]
    raca: Optional[str]
    classe: Optional[str]
    nivel: Optional[int]
    atributos: Dict[str, Optional[int]]
    pericias: List[str]
    equipamento: List[str]
    validacao: Dict[str, Any]
    texto_bruto: str
    imagem_path: Optional[Path]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nome_personagem": self.nome_personagem,
            "nome_jogador": self.nome_jogador,
            "raca": self.raca,
            "classe": self.classe,
            "nivel": self.nivel,
            "atributos": self.atributos,
            "pericias": self.pericias[:5],
            "equipamento": self.equipamento[:3],
            "validacao": self.validacao,
        }


class VisualProcessor3DT:
    """
    Processador visual completo para 3D&T.
    Extrai, classifica e processa elementos visuais dos PDFs.
    """

    def __init__(self, output_dir: str = "data/visual") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.img_dir = self.output_dir / "imagens"
        self.map_dir = self.output_dir / "mapas"
        self.ficha_dir = self.output_dir / "fichas"
        self.temp_dir = self.output_dir / "temp"
        for d in (self.img_dir, self.map_dir, self.ficha_dir, self.temp_dir):
            d.mkdir(exist_ok=True)

        self.cache_file = self.output_dir / "visual_metadata.json"
        self.elementos: Dict[str, ElementoVisual] = {}
        self.mapas: Dict[str, MapaProcessado] = {}
        self.fichas_ocr: Dict[str, FichaOCR] = {}
        self._carregar_cache()

        print("VisualProcessor inicializado")
        print(f"   Diretorio: {self.output_dir}")
        print(f"   Elementos cacheados: {len(self.elementos)}")

    def _carregar_cache(self) -> None:
        """Carrega metadados de execucoes anteriores."""
        if not self.cache_file.exists():
            return
        try:
            with self.cache_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            for e_data in data.get("elementos", []):
                try:
                    tipo_val = e_data.get("tipo", "desconhecido")
                    if isinstance(tipo_val, str):
                        tipo = TipoVisual(tipo_val)
                    else:
                        tipo = TipoVisual.DESCONHECIDO
                    tamanho_bytes = e_data.get("tamanho_bytes")
                    if tamanho_bytes is None and "tamanho_kb" in e_data:
                        tamanho_bytes = int(float(e_data["tamanho_kb"]) * 1024)
                    else:
                        tamanho_bytes = int(tamanho_bytes or 0)
                    elem = ElementoVisual(
                        id=e_data["id"],
                        tipo=tipo,
                        source=e_data.get("source", ""),
                        pagina=int(e_data.get("pagina", 0)),
                        dimensoes=tuple(e_data.get("dimensoes", [0, 0])[:2]),
                        formato=e_data.get("formato", "png"),
                        tamanho_bytes=tamanho_bytes,
                        path=Path(e_data.get("path", "")),
                        contexto_texto=e_data.get("contexto", ""),
                        entidades_relacionadas=e_data.get("entidades", []),
                        metadata=e_data.get("metadata", {}),
                    )
                    self.elementos[elem.id] = elem
                except (KeyError, ValueError, TypeError) as e:
                    logging.debug("Ignorando elemento no cache: %s", e)
        except (json.JSONDecodeError, OSError) as e:
            logging.warning("Erro ao carregar cache visual: %s", e)

    def _salvar_cache(self) -> None:
        """Persiste metadados no disco."""
        data = {
            "elementos": [e.to_dict() for e in self.elementos.values()],
            "mapas": [
                {
                    "id": m.id,
                    "nome": m.nome,
                    "tipo": m.tipo.value,
                    "dimensoes_pixels": list(m.dimensoes_pixels),
                    "escala": m.escala,
                    "pontos_interesse": m.pontos_interesse,
                    "conexoes": m.conexoes,
                    "areas_perigosas": m.areas_perigosas,
                    "notas_mestre": m.notas_mestre,
                    "imagem_path": str(m.imagem_path),
                }
                for m in self.mapas.values()
            ],
            "fichas": [f.to_dict() for f in self.fichas_ocr.values()],
        }
        with self.cache_file.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def processar_pdf(
        self,
        pdf_path: str,
        extrair_tudo: bool = False,
    ) -> List[ElementoVisual]:
        """Extrai e processa todos os elementos visuais de um PDF."""
        if not HAS_PYMUPDF:
            raise ImportError("PyMuPDF necessario para processar PDFs")
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF nao encontrado: {pdf_path}")

        print(f"\nProcessando: {pdf_path.name}")
        doc = fitz.open(pdf_path)
        elementos_encontrados: List[ElementoVisual] = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            print(f"   Pagina {page_num + 1}/{len(doc)}...")
            texto_pagina = page.get_text()
            image_list = page.get_images(full=True)

            for img_index, img in enumerate(image_list, start=1):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                if not extrair_tudo and len(image_bytes) < 10000:
                    continue

                img_hash = hashlib.md5(image_bytes).hexdigest()[:12]
                elem_id = f"{pdf_path.stem}_p{page_num+1}_{img_hash}"

                if elem_id in self.elementos:
                    elementos_encontrados.append(self.elementos[elem_id])
                    continue

                img_filename = f"{elem_id}.{image_ext}"
                img_path = self.img_dir / img_filename
                img_path.write_bytes(image_bytes)

                dimensoes = (0, 0)
                if HAS_PIL:
                    try:
                        pil_img = Image.open(io.BytesIO(image_bytes))
                        dimensoes = pil_img.size
                    except Exception as e:
                        logging.debug("Erro ao abrir imagem: %s", e)

                tipo = self._classificar_imagem(
                    dimensoes,
                    texto_pagina,
                    img_index,
                    len(image_bytes),
                )
                entidades = self._extrair_entidades_contexto(texto_pagina)

                elemento = ElementoVisual(
                    id=elem_id,
                    tipo=tipo,
                    source=pdf_path.name,
                    pagina=page_num + 1,
                    dimensoes=dimensoes,
                    formato=image_ext,
                    tamanho_bytes=len(image_bytes),
                    path=img_path,
                    contexto_texto=texto_pagina[:500],
                    entidades_relacionadas=entidades,
                    metadata={
                        "xref": xref,
                        "index": img_index,
                        "colorspace": base_image.get("colorspace", "unknown"),
                    },
                )
                self.elementos[elem_id] = elemento
                elementos_encontrados.append(elemento)
                print(
                    f"      [OK] {tipo.value}: {dimensoes[0]}x{dimensoes[1]} "
                    f"({len(image_bytes) // 1024}KB)"
                )

                if tipo in (TipoVisual.FICHA_PERSONAGEM, TipoVisual.FICHA_MONSTRO):
                    self._processar_ocr_ficha(elemento, image_bytes)
                elif tipo in (
                    TipoVisual.MAPA_DUNGEON,
                    TipoVisual.MAPA_REGIAO,
                ):
                    self._processar_mapa(elemento, image_bytes)

        doc.close()
        self._salvar_cache()
        print(f"\n[OK] Total: {len(elementos_encontrados)} elementos processados")
        return elementos_encontrados

    def _classificar_imagem(
        self,
        dimensoes: Tuple[int, int],
        contexto: str,
        index: int,
        tamanho: int,
    ) -> TipoVisual:
        """Classifica o tipo de imagem baseado em heuristicas."""
        width, height = dimensoes
        area = width * height
        razao = width / height if height > 0 else 1
        texto_lower = contexto.lower()

        if any(
            x in texto_lower
            for x in ["ficha", "personagem", "atributos", "forca", "hp", "pm"]
        ):
            if 0.7 < razao < 1.5 and area > 100000:
                return TipoVisual.FICHA_PERSONAGEM

        if razao > 1.5 and area > 200000:
            if any(
                x in texto_lower
                for x in ["mapa", "dungeon", "masmorra", "regiao", "cidade"]
            ):
                if "combate" in texto_lower or "tatico" in texto_lower:
                    return TipoVisual.MAPA_COMBATE
                if "dungeon" in texto_lower or "masmorra" in texto_lower:
                    return TipoVisual.MAPA_DUNGEON
                return TipoVisual.MAPA_REGIAO

        if razao < 0.8 and area > 50000:
            if any(
                x in texto_lower
                for x in ["monstro", "inimigo", "criatura", "besta"]
            ):
                return TipoVisual.ILUSTRACAO_MONSTRO

        if razao < 0.9 and area > 80000:
            if any(
                x in texto_lower
                for x in ["personagem", "npc", "heroi", "aventureiro"]
            ):
                return TipoVisual.ILUSTRACAO_PERSONAGEM

        if area < 50000 and 0.9 < razao < 1.1:
            if any(
                x in texto_lower
                for x in ["arma", "armadura", "item", "equipamento"]
            ):
                return TipoVisual.ILUSTRACAO_EQUIPAMENTO

        if razao > 2.0 and area > 30000 and "tabela" in texto_lower:
            return TipoVisual.TABELA_IMAGEM

        if index <= 2 and area < 100000:
            return TipoVisual.DECORATIVO

        return TipoVisual.DESCONHECIDO

    def _extrair_entidades_contexto(self, texto: str) -> List[str]:
        """Extrai nomes de entidades mencionadas no texto."""
        entidades: List[str] = []
        racas_classes = [
            "humano", "elfo", "anao", "orc", "mago", "guerreiro",
            "ladino", "clerigo",
        ]
        padroes = [
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"([A-Z]{2,})",
        ]
        for padrao in padroes:
            for match in re.findall(padrao, texto[:1000]):
                m = match if isinstance(match, str) else match[0]
                if len(m) > 3 and m.lower() not in racas_classes:
                    entidades.append(m)
        return list(dict.fromkeys(entidades))[:5]

    def _processar_ocr_ficha(
        self, elemento: ElementoVisual, image_bytes: bytes
    ) -> None:
        """Processa OCR em ficha de personagem/monstro."""
        if not HAS_TESSERACT or not HAS_PIL:
            print("      [AVISO] OCR nao disponivel")
            return
        print("      Executando OCR...")
        try:
            custom_config = r"--oem 3 --psm 6 -l por+eng"
            image = Image.open(io.BytesIO(image_bytes))
            img_gray = image.convert("L")
            texto = pytesseract.image_to_string(img_gray, config=custom_config)
            ficha = self._parse_ficha_ocr(texto, elemento)
            self.fichas_ocr[elemento.id] = ficha
            txt_path = self.ficha_dir / f"{elemento.id}.txt"
            txt_path.write_text(texto, encoding="utf-8")
            nome = ficha.nome_personagem or "N/A"
            nivel = ficha.nivel if ficha.nivel is not None else "?"
            print(f"      [OK] OCR: {nome} (Nivel {nivel})")
        except Exception as e:
            print(f"      [ERRO] OCR: {e}")

    def _parse_ficha_ocr(self, texto: str, elemento: ElementoVisual) -> FichaOCR:
        """Extrai campos estruturados do texto OCR."""
        linhas = texto.split("\n")
        texto_lower = texto.lower()
        nome_personagem: Optional[str] = None
        nome_jogador: Optional[str] = None
        raca: Optional[str] = None
        classe: Optional[str] = None
        nivel: Optional[int] = None
        atributos: Dict[str, Optional[int]] = {
            "F": None, "H": None, "R": None, "A": None, "PV": None, "PM": None
        }
        pericias: List[str] = []
        equipamento: List[str] = []
        campos_problematicos: List[str] = []

        for linha in linhas:
            linha_limpa = linha.strip()
            if linha_limpa and len(linha_limpa) > 2:
                if nome_personagem is None:
                    nome_personagem = linha_limpa[:30]
                break

        padroes_atributos = {
            "F": r"[Ff][Oo][Rr][Cc][Aa]?\s*[:=]?\s*(\d+)",
            "H": r"[Hh][Aa][Bb][Ii][Ll][Ii][Dd][Aa][Dd][Ee]?\s*[:=]?\s*(\d+)",
            "R": r"[Rr][Ee][Ss][Ii][Ss][Tt][Ee][Nn][Cc][Ii][Aa]?\s*[:=]?\s*(\d+)",
            "A": r"[Aa][Rr][Mm][Aa][Dd][Uu][Rr][Aa]?\s*[:=]?\s*(\d+)",
            "PV": r"[Pp][Vv]\s*[:=]?\s*(\d+)",
            "PM": r"[Pp][Mm]\s*[:=]?\s*(\d+)",
        }
        for attr, padrao in padroes_atributos.items():
            match = re.search(padrao, texto)
            if match:
                try:
                    atributos[attr] = int(match.group(1))
                except (ValueError, IndexError):
                    campos_problematicos.append(attr)
            else:
                campos_problematicos.append(attr)

        racas = ["humano", "elfo", "elfa", "anao", "orc", "halfling", "gnomo"]
        classes = [
            "guerreiro", "mago", "ladino", "clerigo", "druida",
            "barbaro", "paladino",
        ]
        for r in racas:
            if r in texto_lower:
                raca = r.capitalize()
                break
        for c in classes:
            if c in texto_lower:
                classe = c.capitalize()
                break

        match_nivel = re.search(r"[Nn][Ii][Vv][Ee][Ll]\s*[:=]?\s*(\d+)", texto)
        if match_nivel:
            try:
                nivel = int(match_nivel.group(1))
            except (ValueError, IndexError):
                pass

        for linha in linhas:
            if any(
                x in linha.lower()
                for x in ["pericia", "pericia", "oficio", "conhecimento"]
            ):
                pericias.append(linha.strip()[:50])
            if len(pericias) >= 10:
                break
        for linha in linhas:
            if any(
                x in linha.lower()
                for x in ["arma", "espada", "machado", "arco", "armadura", "escudo", "pocao", "item"]
            ):
                equipamento.append(linha.strip()[:50])
            if len(equipamento) >= 5:
                break

        campos_preenchidos = sum(
            1 for v in [nome_personagem, raca, classe, nivel] if v is not None
        )
        atributos_preenchidos = sum(
            1 for v in atributos.values() if v is not None
        )
        confianca = min(
            (campos_preenchidos * 0.15) + (atributos_preenchidos * 0.1),
            1.0,
        )

        return FichaOCR(
            nome_jogador=nome_jogador,
            nome_personagem=nome_personagem,
            raca=raca,
            classe=classe,
            nivel=nivel,
            atributos=atributos,
            pericias=pericias,
            equipamento=equipamento,
            validacao={
                "confianca_geral": round(confianca, 2),
                "campos_problematicos": campos_problematicos,
                "qualidade_imagem": "media",
            },
            texto_bruto=texto,
            imagem_path=elemento.path,
        )

    def _processar_mapa(
        self, elemento: ElementoVisual, image_bytes: bytes
    ) -> None:
        """Processa estrutura de mapa (simplificado)."""
        print("      Processando estrutura do mapa...")
        mapa = MapaProcessado(
            id=elemento.id,
            nome=f"Mapa {elemento.source} p.{elemento.pagina}",
            tipo=elemento.tipo,
            dimensoes_pixels=elemento.dimensoes,
            escala=None,
            pontos_interesse=[],
            conexoes=[],
            areas_perigosas=[],
            notas_mestre=f"Mapa extraido de {elemento.source}. Use descricao textual para navegacao.",
            imagem_path=elemento.path,
        )
        if elemento.contexto_texto:
            legendas = re.findall(
                r"(\d+)[.)]\s*([^\n]+)",
                elemento.contexto_texto,
            )
            for num, desc in legendas[:10]:
                mapa.pontos_interesse.append({
                    "x": 0,
                    "y": 0,
                    "label": f"Ponto {num}",
                    "descricao": desc.strip(),
                    "tipo": "desconhecido",
                })
        self.mapas[elemento.id] = mapa
        desc_path = self.map_dir / f"{elemento.id}_descricao.txt"
        desc_path.write_text(
            mapa.gerar_descricao_textual(),
            encoding="utf-8",
        )
        print(f"      [OK] Mapa: {len(mapa.pontos_interesse)} POIs detectados")

    def buscar_por_entidade(self, nome_entidade: str) -> List[ElementoVisual]:
        """Busca imagens relacionadas a uma entidade."""
        resultados: List[ElementoVisual] = []
        nome_lower = nome_entidade.lower()
        for elem in self.elementos.values():
            if any(nome_lower in (e or "").lower() for e in elem.entidades_relacionadas):
                resultados.append(elem)
                continue
            if nome_lower in (elem.contexto_texto or "").lower():
                resultados.append(elem)
        return sorted(resultados, key=lambda x: x.tamanho_bytes, reverse=True)

    def listar_por_tipo(self, tipo: TipoVisual) -> List[ElementoVisual]:
        """Lista todos os elementos de um tipo."""
        return [e for e in self.elementos.values() if e.tipo == tipo]

    def gerar_dataset_treinamento(self) -> Dict[str, Any]:
        """Gera dataset para treinamento de modelo de classificacao."""
        dataset: Dict[str, Any] = {
            "metadados": {
                "total_imagens": len(self.elementos),
                "por_tipo": {},
                "fontes": list(set(e.source for e in self.elementos.values())),
            },
            "imagens": [],
        }
        for elem in self.elementos.values():
            tipo = elem.tipo.value
            dataset["metadados"]["por_tipo"][tipo] = (
                dataset["metadados"]["por_tipo"].get(tipo, 0) + 1
            )
            dataset["imagens"].append({
                "path": str(elem.path),
                "tipo": tipo,
                "dimensoes": elem.dimensoes,
                "contexto": elem.contexto_texto[:200],
            })
        dataset_path = self.output_dir / "dataset_treinamento.json"
        dataset_path.write_text(
            json.dumps(dataset, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\n[OK] Dataset gerado: {dataset_path}")
        print(f"   Total: {dataset['metadados']['total_imagens']} imagens")
        for tipo, count in dataset["metadados"]["por_tipo"].items():
            print(f"   - {tipo}: {count}")
        return dataset


def demo_visual() -> VisualProcessor3DT:
    """Demonstracao do sistema visual."""
    print("=" * 80)
    print("NIVEL 7: MULTIMODAL - Processamento Visual 3D&T")
    print("=" * 80)
    processor = VisualProcessor3DT()
    print("\nPara testar com PDF real:")
    print("   processor.processar_pdf('data/raw/3det_manual.pdf')")
    print("\n[OK] Sistema visual pronto!")
    print("   Capacidades:")
    print("   - Extracao de imagens de PDFs")
    print("   - Classificacao automatica (mapas, fichas, ilustracoes)")
    print("   - OCR de fichas de personagem")
    print("   - Geracao de descricoes textuais de mapas")
    print("   - Integracao com sistema RAG (proximo passo)")
    return processor


if __name__ == "__main__":
    demo_visual()
