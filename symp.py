import joblib

mlb = joblib.load("models/symptom_binarizer.pkl")

print(sorted(mlb.classes_))