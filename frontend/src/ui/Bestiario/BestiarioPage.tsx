import { useParams, useNavigate } from "react-router-dom";
import { useMemo, useEffect, useState } from "react";
import { getMonstros } from "@/data/monstros";
import { useBestiarioStore } from "@/store/bestiarioStore";
import {
  filtrarMonstros,
  ordenarMonstros,
  monstroPorSlug,
} from "@/core/bestiario";
import { slugParaLivro, livroParaSlug, normalizarLivro } from "@/core/livroNormalizado";
import { ListaLivros } from "./ListaLivros";
import { ListaMonstros } from "./ListaMonstros";
import { FiltrosOrdenacao } from "./FiltrosOrdenacao";
import { FichaMonstro } from "./FichaMonstro";

export function BestiarioPage() {
  const { livroSlug, monstroSlug } = useParams<{
    livroSlug?: string;
    monstroSlug?: string;
  }>();
  const navigate = useNavigate();
  const monstros = getMonstros();
  const livros = useMemo(
    () => [...new Set(monstros.map((m) => m.livro).filter(Boolean))] as string[],
    [monstros]
  );

  const {
    livroSelecionado,
    filtroTipo,
    ordem,
    setLivroSelecionado,
    setFiltroTipo,
    setOrdem,
  } = useBestiarioStore();
  const [searchTerm, setSearchTerm] = useState("");

  // Se estamos em /bestiario/livro/:slug, resolver livro ("todos" = todos os monstros)
  const livroResolvido = useMemo(() => {
    if (livroSlug === "todos") return null;
    if (livroSlug && livros.length) {
      const encontrado = slugParaLivro(livroSlug, livros);
      if (encontrado) return encontrado;
    }
    return livroSelecionado;
  }, [livroSlug, livros, livroSelecionado]);

  // Monstro específico (rota /bestiario/.../monstro/:slug)
  const monstro = useMemo(() => {
    if (!monstroSlug) return null;
    return monstroPorSlug(monstros, monstroSlug, livroResolvido ?? undefined);
  }, [monstros, monstroSlug, livroResolvido]);

  // Lista filtrada e ordenada (para ListaMonstros)
  const monstrosFiltrados = useMemo(() => {
    const filtrados = filtrarMonstros(monstros, {
      livro: livroResolvido ?? undefined,
      tipo: filtroTipo ?? undefined,
      search: searchTerm || undefined,
    });
    return ordenarMonstros(filtrados, ordem);
  }, [monstros, livroResolvido, filtroTipo, ordem, searchTerm]);

  // Sincronizar store com URL ao montar
  useEffect(() => {
    if (livroSlug && livros.length) {
      const l = slugParaLivro(livroSlug, livros);
      if (l) setLivroSelecionado(l);
    }
  }, [livroSlug, livros, setLivroSelecionado]);

  // Página: lista de livros (apenas em /bestiario sem segmentos)
  if (!livroSlug && !monstroSlug) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-stone-800">Bestiário</h1>
        <p className="text-stone-600">
          Escolha um livro para ver os monstros.
        </p>
        <ListaLivros monstros={monstros} />
      </div>
    );
  }

  // Página: ficha do monstro
  if (monstro) {
    return (
      <FichaMonstro
        monstro={monstro}
        livroSlug={livroSlug ?? null}
      />
    );
  }

  // Página: lista de monstros (com ou sem filtro por livro)
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-stone-800">Bestiário</h1>
      <FiltrosOrdenacao
        monstros={monstros}
        livroSelecionado={livroResolvido}
        filtroTipo={filtroTipo}
        ordem={ordem}
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        onLivroChange={(livro) => {
          setLivroSelecionado(livro);
          if (livro) {
            const slug = livroParaSlug(normalizarLivro(livro) || livro);
            navigate(`/bestiario/livro/${slug}`, { replace: true });
          } else {
            navigate("/bestiario/livro/todos", { replace: true });
          }
        }}
        onTipoChange={setFiltroTipo}
        onOrdemChange={setOrdem}
      />
      <ListaMonstros monstros={monstrosFiltrados} livroSlug={livroSlug ?? null} />
    </div>
  );
}
