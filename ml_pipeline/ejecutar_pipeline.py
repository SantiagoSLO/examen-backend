"""
Script de ejecucion del pipeline QLoRA/PEFT
============================================

Este script demuestra como usar el pipeline de fine-tuning.

REQUISITOS:
-----------
1. GPU NVIDIA con al menos 12GB VRAM (recomendado 24GB+)
2. CUDA instalado y configurado
3. Dependencies instaladas

INSTALACION:
------------
pip install -r requirements.txt

Ejecutar:
---------
python ml_pipeline/ejecutar_pipeline.py
"""

import os
import sys

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml_pipeline.qlora_pipeline import (
    run_full_pipeline,
    inference_with_adapters,
    TrainingConfig,
)


def ejemplo_entrenamiento():
    """Ejemplo 1: Fine-tuning completo del modelo."""
    
    # Texts de entrenamiento (en un caso real, seria un dataset mas grande)
    train_texts = [
        # Formato tipico para fine-tuning instructivo
        "Pregunta: Cuales son los platos mas populares de la casa? Respuesta: Nuestra paella marinera, el solomillo al plato y el bacalao a la brasa son los mas solicitados por nuestros clientes.",
        "Pregunta: Tienen opciones vegetarianas? Respuesta: Si, contamos con varias opciones como la ensalada Cesar con tofu, el risotto de setas, la pasta vegetariana y hamburguesa de quinoa.",
        "Pregunta: A que hora abren y cierran? Respuesta: Abrimos de lunes a jueves de 12:00 a 23:00, y viernes a domingo de 12:00 a 00:00.",
        "Pregunta: Hacen entregas a domicilio? Respuesta: Si, tenemos servicio de entrega a domicilio sin cargo minimo dentro de un radio de 10 kilometros.",
        "Pregunta: Tienen menu para ninos? Respuesta: Si, tenemos un menu infantil completo por $9.99 que incluye bebida, plato principal y postre.",
        "Pregunta: Aceptan reservas? Respuesta: Si, puede hacer reservas llamando al telefono del restaurante o a traves de nuestra pagina web.",
        "Pregunta: Cual es el dress code? Respuesta: No tenemos un dress code estricto, pero recomendamos vestimenta casual elegante.",
        "Pregunta: Tienen estacionamiento? Respuesta: Si, contamos con estacionamiento propio gratuito para nuestros clientes.",
        "Pregunta: Hacen eventos privados? Respuesta: Si, contamos con salones privados para eventos empresariales, celebraciones familiares y reuniones.",
        "Pregunta: Cual es el plato del chef? Respuesta: El plato del chef es nuestro Steak Tartar preparado en mesa, acompanhado de fries caseras y alioli.",
    ]
    
    # Configuracion de entrenamiento personalizada
    training_config = TrainingConfig(
        learning_rate=2e-4,
        per_device_train_batch_size=4,
        num_train_epochs=3,
        gradient_accumulation_steps=2,
        logging_steps=10,
        save_steps=50,
        max_seq_length=512,
        packing=True,
    )
    
    # Ejecutar pipeline completo
    model = run_full_pipeline(
        model_name="meta-llama/Llama-2-7b-hf",  # O cualquier modelo compatible
        train_texts=train_texts,
        output_dir="./adapters/restaurante-bot",
        max_seq_length=512,
        training_config=training_config,
    )
    
    return model


def ejemplo_inferencia():
    """Ejemplo 2: Inferencia con el modelo entrenado."""
    
    # Ejecutar inferencia
    output = inference_with_adapters(
        base_model_name="meta-llama/Llama-2-7b-hf",
        adapters_path="./adapters/restaurante-bot",
        prompt="Cual es el mejor plato de la casa?",
        max_new_tokens=256,
        temperature=0.7,
    )
    
    print("=" * 50)
    print("RESULTADO DE INFERENCIA:")
    print("=" * 50)
    print(output)
    print("=" * 50)
    
    return output


def ejemplo_minimo():
    """Ejemplo 3: Caso minimo de uso."""
    from ml_pipeline.qlora_pipeline import (
        QuantizationConfig,
        LoRAConfig,
        TrainingConfig,
        get_bitsandbytes_config,
        get_lora_config,
        AutoModelForCausalLM,
        AutoTokenizer,
        prepare_model_for_training,
        create_peft_model,
        prepare_dataset,
        create_sft_trainer,
        save_adapters,
        generate_text,
    )
    
    # 1. Configuracion
    print("\n[1] Configurando BitsAndBytes para 4-bit quantization...")
    bnb_config = get_bitsandbytes_config()
    print("    - Tipo de cuantizacion: nf4")
    print("    - Double quantization: enabled")
    print("    - Compute dtype: bfloat16")
    
    print("\n[2] Configurando LoRA para PEFT...")
    lora_config = get_lora_config()
    print(f"    - Rank (r): {lora_config.r}")
    print(f"    - Alpha: {lora_config.lora_alpha}")
    print(f"    - Dropout: {lora_config.lora_dropout}")
    print(f"    - Target modules: {lora_config.target_modules}")
    
    print("\n[3] Configuracion de entrenamiento...")
    training_config = TrainingConfig()
    print(f"    - Learning rate: {training_config.learning_rate}")
    print(f"    - Batch size: {training_config.per_device_train_batch_size}")
    print(f"    - Epochs: {training_config.num_train_epochs}")
    print(f"    - Optimizer: {training_config.optimizer}")
    
    print("\n[4] Verificando imports de ML...")
    import torch
    print(f"    - PyTorch version: {torch.__version__}")
    
    import transformers
    print(f"    - Transformers version: {transformers.__version__}")
    
    import bitsandbytes
    print(f"    - BitsAndBytes installed: OK")
    
    import peft
    print(f"    - PEFT installed: OK")
    
    import trl
    print(f"    - TRL installed: OK")
    
    print("\n" + "=" * 50)
    print("RESUMEN DEL PIPELINE QLoRA/PEFT")
    print("=" * 50)
    print("""
El pipeline esta configurado y listo. Para ejecutar el entrenamiento
necesitas:

1. GPU NVIDIA con CUDA y al menos 12GB VRAM
2. Instalar PyTorch con soporte CUDA:
   pip uninstall torch
   pip install torch --index-url https://download.pytorch.org/whl/cu121

3. Ejecutar el entrenamiento:
   - Opcion 1: Fine-tuning completo (requiere ~16GB VRAM)
   - Opcion 2: Inferencia con modelo entrenado
   - Opcion 3: Ejemplo con modelo pequeno (~8GB VRAM)

Modelos recomendados por VRAM:
- TinyLlama (1.1B): 6-8 GB
- Llama-2-7b: 12-16 GB  
- Llama-2-13b: 20-24 GB
- Mistral-7b: 12-16 GB

Nota: El modelo base se cuantiza a 4-bit, pero se necesita VRAM
adicional durante el entrenamiento para gradientes y estados
del optimizador.
    """)
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("QLoRA/PEFT Pipeline - Verificacion de configuracion")
    print("=" * 60)
    print()
    print("Ejecutando ejemplo minimo (configuracion)...")
    print("Este ejemplo solo verifica la configuracion del pipeline")
    print("Para entrenamiento real se necesita GPU con CUDA")
    print()
    
    try:
        ejemplo_minimo()
        print()
        print("=" * 50)
        print("Pipeline configurado correctamente!")
        print("El modulo esta listo para usar cuando tengas GPU con CUDA")
        print("=" * 50)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
