import { FormEvent, useMemo, useState } from "react";

type ChatRole = "user" | "assistant";

interface ChatSource {
  title: string;
  source: string;
  kind: string;
}

interface ChatMessage {
  role: ChatRole;
  content: string;
  sources?: ChatSource[];
}

interface ChatApiResponse {
  answer: string;
  sources: ChatSource[];
}

export function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Pergunte sobre monstros, vantagens, desvantagens, magias e itens do sistema 3D&T. No deploy do Vercel eu respondo usando a base publicada junto com o app.",
    },
  ]);
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = useMemo(() => prompt.trim().length > 2 && !loading, [prompt, loading]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const question = prompt.trim();
    if (!question || loading) return;

    const nextMessages: ChatMessage[] = [...messages, { role: "user", content: question }];
    setMessages(nextMessages);
    setPrompt("");
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: nextMessages,
        }),
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Falha ao consultar o chat.");
      }

      const data = (await response.json()) as ChatApiResponse;
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: data.answer,
          sources: data.sources,
        },
      ]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Falha ao consultar o chat.";
      setError(message);
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content:
            "Não consegui responder agora. Verifique se a função `/api/chat` está publicada no Vercel e se a chave da OpenAI foi configurada.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-4">
      <div className="rounded-xl border-2 border-stone-300 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-bold text-stone-800">Assistente 3D&T</h1>
        <p className="mt-2 text-sm text-stone-600">
          Chat disponível no mesmo deploy do Vercel. As respostas são ancoradas nos dados publicados
          junto com o app e exibem as fontes usadas.
        </p>
      </div>

      <div className="rounded-xl border-2 border-stone-300 bg-white p-4 shadow-sm">
        <div className="flex max-h-[60vh] min-h-[360px] flex-col gap-3 overflow-y-auto">
          {messages.map((message, index) => (
            <div
              key={`${message.role}-${index}`}
              className={`max-w-[92%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                message.role === "user"
                  ? "ml-auto bg-amber-500 text-white"
                  : "bg-stone-100 text-stone-800"
              }`}
            >
              <p className="whitespace-pre-wrap">{message.content}</p>
              {message.sources && message.sources.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {message.sources.map((source, sourceIndex) => (
                    <span
                      key={`${source.title}-${sourceIndex}`}
                      className="rounded-full bg-stone-200 px-2 py-1 text-[11px] text-stone-700"
                    >
                      {source.kind}: {source.title} · {source.source}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className="max-w-[92%] rounded-2xl bg-stone-100 px-4 py-3 text-sm text-stone-600">
              Consultando a base publicada...
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="mt-4 flex flex-col gap-3">
          <textarea
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            rows={4}
            placeholder="Ex.: O que faz a vantagem Área de Batalha? Quais são os dados do Dragão do Ar?"
            className="w-full rounded-xl border border-stone-300 bg-stone-50 px-4 py-3 text-sm text-stone-800 outline-none ring-0 placeholder:text-stone-400 focus:border-amber-500"
          />
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs text-stone-500">
              Dica: perguntas com nome exato de magia, monstro ou vantagem tendem a trazer respostas
              melhores.
            </p>
            <button
              type="submit"
              disabled={!canSubmit}
              className={`rounded-lg px-4 py-2 text-sm font-semibold ${
                canSubmit
                  ? "bg-amber-500 text-white hover:bg-amber-600"
                  : "cursor-not-allowed bg-stone-200 text-stone-500"
              }`}
            >
              Enviar
            </button>
          </div>
          {error && <p className="text-xs text-red-600">{error}</p>}
        </form>
      </div>
    </div>
  );
}
