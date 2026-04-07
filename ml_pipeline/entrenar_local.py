"""
Script para ejecutar fine-tuning real con GPU
============================================
Usa un modelo pequeno (TinyLlama) que puede correr en 4GB VRAM
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_pipeline.qlora_pipeline import (
    get_bitsandbytes_config,
    get_lora_config,
    AutoModelForCausalLM,
    AutoTokenizer,
    prepare_model_for_training,
    create_peft_model,
    create_tokenizer,
    prepare_dataset,
    create_sft_trainer,
    save_adapters,
)

print("=" * 60)
print("QLoRA Fine-Tuning con GPU")
print("=" * 60)
print()

# Verificar GPU
import torch
print(f"[GPU] PyTorch version: {torch.__version__}")
print(f"[GPU] CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"[GPU] GPU: {torch.cuda.get_device_name(0)}")
    print(f"[GPU] VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
print()

# Configuracion
print("[1] Configurando BitsAndBytes para 4-bit quantization...")
bnb_config = get_bitsandbytes_config()

print("[2] Configurando LoRA...")
lora_config = get_lora_config()

# Modelo pequeno para 4GB VRAM
model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
print(f"[3] Descargando modelo: {model_name}...")
print("    (Esto puede tomar unos minutos)")

# Cargar modelo con cuantizacion
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
)

print("[4] Preparando modelo para entrenamiento...")
model = prepare_model_for_training(model)

print("[5] Aplicando LoRA...")
model = create_peft_model(model, lora_config)

print("[6] Descargando tokenizador...")
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token

# Dataset pequeno de ejemplo
train_texts = [
    "Pregunta: Cuales son los platos mas populares? Respuesta: Nuestra paella marinera es el mas solicitado.",
    "Pregunta: Tienen opciones vegetarianas? Respuesta: Si, tenemos ensalada Cesar con tofu y risotto de setas.",
    "Pregunta: A que hora abren? Respuesta: Abrimos de lunes a domingo de 12:00 a 23:00.",
    "Pregunta: Hacen entregas a domicilio? Respuesta: Si, hacemos entregas dentro de 10 kilometros.",
]

print("[7] Preparando dataset...")
dataset = prepare_dataset(train_texts, tokenizer, max_seq_length=256)

print("[8] Configurando trainer...")
trainer = create_sft_trainer(
    model,
    tokenizer,
    dataset,
    output_dir="./test_output",
)

print()
print("=" * 60)
print("INICIANDO ENTRENAMIENTO...")
print("=" * 60)
print()

# Entrenar (solo 1 epoch para prueba rapida)
trainer.train()

print()
print("=" * 60)
print("GUARDANDO ADAPTERS...")
print("=" * 60)
print()

save_adapters(model, "./adapters/tinyllama-restaurante")

print()
print("=" * 60)
print("ENTRENAMIENTO COMPLETADO!")
print("=" * 60)
print("Los adapters se han guardado en: ./adapters/tinyllama-restaurante")