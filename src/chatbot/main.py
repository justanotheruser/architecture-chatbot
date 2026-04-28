from chatbot.rag import RAG
from chatbot.config import load_config
from chatbot.index.faiss import FaissIndex
from chatbot.encoder.sentence_transformer import SentenceTransformerEncoder


def chat_loop(rag: RAG):
    print("Задайте вопрос")
    while True:
        question = input()
        if question == "exit":
            break
        answer = rag.get_answer(question)
        print(answer)


if __name__ == "__main__":
    encoder = SentenceTransformerEncoder("all-MiniLM-L6-v2")
    index = FaissIndex(encoder)
    rag = RAG(config=load_config(), encoder=encoder, index=index)
    chat_loop(rag)
