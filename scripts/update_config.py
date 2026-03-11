"""
Atualiza `config/settings.yaml` para apontar para o modelo de embeddings desejado.

Uso (na raiz do projeto):
  python scripts/update_config.py --model v3
  python scripts/update_config.py --model v2
  python scripts/update_config.py --path models/embeddings/custom_model
"""
from __future__ import annotations

import argparse
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "settings.yaml"


def resolve_model_path(model_flag: str | None, path_flag: str | None) -> str:
    if path_flag:
        return path_flag
    if model_flag == "v3":
        return "models/embeddings/3dt_finetuned_v3"
    if model_flag == "v2":
        return "models/embeddings/3dt_finetuned_v2"
    if model_flag == "v1":
        return "models/embeddings/3dt_finetuned"
    raise SystemExit("[ERRO] Use --model {v1,v2,v3} ou --path PATH_EXPLICITO.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Atualiza embedding_model em config/settings.yaml.")
    parser.add_argument(
        "--model",
        choices=["v1", "v2", "v3"],
        help="Atalho para modelos conhecidos (v1, v2, v3).",
    )
    parser.add_argument(
        "--path",
        type=str,
        help="Path explícito para o modelo (sobrescreve --model se informado).",
    )
    args = parser.parse_args()

    target = resolve_model_path(args.model, args.path)

    if not CONFIG_PATH.exists():
        raise SystemExit(f"[ERRO] Arquivo de config não encontrado: {CONFIG_PATH}")

    data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    emb = data.get("embedding", {}) or {}
    emb["embedding_model"] = target
    data["embedding"] = emb

    CONFIG_PATH.write_text(yaml.dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"[OK] embedding.embedding_model atualizado para: {target}")


if __name__ == "__main__":
    main()

