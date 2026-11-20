#!/usr/bin/env bash
# Sobe o ComfyUI-h3 DENTRO de um cgroup com teto de memória.
#
# Motivo: em 2026-08-20 o ComfyUI-h3 chegou a 48 GB de RSS, derrubou o
# MemAvailable pra 4.9 GB e travou a máquina inteira (thrashing, reboot forçado).
# Com o scope abaixo, quem morre é só o ComfyUI — o host continua de pé.
#
#   MemoryHigh     = pressão/reclaim começa aqui (soft, só segura o processo)
#   MemoryMax      = teto duro; estourou, o kernel mata SÓ este cgroup
#   MemorySwapMax  = limita swap-out, que é o que trava o host (thrashing)
#
# Ajuste pelas variáveis de ambiente se um render legítimo precisar de mais:
#   MEM_HIGH=64G MEM_MAX=80G ./comfyui-h3-start.sh

set -eu

MEM_HIGH="${MEM_HIGH:-56G}"
MEM_MAX="${MEM_MAX:-72G}"
MEM_SWAP="${MEM_SWAP:-2G}"

COMFY_DIR="${COMFY_DIR:-$HOME/projetos/VideosDGX2/ComfyUI-h3}"   # pasta do seu ComfyUI
VENV="${VENV:-$HOME/projetos/VideosDGX2/comfyui-h3-env}"   # venv do ComfyUI
PORT="${PORT:-8299}"
EXTRA_ARGS="${EXTRA_ARGS:---disable-dynamic-vram --disable-pinned-memory --cache-none}"   # sem isso os pesos ficam em dobro (RAM + GPU) no GB10
LOG="${LOG:-$HOME/comfyui-h3.log}"

# checa pela porta/unit, não por pgrep (pgrep -f casaria com o próprio script)
if curl -s -o /dev/null -m 3 "http://127.0.0.1:${PORT}/"; then
  echo "⚠️  ComfyUI-h3 já está respondendo na porta ${PORT}"
  exit 1
fi

echo "▶️  Subindo ComfyUI-h3 com teto: high=${MEM_HIGH} max=${MEM_MAX} swap=${MEM_SWAP}"

systemd-run --user --scope --unit="comfyui-h3" --collect \
  -p MemoryHigh="${MEM_HIGH}" \
  -p MemoryMax="${MEM_MAX}" \
  -p MemorySwapMax="${MEM_SWAP}" \
  bash -c "cd '${COMFY_DIR}' && source '${VENV}/bin/activate' && exec python main.py --listen 0.0.0.0 --port ${PORT} ${EXTRA_ARGS:-}" \
  >> "${LOG}" 2>&1 &

# o boot do h3 leva ~20-40s (carrega custom nodes); espera até 90s
for _ in $(seq 1 45); do
  curl -s -o /dev/null -m 2 "http://127.0.0.1:${PORT}/" && break
  sleep 2
done

if curl -s -o /dev/null -m 3 "http://127.0.0.1:${PORT}/"; then
  echo "✅ ComfyUI-h3 no ar em http://0.0.0.0:${PORT}"
  systemctl --user show comfyui-h3.scope -p MemoryHigh -p MemoryMax -p MemorySwapMax | sed 's/^/   /'
  echo "   Log: tail -f ${LOG}"
else
  echo "❌ Não subiu. Veja: tail -50 ${LOG}"
  exit 1
fi
