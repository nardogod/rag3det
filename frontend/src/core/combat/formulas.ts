import type {
  EstadoLado,
  TipoAcaoBasica,
  ResultadoRolagem,
} from "./types";

function rolarD6(): number {
  return Math.floor(Math.random() * 6) + 1;
}

export function rolarFA(
  lado: EstadoLado,
  tipo: TipoAcaoBasica
): ResultadoRolagem {
  const d6 = rolarD6();
  let base = 0;
  if (tipo === "ataque_corpo_a_corpo") {
    base = lado.F + lado.H;
  } else if (tipo === "ataque_distancia" || tipo === "magia") {
    base = lado.PdF + lado.H + (tipo === "magia" ? 2 : 0);
  } else {
    base = lado.H;
  }
  const total = base + d6;
  return { d6, total };
}

export function rolarFD(lado: EstadoLado): ResultadoRolagem {
  const d6 = rolarD6();
  const base = lado.A + lado.H;
  const total = base + d6;
  return { d6, total };
}

export function aplicarDano(
  pvAtual: number,
  dano: number
): number {
  return Math.max(0, pvAtual - Math.max(0, dano));
}

export function parseNumeroSimples(valor: string | undefined | null): number {
  if (!valor) return 0;
  const limpo = valor.trim();
  const num = parseInt(limpo, 10);
  return Number.isNaN(num) ? 0 : num;
}

