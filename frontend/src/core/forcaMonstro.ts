/**
 * Cálculo de força/poder do monstro para 3D&T.
 * Combina características, PV/PM, habilidades, imunidades, vulnerabilidades e escala.
 *
 * Técnicas utilizadas:
 * 1. Fórmula ponderada (CR-like): soma de componentes normalizados
 * 2. Peso por categoria: stats > recursos > habilidades > defesas
 * 3. Habilidades core: as 14 mais comuns têm peso maior (impacto no combate)
 */

import type { Monstro } from "@/types/monstro";

/** Habilidades que aumentam significativamente o poder (peso 2) */
const HABILIDADES_FORTES = new Set([
  "aceleração",
  "resistência à magia",
  "voo",
  "invisibilidade",
  "paralisia",
  "magia elemental",
  "ataque múltiplo",
  "fúria",
  "membros elásticos",
  "regeneração",
  "imortal",
  "invulnerabilidade",
  "veneno",
  "armadura extra",
  "deflexão",
  "ataque especial",
  "resistência à magia",
]);

/** Habilidades que reduzem poder (desvantagens) */
const HABILIDADES_FRACAS = new Set([
  "inculto",
  "modelo especial",
  "vulnerabilidade",
  "fobia",
  "dependente",
]);

/**
 * Extrai valor numérico de característica (ex: "3-4" -> 3.5, "5" -> 5)
 */
function parseCarac(val: string | undefined): number {
  if (!val || !val.trim()) return 0;
  const v = val.trim();
  const range = v.match(/^(\d+)\s*[-–]\s*(\d+)$/);
  if (range) {
    return (parseInt(range[1], 10) + parseInt(range[2], 10)) / 2;
  }
  const num = parseInt(v, 10);
  return isNaN(num) ? 0 : num;
}

/**
 * Extrai valor médio de PV/PM (ex: "1d+6" -> 10, "variável" -> 10)
 */
function parseRecurso(val: string | undefined): number {
  if (!val || !val.trim()) return 0;
  const v = val.trim().toLowerCase();
  if (v === "variável" || v === "variavel") return 15;
  const num = parseInt(v, 10);
  if (!isNaN(num)) return num;
  const dice = v.match(/^(\d+)d\+?(\d+)?/);
  if (dice) {
    const dados = parseInt(dice[1], 10);
    const bonus = parseInt(dice[2] || "0", 10);
    return Math.round(dados * 3.5 + bonus);
  }
  return 5;
}

/**
 * Peso da escala (N=1, S=2, K=3)
 */
function pesoEscala(escala: string | null | undefined): number {
  if (!escala?.trim()) return 1;
  const s = escala.toUpperCase();
  if (s.includes("S") || s.includes("SUGOI")) return 2;
  if (s.includes("K") || s.includes("KIODAI")) return 3;
  return 1;
}

/**
 * Calcula força do monstro (0–100).
 * Quanto maior, mais perigoso.
 */
export function calcularForcaMonstro(monstro: Monstro): number {
  const c = monstro.caracteristicas || {};
  const carac =
    parseCarac(c.F) +
    parseCarac(c.H) +
    parseCarac(c.R) +
    parseCarac(c.A) +
    parseCarac(c.PdF);

  const pv = parseRecurso(monstro.pv);
  const pm = parseRecurso(monstro.pm);

  const habs = [
    ...(monstro.habilidades || []),
    ...(monstro.habilidades_extra
      ? `${monstro.habilidades_extra}`.split(/[;,.]/).map((h) => h.trim())
      : []),
  ].filter(Boolean);

  let habilidadeScore = 0;
  for (const h of habs) {
    const nome = h.toLowerCase().split("(")[0].trim();
    const nomeNorm = nome.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    const isForte =
      HABILIDADES_FORTES.has(nome) ||
      HABILIDADES_FORTES.has(nomeNorm) ||
      /veneno|regenera|imortal|invulner|paralisia|magia elemental|ataque múltiplo|resistência à magia/i.test(nome);
    const isFraco = HABILIDADES_FRACAS.has(nome) || HABILIDADES_FRACAS.has(nomeNorm);
    if (isForte) habilidadeScore += 2;
    else if (isFraco) habilidadeScore -= 1;
    else habilidadeScore += 0.5;
  }

  const imunidades = (monstro.imunidades || []).length;
  const vulnerabilidades = (monstro.vulnerabilidades || []).length;
  const fraquezas = monstro.fraqueza || monstro.fraquezas?.length ? 1 : 0;

  const escalaMult = pesoEscala(monstro.escala);

  const ataques = monstro.ataques_especificos?.length ?? 0;
  const ataquesBonus = Math.min(ataques * 2, 10);

  // Fórmula: stats (até 25) + recursos (até 20) + habilidades (até 25) + defesas (até 15) + escala
  const statsScore = Math.min(25, carac * 1.5);
  const recursosScore = Math.min(20, (pv + pm) / 4);
  const habScore = Math.min(25, Math.max(-5, habilidadeScore * 1.5));
  const defesaScore = Math.min(15, imunidades * 2 - vulnerabilidades * 2 - fraquezas * 3);
  const escalaBonus = (escalaMult - 1) * 10;
  const ataqueBonus = ataquesBonus;

  const raw =
    statsScore +
    recursosScore +
    habScore +
    defesaScore +
    escalaBonus +
    ataqueBonus;

  return Math.round(Math.max(0, Math.min(100, raw)));
}

/**
 * Retorna label de força (para exibição)
 */
export function labelForca(forca: number): string {
  if (forca < 15) return "Muito fraco";
  if (forca < 30) return "Fraco";
  if (forca < 50) return "Médio";
  if (forca < 70) return "Forte";
  if (forca < 85) return "Muito forte";
  return "Extremo";
}

/**
 * Cor para o indicador de força (texto)
 */
export function corForca(forca: number): string {
  if (forca < 15) return "text-stone-400";
  if (forca < 30) return "text-green-600";
  if (forca < 50) return "text-amber-600";
  if (forca < 70) return "text-orange-600";
  if (forca < 85) return "text-red-600";
  return "text-purple-700";
}

/**
 * Classe para badge de força (com fundo)
 */
export function badgeForca(forca: number): string {
  if (forca < 15) return "bg-stone-100 text-stone-600";
  if (forca < 30) return "bg-green-100 text-green-800";
  if (forca < 50) return "bg-amber-100 text-amber-800";
  if (forca < 70) return "bg-orange-100 text-orange-800";
  if (forca < 85) return "bg-red-100 text-red-800";
  return "bg-purple-100 text-purple-800";
}
