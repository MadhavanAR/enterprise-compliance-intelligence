from dotenv import load_dotenv

# Load environment variables before any other imports
load_dotenv()

from rag.supervisor import supervisor

def main():
    result = supervisor({
        "question": "Research the arXiv paper 'Extending Llama-3's Context Ten-Fold Overnight' and write a dope LinkedIn post about it."
    })

    print("\nFINAL POST\n")
    print(result["final_post"])

if __name__ == "__main__":
    main()
