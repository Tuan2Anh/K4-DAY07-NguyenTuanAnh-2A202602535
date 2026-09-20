# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** TuDaiBoTuc
**Thành viên:** 
1. Nguyễn Tuấn Anh (R1 - Data Lead & Heading Chunker)
2. Đỗ Nguyễn Ngọc Long (R2 - Benchmark Lead & Recursive Chunker)
3. Cao Đức Anh (R3 - Strategy Lead & Fixed-Size Chunker)
**Ngày:** 20-09-2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Chính sách Đổi trả, Bảo hành, Thanh toán và Quy định Người bán trên các Nền tảng Thương mại Điện tử (E-commerce Marketplace Platforms: Shopee, Newegg, Tamara, Reebelo, Refurbed, Revibe, Reveni, Điện Máy Chợ Lớn).

**Tại sao nhóm chọn chủ đề này?**
> Nhóm thu thập tập dữ liệu gồm 10 tài liệu chính sách thương mại điện tử đa dạng (cả tiếng Anh lẫn tiếng Việt, các sàn quốc tế và trong nước). Điểm mấu chốt là có sự phân định rành mạch giữa hai nhóm đối tượng: Người Mua (`audience: buyer`) và Người Bán (`audience: seller`). Các tài liệu chứa nhiều quy định về mốc thời gian (30 ngày đổi trả, 14 ngày gửi kiện, ngày thứ 4 giải ngân), con số tỷ lệ phí (phí hoàn kho 15%, phí giao dịch 6%), rất lý tưởng để kiểm thử độ chính xác của retrieval và chứng minh vai trò quyết định của tính năng lọc metadata (`metadata_filter`).

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | `refurbed-return-policy.md` | https://www.refurbed.at/en-at/how-to-return-your-product/ | 2026-09-20 / not-stated | 3.695 | `audience: buyer`, `category: returns-policy`, `language: en` |
| 2 | `revibe-seller-guidelines.md` | https://revibe.ae/pages/become-a-seller | 2026-09-20 / not-stated | 1.723 | `audience: seller`, `category: seller-policy`, `language: en` |
| 3 | `revibe-terms-and-warranty.md` | https://revibe.ae/pages/terms-and-conditions | 2026-09-20 / not-stated | 31.699 | `audience: buyer`, `category: warranty-policy`, `language: en` |
| 4 | `shopee-returns-buyer.md` | https://help.shopee.vn/portal/4/article/77243 | 2026-09-20 / 2026-05-01 | 2.861 | `audience: buyer`, `category: returns-policy`, `language: vi` |
| 5 | `shopee-returns-seller.md` | https://help.shopee.vn/portal/4/article/77243 | 2026-09-20 / 2026-05-01 | 3.144 | `audience: seller`, `category: seller-policy`, `language: vi` |
| 6 | `newegg-return-policy.md` | https://www.newegg.com/promotions/nepro/22-0073/index.html | 2026-09-20 / not-stated | 15.003 | `audience: buyer`, `category: returns-policy`, `language: en` |
| 7 | `tamara-customer-terms.md` | https://tamara.co/en-sa/terms-and-conditions | 2026-09-20 / not-stated | 40.806 | `audience: buyer`, `category: payment-policy`, `language: en` |
| 8 | `reveni-terms-of-use.md` | https://www.reveni.com/legal/legal | 2026-09-20 / not-stated | 6.759 | `audience: buyer`, `category: terms-of-use`, `language: en` |
| 9 | `reebelo-terms-of-service.md` | https://reebelo.com/policies/terms-of-service | 2026-09-20 / not-stated | 4.388 | `audience: both`, `category: terms-of-service`, `language: en` |
| 10 | `trang-bao-tri-bao-hanh-doi-tra.md` | https://dienmaycholon.com/trang-bao-tri-bao-hanh-doi-tra | 2026-09-20 / 2026-08-01 | 7.017 | `audience: buyer`, `category: warranty-policy`, `language: vi` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ (đã kiểm tra `robots.txt` cho phép).
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.
- [x] Đã dọn sạch toàn bộ menu, thanh điều hướng, banner quảng cáo khuyến mãi và cookie popup trước khi lưu.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | `str` | `revibe-seller-guidelines` | Định danh tài liệu gốc duy nhất, dùng để liên kết chunk về văn bản cha và thực thi hàm `delete_document()`. |
| `audience` | `str` | `buyer`, `seller` | Bắt buộc cho K4-L3B: phục vụ lọc trước (`metadata_filter`) để phân tách luồng quy định giữa người mua và người bán. |
| `category` | `str` | `returns-policy`, `warranty-policy`, `seller-policy` | Phân loại nghiệp vụ chính sách, hỗ trợ thu hẹp không gian tìm kiếm khi người dùng hỏi chuyên biệt về bảo hành hay đổi trả. |
| `source_url` | `str` | `https://revibe.ae/...` | Đảm bảo tính minh bạch nguồn gốc dữ liệu (Provenance) và cho phép trích dẫn đường dẫn gốc khi RAG agent trả lời. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên các tài liệu đã tách bỏ frontmatter:

