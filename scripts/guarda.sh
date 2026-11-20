#!/usr/bin/env bash
# Guarda do ComfyUI-h3 no GB10: o MemoryMax do scope NAO conta a memoria da GPU
# (unificada), entao vigia a memoria livre da maquina e derruba o ComfyUI antes do OOM global.
# Uso: guarda.sh <log> [limite_GB=10]
LOG="${1:-/dev/stdout}"; LIM="${2:-10}"
while systemctl --user is-active -q comfyui-h3.scope; do
  A=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)
  C=$(( $(systemctl --user show comfyui-h3.scope -p MemoryCurrent --value 2>/dev/null || echo 0) / 1073741824 ))
  G=$(nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader,nounits 2>/dev/null | awk -F, '{s+=$2} END{print int(s/1024)}')
  echo "$(date +%T) avail=${A}G cgroup=${C}G gpu_procs=${G}G" >> "$LOG"
  if [ "$A" -lt "$LIM" ]; then
    echo "$(date +%T) GUARDA: avail ${A}G < ${LIM}G -> derrubando comfyui-h3" >> "$LOG"
    systemctl --user stop comfyui-h3.scope
    break
  fi
  sleep 3
done
