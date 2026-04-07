"""
Pipeline QLoRA/PEFT para Fine-Tuning eficiente de LLMs
======================================================

Este módulo implementa un pipeline completo de entrenamiento e inferencia
utilizando QLoRA (4-bit Quantization) para adaptar modelos de lenguaje
sin desbordar la memoria VRAM.

Basado en: https://colab.research.google.com/drive/11beFFeC_HoRx2EbdQOco6QNCsqWsxEie

Dependencias requeridas:
- bitsandbytes>=0.41.0
- transformers>=4.35.0
- peft>=0.7.0
- trl>=0.7.0
- accelerate>=0.24.0
- torch>=2.0.0
"""

import os
import torch
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

# Importaciones de Hugging Face y bibliotecas relacionadas
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    DataCollatorForLanguageModeling,
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    PeftModel,
)
from trl import SFTTrainer
from datasets import Dataset


# ==============================================================================
# CONFIGURACIÓN DE CUANTIZACIÓN (BitsAndBytesConfig)
# ==============================================================================

@dataclass
class QuantizationConfig:
    """Configuración para cuantización 4-bit del modelo."""
    
    # Tipo de cuantización: nf4 (NormalFloat4) es óptimo para pesos de redes neuronales
    quantization_type: str = "nf4"
    
    # Habilitar cuantización doble para mayor ahorro de memoria
    double_quant: bool = True
    
    # Precisión de cómputo: bfloat16 para estabilidad en entrenamiento
    compute_dtype: torch.dtype = torch.bfloat16
    
    # Tipo de cuantización para almacenamiento
    load_in_4bit: bool = True


def get_bitsandbytes_config(config: Optional[QuantizationConfig] = None) -> BitsAndBytesConfig:
    """
    Genera la configuración de BitsAndBytes para carga en 4-bits.
    
    Args:
        config: Objeto de configuración de cuantización. Si es None, usa valores por defecto.
        
    Returns:
        BitsAndBytesConfig configurado para QLoRA.
        
    Ejemplo:
        >>> bnb_config = get_bitsandbytes_config()
        >>> model = AutoModelForCausalLM.from_pretrained(
        ...     "model_name",
        ...     quantization_config=bnb_config,
        ...     device_map="auto"
        ... )
    """
    if config is None:
        config = QuantizationConfig()
    
    return BitsAndBytesConfig(
        load_in_4bit=config.load_in_4bit,
        bnb_4bit_compute_dtype=config.compute_dtype,
        bnb_4bit_quant_type=config.quantization_type,
        bnb_4bit_use_double_quant=config.double_quant,
    )


# ==============================================================================
# CONFIGURACIÓN DE LoRA (PEFT)
# ==============================================================================

@dataclass
class LoRAConfig:
    """Configuración de parámetros LoRA para Fine-Tuning."""
    
    # Rango de la matriz de decompose (dimensión latente)
    r: int = 16
    
    # Escala de losAdapter
    lora_alpha: int = 32
    
    # Dropout para regularización
    lora_dropout: float = 0.05
    
    # Capas objetivo para aplicar LoRA
    target_modules: List[str] = None
    
    # Bias type: "none", "all", "lora_only"
    bias: str = "none"
    
    # Tipo de tarea para el modelo
    task_type: str = "CAUSAL_LM"


def get_lora_config(config: Optional[LoRAConfig] = None) -> LoraConfig:
    """
    Genera la configuración de LoRA para PEFT.
    
    Args:
        config: Objeto de configuración LoRA. Si es None, usa valores por defecto.
        
    Returns:
        LoraConfig configurado para el entrenamiento.
        
    Ejemplo:
        >>> lora_config = get_lora_config()
        >>> model = get_peft_model(model, lora_config)
    """
    if config is None:
        config = LoRAConfig()
    
    # Valores por defecto para target_modules (puede variar según la arquitectura)
    if config.target_modules is None:
        config.target_modules = ["q_proj", "v_proj"]
    
    return LoraConfig(
        r=config.r,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        target_modules=config.target_modules,
        bias=config.bias,
        task_type=config.task_type,
    )


