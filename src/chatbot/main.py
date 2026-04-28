from chatbot.rag import RAG
from pathlib import Path
from chatbot.config import load_config
WIKI_PATH = Path(__file__).parent.parent.parent / "wiki" / "wiki"

rag = RAG(wiki_path=WIKI_PATH, config=load_config())

if __name__ == "__main__":
    print("Задайте вопрос")
    while True:
        question = input()
        if question == "exit":
            break
        answer = rag.get_answer(question)
        print(answer)