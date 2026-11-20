# Pika H3 Flex en DGX

[![Pika H3 Flex en DGX](guia/assets/banner-es.jpg)](https://inematds.github.io/pika-h3-flex/guia/es/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## Qué es

Un kit para ejecutar **Pika H3 Flex** en tu propia computadora, sin nube y sin pagar créditos. Flex es un modelo abierto de Pika que genera **video con sonido sincronizado** a partir de texto, en solo 6 pasos. No es un modelo completo: son adaptadores (LoRA) que se acoplan a MiniMax H3. Aquí está el procedimiento que funcionó en un **NVIDIA DGX Spark (GB10, 128 GB de memoria unificada)** con ComfyUI: qué descargar, cómo iniciarlo sin agotar la memoria y un script que genera varios clips de una vez.

## 📖 Guía de uso

Guía completa (landing + paso a paso): **https://inematds.github.io/pika-h3-flex/guia/es/**

## El proceso, de principio a fin

Quién lo hace: 🧠 sesión con Nei · ⚙️ script · 🤖 agente (`codex exec` / `claude -p`).

1. 🧠 **Comprobar si cabe.** Flex son 2 LoRA de ~2 GB sobre MiniMax H3. Si H3 ya funciona, Flex también.
2. 🤖 **Descargar los LoRA en formato ComfyUI** (lo hizo Astra de Codex, con el hash verificado):
   `hf download Pika-Labs/Pika-H3-Flex --include 'comfy/*' --local-dir pika-flex && (cd pika-flex/comfy && sha256sum -c SHA256SUMS)`
3. ⚙️ **Mover a `models/loras/`** de ComfyUI los dos archivos `pika_h3_flex_*_comfy_bf16.safetensors`.
4. ⚙️ **Iniciar ComfyUI con las opciones de memoria:** `./scripts/comfyui-start.sh` (ya incluye `--disable-dynamic-vram --disable-pinned-memory --cache-none`).
5. ⚙️ **Activar el monitor de memoria:** `./scripts/guarda.sh guarda.log 8 &`.
6. ⚙️ **Generar:** `python3 scripts/gera.py --arquivo exemplos/prompts.txt --largura 1344 --altura 768 --segundos 5`.
7. 🧠 **Revisar la imagen y el sonido**; ajustar el prompt y repetir.
8. ⚙️ **Apagar:** `systemctl --user stop comfyui-h3.scope`.

## Qué necesitas

- **Una GPU con ~60 GB libres** (el DGX Spark sirve; en una PC común, usa versiones cuantizadas más pequeñas).
- **ComfyUI** reciente, con los nodos nativos de MiniMax H3 (`MiniMaxH3ImageToVideo`, `ManualSigmas`, `SamplerCustomAdvanced`).
- **Modelos de MiniMax H3** en `models/`:

| Carpeta | Archivo | Tamaño |
|---|---|---|
| `diffusion_models/` | `minimax_h3_fl2va_pruned_fp8_scaled.safetensors` | 21 GB |
| `text_encoders/` | `qwen3vl_32b_minimax_h3_int8_convrot.safetensors` | 27 GB |
| `vae/` | `minimax_h3_video_vae_fp16.safetensors` + `minimax_h3_audio_vae_fp32.safetensors` | 5,8 GB |
| `loras/` | `pika_h3_flex_fl2va_comfy_bf16.safetensors` (+ `ref2va`) | 2 GB cada uno |

Los LoRA de Flex **no están en este repositorio**: descárgalos de Pika en Hugging Face (`Pika-Labs/Pika-H3-Flex`). Siguen la licencia comunitaria de MiniMax H3.

## Cómo genera Flex en 6 pasos

No basta con elegir «6 pasos» en cualquier sampler. Flex usa una programación propia que `gera.py` ya configura:

- **Sigmas manuales:** `1.0, 0.972973, 0.923077, 0.8, 0.571429, 0.333333, 0.0`
- **Sampler `lcm`** (ruido nuevo en cada paso), **LoRA con fuerza 1.0**, sin CFG.
- **Cuadros:** H3 necesita `17k + 5` (73 = 3 s, 124 = 5 s a 24 fps). `--segundos` calcula la cantidad.

## La trampa de la memoria (GB10)

En el DGX Spark, la GPU y la CPU **comparten la misma memoria**. Por eso:

- Sin las opciones `--disable-dynamic-vram --disable-pinned-memory --cache-none`, ComfyUI guardaba los pesos **dos veces** (RAM + GPU) y superó los 80 GB solo al cargar. Con ellas, quedó suficiente margen incluso con otro servicio de imágenes activo.
- **El límite de systemd (`MemoryMax`) no detecta la memoria de la GPU** en el GB10. En la primera prueba, el límite marcaba 41 GB y la máquina llegó a 0 GB libres. `guarda.sh` ayuda: revisa la memoria libre de la máquina y detiene ComfyUI antes de que se bloquee.
- **Ejecuta solo en la GPU.** En un lote de clips de 1344×768, al ejecutarlo junto con otros renders de video, la GPU se quedó sin memoria y el servidor se bloqueó. `guarda.sh` no evita este caso. Cierra los otros trabajos pesados de GPU y empieza con 832×480.

## Ejemplos

Todos se generaron en el DGX con `gera.py`:

| Clip | Tamaño | Tiempo |
|---|---|---|
| `exemplos/pescador-832x480.mp4` — pescador lanzando la red al amanecer | 832×480, 3 s | 341 s (con la carga de los modelos; los 6 pasos ≈ 30 s) |

Hay más prompts listos (gaucho en la pampa, robot humanoide, tormenta en la costa, estudio en casa) en `exemplos/prompts.txt`; todavía no se han generado aquí.

## Archivos

| Archivo | Para qué sirve |
|---|---|
| `scripts/gera.py` | texto → video + audio mediante ComfyUI (varios prompts en una llamada) |
| `scripts/comfyui-start.sh` | inicia ComfyUI con límite de memoria y las opciones del GB10 |
| `scripts/guarda.sh` | detiene ComfyUI si la memoria libre de la máquina baja demasiado |
| `workflows/pika_flex_*_ui.json` | workflows oficiales (t2v, fl2va, ref2va) con los nombres cambiados para los modelos anteriores: ábrelos en la interfaz de ComfyUI |
| `exemplos/` | prompts y videos generados |

## Límites

- La versión abierta genera hasta **768p**. El aumento de resolución a 1080p/2K/4K y la separación del audio en pistas solo están disponibles en el servicio pago de Pika.
- El prompt sigue el formato de los ejemplos oficiales, en inglés: `integrated_multimodal_description:` (la escena) y `overall_soundscape:` (el sonido). No se han probado prompts en portugués.
- Probado el 09/11/2026 en un DGX Spark con ComfyUI 0.33.0.

---
**INEMA.CLUB** — https://inema.club