import joblib


# Load trained model
model = joblib.load(
    "ml/model/curated_space_classifier.pkl"
)


# New content
text = """
React JWT Authentication Tutorial.
A step-by-step guide explaining how to implement
JWT authentication in a React application.
Tags: React, JWT, Authentication, JavaScript
"""


# Predict category
prediction = model.predict([text])[0]


print("Predicted Category:", prediction)