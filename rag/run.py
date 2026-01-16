from dotenv import load_dotenv
from rag.supervisor import build_supervisor

load_dotenv()

app = build_supervisor()

result = app.invoke({
    "question": "Did the Edmonton Oilers win the 2025 Stanley Cup?"
})

print("\nFINAL ANSWER\n")
print(result["answer"])
