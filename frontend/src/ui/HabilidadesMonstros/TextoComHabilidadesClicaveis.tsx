/**
 * Renderiza texto com nomes de habilidades clicáveis.
 * Ao clicar em uma habilidade, exibe um card com a descrição completa.
 */

import { useCallback, useMemo, useState } from "react";
import type { HabilidadeMonstro } from "@/data/habilidadesMonstros";
import { getHabilidadesMonstros } from "@/data/habilidadesMonstros";
import { sanitizarTextoExibicao } from "@/core/sanitizarTexto";

interface TextoComHabilidadesClicaveisProps {
  texto: string;
  habilidades?: HabilidadeMonstro[];
  className?: string;
}

/**
 * Divide o texto em partes: texto normal e spans clicáveis para cada habilidade.
 * Em cada posição, prioriza o match mais longo (ex.: "Aparência Inofensiva" antes de "Aparência").
 */
function parsearTextoComHabilidades(
  texto: string,
  habilidades: HabilidadeMonstro[]
): Array<{ tipo: "texto" | "habilidade"; conteudo: string; habilidade?: HabilidadeMonstro }> {
  if (!texto?.trim() || habilidades.length === 0) {
    return [{ tipo: "texto", conteudo: texto || "" }];
  }

  const partes: Array<{ tipo: "texto" | "habilidade"; conteudo: string; habilidade?: HabilidadeMonstro }> = [];
  let i = 0;

  while (i < texto.length) {
    let melhor: { length: number; hab: HabilidadeMonstro } | null = null;

    for (const h of habilidades) {
      if (h.nome.length < 2) continue;
      const sub = texto.slice(i, i + h.nome.length);
      if (sub.length === h.nome.length && sub.toLowerCase() === h.nome.toLowerCase()) {
        if (melhor === null || h.nome.length > melhor.length) {
          melhor = { length: h.nome.length, hab: h };
        }
      }
    }

    if (melhor === null) {
      let j = i + 1;
      while (j < texto.length) {
        let found = false;
        for (const h of habilidades) {
          if (h.nome.length < 2) continue;
          const sub = texto.slice(j, j + h.nome.length);
          if (sub.length === h.nome.length && sub.toLowerCase() === h.nome.toLowerCase()) {
            found = true;
            break;
          }
        }
        if (found) break;
        j++;
      }
      partes.push({ tipo: "texto", conteudo: texto.slice(i, j) });
      i = j;
    } else {
      const match = texto.slice(i, i + melhor.length);
      partes.push({
        tipo: "habilidade",
        conteudo: match,
        habilidade: melhor.hab,
      });
      i += melhor.length;
    }
  }

  return partes;
}

export function TextoComHabilidadesClicaveis({
  texto,
  habilidades: habilidadesProp,
  className = "",
}: TextoComHabilidadesClicaveisProps) {
  const [cardAberta, setCardAberta] = useState<HabilidadeMonstro | null>(null);

  const habilidades = habilidadesProp ?? getHabilidadesMonstros();

  const partes = useMemo(() => {
    const sanitizado = sanitizarTextoExibicao(texto);
    return parsearTextoComHabilidades(sanitizado, habilidades);
  }, [texto, habilidades]);

  const abrirCard = useCallback((hab: HabilidadeMonstro) => {
    setCardAberta(hab);
  }, []);

  const fecharCard = useCallback(() => {
    setCardAberta(null);
  }, []);

  return (
    <span className={className}>
      {partes.map((p, i) => {
        if (p.tipo === "texto") {
          return <span key={i}>{p.conteudo}</span>;
        }
        if (p.tipo === "habilidade" && p.habilidade) {
          return (
            <button
              key={i}
              type="button"
              onClick={() => abrirCard(p.habilidade!)}
              className="cursor-pointer text-amber-600 underline decoration-amber-400 hover:text-amber-700 hover:decoration-amber-500"
            >
              {p.conteudo}
            </button>
          );
        }
        return <span key={i}>{p.conteudo}</span>;
      })}

      {cardAberta && (
        <CardHabilidade
          habilidade={cardAberta}
          onFechar={fecharCard}
        />
      )}
    </span>
  );
}

interface CardHabilidadeProps {
  habilidade: HabilidadeMonstro;
  onFechar: () => void;
}

function CardHabilidade({ habilidade, onFechar }: CardHabilidadeProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={onFechar}
      role="dialog"
      aria-modal="true"
      aria-labelledby="card-habilidade-titulo"
    >
      <div
        className="max-h-[85vh] w-full max-w-lg overflow-hidden rounded-lg border border-stone-300 bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-stone-200 bg-stone-50 px-4 py-2">
          <h3 id="card-habilidade-titulo" className="font-semibold text-stone-800">
            {habilidade.nome}
          </h3>
          <button
            type="button"
            onClick={onFechar}
            className="rounded p-1 text-stone-500 hover:bg-stone-200 hover:text-stone-700"
            aria-label="Fechar"
          >
            ✕
          </button>
        </div>
        <div className="max-h-[60vh] overflow-y-auto p-4 space-y-3">
          {habilidade.fonte && (
            <p className="text-xs text-stone-500">Fonte: {habilidade.fonte}</p>
          )}
          <div>
            <h4 className="text-sm font-medium text-stone-700">O que faz</h4>
            <p className="mt-1 whitespace-pre-wrap text-sm text-stone-600">
              {habilidade.descricao}
            </p>
          </div>
          {habilidade.monstros.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-stone-700">
                Monstros ({habilidade.monstros.length})
              </h4>
              <ul className="mt-1 max-h-32 overflow-y-auto space-y-0.5 text-sm text-stone-600">
                {habilidade.monstros.slice(0, 10).map((m) => (
                  <li key={m}>• {m}</li>
                ))}
                {habilidade.monstros.length > 10 && (
                  <li className="text-stone-500">
                    … e mais {habilidade.monstros.length - 10}
                  </li>
                )}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