| Tài liệu (đã bỏ YAML) | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|:-------------:|:------------:|-------------------|
| `shopee-returns-buyer.md` | `fixed_size` (400/50) | 16 | 197.6 | Kém; cắt đứt ngang các mốc thời gian hoàn tiền |
| `shopee-returns-buyer.md` | `by_sentences` (max 3) | 7 | 407.0 | Tốt; câu tiếng Việt trọn vẹn theo từng điều khoản |
| `shopee-returns-buyer.md` | `recursive` (400) | 19 | 149.4 | Khá; mảnh nhỏ gọn nhưng không vụn |
| `shopee-returns-seller.md` | `fixed_size` (400/50) | 18 | 193.6 | Kém; chia cắt điều khoản phí giao dịch 6% và phí cố định |
| `shopee-returns-seller.md` | `by_sentences` (max 3) | 7 | 446.9 | Tốt; giữ nguyên ngữ cảnh các loại phí và xử lý khiếu nại |
| `shopee-returns-seller.md` | `recursive` (400) | 20 | 155.8 | Khá; cân bằng kích thước tốt |
| `refurbed-return-policy.md` | `fixed_size` (400/50) | 21 | 195.0 | Kém; cắt đôi các bước hướng dẫn gửi hàng |
| `refurbed-return-policy.md` | `by_sentences` (max 3) | 15 | 242.3 | Trung bình; giữ trọn câu tiếng Anh nhưng câu ghép dài |
| `refurbed-return-policy.md` | `recursive` (400) | 24 | 151.7 | Tốt; bảo toàn đoạn văn hợp lý |

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Tuấn Anh**
- **Loại chiến lược:** `HeadingChunker` (Custom Heading / Section-based Chunking)
- **Mô tả & lý do chọn cho chủ đề này:** Tận dụng cấu trúc văn bản pháp lý/chính sách vốn được chia sẵn theo các đề mục Markdown (`## `). Mỗi mục là một đơn vị ngữ nghĩa độc lập (ví dụ `## Revibe Warranty`, `## Return and Refund Policy`). Khi một section quá dài (> 600 ký tự), chiến lược gọi fallback `RecursiveChunker` và **gắn lại tiêu đề mục cha** vào từng mảnh con để bảo toàn ngữ cảnh truy vết.
- **Code snippet:**
```python
class HeadingChunker:
    def __init__(self, max_chunk_size: int = 600) -> None:
        self.max_chunk_size = max_chunk_size
        self.fallback = RecursiveChunker(chunk_size=max_chunk_size)

    def chunk(self, text: str) -> list[str]:
        cleaned = text.strip()
        if not cleaned: return []
        raw_sections = [s.strip() for s in re.split(r"(?m)(?=^#{1,3}\s+)", cleaned) if s.strip()]
        chunks = []
        for sec in raw_sections:
            if len(sec) <= self.max_chunk_size:
                chunks.append(sec)
            else:
                lines = sec.split("\n", 1)
                heading = lines[0].strip() if lines[0].strip().startswith("#") else ""
                for sc in self.fallback.chunk(sec):
                    chunks.append(f"{heading}\n{sc}" if heading and not sc.startswith(heading) else sc)
        return chunks
```

