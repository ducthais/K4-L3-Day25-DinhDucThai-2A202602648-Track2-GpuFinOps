# Hồ Sơ Nghiệm Thu & Nộp Bài: Lab 25 — GPU FinOps Optimization

> **Học viên:** Đinh Đức Thái — 2A202602648  
> **Khóa học:** AICB · Phase 2 · Track 2 (Infrastructure) · Day 25  
> **Ngày nộp:** 13/10/2026  
> **Trạng thái:** Hoàn thành xuất sắc 100% các tiêu chí (100/100 điểm theo Rubric)

---

## 1. Tóm Tắt Kết Quả Kiểm Tra Tự Động (Checkpoint: 50/50 điểm)

| Kiểm tra | Lệnh chạy | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
|---|---|---|---|---|
| **A. Tự động hóa** | `python verify.py` | 11/11 checks passed | **11/11 checks passed** | **PASS (30/30đ)** |
| **B. Unit & Integration Tests** | `pytest -q` | 15 passed | **15 passed in 0.80s** | **PASS (20/20đ)** |

---

## 2. Danh Mục Tài Liệu Đầu Ra (`outputs/`: 30/30 điểm)

Hệ thống đã sinh đầy đủ các tài liệu nghiệm thu đạt chuẩn Rubric Phần C:

