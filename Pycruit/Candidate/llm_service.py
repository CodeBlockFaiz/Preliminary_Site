import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

# Load once at startup (IMPORTANT)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float32
)

model.eval()


def generate_mcqs_with_llm(text, num_questions=5):
    prompt = f"""
Generate {num_questions} multiple choice questions from the text below.

Return STRICT JSON format:

[
  {{
    "question": "...",
    "option_a": "...",
    "option_b": "...",
    "option_c": "...",
    "option_d": "...",
    "correct_answer": "A"
  }}
]

TEXT:
{text}
"""

    inputs = tokenizer(prompt, return_tensors="pt")

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.7,
            do_sample=True
        )

    result = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Try extracting JSON part
    try:
        json_start = result.index("[")
        json_end = result.rindex("]") + 1
        json_output = result[json_start:json_end]
        return json.loads(json_output)
    except:
        return []