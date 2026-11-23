#!/usr/bin/env bash
set -euo pipefail

out="$(realpath "$1")"
runtime="$RUNNER_TEMP/puppy50-image-models"
mkdir -p "$runtime"
cd "$runtime"

download() {
  local url=$1 file=$2 checksum=$3
  curl -fsSL --retry 1 --connect-timeout 20 --max-time 420 "$url" -o "$file"
  printf '%s  %s\n' "$checksum" "$file" | sha256sum -c -
}

download \
  'https://github.com/leejet/stable-diffusion.cpp/releases/download/master-1117-0d71f96/sd-master-0d71f96-bin-Linux-Ubuntu-26.04-x86_64.zip' \
  sd.zip c710c9413aac5b3cab4a2a0260b1e5488d0abd8659254466523d2433c3cba421
unzip -q sd.zip -d sd
download \
  'https://huggingface.co/AtomicChat/Qwen-Image-2.1-Turbo-GGUF/resolve/cbcb9ff83b17e1eeef693479a8d34cea355a0ee4/Qwen-Image-2.1-Turbo-AD-Q4_K.gguf?download=true' \
  diffusion.gguf 4bb73c53cbe284bbd6d69b9fdc59539c531f0389dd2aa567663d777f8130bc59 &
diffusion_job=$!
download \
  'https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct-GGUF/resolve/f982a07559d4a2f6c8744d840bf6fccab30eea96/Qwen3VL-8B-Instruct-Q4_K_M.gguf?download=true' \
  text.gguf 67d1659bfe71b89d50b45a4ad1a9e5b997e5bb16ce5da66a6a6167abd569e9e2 &
text_job=$!
download \
  'https://huggingface.co/Comfy-Org/Qwen-Image-2.1/resolve/aacf31a6d48e707f352ecba714cee0680da3479b/vae/qwen_image_2.1_vae_bf16.safetensors?download=true' \
  vae.safetensors bb21f7473051e1ac368515dd3f2e15cd44d7a11748ee8823e1ddca3e4876b7c9 &
vae_job=$!
wait "$diffusion_job"
wait "$text_job"
wait "$vae_job"

prompt="$(jq -er '.prompt' "$out/image-example.json")"
seed="$(jq -er '.seed' "$out/image-example.json")"
width="$(jq -er '.width' "$out/image-example.json")"
height="$(jq -er '.height' "$out/image-example.json")"
timeout --kill-after=10s 40m sd/sd-cli \
  --backend cpu \
  --diffusion-model "$runtime/diffusion.gguf" --llm "$runtime/text.gguf" \
  --vae "$runtime/vae.safetensors" --params-backend 'te=disk,diffusion=disk,vae=cpu' \
  --offload-to-cpu --cfg-scale 1 --sampling-method euler --steps 8 \
  --sigmas '1.0,0.978453,0.95418,0.926626,0.89508,0.845148,0.704534,0.414568,0.0' \
  -t 4 -s "$seed" -W "$width" -H "$height" -p "$prompt" \
  -o "$out/puppy50-qwen-image.png" 2>&1 | tee "$out/qwen-image-render.log"
