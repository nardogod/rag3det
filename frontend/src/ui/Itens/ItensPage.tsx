/**
 * Página de visualização de todos os itens mágicos (3D&T).
 * Filtros: tipo, livro, busca por nome. Ordenação por nome, tipo ou livro.
 */

import { useMemo, useState } from "react";
import { itensSistema, TIPOS_ITENS } from "@/data/itens";
import { ListaItens } from "./ListaItens";

type OrdemItens = "nome" | "tipo" | "livro";
type NaturezaFiltro = "" | "Item" | "Habilidade";

export function ItensPage() {
  const [busca, setBusca] = useState("");
  const [filtroTipo, setFiltroTipo] = useState<string>("");
  const [filtroLivro, setFiltroLivro] = useState<string>("");
  const [filtroNatureza, setFiltroNatureza] = useState<NaturezaFiltro>("");
  const [ordem, setOrdem] = useState<OrdemItens>("nome");

  const livros = useMemo(
    () =>
      [...new Set(itensSistema.map((i) => i.livro).filter(Boolean))].sort(
        (a, b) => (a || "").localeCompare(b || "", "pt-BR")
      ) as string[],
    []
  );

  const itensFiltrados = useMemo(() => {
    let lista = [...itensSistema];

    if (busca.trim()) {
      const q = busca.trim().toLowerCase();
      lista = lista.filter((i) =>
        (i.nome || "").toLowerCase().includes(q)
      );
    }
    if (filtroTipo) {
      lista = lista.filter((i) => i.tipo === filtroTipo);
    }
    if (filtroLivro) {
      lista = lista.filter((i) => i.livro === filtroLivro);
    }
    if (filtroNatureza) {
      lista = lista.filter((i) => (i.natureza || "Item") === filtroNatureza);
    }

    lista.sort((a, b) => {
      switch (ordem) {
        case "tipo":
          return (a.tipo || "").localeCompare(b.tipo || "", "pt-BR") ||
            (a.nome || "").localeCompare(b.nome || "", "pt-BR");
        case "livro":
          return (a.livro || "").localeCompare(b.livro || "", "pt-BR") ||
            (a.nome || "").localeCompare(b.nome || "", "pt-BR");
        default:
          return (a.nome || "").localeCompare(b.nome || "", "pt-BR");
      }
    });

    return lista;
  }, [busca, filtroTipo, filtroLivro, ordem]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-stone-800">Itens Mágicos</h1>
      <p className="text-stone-600">
        Visualize todos os itens do sistema 3D&T. Filtre por tipo, livro ou busque por nome.
      </p>

      <div className="flex flex-wrap gap-3 rounded-lg border border-stone-300 bg-white p-4">
        <div className="flex flex-1 min-w-[200px] flex-col gap-1">
          <label className="text-sm font-medium text-stone-600">Buscar</label>
          <input
            type="text"
            placeholder="Nome do item..."
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            className="rounded border border-stone-300 px-3 py-2 text-sm"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-stone-600">Tipo</label>
          <select
            value={filtroTipo}
            onChange={(e) => setFiltroTipo(e.target.value)}
            className="rounded border border-stone-300 px-3 py-2 text-sm"
          >
            <option value="">Todos</option>
            {TIPOS_ITENS.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-stone-600">Natureza</label>
          <select
            value={filtroNatureza}
            onChange={(e) => setFiltroNatureza(e.target.value as NaturezaFiltro)}
            className="rounded border border-stone-300 px-3 py-2 text-sm"
          >
            <option value="">Todos</option>
            <option value="Item">Itens físicos</option>
            <option value="Habilidade">Habilidades (arma/armadura)</option>
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-stone-600">Livro</label>
          <select
            value={filtroLivro}
            onChange={(e) => setFiltroLivro(e.target.value)}
            className="rounded border border-stone-300 px-3 py-2 text-sm"
          >
            <option value="">Todos</option>
            {livros.map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-stone-600">Ordenar</label>
          <select
            value={ordem}
            onChange={(e) => setOrdem(e.target.value as OrdemItens)}
            className="rounded border border-stone-300 px-3 py-2 text-sm"
          >
            <option value="nome">Por nome (A–Z)</option>
            <option value="tipo">Por tipo</option>
            <option value="livro">Por livro</option>
          </select>
        </div>
      </div>

      <ListaItens itens={itensFiltrados} />
    </div>
  );
}
