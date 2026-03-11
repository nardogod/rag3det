/**
 * Lógica do bestiário: filtros, ordenação e formatação de ficha.
 * Espelho de src/utils/formatar_monstro.py
 */

import type { Monstro, LinhaFicha, AtaqueEspecifico } from "@/types/monstro";
import { normalizarLivro } from "./livroNormalizado";
import { sanitizarTextoExibicao } from "./sanitizarTexto";

const VAZIO = "—";

export type OrdemBestiario = "alfabetica" | "livro" | "tipo";

function _valor(v: unknown): string {
  if (v == null) return VAZIO;
  if (Array.isArray(v) && v.length === 0) return VAZIO;
  if (typeof v === "object" && Object.keys(v as object).length === 0) return VAZIO;
  if (typeof v === "string" && !v.trim()) return VAZIO;
  return String(v).trim();
}

function _resumirAtaques(ataques: AtaqueEspecifico[] | null | undefined): string {
  if (!ataques?.length) return VAZIO;
  const partes = ataques.map((a) => {
    let p = a.nome || "";
    if (a.fa_fd) p += ` (${a.fa_fd})`;
    if (a.dano) p += ` dano ${a.dano}`;
    return p;
  });
  return partes.filter(Boolean).join("; ") || VAZIO;
}

function _juntarHabilidades(monstro: Monstro): string {
  const hab = monstro.habilidades || [];
  const extra = monstro.habilidades_extra;
  const partes = Array.isArray(hab) ? [...hab] : [String(hab)];
  if (extra) partes.push(String(extra));
  return partes.filter(Boolean).join("; ") || VAZIO;
}

/**
 * Converte escala (1N, 8N, 61S, 84K) em descrição legível.
 * N=Ningen (humano), S=Sugoi (superior), K=Kiodai (gigante).
 */
export function formatarEscalaParaExibicao(escala: string | null | undefined): string {
  const raw = (escala || "").trim();
  if (!raw) return VAZIO;
  const m = raw.match(/^(\d+)([NSK])?$/i);
  if (!m) return raw;
  const num = m[1];
  const suf = (m[2] || "N").toUpperCase();
  const desc: Record<string, string> = {
    N: "Tamanho humano (1–2 m)",
    S: "Tamanho superior (alguns metros)",
    K: "Tamanho gigante (dezenas de metros)",
  };
  return `${desc[suf] || desc.N}, nível ${num}`;
}

/**
 * Agrupa monstros por livro (chave = livro original).
 */
export function agruparPorLivro(monstros: Monstro[]): Record<string, Monstro[]> {
  const grupos: Record<string, Monstro[]> = {};
  for (const m of monstros) {
    const livro = m.livro || "sem-livro";
    if (!grupos[livro]) grupos[livro] = [];
    grupos[livro].push(m);
  }
  return grupos;
}

/**
 * Retorna lista única de livros presentes nos monstros.
 */
export function obterLivros(monstros: Monstro[]): string[] {
  const set = new Set<string>();
  for (const m of monstros) {
    if (m.livro) set.add(m.livro);
  }
  return Array.from(set);
}

/**
 * Filtra monstros por livro, tipo e/ou termo de pesquisa (nome).
 */
