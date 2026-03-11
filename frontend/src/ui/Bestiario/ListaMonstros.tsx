import { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import type { Monstro } from "@/types/monstro";
import { nomeParaSlug } from "@/core/bestiario";
import { BarraVital } from "./BarraVital";
import {
  calcularForcaMonstro,
  labelForca,
  corForca,
} from "@/core/forcaMonstro";

interface ListaMonstrosProps {
  monstros: Monstro[];
  livroSlug?: string | null;
}

type OrdemForca = "crescente" | "decrescente" | null;

export function ListaMonstros({ monstros, livroSlug }: ListaMonstrosProps) {
  const [ordemForca, setOrdemForca] = useState<OrdemForca>(null);
  const basePath = livroSlug
    ? `/bestiario/livro/${livroSlug}`
    : "/bestiario";

  const monstrosExibir = useMemo(() => {
    if (!ordemForca) return monstros;
    return [...monstros].sort((a, b) => {
      const fa = calcularForcaMonstro(a);
      const fb = calcularForcaMonstro(b);
      return ordemForca === "crescente" ? fa - fb : fb - fa;
    });
  }, [monstros, ordemForca]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-xl font-semibold text-stone-800">
          Lista de monstros ({monstros.length})
        </h2>
        <div className="flex items-center gap-1">
          <span className="text-xs text-stone-500">Força:</span>
          <button
            type="button"
            onClick={() =>
              setOrdemForca((o) => (o === "crescente" ? null : "crescente"))
            }
            className={`rounded px-2 py-1 text-xs font-medium transition ${
              ordemForca === "crescente"
                ? "bg-amber-100 text-amber-800"
                : "bg-stone-100 text-stone-600 hover:bg-stone-200"
            }`}
            title="Ordenar por força (mais fraco primeiro)"
          >
            ↑ Crescente
          </button>
          <button
            type="button"
            onClick={() =>
              setOrdemForca((o) => (o === "decrescente" ? null : "decrescente"))
            }
            className={`rounded px-2 py-1 text-xs font-medium transition ${
              ordemForca === "decrescente"
                ? "bg-amber-100 text-amber-800"
                : "bg-stone-100 text-stone-600 hover:bg-stone-200"
            }`}
            title="Ordenar por força (mais forte primeiro)"
          >
            ↓ Decrescente
          </button>
        </div>
      </div>
      <ul className="max-h-[60vh] space-y-1 overflow-y-auto rounded-lg border border-stone-300 bg-white p-2">
        {monstrosExibir.map((m) => {
          const forca = calcularForcaMonstro(m);
          return (
            <li key={m.nome}>
              <Link
                to={`${basePath}/monstro/${nomeParaSlug(m.nome)}`}
                className="flex items-center gap-3 rounded px-3 py-2 text-stone-700 hover:bg-amber-50 hover:text-amber-800"
              >
                <span className="min-w-0 flex-1 truncate font-medium">
                  {m.nome}
                </span>
                <div className="flex flex-shrink-0 items-center gap-2">
                  <BarraVital
                    valor={m.pv ?? "—"}
                    tipo="pv"
                    altura={12}
                    compacto
                  />
                  <BarraVital
                    valor={m.pm ?? "—"}
                    tipo="pm"
                    altura={12}
                    compacto
                  />
                  <span
                    className={`w-8 text-right text-xs font-medium tabular-nums ${corForca(forca)}`}
                    title={labelForca(forca)}
                  >
                    {forca}
                  </span>
                </div>
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
