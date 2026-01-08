"""
LLM Adapter — Local Google FLAN (macOS HARD SAFE MODE)
"""

import os

# --- HARD DISABLE ALL PARALLELISM ---
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import torch
torch.set_num_threads(1)
torch.set_num_interop_threads(1)

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


MODEL_NAME = "google/flan-t5-small"

print("🔹 Loading FLAN tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

print("🔹 Loading FLAN model (CPU, single-thread)...")
model = AutoModelForSeq2SeqLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float32
)

model.eval()
model.to("cpu")

print("✅ FLAN model loaded successfully")


def run_llm(prompt: str) -> str:
    with torch.no_grad():
        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=1024
        )

        outputs = model.generate(
            **inputs,
            max_new_tokens=300,
            do_sample=False,
            num_beams=1
        )

    return tokenizer.decode(outputs[0], skip_special_tokens=True)















# 
# """
# LLM Adapter — Local Google FLAN
# -------------------------------
# Uses google/flan-t5 for local, deterministic text rewriting.

# Phase: 3
# Design:
# - No internet calls
# - No hallucination
# - Language-only usage
# """

# from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
# import torch


# MODEL_NAME = "google/flan-t5-base"

# # Load once at startup
# tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
# model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

# device = "cuda" if torch.cuda.is_available() else "cpu"
# model = model.to(device)


# def run_llm(prompt: str) -> str:
#     """
#     Runs FLAN locally to rewrite text.
#     """

#     inputs = tokenizer(
#         prompt,
#         return_tensors="pt",
#         truncation=True,
#         max_length=2048
#     ).to(device)

#     outputs = model.generate(
#         **inputs,
#         max_new_tokens=500,
#         temperature=0.2,      # low creativity
#         do_sample=False,      # deterministic
#         num_beams=4,          # better phrasing
#         repetition_penalty=1.1
#     )

#     return tokenizer.decode(outputs[0], skip_special_tokens=True)










# import openai

# openai.api_key = "YOUR_API_KEY"

# def run_llm(prompt: str) -> str:
#     response = openai.ChatCompletion.create(
#         model="gpt-4.1-mini",
#         messages=[
#             {"role": "system", "content": "You rewrite text only. You do not reason."},
#             {"role": "user", "content": prompt}
#         ],
#         temperature=0.2,
#         max_tokens=800
#     )

#     return response.choices[0].message.content.strip()
