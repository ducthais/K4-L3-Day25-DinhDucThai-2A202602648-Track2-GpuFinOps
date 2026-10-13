# NimbusAI — GPU Cost Optimization Report

**Period:** monthly  
**Baseline spend:** $27,133  
**Optimized spend:** $14,626  
**Projected savings:** $12,507  (**46%**)

## Savings by lever

| Lever | Savings (USD) |
|---|---|
| Inference (cascade/cache/batch) | $1,212 |
| Purchasing (spot/reserved) | $10,040 |
| Right-size util-lies | $655 |
| Kill idle GPUs | $600 |

## Sustainability

- Energy per query: 0.24 Wh
- Carbon per query: 0.091 gCO2e
- Cheapest+cleanest region: europe-north1

---

## Executive Summary: Ba Câu Hỏi Cốt Lõi Cho Lãnh Đạo

1. **Trước đây tốn bao nhiêu tiền (Baseline)?**
   - Tổng chi phí hạ tầng GPU hàng tháng là **$27,133**.
   - Đơn vị đo lường hiệu quả LLM Inference trước tối ưu là **$6.488 / 1M-token** (mọi request đều đẩy lên model lớn `large`, không có cache, không xử lý batch).

2. **Sau khi tối ưu còn bao nhiêu (Optimized)?**
   - Tổng chi phí giảm xuống còn **$14,626** hàng tháng (cắt giảm **46.1%** tổng chi phí).
   - Chi phí xử lý Inference giảm ngoạn mục xuống còn **$1.126 / 1M-token** (tiết kiệm **82.6%** chi phí inference).

3. **Từng giải pháp đã giúp tiết kiệm được bao nhiêu (Breakdown từng đòn bẩy)?**
   - **Purchasing Strategy (Spot & Reserved Commitments):** Tiết kiệm **$10,040 / tháng** (chiếm 80.3% tổng số tiền tiết kiệm) nhờ chuyển các job huấn luyện ngắt quãng sang Spot + Checkpointing và cam kết Reserved cho inference 24/7.
   - **Inference Optimization (Cascade Routing + Prompt Caching + Batch API):** Tiết kiệm **$1,212 / tháng** trực tiếp trên lớp gọi API mô hình.
   - **Right-sizing Util-Lies (Khắc phục GPU nói dối):** Tiết kiệm **$655 / tháng** bằng cách chuyển GPU bị nghẽn bộ nhớ xuống loại GPU có băng thông/chi phí tối ưu hơn.
   - **Kill Idle GPUs (Dọn dẹp GPU chạy không tải):** Tiết kiệm **$600 / tháng** nhờ tự động tắt cụm GPU huấn luyện bỏ không qua đêm.

---

## Unit Economics: Baseline vs. Optimized $/1M-Token

Đo lường chi phí LLM theo `$/GPU-giờ` thường che giấu sự lãng phí; đơn vị chuẩn hóa theo FinOps hiện đại là **$/1M-token** (chi phí phục vụ 1 triệu token gồm input + output):

| Chỉ số | Baseline (Trước tối ưu) | Optimized (Sau tối ưu) | Mức độ cải thiện |
|---|---|---|---|
| **Chi phí Inference / ngày** | $48.87 | $8.48 | **-82.6%** |
| **Đơn giá $/1M-token** | $6.488 | $1.126 | **-82.6%** |
| **Tổng token xử lý / ngày** | 7,533,027 | 7,533,027 | Duy trì 100% throughput |
| **Cấu hình mô hình** | 100% Large Model ($3/$15) | 80% Small ($0.2/$0.4) + 20% Large | Cascade routing tự động |
| **Tỷ lệ Cache hit input** | 0% (Tắt cache) | 31.9% toàn fleet (51% tại Chat/RAG) | Chiết khấu 90% input cache |
| **Tỷ lệ Batch API** | 0% (Real-time hết) | 100% traffic Eval (chiết khấu 50%) | Tận dụng SLA linh hoạt |

---

## Phân tích Chi tiết Từng Đòn Bẩy Tiết Kiệm (FinOps Levers)

### 1. Đòn bẩy Mua sắm (Purchasing Strategy: Spot + Reserved)
- **Mô hình hóa điểm hòa vốn (Break-even Utilization):** Với mức chiết khấu Reserved 45% (3 năm), điểm hòa vốn là `1 - 0.45 = 55%` (tương đương 13.2 giờ/ngày).
- **Quy tắc phân tầng (Tier Recommendation):**
  - Các job có thể ngắt quãng (`interruptible=1`, ví dụ: huấn luyện LLM, embedding, finetuning, dev sandbox) được chuyển sang **Spot Instance** kết hợp lưu checkpoint định kỳ.
  - Các job phục vụ inference 24/7 (`interruptible=0`, duty cycle 100% >= 55%) được cam kết **Reserved Instance**.
  - Kết quả: Chi phí mua sắm hàng tháng giảm từ **$25,667** xuống **$15,627**, tiết kiệm **$10,040/tháng (39.1%)**.

### 2. Đòn bẩy Inference (Cascade, Cache, Batch)
- **Cascade Routing (Định tuyến tầng):** Khoảng 80% truy vấn thực tế có độ phức tạp thấp được chuyển sang model nhỏ (giá $0.20/$0.40 thay vì $3.00/$15.00 của model lớn, rẻ hơn 15–37 lần).
- **Prompt Caching:** Các team Assistant Chat và RAG Doc-QA có tỷ lệ tiền tố (system prompt, ngữ cảnh tài liệu) trùng lặp cao (trên 50%). Phần input đã cache chỉ tính 10% giá gốc (chiết khấu 90%).
- **Batch API:** Lưu lượng đánh giá nightly eval không cần phản hồi tức thì được gộp batch để hưởng chiết khấu 50%.
- **Hiệu ứng nhân dồn (Discount Stack):** Batch API kết hợp 100% cache hit đạt hệ số chi phí chỉ `0.5 × 0.1 = 0.05` (tiết kiệm tới 95% chi phí naive).

