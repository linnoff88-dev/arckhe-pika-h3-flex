ï»¿# Pika H3 Flex no DGX

<div align="center">
  <img src="capa/logo.svg" alt="Arckhé AI" height="48" />
  <p><strong>Arckhé AI</strong></p>
</div>


[![Pika H3 Flex no DGX](guia/assets/banner.jpg)](https://inematds.github.io/pika-h3-flex/guia/)

**ê°Å¸â¡Â§ê°Å¸â¡Â· [PortuguêÂªs](README.md) êÂ· ê°Å¸â¡Âºê°Å¸â¡Â¸ [English](README.en.md) êÂ· ê°Å¸â¡Âªê°Å¸â¡Â¸ [EspaêÂ±ol](README.es.md)**

## O que êÂ©

Um kit para rodar o **Pika H3 Flex** no seu prêÂ³prio computador, sem nuvem e sem pagar crêÂ©dito. O Flex êÂ© um modelo aberto da Pika que gera **vêÂ­deo com som sincronizado** a partir de texto, em sêÂ³ 6 passos. Ele nêÂ£o êÂ© um modelo inteiro: sêÂ£o adaptadores (LoRA) que encaixam no MiniMax H3. Aqui estêÂ¡ a receita que funcionou num **NVIDIA DGX Spark (GB10, 128 GB de memêÂ³ria unificada)**, com o ComfyUI: o que baixar, como subir sem estourar a memêÂ³ria e um script que gera vêÂ¡rios clipes de uma vez.

## ê°Å¸ââ Guia de uso

Guia completo (landing + passo a passo): **https://inematds.github.io/pika-h3-flex/guia/**

## O processo, do inêÂ­cio ao fim

Quem faz: ê°Å¸Â§Â  sessêÂ£o com o Nei êÂ· ê¢Å¡â¢ê¯Â¸Â script êÂ· ê°Å¸Â¤â agente (`codex exec` / `claude -p`).

1. ê°Å¸Â§Â  **Conferir se cabe.** O Flex sêÂ£o 2 LoRAs de ~2 GB sobre o MiniMax H3. Se o H3 jêÂ¡ roda, o Flex roda.
2. ê°Å¸Â¤â **Baixar os LoRAs no formato ComfyUI** (feito pelo Astra do Codex, com hash conferido):
   `hf download Pika-Labs/Pika-H3-Flex --include 'comfy/*' --local-dir pika-flex && (cd pika-flex/comfy && sha256sum -c SHA256SUMS)`
3. ê¢Å¡â¢ê¯Â¸Â **Mover para `models/loras/`** do ComfyUI os dois arquivos `pika_h3_flex_*_comfy_bf16.safetensors`.
4. ê¢Å¡â¢ê¯Â¸Â **Subir o ComfyUI com as opêÂ§êÂµes de memêÂ³ria:** `./scripts/comfyui-start.sh` (jêÂ¡ passa `--disable-dynamic-vram --disable-pinned-memory --cache-none`).
5. ê¢Å¡â¢ê¯Â¸Â **Ligar o guarda de memêÂ³ria:** `./scripts/guarda.sh guarda.log 8 &`.
6. ê¢Å¡â¢ê¯Â¸Â **Gerar:** `python3 scripts/gera.py --arquivo exemplos/prompts.txt --largura 1344 --altura 768 --segundos 5`.
7. ê°Å¸Â§Â  **Assistir e conferir** imagem e som; ajustar o prompt e repetir.
8. ê¢Å¡â¢ê¯Â¸Â **Desligar:** `systemctl --user stop comfyui-h3.scope`.

## O que vocêÂª precisa

- **Uma GPU com ~60 GB livres** (o DGX Spark serve; num PC comum, use versêÂµes quantizadas menores).
- **ComfyUI** recente, com os nêÂ³s nativos do MiniMax H3 (`MiniMaxH3ImageToVideo`, `ManualSigmas`, `SamplerCustomAdvanced`).
- **Modelos do MiniMax H3** em `models/`:

| Pasta | Arquivo | Tamanho |
|---|---|---|
| `diffusion_models/` | `minimax_h3_fl2va_pruned_fp8_scaled.safetensors` | 21 GB |
| `text_encoders/` | `qwen3vl_32b_minimax_h3_int8_convrot.safetensors` | 27 GB |
| `vae/` | `minimax_h3_video_vae_fp16.safetensors` + `minimax_h3_audio_vae_fp32.safetensors` | 5,8 GB |
| `loras/` | `pika_h3_flex_fl2va_comfy_bf16.safetensors` (+ `ref2va`) | 2 GB cada |

Os LoRAs do Flex **nêÂ£o estêÂ£o neste repositêÂ³rio**: baixe da Pika no Hugging Face (`Pika-Labs/Pika-H3-Flex`). Eles seguem a licenêÂ§a comunitêÂ¡ria do MiniMax H3.

## Como o Flex gera em 6 passos

NêÂ£o basta escolher "6 passos" num sampler qualquer. O Flex usa um agendamento prêÂ³prio, que o `gera.py` jêÂ¡ monta:

- **Sigmas manuais:** `1.0, 0.972973, 0.923077, 0.8, 0.571429, 0.333333, 0.0`
- **Sampler `lcm`** (ruêÂ­do novo a cada passo), **LoRA com forêÂ§a 1.0**, sem CFG.
- **Quadros:** o H3 quer `17k + 5` (73 = 3 s, 124 = 5 s a 24 fps). O `--segundos` faz a conta.

## A armadilha da memêÂ³ria (GB10)

No DGX Spark a GPU e a CPU **dividem a mesma memêÂ³ria**. Por isso:

- Sem as opêÂ§êÂµes `--disable-dynamic-vram --disable-pinned-memory --cache-none`, o ComfyUI guardava os pesos **duas vezes** (RAM + GPU) e passou de 80 GB sêÂ³ no carregamento. Com elas, sobrou folga mesmo com outro serviêÂ§o de imagem ligado.
- **O teto do systemd (`MemoryMax`) nêÂ£o enxerga a memêÂ³ria da GPU** no GB10. No primeiro teste o teto marcava 41 GB e a mêÂ¡quina chegou a 0 GB livre. O `guarda.sh` ajuda: olha a memêÂ³ria livre da mêÂ¡quina e derruba o ComfyUI antes do travamento.
- **Rode sozinho na GPU.** Num lote de clipes de 1344êâ768, rodando junto com outros renders de vêÂ­deo, o driver da GPU ficou sem memêÂ³ria e o servidor travou. O `guarda.sh` nêÂ£o segura esse caso. Feche os outros trabalhos pesados de GPU e comece por 832êâ480.

## Exemplos

Todos gerados no DGX com o `gera.py`:

| Clipe | Tamanho | Tempo |
|---|---|---|
| `exemplos/pescador-832x480.mp4` ê¢â¬â pescador jogando a rede ao amanhecer | 832êâ480, 3 s | 341 s (com carga dos modelos; os 6 passos ê¢â°Ë 30 s) |

Mais prompts prontos (gaêÂºcho no pampa, robêÂ´ humanoide, temporal no litoral, estêÂºdio em casa) estêÂ£o em `exemplos/prompts.txt`, ainda nêÂ£o gerados aqui.

## Arquivos

| Arquivo | Para quêÂª |
|---|---|
| `scripts/gera.py` | texto ê¢â â vêÂ­deo + êÂ¡udio pelo ComfyUI (vêÂ¡rios prompts numa chamada) |
| `scripts/comfyui-start.sh` | sobe o ComfyUI com teto de memêÂ³ria e as opêÂ§êÂµes do GB10 |
| `scripts/guarda.sh` | derruba o ComfyUI se a memêÂ³ria livre da mêÂ¡quina cair demais |
| `workflows/pika_flex_*_ui.json` | workflows oficiais (t2v, fl2va, ref2va) com os nomes trocados para os modelos acima ê¢â¬â abra na tela do ComfyUI |
| `exemplos/` | prompts e vêÂ­deos gerados |

## Limites

- A versêÂ£o aberta gera atêÂ© **768p**. Upscale para 1080p/2K/4K e separaêÂ§êÂ£o do êÂ¡udio em faixas existem sêÂ³ no serviêÂ§o pago da Pika.
- O prompt segue o formato dos exemplos oficiais, em inglêÂªs: `integrated_multimodal_description:` (a cena) e `overall_soundscape:` (o som). Prompt em portuguêÂªs nêÂ£o foi testado.
- Testado em 09/11/2026 no DGX Spark com ComfyUI 0.33.0.

---
**INEMA.CLUB** ê¢â¬â https://inema.club

---

<div align="center">
  <img src="capa/logo.svg" alt="Arckhé AI" height="32" />
  <p><strong>Arckhé AI</strong></p>
</div>