# ==============================================================================
# PREPARACIÓN DEL MODELO
# ==============================================================================

def prepare_model_for_training(
    model: AutoModelForCausalLM,
    use_gradient_checkpointing: bool = True
) -> AutoModelForCausalLM:
    """
    Prepara el modelo cuantizado para el entrenamiento con k-bit.
    
    Args:
        model: Modelo cuantizado con BitsAndBytes.
        use_gradient_checkpointing: Habilitar checkpointing de gradientes para ahorrar VRAM.
        
    Returns:
        Modelo preparado para entrenamiento.
        
    Ejemplo:
        >>> model = prepare_model_for_training(model)
        >>> model = get_peft_model(model, lora_config)
    """
    # Preparar el modelo para entrenamiento con cuantización
    model = prepare_model_for_kbit_training(
        model,
        use_gradient_checkpointing=use_gradient_checkpointing
    )
    
    return model


def create_peft_model(
    base_model: AutoModelForCausalLM,
    lora_config: Optional[LoRAConfig] = None
) -> PeftModel:
    """
    Crea un modelo PEFT aplicando LoRA al modelo base.
    
    Args:
        base_model: Modelo base cuantizado.
        lora_config: Configuración de LoRA.
        
    Returns:
        Modelo con adaptadores LoRA aplicados.
    """
    if lora_config is None:
        lora_config = LoRAConfig()
    
    lora_config_obj = get_lora_config(lora_config)
    peft_model = get_peft_model(base_model, lora_config_obj)
    
    # Mostrar información de parámetros entrenables
    peft_model.print_trainable_parameters()
    
    return peft_model


# ==============================================================================
# TOKENIZACIÓN
# ==============================================================================

def create_tokenizer(
    model_name: str,
    max_seq_length: Optional[int] = None,
    padding_side: str = "right"
) -> AutoTokenizer:
    """
    Crea un tokenizador configurado para el modelo.
    
    Args:
        model_name: Nombre o path del modelo en Hugging Face.
        max_seq_length: Longitud máxima de secuencia. Si es None, usa la del modelo.
        padding_side: Lado del padding ("left" o "right").
        
    Returns:
        Tokenizador configurado.
        
    Ejemplo:
        >>> tokenizer = create_tokenizer("meta-llama/Llama-2-7b-hf", max_seq_length=512)
    """
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        padding_side=padding_side,
        trust_remote_code=True,
    )
    
    # Configurar tokens de padding
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Establecer longitud máxima de secuencia
    if max_seq_length is not None:
        tokenizer.model_max_length = max_seq_length
    
    return tokenizer


def tokenize_function(
    examples: Dict[str, Any],
    tokenizer: AutoTokenizer,
    max_seq_length: Optional[int] = None,
    add_special_tokens: bool = True
) -> Dict[str, List]:
    """
    Función de tokenización que maneja padding y truncamiento.
    
    Args:
        examples: Batch de ejemplos del dataset.
        tokenizer: Tokenizador a usar.
        max_seq_length: Longitud máxima de secuencia.
        add_special_tokens: Añadir tokens especiales (CLS, SEP, etc.).
        
    Returns:
        Batch tokenizado.
    """
    # Determinar longitud máxima
    max_length = max_seq_length or tokenizer.model_max_length
    
    # Tokenizar el texto
    tokenized = tokenizer(
        examples["text"],
        max_length=max_length,
        truncation=True,
        padding="max_length",
        add_special_tokens=add_special_tokens,
        return_tensors=None,
    )
    
    return tokenized


