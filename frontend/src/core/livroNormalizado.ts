/**
 * Mapeamento de nomes de livros para exibição consistente.
 * Port do src/utils/livro_normalizado.py
 */

const MAPEAMENTO_PADRAO: Record<string, string> = {
  "3dt-manual-da-magia-biblioteca-elfica.pdf": "Manual da Magia",
  "3dt-manual-da-magia-biblioteca-elfica": "Manual da Magia",
  "3dt-alpha-manual-da-magia-biblioteca-elfica.pdf": "Manual da Magia Alpha",
  "3dt-alpha-manual-revisado-biblioteca-elfica.pdf": "Manual Revisado (Alpha)",
  "3dt-manual-revisado-ampliado-e-turbinado-biblioteca-elfica.pdf":
    "Manual Revisado Ampliado e Turbinado",
  "3dt-alpha-manual-dos-dragoes-biblioteca-elfica.pdf": "Manual dos Dragões",
  "3dt-alpha-manual-dos-monstros.pdf": "Manual dos Monstros",
  "manual da magia": "Manual da Magia",
  "manual da magia 3dt": "Manual da Magia",
  "manual 3d&t turbinado": "Manual 3D&T Turbinado",
  "manual 3d&t turbinado digital": "Manual 3D&T Turbinado",
  "manual turbinado": "Manual 3D&T Turbinado",
  "manual do aventureiro": "Manual do Aventureiro",
  "manual do aventureiro 3dt": "Manual do Aventureiro",
  "manual alpha": "Manual Alpha",
  "3det alpha magias": "Manual Alpha",
  "manual revisado alpha": "Manual Revisado (Alpha)",
  "manual revisado ampliado e turbinado": "Manual Revisado Ampliado e Turbinado",
  "manual dos monstros": "Manual dos Monstros",
  "bestiario alpha": "Bestiário Alpha",
  "3dt alpha bestiario alpha biblioteca elfica": "Bestiário Alpha",
  "3dt alpha manual dos dragoes biblioteca elfica": "Manual dos Dragões",
  "tormenta daemon guia de monstros de arton biblioteca elfica":
    "Guia de Monstros de Arton",
  "3dt alpha manual da magia biblioteca elfica": "Manual da Magia Alpha",
  "3dt alpha manual biblioteca elfica": "Manual Alpha",
  "3dt alpha manual revisado biblioteca elfica": "Manual Revisado (Alpha)",
  "3dt manual da magia biblioteca elfica": "Manual da Magia",
  "3dt alpha tormenta alpha": "Tormenta Alpha",
  "3d&t manual turbinado digital": "Manual 3D&T Turbinado",
  "manual-dos-monstros-criaturas-fantasticas-revisado":
    "Manual dos Monstros: Criaturas Fantásticas (revisado)",
};

/**
 * Retorna o nome normalizado do livro para exibição.
 */
export function normalizarLivro(livro: string | null | undefined): string {
  if (!livro || typeof livro !== "string") return "";
  const livroClean = livro.trim();
  if (!livroClean) return "";
  if (livroClean in MAPEAMENTO_PADRAO) return MAPEAMENTO_PADRAO[livroClean];
  for (const [k, v] of Object.entries(MAPEAMENTO_PADRAO)) {
    if (k.toLowerCase() === livroClean.toLowerCase()) return v;
  }
  return livroClean;
}

/**
 * Gera slug para URL a partir do nome do livro.
 */
export function livroParaSlug(livro: string): string {
  const norm = normalizarLivro(livro) || livro;
  return norm
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

/**
 * Encontra o livro original pelo slug (busca em todos os livros conhecidos).
 * O slug é gerado a partir do nome normalizado do livro.
 */
export function slugParaLivro(slug: string, livrosDisponiveis: string[]): string | null {
  const slugNorm = slug.toLowerCase().trim();
  for (const livro of livrosDisponiveis) {
    const slugDoLivro = livroParaSlug(normalizarLivro(livro) || livro);
    if (slugDoLivro === slugNorm) return livro;
  }
  return null;
}
