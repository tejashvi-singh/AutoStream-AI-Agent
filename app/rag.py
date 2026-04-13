import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

# Resolve path to knowledge_base.md relative to this file
KB_PATH = os.path.join(os.path.dirname(__file__), "..", "knowledge_base.md")

def get_retriever():
    """
    Creates and returns a FAISS retriever based on the local knowledge base.
    """
    loader = TextLoader(KB_PATH)
    docs = loader.load()

    # Text splitter config
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    splits = text_splitter.split_documents(docs)

    # Free local embeddings via HuggingFace
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # FIX: FAISS.from_documents takes positional args (not docs= keyword)
    vectorstore = FAISS.from_documents(splits, embeddings)
    return vectorstore.as_retriever(search_kwargs={"k": 3})


# Lazy-initialized global retriever (avoid reloading on every request)
_RETRIEVER = None


def get_rag_chain():
    """
    Returns a Runnable RAG chain that takes a question string and returns a string answer.
    """
    global _RETRIEVER
    if _RETRIEVER is None:
        _RETRIEVER = get_retriever()

    # FIX: use 'model' not 'model_name' for ChatGroq
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

    template = """You are a helpful AutoStream AI sales assistant. Use the context below from AutoStream's knowledge base to answer the question accurately and concisely.
If the answer is not in the context, just say you don't know.

Context:
{context}

Question: {question}

Answer:"""
    custom_rag_prompt = PromptTemplate.from_template(template)

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain = (
        {"context": _RETRIEVER | format_docs, "question": RunnablePassthrough()}
        | custom_rag_prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain
