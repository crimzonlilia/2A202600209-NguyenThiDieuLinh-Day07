# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Thị Diệu Linh
**Nhóm:** 09
**Ngày:** 10/04/2026

### Danh sách thành viên nhóm

| STT | Họ tên | MSSV |
|-----|--------|------|
| 1 | Nguyễn Triệu Gia Khánh | 2A202600225 |
| 2 | Nguyễn Thùy Linh | 2A202600216 |
| 3 | Nguyễn Hoàng Khải Minh | 2A202600159 |
| 4 | Nguyễn Thị Diệu Linh | 2A202600209 |
| 5 | Nguyễn Hoàng Duy | 2A202600158 |
---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> Cosine similarity cao nghĩa là hai vector embedding có hướng gần nhau trong không gian chiều cao, tức là hai văn bản chia sẻ cùng một ý nghĩa hoặc chủ đề chính — dù độ lớn (magnitude) của vector có thể khác nhau.

**Ví dụ HIGH similarity:**
- Sentence A: "Tôi thích ăn phở vào buổi sáng."
- Sentence B: "Buổi sáng tôi thường ăn phở."
- Tại sao tương đồng: Cả hai câu diễn đạt cùng một ý (ăn phở vào buổi sáng) với từ ngữ khác nhau nên vector hướng gần nhau.

**Ví dụ LOW similarity:**
- Sentence A: "Tôi thích ăn phở vào buổi sáng."
- Sentence B: "Hôm qua trời mưa to ở VinUni."
- Tại sao khác: Nội dung và chủ đề khác nhau hoàn toàn, nên vector sẽ có hướng xa nhau.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Vì cosine đo góc giữa hai vector (tức là hướng), nên không bị ảnh hưởng nhiều bởi độ lớn của vector; điều này phù hợp khi embedding có thể khác về độ lớn do độ dài hoặc cường độ từ vựng nhưng vẫn mang cùng ý nghĩa.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* [(10000-50)/(500-50)]

> *Đáp án:* 23 chunks

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> *Viết 1-2 câu:* [(10000-100)/(500-100)] = 25 chunks

> Lý do muốn tăng overlap: overlap lớn hơn giữ nhiều ngữ cảnh qua các biên chunk (giảm mất mát thông tin ở ranh giới), giúp retrieval tìm thông tin liên quan tốt hơn; trade-off là tốn bộ nhớ và chi phí tính toán (nhiều chunk hơn). 

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** IELTS Speaking knowledge base

Nhóm chọn domain IELTS Speaking vì dữ liệu vừa có cấu trúc rõ (part, strategy, ví dụ, lỗi thường gặp), vừa có tính thực dụng để đánh giá chất lượng retrieval. Đây là domain dễ thiết kế benchmark query theo tình huống thật của người học, và có metadata tự nhiên để kiểm thử `search_with_filter`.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | `01_ielts_kb.md` | EnglishExample.md | ~1,500 | source, category, topic, language |
| 2 | `02_ielts_kb.md` | EnglishExample.md | ~2,100 | source, category, topic, language |
| 3 | `03_ielts_kb.md` | EnglishExample.md | ~1,900 | source, category, topic, language |
| 4 | `04_ielts_kb.md` | EnglishExample.md | ~1,800 | source, category, topic, language |
| 5 | `05_ielts_kb.md` | EnglishExample.md | ~1,700 | source, category, topic, language |
| 6 | `06_ielts_kb.md` | EnglishExample.md | ~1,600 | source, category, topic, language |
| 7 | `07_ielts_kb.md` | EnglishExample.md | ~1,700 | source, category, topic, language |
| 8 | `08_ielts_kb.md` | EnglishExample.md | ~1,900 | source, category, topic, language |
| 9 | `09_ielts_kb.md` | EnglishExample.md | ~1,800 | source, category, topic, language |
| 10 | `10_ielts_kb.md` | EnglishExample.md | ~1,600 | source, category, topic, language |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Giá trị cho retrieval |
|----------------|------|---------------|------------------------|
| `source` | string | `ielts_knowledge_base/04_ielts_kb.md` | Truy vết provenance, debug kết quả retrieve |
| `category` | string | `IELTS_Speaking_Strategy` | Lọc đúng nhóm kiến thức bằng `search_with_filter` |
| `topic` | string | `Affect vs Effect` | Tăng precision khi query theo topic hẹp |
| `language` | string | `English` / `Vietnamese` | Ưu tiên tài liệu đúng ngôn ngữ đầu vào |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Nhóm chạy `ChunkingStrategyComparator().compare(text, chunk_size=500)` trên từng file (mẫu 3 file đầu) và trên toàn bộ 10 file nối lại (cùng cách `run_comparison.py`). Số liệu dưới đây lấy từ lần chạy thực tế (`py eval_lab_metrics.py`, `py run_comparison.py`).

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| 01_ielts_kb.md | FixedSizeChunker (fixed_size) | 7 | 178.57 | |
| 01_ielts_kb.md | SentenceChunker (by_sentences) | 6 |206.33 | |
| 01_ielts_kb.md | RecursiveChunker (recursive) | 9 | 137.33 | |
| 02_ielts_kb.md | FixedSizeChunker (fixed_size) | 12 | 195.58 | |
| 02_ielts_kb.md | SentenceChunker (by_sentences) | 7 | 332.14 | |
| 02_ielts_kb.md | RecursiveChunker (recursive) | 17 | 136.59 |  |
| 03_ielts_kb.md | FixedSizeChunker (fixed_size) | 31 | 193.97 | |
| 03_ielts_kb.md | SentenceChunker (by_sentences) | 20 | 298.50 | |
| 03_ielts_kb.md | RecursiveChunker (recursive) | 52 | 114.02 | |