def prepare_dataset(
    texts: List[str],
    tokenizer: AutoTokenizer,
    max_seq_length: Optional[int] = None
) -> Dataset:
    """
    Prepara un dataset para entrenamiento.
    
    Args:
        texts: Lista de textos para el dataset.
        tokenizer: Tokenizador a usar.
        max_seq_length: Longitud máxima de secuencia.
        
    Returns:
        Dataset tokenizado listo para entrenamiento.
    """
    # Crear dataset desde lista de textos
    dataset = Dataset.from_dict({"text": texts})
    
    # Aplicar tokenización
    def tokenize_wrapper(examples):
        return tokenize_function(examples, tokenizer, max_seq_length)
    
    dataset = dataset.map(
        tokenize_wrapper,
        batched=True,
        remove_columns=dataset.column_names,
    )
    
    return dataset


# ==============================================================================
# ENTRENAMIENTO CON SFTTrainer
# ==============================================================================

@dataclass
class TrainingConfig:
    """Configuración de hiperparámetros de entrenamiento."""
    
    # Learning rate
    learning_rate: float = 2e-4
    
    # Tamaño de batch
    per_device_train_batch_size: int = 4
    
    # Número de epochs
    num_train_epochs: int = 3
    
    # Paso de gradient accumulation
    gradient_accumulation_steps: int = 2
    
    # Optimizer
    optimizer: str = "paged_adamw_32bit"
    
    # Scheduler
    lr_scheduler_type: str = "cosine"
    
    # Logging steps
    logging_steps: int = 10
    
    # Saving steps
    save_steps: int = 100
    
    # Warmup ratio
    warmup_ratio: float = 0.03
    
    # Longitud máxima de secuencia
    max_seq_length: int = 512
    
    # packing
    packing: bool = True


def create_sft_trainer(
    model: PeftModel,
    tokenizer: AutoTokenizer,
    train_dataset: Dataset,
    output_dir: str = "./results",
    config: Optional[TrainingConfig] = None,
) -> SFTTrainer:
    """
    Configura el SFTTrainer (Supervised Fine-tuning Trainer).
    
    Args:
        model: Modelo PEFT preparado.
        tokenizer: Tokenizador del modelo.
        train_dataset: Dataset de entrenamiento.
        output_dir: Directorio para guardar resultados.
        config: Configuración de entrenamiento.
        
    Returns:
        SFTTrainer configurado.
        
    Ejemplo:
        >>> trainer = create_sft_trainer(model, tokenizer, train_dataset)
        >>> trainer.train()
    """
    if config is None:
        config = TrainingConfig()
    
    # Data collator para language modeling
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,  # Para CLM (Causal Language Modeling)
    )
    
    # Configuración de argumentos de entrenamiento
    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=config.per_device_train_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        num_train_epochs=config.num_train_epochs,
        lr_scheduler_type=config.lr_scheduler_type,
        logging_steps=config.logging_steps,
        save_steps=config.save_steps,
        warmup_ratio=config.warmup_ratio,
        optim=config.optimizer,
        fp16=False,  # Usamos bfloat16 en la cuantización
        bf16=True,   # Habilitar bfloat16
        save_total_limit=2,
        report_to="none",
    )
    
    # Crear SFTTrainer
    trainer = SFTTrainer(
        model=model,
        train_dataset=train_dataset,
        tokenizer=tokenizer,
        args=training_args,
        data_collator=data_collator,
        max_seq_length=config.max_seq_length,
        packing=config.packing,
    )
    
    return trainer


# ==============================================================================
# GUARDADO DE ADAPTERS
# ==============================================================================

def save_adapters(
    model: PeftModel,
    output_dir: str,
    safe_serialization: bool = True
) -> None:
    """
    Guarda únicamente los adapters entrenados.
    
    Args:
        model: Modelo PEFT con adapters.
        output_dir: Directorio donde guardar los adapters.
        safe_serialization: Usar formato seguro (safetensors).
        
    Ejemplo:
        >>> save_adapters(model, "./adapters/qlora-model")
    """
    model.save_pretrained(output_dir, safe_serialization=safe_serialization)
    print(f"✅ Adapters guardados en: {output_dir}")


