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

# — Initialize session state —
st.session_state.setdefault("sql", "")
st.session_state.setdefault("sql_placeholder", "")
st.session_state.setdefault("last_result", None)

# — Sidebar: template picker —
st.sidebar.header("Query Templates")
for template in state["templates"]:
    if st.sidebar.button(template):
        # Use template as placeholder; clear any existing text
        st.session_state["sql_placeholder"] = template
        st.session_state["sql"] = ""

# — Main UI —
st.title("QueryTheory")
st.write(f"Loaded {len(state['templates'])} SQL templates")
st.write(f"Dataset: {df.shape[0]} rows × {df.shape[1]} columns")

# — Raw dataset viewer —
with st.expander("View raw dataset"):
    st.dataframe(df)

st.subheader("SQL Editor")
sql = st.text_area(
    "Edit your SQL here",
    value=st.session_state["sql"],
    placeholder=st.session_state["sql_placeholder"],
    height=200,
    key="sql_editor"
)
st.session_state["sql"] = sql

# — Run button and persist results —
if st.button("Run Query"):
    try:
        con = duckdb.connect()
        con.register("fruit_prices_2022", df)
        result_df = con.execute(st.session_state["sql"]).df()
        st.session_state["last_result"] = result_df
    except Exception as e:
        st.error(f"Error running query:\n{e}")

# — Always show last results if they exist —
if st.session_state["last_result"] is not None:
    st.subheader("Results")
    st.dataframe(st.session_state["last_result"])

# — AI Explainer —
st.subheader("Math Explainer")
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
                "  cup_equiv_size REAL,\n"
                "  cup_equiv_unit TEXT,\n"
                "  cup_equiv_price REAL\n"
                ")"
            )
            resp = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert in relational algebra and set theory as applied to SQL. "
                            "When given a SQL query and its schema, produce:\n"
                            "  1. The equivalent relational-algebra expression.\n"
                            "  2. A step-by-step explanation of each operator in set-theoretic terms.\n"
                            "Keep it concise and focus purely on the math behind the query."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Schema:\n{schema}\n\nSQL:\n{st.session_state['sql']}"
                    }
                ]
            )
            explanation = resp.choices[0].message.content
        st.markdown("**Explanation:**")
        st.write(explanation)
    except Exception as e:
        st.error(f"Error generating explanation:\n{e}")