### Strategy Của Tôi
**Loại:** FixedSizeChunker (thay `chunk_size` từ 500 → 200, overlap=10% trong thử nghiệm).

**Mô tả cách hoạt động:**
> Strategy của tôi đơn giản: chia văn bản thành các chunk có độ dài tối đa cố định (`chunk_size`). Trong báo cáo thử nghiệm này tôi giảm `chunk_size` từ 500 xuống 200 để tăng tính granular — mỗi chunk nhỏ hơn, dễ tìm thông tin cụ thể hơn khi truy vấn. Để giữ một ít ngữ cảnh quanh biên, tôi dùng overlap ≈ 10% (ví dụ overlap=20 khi `chunk_size=200`).

**Tại sao chọn cho domain này:**
> Tài liệu IELTS chứa nhiều đoạn ngắn, tips và ví dụ; dùng `FixedSizeChunker` với kích thước nhỏ (200) giúp tăng khả năng trả về chunk chính xác cho câu hỏi ngắn, đồng thời overlap đảm bảo ít mất mát ngữ cảnh ở ranh giới.

**Code snippet (nếu custom):**
```python
# Paste implementation here
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu            | Strategy                                           | Chunk Count | Avg Length | Ghi chú                                                                                      |
| ------------------- | -------------------------------------------------- | ----------- | ---------- | -------------------------------------------------------------------------------------------- |
| IELTS KB (10 files) | Baseline (`SentenceChunker`)                       | 146         | 353.35     | Chunk dài, bám theo câu hoàn chỉnh, giữ ngữ nghĩa tự nhiên                                   |
| IELTS KB (10 files) | **Của tôi (`FixedSizeChunker`, `chunk_size=500`)** | 160         | 322.14     | Chia đều theo kích thước cố định → nhiều chunk hơn, độ dài ổn định nhưng có thể cắt giữa câu |


### So Sánh Với Thành Viên Khác


Điểm **/10** dưới đây là **đánh giá đồng thuận trong nhóm** sau khi xem code, benchmark và demo.


| Thành viên | Strategy (tóm tắt) | Điểm nhóm (/10) | Điểm mạnh | Điểm yếu |
|-------------|-------------------|-----------------|-----------|----------|
| Nguyễn Triệu Gia Khánh | Semantic Chunker | 10 | Các chunk giàu ngữ nghĩa hơn giúp cải thiện độ chính xác của bước retrieval, dẫn đến phản hồi mạch lạc và liên quan hơn từ LLM. | Tính toán embedding và độ tương đồng có thể tốn kém hơn fixed-size chunking. |
| Nguyễn Thùy Linh | SentenceChunker| 10 | Giữ được ngữ nghĩa tự nhiên của câu, ít bị cắt ngang ý giữa câu | Có thể thiếu thông tin quan trọng nếu câu standalone không đủ nghĩa |
| Nguyễn Hoàng Khải Minh | RecursiveChunker | 10 | Cố gắng tôn trọng cấu trúc logic (đoạn văn, câu) của văn bản nhiều nhất có thể trong khi vẫn đảm bảo kích thước chunk phù hợp. | Việc triển khai có thể phức tạp hơn một chút, chi phí tính toán có thể tăng lên do quá trình kiểm tra và chia đệ quy. |
| Nguyễn Thị Diệu Linh | FixedSizeChunker | 10 | Dễ triển khai và quản lý, kích thước chunk đồng nhất giúp đơn giản hóa việc xử lý hàng loạt (batch processing). | Rất dễ phá vỡ cấu trúc ngữ nghĩa tự nhiên của văn bản. Một câu, một ý tưởng quan trọng có thể bị chia cắt làm đôi, nằm ở hai chunk khác nhau, làm giảm chất lượng ngữ cảnh được cung cấp cho LLM. |
| Nguyễn Hoàng Duy | HeadingChunker | 10 | Giữ được context lớn theo từng mục (section-level) | Chunk có thể quá dài, có thể chứa nhiều thông tin không liên quan, giảm precision |

**Kết luận strategy tốt nhất cho dmoain này:**  
Nhóm thống nhất RecursiveChunker làm hướng chính cho IELTS (heading/bullet), đồng thời mỗi thành viên có nhánh so sánh riêng để học chéo. Sau benchmark và demo, nhóm đồng thuận 10/10 cho từng thành viên về đóng góp strategy và phối hợp nhóm.


---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Dùng regex đơn giản để tách câu (pattern bắt các kết thúc bằng `. `, `! `, `? ` hoặc `.` trước newline), sau đó gom nhóm theo `max_sentences_per_chunk`. Xử lý edge-case bằng cách lọc các câu rỗng và đảm bảo `max_sentences_per_chunk >= 1`.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Thuật toán đệ quy thử các separator theo thứ tự ưu tiên (`"\n\n"`, `"\n"`, `". "`, `' '`, `''`) để chia nhỏ mà vẫn cố giữ nguyên ngữ cảnh. Base case là khi đoạn ngắn hơn `chunk_size` hoặc không còn separator; khi đó trả về slice cố định. Khi một fragment quá lớn, hàm đệ quy xuống bộ separators thấp hơn.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> `add_documents` lưu mỗi chunk cùng metadata và embedding (vector). `search` lấy embedding của query, tính cosine similarity với các embedding đã lưu, sắp xếp theo điểm và trả về top-k. Để nhanh, lưu embeddings dưới dạng list/array và dùng vòng lặp hoặc numpy để tính dot product / norm.

**`search_with_filter` + `delete_document`** — approach:
> `search_with_filter` áp dụng filter metadata trước khi tính similarity (lọc candidate pool) để giảm false positives. `delete_document` đánh dấu document/chunk là xoá (soft-delete) hoặc loại bỏ entry khỏi danh sách dữ liệu và embeddings; soft-delete cho phép rollback nếu cần.

### KnowledgeBaseAgent

**`answer`** — approach:
> Agent lấy top-k chunks từ `EmbeddingStore`, chèn chúng vào prompt template (context + instruction + user query) rồi gọi model để sinh câu trả lời. Thêm thông tin metadata (ví dụ `source`, `skill`) vào prompt nếu cần giới hạn phạm vi.

### Test Results

```
# Paste output of: pytest tests/ -v

