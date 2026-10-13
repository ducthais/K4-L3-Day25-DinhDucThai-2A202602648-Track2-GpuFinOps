"""M1 — Efficiency Audit: MFU/MBU, the GPU-Util lie, and idle waste (deck §5).

Run: python missions/m1_efficiency_audit.py
"""
from __future__ import annotations
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from collections import defaultdict
from missions._common import load_csv, num, catalog_by_type
from finops import metrics


def run(verbose: bool = True) -> dict:
    tel = load_csv("gpu_telemetry.csv")
    cat = catalog_by_type()

    # per-row MFU/MBU, then aggregate per GPU
    agg = defaultdict(lambda: {"util": [], "mfu": [], "mbu": [], "type": None, "idle_hours": 0})
    for r in tel:
        gtype = r["gpu_type"]
        peak_fp16 = num(cat[gtype]["peak_tflops_fp16"])
        peak_bw = num(cat[gtype]["peak_bw_tbs"])
        mfu = metrics.compute_mfu(num(r["achieved_tflops"]), peak_fp16)
        mbu = metrics.compute_mbu(num(r["achieved_bw_tbs"]), peak_bw)
        a = agg[r["gpu_id"]]
        a["type"] = gtype
        a["util"].append(num(r["gpu_util_pct"]))
        a["mfu"].append(mfu)
        a["mbu"].append(mbu)
        if num(r["gpu_util_pct"]) < 10:  # effectively idle this interval (1h)
            a["idle_hours"] += 1

    summary = []
    for gid, a in agg.items():
        summary.append({
            "gpu_id": gid, "gpu_type": a["type"],
            "gpu_util_pct": round(sum(a["util"]) / len(a["util"]), 1),
            "mfu": round(sum(a["mfu"]) / len(a["mfu"]), 3),
            "mbu": round(sum(a["mbu"]) / len(a["mbu"]), 3),
            "idle_hours": a["idle_hours"],
        })

    lies = metrics.flag_util_lies(summary)
    idle_waste = 0.0
    for s in summary:
        on_demand = num(catalog_by_type()[s["gpu_type"]]["on_demand_hr"])
        idle_waste += metrics.idle_waste_usd(s["idle_hours"], on_demand)

    if verbose:
        print("== M1 Efficiency Audit ==")
        print(f"{'GPU':14}{'type':7}{'util%':>7}{'MFU':>7}{'MBU':>7}{'idle_h':>8}")
        for s in sorted(summary, key=lambda x: x["mfu"]):
            print(f"{s['gpu_id']:14}{s['gpu_type']:7}{s['gpu_util_pct']:>7}{s['mfu']:>7}{s['mbu']:>7}{s['idle_hours']:>8}")
        print(f"\nGPU-Util LIES (util>=90% but MFU<30%): {[l['gpu_id'] for l in lies]}")
        print(f"Idle waste (1 day): ${idle_waste:,.2f}  ->  ${idle_waste*30:,.0f}/month")

        # --- Extension 2: Right-sizing memory-bound GPUs by MBU & $/GB-VRAM ---
        print("\n--- [Extension 2] Right-sizing Analysis (MBU & $/GB-VRAM) ---")
        print(f"{'GPU Type':10}{'On-Demand':>11}{'VRAM(GB)':>10}{'$/GB-VRAM':>12}{'BW(TB/s)':>11}{'$/(TB/s)':>12}")
        for gtype, c in cat.items():
            od = num(c["on_demand_hr"])
            hbm = num(c["hbm_gb"])
            bw = num(c["peak_bw_tbs"])
            vram_cost = od / hbm if hbm else 0
            bw_cost = od / bw if bw else 0
            print(f"{gtype:10}${od:>10.2f}{hbm:>10.0f}${vram_cost:>11.4f}{bw:>11.2f}${bw_cost:>11.3f}")

        print("\nRight-sizing Recommendations for Memory-Bound / Low-MFU GPUs:")
        rightsize_monthly_total = 0.0
        for lie in lies:
            cur_type = lie["gpu_type"]
            rec = metrics.recommend_rightsize_gpu(
                achieved_tflops=num(lie.get("achieved_tflops", num(cat[cur_type]["peak_tflops_fp16"]) * lie["mfu"])),
                achieved_bw_tbs=num(lie.get("achieved_bw_tbs", num(cat[cur_type]["peak_bw_tbs"]) * lie["mbu"])),
                mem_used_gb=num(lie.get("mem_used_gb", 30)),
                catalog=cat
            )
            target_type = rec["gpu_type"] if rec else ("A100" if cur_type == "H100" else "L4")
            cur_cost = num(cat[cur_type]["on_demand_hr"])
            new_cost = num(cat[target_type]["on_demand_hr"])
            delta_hr = max(0.0, cur_cost - new_cost)
            save_mo = delta_hr * 24 * 30
            rightsize_monthly_total += save_mo
            pct = (delta_hr / cur_cost * 100) if cur_cost else 0
            print(f"  * {lie['gpu_id']} ({cur_type}): Downsize -> {target_type} (${cur_cost:.2f}/h -> ${new_cost:.2f}/h) | Save: ${delta_hr:.2f}/h (-{pct:.1f}%) = ${save_mo:,.0f}/month")
        print(f"  => Total Monthly Right-sizing Savings: ${rightsize_monthly_total:,.0f}/month")
        print("  Insight: Never choose GPU solely by lowest $/GPU-hr! A GPU with insufficient VRAM or BW causes OOM or severe latency degradation.")

    return {"summary": summary, "lies": lies, "idle_waste_daily": round(idle_waste, 2)}


if __name__ == "__main__":
    run()
