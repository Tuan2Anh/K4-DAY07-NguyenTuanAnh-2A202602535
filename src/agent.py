from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        if self.store.get_collection_size() == 0:
            return "Không tìm thấy thông tin trong cơ sở tri thức vì cơ sở tri thức hiện đang rỗng."

        results = self.store.search(question, top_k=top_k)
        if not results:
            return "Không tìm thấy thông tin phù hợp trong cơ sở tri thức để trả lời câu hỏi."

        context_blocks = []
        for i, res in enumerate(results, start=1):
            source = (
                res.get("metadata", {}).get("source")
                or res.get("metadata", {}).get("doc_id")
                or res.get("id", "unknown")
            )
            content = res.get("content", "").strip()
            context_blocks.append(f"[{i}] Nguồn ({source}):\n{content}")

        context_str = "\n\n".join(context_blocks)

        prompt = (
            "Bạn là một trợ lý thông minh hỗ trợ trả lời câu hỏi dựa trên tài liệu được cung cấp.\n"
            "Chỉ trả lời dựa trên các đoạn ngữ cảnh dưới đây. Nếu thông tin không có trong tài liệu, hãy trả lời rõ là không tìm thấy, tuyệt đối không suy đoán hay bịa đặt.\n"
            "Khi trích xuất thông tin, hãy trích dẫn số thứ tự nguồn [1], [2] tương ứng.\n\n"
            f"--- NGỮ CẢNH ---\n{context_str}\n\n"
            f"--- CÂU HỎI ---\n{question}\n\n"
            "--- CÂU TRẢ LỜI ---"
        )

        return self.llm_fn(prompt)
