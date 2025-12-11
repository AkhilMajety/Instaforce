import json
import streamlit as st
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferMemory
from langchain_classic.prompts import PromptTemplate
from pathlib import Path
import pickle
from dotenv import load_dotenv
import os
import chardet 


load_dotenv() 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# ===== CONFIG =====
ORG_JSON_PATH = "org_analysis_3.json"
INDEX_PATH = "org_vector_index"
OPENAI_MODEL = "gpt-4o-mini"  # you can use gpt-4-turbo, gpt-4o, etc.

# ===== SETUP PAGE =====
st.set_page_config(page_title="SFMind", page_icon="🤖", layout="wide")
st.title("💬 SFMind")
st.caption("Chat with your Salesforce Org and metadata using OpenAI + LangChain")

# ===== LOAD ORG DATA =====

@st.cache_resource
def load_faiss():
    index_path = Path("org_vector_index")

    # If index already exists — load it directly
    
    if index_path.exists():
        print("-------------vector db found----------")
        st.info("🔁 Using existing FAISS vector index...")
        db = FAISS.load_local(
            index_path,
            OpenAIEmbeddings(),
            allow_dangerous_deserialization=True
        )
        return db

    # Otherwise, build new FAISS index from org_analysis.json
    
    st.warning("⚙️ Building new FAISS vector index (first run)...")
    # with open(ORG_JSON_PATH, "r", encoding="utf-8") as f:
    #     data = json.load(f)
    with open(ORG_JSON_PATH, "rb") as f:
      raw = f.read()

    # detected_encoding = chardet.detect(raw_data)["encoding"] or "utf-8"
    # print(f"🔍 Detected file encoding: {detected_encoding}")
    enc = chardet.detect(raw)["encoding"] or "utf-8"
    data = json.loads(raw.decode(enc, errors="ignore"))

    with open("org_analysis.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("✅ Re-saved org_analysis.json in UTF-8 encoding.")

    # data = json.loads(raw_data.decode(detected_encoding, errors="ignore"))
    if isinstance(data, dict):
        print("-------------vector db not found----------")

        data = [data]

    texts, metadata = [], []
    for item in data:
        if isinstance(item, dict) and "class_name" in item:
            summary = (
                f"Class: {item.get('class_name', '')}\n"
                f"Description: {item.get('purpose', item.get('description', ''))}\n"
                f"Methods: {json.dumps(item.get('methods', []))}\n"
                f"SOQL: {json.dumps(item.get('soql_queries', item.get('soql_operations', [])))}\n"
                f"DML: {json.dumps(item.get('dml_operations', []))}\n"
                f"Related Objects: {json.dumps(item.get('related_objects', item.get('other_objects_or_triggers_referenced', [])))}\n"
                f"Issues: {json.dumps(item.get('issues', item.get('potential_errors_or_best_practice_issues', [])))}"
            )
        else:
            summary = json.dumps(item, ensure_ascii=False)
        texts.append(summary)
        metadata.append({"file": item.get("file", "unknown") if isinstance(item, dict) else "unknown"})

    embeddings = OpenAIEmbeddings()
    db = FAISS.from_texts(texts, embeddings, metadatas=metadata)
    db.save_local(index_path)

    st.success("✅ New FAISS index created and saved!")
    return db


@st.cache_resource
def get_chain():
    db = load_faiss()
    retriever = db.as_retriever(search_kwargs={"k": 5})
    memory = ConversationBufferMemory(memory_key
    ="chat_history", return_messages=True)

    custom_prompt = PromptTemplate.from_template("""
    You are an expert Salesforce Apex assistant.
    Use the context below (from the org analysis) to answer clearly and helpfully.
    If the context lacks the answer, use your Salesforce knowledge to infer a likely response.

    CONTEXT:
    {context}

    QUESTION:
    {question}

    Respond in markdown with clear explanations.
    """)

    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0.3)
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": custom_prompt},
        verbose=False
    )

# ===== MAIN CHAT =====
qa_chain = get_chain()

# Initialize chat history in Streamlit session
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.markdown("---")

query = st.text_input("💭 Ask your Salesforce Org a question:", placeholder="e.g. What does DivisionBudgetCalculatorr class do?")

if query:
    with st.spinner("Thinking... 🤔"):
        response = qa_chain.invoke({"question": query})
        answer = response["answer"]

    st.session_state.chat_history.append(("You", query))
    st.session_state.chat_history.append(("AI", answer))

st.markdown("### 🗨️ Chat History")
for role, msg in st.session_state.chat_history:
    if role == "You":
        st.markdown(f"**🧑 {role}:** {msg}")
    else:
        st.markdown(f"**🤖 {role}:** {msg}")

st.markdown("---")
st.caption("Built by Akhil — powered by LangChain + OpenAI 🚀")
