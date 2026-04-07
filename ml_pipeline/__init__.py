"""
ML Pipeline - QLoRA/PEFT Fine-Tuning Module
==========================================

Este módulo proporciona funciones para Fine-Tuning eficiente de LLMs
utilizando QLoRA (4-bit Quantization) y PEFT.

Módulos principales:
- qlora_pipeline: Pipeline completo de entrenamiento e inferencia

Uso básico:
    from ml_pipeline.qlora_pipeline import run_full_pipeline
    
    texts = ["Texto de ejemplo para entrenamiento..."]
    model = run_full_pipeline("meta-llama/Llama-2-7b-hf", texts)
"""

from .qlora_pipeline import (
    # Configuración
    QuantizationConfig,
    LoRAConfig,
    TrainingConfig,
    # Funciones de configuración
    get_bitsandbytes_config,
    get_lora_config,
    # Preparación del modelo
    prepare_model_for_training,
    create_peft_model,
    # Tokenización
    create_tokenizer,
    tokenize_function,
    prepare_dataset,
    # Entrenamiento
    create_sft_trainer,
    # Guardado y carga
    save_adapters,
    load_adapters,
    # Inferencia
    generate_text,
    inference_with_adapters,
    # Pipeline completo
    run_full_pipeline,
)

__all__ = [
    "QuantizationConfig",
    "LoRAConfig", 
    "TrainingConfig",
    "get_bitsandbytes_config",
    "get_lora_config",
    "prepare_model_for_training",
    "create_peft_model",
    "create_tokenizer",
    "tokenize_function",
    "prepare_dataset",
    "create_sft_trainer",
    "save_adapters",
    "load_adapters",
    "generate_text",
    "inference_with_adapters",
    "run_full_pipeline",
]

__version__ = "1.0.0"
