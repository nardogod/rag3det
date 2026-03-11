import { Link } from "react-router-dom";
import { normalizarLivro, livroParaSlug } from "@/core/livroNormalizado";
import type { Monstro } from "@/types/monstro";
import { agruparPorLivro } from "@/core/bestiario";

interface ListaLivrosProps {
  monstros: Monstro[];
}

export function ListaLivros({ monstros }: ListaLivrosProps) {
  const grupos = agruparPorLivro(monstros);
  const livros = Object.keys(grupos).sort((a, b) =>
    normalizarLivro(a).localeCompare(normalizarLivro(b), "pt-BR")
  );

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-stone-800">
        Monstros por livro
      </h2>
      <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
        <Link
          to="/bestiario/livro/todos"
          className="block rounded-lg border border-amber-300 bg-amber-50 p-4 shadow-sm transition hover:border-amber-400 hover:shadow-md"
        >
          <h3 className="font-medium text-stone-800">Todos os monstros</h3>
          <p className="mt-1 text-sm text-stone-500">
            {monstros.length} monstros
          </p>
        </Link>
        {livros.map((livro) => {
          const count = grupos[livro].length;
          const nomeExibicao = normalizarLivro(livro) || livro;
          const slug = livroParaSlug(nomeExibicao);
          return (
            <Link
              key={livro}
              to={`/bestiario/livro/${slug}`}
              className="block rounded-lg border border-stone-300 bg-white p-4 shadow-sm transition hover:border-amber-400 hover:shadow-md"
            >
              <h3 className="font-medium text-stone-800">{nomeExibicao}</h3>
              <p className="mt-1 text-sm text-stone-500">
                {count} {count === 1 ? "monstro" : "monstros"}
              </p>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
