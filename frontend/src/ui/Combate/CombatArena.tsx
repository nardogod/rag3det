import { useState } from "react";
import { useCombatStore } from "@/store/combatStore";
import { usePersonagensStore } from "@/store/personagensStore";
import { TIPOS_ITENS, getItensPorTipo } from "@/data/itens";
import { CardCombate } from "./CardCombate";
import { LogNarrativo } from "./LogNarrativo";
import { FloatingDice } from "./FloatingDice";

export function CombatArena() {
  const { visao, acaoJogador, resetar, ultimoD6Jogador, usarItemMensagem } =
    useCombatStore();
  const personagensStore = usePersonagensStore();

  if (visao.estado === "selecao") {
    return null;
  }

  const batalha = visao.batalha;
  const mensagens = visao.mensagens;
  const turnoDoJogador =
    visao.estado === "em_combate" && batalha.turnoDe === "jogador";

  const desabilitarAcoes = !turnoDoJogador || visao.estado !== "em_combate";

  const handleAcao = (tipo: "ataque_corpo_a_corpo" | "ataque_distancia") => {
    if (desabilitarAcoes) return;
    acaoJogador({ lado: "jogador", tipo });
  };

  const magiasConhecidas = batalha.jogador.magiasConhecidas ?? [];
  const [mostrandoMagias, setMostrandoMagias] = useState(false);
  const [menu, setMenu] = useState<"principal" | "lutar" | "mochila">(
    "principal"
  );

  const personagemAtivo = personagensStore.getPersonagemAtivo();

  const handleMagia = (nome: string) => {
    if (desabilitarAcoes) return;
    acaoJogador({ lado: "jogador", tipo: "magia", magiaNome: nome });
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start gap-4">
        <CardCombate lado="jogador" batalha={batalha} />
        <CardCombate lado="monstro" batalha={batalha} />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold uppercase text-stone-600">
          Turno:
        </span>
        <span className="rounded bg-stone-200 px-2 py-0.5 text-xs font-medium text-stone-800">
          {batalha.turnoDe === "jogador"
            ? "Sua vez — escolha a ação"
            : "O monstro está agindo"}
        </span>
        {visao.estado === "vitoria" && (
          <span className="ml-2 rounded bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-800">
            Vitória do jogador
          </span>
        )}
        {visao.estado === "derrota" && (
          <span className="ml-2 rounded bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-800">
            Jogador derrotado
          </span>
        )}
      </div>

      {visao.estado === "em_combate" && (
        <div className="rounded-xl border border-stone-300 bg-white p-3 shadow-sm">
          <p className="mb-2 text-xs font-semibold uppercase text-stone-700">
            {menu === "principal" ? "Menu de batalha" : "Escolha sua ação"}
          </p>

          {menu === "principal" ? (
            <div className="grid max-w-xs grid-cols-2 gap-3">
              <button
                type="button"
                disabled={desabilitarAcoes}
                onClick={() => !desabilitarAcoes && setMenu("lutar")}
                className={`rounded-lg px-4 py-3 text-sm font-semibold ${
                  desabilitarAcoes
                    ? "cursor-not-allowed bg-stone-200 text-stone-500"
                    : "bg-amber-500 text-white hover:bg-amber-600"
                }`}
              >
                Lutar
              </button>
              <button
                type="button"
                disabled={desabilitarAcoes}
                onClick={() => {
                  if (desabilitarAcoes) return;
                  setMenu("mochila");
                }}
                className={`rounded-lg px-4 py-3 text-sm font-semibold ${
                  desabilitarAcoes
                    ? "cursor-not-allowed bg-stone-200 text-stone-500"
                    : "bg-emerald-500 text-white hover:bg-emerald-600"
                }`}
              >
                Mochila
              </button>
              <button
                type="button"
                disabled={desabilitarAcoes}
                className="rounded-lg bg-stone-200 px-4 py-3 text-sm font-semibold text-stone-500"
                title="Time (ainda em desenvolvimento)"
              >
                Time
              </button>
              <button
                type="button"
                disabled={desabilitarAcoes}
                onClick={() => {
                  if (desabilitarAcoes) return;
                  resetar();
                }}
                className={`rounded-lg px-4 py-3 text-sm font-semibold ${
                  desabilitarAcoes
                    ? "cursor-not-allowed bg-stone-200 text-stone-500"
                    : "bg-stone-800 text-white hover:bg-stone-900"
                }`}
              >
                Fugir
              </button>
            </div>
          ) : (
            menu === "lutar" ? (
              <>
              <div className="grid max-w-md grid-cols-2 gap-2">
                <button
                  type="button"
                  disabled={desabilitarAcoes}
                  onClick={() => handleAcao("ataque_corpo_a_corpo")}
                  className={`rounded-lg px-4 py-2 text-sm font-medium ${
                    desabilitarAcoes
                      ? "cursor-not-allowed bg-stone-200 text-stone-500"
                      : "bg-amber-500 text-white hover:bg-amber-600"
                  }`}
                >
                  Ataque corpo a corpo
                </button>
                <button
                  type="button"
                  disabled={desabilitarAcoes}
                  onClick={() => handleAcao("ataque_distancia")}
                  className={`rounded-lg px-4 py-2 text-sm font-medium ${
                    desabilitarAcoes
                      ? "cursor-not-allowed bg-stone-200 text-stone-500"
                      : "bg-sky-500 text-white hover:bg-sky-600"
                  }`}
                >
                  Ataque à distância
                </button>
              </div>
              {magiasConhecidas.length > 0 && (
                <div className="mt-3 space-y-1">
                  <button
                    type="button"
                    disabled={desabilitarAcoes}
                    onClick={() => setMostrandoMagias((v) => !v)}
                    className={`rounded-lg px-4 py-2 text-sm font-medium ${
                      desabilitarAcoes
                        ? "cursor-not-allowed bg-stone-200 text-stone-500"
                        : "bg-purple-500 text-white hover:bg-purple-600"
                    }`}
                  >
                    {mostrandoMagias ? "Fechar magias" : "Magias"}
                  </button>
                  {mostrandoMagias && (
                    <div className="mt-1 flex max-w-md flex-wrap gap-1">
                      {magiasConhecidas.map((nome) => (
                        <button
                          key={nome}
                          type="button"
                          disabled={desabilitarAcoes}
                          onClick={() => {
                            handleMagia(nome);
                            setMostrandoMagias(false);
                          }}
                          className={`rounded-full px-3 py-1 text-xs ${
                            desabilitarAcoes
                              ? "cursor-not-allowed bg-stone-200 text-stone-500"
                              : "bg-purple-100 text-purple-800 hover:bg-purple-200"
                          }`}
                        >
                          {nome}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
              <button
                type="button"
                onClick={() => {
                  setMostrandoMagias(false);
                  setMenu("principal");
                }}
                className="mt-3 rounded border border-stone-400 px-4 py-1 text-xs font-medium text-stone-700 hover:bg-stone-100"
              >
                Voltar ao menu
              </button>
            </>
            ) : (
              <div className="space-y-3">
                <p className="text-xs text-stone-600">
                  Escolha um item da mochila do personagem
                  {personagemAtivo ? ` ${personagemAtivo.ficha.nome}` : ""}.
                </p>
                <div className="flex max-h-40 flex-col gap-2 overflow-y-auto">
                  {TIPOS_ITENS.map((tipo) => {
                    const itens = getItensPorTipo(tipo);
                    if (!itens.length) return null;
                    return (
                      <div key={tipo}>
                        <p className="text-[11px] font-semibold uppercase text-stone-600">
                          {tipo}
                        </p>
                        <div className="mt-1 flex flex-wrap gap-1">
                          {itens.map((item) => (
                            <button
                              key={item.nome}
                              type="button"
                              disabled={desabilitarAcoes}
                              onClick={() => {
                                usarItemMensagem(item.nome);
                                setMenu("principal");
                              }}
                              className={`rounded-full px-3 py-1 text-xs ${
                                desabilitarAcoes
                                  ? "cursor-not-allowed bg-stone-200 text-stone-500"
                                  : "bg-emerald-100 text-emerald-800 hover:bg-emerald-200"
                              }`}
                            >
                              {item.nome}
                            </button>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
                <button
                  type="button"
                  onClick={() => setMenu("principal")}
                  className="mt-1 rounded border border-stone-400 px-4 py-1 text-xs font-medium text-stone-700 hover:bg-stone-100"
                >
                  Voltar ao menu
                </button>
              </div>
            )
          )}
        </div>
      )}

      {(visao.estado === "vitoria" || visao.estado === "derrota") && (
        <button
          type="button"
          onClick={resetar}
          className="rounded-lg border border-stone-400 px-4 py-2 text-sm text-stone-700 hover:bg-stone-200"
        >
          Nova batalha
        </button>
      )}

      <LogNarrativo mensagens={mensagens} />
      <FloatingDice value={ultimoD6Jogador} />
    </div>
  );
}

