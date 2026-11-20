#!/usr/bin/env python3
"""Monta guia/index.html (e en/, es/) a partir do template INEMA + corpo.<lang>.html + exemplos.

Uso: python3 guia/montar.py [pt|en|es ...]   (sem argumento: os que tiverem corpo)
"""
import html, json, os, re, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.expanduser("~/.claude/skills/projetos-landing-guia/assets/template.html")
SLUG = "pika-h3-flex"
META = {
    "pt": ("Pika H3 Flex no DGX", "vídeo com som em 6 passos, local",
           "Kit para rodar o Pika H3 Flex (vídeo com áudio, pesos abertos, 6 passos) no ComfyUI de um DGX Spark: download, memória unificada, gerador e exemplos."),
    "en": ("Pika H3 Flex on the DGX", "video with sound in 6 steps, local",
           "Kit to run Pika H3 Flex (video with audio, open weights, 6 steps) in ComfyUI on a DGX Spark: download, unified memory, generator and examples."),
    "es": ("Pika H3 Flex en el DGX", "video con sonido en 6 pasos, local",
           "Kit para correr Pika H3 Flex (video con audio, pesos abiertos, 6 pasos) en ComfyUI en un DGX Spark: descarga, memoria unificada, generador y ejemplos."),
}
SCRIPT = """
<script>
  (function(){
    var KEY='pika-h3-flex-theme';
    var b=document.body, t=document.getElementById('themeToggle');
    try{ if(localStorage.getItem(KEY)==='light'){ b.classList.add('light'); t.textContent='☀️'; } }catch(e){}
    t.addEventListener('click',function(){
      var light=b.classList.toggle('light');
      t.textContent=light?'☀️':'🌙';
      try{ localStorage.setItem(KEY, light?'light':'dark'); }catch(e){}
    });
  })();
</script>
</body>
</html>
"""
CSS_EXTRA = """  .ex video{width:100%;display:block;border-radius:12px;background:#000}
  code{font-family:'JetBrains Mono',monospace;font-size:.88em;color:var(--amb)}
</style>"""


def exemplos(lang, pre):
    itens = json.load(open(os.path.join(AQUI, "exemplos.json"), encoding="utf-8"))
    out = []
    for it in itens:
        leg = html.escape(it["legenda"][lang])
        out.append(f'    <figure><video src="{pre}assets/{it["video"]}" poster="{pre}assets/{it["poster"]}" '
                   f'controls loop playsinline preload="none"></video><figcaption>{leg}</figcaption></figure>')
    return "\n".join(out)


def monta(lang):
    corpo = open(os.path.join(AQUI, f"corpo.{lang}.html"), encoding="utf-8").read()
    t = open(TEMPLATE, encoding="utf-8").read()
    head = t[: t.index("<body>") + len("<body>")]
    proj, tag, desc = META[lang]
    head = (head.replace("{{PROJETO}}", proj).replace("{{TAGLINE}}", tag)
                .replace("{{META_DESCRICAO}}", desc).replace("{{SLUG}}", SLUG)
                .replace("</style>", CSS_EXTRA, 1))
    head = head.replace('<html lang="pt-BR">', {"pt": '<html lang="pt-BR">', "en": '<html lang="en">', "es": '<html lang="es">'}[lang])
    head = re.sub(r"<!-- TEMPLATE projetos-landing-guia.*?-->\n", "", head, flags=re.S)
    pre = "" if lang == "pt" else "../"
    corpo = corpo.replace("<!--EXEMPLOS-->", exemplos(lang, pre))
    destino = os.path.join(AQUI, "index.html" if lang == "pt" else f"{lang}/index.html")
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    open(destino, "w", encoding="utf-8").write(head + "\n\n" + corpo + SCRIPT)
    print("ok", destino)


if __name__ == "__main__":
    langs = sys.argv[1:] or [l for l in ("pt", "en", "es") if os.path.exists(os.path.join(AQUI, f"corpo.{l}.html"))]
    for l in langs:
        monta(l)
