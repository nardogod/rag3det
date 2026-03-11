import type { OrdemBestiario } from "@/core/bestiario";
import { normalizarLivro } from "@/core/livroNormalizado";
import type { Monstro } from "@/types/monstro";
import { obterLivros } from "@/core/bestiario";

interface FiltrosOrdenacaoProps {
  monstros: Monstro[];
  livroSelecionado: string | null;
  filtroTipo: string | null;
  ordem: OrdemBestiario;
  searchTerm: string;
  onLivroChange: (livro: string | null) => void;
  onTipoChange: (tipo: string | null) => void;
  onOrdemChange: (ordem: OrdemBestiario) => void;
  onSearchChange: (term: string) => void;
}

const TIPOS: string[] = [
  "humanóide",
  "besta",
  "elemental",
  "morto-vivo",
  "construto",
  "espírito",
  "outro",
];

export function FiltrosOrdenacao({
  monstros,
  livroSelecionado,
  filtroTipo,
  ordem,
  searchTerm,
  onLivroChange,
  onTipoChange,
  onOrdemChange,
  onSearchChange,
}: FiltrosOrdenacaoProps) {
  const livros = obterLivros(monstros);

  return (
    <div className="flex flex-wrap gap-3 rounded-lg border border-stone-300 bg-white p-4">
      <div className="flex flex-1 min-w-[200px] flex-col gap-1">
        <label className="text-sm font-medium text-stone-600">Pesquisar</label>
        <input
          type="search"
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Nome do monstro..."
          className="rounded border border-stone-300 px-3 py-2 text-sm placeholder:text-stone-400"
        />
      </div>
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-stone-600">Livro</label>
        <select
          value={livroSelecionado ?? ""}
          onChange={(e) =>
            onLivroChange(e.target.value ? e.target.value : null)
          }
          className="rounded border border-stone-300 px-3 py-2 text-sm"
        >
          <option value="">Todos</option>
          {livros.map((livro) => (
            <option key={livro} value={livro}>
              {normalizarLivro(livro) || livro}
            </option>
          ))}
        </select>
      </div>
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-stone-600">Tipo</label>
        <select
          value={filtroTipo ?? ""}
          onChange={(e) =>
            onTipoChange(e.target.value ? e.target.value : null)
          }
          className="rounded border border-stone-300 px-3 py-2 text-sm"
        >
          <option value="">Todos</option>
          {TIPOS.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-stone-600">Ordenar</label>
        <select
          value={ordem}
          onChange={(e) =>
            onOrdemChange(e.target.value as OrdemBestiario)
          }
          className="rounded border border-stone-300 px-3 py-2 text-sm"
        >
          <option value="alfabetica">Alfabética (A–Z)</option>
          <option value="livro">Por livro</option>
          <option value="tipo">Por tipo</option>
        </select>
      </div>
    </div>
  );
}
