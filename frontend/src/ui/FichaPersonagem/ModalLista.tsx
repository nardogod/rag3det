/**
 * Modal para seleção de itens (vantagens, desvantagens, magias, raças)
 * com descrição ao clicar.
 */

import { useState } from "react";

export interface ItemLista {
  nome: string;
  bonus?: string;
  custo?: string;
  efeito?: string;
  descricao?: string;
  escola?: string;
  livro?: string;
  pagina?: number;
  /** true = Única (apenas uma por personagem). */
  unica?: boolean;
}

interface ModalListaProps {
  titulo: string;
  itens: ItemLista[];
  selecionados: string[];
  onSelecionar: (nome: string) => void;
  onRemover: (nome: string) => void;
  onFechar: () => void;
  multiSelect?: boolean;
  parseCusto?: (custo: string) => number;
  pontosDisponiveis?: number;
  /** Nomes que podem ser adicionados (regras 3D&T). Se omitido, todos podem. */
  nomesDisponiveis?: Set<string>;
}

export function ModalLista({
  titulo,
  itens,
  selecionados,
  onSelecionar,
  onRemover,
  onFechar,
  multiSelect = true,
  parseCusto,
  pontosDisponiveis = 999,
  nomesDisponiveis,
}: ModalListaProps) {
  const [busca, setBusca] = useState("");
  const [itemExpandido, setItemExpandido] = useState<string | null>(null);

  const filtrados = itens.filter((i) =>
    i.nome.toLowerCase().includes(busca.toLowerCase())
  );

  const custoItem = (item: ItemLista) => {
    if (!parseCusto || !item.custo) return 0;
    return parseCusto(item.custo);
  };

  const jaSelecionado = (nome: string) => selecionados.includes(nome);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={(e) => e.target === e.currentTarget && onFechar()}
    >
      <div
        className="max-h-[90vh] w-full max-w-lg overflow-hidden rounded-xl bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-stone-200 px-4 py-3">
          <h2 className="text-lg font-bold text-stone-800">{titulo}</h2>
          <button
            type="button"
            onClick={onFechar}
            className="rounded p-2 text-stone-500 hover:bg-stone-100"
          >
            ✕
          </button>
        </div>
        <div className="p-4">
          <input
            type="text"
            placeholder="Buscar..."
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            className="mb-4 w-full rounded border border-stone-300 px-3 py-2"
          />
          <div className="max-h-[50vh] space-y-2 overflow-y-auto">
            {filtrados.map((item, idx) => {
              const sel = jaSelecionado(item.nome);
              const custo = custoItem(item);
              const disponivelPorRegras =
                !nomesDisponiveis || nomesDisponiveis.has(item.nome);
              const podePontos =
                multiSelect
                  ? sel || pontosDisponiveis >= custo
                  : sel || selecionados.length === 0;
              const pode = podePontos && disponivelPorRegras;
              const itemKey = `${item.nome}|${item.livro || ""}|${idx}`;
              const expandido = itemExpandido === itemKey;
              return (
                <div
                  key={itemKey}
                  className="rounded-lg border border-stone-200"
                >
                  <div
                    className="flex cursor-pointer items-center justify-between px-3 py-2 hover:bg-stone-50"
                    onClick={() => setItemExpandido(expandido ? null : itemKey)}
                  >
                    <span className="font-medium text-stone-800">
                      {item.nome}
                      {item.livro && (
                        <span className="ml-1.5 text-xs font-normal text-stone-500">
                          ({item.livro})
                        </span>
                      )}
                      {item.unica && (
                        <span className="ml-1.5 rounded bg-amber-200 px-1.5 py-0.5 text-[10px] font-normal text-amber-800">
                          Única
                        </span>
                      )}
                    </span>
                    <div className="flex flex-wrap items-center gap-2">
                      {item.bonus && (
                        <span className="rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-medium text-emerald-800">
                          {item.bonus}
                        </span>
                      )}
                      {item.custo && (
                        <span className="text-xs text-stone-500">
                          {item.custo}
                        </span>
                      )}
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (sel) onRemover(item.nome);
                          else if (pode) onSelecionar(item.nome);
                        }}
                        disabled={!pode && !sel}
                        className={`rounded px-2 py-1 text-sm ${
                          sel
                            ? "bg-amber-200 text-amber-800"
                            : pode
                            ? "bg-amber-100 text-amber-700 hover:bg-amber-200"
                            : "bg-stone-100 text-stone-400"
                        }`}
                      >
                        {sel ? "Remover" : "Adicionar"}
                      </button>
                    </div>
                  </div>
                  {expandido && (
                    <div className="max-h-64 overflow-y-auto border-t border-stone-100 bg-stone-50 px-3 py-2 text-sm text-stone-600 whitespace-pre-wrap">
                      {item.efeito || item.descricao || "Sem descrição."}
                      {item.escola && item.escola !== "—" && item.escola !== "NÃO ENCONTRADO" && (
                        <p className="mt-1 text-xs text-stone-500">
                          Escola: {item.escola}
                        </p>
                      )}
                      {(item.livro || item.pagina) && (
                        <p className="mt-1 text-xs text-stone-400">
                          {[item.livro, item.pagina ? `p. ${item.pagina}` : ""]
                            .filter(Boolean)
                            .join(", ")}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
