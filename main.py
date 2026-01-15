from rag.graph import app
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    result = app.invoke(
        {"question": "Explain BM25 keyword search in RAG systems"}
    )
    print(result["answer"])
