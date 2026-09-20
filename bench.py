#!/usr/bin/env python3
"""
Benchmark Runner for Lab 7 - K4-L3B: E-commerce Policies Knowledge Base.

This script:
1. Loads cleaned .md documents from data/ecommerce/.
2. Chunks documents using the selected strategy (HeadingChunker, RecursiveChunker, or FixedSizeChunker).
3. Indexes chunks into EmbeddingStore with metadata (including doc_id, audience).
4. Runs 5 diverse benchmark queries (with A/B metadata filtering test on Query 3).
5. Evaluates two-tier quality (Doc ID match + Content keyword verification).
6. Exports results to ket_qua_benchmark.txt.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.agent import KnowledgeBaseAgent
from src.chunking import FixedSizeChunker, RecursiveChunker
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    GEMINI_EMBEDDING_MODEL,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    GeminiEmbedder,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)
from src.models import Document
from src.store import EmbeddingStore


class HeadingChunker:
    """
    Chunker chia theo ti\u00eau \u0111\u1ec1/m\u1ee5c (Heading / Section) d\u00e0nh cho v\u0103n b\u1ea3n ch\u00ednh s\u00e1ch/quy \u0111\u1ecbnh.
    M\u1ed7i section b\u1eaft \u0111\u1ea7u b\u1eb1ng #, ##, ### l\u00e0 m\u1ed9t \u0111\u01a1n v\u1ecb ng\u1eef ngh\u0129a tr\u1ecdn v\u1eb9n.
    N\u1ebfu m\u1ed9t section v\u01b0\u1ee3t qu\u00e1 max_chunk_size, s\u1eed d\u1ee5ng RecursiveChunker v\u00e0 g\u1eafn l\u1ea1i ti\u00eau \u0111\u1ec1 v\u00e0o c\u00e1c m\u1ea3nh con.
    """

    def __init__(self, max_chunk_size: int = 600) -> None:
        self.max_chunk_size = max_chunk_size
        self.fallback = RecursiveChunker(chunk_size=max_chunk_size)

    def chunk(self, text: str) -> list[str]:
        cleaned = text.strip()
        if not cleaned:
            return []

        heading_pattern = r"(?m)(?=^#{1,3}\s+)"
        raw_sections = [s.strip() for s in re.split(heading_pattern, cleaned) if s.strip()]

        chunks: list[str] = []
        for sec in raw_sections:
            if len(sec) <= self.max_chunk_size:
                chunks.append(sec)
            else:
                lines = sec.split("\n", 1)
                first_line = lines[0].strip()
                heading_title = first_line if first_line.startswith("#") else ""
                sub_chunks = self.fallback.chunk(sec)
                for sc in sub_chunks:
                    if heading_title and not sc.startswith(heading_title):
                        chunks.append(f"{heading_title}\n{sc}")
                    else:
                        chunks.append(sc)
        return chunks


BENCHMARK_QUERIES = [
    {
        "id": 1,
        "query": "Màn hình điện thoại mua tại Revibe được bảo hành trong bao lâu và có những điều kiện loại trừ nào?",
        "gold_doc": "revibe-terms-and-warranty",
        "gold_answer": "Màn hình chỉ được bảo hành trong 10 ngày đầu tiên kể từ ngày mua. Sau 10 ngày, bảo hành chỉ áp dụng cho các linh kiện khác ngoại trừ màn hình. Các trường hợp rơi vỡ vật lý, vào nước hoặc tự ý sửa chữa sẽ bị từ chối bảo hành.",
        "target_keywords": ["10 days", "screen", "water"],
        "metadata_filter": None,
    },
    {
        "id": 2,
        "query": "Khi mua hàng tại Newegg, phí hoàn kho (restocking fee) áp dụng cho những mặt hàng nào và mức phí là bao nhiêu?",
        "gold_doc": "newegg-return-policy",
        "gold_answer": "Mức phí hoàn kho là 15%, áp dụng cho các sản phẩm đã mở hộp (opened condition) thuộc các danh mục: ổ cứng (HD), bo mạch chủ (MB), card đồ họa (VGA), máy chiếu và tivi. Hàng còn nguyên seal hoặc bị lỗi không chịu phí này.",
        "target_keywords": ["15%", "restocking fee", "hard drives"],
        "metadata_filter": None,
    },
    {
        "id": 3,
        "query": "Khi đơn hàng giao thành công mà hai bên không phát sinh khiếu nại, sau bao nhiêu ngày tiền thanh toán sẽ được giải ngân vào Số Dư Tài Khoản?",
        "gold_doc": "shopee-returns-seller",
        "gold_answer": "Nếu Người Mua không nhấn 'Đã nhận được hàng' và không yêu cầu 'Trả hàng/Hoàn tiền', Shopee sẽ thanh toán tiền cho Người Bán nhanh nhất vào ngày thứ 04 (bốn) kể từ khi đơn hàng được cập nhật trạng thái 'Giao Hàng Thành Công'.",
        "target_keywords": ["ngày thứ 04", "Giao Hàng Thành Công", "Số Dư Tài Khoản"],
        "metadata_filter": {"audience": "seller"},
        "is_ab_test": True,
    },
    {
        "id": 4,
        "query": "Khách hàng mua hàng tại Refurbed cần làm những bước nào trước khi đóng gói gửi trả thiết bị?",
        "gold_doc": "refurbed-return-policy",
        "gold_answer": "Khách hàng phải sao lưu dữ liệu, khôi phục cài đặt gốc, đăng xuất khỏi tài khoản cá nhân (iCloud/Google), đóng gói bằng hộp carton chèn đệm, dán nhãn mới và tuyệt đối không gửi thiết bị có pin bị phồng (swollen battery).",
        "target_keywords": ["factory settings", "padded envelopes", "swollen battery"],
        "metadata_filter": None,
    },
    {
        "id": 5,
        "query": "Theo quy định Shopee, Người Bán phải chịu những loại phí cố định và phí giao dịch nào trên mỗi đơn hàng thành công?",
        "gold_doc": "shopee-returns-seller",
        "gold_answer": "Người Bán chịu Phí Xử Lý Giao Dịch là 6% (đã gồm VAT) áp dụng cho mọi phương thức thanh toán, và Phí Cố Định (hoa hồng sàn) tính theo tỷ lệ phần trăm tùy ngành hàng trên giá bán sản phẩm.",
        "target_keywords": ["6%", "Phí Xử Lý Giao Dịch", "Phí Cố Định"],
        "metadata_filter": None,
    },
]


def parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    parts = content.split("---", 2)
    if len(parts) >= 3:
        fm_text = parts[1].strip()
        body = parts[2].strip()
        fm = {}
        for line in fm_text.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip().strip('"').strip("'")
        return fm, body
    return {}, content


def get_embedder():
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    if provider == "local":
        try:
            return LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        except Exception:
            return _mock_embed
    elif provider == "openai":
        try:
            return OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL))
        except Exception:
            return _mock_embed
    elif provider == "gemini":
        try:
            return GeminiEmbedder(model_name=os.getenv("GEMINI_EMBEDDING_MODEL", GEMINI_EMBEDDING_MODEL))
        except Exception:
            return _mock_embed
    return _mock_embed


def build_store(data_dir: Path, chunker, embedder) -> tuple[EmbeddingStore, int]:
    store = EmbeddingStore(collection_name="benchmark_store", embedding_fn=embedder)
    total_chunks = 0
    md_files = sorted(data_dir.glob("*.md"))

    for path in md_files:
        content = path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(content)
        doc_id = fm.get("doc_id", path.stem)
        chunks = chunker.chunk(body)

        docs = []
        for i, ch in enumerate(chunks):
            doc = Document(
                id=f"{path.stem}#{i}",
                content=ch,
                metadata={
                    **fm,
                    "doc_id": doc_id,
                    "chunk_id": i,
                    "source": str(path),
                },
            )
            docs.append(doc)

        store.add_documents(docs)
        total_chunks += len(docs)

    return store, total_chunks


def run_benchmark(strategy_name: str, chunker, data_dir: Path, output_lines: list[str]) -> float:
    embedder = get_embedder()
    store, total_chunks = build_store(data_dir, chunker, embedder)

    backend_name = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    header = f"\n=======================================================\nCHIẾN LƯỢC: {strategy_name} (Tổng số chunks: {total_chunks})\nBackend Embedding: {backend_name}\n======================================================="
    print(header)
    output_lines.append(header)

    total_score = 0.0

    for q in BENCHMARK_QUERIES:
        qid = q["id"]
        query_text = q["query"]
        gold_doc = q["gold_doc"]
        meta_filter = q["metadata_filter"]

        if q.get("is_ab_test"):
            unfiltered_results = store.search_with_filter(query_text, top_k=3, metadata_filter=None)
            filtered_results = store.search_with_filter(query_text, top_k=3, metadata_filter=meta_filter)

            ab_header = f"\n[Câu {qid} - A/B FILTER TEST] Query: {query_text}"
            print(ab_header)
            output_lines.append(ab_header)

            unf_top_doc = unfiltered_results[0]["metadata"].get("doc_id") if unfiltered_results else "None"
            unf_score = unfiltered_results[0]["score"] if unfiltered_results else 0.0
            fil_top_doc = filtered_results[0]["metadata"].get("doc_id") if filtered_results else "None"
            fil_score = filtered_results[0]["score"] if filtered_results else 0.0

            unfiltered_info = f"  * KHÔNG lọc (unfiltered): Top-1 doc={unf_top_doc} (score={unf_score:.3f})"
            filtered_info = f"  * CÓ lọc (filter={meta_filter}): Top-1 doc={fil_top_doc} (score={fil_score:.3f})"
            print(unfiltered_info)
            print(filtered_info)
            output_lines.append(unfiltered_info)
            output_lines.append(filtered_info)

            results = filtered_results
        else:
            results = store.search_with_filter(query_text, top_k=3, metadata_filter=meta_filter)

        top_docs = [r["metadata"].get("doc_id") for r in results]
        combined_context = " ".join(r["content"] for r in results)
        keywords_present = any(kw.lower() in combined_context.lower() for kw in q["target_keywords"])

        q_score = 0.0
        if gold_doc in top_docs and keywords_present:
            q_score = 2.0 if top_docs[0] == gold_doc else 1.0
        elif gold_doc in top_docs:
            q_score = 1.0

        total_score += q_score

        top_content = results[0]["content"][:140].replace("\n", " ") if results else "None"
        q_report = (
            f"\n[Câu {qid}] {query_text}\n"
            f"  - Gold Doc: {gold_doc}\n"
            f"  - Top-3 Docs: {top_docs}\n"
            f"  - Điểm câu: {q_score}/2.0\n"
            f"  - Top-1 Preview: {top_content}..."
        )
        print(q_report)
        output_lines.append(q_report)

    summary = f"\n--> TỔNG ĐIỂM TRUY XUẤT CHO \"{strategy_name}\": {total_score}/10.0\n"
    print(summary)
    output_lines.append(summary)
    return total_score


def main():
    parser = argparse.ArgumentParser(description="Lab 7 Benchmark Runner - R1 (Nguyễn Tuấn Anh)")
    parser.add_argument("--data-dir", type=str, default="data/ecommerce", help="Directory with .md documents")
    parser.add_argument("--output", type=str, default="ket_qua_benchmark.txt", help="Output file")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"Error: Data directory {data_dir} does not exist.")
        return 1

    # R1 (Bạn): Chỉ chạy duy nhất chiến lược cá nhân HeadingChunker
    strategy_name = "HeadingChunker (Thành viên 1 - Nguyễn Tuấn Anh)"
    chunker = HeadingChunker(max_chunk_size=600)

    output_lines = [
        "BÁO CÁO KẾT QUẢ BENCHMARK CÁ NHÂN — LAB 7",
        "Thành viên 1: Nguyễn Tuấn Anh (R1 - HeadingChunker)",
        "Tập dữ liệu: 10 tài liệu E-commerce",
        "====================================================================",
    ]

    run_benchmark(strategy_name, chunker, data_dir, output_lines)

    output_path = Path(args.output)
    output_path.write_text("\n".join(output_lines), encoding="utf-8")
    print(f"\n[OK] Đã ghi kết quả benchmark CÁ NHÂN của R1 vào: {output_path.resolve()}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
