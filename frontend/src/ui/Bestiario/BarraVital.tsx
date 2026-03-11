/**
 * Barra de PV/PM no estilo pixel art retro (8-bit/16-bit).
 * Sempre 10 segmentos; em vermelho/azul só os preenchidos (cada segmento = 10 pts).
 * Vermelho para PV, azul para PM.
 */

interface BarraVitalProps {
  /** Valor bruto: "variável", "1d+6", "12", "0", etc. */
  valor: string;
  /** "pv" = vermelho, "pm" = azul */
  tipo: "pv" | "pm";
  /** Altura em px (padrão 16) */
  altura?: number;
  /** Ocultar texto do valor (só barra, para listas compactas) */
  compacto?: boolean;
}

const CORES = {
  pv: {
    cheio: "#FF3333",
    vazio: "#3A3A4A",
    borda: "#1a1a1a",
    sombra: "rgba(0,0,0,0.4)",
  },
  pm: {
    cheio: "#3366FF",
    vazio: "#3A3A4A",
    borda: "#1a1a1a",
    sombra: "rgba(0,0,0,0.4)",
  },
};

const PTS_POR_SEG = 10;

/**
 * Extrai valor numérico de PV/PM para calcular segmentos preenchidos.
 * Cada segmento = 10 pts. Retorna 0–10 (segmentos preenchidos).
 * Formato "atual/max" (ex.: "8/15") mostra proporção atual do máximo.
 */
function parseValorParaSegmentos(valor: string): number {
  const v = (valor || "").trim().toLowerCase();
  if (!v || v === "0") return 0;
  // Formato atual/max para personagens (proporção)
  if (v.includes("/")) {
    const [a, b] = v.split("/").map((s) => parseInt(s.trim(), 10));
    if (!isNaN(a) && !isNaN(b) && b > 0) {
      return Math.min(10, Math.max(0, Math.round((a / b) * 10)));
    }
  }
  if (v === "variável" || v === "variavel") return 5; // fallback: metade
  const num = parseInt(v, 10);
  if (!isNaN(num)) {
    const segs = Math.ceil(num / PTS_POR_SEG);
    return Math.min(10, Math.max(0, segs));
  }
  if (v.includes("d")) {
    const match = v.match(/^(\d+)d\+?(\d+)?/);
    if (match) {
      const dados = parseInt(match[1], 10);
      const bonus = parseInt(match[2] || "0", 10);
      const media = Math.round(dados * 3.5 + bonus);
      const segs = Math.ceil(media / PTS_POR_SEG);
      return Math.min(10, Math.max(0, segs));
    }
  }
  return 5;
}

const SEGMENTOS_FIXOS = 10;

export function BarraVital({
  valor,
  tipo,
  altura = 16,
  compacto = false,
}: BarraVitalProps) {
  const segmentos = SEGMENTOS_FIXOS;
  const nivel = parseValorParaSegmentos(valor);
  const cores = CORES[tipo];
  const larguraSeg = 6;
  const larguraTotal = segmentos * larguraSeg + 4;

  const isProporcao = (valor || "").trim().includes("/");
  const title = isProporcao
    ? `${tipo.toUpperCase()}: ${valor} (atual/máx)`
    : `${tipo.toUpperCase()}: ${valor} (cada segmento = ${PTS_POR_SEG} pts)`;

  return (
    <div className="inline-flex items-center gap-1.5" title={title}>
      {/* Ícone pixel (12x12): coração para PV, cristal para PM */}
      <div
        className="flex-shrink-0"
        style={{
          width: 12,
          height: 12,
          backgroundColor: nivel > 0 ? cores.cheio : cores.vazio,
          border: `1px solid ${cores.borda}`,
          boxShadow: `0 1px 0 ${cores.sombra}`,
          borderRadius: tipo === "pv" ? "2px" : "1px",
        }}
        aria-hidden
      />
      {/* Barra: 10 segmentos fixos; preenchidos = quantidade do monstro */}
      <div
        className="flex"
        style={{
          height: altura,
          width: larguraTotal,
          border: `1px solid ${cores.borda}`,
          borderRadius: "0 8px 8px 0",
          boxShadow: `0 1px 0 ${cores.sombra}`,
          overflow: "hidden",
        }}
      >
        {Array.from({ length: segmentos }).map((_, i) => (
          <div
            key={i}
            className="flex-1 border-r last:border-r-0"
            style={{
              backgroundColor: i < nivel ? cores.cheio : cores.vazio,
              borderColor: cores.borda,
              boxShadow: i < nivel ? "inset 0 1px 0 rgba(255,255,255,0.2)" : undefined,
            }}
          />
        ))}
      </div>
      {!compacto && (
        <span className="text-[10px] text-stone-500 tabular-nums">{valor}</span>
      )}
    </div>
  );
}
