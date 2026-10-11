import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report


# --------------------------------
# 1. Load dataset
# --------------------------------

df = pd.read_csv("ml/dataset/curated_space_dataset.csv")

print("Total examples:", len(df))
print("\nCategory distribution:")
print(df["category"].value_counts())


# --------------------------------
# 2. Separate input and output
# --------------------------------

X = df["text"]
y = df["category"]


# --------------------------------
# 3. Split dataset
# --------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining examples:", len(X_train))
print("Testing examples:", len(X_test))


# --------------------------------
# 4. Create ML pipeline
# --------------------------------

model = Pipeline([
    ("tfidf", TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2)
    )),

    ("svm", LinearSVC())
])


# --------------------------------
# 5. Train the model
# --------------------------------

print("\nTraining model...")

model.fit(X_train, y_train)

print("Training completed!")


# --------------------------------
# 6. Test the model
# --------------------------------

predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print("\nAccuracy:", round(accuracy * 100, 2), "%")

print("\nClassification Report:")
print(classification_report(y_test, predictions))


# --------------------------------
# 7. Save trained model
# --------------------------------

joblib.dump(model, "ml/model/curated_space_classifier.pkl")

print("\nModel saved successfully!")
print("Location: ml/model/curated_space_classifier.pkl")