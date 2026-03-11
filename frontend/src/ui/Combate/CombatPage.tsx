import { useMemo, useState } from "react";
import { useCombatStore } from "@/store/combatStore";
import { usePersonagensStore } from "@/store/personagensStore";
import { getMonstros } from "@/data/monstros";
import { CombatArena } from "./CombatArena";
import { obterLivros } from "@/core/bestiario";
import { calcularForcaMonstro, labelForca } from "@/core/forcaMonstro";

export function CombatPage() {
  const personagensStore = usePersonagensStore();
  const {
    visao,
    monstroSelecionado,
    setMonstroSelecionado,
    iniciarBatalha,
  } = useCombatStore();

  const personagemAtivo = personagensStore.getPersonagemAtivo();

  const monstros = useMemo(() => getMonstros(), []);
  const livros = useMemo(() => obterLivros(monstros), [monstros]);
  const [livroSelecionado, setLivroSelecionado] = useState<string>("");
  const [buscaMonstro, setBuscaMonstro] = useState<string>("");

  const monstrosFiltrados = useMemo(() => {
    let resultado = monstros;
    if (livroSelecionado) {
      resultado = resultado.filter((m) => m.livro === livroSelecionado);
    }
    if (buscaMonstro.trim()) {
      const termo = buscaMonstro.trim().toLowerCase();
      resultado = resultado.filter((m) =>
        (m.nome || "").toLowerCase().includes(termo)
      );
    }
    return resultado;
  }, [livroSelecionado, buscaMonstro, monstros]);

  const podeIniciar =
    personagemAtivo != null && monstroSelecionado != null;

  return (
    <div className="mx-auto max-w-5xl space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-stone-800">
            Combate 3D&T — Duelo Rápido
          </h1>
          <p className="text-xs text-stone-500">
            Escolha um personagem salvo e um monstro do bestiário para colocar frente a frente.
            O sistema atua como Mestre imparcial, descrevendo cada lance.
          </p>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="space-y-3 rounded-xl border-2 border-stone-300 bg-white p-4 shadow-sm">
          <h2 className="text-sm font-bold uppercase text-stone-700">
            Personagem
          </h2>
          {personagemAtivo ? (
            <div className="space-y-1 text-sm text-stone-700">
              <p>
                <span className="font-semibold">Nome:</span>{" "}
                {personagemAtivo.ficha.nome}
              </p>
              <p>
                <span className="font-semibold">PV:</span>{" "}
                {personagemAtivo.ficha.pvAtual} /{" "}
                {personagemAtivo.ficha.pvMax}{" "}
                <span className="ml-2 font-semibold">PM:</span>{" "}
                {personagemAtivo.ficha.pmAtual} /{" "}
                {personagemAtivo.ficha.pmMax}
              </p>
            </div>
          ) : (
            <p className="text-sm text-stone-500">
              Nenhum personagem ativo. Vá até a Ficha, crie ou carregue um
              personagem e salve para poder usá-lo em combate.
            </p>
          )}
        </div>

        <div className="space-y-3 rounded-xl border-2 border-stone-300 bg-white p-4 shadow-sm">
          <h2 className="text-sm font-bold uppercase text-stone-700">
            Monstro do Bestiário
          </h2>
          <p className="text-xs text-stone-500">
            Escolha primeiro o livro do bestiário e, em seguida, o monstro que
            deseja enfrentar. Os dados de combate vêm da ficha original.
          </p>
          <label className="mt-1 block text-[11px] font-medium text-stone-600">
            Livro
          </label>
          <select
            value={livroSelecionado}
            onChange={(e) => {
              const livro = e.target.value;
              setLivroSelecionado(livro);
              setMonstroSelecionado(null);
            }}
            className="mt-0.5 w-full rounded border border-stone-300 px-3 py-2 text-sm"
          >
            <option value="">— Todos os livros —</option>
            {livros.map((livro) => (
              <option key={livro} value={livro}>
                {livro}
              </option>
            ))}
          </select>
          <label className="mt-3 block text-[11px] font-medium text-stone-600">
            Monstro
          </label>
          <input
            type="text"
            value={buscaMonstro}
            onChange={(e) => setBuscaMonstro(e.target.value)}
            placeholder="Buscar por nome (ex.: dragão)"
            className="mt-1 w-full rounded border border-stone-300 px-3 py-2 text-sm"
          />
          <select
            value={monstroSelecionado?.nome ?? ""}
            onChange={(e) => {
              const nome = e.target.value;
              const m = monstrosFiltrados.find((mm) => mm.nome === nome) ?? null;
              setMonstroSelecionado(m);
            }}
            className="mt-1 w-full rounded border border-stone-300 px-3 py-2 text-sm"
          >
            <option value="">— Escolher monstro —</option>
            {monstrosFiltrados.map((m) => {
              const forca = calcularForcaMonstro(m);
              const rotulo = labelForca(forca);
              return (
                <option key={m.nome} value={m.nome}>
                  {m.nome} — Força: {rotulo} ({forca})
                </option>
              );
            })}
          </select>
          {monstroSelecionado && (
            <div className="mt-2 space-y-1 text-sm text-stone-700">
              <p>
                <span className="font-semibold">PV/PM (texto):</span>{" "}
                {monstroSelecionado.pv ?? "—"} /{" "}
                {monstroSelecionado.pm ?? "—"}
              </p>
              <p>
                <span className="font-semibold">Força estimada:</span>{" "}
                {(() => {
                  const forca = calcularForcaMonstro(monstroSelecionado);
                  const rotulo = labelForca(forca);
                  return `${rotulo} (${forca})`;
                })()}
              </p>
              <p className="text-xs text-stone-500">
                Valores exatos para o combate são derivados desses campos da ficha
                e das características do monstro.
              </p>
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          disabled={!podeIniciar || visao.estado !== "selecao"}
          onClick={iniciarBatalha}
          className={`rounded-lg px-6 py-2 text-sm font-medium ${
            !podeIniciar || visao.estado !== "selecao"
              ? "cursor-not-allowed bg-stone-200 text-stone-500"
              : "bg-emerald-600 text-white hover:bg-emerald-700"
          }`}
        >
          Iniciar Batalha
        </button>
        {!podeIniciar && (
          <span className="text-xs text-stone-500">
            Selecione um personagem ativo e um monstro para habilitar o combate.
          </span>
        )}
      </div>

      {(visao.estado === "em_combate" ||
        visao.estado === "vitoria" ||
        visao.estado === "derrota") && <CombatArena />}
    </div>
  );
}