### 3. Khắc phục GPU "Nói Dối" (Right-sizing Util-Lies)
- **Hiện tượng:** GPU `gpu-h100-4` ghi nhận `nvidia-smi` GPU-Util đạt **98.2%**, nhưng MFU (Model FLOPs Utilization) chỉ đạt **0.194** (19.4%) và MBU chỉ đạt **0.207** (20.7%). Tương tự, `gpu-a10g-1` ghi nhận GPU-Util **96.9%** nhưng MFU chỉ **0.268**.
- **Nguyên nhân cốt lõi:** `nvidia-smi` chỉ đo tỷ lệ thời gian xung nhịp nhân SM đang tích cực (clock is active), không đo FLOPs hay hiệu quả xử lý thực sự. Workload bị nghẽn bộ nhớ (memory stall), I/O wait hoặc kernel launch overhead cao khiến GPU tiêu tốn điện năng và tiền thuê nhưng sản lượng tính toán rất thấp.
- **Giải pháp Right-sizing:** Chuyển `gpu-h100-4` (H100 $2.50/hr) sang A100 ($1.79/hr) với đủ 80GB VRAM và 2.0 TB/s băng thông, và chuyển `gpu-a10g-1` (A10G $1.00/hr) sang L4 ($0.80/hr). Tiết kiệm **$655/tháng** mà không hề làm suy giảm SLA.

### 4. Xóa Bỏ Lãng Phí Chạy Không Tải (Kill Idle GPUs)
- **Phát hiện:** GPU `gpu-h100-5` bị bỏ trống 8 giờ mỗi đêm sau khi job huấn luyện hoàn tất (utilization < 10%).
- **Hành động:** Thiết lập chính sách auto-shutdown / idle reaper sau 15 phút không tải.
- **Tiết kiệm:** $20.00/ngày, tương đương **$600/tháng**.

---

## Phân Bổ Chi Phí & Sẵn Sàng Chargeback (Cost Allocation & FOCUS)

| Nhóm (Team) | Chi phí Inference ($/ngày) | Tỷ lệ (%) | Dự án chính |
|---|---|---|---|
| **assistant** | $2.59 | 30.5% | chat |
| **search** | $2.49 | 29.4% | web-search |
| **eval** | $1.79 | 21.1% | nightly-eval |
| **rag** | $1.60 | 18.9% | doc-qa |

- **Tag Coverage Đạt 92%:** Vượt ngưỡng quy định **80%**, đảm bảo công ty đủ điều kiện chuyển từ giai đoạn *Showback* (minh bạch chi phí) sang *Chargeback* (thực thu ngân sách nội bộ).
- **Tuân thủ Chuẩn FOCUS 1.0:** Dữ liệu chi phí đã được trích xuất thành công ra file `outputs/focus_export.csv` với các thuộc tính chuẩn hóa (`BillingAccountId`, `ServiceCategory`, `BilledCost`, `Tags`).

---

## Tính Bền Vững & Tối Ưu Năng Lượng / Carbon

- **Năng lượng trung bình:** 0.24 Wh / truy vấn thông thường; tuy nhiên các truy vấn Reasoning tiêu thụ tới 19.2 Wh / truy vấn (~80 lần).
- **Lượng phát thải trung bình:** 0.091 gCO2e / truy vấn tại vùng mặc định `us-east-1`.
- **Chiến lược chọn vùng (Multi-Region Scheduling):**
  - Vùng sạch nhất: **europe-north1** (Na Uy, 30 gCO2/kWh) giảm tới **92.1% lượng carbon** so với `us-east-1`.
  - Vùng chi phí điện rẻ nhất: **us-east-wa** ($0.055/kWh) giảm **54.2% chi phí điện năng**.

---

## Kế Hoạch Hành Động Đề Xuất (Prioritized FinOps Roadmap)

1. **P0 — Ngay lập tức (Quick Wins, ROI tức thì, Rủi ro = 0):**
   - Kích hoạt Auto-Termination Reaper cho GPU idle quá 15 phút (tiết kiệm ngay $600/tháng).
   - Chuyển 5 job training/eval có thể ngắt quãng sang Spot Instances với checkpointing tự động (tiết kiệm ngay $10,040/tháng).
2. **P1 — Trong vòng 2 tuần (Inference Platform Optimization):**
   - Cấu hình LiteLLM Gateway kích hoạt Cascade Routing (chuyển 80% truy vấn đơn giản sang small model).
   - Bật Prompt Caching cho Assistant Chat và RAG Doc-QA (giảm chi phí $/1M-token từ $6.488 xuống $1.126).
3. **P2 — Trong tháng đầu tiên (Fleet Governance & Right-sizing):**
   - Hạ cấp các GPU bị util-lie (chuyển `gpu-h100-4` sang A100, `gpu-a10g-1` sang L4, tiết kiệm $655/tháng).
   - Áp dụng cổng thanh toán Chargeback nội bộ dựa trên dữ liệu tag FOCUS 92% coverage.

_Figures are June-2026 as-of snapshots; re-baseline before acting._