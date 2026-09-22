import pandas as pd
import joblib

from sklearn.preprocessing import MultiLabelBinarizer, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Load dataset
df = pd.read_csv("dataset.csv")

# Clean column names
df.columns = df.columns.str.strip()

# Symptom columns
symptom_cols = [f"Symptom_{i}" for i in range(1, 18)]

symptom_data = []

for _, row in df.iterrows():

    symptoms = []

    for col in symptom_cols:

        value = str(row[col]).strip().lower()

        if value != "nan" and value != "":
            # Standardize symptom names
            value = value.replace(" ", "_")
            symptoms.append(value)

    # Remove duplicates from each row
    symptoms = list(set(symptoms))

    symptom_data.append(symptoms)

# Convert symptoms to binary features
mlb = MultiLabelBinarizer()
X = mlb.fit_transform(symptom_data)

# Encode diseases
le = LabelEncoder()
y = le.fit_transform(df["Disease"].str.strip())

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# Train model
model = RandomForestClassifier(
    n_estimators=500,
    max_depth=None,
    min_samples_split=2,
    min_samples_leaf=1,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

# Evaluate model
y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)

print(f"Model Accuracy: {accuracy * 100:.2f}%")

# Save model and encoders
joblib.dump(model, "models/disease_model.pkl")
joblib.dump(le, "models/label_encoder.pkl")
joblib.dump(mlb, "models/symptom_binarizer.pkl")

print("Model trained successfully!")