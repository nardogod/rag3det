import { demoKnowledgeBase, type KnowledgeEntry } from "./demoKnowledge";

type ChatRole = "user" | "assistant";
type ChatLanguage = "pt" | "en";

interface ChatMessage {
  role: ChatRole;
  content: string;
}

interface ChatRequestBody {
  messages?: ChatMessage[];
  language?: ChatLanguage;
}

const OPENAI_API_URL = "https://api.openai.com/v1/chat/completions";

function normalize(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function uniqueTokens(text: string): string[] {
  return [...new Set(normalize(text).split(" ").filter((token) => token.length >= 2))];
}

function scoreEntry(entry: KnowledgeEntry, query: string): number {
  const normalizedQuery = normalize(query);
  const normalizedTitle = normalize(entry.title);
  const normalizedContent = normalize(entry.content);
  const tokens = uniqueTokens(query);

  let score = 0;

  if (normalizedTitle === normalizedQuery) score += 300;
  if (normalizedTitle.includes(normalizedQuery)) score += 180;
  if (normalizedContent.includes(normalizedQuery)) score += 80;

  for (const token of tokens) {
    if (normalizedTitle.includes(token)) score += 35;
    if (normalizedContent.includes(token)) score += 8;
  }

  return score;
}

async function retrieveContext(query: string): Promise<KnowledgeEntry[]> {
  return demoKnowledgeBase
    .map((entry) => ({ entry, score: scoreEntry(entry, query) }))
    .filter((item) => item.score > 0)
    .sort((left, right) => right.score - left.score)
    .slice(0, 6)
    .map((item) => item.entry);
}

function fallbackAnswer(query: string, context: KnowledgeEntry[], language: ChatLanguage): string {
  if (context.length === 0) {
    return language === "en"
      ? `I could not find enough data in the published knowledge base to answer "${query}". Try using the exact name of the spell, advantage, item, or monster.`
      : `Não encontrei dados suficientes na base publicada para responder sobre "${query}". Tente citar o nome exato da magia, vantagem, item ou monstro.`;
  }

  const lines = context.map(
    (item, index) =>
      `${index + 1}. ${item.kind.toUpperCase()} - ${item.title}: ${item.content.slice(0, 280)}`
  );

  return [
    language === "en"
      ? `I found ${context.length} relevant reference(s) for "${query}".`
      : `Encontrei ${context.length} referência(s) relevantes para "${query}".`,
    "",
    ...lines,
    "",
    language === "en"
      ? "This Vercel deployment is running in demo mode with a curated 3D&T knowledge sample."
      : "Este deploy do Vercel está rodando em modo de demonstração com uma base curada de exemplos de 3D&T.",
  ].join("\n");
}

async function generateAnswerWithOpenAI(
  query: string,
  context: KnowledgeEntry[],
  language: ChatLanguage
): Promise<string> {
  const apiKey = process.env.OPENAI_API_KEY;
  const model = process.env.OPENAI_MODEL_NAME || "gpt-4.1-mini";

  if (!apiKey) {
    return fallbackAnswer(query, context, language);
  }

  const contextText =
    context.length > 0
      ? context
          .map(
            (item, index) =>
              `[${index + 1}] ${item.kind.toUpperCase()} | ${item.title} | ${item.source}\n${item.content}`
          )
          .join("\n\n")
      : "Nenhuma fonte encontrada.";

  const response = await fetch(OPENAI_API_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model,
      temperature: 0.2,
      messages: [
        {
          role: "system",
          content:
            language === "en"
              ? "You are a 3D&T assistant. Answer in English, use only the provided sources, cite source names when possible, and clearly say when the published knowledge base does not contain enough information."
              : "Você é um assistente de 3D&T. Responda em português, use apenas as fontes fornecidas, cite os nomes das fontes quando possível e diga claramente quando a base publicada não contiver informação suficiente.",
        },
        {
          role: "user",
          content:
            language === "en"
              ? `Question: ${query}\n\nAvailable sources:\n${contextText}`
              : `Pergunta: ${query}\n\nFontes disponíveis:\n${contextText}`,
        },
      ],
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || "Falha ao consultar a OpenAI.");
  }

  const payload = (await response.json()) as {
    choices?: Array<{ message?: { content?: string } }>;
  };

  return payload.choices?.[0]?.message?.content?.trim() || fallbackAnswer(query, context, language);
}

export default async function handler(request: { method?: string; body?: unknown }, response: {
  status: (code: number) => { json: (payload: unknown) => void };
  json: (payload: unknown) => void;
  setHeader: (name: string, value: string) => void;
}) {
  response.setHeader("Content-Type", "application/json; charset=utf-8");

  if (request.method !== "POST") {
    response.status(405).json({ error: "Method not allowed" });
    return;
  }

  let body: ChatRequestBody;
  try {
    body =
      typeof request.body === "string"
        ? (JSON.parse(request.body) as ChatRequestBody)
        : ((request.body as ChatRequestBody) || {});
  } catch {
    response.status(400).json({ error: "Invalid request body." });
    return;
  }
  const messages = Array.isArray(body?.messages) ? body.messages : [];
  const language: ChatLanguage = body?.language === "en" ? "en" : "pt";
  const question = [...messages].reverse().find((message) => message.role === "user")?.content?.trim();

  if (!question) {
    response
      .status(400)
      .json({ error: language === "en" ? "Invalid question." : "Pergunta inválida." });
    return;
  }

  try {
    const context = await retrieveContext(question);
    const answer = await generateAnswerWithOpenAI(question, context, language);

    response.json({
      answer,
      sources: context.map((item) => ({
        title: item.title,
        source: item.source,
        kind: item.kind,
      })),
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Falha interna ao responder.";
    response.status(500).json({ error: message });
  }
}