PS D:\HUST\20252\vinvin\2A202600209-NguyenThiDieuLinh-Day07> pytest tests/ -v    
===================================== test session starts =====================================
platform win32 -- Python 3.13.12, pytest-9.0.3, pluggy-1.6.0 -- D:\HUST\20252\vinvin\2A202600209-NguyenThiDieuLinh-Day07\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\HUST\20252\vinvin\2A202600209-NguyenThiDieuLinh-Day07
plugins: anyio-4.13.0
collected 42 items                                                                             

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED    [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED             [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED      [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED       [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED            [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED  [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED   [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED   [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED              [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED          [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED     [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED       [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED             [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED  [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED    [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED     [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED              [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED             [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED        [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED    [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED   [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED         [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED   [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

===================================== 42 passed in 0.27s ======================================
```
**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Well, I’m a food enthusiast, so there are many cuisines I’m really into. | I also occasionally enjoy Italian food since I have a passion for pizza. | low | 0.0258 | Yes |
| 2 | On a general level, mountains are great choices for a holiday, the nature around them is very comfortable. | One of the most popular activities is hiking. I think it’s popular because I like challenges and danger. | low | 0.2759 | Yes |
| 3 | I think it really depends. If I’m at work, I’d prefer something quick like fast food because I only have a short break. | If I’m out with friends, I’d rather have something more exotic such as Thai or Chinese food. | low | 0.0751 | Yes |
| 4 | The hotel provides great comfort to its guests. | Online shopping provides great convenience. | low | -0.0926 | Yes |
| 5 | I love outdoor activities like hiking and camping. | It was raining, so we decided to play tennis indoors. | low | -0.2390 | Yes |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Pair 2 là kết quả bất ngờ nhất, vì hai câu đều nói về chủ đề liên quan đến du lịch và hoạt động ngoài trời nhưng điểm similarity vẫn khá thấp. Điều này cho thấy embeddings không chỉ dựa vào chủ đề chung mà còn phụ thuộc mạnh vào ngữ cảnh cụ thể và cách diễn đạt; các câu nói về cùng lĩnh vực nhưng khác ý định vẫn có thể bị xem là ít tương đồng.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | In IELTS Speaking Part 2, how should I open my answer in the first 10-15 seconds so I sound clear and on-topic before adding details? | Start with a direct one-sentence answer to the prompt, then extend with reason/example instead of giving background first. |
| 2 | My ideas are too general in Speaking. What exact structure can I use to move from a broad claim to a specific personal example without losing coherence? | Use a 3-step structure: general statement -> narrow reason -> concrete personal example (time/place/result). |
| 3 | If I don't know much about a topic, what is the safest high-control response pattern that avoids silence but still sounds natural and balanced? | Use an "it depends" frame with two short contrasting cases, then close by choosing one side. |
| 4 | During Speaking, when I run out of ideas mid-answer, what language moves can I use to keep fluency while buying thinking time and still add value? | Use filler bridges plus extension templates (reason, example, comparison) to maintain flow instead of stopping abruptly. |
| 5 | For a band-5 to band-6 improvement path, which habit hurts score most in spontaneous speaking and what should I do immediately to replace it? | Avoid switching to L1; stay in English and paraphrase with simpler words when vocabulary gaps appear. |
### Kết Quả Của Tôi
| # | Top-1 (tóm tắt)                                                     | Score (cosine query–chunk) | max cos(gold, chunk) trong top-3 | Tier (script) | Điểm query |
| - | ------------------------------------------------------------------- | -------------------------- | -------------------------------- | ------------- | ---------- |
| 1 | Đoạn về social media nhưng bị cắt mất phần hướng dẫn mở bài         | 0.1482                     | 0.1725                           | partial       | 1/2        |
| 2 | Strategy nói về mở rộng ý nhưng thiếu ví dụ cụ thể                  | 0.1934                     | 0.2110                           | full          | 2/2        |
| 3 | Nội dung liên quan food nhưng lệch intent câu hỏi                   | 0.1217                     | 0.0978                           | partial       | 1/2        |
| 4 | Đoạn có keyword “fluency” nhưng không có hướng dẫn xử lý tình huống | 0.1356                     | 0.1422                           | partial       | 1/2        |
| 5 | Chủ đề technology nhưng chunk bị cắt giữa câu, mất ý chính          | 0.1291                     | 0.1184                           | partial       | 1/2        |

Kết quả cho thấy FixedSizeChunker dẫn đến việc nhiều chunk bị cắt ngang ngữ cảnh, làm giảm độ tương đồng và ảnh hưởng đến khả năng truy hồi chính xác. Dù một số chunk vẫn chứa từ khóa liên quan, việc thiếu thông tin đầy đủ khiến hiệu quả retrieval không ổn định.
---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> *Thành viên trong nhóm đã chỉ cho tôi cách phân chia công việc rõ ràng và giao tiếp hiệu quả khi giải quyết các lỗi phức tạp. Nhờ đó tôi học được cách đặt ưu tiên nhiệm vụ và báo cáo tiến độ ngắn gọn, giúp cả nhóm làm việc trơn tru hơn.*

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> *Qua demo của nhóm khác, tôi thấy một phương pháp tiền xử lý dữ liệu và trực quan hóa kết quả rất trực quan và hiệu quả. Ý tưởng về cách họ lựa chọn mẫu kiểm thử và hiển thị so sánh đã gợi ý cho tôi cải thiện phần báo cáo kết quả của cả nhóm.*

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> *Nếu làm lại, tôi sẽ đầu tư vào việc chuẩn hóa và mở rộng tập dữ liệu (augmentation) đồng thời thêm bước kiểm định chất lượng nhãn (label validation). Ngoài ra sẽ áp dụng sampling phân tầng để đảm bảo dữ liệu huấn luyện phản ánh đủ các trường hợp biên, từ đó cải thiện độ bền và khả năng tổng quát hóa của mô hình.*

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 10 / 10 |
| Chunking strategy | Nhóm | 15 / 15 |
| My approach | Cá nhân | 9 / 10 |
| Similarity predictions | Cá nhân | 5/ 5 |
| Results | Cá nhân | 8 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 5 / 5 |
| **Tổng** | | 97/ 100** |
