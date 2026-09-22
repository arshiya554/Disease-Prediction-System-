import pandas as pd
import joblib
import numpy as np
import sqlite3

from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "disease_prediction_secret"

# Load ML model
model = joblib.load("models/disease_model.pkl")
label_encoder = joblib.load("models/label_encoder.pkl")
symptom_binarizer = joblib.load("models/symptom_binarizer.pkl")

# Load extra data
description_df = pd.read_csv("symptom_Description.csv")
precaution_df = pd.read_csv("symptom_precaution.csv")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database/users.db")
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users(username,email,password) VALUES(?,?,?)",
                (username, email, password)
            )
            conn.commit()
            return redirect("/login")

        except Exception as e:
            return render_template(
    "register.html",
    error="Username or email already exists"
)

        finally:
            conn.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database/users.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            session["username"] = username
            return redirect("/dashboard")
        else:
            return render_template(
    "login.html",
    error="Invalid username or password"
)

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    if "username" not in session:
        return redirect("/login")

    return render_template(
        "dashboard.html",
        username=session["username"]
    )

@app.route("/predict", methods=["GET", "POST"])
def predict():

    if "username" not in session:
        return redirect("/login")

    symptoms_list = sorted(symptom_binarizer.classes_)

    predicted_disease = None
    description = ""
    precautions = []
    confidence = None

    if request.method == "POST":

        symptom_list = request.form.getlist("symptoms")

        symptom_list = [
            symptom.strip().lower().replace(" ", "_")
            for symptom in symptom_list
        ]

        print("Selected symptoms:", symptom_list)

        if symptom_list:

            X = symptom_binarizer.transform([symptom_list])

            prediction = model.predict(X)

            predicted_disease = label_encoder.inverse_transform(
                prediction
            )[0]
            print("Selected symptoms:", symptom_list)
            print("Prediction:", predicted_disease)

            probabilities = model.predict_proba(X)[0]

            confidence = round(max(probabilities) * 100, 2)

            print("Predicted disease:", predicted_disease)

            symptoms = ", ".join(symptom_list)

            conn = sqlite3.connect("database/users.db")
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO prediction_history
                (username, symptoms, disease)
                VALUES (?, ?, ?)
            """, (
                session["username"],
                symptoms,
                predicted_disease
            ))

            conn.commit()
            conn.close()

            desc_row = description_df[
                description_df["Disease"] == predicted_disease
            ]

            if not desc_row.empty:
                description = desc_row.iloc[0]["Description"]

            prec_row = precaution_df[
                precaution_df["Disease"] == predicted_disease
            ]

            if not prec_row.empty:
                precautions = [
                    prec_row.iloc[0]["Precaution_1"],
                    prec_row.iloc[0]["Precaution_2"],
                    prec_row.iloc[0]["Precaution_3"],
                    prec_row.iloc[0]["Precaution_4"]
                ]

    return render_template(
        "predict.html",
        symptoms_list=symptoms_list,
        disease=predicted_disease,
        description=description,
        precautions=precautions,
        confidence=confidence
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
@app.route("/history")
def history():

    if "username" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database/users.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT symptoms, disease
        FROM prediction_history
        WHERE username = ?
        ORDER BY id DESC
    """, (session["username"],))

    data = cursor.fetchall()

    cursor.execute("""
        SELECT disease, COUNT(*) as total
        FROM prediction_history
        WHERE username = ?
        GROUP BY disease
        ORDER BY total DESC
    """, (session["username"],))

    chart_data = cursor.fetchall()

    conn.close()

    diseases = [row[0] for row in chart_data]
    counts = [row[1] for row in chart_data]

    return render_template(
        "history.html",
        history=data,
        username=session["username"],
        diseases=diseases,
        counts=counts
    )
@app.route("/delete_history")
def delete_history():
    if "username" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database/users.db")
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM prediction_history
        WHERE username = ?
    """, (session["username"],))

    conn.commit()
    conn.close()

    return redirect("/history")
if __name__ == "__main__":
    app.run(debug=True)