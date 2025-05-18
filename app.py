import streamlit as st
import json
from pathlib import Path
import pandas as pd
import duckdb
import openai

# — Load OpenAI key from Streamlit secrets —
openai.api_key = st.secrets["openai"]["api_key"]

# — Load app state —
STATE_PATH = Path("app_state.json")
state = json.loads(STATE_PATH.read_text())

# — Load practice dataset —
df = pd.read_csv("Fruit-Prices-2022.csv")

# — Normalize CamelCase headers → snake_case so SQL templates match —
df.columns = (
    df.columns
      .str.replace(r'([a-z0-9])([A-Z])', r'\1_\2', regex=True)  # e.g. RetailPrice → Retail_Price
      .str.replace(r'\s+', '_', regex=True)                      # spaces → underscores
      .str.lower()                                               # lowercase all
)

# — Initialize session state —
st.session_state.setdefault("sql", "")
st.session_state.setdefault("last_result", None)
st.session_state.setdefault("chat_history", [])

# — Sidebar: template picker —
st.sidebar.header("Query Templates")
for template in state["templates"]:
    if st.sidebar.button(template):
        st.session_state["sql"] = template

# — Main UI —
st.title("QueryTheory")
st.write(f"Loaded {len(state['templates'])} SQL templates")
st.write(f"Dataset: {df.shape[0]} rows × {df.shape[1]} columns")

# — Raw dataset viewer —
with st.expander("View raw dataset"):
    st.dataframe(df)

# — SQL Editor —
st.subheader("SQL Editor")
sql = st.text_area(
    "Edit your SQL here",
    value=st.session_state["sql"],
    height=200,
    key="sql_editor"
)
st.session_state["sql"] = sql

# — Run button and persist results —
if st.button("Run Query"):
    try:
        con = duckdb.connect()
        con.register("fruit_prices_2022", df)
        st.session_state["last_result"] = con.execute(st.session_state["sql"]).df()
    except Exception as e:
        st.error(f"Error running query:\n{e}")

# — Always show last results —
if st.session_state["last_result"] is not None:
    st.subheader("Results")
    st.dataframe(st.session_state["last_result"])

# — AI Explainer & Chat —
st.subheader("Math Explainer")

# Initial explanation
if st.button("Discover Mathematical Underpinnings"):
    try:
        with st.spinner("Generating explanation…"):
            schema = (
                "fruit_prices_2022(\n"
                "  fruit TEXT,\n"
                "  form TEXT,\n"
                "  retail_price REAL,\n"
                "  retail_price_unit TEXT,\n"
                "  yield REAL,\n"
                "  cup_equivalent_size REAL,\n"
                "  cup_equivalent_unit TEXT,\n"
                "  cup_equivalent_price REAL\n"
                ")"
            )
            system_msg = {
                "role": "system",
                "content": (
                    "You are an expert in relational algebra and set theory as applied to SQL. "
                    "Given a SQL query and its schema, provide:\n"
                    "1. The equivalent relational-algebra expression.\n"
                    "2. A step-by-step explanation of each operator in set-theoretic terms.\n"
                    "Be concise and math-focused."
                )
            }
            user_msg = {
                "role": "user",
                "content": f"Schema:\n{schema}\n\nSQL:\n{st.session_state['sql']}"
            }
            resp = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[system_msg, user_msg]
            )
            explanation = resp.choices[0].message.content

        st.session_state["chat_history"] = [
            system_msg,
            user_msg,
            {"role": "assistant", "content": explanation},
        ]
    except Exception as e:
        st.error(f"Error generating explanation:\n{e}")

# Display conversation (excluding system)
for msg in st.session_state["chat_history"]:
    if msg["role"] in ("user", "assistant"):
        st.chat_message(msg["role"]).write(msg["content"])

# Follow-up questions
if st.session_state["chat_history"]:
    followup = st.chat_input("Ask about the explanation…")
    if followup:
        try:
            st.session_state["chat_history"].append({"role": "user", "content": followup})
            with st.spinner("Waiting for response…"):
                resp2 = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=st.session_state["chat_history"]
                )
                reply = resp2.choices[0].message.content
            st.session_state["chat_history"].append({"role": "assistant", "content": reply})
        except Exception as e:
            st.error(f"Error generating follow-up response:\n{e}")

