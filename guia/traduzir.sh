#!/usr/bin/env bash
# Traduz o corpo do guia e o README para EN e ES pelo tradutor central (inema-traduz, assinatura).
# Uso: bash guia/traduzir.sh   (na raiz do repo) · log em /tmp/claude-1000/pika-traduz-*.log
set -u
cd "$(dirname "$0")/.."
export PATH="$HOME/.npm-global/bin:$HOME/.local/bin:$PATH"
T=$HOME/projetos/wifi/scripts/inema-traduz
L=/tmp/claude-1000; mkdir -p $L
REGRA_HTML='Responda SÓ com o HTML traduzido, sem cercas de código e sem comentário. Preserve EXATAMENTE: estrutura, tags, classes, ids, âncoras (#...), URLs, comandos dentro de <pre>, flags (--...), nomes de arquivo, números, nomes próprios (Pika, MiniMax H3, ComfyUI, DGX Spark, GB10, Qwen3-VL, INEMA.CLUB, PRO) e o marcador <!--EXEMPLOS-->. Traduza só o texto visível, alt, aria-label e title; os comentários <span class="c"> dentro de <pre> também. Ajustes obrigatórios: troque o conteúdo do <span class="lang"> por LANGSEL; todo src="assets/ vira src="../assets/; banner.jpg vira BANNER e banner-grade.jpg vira GRADE.'
REGRA_MD='Responda SÓ com o Markdown traduzido, sem cercas extras em volta e sem comentário. Preserve comandos, blocos de código, nomes de arquivo, URLs, tabelas e nomes próprios.'

html(){ # html <idioma> <LANGSEL> <sufixo>
  { printf 'Traduza para %s. %s\nLANGSEL = %s\nBANNER = banner-%s.jpg · GRADE = banner-grade-%s.jpg\n\n' "$1" "$REGRA_HTML" "$2" "$3" "$3"; cat guia/corpo.pt.html; } \
    | $T -o guia/corpo.$3.html > $L/pika-traduz-html-$3.log 2>&1
}
md(){ # md <idioma> <titulo-secao> <sufixo>
  { printf 'Traduza para %s. %s Título da seção "## O que é" vira "%s". O link do guia vira https://inematds.github.io/pika-h3-flex/guia/%s/ e o banner vira guia/assets/banner-%s.jpg.\n\n' "$1" "$REGRA_MD" "$2" "$3" "$3"; cat README.md; } \
    | $T -o README.$3.md > $L/pika-traduz-md-$3.log 2>&1
}
html "INGLÊS (EUA)" '<a href="../">PT</a><a class="on" href="./">EN</a><a href="../es/">ES</a>' en &
html "ESPANHOL (América Latina)" '<a href="../">PT</a><a href="../en/">EN</a><a class="on" href="./">ES</a>' es &
md "INGLÊS (EUA)" "## What it is" en &
md "ESPANHOL (América Latina)" "## Qué es" es &
wait
ls -la guia/corpo.*.html README.*.md
echo FIM_TRADUCAO
