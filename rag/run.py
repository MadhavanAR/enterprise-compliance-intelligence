from dotenv import load_dotenv

# Load environment variables before any other imports
load_dotenv()

from rag.graph import app

def main():
    result = app.invoke(
        {"question": "Explain BM25 keyword search in RAG systems"}
    )

    print("\nFINAL ANSWER\n")
    print(result["answer"])

if __name__ == "__main__":
    main()