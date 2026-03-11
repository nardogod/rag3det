export interface NivelInfo {
  nivel: number;
  xpAtual: number;
  xpNivel: number;
  xpProximo: number;
  falta: number;
  progresso: number; // 0–100
}

// Tabela de XP simples e crescente (estilo idle game)
// índice = nível, valor = XP acumulado mínimo para aquele nível
const XP_POR_NIVEL: number[] = [
  0, // placeholder índice 0
  0, // nível 1
  50, // nível 2
  150, // nível 3
  300, // nível 4
  500, // nível 5
  800, // nível 6
  1200, // nível 7
  1700, // nível 8
  2300, // nível 9
  3000, // nível 10
];

export function calcularNivel(xpTotal: number): NivelInfo {
  const xp = Math.max(0, xpTotal);
  let nivel = 1;
  for (let i = 1; i < XP_POR_NIVEL.length; i += 1) {
    if (xp >= XP_POR_NIVEL[i]) {
      nivel = i;
    } else {
      break;
    }
  }

  const xpNivel = XP_POR_NIVEL[nivel];
  const xpProximo =
    nivel + 1 < XP_POR_NIVEL.length
      ? XP_POR_NIVEL[nivel + 1]
      : XP_POR_NIVEL[XP_POR_NIVEL.length - 1] +
        500 * (nivel - (XP_POR_NIVEL.length - 2));
  const xpAtual = xp;
  const intervalo = Math.max(1, xpProximo - xpNivel);
  const progressoBruto = ((xpAtual - xpNivel) / intervalo) * 100;
  const progresso = Math.max(0, Math.min(100, Math.round(progressoBruto)));
  const falta = Math.max(0, xpProximo - xpAtual);

  return {
    nivel,
    xpAtual,
    xpNivel,
    xpProximo,
    falta,
    progresso,
  };
}

