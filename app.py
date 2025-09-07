from flask import Flask, render_template, request
import sqlite3
import requests
import spacy
import re
import os

app = Flask(__name__)

# N8N webhook URL (replace with your public n8n webhook URL for deployment)
N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/user-subscribe")

# Initialize spaCy
nlp = spacy.load("en_core_web_sm")

# Custom keywords
crime_keywords = ["murder", "robbery", "theft", "assault", "rape", "kidnap", "fraud", "arson"]
weapon_keywords = ["knife", "gun", "pistol", "rifle", "sword"]
vehicle_keywords = ["car", "bike", "van", "truck", "bus"]

# Initialize SQLite DB
def init_db():
    conn = sqlite3.connect("crime_alert.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        location TEXT,
        crime_type TEXT,
        subscribe BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

# Function to send data to n8n webhook
def send_to_n8n(name, email, location, crime_type):
    payload = {
        "name": name,
        "email": email,
        "location": location,
        "crime_type": crime_type
    }
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload)
        print("Webhook response:", response.status_code, response.text)
    except Exception as e:
        print("Error sending to n8n:", e)

# Function: Extract NER entities from description
def extract_entities(text):
    doc = nlp(text)
    entities = {}

    # SpaCy built-in entities
    for ent in doc.ents:
        label = ent.label_
        entities.setdefault(label, []).append(ent.text)

    # Custom crime type detection
    for word in crime_keywords:
        if re.search(rf"\b{word}\b", text, re.IGNORECASE):
            entities.setdefault("CRIME_TYPE", []).append(word)

    # Custom weapons
    for word in weapon_keywords:
        if re.search(rf"\b{word}\b", text, re.IGNORECASE):
            entities.setdefault("WEAPON", []).append(word)

    # Custom vehicles
    for word in vehicle_keywords:
        if re.search(rf"\b{word}\b", text, re.IGNORECASE):
            entities.setdefault("VEHICLE", []).append(word)

    # Deduplicate values
    for key in entities:
        entities[key] = list(set(entities[key]))

    return entities

# Route: Home page with form
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

# Route: Handle alert form submission
@app.route("/alert", methods=["POST"])
def alert():
    name = request.form.get("name", "Anonymous")
    email = request.form.get("email")
    location = request.form.get("location", "Unknown")
    crime_type = request.form.get("crime_type", "Unknown")
    
    # Save user in SQLite DB
    try:
        conn = sqlite3.connect("crime_alert.db")
        c = conn.cursor()
        c.execute("""
            INSERT OR IGNORE INTO users (name, email, location, crime_type)
            VALUES (?, ?, ?, ?)
        """, (name, email, location, crime_type))
        conn.commit()
        conn.close()
    except Exception as e:
        print("DB error:", e)
    
    # Send data to n8n webhook
    send_to_n8n(name, email, location, crime_type)
    
    return "Subscription received! You will get alerts shortly."

# Route: Handle NER form submission
@app.route("/ner", methods=["POST"])
def ner():
    description = request.form.get("description", "")
    entities = extract_entities(description)
    return render_template("ner_result.html", entities=entities)

if __name__ == "__main__":
    init_db()  # Create DB if not exists
    # Use host 0.0.0.0 and dynamic PORT for deployment
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