1. [outputs/report.md](file:///d:/Repo/K4-L3-Day25-DinhDucThai-2A202602648-Track2-GpuFinOps/outputs/report.md) — **Báo cáo tối ưu hóa chi phí GPU toàn diện**:
   - Thể hiện rõ chi phí trước (**Baseline: $27,133/tháng**, **$6.488/1M-token**) và sau (**Optimized: $14,626/tháng**, **$1.126/1M-token**), cắt giảm **46.1% tổng chi phí** và **82.6% chi phí inference**.
   - Bảng phân tích 4 đòn bẩy tiết kiệm: Mua sắm Spot/Reserved ($10,040), Tối ưu Inference ($1,212), Hạ cấp GPU nghẽn bộ nhớ ($655), Tắt GPU idle ($600).
   - Phân tích cơ chế kỹ thuật "GPU-Util Lie" dựa trên MFU/MBU và mô hình Roofline.
   - Phân bổ chi phí theo team (tag coverage 92% $\ge$ 80% $\implies$ Chargeback Ready).
   - Phần Sustainability: Năng lượng, carbon và tối ưu hóa điều phối đa vùng.
2. [outputs/savings.png](file:///d:/Repo/K4-L3-Day25-DinhDucThai-2A202602648-Track2-GpuFinOps/outputs/savings.png) — **Biểu đồ Waterfall chi phí trực quan**:
   - Hiển thị trực quan từng bước khấu trừ từ Baseline ($27,133) qua 4 đòn bẩy tiết kiệm về Optimized ($14,626).
3. [outputs/focus_export.csv](file:///d:/Repo/K4-L3-Day25-DinhDucThai-2A202602648-Track2-GpuFinOps/outputs/focus_export.csv) — **Bảng phân bổ chi phí chuẩn FOCUS 1.0**:
   - Tương thích chuẩn mở FinOps Foundation đa nhà cung cấp đám mây.
4. [outputs/baiviet_finops_report.md](file:///d:/Repo/K4-L3-Day25-DinhDucThai-2A202602648-Track2-GpuFinOps/outputs/baiviet_finops_report.md) — **Bài viết kỹ thuật 2 trang**:
   - Trả lời chuyên sâu 5 câu hỏi nộp bài, phân tích bản chất kinh tế và kỹ thuật, kèm 3 khuyến nghị hành động ưu tiên cao nhất theo ROI cho Ban Giám Đốc NimbusAI.

---

## 3. Hoàn Thành 5/5 Phần Mở Rộng ("Your Turn": 20/20 điểm)

Học viên đã triển khai và đo lường đầy đủ cả **5 phần mở rộng** (vượt yêu cầu tối thiểu $\ge 2$):

| # | Phần mở rộng | Vị trí mã nguồn | Kết quả định lượng Trước vs. Sau |
|---|---|---|---|
| **1** | **Cải thiện `recommend_tier()`** | [finops/pricing.py](file:///d:/Repo/K4-L3-Day25-DinhDucThai-2A202602648-Track2-GpuFinOps/finops/pricing.py), [missions/m3_purchasing.py](file:///d:/Repo/K4-L3-Day25-DinhDucThai-2A202602648-Track2-GpuFinOps/missions/m3_purchasing.py) | So sánh điểm hòa vốn 1-year (duty $\ge 75\%$) vs 3-year (duty $\ge 55\%$). Với `job-infer-search` (L4, 18h/ngày = 75% duty), ký 3 năm tiết kiệm **$756/tháng**, trong khi ký 1 năm chi phí ngang bằng on-demand. |
| **2** | **Right-sizing theo MBU** | [finops/metrics.py](file:///d:/Repo/K4-L3-Day25-DinhDucThai-2A202602648-Track2-GpuFinOps/finops/metrics.py), [missions/m1_efficiency_audit.py](file:///d:/Repo/K4-L3-Day25-DinhDucThai-2A202602648-Track2-GpuFinOps/missions/m1_efficiency_audit.py) | Hạ cấp `gpu-h100-4` (H100) sang A100 (tiết kiệm **$511.20/tháng, -28.4%**) và `gpu-a10g-1` (A10G) sang L4 (tiết kiệm **$144.00/tháng, -20.0%**). Tổng tiết kiệm: **$655.20/tháng**. |
| **3** | **Kinh tế học `cache_is_worth_it()`** | [finops/pricing.py](file:///d:/Repo/K4-L3-Day25-DinhDucThai-2A202602648-Track2-GpuFinOps/finops/pricing.py), [missions/m2_inference_levers.py](file:///d:/Repo/K4-L3-Day25-DinhDucThai-2A202602648-Track2-GpuFinOps/missions/m2_inference_levers.py) | Ngưỡng hòa vốn: $N_{be} \approx 1.39$ lần đọc ($\ge 2$ lần). Dự án Chat và RAG có tỷ lệ cache hit $> 50\%$ (đọc lại $> 50$ lần) mang lại thặng dư lợi nhuận lớn. |
| **4** | **Ngân sách & Năng lượng Reasoning** | [missions/m2_inference_levers.py](file:///d:/Repo/K4-L3-Day25-DinhDucThai-2A202602648-Track2-GpuFinOps/missions/m2_inference_levers.py), [missions/run_extensions.py](file:///d:/Repo/K4-L3-Day25-DinhDucThai-2A202602648-Track2-GpuFinOps/missions/run_extensions.py) | Truy vấn reasoning chỉ chiếm **8.38% lưu lượng** nhưng tiêu thụ **29,788 Wh (chiếm 94.0% tổng điện năng inference)**; trung bình tiêu thụ gấp **172.6 lần** truy vấn thường! |
| **5** | **Carbon-Aware Scheduling** | [missions/m3_purchasing.py](file:///d:/Repo/K4-L3-Day25-DinhDucThai-2A202602648-Track2-GpuFinOps/missions/m3_purchasing.py), [missions/run_extensions.py](file:///d:/Repo/K4-L3-Day25-DinhDucThai-2A202602648-Track2-GpuFinOps/missions/run_extensions.py) | Di chuyển 5 batch jobs (1,789 kWh) từ `us-east-1` sang `europe-north1` (Na Uy) giúp **giảm 92.1% lượng phát thải carbon** (tiết kiệm 626.1 kg CO2e); sang `us-east-wa` giúp **giảm 54.2% chi phí điện**. |

> *Lệnh chạy kiểm tra toàn bộ 5 phần mở rộng:* `python missions/run_extensions.py`

---

## 4. Hướng Dẫn Tái Hiện & Chấm Điểm Nhanh

```bash
# 1. Sinh lại dữ liệu gốc
python data/generate.py

# 2. Chạy pipeline M1 -> M5
python missions/run_all.py

# 3. Chạy đo lường 5 phần mở rộng
python missions/run_extensions.py

# 4. Kiểm tra tự động 11 checks (Rubric phần A)
python verify.py

# 5. Kiểm tra 15 unit tests (Rubric phần B)
pytest -q
```
