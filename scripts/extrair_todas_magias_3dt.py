"""
Pipeline completo: Extração em 3 Camadas (Defesa em Profundidade)

Camada 1: Índice (300 nomes)
Camada 2: Páginas (blocos completos por delimitador)
Camada 3: Validação (cruzamento índice × descrição)
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion.extrair_indice_magias import extrair_indice_magias, salvar_indice
from src.ingestion.chunking_magias import extrair_magias_por_delimitador, Magia
from src.ingestion.extrator_magias_flexivel import ExtratorMagiaFlexivel


def _magia_para_dict(m: Magia) -> Dict:
    """Converte Magia dataclass para dict."""
    return {
        "nome": m.nome,
        "escola": m.escola,
        "custo": m.custo,
        "alcance": m.alcance,
        "duracao": m.duracao,
        "descricao": m.descricao,
        "pagina": m.pagina,
        "texto_original": m.texto_original,
    }


def pipeline_completo(caminho_pdf: str | Path | None = None) -> List[Dict]:
    """
    Pipeline completo: índice → extração → validação → correção.
    """
    print("=" * 60)
    print("PIPELINE DE EXTRAÇÃO DE MAGIAS 3D&T (3 Camadas)")
    print("=" * 60)

    # PASSO 1: Índice de referência (ground truth)
    print("\n[Camada 1] Extraindo indice de referencia...")
    try:
        indice_nomes = extrair_indice_magias(caminho_pdf)
        salvar_indice(indice_nomes)
    except (ImportError, FileNotFoundError) as e:
        print(f"   ⚠ Camada 1 falhou: {e}")
        print("   Continuando sem índice (usando apenas extração por delimitador)...")
        indice_nomes = []

    # PASSO 2: Extração por delimitador
    print("\n[Camada 2] Extraindo magias por delimitador...")
    try:
        magias_brutas = extrair_magias_por_delimitador(caminho_pdf)
    except (ImportError, FileNotFoundError) as e:
        print(f"   [!] Camada 2 falhou: {e}")
        magias_brutas = []

    # PASSO 3: Cruzamento índice × extração
    print("\n[Camada 3] Cruzando indice com extracoes...")

    magias_finais: List[Dict] = []
    nomes_encontrados = set()

    magia_por_nome: Dict[str, Magia] = {}
    for m in magias_brutas:
        key = m.nome.strip().lower()
        if key not in magia_por_nome:
            magia_por_nome[key] = m

    if not indice_nomes:
        # Sem índice: usa todas as magias extraídas
        for m in magias_brutas:
            magias_finais.append({
                **{k: v for k, v in _magia_para_dict(m).items() if k != "texto_original"},
                "texto_completo": m.texto_original,
                "fonte": "delimitador",
                "confianca": 1.0,
            })
    else:
        for nome_indice in indice_nomes:
            nome_key = nome_indice.strip().lower()

            if nome_key in magia_por_nome:
                magia = magia_por_nome[nome_key]
                magias_finais.append({
                    **{k: v for k, v in _magia_para_dict(magia).items() if k != "texto_original"},
                    "texto_completo": magia.texto_original,
                    "fonte": "delimitador",
                    "confianca": 1.0,
                })
                nomes_encontrados.add(nome_key)
                continue

            # Match parcial
            for nome_extraido, magia in magia_por_nome.items():
                if nome_key in nome_extraido or nome_extraido in nome_key:
                    magias_finais.append({
                        **{k: v for k, v in _magia_para_dict(magia).items() if k != "texto_original"},
                        "texto_completo": magia.texto_original,
                        "nome_indice": nome_indice,
                        "fonte": "delimitador_parcial",
                        "confianca": 0.8,
                    })
                    nomes_encontrados.add(nome_key)
                    break
            else:
                magias_finais.append({
                    "nome": nome_indice,
                    "escola": "NÃO ENCONTRADO",
                    "custo": "",
                    "alcance": "",
                    "duracao": "",
                    "descricao": "Magia listada no índice mas não extraída automaticamente.",
                    "pagina": 0,
                    "fonte": "indice_apenas",
                    "confianca": 0.0,
                })

        # Magias extraídas que não estão no índice (extras)
        for nome_extraido, magia in magia_por_nome.items():
            if nome_extraido not in nomes_encontrados:
                magias_finais.append({
                    **{k: v for k, v in _magia_para_dict(magia).items() if k != "texto_original"},
                    "texto_completo": magia.texto_original,
                    "fonte": "extra",
                    "confianca": 0.9,
                })

    # Estatísticas
    print("\n" + "=" * 60)
    print("ESTATÍSTICAS")
    print("=" * 60)
    print(f"Total no índice:        {len(indice_nomes)}")
    print(f"Extraídas completas:    {len([m for m in magias_finais if m.get('fonte') == 'delimitador'])}")
    print(f"Extraídas parciais:     {len([m for m in magias_finais if m.get('fonte') == 'delimitador_parcial'])}")
    print(f"Extras (não no índice): {len([m for m in magias_finais if m.get('fonte') == 'extra'])}")
    print(f"Faltantes:              {len([m for m in magias_finais if m.get('fonte') == 'indice_apenas'])}")

    # Salvar resultados
    output_dir = Path("data/processed/magias")
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "magias_3dt_completo.json", "w", encoding="utf-8") as f:
        json.dump(magias_finais, f, ensure_ascii=False, indent=2)

    with open(output_dir / "magias_3dt_revisao.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["nome", "escola", "custo", "pagina", "confianca", "fonte"],
            extrasaction="ignore",
        )
        writer.writeheader()
        for m in magias_finais:
            writer.writerow({
                "nome": m.get("nome", ""),
                "escola": m.get("escola", ""),
                "custo": m.get("custo", ""),
                "pagina": m.get("pagina", 0),
                "confianca": m.get("confianca", 0),
                "fonte": m.get("fonte", ""),
            })

    print(f"\n[OK] Resultados salvos em {output_dir}/")
    print("   - magias_3dt_completo.json (dados completos)")
    print("   - magias_3dt_revisao.csv (para revisão manual)")

    return magias_finais


if __name__ == "__main__":
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else None
    pipeline_completo(pdf_path)