def load_adapters(
    base_model_name: str,
    adapters_path: str,
    device_map: str = "auto"
) -> PeftModel:
    """
    Carga el modelo base y fusiona los adapters entrenados.
    
    Args:
        base_model_name: Nombre del modelo base.
        adapters_path: Path a los adapters guardados.
        device_map: Estrategia de mapeo de dispositivos.
        
    Returns:
        Modelo con adapters fusionados.
    """
    # Cargar configuración de cuantización
    bnb_config = get_bitsandbytes_config()
    
    # Cargar modelo base con cuantización
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        quantization_config=bnb_config,
        device_map=device_map,
        trust_remote_code=True,
    )
    
    # Cargar adapters y fusionar
    model = PeftModel.from_pretrained(
        base_model,
        adapters_path,
        is_trainable=False,  # Modo inferencia
    )
    
    # Fusionar pesos de LoRA con el modelo base
    model = model.merge_and_unload()
    
    print(f"✅ Modelo con adapters fusionados cargado desde: {adapters_path}")
    
    return model


# ==============================================================================
# INFERENCIA
# ==============================================================================

def generate_text(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    prompt: str,
    max_new_tokens: int = 256,
    temperature: float = 0.7,
    top_p: float = 0.9,
    top_k: int = 50,
    do_sample: bool = True,
    repetition_penalty: float = 1.1
) -> str:
    """
    Genera texto utilizando el modelo entrenado.
    
    Args:
        model: Modelo para generación.
        tokenizer: Tokenizador del modelo.
        prompt: Prompt de entrada.
        max_new_tokens: Máximo de tokens a generar.
        temperature: Temperatura para muestreo.
        top_p: Nucleus sampling threshold.
        top_k: Top-k sampling.
        do_sample: Usar muestreo estocástico.
        repetition_penalty: Penalización por repetición.
        
    Returns:
        Texto generado.
        
    Ejemplo:
        >>> output = generate_text(model, tokenizer, "¿Cuál es el mejor restaurante?")
        >>> print(output)
    """
    # Tokenizar el prompt
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        padding=True,
        truncation=True,
    ).to(model.device)
    
    # Generar
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            do_sample=do_sample,
            repetition_penalty=repetition_penalty,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    
    # Decodificar la respuesta
    response = tokenizer.decode(
        outputs[0],
        skip_special_tokens=True
    )
    
    return response


def inference_with_adapters(
    base_model_name: str,
    adapters_path: str,
    prompt: str,
    **generation_kwargs
) -> str:
    """
    Función de inferencia que carga el modelo base, fusiona adapters y genera texto.
    
    Args:
        base_model_name: Nombre del modelo base.
        adapters_path: Path a los adapters.
        prompt: Prompt de entrada.
        **generation_kwargs: Argumentos adicionales para generación.
        
    Returns:
        Texto generado.
        
    Ejemplo:
        >>> output = inference_with_adapters(
        ...     "meta-llama/Llama-2-7b-hf",
        ...     "./adapters/qlora-model",
        ...     "Explain quantum computing in simple terms"
        ... )
    """
    # Cargar tokenizador
    tokenizer = AutoTokenizer.from_pretrained(
        base_model_name,
        trust_remote_code=True
    )
    
    # Cargar modelo con adapters fusionados
    model = load_adapters(base_model_name, adapters_path)
    
    # Generar texto
    output = generate_text(
        model,
        tokenizer,
        prompt,
        **generation_kwargs
    )
    
    return output


# ==============================================================================
# PIPELINE COMPLETO
# ==============================================================================

