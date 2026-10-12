import json
import time

import joblib
import numpy as np
import torch

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report, precision_recall_fscore_support

from transformers import AutoTokenizer, AutoModelForSequenceClassification


# ==========================================
# CONFIG
# ==========================================

ML_DIR = "curated_space_ml"

DATA_DIR = f"{ML_DIR}/data/processed"

DISTILBERT_PATH = f"{ML_DIR}/models/curated-space-distilbert"

TFIDF_OUT = "ml/model/curated_space_classifier.pkl"


# ==========================================
# LOAD LABELS + SPLITS
# ==========================================

with open(f"{DATA_DIR}/labels.json", "r", encoding="utf-8") as f:
    label_data = json.load(f)


id2label = {int(index): label for index, label in label_data["id2label"].items()}


import pandas as pd

train_df = pd.read_csv(f"{DATA_DIR}/train.csv")

test_df = pd.read_csv(f"{DATA_DIR}/test.csv")


print("=" * 60)
print("SHARED EVALUATION SET")
print("=" * 60)
print("Train rows:", len(train_df))
print("Test rows:", len(test_df))
print("Labels:", list(label_data["label2id"].keys()))


X_train = train_df["text"].tolist()
y_train = train_df["label"].tolist()

X_test = test_df["text"].tolist()
y_test = test_df["label"].tolist()

y_test_names = [id2label[i] for i in y_test]


# ==========================================
# MODEL A: TF-IDF + LinearSVC  (ml/ approach)
# ==========================================

print()
print("=" * 60)
print("MODEL A: TF-IDF + LinearSVC  (ml/train.py approach)")
print("=" * 60)

tfidf_model = Pipeline(
    [("tfidf", TfidfVectorizer(lowercase=True, ngram_range=(1, 2))), ("svm", LinearSVC())]
)

tfidf_start = time.perf_counter()

tfidf_model.fit(X_train, y_train)

tfidf_train_time = time.perf_counter() - tfidf_start

tfidf_pred_ids = tfidf_model.predict(X_test)

tfidf_pred_names = [id2label[int(i)] for i in tfidf_pred_ids]

tfidf_acc = accuracy_score(y_test_names, tfidf_pred_names)

tfidf_p, tfidf_r, tfidf_f1, _ = precision_recall_fscore_support(
    y_test_names, tfidf_pred_names, average="macro", zero_division=0
)

# inference latency
tfidf_latency_start = time.perf_counter()

for _ in range(20):
    tfidf_model.predict([X_test[0]])

tfidf_latency = (time.perf_counter() - tfidf_latency_start) / 20

print("Train time:", round(tfidf_train_time, 3), "s")
print("Accuracy:", round(tfidf_acc * 100, 2), "%")
print("Macro precision:", round(tfidf_p, 4))
print("Macro recall:", round(tfidf_r, 4))
print("Macro F1:", round(tfidf_f1, 4))
print("Latency/item:", round(tfidf_latency * 1000, 3), "ms")

print()
print(classification_report(y_test_names, tfidf_pred_names))

joblib.dump(tfidf_model, TFIDF_OUT)

import os

print("Saved to:", TFIDF_OUT, os.path.getsize(TFIDF_OUT), "bytes")


# ==========================================
# MODEL B: Fine-tuned DistilBERT
# ==========================================

print()
print("=" * 60)
print("MODEL B: Fine-tuned DistilBERT  (curated_space_ml)")
print("=" * 60)

tokenizer = AutoTokenizer.from_pretrained(DISTILBERT_PATH)

distilbert = AutoModelForSequenceClassification.from_pretrained(DISTILBERT_PATH)

distilbert.eval()

distilbert_pred_ids = []

distilbert_latency_total = 0.0

with torch.no_grad():
    for text in X_test:
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=256)

        t0 = time.perf_counter()

        outputs = distilbert(**inputs)

        distilbert_latency_total += time.perf_counter() - t0

        distilbert_pred_ids.append(int(torch.argmax(outputs.logits, dim=-1).item()))

distilbert_pred_names = [id2label[i] for i in distilbert_pred_ids]

distilbert_acc = accuracy_score(y_test_names, distilbert_pred_names)

distilbert_p, distilbert_r, distilbert_f1, _ = precision_recall_fscore_support(
    y_test_names, distilbert_pred_names, average="macro", zero_division=0
)

distilbert_latency = distilbert_latency_total / len(X_test)

print("Accuracy:", round(distilbert_acc * 100, 2), "%")
print("Macro precision:", round(distilbert_p, 4))
print("Macro recall:", round(distilbert_r, 4))
print("Macro F1:", round(distilbert_f1, 4))
print("Latency/item:", round(distilbert_latency * 1000, 3), "ms")

print()
print(classification_report(y_test_names, distilbert_pred_names))


# ==========================================
# SIDE BY SIDE
# ==========================================

print()
print("=" * 60)
print("SIDE BY SIDE  (same test set, same 8 labels)")
print("=" * 60)

print(f"{'Metric':<18}{'TF-IDF+SVC':>16}{'DistilBERT':>16}")
print("-" * 50)
print(f"{'Accuracy':<18}{tfidf_acc * 100:>15.2f}%{distilbert_acc * 100:>15.2f}%")
print(f"{'Macro F1':<18}{tfidf_f1:>16.4f}{distilbert_f1:>16.4f}")
print(f"{'Latency (ms)':<18}{tfidf_latency * 1000:>16.3f}{distilbert_latency * 1000:>16.3f}")
print(
    f"{'Size (bytes)':<18}{os.path.getsize(TFIDF_OUT):>16}{os.path.getsize(DISTILBERT_PATH + '/model.safetensors'):>16}"
)


# ==========================================
# DISAGREEMENT ANALYSIS
# ==========================================

print()
print("=" * 60)
print("DISAGREEMENTS ON TEST SET")
print("=" * 60)

disagreements = 0

for i, text in enumerate(X_test):
    if tfidf_pred_names[i] != distilbert_pred_names[i]:
        disagreements += 1

        correct_a = tfidf_pred_names[i] == y_test_names[i]
        correct_b = distilbert_pred_names[i] == y_test_names[i]

        winner = "tie"

        if correct_a and not correct_b:
            winner = "TF-IDF"
        elif correct_b and not correct_a:
            winner = "DistilBERT"

        print()
        print("Text:", text[:150])
        print("  Truth:      ", y_test_names[i])
        print("  TF-IDF:     ", tfidf_pred_names[i], "(correct)" if correct_a else "")
        print("  DistilBERT: ", distilbert_pred_names[i], "(correct)" if correct_b else "")
        print("  Winner:     ", winner)

print()
print("Total disagreements:", disagreements, "of", len(X_test))
