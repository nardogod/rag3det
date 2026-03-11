/**
 * Corrige erros OCR comuns em textos extraídos de PDFs/livros digitalizados.
 * Espelho de src/utils/normalizar_ocr.py
 */

export function normalizarOcr(texto: string): string {
  if (!texto || typeof texto !== "string") return texto;
  let t = texto;

  // Sequências específicas (ordem importa)
  t = t.replace(/\bcon1\b/gi, "com");
  t = t.replace(/con1([a-záéíóúâêôãõ])/gi, "com$1");
  t = t.replace(/\ben1\b/gi, "em");
  t = t.replace(/en1([a-záéíóúâêôãõ])/gi, "em$1");
  t = t.replace(/\bun1\b/gi, "um");
  t = t.replace(/un1([a-záéíóúâêôãõ])/gi, "um$1");
  t = t.replace(/\btên1\b/gi, "têm");
  t = t.replace(/\btcn1\b/gi, "tem");
  t = t.replace(/con1eçar/gi, "começar");
  t = t.replace(/Radar-\s*1nas/gi, "Radar. Mas");
  t = t.replace(/1nas\b/gi, "Mas");
  t = t.replace(/inaiores/gi, "maiores");
  t = t.replace(/n1ais\b/gi, "mais");
  t = t.replace(/fo1tes\b/gi, "fortes");
  t = t.replace(/n1estres\b/gi, "mestres");
  t = t.replace(/fican1\b/gi, "ficam");
  t = t.replace(/can1uflagen1/gi, "camuflagem");
  t = t.replace(/camuflagern\b/gi, "camuflagem");
  t = t.replace(/c:anuflage1n/gi, "camuflagem");
  t = t.replace(/folhagen1\b/gi, "folhagem");
  t = t.replace(/alén1\b/gi, "além");
  t = t.replace(/notmal\b/gi, "normal");
  t = t.replace(/percebída/gi, "percebida");
  t = t.replace(/1\\rn1adura/gi, "Armadura");
  t = t.replace(/1\s*\\\s*r\s*n1adura/gi, "Armadura");
  t = t.replace(/\\\s*ler\s+o\s+Invisível/gi, "ou Ler o Invisível");
  t = t.replace(/\\\s*1er\s+o\s+Invisível/gi, "ou Ler o Invisível");
  t = t.replace(/\b1er\b/gi, "ler");
  t = t.replace(/\bl\s+ima\s+/gi, "Uma ");
  t = t.replace(/c:an1uflage1n/gi, "camuflagem");
  t = t.replace(/folha-\s*gem\b/gi, "folhagem");
  t = t.replace(/prefe-\s*rindo/gi, "preferindo");
  t = t.replace(/[~:]+fordida\b/gi, "Mordida");
  t = t.replace(/P\.'?\s*s\b/gi, "PVs");
  t = t.replace(/Teste\s+de\s+H\s*\.+\s*esistência/gi, "Teste de Resistência");
  t = t.replace(/H\s*\.+\s*esistência/gi, "Resistência");
  t = t.replace(/J[\s\\]+aques/gi, "Ataques");
  t = t.replace(/t[\s\\]+ndre\.?v/gi, "Andrew");
  t = t.replace(/t[\s\\]+dre\.?v/gi, "Andrew");
  t = t.replace(/c:c\)N?/gi, "CON");
  t = t.replace(/CONN\b/gi, "CON");
  t = t.replace(/C:1'\\?R/gi, "CAR");
  t = t.replace(/C:AR\b/gi, "CAR");
  t = t.replace(/\\X!IJL/gi, "WILL");
  t = t.replace(/X!IJL/gi, "WILL");
  t = t.replace(/J[\s\\]+taques/gi, "Ataques");
  t = t.replace(/P\\.'?\s*s\b/gi, "PVs");  // P\.' s (backslash-dot) → PVs
  t = t.replace(/i\s*\\?\s*\(\s*;\s*I/gi, "CON");
  t = t.replace(/i\s*\\\s*\(\s*;\s*\]/gi, "CON");
  t = t.replace(/t\\ndre\\.v/gi, "Andrew");
  t = t.replace(/t[\s\\]+ndre\\.v/gi, "Andrew");
  t = t.replace(/\bet1\s+sei\b/gi, "que sei");
  t = t.replace(/aqtti\b/gi, "aqui");
  t = t.replace(/assi111\b/gi, "assim");
  t = t.replace(/\bolbe\b/gi, "olhe");
  t = t.replace(/ntesv10\b/gi, "nentes");
  t = t.replace(/Nlas\b/gi, "Mas");
  t = t.replace(/\bten1\b/gi, "têm");
  t = t.replace(/plumagen1\b/gi, "plumagem");
  t = t.replace(/totalrnente\b/gi, "totalmente");
  t = t.replace(/ne-\s*é,tra\b/gi, "negra");
  t = t.replace(/n1uito\b/gi, "muito");
  t = t.replace(/con10\b/gi, "como");
  t = t.replace(/co1npetições/gi, "competições");
  t = t.replace(/Porén1\b/gi, "Porém");
  t = t.replace(/tornan1-se/gi, "tornam-se");
  t = t.replace(/companheixas\b/gi, "companheiras");
  t = t.replace(/J\\?\s*sa-Negra/gi, "Asa-Negra");
  t = t.replace(/\bxton\b/gi, "Arton");
  t = t.replace(/J\\raques/gi, "Ataques");
  t = t.replace(/i\.sfixia/gi, "Asfixia");
  t = t.replace(/fóle\.?:?go\b/gi, "fôlego");
  t = t.replace(/I<\.?\s*atabrok/gi, "Katabrok");
  // Carniceiros, Carrasco de Lena e similares
  t = t.replace(/\(arniceiros/gi, "Carniceiros");
  t = t.replace(/\bgue\s+os\b/gi, "que os");
  t = t.replace(/abu-\s*tres\b/gi, "abutres");
  t = t.replace(/tambétn\b/gi, "também");
  t = t.replace(/c:omo\b/gi, "como");
  t = t.replace(/alinentam-se/gi, "alimentam-se");
  t = t.replace(/n1orros\b/gi, "mortos");
  t = t.replace(/\/\\.+?\s*grande/gi, "A grande");  // /\.. grande → A grande
  t = t.replace(/enconu·ados/gi, "encontrados");
  t = t.replace(/poden1\b/gi, "podem");
  t = t.replace(/mesrna\b/gi, "mesma");
  t = t.replace(/Yítina\b/gi, "vítima");
  t = t.replace(/mo\.rtos/gi, "mortos");
  t = t.replace(/ura de l\\:?Iedo/gi, "aura de Medo");
  t = t.replace(/L\\.íagias/gi, "Magias");
  t = t.replace(/\.lé1n\b/gi, "Além");
  t = t.replace(/conseguen1\b/gi, "conseguem");
  t = t.replace(/n1ortos-vivos/gi, "mortos-vivos");
  t = t.replace(/n1esmo\b/gi, "mesmo");
  t = t.replace(/l\\íagia\b/gi, "Magia");
  t = t.replace(/arnas\s+n1ágicas/gi, "armas mágicas");
  t = t.replace(/possan1\b/gi, "possam");
  t = t.replace(/escassear·esse/gi, "escassear esse");
  t = t.replace(/atacan1\b/gi, "atacam");
  t = t.replace(/rananho\b/gi, "tamanho");
  t = t.replace(/111011stro\b/gi, "monstro");
  t = t.replace(/\.GI\b/gi, " AGI");
  t = t.replace(/#tagues\b/gi, "#Ataques");
  t = t.replace(/\(\]ucotada/gi, "Coçada");
  t = t.replace(/Gi\\l'\\JHE\b/gi, "GANHE");
  t = t.replace(/Cl\s*:RA\s*R\b/gi, "cravá");
  // Avatares e similares (Guia Arton)
  t = t.replace(/i\\taque\b/gi, "Ataque");
  t = t.replace(/\\lorpal\b/gi, "Mortal");
  t = t.replace(/\bforna\b/gi, "forma");
  t = t.replace(/n1undo\b/gi, "mundo");
  t = t.replace(/n1enores\b/gi, "menores");
  t = t.replace(/J\\\s*aparência/gi, "A aparência");
  t = t.replace(/co-\s*mun1\b/gi, "comum");
  t = t.replace(/n1eios\b/gi, "meios");
  t = t.replace(/\brneios\b/gi, "meios");
  t = t.replace(/\bn1enos\b/gi, "menos");
  t = t.replace(/assin1\b/gi, "assim");
  t = t.replace(/vatt'lres\b/gi, "Avatares");
  t = t.replace(/\bsào\b/gi, "são");
  t = t.replace(/\blnortal\b/gi, "Imortal");
  t = t.replace(/\bln1ortal\b/gi, "Imortal");
  t = t.replace(/Canúnhos\b/gi, "Caminhos");
  t = t.replace(/Cru11inhos\b/gi, "Caminhos");
  t = t.replace(/consonem\b/gi, "consomem");
  t = t.replace(/conson1em\b/gi, "consomem");
  t = t.replace(/n1ágicos\b/gi, "mágicos");
  t = t.replace(/\butna\b/gi, "uma");
  t = t.replace(/\b1nais\b/gi, "mais");
  t = t.replace(/\bu1n\b/gi, "um");
  t = t.replace(/í111une\b/gi, "imune");
  t = t.replace(/\barnas\b/gi, "armas");
  // Magia (variantes OCR)
  t = t.replace(/l\\iagia/gi, "Magia");
  t = t.replace(/I\\Jagia/gi, "Magia");
  t = t.replace(/psiquisn10\b/gi, "psiquismo");
  t = t.replace(/^cial\s/, "Especial ");

  // Padrões genéricos
  t = t.replace(/1\s*\\\s*/g, "");
  t = t.replace(/~/g, "");
  t = t.replace(/con1prar/gi, "comprar");
  t = t.replace(/perden1|perdem1/gi, "perdem");
  t = t.replace(/nunc:a|nunca\s*:/gi, "nunca");
  t = t.replace(/catacu1nbas/gi, "catacumbas");
  t = t.replace(/([a-záéíóúâêôãõ])n1([a-záéíóúâêôãõ])/gi, "$1n$2");
  t = t.replace(/fo1([a-záéíóúâêôãõ]{2,})/gi, "for$1");

  return t;
}
