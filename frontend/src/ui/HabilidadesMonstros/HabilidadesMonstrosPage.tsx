/**
 * Página de Habilidades de Monstros.
 * Lista todas as habilidades dos 284 monstros do Manual (revisado).
 * Ao clicar: exibe todos os dados do JSON (descrição, fonte, variantes, monstros).
 * Filtros: busca, fonte, ordenação.
 */

import { useMemo, useState } from "react";
import { getHabilidadesMonstros } from "@/data/habilidadesMonstros";
import { TextoComHabilidadesClicaveis } from "./TextoComHabilidadesClicaveis";

type OrdemHabilidade = "nome" | "monstros" | "fonte";

export function HabilidadesMonstrosPage() {
  const [busca, setBusca] = useState("");
  const [filtroFonte, setFiltroFonte] = useState<string>("");
  const [ordem, setOrdem] = useState<OrdemHabilidade>("nome");
  const [selecionada, setSelecionada] = useState<string | null>(null);

  const habilidades = getHabilidadesMonstros();

  const fontes = useMemo(
    () =>
      [...new Set(habilidades.map((h) => h.fonte).filter(Boolean))].sort(
        (a, b) => (a || "").localeCompare(b || "", "pt-BR")
      ) as string[],
    [habilidades]
  );

  const habilidadeSelecionada = useMemo(() => {
    if (!selecionada) return null;
    return habilidades.find((h) => h.nome === selecionada);
  }, [habilidades, selecionada]);

  const filtradas = useMemo(() => {
    let lista = [...habilidades];

    if (busca.trim()) {
      const q = busca.trim().toLowerCase();
      lista = lista.filter(
        (h) =>
          h.nome.toLowerCase().includes(q) ||
          h.monstros.some((m) => m.toLowerCase().includes(q))
      );
    }
    if (filtroFonte) {
      lista = lista.filter((h) => h.fonte === filtroFonte);
    }

    lista.sort((a, b) => {
      switch (ordem) {
        case "monstros":
          return (b.monstros?.length ?? 0) - (a.monstros?.length ?? 0) ||
            (a.nome || "").localeCompare(b.nome || "", "pt-BR");
        case "fonte":
          return (a.fonte || "").localeCompare(b.fonte || "", "pt-BR") ||
            (a.nome || "").localeCompare(b.nome || "", "pt-BR");
        default:
          return (a.nome || "").localeCompare(b.nome || "", "pt-BR");
      }
    });

    return lista;
  }, [habilidades, busca, filtroFonte, ordem]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-stone-800">
        Habilidades de Monstros
      </h1>
      <p className="text-stone-600">
        Habilidades e técnicas dos 284 monstros do Manual dos Monstros:
        Criaturas Fantásticas (revisado). Clique em uma habilidade para ler o
        que ela faz.
      </p>

      <div className="flex flex-wrap gap-3 rounded-lg border border-stone-300 bg-white p-4">
        <div className="flex flex-1 min-w-[200px] flex-col gap-1">
          <label className="text-sm font-medium text-stone-600">Buscar</label>
          <input
            type="text"
            placeholder="Nome da habilidade ou monstro..."
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            className="rounded border border-stone-300 px-3 py-2 text-sm"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-stone-600">Fonte</label>
          <select
            value={filtroFonte}
            onChange={(e) => setFiltroFonte(e.target.value)}
            className="rounded border border-stone-300 px-3 py-2 text-sm min-w-[180px]"
          >
            <option value="">Todas</option>
            {fontes.map((f) => (
              <option key={f} value={f}>
                {f}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-stone-600">Ordenar</label>
          <select
            value={ordem}
            onChange={(e) => setOrdem(e.target.value as OrdemHabilidade)}
            className="rounded border border-stone-300 px-3 py-2 text-sm"
          >
            <option value="nome">Por nome (A–Z)</option>
            <option value="monstros">Por mais monstros</option>
            <option value="fonte">Por fonte</option>
          </select>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border border-stone-300 bg-white p-2">
          <h2 className="mb-2 text-lg font-semibold text-stone-800">
            Lista ({filtradas.length})
          </h2>
          <ul className="max-h-[60vh] space-y-1 overflow-y-auto">
            {filtradas.map((h) => {
              const ativa = selecionada === h.nome;
              return (
                <li
                  key={h.nome}
                  className={`cursor-pointer rounded px-2 py-1.5 text-sm transition hover:bg-stone-100 ${
                    ativa
                      ? "bg-amber-100 font-medium text-amber-900"
                      : "text-stone-700"
                  }`}
                  onClick={() => setSelecionada(ativa ? null : h.nome)}
                >
                  {h.nome}
                  {h.monstros.length > 0 && (
                    <span className="ml-1.5 text-xs text-stone-500">
                      ({h.monstros.length} monstros)
                    </span>
                  )}
                </li>
              );
            })}
          </ul>
        </div>

        <div className="rounded-lg border border-stone-300 bg-white p-4">
          <h2 className="mb-2 text-lg font-semibold text-stone-800">
            Detalhes
          </h2>
          {habilidadeSelecionada ? (
            <div className="space-y-4 max-h-[70vh] overflow-y-auto">
              <div>
                <h3 className="text-lg font-medium text-stone-800">
                  {habilidadeSelecionada.nome}
                </h3>
                <span className="text-xs text-stone-500">
                  Fonte: {habilidadeSelecionada.fonte}
                </span>
              </div>

              <div>
                <h4 className="text-sm font-medium text-stone-700">
                  O que faz
                </h4>
                <p className="mt-1 whitespace-pre-wrap text-sm text-stone-600">
                  <TextoComHabilidadesClicaveis texto={habilidadeSelecionada.descricao} />
                </p>
              </div>

              {habilidadeSelecionada.variantes.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-stone-700">
                    Variantes
                  </h4>
                  <ul className="mt-1 space-y-1 text-sm text-stone-600">
                    {habilidadeSelecionada.variantes.map((v) => (
                      <li key={v}>• {v}</li>
                    ))}
                  </ul>
                </div>
              )}

              {habilidadeSelecionada.monstros.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-stone-700">
                    Monstros com esta habilidade ({habilidadeSelecionada.monstros.length})
                  </h4>
                  <ul className="mt-1 max-h-48 overflow-y-auto space-y-0.5 text-sm text-stone-600">
                    {habilidadeSelecionada.monstros.map((m) => (
                      <li key={m}>• {m}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-stone-500">
              Clique em uma habilidade para ler o que ela faz.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
