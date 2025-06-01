import streamlit as st
import json
from pathlib import Path
import pandas as pd
import duckdb
import openai
import re

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
for tpl in state["templates"]:
    tooltip = f'SQL: {tpl["sql"]}\nCategory: {tpl["category"]}'
    if st.sidebar.button(tpl["label"], help=tooltip):
        st.session_state["sql"] = tpl["sql"]

# — Main UI —
st.title("QueryTheory")
st.write(f"Loaded {len(state['templates'])} SQL templates")
st.write(f"Dataset: {df.shape[0]} rows × {df.shape[1]} columns")

# — Raw dataset viewer —
with st.expander("View raw dataset"):
    st.dataframe(df)

# — SQL Editor —
st.subheader("SQL Editor")

# Show the selected query as a faint reference above the editor
if st.session_state["sql"]:
    st.markdown(
        "<div style='color:#999;font-size:14px;'>Type this query for practice:</div>"
        f"<div style='color:#bbb;font-family:monospace;font-size:14px;padding:4px 0 8px 0;'>{st.session_state['sql']}</div>",
        unsafe_allow_html=True
    )

# Insert Query Example button
if st.session_state["sql"] and st.button("Insert Query Example"):
    st.session_state["sql_editor"] = st.session_state["sql"]
    st.rerun()

# Initialize the editor's session state if not present
if "sql_editor" not in st.session_state:
    st.session_state["sql_editor"] = ""

# The editor uses only session state
user_sql = st.text_area(
    "Edit your SQL here",
    key="sql_editor",
    height=200,
)

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
            
            # 1. Get LaTeX math expression
            system_msg_math = {
                "role": "system",
                "content": (
                    "You are an expert in relational algebra and set theory as applied to SQL. "
                    "Given a SQL query and its schema, provide only the equivalent relational-algebra expression in LaTeX math. "
                    "Do NOT explain, do NOT wrap in markdown. Output only the LaTeX code."
                )
            }
            user_msg_math = {
                "role": "user",
                "content": f"Schema:\n{schema}\n\nSQL:\n{st.session_state['sql']}"
            }
            resp_math = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[system_msg_math, user_msg_math]
            )
            latex_math = resp_math.choices[0].message.content.strip()
            latex_math = re.sub(r"^```(?:latex)?\s*", "", latex_math)
            latex_math = re.sub(r"\s*```$", "", latex_math)

            # 2. Get plain English explanation only (NO raw math in response)
            system_msg_exp = {
                "role": "system",
                "content": (
                    "You are an expert in relational algebra and set theory as applied to SQL. "
                    "Given a SQL query and its schema, explain in clear plain English how the query maps to relational algebra and set theory, step by step. "
                    "Do NOT include the LaTeX or raw relational-algebra expression. Only explain in words."
                )
            }
            user_msg_exp = {
                "role": "user",
                "content": f"Schema:\n{schema}\n\nSQL:\n{st.session_state['sql']}"
            }
            resp_exp = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[system_msg_exp, user_msg_exp]
            )
            explanation = resp_exp.choices[0].message.content.strip()
        
        # Show the schema and SQL
        st.success(f"Schema:\n{schema}\n\nSQL: {st.session_state['sql']}")

        # Show the LaTeX math, rendered as math
        st.markdown("#### Mathematical Expression Equivalent:")
        st.latex(latex_math)
        st.markdown("_Legend: π = projection, σ = selection, ⋈ = join, × = cross product_", unsafe_allow_html=True)

        # Show the explanation in plain English
        st.markdown("**Step-by-step explanation:**")
        st.info(explanation)

        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []

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

