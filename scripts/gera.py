#!/usr/bin/env python3
"""Gera video + audio com o Pika H3 Flex (LoRA sobre o MiniMax H3) num ComfyUI local.

Texto -> video com som sincronizado, 6 passos (sigmas do Flex + sampler lcm).
O servidor ComfyUI precisa estar no ar com os modelos do H3 e os LoRAs do Flex
(veja o README). Varios prompts na mesma chamada reaproveitam os modelos carregados.

Uso:
  python3 gera.py --prompt "cena" [--prompt "outra cena"] [--largura 1344 --altura 768 --segundos 5]
  python3 gera.py --arquivo prompts.txt          # um prompt por bloco separado por linha em branco
  python3 gera.py --sem-lora --prompt "..."      # H3 puro, para comparar
"""
import argparse, json, os, time, urllib.request, uuid

SIGMAS = "1.0, 0.972973, 0.923077, 0.8, 0.571429, 0.333333, 0.0"  # 6 NFE do Flex (shift 12 ja aplicado)

MODELOS = {
    "unet": "minimax_h3_fl2va_pruned_fp8_scaled.safetensors",
    "lora": "pika_h3_flex_fl2va_comfy_bf16.safetensors",
    "clip": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
    "vae_video": "minimax_h3_video_vae_fp16.safetensors",
    "vae_audio": "minimax_h3_audio_vae_fp32.safetensors",
}


def quadros(segundos):
    """O H3 quer N = 17k + 5 quadros a 24 fps (mesma conta do template oficial)."""
    n = max(5, round(segundos * 24))
    return n + (5 - n % 17) % 17


def grafo(prompt, larg, alt, frames, seed, sem_lora, prefixo):
    modelo = ["1", 0] if sem_lora else ["2", 0]
    g = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": MODELOS["unet"], "weight_dtype": "default"}},
        "2": {"class_type": "LoraLoaderModelOnly", "inputs": {
            "model": ["1", 0], "lora_name": MODELOS["lora"], "strength_model": 1.0}},
        "4": {"class_type": "CLIPLoader", "inputs": {"clip_name": MODELOS["clip"], "type": "minimax"}},
        "5": {"class_type": "VAELoader", "inputs": {"vae_name": MODELOS["vae_video"]}},
        "6": {"class_type": "VAELoader", "inputs": {"vae_name": MODELOS["vae_audio"]}},
        "8": {"class_type": "MiniMaxH3ImageToVideo", "inputs": {
            "clip": ["4", 0], "vae": ["5", 0], "prompt": prompt,
            "width": larg, "height": alt, "length": frames}},
        "20": {"class_type": "ManualSigmas", "inputs": {"sigmas": SIGMAS}},
        "21": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "lcm"}},
        "22": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "23": {"class_type": "BasicGuider", "inputs": {"model": modelo, "conditioning": ["8", 0]}},
        "10": {"class_type": "SamplerCustomAdvanced", "inputs": {
            "noise": ["22", 0], "guider": ["23", 0], "sampler": ["21", 0],
            "sigmas": ["20", 0], "latent_image": ["8", 1]}},
        "11": {"class_type": "VAEDecode", "inputs": {"samples": ["10", 0], "vae": ["5", 0]}},
        "12": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["10", 0], "vae": ["6", 0]}},
        "13": {"class_type": "CreateVideo", "inputs": {"images": ["11", 0], "fps": 24.0, "audio": ["12", 0]}},
        "14": {"class_type": "SaveVideo", "inputs": {
            "video": ["13", 0], "filename_prefix": prefixo, "format": "auto", "codec": "auto"}},
    }
    if sem_lora:
        del g["2"]
    return g


def roda(base, g, timeout):
    req = urllib.request.Request(base + "/prompt", headers={"Content-Type": "application/json"},
                                 data=json.dumps({"prompt": g, "client_id": uuid.uuid4().hex}).encode())
    r = json.load(urllib.request.urlopen(req, timeout=60))
    if r.get("node_errors"):
        raise SystemExit(f"erro no grafo: {r['node_errors']}")
    pid, t0 = r["prompt_id"], time.time()
    while time.time() - t0 < timeout:
        time.sleep(5)
        try:
            h = json.load(urllib.request.urlopen(f"{base}/history/{pid}", timeout=10))
        except Exception:
            raise SystemExit(f"servidor caiu apos {time.time()-t0:.0f}s (memoria? veja o README)")
        if pid in h:
            st = h[pid]["status"]
            if st.get("status_str") != "success":
                raise SystemExit("falhou: " + json.dumps(st.get("messages", [])[-2:])[:600])
            arq = [v[0] for o in h[pid]["outputs"].values() for v in o.values()
                   if isinstance(v, list) and v and isinstance(v[0], dict)][0]
            return os.path.join(arq.get("subfolder", ""), arq["filename"]), time.time() - t0
    raise SystemExit("timeout")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt", action="append", default=[])
    ap.add_argument("--arquivo")
    ap.add_argument("--largura", type=int, default=832)
    ap.add_argument("--altura", type=int, default=480)
    ap.add_argument("--segundos", type=float, default=3)
    ap.add_argument("--seed", type=int, default=20261109)
    ap.add_argument("--sem-lora", action="store_true")
    ap.add_argument("--prefixo", default="pika_flex/clip")
    ap.add_argument("--servidor", default="http://127.0.0.1:8299")
    a = ap.parse_args()
    prompts = list(a.prompt)
    if a.arquivo:
        prompts += [b.strip() for b in open(a.arquivo, encoding="utf-8").read().split("\n\n") if b.strip()]
    if not prompts:
        ap.error("passe --prompt ou --arquivo")
    n = quadros(a.segundos)
    for i, p in enumerate(prompts, 1):
        g = grafo(p, a.largura, a.altura, n, a.seed + i, a.sem_lora, f"{a.prefixo}{i:02d}")
        arq, s = roda(a.servidor, g, 3600)
        print(f"[{i}/{len(prompts)}] {a.largura}x{a.altura} {n} quadros em {s:.0f}s -> output/{arq}", flush=True)


if __name__ == "__main__":
    main()
