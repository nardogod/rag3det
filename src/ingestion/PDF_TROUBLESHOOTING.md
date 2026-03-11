# Quando um PDF dá erro na ingestão

## Erro: "Unexpected end of stream" (PdfReadError)

**O que significa:** O pypdf encontrou um *stream* (bloco de dados) truncado ou malformado dentro do PDF — por exemplo, uma imagem embutida com dados incompletos ou um objeto que termina antes do esperado.

**Por que acontece:**
- PDF foi copiado/baixado de forma incompleta.
- Arquivo corrompido ou gerado por um programa que não seguiu o padrão à risca.
- PDF é uma "cópia" (ex.: "Cópia de ...") feita pelo sistema e algo falhou na cópia.
- O leitor (pypdf) é estrito: ao encontrar o primeiro problema, interrompe a leitura daquele arquivo.

**Como corrigir:**

1. **Instalar fallback opcional (recomendado)**  
   O código tenta primeiro com **pypdf** e, se falhar, usa **PyMuPDF** para o mesmo arquivo (se estiver instalado). PyMuPDF costuma ser mais tolerante a PDFs problemáticos.
   ```bash
   pip install pymupdf
   ```
   Depois rode de novo: `python scripts/build_index.py`. O PDF que falhou pode passar no fallback.

2. **Re-salvar o PDF**  
   Abra o arquivo em outro programa (Adobe Reader, navegador, “Imprimir → Salvar como PDF”) e salve de novo. Isso costuma “normalizar” o arquivo e eliminar streams truncados.

3. **Usar o original em vez da cópia**  
   Se o arquivo é “Cópia de …”, use o PDF original (sem ser cópia do sistema). Cópias feitas por alguns sistemas podem gerar arquivos quebrados.

4. **Deixar o arquivo de fora**  
   Se não for essencial, mova o PDF problemático para fora da pasta de ingestão; o restante será indexado normalmente.

---

**Resumo:** O projeto ignora PDFs que falham e segue com os demais. Para aumentar a chance de ler PDFs difíceis, instale `pymupdf` e rode o build de novo.
