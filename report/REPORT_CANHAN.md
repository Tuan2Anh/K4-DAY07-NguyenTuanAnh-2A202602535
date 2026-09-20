# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Tuấn Anh
**Nhóm:** Nhóm 3 (K4-L3B)
**Ngày:** 2026-09-20

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (tiệm cận 1.0) nghĩa là hai vector embedding chỉ về cùng một hướng trong không gian đa chiều, phản ánh hai đoạn văn bản có sự tương đồng sâu sắc về mặt ngữ nghĩa (semantic similarity) bất kể cách dùng từ diễn đạt khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Khách hàng được quyền trả lại sản phẩm và nhận lại tiền trong vòng 10 ngày kể từ lúc nhận hàng."
- Câu B: "Người mua có thể gửi hoàn hàng và yêu cầu hoàn lại chi phí trong thời hạn mười hôm sau khi giao thành công."
- Tại sao tương đồng: Hai câu sử dụng tập từ vựng khác nhau ("trả lại" vs "gửi hoàn hàng", "nhận lại tiền" vs "hoàn lại chi phí", "10 ngày" vs "mười hôm") nhưng hoàn toàn đồng nhất về nghĩa và ngữ cảnh chính sách đổi trả.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Thời gian xử lý yêu cầu bảo hành linh kiện phần cứng máy tính là tối đa 14 ngày làm việc."
- Câu B: "Công thức làm bánh mì hoa cúc kiểu Pháp cần ủ bột ở nhiệt độ phòng trong hai tiếng."
- Tại sao khác: Hai câu thuộc hai miền kiến thức hoàn toàn tách biệt (chính sách kỹ thuật bảo hành vs công thức làm bánh ẩm thực), vector của chúng gần như trực giao (góc gần 90 độ, cosine tiệm cận 0.0).

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chỉ đo góc giữa hai vector mà không phụ thuộc vào độ lớn (magnitude/độ dài) của vector. Điều này giúp hệ thống không bị ảnh hưởng bởi độ dài câu/văn bản (văn bản dài lặp từ có thể làm tăng khoảng cách Euclid dù ý nghĩa giống nhau).

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> - Bước nhảy (step) = chunk_size - overlap = 500 - 50 = 450 ký tự.
> - Số lượng chunk = ceil((10,000 - 50) / (500 - 50)) = ceil(9,950 / 450) = ceil(22.11) = 23 chunks.
> *Đáp án:* 23 chunks (đã kiểm chứng trùng khớp 100% với `FixedSizeChunker(chunk_size=500, overlap=50)`).

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng lên 100, số lượng chunk tăng từ 23 lên 25 chunks: ceil((10,000 - 100) / (500 - 100)) = ceil(9,900 / 400) = ceil(24.75) = 25 chunks. Ta muốn tăng độ chồng chéo để bảo toàn tính mạch lạc của ngữ cảnh giữa các đoạn liền kề, tránh để các câu văn hay điều khoản quan trọng bị cắt đứt gãy ở đúng đường biên ranh giới chia nhỏ.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng biểu thức chính quy với kỹ thuật Positive Lookbehind `(?<=[.!?])(?:\s+|\n+)` để tách ranh giới câu mà không làm nuốt mất dấu câu ở cuối. Sau khi lọc các câu rỗng và strip khoảng trắng thừa, thuật toán nhóm tối đa `max_sentences_per_chunk` câu vào mỗi chunk bằng `" ".join()`. Xử lý an toàn chuỗi rỗng trả về `[]`. Hạn chế đã biết: các từ viết tắt có dấu chấm (như `TS.`, `v.v.`) hoặc số thập phân (`3.14`) có thể bị nhận diện nhầm thành kết thúc câu.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán hoạt động theo hai chiều: đệ quy xuống sâu và gom lên. Đầu tiên ưu tiên cắt theo các dấu phân cách có mức ngữ nghĩa lớn `["\n\n", "\n", ". ", " ", ""]`. Nếu một mảnh vẫn vượt quá `chunk_size`, thuật toán đệ quy gọi `_split` với danh sách dấu phân cách còn lại; sau đó gom các mảnh nhỏ liền kề lại cho tới khi chạm ngưỡng `chunk_size` để tránh tạo ra các chunk vụn. Base cases gồm: chuỗi rỗng, chuỗi đã $\le$ `chunk_size`, và trường hợp `remaining_separators == []` (hoặc `sep == ""`) thì cắt cứng theo `chunk_size`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Lưu trữ in-memory dưới dạng danh sách dictionary thông qua helper `_make_record`, mỗi record lưu `id`, `content`, bản sao `metadata` (đảm bảo luôn có khóa `doc_id` trỏ về tài liệu gốc) và vector `embedding`. Hàm `search` gọi qua helper chung `_search_records`: nhúng vector câu hỏi, tính độ tương đồng bằng tích vô hướng (`_dot`) do các vector đã được chuẩn hóa đơn vị, loại bỏ trường vector 1536 chiều để output gọn gàng, sắp xếp giảm dần theo `score` và trả về `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` bắt buộc thực hiện **lọc trước (pre-filtering)** trên toàn bộ store để chọn ra tập ứng viên thỏa mãn tất cả điều kiện trong `metadata_filter` trước khi tính điểm cosine; nếu lọc sau thì k vị trí đầu bảng có thể bị tài liệu không khớp chiếm hết dẫn đến 0 kết quả. `delete_document` loại bỏ tất cả các bản ghi có `metadata['doc_id']` hoặc `id` trùng khớp, so sánh kích thước store trước và sau để trả về `True` (nếu có bản ghi bị xóa) hoặc `False`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Thực hiện quy trình RAG 3 nhịp chuẩn: Kiểm tra cơ sở tri thức (nếu rỗng thì thông báo ngay thay vì gọi LLM vô ích) $\rightarrow$ gọi `store.search()` lấy `top_k` chunk $\rightarrow$ định dạng ngữ cảnh được đánh số thứ tự kèm tên file nguồn `[1] Nguồn (...): <content>` để đảm bảo khả năng truy vết nguồn (Source Traceability). Cuối cùng, ghép vào prompt hướng dẫn mô hình chỉ trả lời từ thông tin được cung cấp, cấm bịa đặt, bắt buộc trích dẫn số `[1], [2]` và gọi hàm `llm_fn`.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts ==============================
platform linux -- Python 3.12.14, pytest-9.1.1, pluggy-1.6.0
rootdir: /mnt/win_d/vinuni/week-2/lab 7/K4-L3B-Data-Foundations
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================== 42 passed in 0.04s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Khách hàng được quyền trả lại sản phẩm trong vòng 10 ngày nếu đổi ý. | Người mua có thể hoàn trả thiết bị trong thời hạn mười ngày kể từ khi nhận hàng. | cao | +0.1597 | Đúng |
| 2 | Bảo hành tiêu chuẩn một năm bao gồm toàn bộ linh kiện và màn hình trong 10 ngày đầu. | Người bán được thanh toán tiền hàng tự động mỗi tuần và không mất phí hoa hồng. | thấp | +0.1437 | Sai lệch (do Mock) |
| 3 | Chính sách bảo hành tiêu chuẩn áp dụng trong thời hạn 12 tháng từ ngày giao hàng. | Gói bảo hành mở rộng kéo dài thời gian bảo vệ thiết bị lên tổng cộng 2 năm. | cao | -0.0280 | Sai lệch (do Mock) |
| 4 | Sản phẩm đổi trả phải còn nguyên hộp và không bị trầy xước bề mặt. | Kỹ thuật nướng bánh bông lan cần làm nóng lò nướng trước mười lăm phút. | thấp | -0.1198 | Đúng |
| 5 | Gói hàng được vận chuyển miễn phí đến tận tay người mua qua đơn vị giao vận. | Mọi tranh chấp phát sinh sẽ được phân xử theo quy tắc trọng tài quốc tế tại Dubai. | thấp | -0.0348 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là ở Cặp 3: Hai câu đều nói về mốc thời gian bảo hành sản phẩm (12 tháng vs 2 năm) nhưng điểm thực tế của `MockEmbedder` lại ra giá trị âm (-0.0280), trong khi Cặp 2 (hai chủ đề khác hẳn nhau) lại có điểm dương (+0.1437). Điều này chứng minh rằng trình nhúng giả lập băm MD5 (`MockEmbedder`) chỉ tạo số giả ngẫu nhiên dựa trên mã băm chuỗi ký tự rời rạc mà hoàn toàn không nắm bắt được ngữ nghĩa (semantics) thực sự như các mô hình ngôn ngữ lớn (Dense Embeddings).

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá chuẩn của nhóm** trên mã nguồn cá nhân với chiến lược **`HeadingChunker(max_chunk_size=600)`** (chia theo Section/Heading Markdown có gắn lại tiêu đề mục cha). Kết quả đối chiếu trực tiếp từ file `ket_qua_benchmark_1.txt` (tổng số: 310 chunks):

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Top-3 Docs | Có Gold Doc trong Top-3? | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|:----------:|:------------------------:|------------------------|
| 1 | Màn hình điện thoại mua tại Revibe được bảo hành trong bao lâu và có những điều kiện loại trừ nào? | `tamara-customer-terms`: mục giới thiệu điều khoản đối tác | `tamara`, `reveni`, `shopee-buyer` | Chưa (nhiễu do Mock) | Mock embedding chưa đưa doc Revibe vào top-3 của câu này. |
| 2 | Khi mua hàng tại Newegg, phí hoàn kho (restocking fee) áp dụng cho những mặt hàng nào và mức phí là bao nhiêu? | `newegg-return-policy`: mục `### Refunds` và chính sách hoàn tiền | `newegg`, `newegg`, `reveni` | **CÓ (Top-1 & Top-2)** | Đạt kết quả xuất sắc: cả Top-1 và Top-2 đều thuộc đúng tài liệu Newegg. |
| 3 | Khi đơn hàng giao thành công mà hai bên không phát sinh khiếu nại, sau bao nhiêu ngày tiền thanh toán sẽ được giải ngân vào Số Dư Tài Khoản? *(A/B Test)* | `revibe-seller-guidelines`: mục bán hàng cho người bán (khi lọc `seller`) | `revibe-seller`, `revibe-seller`, `shopee-seller` | **CÓ (Top-3)** | Khi có bộ lọc `metadata_filter={"audience": "seller"}`, tài liệu chuẩn `shopee-returns-seller` lọt vào Top-3. |
| 4 | Khách hàng mua hàng tại Refurbed cần làm những bước nào trước khi đóng gói gửi trả thiết bị? | `reveni-terms-of-use`: mục tài sản trí tuệ | `reveni`, `tamara`, `tamara` | Chưa (nhiễu do Mock) | Mock embedding bị lệch sang các điều khoản dài của Tamara và Reveni. |
| 5 | Theo quy định Shopee, Người Bán phải chịu những loại phí cố định và phí giao dịch nào trên mỗi đơn hàng thành công? | `reebelo-terms-of-service`: mục bảo hành và hoàn tiền | `reebelo`, `tamara`, `revibe-terms` | Chưa (nhiễu do Mock) | Chưa truy xuất được tài liệu phí Shopee khi chưa áp dụng filter. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 2 / 5 câu (Câu 2 và Câu 3).

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Nhận ra rằng việc chia nhỏ theo Heading/Section (`HeadingChunker`) giúp giữ được tính trọn vẹn của từng điều khoản chính sách tốt nhất về mặt ngữ nghĩa (người đọc rất dễ hiểu vì luôn có tiêu đề mục đi kèm). Tuy nhiên, khi kết hợp với bộ lọc metadata (`search_with_filter`), hiệu quả tăng vọt rõ rệt ở Câu 3: bộ lọc đã loại bỏ 100% tài liệu người mua gây nhiễu, giúp đưa tài liệu thanh toán của người bán lên vị trí Top-1 tuyệt đối.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
