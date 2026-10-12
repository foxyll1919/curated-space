import json
import os
import time

import joblib
import pandas as pd
import torch

from sklearn.metrics import accuracy_score, precision_recall_fscore_support

from transformers import AutoTokenizer, AutoModelForSequenceClassification


# ==========================================
# CONFIG
# ==========================================

ML_DIR = "curated_space_ml"

DISTILBERT_PATH = f"{ML_DIR}/models/curated-space-distilbert"

TFIDF_PATH = "ml/model/curated_space_classifier.pkl"

EVAL_CSV = "ml/dataset/realistic_eval.csv"


# ==========================================
# LOAD
# ==========================================

with open(f"{ML_DIR}/data/processed/labels.json", "r", encoding="utf-8") as f:
    label_data = json.load(f)


id2label = {int(index): label for index, label in label_data["id2label"].items()}


eval_df = pd.read_csv(EVAL_CSV)

eval_df["tags"] = eval_df["tags"].fillna("")

print("=" * 64)
print("REALISTIC EVAL SET (held out - never trained on)")
print("=" * 64)
print("Items:", len(eval_df))
print()
print(eval_df["category"].value_counts().to_string())


def build_text(row, use_tags):

    tags = str(row["tags"]).strip()

    if use_tags and tags:
        return f"Title: {row['title']}. Description: {row['description']}. Tags: {tags}"

    return f"Title: {row['title']}. Description: {row['description']}. Tags: "


# ==========================================
# MODEL A: TF-IDF + LinearSVC
# ==========================================

tfidf_model = joblib.load(TFIDF_PATH)


# ==========================================
# MODEL B: DistilBERT
# ==========================================

tokenizer = AutoTokenizer.from_pretrained(DISTILBERT_PATH)

distilbert = AutoModelForSequenceClassification.from_pretrained(DISTILBERT_PATH)

distilbert.eval()


def predict_tfidf(texts):

    return [id2label[int(i)] for i in tfidf_model.predict(texts)]


def predict_distilbert(texts):

    results = []

    with torch.no_grad():
        for text in texts:
            inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=256)

            outputs = distilbert(**inputs)

            predicted_id = int(torch.argmax(outputs.logits, dim=-1).item())

            results.append(id2label[predicted_id])

    return results


def report(name, truth, preds_a, preds_b):

    print()
    print("=" * 64)
    print(name)
    print("=" * 64)

    _, _, f1_a, _ = precision_recall_fscore_support(
        truth, preds_a, average="macro", zero_division=0
    )

    _, _, f1_b, _ = precision_recall_fscore_support(
        truth, preds_b, average="macro", zero_division=0
    )

    acc_a = accuracy_score(truth, preds_a)
    acc_b = accuracy_score(truth, preds_b)

    print(f"{'Category':<14}{'Support':>9}{'TF-IDF':>10}{'DistilBERT':>13}")
    print("-" * 46)

    for category in sorted(set(truth)):
        mask = [t == category for t in truth]

        correct_a = sum(1 for i, m in enumerate(mask) if m and preds_a[i] == category)

        correct_b = sum(1 for i, m in enumerate(mask) if m and preds_b[i] == category)

        print(f"{category:<14}{sum(mask):>9}{correct_a:>10}{correct_b:>13}")

    print("-" * 46)
    print(f"{'Accuracy':<14}{len(truth):>9}{acc_a * 100:>9.2f}%{acc_b * 100:>12.2f}%")
    print(f"{'Macro F1':<14}{'':>9}{f1_a:>10.4f}{f1_b:>13.4f}")

    both = sum(1 for i in range(len(truth)) if preds_a[i] == preds_b[i])

    print(f"{'Agreement':<14}{'':>9}{both / len(truth) * 100:>9.2f}%")

    return {
        "acc_a": acc_a,
        "acc_b": acc_b,
        "f1_a": f1_a,
        "f1_b": f1_b,
        "preds_a": preds_a,
        "preds_b": preds_b,
    }


# ==========================================
# RUN BOTH CONDITIONS
# ==========================================

truth = eval_df["category"].tolist()

summary = []

for use_tags in (True, False):
    texts = [build_text(row, use_tags) for _, row in eval_df.iterrows()]

    t0 = time.perf_counter()

    preds_a = predict_tfidf(texts)

    tfidf_time = (time.perf_counter() - t0) / len(texts)

    t0 = time.perf_counter()

    preds_b = predict_distilbert(texts)

    distilbert_time = (time.perf_counter() - t0) / len(texts)

    label = (
        "CONDITION 1: title + description + tags"
        if use_tags
        else "CONDITION 2: title + description only (tags stripped)"
    )

    result = report(label, truth, preds_a, preds_b)

    result["label"] = label
    result["short"] = "with tags" if use_tags else "tags stripped"
    result["tfidf_time"] = tfidf_time
    result["distilbert_time"] = distilbert_time

    summary.append(result)

    print()
    print(
        f"Latency/item  TF-IDF {tfidf_time * 1000:.3f} ms"
        f"   DistilBERT {distilbert_time * 1000:.3f} ms"
    )

    print()
    print("-" * 64)
    print("EVERY ITEM WHERE THEY DISAGREE OR BOTH FAIL")
    print("-" * 64)

    for i, text in enumerate(eval_df["title"].tolist()):
        correct_a = preds_a[i] == truth[i]
        correct_b = preds_b[i] == truth[i]

        if correct_a and correct_b:
            continue

        winner = "both wrong"

        if correct_a:
            winner = "TF-IDF correct"
        elif correct_b:
            winner = "DistilBERT correct"

        print()
        print(f"[{winner}]")
        print("  Title:     ", text)
        print("  Truth:     ", truth[i])
        print("  TF-IDF:    ", preds_a[i])
        print("  DistilBERT:", preds_b[i])


# ==========================================
# FINAL SUMMARY
# ==========================================

print()
print("=" * 64)
print("SUMMARY")
print("=" * 64)

print(f"{'Condition':<52}{'TF-IDF':>10}{'DistilBERT':>12}")
print("-" * 74)

for result in summary:
    print(f"{result['short']:<52}{result['acc_a'] * 100:>9.2f}%{result['acc_b'] * 100:>11.2f}%")

print("-" * 74)

print()
print("TF-IDF model size:", os.path.getsize(TFIDF_PATH), "bytes")
print("DistilBERT model size:", os.path.getsize(DISTILBERT_PATH + "/model.safetensors"), "bytes")