**Thành viên 2 — Đỗ Nguyễn Ngọc Long**
- **Loại chiến lược:** `RecursiveChunker` (`chunk_size=350`)
- **Mô tả & lý do chọn:** Chia nhỏ đệ quy theo danh sách phân tách ngữ nghĩa `["\n\n", "\n", ". ", " ", ""]` với ngưỡng kích thước gọn 350 ký tự. Chiến lược này giúp xử lý tốt các văn bản chứa nhiều danh sách gạch đầu dòng và tự động gom các dòng ngắn liền kề, tối ưu độ dài cho từng đơn vị ý nghĩa.
- **Code snippet:**
```python
class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text:
            return []

        if len(current_text) <= self.chunk_size:
            return [current_text]

        # Base case 1: Không còn separator nào để thử -> cắt cứng theo chunk_size
        if not remaining_separators:
            return [
                current_text[i : i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        sep = remaining_separators[0]
        next_seps = remaining_separators[1:]

        # Base case 2: sep rỗng "" -> tách từng ký tự rồi cắt theo chunk_size
        if sep == "":
            return [
                current_text[i : i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        # Tách chuỗi theo separator hiện tại
        if sep in current_text:
            splits = current_text.split(sep)
        else:
            # Không tìm thấy separator hiện tại -> thử tiếp separator tiếp theo
            return self._split(current_text, next_seps)

        # Đệ quy xuống sâu cho các mảnh con vẫn vượt quá chunk_size
        refined_splits: list[str] = []
        for s in splits:
            if not s:
                continue
            if len(s) > self.chunk_size:
                refined_splits.extend(self._split(s, next_seps))
            else:
                refined_splits.append(s)

        # Gom lên (Merge): gộp các mảnh nhỏ liền kề cho tới sát chunk_size
        chunks: list[str] = []
        current_chunk = ""
        for piece in refined_splits:
            if not piece:
                continue
            if not current_chunk:
                current_chunk = piece
            else:
                candidate = current_chunk + sep + piece
                if len(candidate) <= self.chunk_size:
                    current_chunk = candidate
                else:
                    chunks.append(current_chunk)
                    current_chunk = piece

        if current_chunk:
            chunks.append(current_chunk)

        return chunks
```

**Thành viên 3 — Cao Đức Anh**
- **Loại chiến lược:** `FixedSizeChunker` (Cửa sổ trượt cố định, `chunk_size=400`, `overlap=50`)
- **Mô tả & lý do chọn:** Dùng kích thước cắt cứng cố định có độ chồng lấn để đóng vai trò đường cơ sở (baseline) so sánh. Overlap 50 ký tự giúp đảm bảo từ khóa hoặc mốc số liệu nằm ở ranh giới giữa 2 chunk không bị đứt đoạn hoàn toàn.
- **Code snippet:**
```python
class FixedSizeChunker:
    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks
```

### So Sánh Giữa Các Thành Viên (Dựa trên 3 file benchmark thực tế)

Đối chiếu trực tiếp từ 3 file kết quả thực nghiệm độc lập:
- **Thành viên 1 (`ket_qua_benchmark_1.txt`):** `HeadingChunker(max_chunk_size=600)`
- **Thành viên 2 (`ket_qua_benchmark_2.txt`):** `RecursiveChunker(chunk_size=350)`
- **Thành viên 3 (`ket_qua_benchmark.txt`):** `FixedSizeChunker`

| Thành viên | Chiến lược (Strategy) | Tổng số chunk | Số câu có Gold Doc trong Top-3 | Điểm mạnh thực tế | Điểm yếu thực tế |
|-----------|----------|:---:|:---:|-----------|----------|
| **Thành viên 1 (R1)** | `HeadingChunker` (max 600) | **310** | **2 / 5 câu** | Giữ trọn vẹn tiêu đề mục cha (`## `) cho từng mảnh con; ngữ cảnh điều khoản rõ ràng, không bị đứt câu | Section quá ngắn tạo ra chunk nhỏ nếu không gom cụm |
| **Thành viên 2 (R2)** | `RecursiveChunker` (size 350) | **450** | **3 / 5 câu** (Câu 1, 2, 3) | Kích thước chunk rất vừa vặn, không bị chunk rác quá khổ; gom các dòng liệt kê tốt | Số lượng chunk tăng cao (450 chunks); mảnh con sau bị mất tiêu đề phân mục gốc |
| **Thành viên 3 (R3)** | `FixedSizeChunker` | **264** | **2 / 5 câu** (Câu 1, 3) | Số lượng chunk gọn (264 chunks); thuật toán đơn giản, tốc độ chunking nhanh nhất | Cắt cơ học ngang giữa từ/câu; ranh giới ngữ nghĩa bị phá vỡ |

