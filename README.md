
VocabBuild – English Vocabulary Web App

A full-featured Flask web application for enhancing English vocabulary. Users can register, login, manage their words, explore meanings, synonyms, antonyms, and generate personalized quizzes to track learning progress.

Features
User Authentication

User registration with unique username and email validation.
Login and session management.
Flash messages for feedback.
Vocabulary Management

Add, edit, delete words** from personal collection.
Words are stored **per user** in MySQL.
Display all saved words alphabetically.

Word Exploration

Word meanings using NLP (`spaCy`) + Gemini API for JSON-formatted explanations.
Part of Speech (POS) identification for each word.
Synonyms & antonyms with usage examples fetched via Gemini API.

Quiz Generation

Generate custom quizzes based on saved words.
Quiz types:
Multiple Choice (MCQ)
Fill in the Blank
Direct Question

JSON-based quiz output for frontend rendering.

User Dashboard

Personalized dashboard with word management, quiz generation, history, and progress tracking.

Backend & Database

Flask framework for routing and templates.
MySQL database for persistent storage.
Separate tables for users** and words.

NLP & AI Integration

spaCy for POS tagging.
Google Gemini API for:

Word meanings
Synonyms & antonyms
Quiz generation

Project Structure

```
vocabbuild/
│
├─ app.py                 # Main Flask application
├─ requirements.txt       # Python dependencies
├─ .env                   # Environment variables (Gemini API key)
├─ templates/             # HTML templates
│   ├─ index.html
│   ├─ register.html
│   ├─ login.html
│   ├─ dashboard.html
│   ├─ dashboard2.html
│   ├─ word_manager.html
│   ├─ search_word.html
│   ├─ synonym_page.html
│   ├─ antonym_page.html
│   ├─ generate_quizz.html
│   ├─ history.html
│   └─ progress.html
├─ static/                # CSS, JS, images
│   ├─ css/
│   └─ js/
└─ README.md              # Project documentation
```

 Installation & Setup

1. Clone the repository:

```bash
git clone https://github.com/your-username/vocabbuild.git
cd vocabbuild
```

2. Create a virtual environment (recommended):

```bash
python -m venv venv
venv\Scripts\activate   # Windows
# OR
source venv/bin/activate   # Linux / Mac
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up `.env` file:

```env
GEMINI_API_KEY=your_google_gemini_api_key
```

5. Configure MySQL database:

Database: `vocabbuild`
User table:

  ```sql
  CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    password VARCHAR(100)
  );
  ```
  Words table:

  ```sql
  CREATE TABLE words (
    id INT AUTO_INCREMENT PRIMARY KEY,
    word VARCHAR(255) UNIQUE NOT NULL,
    user_id INT,
    FOREIGN KEY (user_id) REFERENCES users(id)
  );
  ```

6. Run the app:

```bash
python app.py
```

Open in browser: [http://localhost:7000](http://localhost:7000)

Dependencies

Flask
mysql-connector-python
requests
spacy
python-dotenv
Google Gemini API (`google.generativeai`)
json, re, os (built-in)

Install spaCy model:

```bash
python -m spacy download en_core_web_sm
```

 Usage

1. Register/Login
2. Add words to your collection.
3. Search word for meaning and POS.
4. Explore synonyms/antonyms with examples.
5. Generate quizzes to test your knowledge.
6. Track progress over time.

Notes

Ensure `Gemini API key` is valid and has sufficient quota.
Only authenticated users can access vocabulary features.
JSON format is strictly enforced in AI responses for consistency.
Avoid duplicate words per user.

Future Enhancements

User password encryption (currently plain text).
Leaderboard for quiz scores.
Progress graph visualization.
Multi-language support.
Offline caching for AI responses.

