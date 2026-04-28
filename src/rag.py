class RAG:
    def __init__(self):
        pass

    def get_answer(self, question: str) -> str:
        context_chunks = self.get_context(question)
        prompt = self.build_prompt(question, context_chunks)
        answer = self.get_answer_from_llm(prompt)
        return answer

    def get_context(self, question: str) -> list[str]:
        return []

    def build_prompt(self, question: str, context_chunks: list[str]) -> str:
        return ""

    def get_answer_from_llm(self, prompt: str) -> str:
        return ""