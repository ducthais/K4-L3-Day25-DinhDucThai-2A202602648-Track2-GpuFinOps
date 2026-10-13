# Báo Cáo Kỹ Thuật FinOps: Chiến Lược Tối Ưu Hóa Chi Phí GPU Tại NimbusAI

> **Tác giả:** FinOps Lead / GPU Infrastructure Engineer  
> **Dự án:** NimbusAI LLM Platform Optimization (Lab 25 — GPU FinOps Workshop)  
> **Ngày báo cáo:** 13/10/2026 · **Kỳ đánh giá:** Hàng tháng (Monthly Snapshot)  
> **Tài liệu tham chiếu:** [outputs/report.md](file:///d:/Repo/K4-L3-Day25-DinhDucThai-2A202602648-Track2-GpuFinOps/outputs/report.md) · [outputs/savings.png](file:///d:/Repo/K4-L3-Day25-DinhDucThai-2A202602648-Track2-GpuFinOps/outputs/savings.png) · [outputs/focus_export.csv](file:///d:/Repo/K4-L3-Day25-DinhDucThai-2A202602648-Track2-GpuFinOps/outputs/focus_export.csv)

---

## 1. Baseline vs. Optimized: Bức Tranh Toàn Cảnh & Hiệu Quả Đơn Vị ($/1M-Token)

Trong bối cảnh chi phí thuê GPU đám mây tăng vọt, cách tiếp cận truyền thống là đo lường hóa đơn theo `$/GPU-giờ` thường che giấu sự lãng phí nghiêm trọng. Một đội ngũ có thể trả cùng mức `$/GPU-giờ` nhưng đội tối ưu tốt hơn có thể phục vụ số lượng token gấp 5–10 lần. Do đó, nhóm FinOps tại NimbusAI đã chuẩn hóa toàn bộ mô hình đo lường theo **`$/1M-token`** (chi phí phục vụ 1 triệu token, tính gộp cả input và output) song song với tổng chi phí hạ tầng (TCO).

### Bảng So Sánh Chỉ Số Trước & Sau Tối Ưu

| Hạng mục / Chỉ số | Baseline (Trước tối ưu) | Optimized (Sau tối ưu) | Mức độ cắt giảm | Ý nghĩa kinh tế |
|---|---|---|---|---|
| **Tổng chi phí hạ tầng / tháng** | **$27,133** | **$14,626** | **-46.1% (-$12,507)** | Giảm gần một nửa chi phí vận hành fleet GPU |
| **Chi phí Inference / ngày** | **$48.87 / ngày** | **$8.48 / ngày** | **-82.6% (-$40.39)** | Cắt giảm hơn 82% tiền API mô hình hàng ngày |
| **Đơn giá $/1M-token (Inference)** | **$6.488** | **$1.126** | **-82.6% (-$5.362)** | Hiệu quả phục vụ tăng 5.76 lần trên cùng sản lượng |
| **Tổng số token xử lý** | 7,533,027 tokens/ngày | 7,533,027 tokens/ngày | Giữ nguyên 100% | Đáp ứng 100% SLA và throughput của người dùng |
| **Tỷ lệ truy vấn mô hình lớn (Large)** | 100% | 20% | Giảm 80% | 80% truy vấn đơn giản được cascade sang Small Model |
| **Tỷ lệ Cache hit đầu vào** | 0% (Không cache) | 31.9% toàn fleet (51% tại Chat/RAG) | Tăng từ 0% lên 31.9% | Chiết khấu 90% cho token tái sử dụng |
| **Tỷ lệ Batch API** | 0% (Real-time 100%) | 100% traffic nightly-eval | Chiết khấu 50% | Tận dụng cơ chế asynchronous batch processing |

**Ba câu trả lời cốt lõi cho Ban Giám Đốc:**
1. *Trước đây tốn bao nhiêu tiền?* Hóa đơn hàng tháng là **$27,133**, tương ứng chi phí inference **$6.488 / 1M-token**.
2. *Sau khi tối ưu còn bao nhiêu?* Chi phí hàng tháng giảm xuống còn **$14,626**, chi phí inference chỉ còn **$1.126 / 1M-token**.
3. *Đã tiết kiệm được bao nhiêu?* Tiết kiệm **$12,507 / tháng (46.1% tổng chi phí)**, trong đó tầng inference tiết kiệm **82.6%**.

---

## 2. Phân Tích Chuyên Sâu Từng Đòn Bẩy Tiết Kiệm (FinOps Levers)

Khoản ngân sách tiết kiệm **$12,507 / tháng** được tạo thành từ 4 đòn bẩy độc lập:

```
+-----------------------------------------------------------------------------------------+
|                  NIMBUSAI GPU COST REDUCTION WATERFALL ($27,133 -> $14,626)             |
+-----------------------------------------------------------------------------------------+
|  Baseline Spend: $27,133/tháng                                                          |
|    |-- [1] Purchasing Strategy (Spot + Reserved):  -$10,040/tháng (80.3% tổng savings)  |
|    |-- [2] Inference Platform (Cascade/Cache/Batch):-$1,212/tháng  (9.7% tổng savings)  |
|    |-- [3] Right-sizing Memory-bound Util-Lies:     -$655/tháng   (5.2% tổng savings)   |
|    `-- [4] Killing Overnight Idle GPUs:             -$600/tháng   (4.8% tổng savings)   |
|  = Optimized Spend: $14,626/tháng (Tiết kiệm ròng 46.1%)                               |
+-----------------------------------------------------------------------------------------+
```

### Đòn bẩy nào đóng góp lớn nhất? Tại sao?
- **Purchasing Strategy (Spot & Reserved)** là đòn bẩy đóng góp lớn nhất, mang lại **$10,040 / tháng (chiếm 80.3% tổng số tiền tiết kiệm)**.
- **Nguyên nhân cốt lõi:** Các workload huấn luyện mô hình nền tảng (Foundation training như `job-train-llm`, embedding, fine-tuning) ngốn số lượng GPU-giờ khổng lồ (cụm 8×H100, 4×A100). Trong mô hình On-Demand nguyên bản, NimbusAI phải trả trần giá cao nhất ($2.50/h cho H100). Khi phân loại đúng đặc tính công việc:
  - Các job batch có thể ngắt quãng (`interruptible=1`) được chuyển sang **Spot Instance** với giá chỉ $1.50/h (giảm 40%), kết hợp lưu checkpoint định kỳ 1 giờ/lần.
  - Các job inference chạy liên tục 24/7 (`duty cycle = 100%`, vượt xa điểm hòa vốn 55%) được cam kết **Reserved 3-year** với giá chỉ $1.40/h (giảm 44%).
  - Khoản chiết khấu phần trăm lớn áp dụng trên quy mô hàng nghìn GPU-giờ đã tạo ra giá trị tuyệt đối vượt trội.

### Đòn bẩy Inference có vai trò gì?
- Mặc dù giá trị tuyệt đối là **$1,212 / tháng**, đòn bẩy Inference có **tỷ lệ cắt giảm chi phí đơn vị cao nhất (82.6%)**, đưa đơn giá từ **$6.488** xuống **$1.126 / 1M-token**.
- Sự kết hợp cấp số nhân (Discount Stack):
  - **Cascade routing:** Chuyển 80% lưu lượng đơn giản sang model nhỏ (giá $0.20/$0.40 thay vì $3.00/$15.00 của model lớn, rẻ hơn 15–37 lần).
  - **Prompt Caching:** Giảm 90% chi phí cho phần input lặp lại (ở Chat và RAG tỷ lệ cache hit > 50%).
  - **Batch API:** Giảm thêm 50% cho lưu lượng eval. Khi gộp batch và 100% cache hit, hệ số chi phí thực tế chỉ còn `0.5 × 0.1 = 0.05` (giảm 95% so với naive)!

---

## 3. Giải Mã Hiện Tượng "GPU-Util Lie" & Tác Động Tài Chính

### Phát hiện từ Telemetry
Trong 11 GPU thuộc đội tàu tính toán, lệnh `nvidia-smi` báo cáo 2 trường hợp bất thường nghiêm trọng:
1. **`gpu-h100-4` (H100):** `GPU-Util = 98.2%`, nhưng **MFU (Model FLOPs Utilization) chỉ đạt 0.194 (19.4%)**, và **MBU (Model Bandwidth Utilization) chỉ đạt 0.207**.
2. **`gpu-a10g-1` (A10G):** `GPU-Util = 96.9%`, nhưng **MFU chỉ đạt 0.268 (26.8%)**, và MBU đạt 0.302.

### Cơ chế kỹ thuật: Tại sao GPU-Util 98% lại là "Nói Dối"?
- **`nvidia-smi` GPU-Util thực chất đo gì?** Chỉ số này đo tỷ lệ phần trăm thời gian trong chu kỳ lấy mẫu mà ít nhất một nhân xử lý (Streaming Multiprocessor - SM) có xung nhịp hoạt động (`clock is active`). Nó **KHÔNG đo số phép tính dấu phẩy động (FLOPs)** thực sự được thực thi.
- **Nguyên nhân gốc rễ:**
  - **Memory Stalls:** Workload giải mã LLM (Decode) có tỷ số tính toán trên bộ nhớ rất thấp (Arithmetic Intensity ~1–2 FLOP/byte, nằm sâu trong vùng *memory-bound* của Roofline Model so với đỉnh ridge 295 FLOP/byte của H100). Nhân SM phải dừng chờ dữ liệu tải từ HBM (High Bandwidth Memory) qua thanh ghi. Trong lúc chờ, xung nhịp vẫn quay, `nvidia-smi` vẫn ghi nhận 100% bận rộn, nhưng số phép tính thực tế chỉ đạt 1/5 công suất cực đại.
  - **Over-provisioning:** Workload chạy trên `gpu-h100-4` chỉ đạt đỉnh 225.5 TFLOPs, 0.91 TB/s băng thông và chiếm 40GB VRAM. Việc cấp phát một chiếc H100 ($2.50/h, 990 TFLOPs, 3.35 TB/s, 80GB HBM) cho tác vụ này tương tự như "dùng xe tải hạng nặng để chở bưu phẩm".

### Tác động tài chính
- Doanh nghiệp phải trả đủ 100% giá thuê H100 ($2.50/giờ = $1,800/tháng) nhưng chỉ nhận được giá trị tính toán tương đương một GPU hạng trung.
- **Giải pháp Right-sizing:** Chuyển `gpu-h100-4` sang A100 ($1.79/h) và `gpu-a10g-1` sang L4 ($0.80/h). Băng thông và dung lượng VRAM của A100 (80GB, 2.0 TB/s) và L4 (24GB, 0.3 TB/s) thừa sức đáp ứng nhu cầu thực tế với hệ số an toàn >120%, giúp tiết kiệm ngay **$655.20 / tháng ($7,862 / năm)**.

---

## 4. Báo Cáo Triển Khai 5/5 Phần Mở Rộng ("Your Turn" Extensions)

Chúng tôi đã triển khai đầy đủ cả **5 phần mở rộng** với mã nguồn thực tế và số liệu định lượng:

### Extension 1: Nâng Cấp Thuật Toán Phân Tầng Mua Sắm (`recommend_tier()`)
- **Code triển khai:** Cập nhật `finops/pricing.py` và `missions/m3_purchasing.py`. Thêm các tham số `job_days`, `gpu_type`, `interruption_rate` và so sánh 1yr vs 3yr commitment.
- **Số liệu trước/sau:**
  - *Baseline Policy:* Chỉ so sánh `hours_per_day >= 13.2h` và `interruptible`. Gán 3 job vào 3-year reserved và 5 job vào spot.
  - *Advanced Policy:* Xét thêm thời hạn job (`days`) và điểm hòa vốn 1 năm.
    - Với `job-infer-search` (L4, 18h/ngày, duty cycle = 75%): Ở mức cam kết 3 năm (chiết khấu 43.75%, điểm hòa vốn 56.25%), reserved tiết kiệm được $756/tháng ($972 vs $1,728 on-demand). Tuy nhiên ở mức cam kết 1 năm (chiết khấu 25%, điểm hòa vốn đúng bằng 75%), chi phí reserved bằng đúng chi phí on-demand.
    - Với các job ngắn ngày (`job-train-embed` 5 ngày, `job-finetune` 3 ngày), thuật toán ưu tiên spot để tránh rủi ro khóa vốn (capital lock-in).
- **Insight:** Cam kết 1 năm chỉ có lợi khi duty cycle $\ge$ 75–80%; cam kết 3 năm chỉ nên dành cho core inference có thời gian khai thác trên 18 tháng.

### Extension 2: Right-sizing Theo MBU & Chi Phí $/GB-VRAM
- **Code triển khai:** Hàm `recommend_rightsize_gpu()` trong `finops/metrics.py` và tích hợp vào `missions/m1_efficiency_audit.py`.
- **Số liệu trước/sau:**
  - Bảng catalog chuẩn hóa: H100 ($0.0312/GB-h, $0.746/(TB/s)-h) vs A100 ($0.0224/GB-h, $0.895/(TB/s)-h) vs L4 ($0.0333/GB-h).
  - `gpu-h100-4` (H100 $2.50/h): Hạ cấp xuống A100 ($1.79/h) $\implies$ Tiết kiệm $0.71/h (-28.4%) = **$511.20 / tháng**.
  - `gpu-a10g-1` (A10G $1.00/h): Hạ cấp xuống L4 ($0.80/h) $\implies$ Tiết kiệm $0.20/h (-20.0%) = **$144.00 / tháng**.
  - Tổng tiết kiệm: **$655.20 / tháng**.
- **Insight:** Tuyệt đối không chọn GPU chỉ dựa trên giá rẻ nhất `$/GPU-hr`. Nếu chọn L4 ($0.80/h) cho job của `gpu-h100-4`, hệ thống sẽ lập tức crash do tràn bộ nhớ (OOM, workload cần 40GB trong khi L4 chỉ có 24GB). Right-sizing buộc phải đối chiếu đồng thời cả 3 chiều: FLOPs, Bandwidth và VRAM.

### Extension 3: Mô Hình Kinh Tế Prompt Caching (`cache_is_worth_it()`)
- **Code triển khai:** Các hàm `cache_break_even_reads()` và `cache_is_worth_it()` trong `finops/pricing.py`, tích hợp vào `missions/m2_inference_levers.py`.
- **Số liệu trước/sau:**
  - Công thức điểm hòa vốn: $N_{be} = \frac{P_{write}}{P_{in} \times (1 - \text{read\_discount})} = \frac{1.25 \times P_{in}}{0.90 \times P_{in}} \approx 1.39 \text{ lần đọc}$.
  - Ngưỡng tối thiểu: Một prompt prefix phải được đọc lại **ít nhất 2 lần** thì việc ghi cache mới có lãi.
  - Kiểm tra dataset `token_usage.csv`:
    - Dự án `assistant/chat`: 732 truy vấn, tỷ lệ cached token đạt **50.5%** (trung bình tiền tố được đọc lại >50 lần).
    - Dự án `rag/doc-qa`: 517 truy vấn, tỷ lệ cached token đạt **51.1%**.
  - Kết luận: `cache_is_worth_it()` trả về `True` với biên độ an toàn cực lớn. Nếu áp dụng cho tác vụ one-off (không tái sử dụng), ghi cache sẽ làm tăng 25% chi phí vô ích.

### Extension 4: Phân Bổ Ngân Sách & Năng Lượng Cho Truy Vấn Reasoning
- **Code triển khai:** Tích hợp phân tích dữ liệu reasoning trong `missions/m2_inference_levers.py` và `missions/run_extensions.py`.
- **Số liệu trước/sau:**
  - Số lượng truy vấn Reasoning: **201 / 2,400 truy vấn (chỉ chiếm 8.38% lưu lượng)**.
  - Sản lượng output token: Reasoning sinh ra trung bình **3,875 token/truy vấn** (gấp 6.04 lần so với 641 token của truy vấn thường).
  - Năng lượng tiêu thụ:
    - Truy vấn thường: tiêu thụ 1,887.6 Wh (chỉ chiếm **6.0%** tổng điện năng inference).
    - Truy vấn Reasoning: tiêu thụ **29,787.7 Wh (chiếm tới 94.0% tổng điện năng inference)**!
    - Mỗi truy vấn Reasoning tiêu thụ trung bình **148.2 Wh**, gấp **172.6 lần** một truy vấn thông thường (0.86 Wh)!
- **Đề xuất kiểm soát:** Thiết lập Complexity Gate (chỉ route sang reasoning khi điểm độ khó > 0.85); khống chế trần lưu lượng reasoning ở mức 5% traffic.

### Extension 5: Điều Phối Nhận Thức Carbon (Carbon-Aware Scheduling)
- **Code triển khai:** Đánh giá 5 vùng điện toán trong `missions/m3_purchasing.py` và `missions/run_extensions.py`.
- **Số liệu trước/sau:**
  - 5 job training/eval có thể ngắt quãng tiêu thụ tổng cộng **1,789.0 kWh** điện năng.
  - So sánh 5 vùng đám mây:
    - `us-east-1` (Mặc định): Lưới điện 380 gCO2/kWh, giá $0.120/kWh $\implies$ Phát thải **679.8 kg CO2e**, tiền điện **$214.68**.
    - `europe-north1` (Na Uy - Thủy điện sạch): 30 gCO2/kWh, giá $0.090/kWh $\implies$ Phát thải **53.7 kg CO2e (GIẢM 92.1%, cắt giảm 626.1 kg CO2e)**, tiền điện $161.01 (giảm 25.0%).
    - `us-east-wa` (Washington - Thủy điện rẻ): 90 gCO2/kWh, giá $0.055/kWh $\implies$ Phát thải **161.0 kg CO2e (giảm 76.3%)**, tiền điện **$98.39 (GIẢM 54.2%, tiết kiệm $116.29)**.
    - `europe-central2` (Ba Lan - Than đá): 660 gCO2/kWh $\implies$ Phát thải tới 1,180.7 kg CO2e (+73.7%).
- **Đánh giá Trade-off:** Các job huấn luyện mô hình là tác vụ chạy nền (offline batch processing), không có người dùng chờ phản hồi thời gian thực. Việc điều phối sang `europe-north1` hoặc `us-east-wa` hoàn toàn không bị ảnh hưởng bởi độ trễ mạng nhưng mang lại lợi ích môi trường và tài chính khổng lồ.

---

## 5. Khuyến Nghị Dành Cho Lãnh Đạo NimbusAI: Top 3 Hành Động Ưu Tiên

Nếu được giao trọng trách FinOps Lead tại NimbusAI, đây là 3 hành động chiến lược tôi sẽ ban hành ngay trong 30 ngày tới:

| Ưu tiên | Hành động chiến lược | Lợi ích tài chính & Vận hành | Mức độ nỗ lực / Rủi ro | Thời gian hoàn thành |
|---|---|---|---|---|
| **1 (P0)** | **Bật Auto-Reaper diệt Idle GPU & Chuyển Batch Workloads sang Spot + Checkpoint** | Tiết kiệm ngay **$10,640 / tháng** ($10,040 từ Spot + $600 từ Idle). Cắt giảm 85% tổng lãng phí. | **Thấp / Không rủi ro** (Có checkpointing tự động lo liệu eviction). | Ngay trong **48 giờ** đầu tiên. |
| **2 (P1)** | **Triển khai LiteLLM Gateway với Cascade Routing & Prompt Caching** | Giảm chi phí inference **82.6%** (từ $6.488 xuống $1.126 / 1M-token). Tiết kiệm **$1,212 / tháng**. | **Trung bình** (Cần thiết lập quy tắc classifier phân loại query). | Trong vòng **2 tuần**. |
| **3 (P2)** | **Right-sizing GPU Util-Lies & Kích Hoạt Cổng Chargeback Nội Bộ (FOCUS)** | Tiết kiệm **$655 / tháng** từ việc hạ cấp phần cứng; Tag coverage đạt 92% giúp thu hồi ngân sách minh bạch. | **Trung bình** (Cần phối hợp với các team product/search). | Trong vòng **30 ngày**. |

---

## 6. Kết Luận

Dự án GPU FinOps tại NimbusAI đã chứng minh rằng: **Chi phí GPU hoàn toàn có thể kiểm soát và tối ưu hóa từ 40% đến hơn 80% mà không làm giảm chất lượng mô hình hay vi phạm SLA**. Bằng việc chuyển dịch tư duy từ `$/GPU-giờ` sang `$/1M-token`, vạch trần "GPU-Util Lie" thông qua MFU/MBU, và kết hợp hài hòa giữa kỹ thuật mua sắm đám mây với tối ưu hóa suy luận LLM, NimbusAI đã thiết lập một nền tảng hạ tầng vững chắc, tiết kiệm và bền vững cho giai đoạn tăng trưởng tiếp theo.
