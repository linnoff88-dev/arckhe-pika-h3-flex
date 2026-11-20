# Pika H3 Flex on DGX

[![Pika H3 Flex on DGX](guia/assets/banner-en.jpg)](https://inematds.github.io/pika-h3-flex/guia/en/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## What it is

A kit for running **Pika H3 Flex** on your own computer, without the cloud or paying for credits. Flex is an open model from Pika that generates **video with synchronized sound** from text in just 6 steps. It is not a complete model: it consists of adapters (LoRAs) that plug into MiniMax H3. Here is the setup that worked on an **NVIDIA DGX Spark (GB10, 128 GB unified memory)** with ComfyUI: what to download, how to launch it without running out of memory, and a script that generates several clips at once.

## 📖 User guide

Complete guide (landing page + walkthrough): **https://inematds.github.io/pika-h3-flex/guia/en/**

## The process, start to finish

Who does what: 🧠 session with Nei · ⚙️ script · 🤖 agent (`codex exec` / `claude -p`).

1. 🧠 **Check that it fits.** Flex consists of 2 LoRAs of ~2 GB on top of MiniMax H3. If H3 runs, Flex runs.
2. 🤖 **Download the LoRAs in ComfyUI format** (done by Codex Astra, with the hash verified):
   `hf download Pika-Labs/Pika-H3-Flex --include 'comfy/*' --local-dir pika-flex && (cd pika-flex/comfy && sha256sum -c SHA256SUMS)`
3. ⚙️ **Move the two `pika_h3_flex_*_comfy_bf16.safetensors` files** to ComfyUI's `models/loras/` folder.
4. ⚙️ **Start ComfyUI with the memory options:** `./scripts/comfyui-start.sh` (already passes `--disable-dynamic-vram --disable-pinned-memory --cache-none`).
5. ⚙️ **Turn on the memory guard:** `./scripts/guarda.sh guarda.log 8 &`.
6. ⚙️ **Generate:** `python3 scripts/gera.py --arquivo exemplos/prompts.txt --largura 1344 --altura 768 --segundos 5`.
7. 🧠 **Watch and check** the image and sound; adjust the prompt and try again.
8. ⚙️ **Shut down:** `systemctl --user stop comfyui-h3.scope`.

## What you need

- **A GPU with ~60 GB free** (the DGX Spark works; on a regular PC, use smaller quantized versions).
- A recent **ComfyUI** version, with the native MiniMax H3 nodes (`MiniMaxH3ImageToVideo`, `ManualSigmas`, `SamplerCustomAdvanced`).
- **MiniMax H3 models** in `models/`:

| Folder | File | Size |
|---|---|---|
| `diffusion_models/` | `minimax_h3_fl2va_pruned_fp8_scaled.safetensors` | 21 GB |
| `text_encoders/` | `qwen3vl_32b_minimax_h3_int8_convrot.safetensors` | 27 GB |
| `vae/` | `minimax_h3_video_vae_fp16.safetensors` + `minimax_h3_audio_vae_fp32.safetensors` | 5,8 GB |
| `loras/` | `pika_h3_flex_fl2va_comfy_bf16.safetensors` (+ `ref2va`) | 2 GB each |

The Flex LoRAs **are not in this repository**: download them from Pika on Hugging Face (`Pika-Labs/Pika-H3-Flex`). They follow the MiniMax H3 community license.

## How Flex generates in 6 steps

You cannot just select “6 steps” in any sampler. Flex uses its own schedule, which `gera.py` already sets up:

- **Manual sigmas:** `1.0, 0.972973, 0.923077, 0.8, 0.571429, 0.333333, 0.0`
- **`lcm` sampler** (new noise at each step), **LoRA strength 1.0**, no CFG.
- **Frames:** H3 requires `17k + 5` (73 = 3 s, 124 = 5 s at 24 fps). `--segundos` calculates this for you.

## The memory trap (GB10)

On the DGX Spark, the GPU and CPU **share the same memory**. So:

- Without the `--disable-dynamic-vram --disable-pinned-memory --cache-none` options, ComfyUI kept the weights **twice** (RAM + GPU) and used over 80 GB just to load. With them, there was room to spare, even with another image service running.
- The systemd limit (`MemoryMax`) **cannot see GPU memory** on the GB10. In the first test, the limit showed 41 GB while the machine had reached 0 GB free. `guarda.sh` helps: it checks the machine's free memory and stops ComfyUI before the system freezes.
- **Run it alone on the GPU.** In a batch of 1344×768 clips running alongside other video renders, the GPU driver ran out of memory and the server froze. `guarda.sh` cannot prevent this. Close other GPU-heavy jobs and start at 832×480.

## Examples

All generated on the DGX with `gera.py`:

| Clip | Size | Time |
|---|---|---|
| `exemplos/pescador-832x480.mp4` — fisherman casting his net at dawn | 832×480, 3 s | 341 s (including model loading; the 6 steps take ≈ 30 s) |

More ready-to-use prompts (gaucho on the pampas, humanoid robot, coastal storm, home studio) are in `exemplos/prompts.txt`; they have not been generated here yet.

## Files

| File | Purpose |
|---|---|
| `scripts/gera.py` | text → video + audio through ComfyUI (multiple prompts in one call) |
| `scripts/comfyui-start.sh` | starts ComfyUI with a memory limit and GB10 options |
| `scripts/guarda.sh` | stops ComfyUI if the machine's free memory drops too low |
| `workflows/pika_flex_*_ui.json` | official workflows (t2v, fl2va, ref2va) with the model names changed to match the models above — open them in the ComfyUI interface |
| `exemplos/` | prompts and generated videos |

## Limitations

- The open version generates up to **768p**. Upscaling to 1080p/2K/4K and splitting audio into tracks are available only through Pika's paid service.
- Prompts follow the format of the official examples, in English: `integrated_multimodal_description:` (the scene) and `overall_soundscape:` (the sound). Prompts in Portuguese have not been tested.
- Tested on 11/09/2026 on the DGX Spark with ComfyUI 0.33.0.

---
**INEMA.CLUB** — https://inema.club