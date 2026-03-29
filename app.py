from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
import os
import requests
import spacy
import google.generativeai as genai
from dotenv import load_dotenv
import json
import re

app = Flask(__name__)
app.secret_key = "vocabbuild_secret"

# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================
dotenv_path = r"C:\Users\ASUS\AppData\Local\Programs\Python\Python312\resume scanner\.env"
load_dotenv(dotenv_path)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ============================================================
# NLP MODEL
# ============================================================
nlp = spacy.load("en_core_web_sm")

# ============================================================
# DATABASE CONFIG
# ============================================================
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="mysql",  # 🔹 Replace with your MySQL password
        database="vocabbuild"
    )

# Create tables if not exist
with get_connection() as db:
    cursor = db.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100),
        email VARCHAR(100) UNIQUE,
        password VARCHAR(100)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS words (
        id INT AUTO_INCREMENT PRIMARY KEY,
        word VARCHAR(255) UNIQUE NOT NULL
    )
    """)
    db.commit()

# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def home():
    return render_template('index.html')

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        if not name or not email or not password:
            flash("All fields are required!", "error")
        else:
            try:
                conn = get_connection()
                cursor = conn.cursor()

                # 🔹 Check if username already exists
                cursor.execute("SELECT * FROM users WHERE name = %s", (name,))
                existing_user = cursor.fetchone()
                if existing_user:
                    flash("Username already exists! Please choose another one.", "error")
                    conn.close()
                    return redirect(url_for('register'))

                # 🔹 Check if email already exists
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                existing_email = cursor.fetchone()
                if existing_email:
                    flash("Email already registered! Please use a different one.", "error")
                    conn.close()
                    return redirect(url_for('register'))

                # 🔹 Insert new user
                cursor.execute(
                    "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                    (name, email, password)
                )
                conn.commit()
                conn.close()
                flash("Registration successful! You can now login.", "success")
                return redirect(url_for('login'))
            except Exception as e:
                flash(f"Error during registration: {e}", "error")
                return redirect(url_for('register'))
    return render_template('register.html')

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_name'] = user[1]
            flash(f"Welcome back, {user[1]}!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password!", "error")
            return redirect(url_for('login'))
    return render_template('login.html')

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user_name' not in session:
        flash("Please login first!", "error")
        return redirect(url_for('login'))
    return render_template('dashboard.html', user_name=session['user_name'])

# ============================================================
# SEARCH WORD MEANING
# ============================================================
@app.route('/search_word', methods=['GET', 'POST'])
def search_word():
    if 'user_name' not in session:
        flash("Please login first!", "error")
        return redirect(url_for('login'))

    word, pos, meaning, examples = None, None, None, None

    if request.method == 'POST':
        word = request.form.get('word')
        if word:
            doc = nlp(word)
            pos = doc[0].pos_ if doc else "Unknown"

            pos_mapping = {
                "NOUN": "Noun — a person, place, thing, or idea.",
                "VERB": "Verb — an action or state of being.",
                "ADJ": "Adjective — describes a noun.",
                "ADV": "Adverb — modifies a verb, adjective, or another adverb.",
                "PRON": "Pronoun — replaces a noun.",
                "DET": "Determiner — introduces nouns.",
                "ADP": "Adposition (Preposition/Postposition).",
                "NUM": "Numeral — expresses a number or order.",
                "CONJ": "Conjunction — connects words or phrases.",
                "SCONJ": "Subordinating conjunction — introduces clauses.",
                "PART": "Particle — functional word.",
                "INTJ": "Interjection — expresses emotion.",
                "SYM": "Symbol — a sign or character.",
                "X": "Other — unclassified word type."
            }
            full_pos = pos_mapping.get(pos, pos)

            GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
            headers = {"Content-Type": "application/json"}
            data = {
                "contents": [{"parts": [{"text": f"Explain '{word}' in simple English. Respond in JSON {{meaning, examples}}"}]}]
            }

            try:
                response = requests.post(url, headers=headers, json=data, verify=False)
                response.raise_for_status()
                text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                clean_text = re.sub(r"```json|```", "", text).strip()
                parsed = json.loads(clean_text)
                meaning = parsed.get("meaning", "")
                examples = parsed.get("examples", [])
            except Exception as e:
                flash(f"Failed to fetch meaning: {e}", "error")

    return render_template('search_word.html',
                           user_name=session['user_name'],
                           word=word, pos=pos,
                           full_pos=full_pos if word else None,
                           meaning=meaning, examples=examples)

# ============================================================
# SYNONYMS PAGE (Gemini API)
# ============================================================
@app.route('/synonyms', methods=['GET', 'POST'])
def synonyms_page():
    if 'user_name' not in session:
        flash("Please login first!", "error")
        return redirect(url_for('login'))

    word, synonyms, examples = None, [], {}

    if request.method == 'POST':
        word = request.form.get('word', '').strip()
        if word:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={os.getenv('GEMINI_API_KEY')}"
                headers = {"Content-Type": "application/json"}

                prompt = f"Provide at least 15 synonyms for '{word}' in JSON format: {{'synonyms': ['a', 'b', ...]}}"
                response = requests.post(url, headers=headers, json={"contents": [{"parts": [{"text": prompt}]}]})
                clean_text = re.sub(r"```json|```", "", response.json()["candidates"][0]["content"]["parts"][0]["text"]).strip()
                parsed = json.loads(clean_text)
                synonyms = [s for s in parsed.get("synonyms", []) if s.lower() != word.lower()]

                if synonyms:
                    top_syns = ", ".join(synonyms[:5])
                    ex_prompt = f"Write one sentence each for these synonyms: {top_syns}. Respond in JSON {{synonym: example}}"
                    response_ex = requests.post(url, headers=headers, json={"contents": [{"parts": [{"text": ex_prompt}]}]})
                    clean_text_ex = re.sub(r"```json|```", "", response_ex.json()["candidates"][0]["content"]["parts"][0]["text"]).strip()
                    examples = json.loads(clean_text_ex)
            except Exception as e:
                flash(f"Gemini API error: {e}", "error")

    return render_template('synonym_page.html', user_name=session['user_name'], word=word, synonyms=synonyms, examples=examples)

# ============================================================
# ANTONYMS PAGE (Gemini API)
# ============================================================
@app.route('/antonyms', methods=['GET', 'POST'])
def antonyms_page():
    if 'user_name' not in session:
        flash("Please login first!", "error")
        return redirect(url_for('login'))

    word, antonyms, examples = None, [], {}

    if request.method == 'POST':
        word = request.form.get('word', '').strip()
        if word:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={os.getenv('GEMINI_API_KEY')}"
                headers = {"Content-Type": "application/json"}

                prompt = f"Provide at least 15 antonyms for '{word}' in JSON format: {{'antonyms': ['a', 'b', ...]}}"
                response = requests.post(url, headers=headers, json={"contents": [{"parts": [{"text": prompt}]}]})
                clean_text = re.sub(r"```json|```", "", response.json()["candidates"][0]["content"]["parts"][0]["text"]).strip()
                parsed = json.loads(clean_text)
                antonyms = [a for a in parsed.get("antonyms", []) if a.lower() != word.lower()]

                if antonyms:
                    top_ants = ", ".join(antonyms[:5])
                    ex_prompt = f"Write one sentence each for these antonyms: {top_ants}. Respond in JSON {{antonym: example}}"
                    response_ex = requests.post(url, headers=headers, json={"contents": [{"parts": [{"text": ex_prompt}]}]})
                    clean_text_ex = re.sub(r"```json|```", "", response_ex.json()["candidates"][0]["content"]["parts"][0]["text"]).strip()
                    examples = json.loads(clean_text_ex)
            except Exception as e:
                flash(f"Gemini API error: {e}", "error")

    return render_template('antonym_page.html', user_name=session['user_name'], word=word, antonyms=antonyms, examples=examples)

# ============================================================
# WORD MANAGER (Add/Edit/Delete Words)
# ============================================================
@app.route('/word_manager')
def word_manager():
    if 'user_name' not in session:
        flash("Please login first!", "error")
        return redirect(url_for('login'))

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT word FROM words ORDER BY word ASC")
    all_words = [row[0] for row in c.fetchall()]
    conn.close()
    return render_template('word_manager.html', words=all_words, user_name=session['user_name'])

# ============================================================
# ADD / DELETE / EDIT WORDS
# ============================================================
@app.route('/add', methods=['POST'])
def add_word():
    if 'user_name' not in session:
        return jsonify({'success': False, 'message': 'Please login first!'})

    data = request.get_json()
    word = data.get('word', '').strip()
    if not word:
        return jsonify({'success': False, 'message': 'Word cannot be empty!'})

    conn = get_connection()
    c = conn.cursor()

    # Get user_id from session
    c.execute("SELECT id FROM users WHERE name = %s", (session['user_name'],))
    user_id = c.fetchone()[0]

    try:
        c.execute("INSERT INTO words (word, user_id) VALUES (%s, %s)", (word, user_id))
        conn.commit()
        message = f"'{word}' added successfully!"
        success = True
    except mysql.connector.IntegrityError:
        message = f"'{word}' already exists!"
        success = False
    conn.close()
    return jsonify({'success': success, 'message': message})

@app.route('/delete', methods=['POST'])
def delete_word():
    if 'user_name' not in session:
        return jsonify({'success': False, 'message': 'Please login first!'})

    data = request.get_json()
    word = data.get('word')

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE name = %s", (session['user_name'],))
    user_id = c.fetchone()[0]

    c.execute("DELETE FROM words WHERE word = %s AND user_id = %s", (word, user_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f"'{word}' deleted!"})


@app.route('/edit', methods=['POST'])
def edit_word():
    if 'user_name' not in session:
        return jsonify({'success': False, 'message': 'Please login first!'})

    data = request.get_json()
    old_word = data.get('old_word')
    new_word = data.get('new_word').strip()

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE name = %s", (session['user_name'],))
    user_id = c.fetchone()[0]

    c.execute("UPDATE words SET word = %s WHERE word = %s AND user_id = %s", (new_word, old_word, user_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f"'{old_word}' updated to '{new_word}'"})


@app.route('/display', methods=['GET'])
def display_words():
    if 'user_name' not in session:
        return jsonify({'words': []})

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE name = %s", (session['user_name'],))
    user_id = c.fetchone()[0]

    c.execute("SELECT word FROM words WHERE user_id = %s ORDER BY word ASC", (user_id,))
    words = [row[0] for row in c.fetchall()]
    conn.close()
    return jsonify({'words': words})

@app.route("/dashboard2")
def dashboard2():
    if 'user_name' not in session:
        flash("Please login first!", "error")
        return redirect(url_for('login'))
   
    return render_template("dashboard2.html", user_name=session['user_name'])

# ============================================================
# GENERATE QUIZ (based on saved words)
# ============================================================
@app.route('/quiz')
def quiz_page():
    if 'user_name' not in session:
        return redirect(url_for('login'))
    return render_template('generate_quizz.html', user_name=session['user_name'])

@app.route('/history')
def history():
    if 'user_name' not in session:
        return redirect(url_for('login'))
    return render_template('history.html', user_name=session['user_name'])

@app.route('/progress')
def progress():
    if 'user_name' not in session:
        return redirect(url_for('login'))
    return render_template('progress.html', user_name=session['user_name'])



@app.route('/generate_quiz', methods=['POST'])
def generate_quiz():
    if 'user_name' not in session:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    count = int(data.get("count", 10))

    # Get the current user's ID
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE name = %s", (session['user_name'],))
    user = c.fetchone()
    if not user:
        conn.close()
        return jsonify({"questions": []})
    user_id = user[0]

    # Fetch only this user's words
    c.execute("SELECT word FROM words WHERE user_id = %s ORDER BY RAND() LIMIT %s", (user_id, count))
    words = [row[0] for row in c.fetchall()]
    conn.close()

    if not words:
        return jsonify({"questions": []})

    # 🔹 Stronger prompt — only mcq, fillup, direct (no match)
    prompt = (
    f"Generate {count} English vocabulary quiz questions "
    f"based only on these words: {', '.join(words)}.\n\n"
    f"Use only the following question types: 'mcq', 'fillup', and 'direct'.\n"
    f"Do NOT include 'match' or any other type.\n\n"
    f"Each question should test one of these aspects:\n"
    f"  - Word meaning or usage\n"
    f"  - Synonyms (same meaning)\n"
    f"  - Antonyms (opposite meaning)\n\n"
    f"For each question, return a JSON object with:\n"
    f"  - 'type': one of mcq, fillup, or direct\n"
    f"  - 'prompt': the question text\n"
    f"  - 'options': an array of 4 options (for all mcq, fillup and direct type)\n"
    f"  - 'correctAnswer': the exact correct answer string\n\n"
    f"Ensure the response is a VALID JSON ARRAY ONLY with no explanations, code blocks, or markdown.\n"
    f"Make questions short, clear, and beginner-friendly."
)


    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        res = requests.post(url, headers=headers, json=payload)
        res.raise_for_status()

        text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
        clean_text = re.sub(r"```json|```", "", text).strip()
        questions = json.loads(clean_text)

        if not isinstance(questions, list):
            raise ValueError("Response is not a list")

    except Exception as e:
        print("❌ Quiz generation error:", e)
        return jsonify({"questions": []})

    return jsonify({"questions": questions})

    
# ============================================================
# RUN APP
# ============================================================
if __name__ == '__main__':
    app.run(debug=True, port=7000)