*(Lưu ý: Điểm truy xuất ở trên chạy với `MockEmbedder` giả lập MD5 nên bị giới hạn bởi tính ngẫu nhiên của hàm băm; giá trị phản ánh cấu trúc chunk hơn là độ hiểu ngữ nghĩa sâu).*

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Với văn bản chính sách thương mại điện tử, chiến lược **`HeadingChunker` kết hợp gắn lại tiêu đề** là giải pháp tối ưu nhất về mặt kiến trúc. Mỗi điều khoản bảo hành hay hoàn tiền là một thực thể độc lập; việc giữ nguyên tiêu đề giúp mô hình RAG biết chính xác điều khoản đó thuộc quy định nào (ví dụ biết rõ đây là bảo hành mở rộng hay bảo hành tiêu chuẩn), loại bỏ hoàn toàn sự mơ hồ về ngữ cảnh.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Màn hình điện thoại mua tại Revibe được bảo hành trong bao lâu và có những điều kiện loại trừ nào? | Màn hình chỉ được bảo hành trong 10 ngày đầu tiên kể từ ngày mua. Sau đó bảo hành loại trừ màn hình; nước, rơi vỡ hoặc tự sửa chữa làm mất bảo hành. | `revibe-terms-and-warranty` (`## Revibe Warranty`) |
| 2 | Khi mua hàng tại Newegg, phí hoàn kho (restocking fee) áp dụng cho những mặt hàng nào và mức phí là bao nhiêu? | Mức phí hoàn kho là 15%, áp dụng cho các sản phẩm đã mở hộp thuộc: ổ cứng (HD), bo mạch chủ (MB), card đồ họa (VGA), máy chiếu và TV. Hàng nguyên seal không chịu phí. | `newegg-return-policy` (`### Restocking Fees`) |
| 3 | Khi đơn hàng giao thành công mà hai bên không phát sinh khiếu nại, sau bao nhiêu ngày tiền thanh toán sẽ được giải ngân vào Số Dư Tài Khoản? *(A/B Test)* | Nếu Người Mua không bấm nhận hàng và không khiếu nại, Shopee sẽ thanh toán cho Người Bán nhanh nhất vào ngày thứ 04 kể từ khi cập nhật trạng thái "Giao Hàng Thành Công". | `shopee-returns-seller` (`## 1. Mốc thời gian ghi nhận tiền...`) |
| 4 | Khách hàng mua hàng tại Refurbed cần làm những bước nào trước khi đóng gói gửi trả thiết bị? | Phải sao lưu dữ liệu, khôi phục cài đặt gốc, đăng xuất iCloud/Google; đóng gói bằng hộp carton chèn đệm, cấm dùng phong bì đệm khí và tuyệt đối không gửi pin bị phồng. | `refurbed-return-policy` (`## 3. Remove personal data` & `## 4. Print label`) |
| 5 | Theo quy định Shopee, Người Bán phải chịu những loại phí cố định và phí giao dịch nào trên mỗi đơn hàng thành công? | Người Bán chịu Phí Xử Lý Giao Dịch 6% (đã gồm VAT) cho mọi phương thức thanh toán, và Phí Cố Định (hoa hồng sàn) theo tỷ lệ % ngành hàng. | `shopee-returns-seller` (`## 2. Nghĩa vụ Phí của Người Bán`) |

### Tổng hợp chất lượng truy xuất của nhóm

