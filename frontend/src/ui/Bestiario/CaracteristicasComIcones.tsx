/**
 * Exibe características 3D&T (F, H, R, A, PdF) com ícones/emotes.
 * Formato: (ícone)F1, (ícone)H0, etc.
 */

import type { Caracteristicas } from "@/types/monstro";

const ICONES: Record<string, string> = {
  F: "💪",   // Força
  H: "🎯",   // Habilidade
  R: "❤️",   // Resistência
  A: "🛡️",   // Armadura
  PdF: "⚔️", // Poder de Fogo
};

const LABELS: Record<string, string> = {
  F: "Força",
  H: "Habilidade",
  R: "Resistência",
  A: "Armadura",
  PdF: "PdF",
};

const ORDEM = ["F", "H", "R", "A", "PdF"] as const;

interface CaracteristicasComIconesProps {
  caracteristicas: Caracteristicas | null | undefined;
  className?: string;
}

export function CaracteristicasComIcones({
  caracteristicas,
  className = "",
}: CaracteristicasComIconesProps) {
  if (!caracteristicas || Object.keys(caracteristicas).length === 0) {
    return <span className="text-stone-500">—</span>;
  }

  const partes = ORDEM.filter((k) => caracteristicas[k] != null).map(
    (k) => {
      const v = caracteristicas[k] ?? "";
      const icon = ICONES[k];
      const label = LABELS[k];
      return (
        <span key={k} title={label} className="whitespace-nowrap">
          {icon}{k}{v}
        </span>
      );
    }
  );

  if (partes.length === 0) return <span className="text-stone-500">—</span>;

  return (
    <span className={`inline-flex flex-wrap items-center gap-x-2 gap-y-0.5 ${className}`}>
      {partes.map((p, i) => (
        <span key={i} className="inline-flex items-center">
          {i > 0 && <span className="text-stone-400 mr-1">,</span>}
          {p}
        </span>
      ))}
    </span>
  );
}
