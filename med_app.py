import streamlit as st
import requests
from typing import List, Dict, Optional
from pydantic import BaseModel
import base64

# --- MCP Models ---
class Message(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str

class MCPContext(BaseModel):
    user: Dict[str, str]
    history: List[Dict[str, str]]
    instructions: Optional[str] = ""
    report: Optional[str] = None
    llm: Optional[str] = None

def set_full_bg(image_file):
    with open(image_file, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        
        [data-testid="stSidebar"] > div:first-child {{
            background-color: rgba(255, 255, 255, 0);  /* transparent sidebar */
        }}
        </style>
        """,
        unsafe_allow_html=True
    )



# --- Streamlit App ---
st.set_page_config(page_title="ARTEMIS: Medical Bot", layout="wide")
st.title("🩺 ARTEMIS: Advanced Result & Test Evaluation Medical Information System")
set_full_bg("background.png")

st.markdown(
    """
    <style>
    /* Main app and all text inside it */
    .stApp {
        color: black;
    }

    .stButton > button {
        color: white !important;      /* Text colour */
        background-color: #4CAF50;    /* Optional: green background */
        border: none;                 /* Optional: no border */
    }

    .stButton > button:hover {
        background-color: #45a049;    /* Optional: hover effect */
    }

    .stDataFrame table, .stTable table {
        border: 1px solid black;
        border-collapse: collapse;
    }

    .stDataFrame td, .stDataFrame th,
    .stTable td, .stTable th {
        border: 1px solid black;
    }

    /* Headers, paragraphs, spans, and labels */
    h1, h2, h3, h4, h5, h6,
    p, span, div, label, li, a {
        color: black !important;
    }

    /* Sidebar elements */
    [data-testid="stSidebar"] * {
        color: Black !important;
    }

    .stTabs [data-testid="stHorizontalBlock"] div[role="tablist"] button {
        font-size: 20px; /* Adjust the font size as needed */
    }
    
    /* Widget labels */
    .css-1cpxqw2, .css-1cpxqw2 label, .css-1cpxqw2 span {
        color: black !important;
    }
    
    /* Change selectbox label color */
    label[data-testid="stWidgetLabel"] {
        color: white !important;
    }
    /* Change the selected value color in the selectbox */
    div[data-testid="stSelectbox"] > div[role="button"] {
        color: white !important;
        background-color: #222 !important; /* optional: dark background */
    }
    /* Change dropdown options color */
    ul[role="listbox"] li {
        color: white !important;
        background-color: #222 !important; /* optional: dark background */
    }
    /* Optional: change scrollbar color for dropdown */
    ul[role="listbox"]::-webkit-scrollbar-thumb {
        background: #444 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# Session state for chat and report
if "history" not in st.session_state:
    st.session_state["history"] = []
if "report_text" not in st.session_state:
    st.session_state["report_text"] = ""

# Sidebar: Upload report
st.sidebar.header("Upload Medical Report")
uploaded_file = st.sidebar.file_uploader("Upload (txt or PDF)", type=["txt", "pdf"])
if uploaded_file is not None:
    if uploaded_file.type == "application/pdf":
        from PyPDF2 import PdfReader
        pdf_reader = PdfReader(uploaded_file)
        st.session_state["report_text"] = "\n".join(page.extract_text() for page in pdf_reader.pages)
    else:
        st.session_state["report_text"] = uploaded_file.read().decode("utf-8")
    st.sidebar.success("Report uploaded!")

st.sidebar.header("LLM Model Selection")
llm_options = ["gemma2-9b-it", "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "qwen-qwq-32b", "compound-beta"]  
selected_llm = st.sidebar.selectbox("Choose LLM Model", llm_options)

# --- ANALYZE BUTTON ---
st.sidebar.markdown("---")
if st.sidebar.button("Analyze Report", disabled=not st.session_state["report_text"]):
    st.session_state["history"].append({
        "role": "user",
        "content": "Please analyze my medical test report and list all abnormal results, their probable causes, and remedies."
    })
    mcp_context = MCPContext(
        user={"id": "user001", "role": "user"},
        history=st.session_state["history"],
        instructions="Be concise and clear.",
        report=st.session_state["report_text"]  # <--- send report
    )
    try:
        response = requests.post("http://localhost:8000/mcp", json=mcp_context.dict())
        response.raise_for_status()
        reply = response.json()["reply"]
        st.session_state["history"].append({"role": "assistant", "content": reply})
        st.session_state["report_sent"] = True  # <--- set flag
        st.success("Analysis complete! See the chat below.")
    except Exception as e:
        st.error(f"Failed to contact MCP server: {e}")

if st.sidebar.button("Reset Chat"):
    st.session_state["history"] = []
    st.session_state["report_sent"] = False
    st.sidebar.success("Chat history has been reset!")
    
# --- CHATBOT INTERFACE ---
st.subheader("Chat with the Medical Assistant")

# Display conversation
for msg in st.session_state["history"]:
    if msg["role"] in ["user", "assistant"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
# Chat input for follow-up questions
if prompt := st.chat_input("Ask a follow-up question about your results:"):
    st.session_state["history"].append({"role": "user", "content": prompt})
    mcp_context = MCPContext(
        user={"id": "user001", "role": "user"},
        history=st.session_state["history"],
        instructions="Be concise and clear.",
        report=None if st.session_state.get("report_sent") else st.session_state["report_text"]
    )
    try:
        response = requests.post("http://localhost:8000/mcp", json=mcp_context.dict())
        response.raise_for_status()
        reply = response.json()["reply"]
        st.session_state["history"].append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)
    except Exception as e:
        st.error(f"Failed to contact MCP server: {e}")