Đối chiếu chi tiết 5 câu hỏi trên cả 3 chiến lược của nhóm:

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có Gold Doc trong Top-3? (R1 / R2 / R3) | Phân tích chi tiết |
|---|---------|:-------------------------------:|:---------------------------------------:|-------------------|
| 1 | Bảo hành màn hình Revibe & điều kiện loại trừ | `FixedSizeChunker` & `RecursiveChunker` | Không (R1) / **Có Top-3 (R2)** / **Có Top-1 (R3)** | R3 đưa đúng `revibe-terms-and-warranty#36` lên Top-1 (score=0.2775); R2 đưa lên Top-3 (score=0.3329). |
| 2 | Phí hoàn kho Newegg 15% cho linh kiện | `HeadingChunker` & `RecursiveChunker` | **Có Top-1,2 (R1)** / **Có Top-3 (R2)** / Không (R3) | R1 xuất sắc đưa `newegg-return-policy` lên cả Top-1 và Top-2; R2 có trong Top-3 (score=0.2850). |
| 3 | Thời hạn giải ngân Shopee cho Người Bán *(A/B Test)* | **Cả 3 chiến lược (100%)** | **Có Top-1,3 (R1)** / **Có Top-1 (R2)** / **Có Top-1 (R3)** | **Điểm sáng tuyệt đối của nhóm**: Cả 3 thành viên khi bật filter đều đưa `shopee-returns-seller` lên Top-1! |
| 4 | Các bước đóng gói an toàn thiết bị Refurbed | Chưa tối ưu do Mock Embedding | Không (R1) / Không (R2) / Không (R3) | Cả 3 chiến lược đều bị tài liệu dài `tamara` và `reveni` lấn át do hạn chế của hàm băm mock MD5. |
| 5 | Phí giao dịch 6% & phí cố định Shopee Người Bán | Chưa tối ưu do Mock Embedding | Không (R1) / Không (R2) / Không (R3) | Câu hỏi chứa nhiều từ khóa tiếng Việt về "phí" bị trùng với các điều khoản phí của `tamara` khi chưa bật filter. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> **CÓ, MANG TÍNH QUYẾT ĐỊNH TUYỆT ĐỐI Ở CÂU HỎI 3 (Chứng minh đồng thuận trên cả 3 thành viên):**
> Câu hỏi: *"Khi đơn hàng giao thành công mà hai bên không phát sinh khiếu nại, sau bao nhiêu ngày tiền thanh toán sẽ được giải ngân vào Số Dư Tài Khoản?"*
> 
> - **Khi KHÔNG lọc (`unfiltered`)**:
>   - **R1:** Bị tài liệu `tamara-customer-terms` chiếm Top-1 (score=0.345).
>   - **R2:** Bị tài liệu `tamara-customer-terms` chiếm trọn Top-1, 2 (score=0.3505) và `revibe-terms` chiếm Top-3.
>   - **R3:** Bị tài liệu `tamara` chiếm Top-1 (score=0.3164) và không có tài liệu Người Bán nào trong Top-3.
>   -> **Hậu quả:** Toàn bộ slot tìm kiếm bị các điều khoản người mua/thanh toán chung chiếm lĩnh, hệ thống không thể trả lời được quy trình của Người Bán.
> 
> - **Khi CÓ lọc (`metadata_filter={"audience": "seller"}`)**:
>   - **R1:** Tài liệu `shopee-returns-seller` lọt vào Top-3 và các tài liệu người mua bị loại bỏ 100%.
>   - **R2:** Tài liệu chuẩn `shopee-returns-seller` nhảy thẳng lên vị trí **Top-1** (score=0.1737).
>   - **R3:** Tài liệu chuẩn `shopee-returns-seller` nhảy thẳng lên vị trí **Top-1** (score=0.2291) với đoạn trích chính xác: *"Người Bán nhanh nhất vào ngày thứ 04 (bốn) kể từ khi đơn hàng được cập nhật trạng thái Giao Hàng Thành Công"*.
> 
> -> Đây là minh chứng hoàn hảo cho thấy Pre-filtering là giải pháp bắt buộc trong các hệ thống RAG đa đối tượng.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
1. **Lọc trước (Pre-filtering) quan trọng hơn lọc sau**: Nếu không lọc trước khi tìm kiếm vector, top-k slot sẽ bị chiếm hết bởi các tài liệu sai đối tượng (`buyer` lấn át `seller`), dẫn đến thất bại truy xuất.
2. **Gắn lại tiêu đề trong Heading Chunking**: Khi cắt nhỏ một điều khoản dài, việc chèn lại dòng Heading vào các mảnh con là chìa khóa để chunk con giữ nguyên ngữ cảnh "đây là mục nói về cái gì" khi đứng độc lập trong Vector Store.
3. **Đánh giá 2 mức (Doc ID vs Content Keywords)**: Kiểm tra chỉ bằng Doc ID sẽ gây ảo tưởng về độ chính xác; bắt buộc phải kiểm tra xem chunk truy xuất có chứa con số/từ khóa trả lời được câu hỏi hay không.

**Bài học rút ra khi so sánh trong nhóm:**
> Trên cùng một bộ dữ liệu chính sách, `FixedSizeChunker` có thể đạt điểm số tương tự nhưng chunk đọc rất rời rạc và hay đứt câu giữa chừng. Trong khi đó, `HeadingChunker` và `RecursiveChunker` cho chất lượng đọc và độ mạch lạc ngữ nghĩa vượt trội, giúp LLM dễ dàng trích dẫn nguồn chính xác mà không bị lẫn lộn giữa các điều khoản khác nhau.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ thu thập thêm các trang FAQ ngắn hoặc bảng biểu đối chiếu chi tiết; đồng thời bổ sung thêm các trường metadata như `product_type` (điện thoại / laptop / máy tính bảng) để có thể lọc đa chiều hơn thay vì chỉ dựa vào mỗi trường `audience`.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |

