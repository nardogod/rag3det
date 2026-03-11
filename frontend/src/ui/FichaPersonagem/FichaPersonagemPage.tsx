/**
 * Ficha de Personagem 3D&T — Cópia interativa
 * Base: Manual 3D&T Turbinado Digital / Defensores de Tóquio 3ª Ed., p. 144
 */

import { useState, useMemo, useEffect } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { usePersonagemStore } from "@/store/personagemStore";
import { usePersonagensStore } from "@/store/personagensStore";
import type { CaracteristicaKey, CaminhoMagia, NivelPontuacao } from "@/types/personagem";
import { CAMINHOS_MAGIA } from "@/types/personagem";
import {
  pontosDisponiveis,
  calcularPvMax,
  calcularPmMax,
} from "@/core/construcaoPersonagem";
import {
  vantagens,
  desvantagens,
  racas,
  parseCusto,
  getRaca,
} from "@/data/vantagens";
import { getMagias } from "@/data/magias";
import {
  vantagensDisponiveis,
  desvantagensDisponiveis,
  magiasDisponiveis,
} from "@/core/dependencias";
import { getPacoteRacial, aplicarModificadoresRaca } from "@/data/racaPacote";
import { TIPOS_DANO_FORCA, TIPOS_DANO_PDF } from "@/data/tiposDano";
import { getItensPorTipo } from "@/data/itens";
import { ModalLista } from "./ModalLista";

const CARAC_LABELS: Record<CaracteristicaKey, string> = {
  F: "Força",
  H: "Habilidade",
  R: "Resistência",
  A: "Armadura",
  PdF: "Poder de Fogo",
};

const CARAC_DESCRICOES: Record<CaracteristicaKey, string> = {
  F: "Controla o dano em combate corpo a corpo e testes de Força (empurrar, carregar).",
  H: "Agilidade, destreza e precisão. Usada em esquiva, testes de perícia e na Força de Defesa (FD).",
  R: "Quanto mais Resistência, mais PV e PM (R×5 cada). Também usada em testes contra magias e venenos.",
  A: "Proteção contra dano. Reduz o dano recebido em combate.",
  PdF: "Controla ataques à distância (flechas, raios, magias ofensivas) e a Força de Ataque à distância.",
};

const PONTUACAO_LABELS: Record<NivelPontuacao, string> = {
  pessoa_comum: "Pessoa Comum (0–4 pts)",
  novato: "Novato (5 pts)",
  lutador: "Lutador (7 pts)",
  campeao: "Campeão (10 pts)",
  lenda: "Lenda (12 pts)",
};

const PONTUACAO_DESCRICAO =
  "Quantidade de pontos que o Mestre define para criar o personagem. Quanto mais pontos, mais poderoso.";

const CAMINHOS_DESCRICOES: Record<string, string> = {
  Água: "Magias de água, gelo e cura. Exigido para várias magias de proteção.",
  Ar: "Magias de vento, voo e eletricidade.",
  Fogo: "Magias de fogo e destruição.",
  Luz: "Magias de luz, ilusão e cura.",
  Terra: "Magias de terra, pedra e natureza.",
  Trevas: "Magias de escuridão, necromancia e debilitação.",
};

function FitaCheckboxes({
  max,
  atual,
  onToggle,
  label,
}: {
  max: number;
  atual: number;
  onToggle: (index: number) => void;
  label: string;
}) {
  return (
    <div className="flex flex-wrap items-center gap-1">
      <span className="w-16 shrink-0 text-xs font-medium text-stone-600 sm:w-20">
        {label}
      </span>
      <div className="flex flex-wrap gap-0.5">
        {Array.from({ length: max }, (_, i) => (
          <button
            key={i}
            type="button"
            onClick={() => onToggle(i)}
            className={`h-5 w-5 rounded border-2 transition sm:h-6 sm:w-6 ${
              i < atual
                ? "border-amber-500 bg-amber-400"
                : "border-stone-300 bg-stone-100 hover:border-amber-400"
            }`}
          />
        ))}
      </div>
      <span className="text-xs text-stone-500">
        {atual}/{max}
      </span>
    </div>
  );
}

function CaracCirculos({
  valor,
  onChange,
  label,
  max,
  descricao,
}: {
  valor: number;
  onChange: (v: number) => void;
  label: string;
  max: number;
  descricao?: string;
}) {
  return (
    <div className="flex flex-col gap-0.5">
      <div className="flex items-center gap-1">
        <span className="w-8 shrink-0 text-xs font-medium text-stone-600 sm:w-10">
          {label}
        </span>
        <div className="flex gap-0.5">
          {[0, 1, 2, 3, 4, 5].slice(0, max + 1).map((n) => (
            <button
              key={n}
              type="button"
              onClick={() => onChange(n)}
              className={`h-5 w-5 rounded-full border-2 transition sm:h-6 sm:w-6 ${
                n < valor
                  ? "border-amber-600 bg-amber-500"
                  : "border-stone-300 bg-white hover:border-amber-400"
              }`}
            />
          ))}
        </div>
      </div>
      {descricao && (
        <p className="text-[10px] text-stone-500 pl-0 sm:pl-10">{descricao}</p>
      )}
    </div>
  );
}

export function FichaPersonagemPage() {
  const navigate = useNavigate();
  const { personagemId: personagemIdFromUrl } = useParams<{ personagemId: string }>();
  const store = usePersonagemStore();
  const personagensStore = usePersonagensStore();
  const personagemIdParaEditar = personagemIdFromUrl ?? null;
  const [personagemEditandoId, setPersonagemEditandoId] = useState<string | null>(null);
  const [modalAberto, setModalAberto] = useState<
    "vantagens" | "desvantagens" | "magias" | "racas" | "racaDetalhe" | null
  >(null);
  const [modalItensTipo, setModalItensTipo] = useState<string | null>(null);

  useEffect(() => {
    if (personagemIdParaEditar) {
      const p = personagensStore.getPersonagemById(personagemIdParaEditar);
      if (p) {
        store.loadFromFicha(p.ficha);
        setPersonagemEditandoId(p.id);
        personagensStore.setPersonagemAtivo(p.id);
      }
    }
  }, [personagemIdParaEditar]);

  const handleSalvar = () => {
    const ficha = store.toFicha();
    if (!ficha.nome?.trim()) {
      alert("Informe o nome do personagem antes de salvar.");
      return;
    }
    if (ptsDisponiveis < 0) {
      alert(
        `Não é possível salvar com pontos negativos (${ptsDisponiveis}). Remova características, vantagens ou magias até ficar com 0 ou mais pontos.`
      );
      return;
    }
    if (personagemEditandoId) {
      personagensStore.updatePersonagem(personagemEditandoId, ficha);
    } else {
      personagensStore.addPersonagem(ficha);
    }
    store.reset();
    setPersonagemEditandoId(null);
    navigate("/", { replace: true });
  };

  const handleNovoPersonagem = () => {
    store.reset();
    setPersonagemEditandoId(null);
    navigate("/ficha", { replace: true });
  };

  const magias = useMemo(() => getMagias(), []);

  const getVantagemCusto = (nome: string) =>
    vantagens.find((v) => v.nome === nome)?.custo ?? "0";
  const getDesvantagemCusto = (nome: string) =>
    desvantagens.find((d) => d.nome === nome)?.custo ?? "0";
  const getRacaCusto = (nome: string) =>
    racas.find((r) => r.nome === nome)?.custo ?? "0";

  const ptsDisponiveis = useMemo(
    () =>
      pontosDisponiveis(
        store.nivelPontuacao,
        store.caracteristicas,
        store.caminhosMagia,
        store.vantagens,
        store.desvantagens,
        store.raca,
        store.magiasConhecidas,
        (n) => parseCusto(getVantagemCusto(n)),
        (n) => parseCusto(getDesvantagemCusto(n)),
        (n) => parseCusto(getRacaCusto(n))
      ),
    [
      store.nivelPontuacao,
      store.caracteristicas,
      store.caminhosMagia,
      store.vantagens,
      store.desvantagens,
      store.raca,
      store.magiasConhecidas,
    ]
  );

  const pacoteRacial = useMemo(
    () => getPacoteRacial(store.raca),
    [store.raca]
  );

  const caracteristicasEfetivas = useMemo(
    () => aplicarModificadoresRaca(store.caracteristicas, store.raca),
    [store.caracteristicas, store.raca]
  );

  const estadoPersonagem = useMemo(
    () => ({
      raca: store.raca,
      vantagens: [...pacoteRacial.vantagens, ...store.vantagens],
      desvantagens: [...pacoteRacial.desvantagens, ...store.desvantagens],
      caminhosMagia: store.caminhosMagia,
      nivel: store.nivelPontuacao,
      vantagensEscolhidas: store.vantagens,
      desvantagensEscolhidas: store.desvantagens,
      getCustoDesvantagem: (nome: string) =>
        Math.abs(parseCusto(desvantagens.find((d) => d.nome === nome)?.custo ?? "0")),
    }),
    [
      store.raca,
      pacoteRacial.vantagens,
      pacoteRacial.desvantagens,
      store.vantagens,
      store.desvantagens,
      store.caminhosMagia,
      store.nivelPontuacao,
    ]
  );

  const nomesVantagensDisponiveis = useMemo(
    () =>
      new Set(
        vantagensDisponiveis(vantagens, estadoPersonagem).map((v) => v.nome)
      ),
    [estadoPersonagem]
  );

  const nomesDesvantagensDisponiveis = useMemo(
    () =>
      new Set(
        desvantagensDisponiveis(desvantagens, estadoPersonagem).map((d) => d.nome)
      ),
    [estadoPersonagem]
  );

  const magiasFiltradas = useMemo(
    () =>
      magiasDisponiveis(magias, store.caminhosMagia).map((m) => m.nome),
    [magias, store.caminhosMagia]
  );

  const nomesMagiasDisponiveis = useMemo(
    () => new Set(magiasFiltradas),
    [magiasFiltradas]
  );

  const itensMagias = useMemo(
    () =>
      magias.map((m) => ({
        nome: m.nome,
        escola: m.escola,
        descricao: m.descricao
          ? m.descricao + (m.custo ? `\n\nCusto em PM: ${m.custo}` : "")
          : undefined,
        custo: "1 ponto",
      })),
    [magias]
  );

  const itensVantagens = useMemo(
    () =>
      vantagens.map((v) => ({
        nome: v.nome,
        custo: v.custo,
        efeito: v.efeito,
        livro: v.livro,
        unica: v.unica === true,
      })),
    []
  );

  const itensDesvantagens = useMemo(
    () =>
      desvantagens.map((d) => ({
        nome: d.nome,
        custo: d.custo,
        efeito: d.efeito,
        livro: d.livro,
        unica: d.unica === true,
      })),
    []
  );

  const maxCarac = useMemo(
    () =>
      ({
        pessoa_comum: 1,
        novato: 3,
        lutador: 4,
        campeao: 5,
        lenda: 5,
      }[store.nivelPontuacao]),
    [store.nivelPontuacao]
  );

  const todasVantagens = useMemo(
    () => [...pacoteRacial.vantagens, ...store.vantagens],
    [pacoteRacial.vantagens, store.vantagens]
  );

  const pvMaxComputed = useMemo(
    () => calcularPvMax(caracteristicasEfetivas.R ?? 0, todasVantagens),
    [caracteristicasEfetivas.R, todasVantagens]
  );

  const pmMaxComputed = useMemo(
    () => calcularPmMax(caracteristicasEfetivas.R ?? 0, todasVantagens),
    [caracteristicasEfetivas.R, todasVantagens]
  );

  useEffect(() => {
    store.setPvMax(pvMaxComputed);
    store.setPmMax(pmMaxComputed);
  }, [pvMaxComputed, pmMaxComputed]);

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-stone-800">
          Ficha de Personagem 3D&T
        </h1>
        <p className="text-xs text-stone-500">
          Defensores de Tóquio 3ª Ed. / Manual Turbinado, p. 144
        </p>
      </div>

      {/* Pontuação e pontos disponíveis */}
      <div className="flex flex-wrap items-center gap-4 rounded-lg border-2 border-amber-200 bg-amber-50 p-4">
        <div>
          <label className="block text-xs font-medium text-stone-600">
            Pontuação (Mestre define)
          </label>
          <p className="text-[10px] text-stone-500 mb-0.5">{PONTUACAO_DESCRICAO}</p>
          <select
            value={store.nivelPontuacao}
            onChange={(e) =>
              store.setNivelPontuacao(e.target.value as NivelPontuacao)
            }
            className="mt-1 rounded border border-stone-300 px-3 py-2"
          >
            {(Object.keys(PONTUACAO_LABELS) as NivelPontuacao[]).map((n) => (
              <option key={n} value={n}>
                {PONTUACAO_LABELS[n]}
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-stone-600">
            Pontos disponíveis:
          </span>
          <span
            className={`text-2xl font-bold ${
              ptsDisponiveis >= 0 ? "text-green-600" : "text-red-600"
            }`}
          >
            {ptsDisponiveis}
          </span>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Coluna esquerda */}
        <div className="space-y-6 rounded-xl border-2 border-stone-300 bg-white p-4 shadow-sm">
          <div>
            <label className="block text-xs font-medium text-stone-600">
              Nome do Personagem
            </label>
            <input
              type="text"
              value={store.nome}
              onChange={(e) => store.setCampo("nome", e.target.value)}
              className="mt-1 w-full rounded border border-stone-300 px-3 py-2"
            />
          </div>

          {/* Raça (Vantagem Única) */}
          <div>
            <label
              className="block cursor-pointer text-xs font-medium text-stone-600"
              onClick={() =>
                store.raca
                  ? setModalAberto("racaDetalhe")
                  : setModalAberto("racas")
              }
              onKeyDown={(e) =>
                e.key === "Enter" &&
                (store.raca
                  ? setModalAberto("racaDetalhe")
                  : setModalAberto("racas"))
              }
              tabIndex={0}
              role="button"
            >
              Raça (Vantagem Única)
            </label>
            <p className="text-[10px] text-stone-500">
              A raça define o que o personagem é — anão, elfo, goblin, paladino — e traz um pacote de vantagens e desvantagens automáticas (incluídas no custo total; não paga nem ganha pontos por elas). Cada personagem pode ter apenas uma raça. Exceções: Paladino pode ser Anão, Meio-Elfo ou Meio-Orc; Construto pode ter Membros Elásticos/Extras. Forma Alternativa: uma raça por forma, mas problemas se acumulam. Clique para ver as opções.
            </p>
            <button
              type="button"
              onClick={() =>
                store.raca
                  ? setModalAberto("racaDetalhe")
                  : setModalAberto("racas")
              }
              className="mt-1 w-full rounded border border-stone-300 bg-stone-50 px-3 py-2 text-left hover:bg-amber-50"
            >
              {store.raca || "Clique para selecionar raça"}
            </button>
            {store.raca && pacoteRacial.efeitosEspeciais && pacoteRacial.efeitosEspeciais.length > 0 && (
              <ul className="mt-1 space-y-0.5 text-[10px] text-stone-600">
                {pacoteRacial.efeitosEspeciais.map((e, i) => (
                  <li key={i}>• {e}</li>
                ))}
              </ul>
            )}
          </div>

          {/* Características */}
          <div>
            <h2 className="mb-2 text-sm font-bold uppercase text-stone-700">
              Características (máx {maxCarac})
            </h2>
            {Object.keys(pacoteRacial.modificadores).length > 0 && (
              <p className="mb-1 text-[10px] text-amber-700">
                Raça {store.raca} aplica bônus automáticos.
              </p>
            )}
            <div className="space-y-3">
              {(["F", "H", "R", "A", "PdF"] as CaracteristicaKey[]).map(
                (key) => {
                  const base = store.caracteristicas[key];
                  const efetivo = caracteristicasEfetivas[key];
                  const temMod = base !== efetivo;
                  return (
                    <div key={key} className="flex flex-wrap items-start gap-2">
                      <div className="flex-1 min-w-0">
                        <CaracCirculos
                          label={CARAC_LABELS[key]}
                          valor={base}
                          onChange={(v) => store.setCaracteristica(key, v)}
                          max={maxCarac}
                          descricao={CARAC_DESCRICOES[key]}
                        />
                      </div>
                      {temMod && (
                        <span className="text-[10px] text-amber-700 shrink-0">
                          → {efetivo} efetivo
                        </span>
                      )}
                    </div>
                  );
                }
              )}
            </div>
          </div>

          {/* PV / PM — Manual 3D&T: PV = PM = R×5; não custam pontos */}
          <div className="space-y-3">
            <h2 className="text-sm font-bold uppercase text-stone-700">
              Pontos de Vida / Magia
            </h2>
            <p className="text-[10px] text-stone-500">
              PV e PM vêm da Resistência (R×5, mín. 1) — não custam pontos. Os quadradinhos marcam dano/gasto em jogo. +5 por Pontos de Vida Extras ou Pontos de Magia Extras.
            </p>
            <FitaCheckboxes
              label="PV"
              max={pvMaxComputed}
              atual={store.pvAtual}
              onToggle={(i) => store.togglePvBox(i, pvMaxComputed)}
            />
            <FitaCheckboxes
              label="PM"
              max={pmMaxComputed}
              atual={store.pmAtual}
              onToggle={(i) => store.togglePmBox(i, pmMaxComputed)}
            />
          </div>

          {/* Vantagens (raça + escolhidas) */}
          <div>
            <h2 className="mb-1 text-sm font-bold uppercase text-stone-700">
              Vantagens
            </h2>
            <p className="mb-1 text-[10px] text-stone-500">
              Poderes especiais comprados com pontos. Da raça (automáticas) + escolhidas. Clique em cada item no modal para ver o efeito.
            </p>
            <button
              type="button"
              onClick={() => setModalAberto("vantagens")}
              className="w-full rounded border border-stone-300 bg-stone-50 py-2 text-sm hover:bg-amber-50"
            >
              + Adicionar vantagem
            </button>
            <ul className="mt-2 space-y-1">
              {pacoteRacial.vantagens.map((n) => (
                <li
                  key={`raca-${n}`}
                  className="flex items-center justify-between rounded bg-amber-100 px-2 py-1 text-sm"
                >
                  <span>
                    {n}
                    <span className="ml-1.5 rounded bg-amber-200 px-1 text-[10px] text-amber-800">
                      raça
                    </span>
                  </span>
                </li>
              ))}
              {store.vantagens.map((n) => (
                <li
                  key={n}
                  className="flex items-center justify-between rounded bg-amber-50 px-2 py-1 text-sm"
                >
                  {n}
                  <button
                    type="button"
                    onClick={() => store.removeVantagem(n)}
                    className="text-red-600 hover:underline"
                  >
                    ✕
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Desvantagens (raça + escolhidas) */}
          <div>
            <h2 className="mb-1 text-sm font-bold uppercase text-stone-700">
              Desvantagens
            </h2>
            <p className="mb-1 text-[10px] text-stone-500">
              Fraquezas que dão pontos extras para gastar. Da raça (automáticas) + escolhidas. Clique em cada item no modal para ver o efeito.
            </p>
            <button
              type="button"
              onClick={() => setModalAberto("desvantagens")}
              className="w-full rounded border border-stone-300 bg-stone-50 py-2 text-sm hover:bg-amber-50"
            >
              + Adicionar desvantagem
            </button>
            <ul className="mt-2 space-y-1">
              {pacoteRacial.desvantagens.map((n) => (
                <li
                  key={`raca-${n}`}
                  className="flex items-center justify-between rounded bg-stone-200 px-2 py-1 text-sm"
                >
                  <span>
                    {n}
                    <span className="ml-1.5 rounded bg-stone-300 px-1 text-[10px] text-stone-700">
                      raça
                    </span>
                  </span>
                </li>
              ))}
              {store.desvantagens.map((n) => (
                <li
                  key={n}
                  className="flex items-center justify-between rounded bg-stone-100 px-2 py-1 text-sm"
                >
                  {n}
                  <button
                    type="button"
                    onClick={() => store.removeDesvantagem(n)}
                    className="text-red-600 hover:underline"
                  >
                    ✕
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* História */}
          <div>
            <label className="block text-xs font-medium text-stone-600">
              História
            </label>
            <textarea
              value={store.historia}
              onChange={(e) => store.setCampo("historia", e.target.value)}
              className="mt-1 w-full rounded border border-stone-300 px-3 py-2 text-sm"
              rows={4}
            />
          </div>
        </div>

        {/* Coluna direita */}
        <div className="space-y-6 rounded-xl border-2 border-stone-300 bg-white p-4 shadow-sm">
          {/* Tipos de Dano (seleção, sem texto livre) */}
          <div className="grid gap-2 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-medium text-stone-600">
                Força (tipo de dano)
              </label>
              <p className="text-[10px] text-stone-500 mb-0.5">
                Tipo de dano dos ataques corpo a corpo (corte, impacto, perfuração).
              </p>
              <select
                value={(TIPOS_DANO_FORCA as readonly string[]).includes(store.tiposDano.Força) ? store.tiposDano.Força : ""}
                onChange={(e) =>
                  store.setCampo("tiposDano", {
                    ...store.tiposDano,
                    Força: e.target.value,
                  })
                }
                className="mt-1 w-full rounded border border-stone-300 px-2 py-1.5 text-sm"
              >
                {TIPOS_DANO_FORCA.map((op) => (
                  <option key={op || "vazio"} value={op}>
                    {op || "— escolher —"}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-stone-600">
                Poder de Fogo (tipo de dano)
              </label>
              <p className="text-[10px] text-stone-500 mb-0.5">
                Tipo de dano dos ataques à distância (flechas, raios, magias).
              </p>
              <select
                value={(TIPOS_DANO_PDF as readonly string[]).includes(store.tiposDano["Poder de Fogo"]) ? store.tiposDano["Poder de Fogo"] : ""}
                onChange={(e) =>
                  store.setCampo("tiposDano", {
                    ...store.tiposDano,
                    "Poder de Fogo": e.target.value,
                  })
                }
                className="mt-1 w-full rounded border border-stone-300 px-2 py-1.5 text-sm"
              >
                {TIPOS_DANO_PDF.map((op) => (
                  <option key={op || "vazio"} value={op}>
                    {op || "— escolher —"}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Caminhos da Magia */}
          <div>
            <h2 className="mb-2 text-sm font-bold uppercase text-stone-700">
              Caminhos da Magia (Focus máx {maxCarac})
            </h2>
            <p className="mb-2 text-[10px] text-stone-500">
              Focus em cada caminho (1 pt cada). Define quais magias você pode aprender.
            </p>
            <div className="grid gap-2 sm:grid-cols-2">
              {CAMINHOS_MAGIA.map((c) => (
                <CaracCirculos
                  key={c}
                  label={c}
                  valor={store.caminhosMagia[c as CaminhoMagia]}
                  onChange={(v) =>
                    store.setCaminhoMagia(c as CaminhoMagia, v)
                  }
                  max={maxCarac}
                  descricao={CAMINHOS_DESCRICOES[c] ?? ""}
                />
              ))}
            </div>
          </div>

          {/* Magias Conhecidas */}
          <div>
            <h2 className="mb-1 text-sm font-bold uppercase text-stone-700">
              Magias Conhecidas
            </h2>
            <p className="mb-1 text-[10px] text-stone-500">
              Magias que o personagem pode lançar (gastam PM). Exigem Focus nos Caminhos. Cada magia custa 1 ponto.
            </p>
            <button
              type="button"
              onClick={() => setModalAberto("magias")}
              className="w-full rounded border border-stone-300 bg-stone-50 py-2 text-sm hover:bg-amber-50"
            >
              + Adicionar magia
            </button>
            <ul className="mt-2 max-h-40 space-y-1 overflow-y-auto">
              {store.magiasConhecidas.map((n) => (
                <li
                  key={n}
                  className="flex items-center justify-between rounded bg-amber-50 px-2 py-1 text-sm"
                >
                  {n}
                  <button
                    type="button"
                    onClick={() => store.removeMagia(n)}
                    className="text-red-600 hover:underline"
                  >
                    ✕
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Dinheiro */}
          <div>
            <label className="block text-xs font-medium text-stone-600">
              Dinheiro
            </label>
            <input
              type="text"
              value={store.dinheiro}
              onChange={(e) => store.setDinheiro(e.target.value)}
              placeholder="Ex.: 1dx100 Moedas"
              className="mt-1 w-full rounded border border-stone-300 px-3 py-2 text-sm"
            />
          </div>

          {/* Itens por tipo (seleção do sistema — não digita) */}
          <div>
            <h2 className="mb-2 text-sm font-bold uppercase text-stone-700">
              Itens (por tipo)
            </h2>
            <p className="mb-2 text-[10px] text-stone-500">
              Selecione itens da lista do sistema.
            </p>
            {store.itensPorTipo.map((grupo) => (
              <div
                key={grupo.tipo}
                className="mb-3 rounded-lg border border-stone-200 bg-stone-50/50 p-2"
              >
                <div className="mb-1.5 flex items-center justify-between">
                  <span className="text-xs font-semibold text-stone-700">
                    {grupo.tipo}
                  </span>
                  <button
                    type="button"
                    onClick={() => setModalItensTipo(grupo.tipo)}
                    className="rounded border border-stone-300 px-2 py-1 text-[11px] text-stone-600 hover:bg-amber-50"
                  >
                    + Adicionar
                  </button>
                </div>
                <ul className="space-y-1">
                  {grupo.itens.length === 0 ? (
                    <li className="text-[11px] italic text-stone-400">
                      Nenhum item
                    </li>
                  ) : (
                    grupo.itens.map((item) => (
                      <li
                        key={item}
                        className="flex items-center justify-between rounded bg-white px-2 py-1 text-sm"
                      >
                        {item}
                        <button
                          type="button"
                          onClick={() => store.removeItem(grupo.tipo, item)}
                          className="text-red-600 hover:underline"
                        >
                          ✕
                        </button>
                      </li>
                    ))
                  )}
                </ul>
              </div>
            ))}
          </div>

          {/* Experiência */}
          <div>
            <label className="block text-xs font-medium text-stone-600">
              Experiência
            </label>
            <input
              type="number"
              min={0}
              value={store.experiencia}
              onChange={(e) =>
                store.setCampo("experiencia", parseInt(e.target.value, 10) || 0)
              }
              className="mt-1 w-24 rounded border border-stone-300 px-2 py-1"
            />
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={handleSalvar}
          disabled={ptsDisponiveis < 0}
          title={ptsDisponiveis < 0 ? "Remova características, vantagens ou caminhos até ter 0 ou mais pontos." : undefined}
          className={`rounded-lg px-6 py-2 font-medium text-white ${
            ptsDisponiveis < 0
              ? "cursor-not-allowed bg-stone-400"
              : "bg-amber-500 hover:bg-amber-600"
          }`}
        >
          Salvar personagem
        </button>
        <button
          type="button"
          onClick={handleNovoPersonagem}
          className="rounded border border-stone-400 px-4 py-2 text-sm text-stone-600 hover:bg-stone-200"
        >
          Novo personagem
        </button>
        <Link
          to="/"
          className="rounded border border-stone-400 px-4 py-2 text-sm text-stone-600 hover:bg-stone-200"
        >
          Voltar
        </Link>
      </div>

      {/* Modais */}
      {modalAberto === "vantagens" && (
        <ModalLista
          titulo="Vantagens"
          itens={itensVantagens.filter(
            (i) => !pacoteRacial.vantagens.includes(i.nome)
          )}
          selecionados={store.vantagens}
          onSelecionar={store.addVantagem}
          onRemover={store.removeVantagem}
          onFechar={() => setModalAberto(null)}
          parseCusto={parseCusto}
          pontosDisponiveis={ptsDisponiveis}
          nomesDisponiveis={nomesVantagensDisponiveis}
        />
      )}
      {modalAberto === "desvantagens" && (
        <ModalLista
          titulo="Desvantagens"
          itens={itensDesvantagens.filter(
            (i) => !pacoteRacial.desvantagens.includes(i.nome)
          )}
          selecionados={store.desvantagens}
          onSelecionar={store.addDesvantagem}
          onRemover={store.removeDesvantagem}
          onFechar={() => setModalAberto(null)}
          parseCusto={(c) => Math.abs(parseCusto(c))}
          pontosDisponiveis={999}
          nomesDisponiveis={nomesDesvantagensDisponiveis}
        />
      )}
      {modalAberto === "magias" && (
        <ModalLista
          titulo="Magias Conhecidas"
          itens={itensMagias}
          selecionados={store.magiasConhecidas}
          onSelecionar={store.addMagia}
          onRemover={store.removeMagia}
          onFechar={() => setModalAberto(null)}
          parseCusto={parseCusto}
          pontosDisponiveis={ptsDisponiveis}
          nomesDisponiveis={nomesMagiasDisponiveis}
        />
      )}
      {modalItensTipo && (
        <ModalLista
          titulo={`Itens — ${modalItensTipo}`}
          itens={getItensPorTipo(modalItensTipo).map((i) => ({
            nome: i.nome,
            bonus: i.bonus,
            custo: i.custo,
            efeito: i.efeito,
            livro: i.livro,
          }))}
          selecionados={
            store.itensPorTipo.find((g) => g.tipo === modalItensTipo)?.itens ??
            []
          }
          onSelecionar={(nome) => store.addItem(modalItensTipo, nome)}
          onRemover={(nome) => store.removeItem(modalItensTipo, nome)}
          onFechar={() => setModalItensTipo(null)}
        />
      )}
      {modalAberto === "racas" && (
        <ModalLista
          titulo="Escolher raça — Pacote racial (vantagens e desvantagens incluídas no custo). Apenas uma por personagem."
          itens={racas.map((r) => ({
            nome: r.nome,
            custo: r.custo,
            efeito: r.efeito,
            livro: r.livro,
            unica: true,
          }))}
          selecionados={store.raca ? [store.raca] : []}
          onSelecionar={(n) => {
            store.setRaca(n);
            setModalAberto(null);
          }}
          onRemover={() => store.setRaca(null)}
          onFechar={() => setModalAberto(null)}
          multiSelect={false}
          parseCusto={parseCusto}
          pontosDisponiveis={ptsDisponiveis}
        />
      )}
      {modalAberto === "racaDetalhe" && store.raca && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
          onClick={(e) => e.target === e.currentTarget && setModalAberto(null)}
        >
          <div
            className="max-h-[90vh] w-full max-w-lg overflow-hidden rounded-xl bg-white shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-stone-200 px-4 py-3">
              <h2 className="text-lg font-bold text-stone-800">
                {store.raca} — Vantagens e Desvantagens
              </h2>
              <div className="flex gap-1">
                <button
                  type="button"
                  onClick={() => setModalAberto("racas")}
                  className="rounded px-2 py-1 text-sm text-amber-700 hover:bg-amber-100"
                >
                  Trocar raça
                </button>
                <button
                  type="button"
                  onClick={() => setModalAberto(null)}
                  className="rounded p-2 text-stone-500 hover:bg-stone-100"
                >
                  ✕
                </button>
              </div>
            </div>
            <div className="max-h-[70vh] space-y-4 overflow-y-auto p-4">
              {(() => {
                const racaItem = getRaca(store.raca);
                return (
                  <>
                    {racaItem?.efeito && (
                      <div>
                        <h3 className="mb-1 text-sm font-semibold text-stone-700">
                          Descrição
                        </h3>
                        <p className="text-sm text-stone-600 whitespace-pre-wrap">
                          {racaItem.efeito}
                        </p>
                        {racaItem.custo && (
                          <p className="mt-1 text-xs text-stone-500">
                            Custo: {racaItem.custo}
                          </p>
                        )}
                      </div>
                    )}
                    {pacoteRacial.vantagens.length > 0 && (
                      <div>
                        <h3 className="mb-1 text-sm font-semibold text-emerald-800">
                          Vantagens da raça
                        </h3>
                        <ul className="list-inside list-disc space-y-0.5 text-sm text-stone-600">
                          {pacoteRacial.vantagens.map((n) => (
                            <li key={n}>{n}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {pacoteRacial.desvantagens.length > 0 && (
                      <div>
                        <h3 className="mb-1 text-sm font-semibold text-amber-800">
                          Desvantagens da raça
                        </h3>
                        <ul className="list-inside list-disc space-y-0.5 text-sm text-stone-600">
                          {pacoteRacial.desvantagens.map((n) => (
                            <li key={n}>{n}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {pacoteRacial.efeitosEspeciais &&
                      pacoteRacial.efeitosEspeciais.length > 0 && (
                        <div>
                          <h3 className="mb-1 text-sm font-semibold text-stone-700">
                            Efeitos especiais
                          </h3>
                          <ul className="list-inside list-disc space-y-0.5 text-sm text-stone-600">
                            {pacoteRacial.efeitosEspeciais.map((e, i) => (
                              <li key={i}>{e}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    {Object.keys(pacoteRacial.modificadores).length > 0 && (
                      <div>
                        <h3 className="mb-1 text-sm font-semibold text-stone-700">
                          Modificadores
                        </h3>
                        <p className="text-sm text-stone-600">
                          {Object.entries(pacoteRacial.modificadores)
                            .map(([k, v]) => `${k}${v! >= 0 ? "+" : ""}${v}`)
                            .join(", ")}
                        </p>
                      </div>
                    )}
                  </>
                );
              })()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