export function filtrarMonstros(
  monstros: Monstro[],
  filtros: { livro?: string | null; tipo?: string | null; search?: string | null }
): Monstro[] {
  let result = monstros;
  if (filtros.livro) {
    result = result.filter((m) => m.livro === filtros.livro);
  }
  if (filtros.tipo) {
    result = result.filter((m) => (m.tipo || "").toLowerCase() === filtros.tipo!.toLowerCase());
  }
  if (filtros.search?.trim()) {
    const raw = filtros.search.trim().toLowerCase();
    const term = raw.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    const termAlt = raw === "dragon" ? "dragao" : null;
    const words = (termAlt ?? term).split(/\s+/).filter(Boolean);
    const wordVariants = (w: string): string[] => {
      const base = [w, w + "s", w + "es"];
      if (w === "dragao") base.push("dragoes");
      if (w === "dragoes") base.push("dragao");
      return base;
    };
    result = result.filter((m) => {
      const nome = (m.nome || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
      const desc = (m.descricao || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
      const text = `${nome} ${desc}`;
      const matchesFull = text.includes(term) || (termAlt !== null && text.includes(termAlt));
      const matchesWords =
        words.length > 0 &&
        words.every((w) => wordVariants(w).some((v) => text.includes(v)));
      return matchesFull || matchesWords;
    });
  }
  return result;
}

/**
 * Ordena monstros conforme critério.
 */
export function ordenarMonstros(
  monstros: Monstro[],
  ordem: OrdemBestiario
): Monstro[] {
  const copy = [...monstros];
  switch (ordem) {
    case "alfabetica":
      return copy.sort((a, b) =>
        (a.nome || "").localeCompare(b.nome || "", "pt-BR")
      );
    case "livro":
      return copy.sort((a, b) => {
        const livroA = normalizarLivro(a.livro) || a.livro || "";
        const livroB = normalizarLivro(b.livro) || b.livro || "";
        if (livroA !== livroB) return livroA.localeCompare(livroB, "pt-BR");
        return (a.nome || "").localeCompare(b.nome || "", "pt-BR");
      });
    case "tipo":
      return copy.sort((a, b) => {
        const tipoA = a.tipo || "outro";
        const tipoB = b.tipo || "outro";
        if (tipoA !== tipoB) return tipoA.localeCompare(tipoB, "pt-BR");
        return (a.nome || "").localeCompare(b.nome || "", "pt-BR");
      });
    default:
      return copy;
  }
}

/**
 * Formata monstro como array de linhas para a ficha (ordem FORMATO_FICHA_MONSTRO).
 */
export function formatarFichaMonstro(monstro: Monstro): LinhaFicha[] {
  const c = monstro.caracteristicas || {};
  const carac = c
    ? `F${c.F ?? ""}, H${c.H ?? ""}, R${c.R ?? ""}, A${c.A ?? ""}, PdF${c.PdF ?? ""}`
    : VAZIO;

  const fraquezasVal =
    Array.isArray(monstro.fraquezas) && monstro.fraquezas.length
      ? monstro.fraquezas.join(", ")
      : _valor(monstro.fraquezas || monstro.fraqueza);

  const linhas: [string, string][] = [
    ["Nome", _valor(monstro.nome)],
    ["Características", carac],
    ["PV / PM", `${_valor(monstro.pv)} / ${_valor(monstro.pm)}`],
    ["Escala", formatarEscalaParaExibicao(monstro.escala) || _valor(monstro.escala)],
    ["Comportamento", _valor(monstro.comportamento)],
    ["Tamanho", _valor(monstro.altura_tamanho)],
    ["Peso", _valor(monstro.peso)],
    ["Habitat", _valor(monstro.habitat)],
    ["Comportamento dia/noite", _valor(monstro.comportamento_dia_noite)],
    ["Combate", _valor(monstro.comportamento_combate)],
    ["Ataques", _resumirAtaques(monstro.ataques_especificos)],
    ["Imunidades", (monstro.imunidades || []).join(", ") || VAZIO],
    ["Fraquezas", fraquezasVal],
    ["Habilidades", _juntarHabilidades(monstro)],
    ["Movimento", _valor(monstro.movimento)],
    ["Origem criação", _valor(monstro.origem_criacao)],
    ["Uso cultural", _valor(monstro.uso_cultural)],
    ["Vínculo montaria", _valor(monstro.vinculo_montaria)],
    ["Veneno", _valor(monstro.veneno_detalhado)],
    ["Resistência controle", _valor(monstro.resistencia_controle)],
    ["Necessidades", _valor(monstro.necessidades)],
    ["Recuperação", _valor(monstro.recuperacao_pv)],
    ["Táticas", _valor(monstro.taticas)],
    ["Loot", _valor(monstro.tesouro)],
    [
      "Fonte",
      _valor(monstro.fonte_referencia) || _valor(monstro.livro),
    ],
  ];

  return linhas
    .map(([campo, valor]) => {
      const v = (valor || VAZIO).replace(/\n/g, " ").trim();
      return { campo, valor: sanitizarTextoExibicao(v) };
    })
    .filter(({ valor }) => valor !== VAZIO && valor.trim().length > 0);
}

/**
 * Gera slug para URL a partir do nome do monstro.
 */
export function nomeParaSlug(nome: string): string {
  return nome
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

/**
 * Busca monstro por slug (compara com nome normalizado).
 * Se livro for informado, prioriza monstros desse livro.
 * Prioriza correspondência exata do slug para evitar que "afogado" retorne "Capitão Afogado".
 */
export function monstroPorSlug(
  monstros: Monstro[],
  slug: string,
  livro?: string | null
): Monstro | null {
  const slugNorm = slug.toLowerCase();
  const exactMatch = (m: Monstro) => nomeParaSlug(m.nome) === slugNorm;
  const partialMatch = (m: Monstro) =>
    nomeParaSlug(m.nome) !== slugNorm &&
    m.nome.toLowerCase().replace(/\s+/g, "-").includes(slugNorm);

  if (livro) {
    const doLivroExact = monstros.find((m) => exactMatch(m) && m.livro === livro);
    if (doLivroExact) return doLivroExact;
    const doLivroPartial = monstros.find((m) => partialMatch(m) && m.livro === livro);
    if (doLivroPartial) return doLivroPartial;
  }
  const exact = monstros.find(exactMatch);
  if (exact) return exact;
  return monstros.find(partialMatch) ?? null;
}
