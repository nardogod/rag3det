import type { EstadoBatalha } from "@/core/combat/types";
import { calcularNivel } from "@/core/experiencia";

interface CardCombateProps {
  lado: "jogador" | "monstro";
  batalha: EstadoBatalha;
}

export function CardCombate({ lado, batalha }: CardCombateProps) {
  const dados = lado === "jogador" ? batalha.jogador : batalha.monstro;

  const barra = (atual: number, max: number, cor: string) => {
    const width = max > 0 ? `${Math.round((atual / max) * 100)}%` : "0%";
    return (
      <div className="h-3 w-full rounded-full bg-stone-200">
        <div
          className={`h-3 rounded-full ${cor}`}
          style={{ width }}
        />
      </div>
    );
  };

  return (
    <div className="flex-1 min-w-[220px] rounded-xl border-2 border-stone-300 bg-white p-4 shadow-sm">
      <h3 className="text-lg font-bold text-stone-800">
        {dados.nome}
      </h3>
      <p className="mt-1 text-xs uppercase tracking-wide text-stone-500">
        {lado === "jogador" ? "Personagem" : "Monstro"}
      </p>

      <div className="mt-3 space-y-2 text-xs text-stone-700">
        <div className="flex items-center justify-between">
          <span className="font-semibold">PV</span>
          <span>
            {dados.pvAtual} / {dados.pvMax}
          </span>
        </div>
        {barra(dados.pvAtual, dados.pvMax, "bg-emerald-500")}

        <div className="flex items-center justify-between">
          <span className="font-semibold">PM</span>
          <span>
            {dados.pmAtual} / {dados.pmMax}
          </span>
        </div>
        {barra(dados.pmAtual, dados.pmMax, "bg-sky-500")}
      </div>

      <div className="mt-3 grid grid-cols-5 gap-1 text-center text-[10px] text-stone-600">
        <div className="rounded bg-stone-50 p-1">
          <div className="text-[9px] font-semibold">F</div>
          <div className="text-xs">{dados.F}</div>
        </div>
        <div className="rounded bg-stone-50 p-1">
          <div className="text-[9px] font-semibold">H</div>
          <div className="text-xs">{dados.H}</div>
        </div>
        <div className="rounded bg-stone-50 p-1">
          <div className="text-[9px] font-semibold">R</div>
          <div className="text-xs">{dados.R}</div>
        </div>
        <div className="rounded bg-stone-50 p-1">
          <div className="text-[9px] font-semibold">A</div>
          <div className="text-xs">{dados.A}</div>
        </div>
        <div className="rounded bg-stone-50 p-1">
          <div className="text-[9px] font-semibold">PdF</div>
          <div className="text-xs">{dados.PdF}</div>
        </div>
      </div>

      {lado === "jogador" && (
        <div className="mt-3 space-y-2">
          {(() => {
            const info = calcularNivel(dados.experiencia ?? 0);
            return (
              <>
                <div className="flex items-center justify-between text-[11px] text-stone-600">
                  <span className="font-semibold">
                    Nível {info.nivel}
                  </span>
                  <span>
                    XP {info.xpAtual}/{info.xpProximo} (falta {info.falta})
                  </span>
                </div>
                <div className="h-2 w-full rounded-full bg-stone-200">
                  <div
                    className="h-2 rounded-full bg-indigo-500"
                    style={{ width: `${info.progresso}%` }}
                  />
                </div>
              </>
            );
          })()}

          {dados.itensEquipados && dados.itensEquipados.length > 0 && (
            <div className="pt-1 border-t border-stone-200">
              <p className="mb-1 text-[10px] font-semibold uppercase text-stone-600">
                Itens equipados
              </p>
              <div className="flex flex-wrap gap-1">
                {dados.itensEquipados.map((nome) => (
                  <span
                    key={nome}
                    className="rounded-full bg-stone-100 px-2 py-0.5 text-[10px] text-stone-700"
                  >
                    {nome}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

