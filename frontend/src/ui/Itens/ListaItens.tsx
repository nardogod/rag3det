import { useState } from "react";
import type { ItemSistema } from "@/data/itens";

interface ListaItensProps {
  itens: ItemSistema[];
}

export function ListaItens({ itens }: ListaItensProps) {
  const [expandido, setExpandido] = useState<string | null>(null);

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-stone-800">
        Lista de itens ({itens.length})
      </h2>
      <ul className="max-h-[65vh] space-y-1 overflow-y-auto rounded-lg border border-stone-300 bg-white p-2">
        {itens.map((item, idx) => {
          const key = `${item.nome}|${item.livro || ""}|${idx}`;
          const isExpandido = expandido === key;
          return (
            <li key={key} className="rounded-lg border border-stone-200">
              <div
                className="flex cursor-pointer items-center justify-between gap-2 px-3 py-2 hover:bg-stone-50"
                onClick={() => setExpandido(isExpandido ? null : key)}
              >
                <div className="min-w-0 flex-1">
                  <span className="font-medium text-stone-800">
                    {item.nome}
                  </span>
                  {item.livro && (
                    <span className="ml-1.5 text-xs text-stone-500">
                      ({item.livro})
                    </span>
                  )}
                </div>
                <div className="flex shrink-0 flex-wrap items-center gap-2">
                  {item.natureza === "Habilidade" && (
                    <span className="rounded bg-amber-100 px-1.5 py-0.5 text-xs font-medium text-amber-800" title="Habilidade de arma ou armadura">
                      Habilidade
                    </span>
                  )}
                  {item.tipo && (
                    <span className="rounded bg-stone-200 px-1.5 py-0.5 text-xs text-stone-600">
                      {item.tipo}
                    </span>
                  )}
                  {item.bonus && (
                    <span className="rounded bg-emerald-100 px-1.5 py-0.5 text-xs font-medium text-emerald-800">
                      {item.bonus}
                    </span>
                  )}
                  {item.custo && (
                    <span className="text-xs text-stone-500">{item.custo}</span>
                  )}
                  <span className="text-stone-400">
                    {isExpandido ? "▼" : "▶"}
                  </span>
                </div>
              </div>
              {isExpandido && (
                <div className="border-t border-stone-100 bg-stone-50 px-3 py-2 text-sm text-stone-600 whitespace-pre-wrap">
                  {item.efeito || "Sem descrição."}
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
