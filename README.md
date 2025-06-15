# QueryTheory

QueryTheory is a web-based educational app that helps users understand how SQL queries translate into relational algebra and set theory. It provides real-time query execution, mathematical explanations, and an AI-powered chat interface for deeper learning.

---

## 🧠 Features

- 🔎 **Query Templates**: Practice with 50+ categorized SQL queries.
- 🧮 **Math Explainer**: View relational algebra equivalents in LaTeX.
- 💬 **Chat Support**: Ask questions about the query’s mathematical structure.
- 🧪 **Run SQL Queries**: Execute SQL directly on a built-in dataset.
- 📊 **Live Results**: See output tables immediately after query execution.
- 📁 **Preloaded Dataset**: Work with `Fruit-Prices-2022.csv` by default.
- 🗃️ **Theory-Driven**: Designed around core relational concepts.

---

## 🧰 Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python (OpenAI API, DuckDB)
- **Data Storage**: CSV (local), JSON state
- **Configuration**: Python scripts, Streamlit secrets

---

## 📂 Project Structure

```
QueryTheory/
│
├── app.py               # Main Streamlit application
├── app_state.json       # Stores query templates & chat history
├── Fruit-Prices-2022.csv # Demo dataset for SQL queries
├── venv/                # Python virtual environment
└── README.md            # Project documentation (this file)
```

---

## ▶️ Running the App

Make sure your virtual environment is activated and required dependencies are installed.

```bash
source venv/bin/activate
streamlit run app.py
```

---

## 🔐 Configuration

Store your OpenAI API key securely in `.streamlit/secrets.toml`:

```toml
[openai]
api_key = "your_openai_key"
```

---

## 👨‍🏫 Use Cases

- CS students learning database theory
- Bootcamp participants practicing SQL
- Instructors creating theory-backed demos
- Anyone exploring how SQL maps to mathematical logic

---

## 📸 Preview

![App Screenshot](screenshot.png)

---

## 🛠️ Development

To contribute or test features:

```bash
git clone https://github.com/ThirDecade2020/QueryTheory.git
cd QueryTheory
source venv/bin/activate
streamlit run app.py
```

---

## 📜 License

MIT License © 2025 Jason Ricciardi