def run_full_pipeline(
    model_name: str,
    train_texts: List[str],
    output_dir: str = "./results",
    max_seq_length: int = 512,
    training_config: Optional[TrainingConfig] = None,
    lora_config: Optional[LoRAConfig] = None,
    quantization_config: Optional[QuantizationConfig] = None,
) -> PeftModel:
    """
    Ejecuta el pipeline completo de entrenamiento QLoRA.
    
    Args:
        model_name: Nombre del modelo a fine-tunear.
        train_texts: Lista de textos para entrenamiento.
        output_dir: Directorio para guardar resultados.
        max_seq_length: Longitud máxima de secuencia.
        training_config: Configuración de entrenamiento.
        lora_config: Configuración de LoRA.
        quantization_config: Configuración de cuantización.
        
    Returns:
        Modelo entrenado con adapters.
        
    Ejemplo:
        >>> train_texts = [
        ...     "Pregunta: ¿Cuál es el mejor plato? Respuesta: Paella.",
        ...     "Pregunta: ¿Tienen opciones vegetarianas? Respuesta: Sí, tenemos ensaladas.",
        ... ]
        >>> model = run_full_pipeline("meta-llama/Llama-2-7b-hf", train_texts)
    """
    print(f"🚀 Iniciando pipeline QLoRA para: {model_name}")
    
    # 1. Configurar cuantización
    print("📦 Configurando cuantización 4-bit...")
    bnb_config = get_bitsandbytes_config(quantization_config)
    
    # 2. Cargar modelo cuantizado
    print("📥 Cargando modelo con cuantización...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    
    # 3. Preparar modelo para entrenamiento
    print("⚙️ Preparando modelo para entrenamiento...")
    model = prepare_model_for_training(model)
    
    # 4. Crear tokenizador
    print("🔤 Creando tokenizador...")
    tokenizer = create_tokenizer(model_name, max_seq_length=max_seq_length)
    
    # 5. Preparar dataset
    print("📚 Preparando dataset...")
    train_dataset = prepare_dataset(train_texts, tokenizer, max_seq_length)
    
    # 6. Crear modelo PEFT
    print("🧬 Aplicando LoRA...")
    model = create_peft_model(model, lora_config)
    
    # 7. Crear trainer
    print("🏋️ Configurando SFTTrainer...")
    trainer = create_sft_trainer(
        model,
        tokenizer,
        train_dataset,
        output_dir=output_dir,
        config=training_config,
    )
    
    # 8. Entrenar
    print("🔥 Iniciando entrenamiento...")
    trainer.train()
    
    # 9. Guardar adapters
    print("💾 Guardando adapters...")
    save_adapters(model, output_dir)
    
    print("✅ Pipeline completado exitosamente!")
    
    return model


# ==============================================================================
# EJEMPLO DE USO
# ==============================================================================

if __name__ == "__main__":
    # Ejemplo de uso del pipeline
    
    # Textos de ejemplo para un restaurant chatbot
    example_texts = [
        "Pregunta: ¿Cuáles son los platos más populares? Respuesta: Nuestra paella marinera y el solomillo al plato son los más solicitados por nuestros clientes.",
        "Pregunta: ¿Tienen opciones vegetarianas? Respuesta: Sí, ofrecemos varias opciones como nuestra ensalada César con tofu, risotto de setas y pasta vegetariana.",
        "Pregunta: ¿A qué hora abren? Respuesta: Abrimos de lunes a domingo de 12:00 a 23:00 horas.",
        "Pregunta: ¿Hacen entregas a domicilio? Respuesta: Sí, temos servicio de entrega a domicilio dentro de un radio de 10 kilómetros.",
        "Pregunta: ¿Tienen menú para niños? Respuesta: Sí, tenemos un menú infantil que incluye plato principal, bebida y postre por $9.99.",
    ]
    
    # Nota: Para ejecutar, necesitas instalar las dependencias y tener GPU con al menos 12GB VRAM
    # pip install bitsandbytes transformers peft trl accelerate torch datasets
    
    print("📝 Este módulo proporciona funciones para Fine-Tuning con QLoRA.")
    print("💡 Para ejecutar el pipeline completo, usa: run_full_pipeline()")
    print("🔧 Para inferencia, usa: inference_with_adapters()")
