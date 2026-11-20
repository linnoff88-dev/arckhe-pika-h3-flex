# Pika H3 Flex no DGX

<div align="center">
  <img src="capa/logo.svg" alt="Arckhé AI" height="48" />
  <p><strong>Arckhé AI</strong></p>
</div>


[![Pika H3 Flex no DGX](guia/assets/banner.jpg)](https://inematds.github.io/pika-h3-flex/guia/)

**ðŸ‡§ðŸ‡· [PortuguÃªs](README.md) Â· ðŸ‡ºðŸ‡¸ [English](README.en.md) Â· ðŸ‡ªðŸ‡¸ [EspaÃ±ol](README.es.md)**

## O que Ã©

Um kit para rodar o **Pika H3 Flex** no seu prÃ³prio computador, sem nuvem e sem pagar crÃ©dito. O Flex Ã© um modelo aberto da Pika que gera **vÃ­deo com som sincronizado** a partir de texto, em sÃ³ 6 passos. Ele nÃ£o Ã© um modelo inteiro: sÃ£o adaptadores (LoRA) que encaixam no MiniMax H3. Aqui estÃ¡ a receita que funcionou num **NVIDIA DGX Spark (GB10, 128 GB de memÃ³ria unificada)**, com o ComfyUI: o que baixar, como subir sem estourar a memÃ³ria e um script que gera vÃ¡rios clipes de uma vez.

## ðŸ“– Guia de uso

Guia completo (landing + passo a passo): **https://inematds.github.io/pika-h3-flex/guia/**

## O processo, do inÃ­cio ao fim

Quem faz: ðŸ§  sessÃ£o com o Nei Â· âš™ï¸ script Â· ðŸ¤– agente (`codex exec` / `claude -p`).

1. ðŸ§  **Conferir se cabe.** O Flex sÃ£o 2 LoRAs de ~2 GB sobre o MiniMax H3. Se o H3 jÃ¡ roda, o Flex roda.
2. ðŸ¤– **Baixar os LoRAs no formato ComfyUI** (feito pelo Astra do Codex, com hash conferido):
   `hf download Pika-Labs/Pika-H3-Flex --include 'comfy/*' --local-dir pika-flex && (cd pika-flex/comfy && sha256sum -c SHA256SUMS)`
3. âš™ï¸ **Mover para `models/loras/`** do ComfyUI os dois arquivos `pika_h3_flex_*_comfy_bf16.safetensors`.
4. âš™ï¸ **Subir o ComfyUI com as opÃ§Ãµes de memÃ³ria:** `./scripts/comfyui-start.sh` (jÃ¡ passa `--disable-dynamic-vram --disable-pinned-memory --cache-none`).
5. âš™ï¸ **Ligar o guarda de memÃ³ria:** `./scripts/guarda.sh guarda.log 8 &`.
6. âš™ï¸ **Gerar:** `python3 scripts/gera.py --arquivo exemplos/prompts.txt --largura 1344 --altura 768 --segundos 5`.
7. ðŸ§  **Assistir e conferir** imagem e som; ajustar o prompt e repetir.
8. âš™ï¸ **Desligar:** `systemctl --user stop comfyui-h3.scope`.

## O que vocÃª precisa

- **Uma GPU com ~60 GB livres** (o DGX Spark serve; num PC comum, use versÃµes quantizadas menores).
- **ComfyUI** recente, com os nÃ³s nativos do MiniMax H3 (`MiniMaxH3ImageToVideo`, `ManualSigmas`, `SamplerCustomAdvanced`).
- **Modelos do MiniMax H3** em `models/`:

| Pasta | Arquivo | Tamanho |
|---|---|---|
| `diffusion_models/` | `minimax_h3_fl2va_pruned_fp8_scaled.safetensors` | 21 GB |
| `text_encoders/` | `qwen3vl_32b_minimax_h3_int8_convrot.safetensors` | 27 GB |
| `vae/` | `minimax_h3_video_vae_fp16.safetensors` + `minimax_h3_audio_vae_fp32.safetensors` | 5,8 GB |
| `loras/` | `pika_h3_flex_fl2va_comfy_bf16.safetensors` (+ `ref2va`) | 2 GB cada |

Os LoRAs do Flex **nÃ£o estÃ£o neste repositÃ³rio**: baixe da Pika no Hugging Face (`Pika-Labs/Pika-H3-Flex`). Eles seguem a licenÃ§a comunitÃ¡ria do MiniMax H3.

## Como o Flex gera em 6 passos

NÃ£o basta escolher "6 passos" num sampler qualquer. O Flex usa um agendamento prÃ³prio, que o `gera.py` jÃ¡ monta:

- **Sigmas manuais:** `1.0, 0.972973, 0.923077, 0.8, 0.571429, 0.333333, 0.0`
- **Sampler `lcm`** (ruÃ­do novo a cada passo), **LoRA com forÃ§a 1.0**, sem CFG.
- **Quadros:** o H3 quer `17k + 5` (73 = 3 s, 124 = 5 s a 24 fps). O `--segundos` faz a conta.

## A armadilha da memÃ³ria (GB10)

No DGX Spark a GPU e a CPU **dividem a mesma memÃ³ria**. Por isso:

- Sem as opÃ§Ãµes `--disable-dynamic-vram --disable-pinned-memory --cache-none`, o ComfyUI guardava os pesos **duas vezes** (RAM + GPU) e passou de 80 GB sÃ³ no carregamento. Com elas, sobrou folga mesmo com outro serviÃ§o de imagem ligado.
- **O teto do systemd (`MemoryMax`) nÃ£o enxerga a memÃ³ria da GPU** no GB10. No primeiro teste o teto marcava 41 GB e a mÃ¡quina chegou a 0 GB livre. O `guarda.sh` ajuda: olha a memÃ³ria livre da mÃ¡quina e derruba o ComfyUI antes do travamento.
- **Rode sozinho na GPU.** Num lote de clipes de 1344Ã—768, rodando junto com outros renders de vÃ­deo, o driver da GPU ficou sem memÃ³ria e o servidor travou. O `guarda.sh` nÃ£o segura esse caso. Feche os outros trabalhos pesados de GPU e comece por 832Ã—480.

## Exemplos

Todos gerados no DGX com o `gera.py`:

| Clipe | Tamanho | Tempo |
|---|---|---|
| `exemplos/pescador-832x480.mp4` â€” pescador jogando a rede ao amanhecer | 832Ã—480, 3 s | 341 s (com carga dos modelos; os 6 passos â‰ˆ 30 s) |

Mais prompts prontos (gaÃºcho no pampa, robÃ´ humanoide, temporal no litoral, estÃºdio em casa) estÃ£o em `exemplos/prompts.txt`, ainda nÃ£o gerados aqui.

## Arquivos

| Arquivo | Para quÃª |
|---|---|
| `scripts/gera.py` | texto â†’ vÃ­deo + Ã¡udio pelo ComfyUI (vÃ¡rios prompts numa chamada) |
| `scripts/comfyui-start.sh` | sobe o ComfyUI com teto de memÃ³ria e as opÃ§Ãµes do GB10 |
| `scripts/guarda.sh` | derruba o ComfyUI se a memÃ³ria livre da mÃ¡quina cair demais |
| `workflows/pika_flex_*_ui.json` | workflows oficiais (t2v, fl2va, ref2va) com os nomes trocados para os modelos acima â€” abra na tela do ComfyUI |
| `exemplos/` | prompts e vÃ­deos gerados |

## Limites

- A versÃ£o aberta gera atÃ© **768p**. Upscale para 1080p/2K/4K e separaÃ§Ã£o do Ã¡udio em faixas existem sÃ³ no serviÃ§o pago da Pika.
- O prompt segue o formato dos exemplos oficiais, em inglÃªs: `integrated_multimodal_description:` (a cena) e `overall_soundscape:` (o som). Prompt em portuguÃªs nÃ£o foi testado.
- Testado em 09/11/2026 no DGX Spark com ComfyUI 0.33.0.

---
**INEMA.CLUB** â€” https://inema.club

---

<div align="center">
  <img src="capa/logo.svg" alt="Arckhé AI" height="32" />
  <p><strong>Arckhé AI</strong></p>
</div>