import type { ReactNode } from "react";
import type { MensagemMestre } from "@/core/combat/types";

interface LogNarrativoProps {
  mensagens: MensagemMestre[];
}

function formatarTextoComDados(texto: string): ReactNode[] {
  const partes: ReactNode[] = [];
  const regex = /1d6=(\d)/g;
  let ultimoIndice = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(texto)) !== null) {
    const indice = match.index;
    if (indice > ultimoIndice) {
      partes.push(
        <span key={`t-${indice}`}>{texto.slice(ultimoIndice, indice)}</span>
      );
    }
    const valorStr = match[1];
    const valor = parseInt(valorStr, 10);
    let classe = "text-stone-800";
    if (valor === 6) {
      classe = "text-green-600 font-semibold";
    } else if (valor === 1) {
      classe = "text-red-600 font-semibold";
    }
    partes.push(
      <span key={`d-${indice}`} className={classe}>
        {`1d6=${valorStr}`}
      </span>
    );
    ultimoIndice = indice + match[0].length;
  }
  if (ultimoIndice < texto.length) {
    partes.push(
      <span key={`t-final`}>{texto.slice(ultimoIndice)}</span>
    );
  }
  return partes;
}

export function LogNarrativo({ mensagens }: LogNarrativoProps) {
  return (
    <div className="mt-4 max-h-64 w-full overflow-y-auto rounded-lg border border-stone-300 bg-stone-50 p-3 text-sm text-stone-800">
      {mensagens.length === 0 ? (
        <p className="text-xs text-stone-500">
          O mestre ainda não descreveu nenhum lance. Inicie a batalha para ver a narração.
        </p>
      ) : (
        <ul className="space-y-2">
          {mensagens.map((m) => (
            <li key={m.id} className="leading-snug">
              <span className="mr-1 text-[10px] font-semibold uppercase text-amber-700">
                Mestre:
              </span>
              <span>{formatarTextoComDados(m.texto)}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

