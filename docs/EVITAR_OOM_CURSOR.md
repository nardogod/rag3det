# Evitar OOM (Out Of Memory) no Cursor IDE

## Análise do problema

O erro `The window terminated unexpectedly (reason: 'oom')` ocorre quando o Cursor IDE consome mais memória RAM do que o disponível. No projeto 3D&T Idle, os principais fatores são:

### Arquivos grandes carregados

| Arquivo | Tamanho | Uso |
|---------|---------|-----|
| `monstros.json` | **2,4 MB** | Bestiário |
| `itens_3dt.json` | 330 KB | Ficha de personagem |
| `habilidades_monstros.json` | 236 KB | Bestiário, Habilidades |
| `magias_3dt.json` | 286 KB | Ficha de personagem |
| `vantagens_turbinado.json` | 38 KB | Ficha de personagem |

**Total:** ~3,3 MB de JSON + bundle React (~3,4 MB) = carga pesada em memória.

---

## O que já foi implementado no projeto

1. **Lazy loading de rotas** – Bestiário, Ficha, Itens e Habilidades só carregam quando o usuário navega até eles. O `monstros.json` (2,4 MB) não é carregado na tela inicial.

2. **Code splitting (Vite)** – `manualChunks` separa o Bestiário e a Ficha em chunks distintos, reduzindo o bundle inicial.

3. **`.cursorignore`** – Pastas e arquivos grandes são ignorados na indexação do Cursor (node_modules, dist, JSONs grandes).

---

## Opções para evitar OOM

### 1. Configuração do Cursor (recomendado)

Aumentar o limite de memória do processo Node/Electron do Cursor:

**Windows:** Crie ou edite o atalho do Cursor e adicione ao final do caminho do executável:
```
--js-flags="--max-old-space-size=4096"
```

Ou defina a variável de ambiente antes de abrir o Cursor:
```powershell
$env:NODE_OPTIONS="--max-old-space-size=4096"
```

**Alternativa:** Em *File > Preferences > Settings*, procure por `max old space` ou configurações de memória do editor.

### 2. Fechar abas e janelas desnecessárias

- Feche abas de arquivos que não está usando.
- Evite ter vários projetos abertos ao mesmo tempo.
- Feche Spotify, navegadores pesados ou outras aplicações que consumam muita RAM.

### 3. Excluir pastas da indexação (Cursor)

O `.cursorignore` já foi criado. Se ainda houver problemas, adicione mais pastas:

```
data/
chroma_db/
*.chroma
```

### 4. Reduzir tamanho do `monstros.json` (futuro)

- Dividir por livro (ex.: um JSON por manual).
- Carregar monstros sob demanda via API em vez de import estático.
- Comprimir ou minificar o JSON (impacto menor).

### 5. Usar modo “Ask” em vez de “Agent” quando possível

O modo Agent mantém mais contexto em memória. Para perguntas simples, use o modo Ask.

---

## Verificação rápida

Após aplicar as mudanças:

1. Reinicie o Cursor.
2. Abra apenas este projeto.
3. Navegue para o Bestiário no app – o carregamento deve ser sob demanda.
4. Monitore o uso de RAM no Gerenciador de Tarefas (processo “Cursor”).

---

## Resumo

| Ação | Impacto |
|------|---------|
| `.cursorignore` criado | Reduz indexação de arquivos grandes |
| Lazy loading já ativo | monstros.json só carrega no Bestiário |
| Aumentar `max-old-space-size` | Aumenta margem de memória do Cursor |
| Fechar abas/outros apps | Libera RAM para o Cursor |
