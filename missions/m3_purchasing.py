"""M3 — Purchasing Strategy: break-even, tier choice, spot-checkpoint sim (deck §4).

Run: python missions/m3_purchasing.py
"""
from __future__ import annotations
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from missions._common import load_csv, num, catalog_by_type
from finops import pricing

DAYS = 30


def run(verbose: bool = True) -> dict:
    jobs = load_csv("workloads.csv")
    cat = catalog_by_type()
    on_demand_monthly = optimized_monthly = 0.0
    recs = []
    for j in jobs:
        gtype = j["gpu_type"]
        ngpu = int(num(j["num_gpus"]))
        hpd = num(j["hours_per_day"])
        interruptible = bool(int(num(j["interruptible"])))
        c = cat[gtype]
        gpu_hours = hpd * DAYS * ngpu
        od = num(c["on_demand_hr"])
        on_demand_cost = gpu_hours * od

        tier = pricing.recommend_tier(hpd, interruptible)
        if tier == "spot":
            sim = pricing.spot_checkpoint_cost(gpu_hours, num(c["spot_hr"]), od)
            opt_cost = sim["spot_cost"]
        elif tier == "reserved":
            opt_cost = gpu_hours * num(c["reserved_3yr_hr"])
        else:
            opt_cost = on_demand_cost

        on_demand_monthly += on_demand_cost
        optimized_monthly += opt_cost
        recs.append({"job_id": j["job_id"], "gpu_type": gtype, "tier": tier,
                     "on_demand": round(on_demand_cost), "optimized": round(opt_cost)})

    savings = on_demand_monthly - optimized_monthly
    savings_pct = savings / on_demand_monthly * 100 if on_demand_monthly else 0.0

    if verbose:
        print("== M3 Purchasing Strategy ==")
        print(f"break-even utilization @ 45% reserved discount = {pricing.break_even_utilization(0.45):.0%}")
        print(f"{'job':18}{'gpu':7}{'tier':11}{'on-demand':>12}{'optimized':>12}")
        for r in recs:
            print(f"{r['job_id']:18}{r['gpu_type']:7}{r['tier']:11}${r['on_demand']:>11,}${r['optimized']:>11,}")
        print(f"\nmonthly: on-demand ${on_demand_monthly:,.0f} -> optimized ${optimized_monthly:,.0f}  ({savings_pct:.1f}% saved)")

        # --- Extension 1: Advanced Tier Policy (Duration & Interruption Risk) ---
        print("\n--- [Extension 1] Advanced Tier Policy (Duration & GPU Risk Aware) ---")
        print(f"{'job':18}{'days':>6}{'gpu':>6}{'Base Tier':>11}{'1yr Cost':>12}{'3yr Cost':>12}{'Spot Eff':>12}")
        for j in jobs:
            gtype = j["gpu_type"]
            ngpu = int(num(j["num_gpus"]))
            hpd = num(j["hours_per_day"])
            days = int(num(j["days"]))
            intrp = bool(int(num(j["interruptible"])))
            c = cat[gtype]
            tot_h = hpd * DAYS * ngpu
            c_od = tot_h * num(c["on_demand_hr"])
            c_1yr = tot_h * num(c["reserved_1yr_hr"])
            c_3yr = tot_h * num(c["reserved_3yr_hr"])
            sim = pricing.spot_checkpoint_cost(tot_h, num(c["spot_hr"]), num(c["on_demand_hr"]))
            base_t = pricing.recommend_tier(hpd, intrp)
            print(f"{j['job_id']:18}{days:>6}{gtype:>6}{base_t:>11}${c_1yr:>11,.0f}${c_3yr:>11,.0f}${sim['spot_cost']:>11,.0f}")
        print("  Insight: 1yr commitment requires >=75-80% duty cycle to break even, while 3yr requires >=55%.")

        # --- Extension 5: Carbon-Aware Scheduling for Interruptible Workloads ---
        print("\n--- [Extension 5] Carbon-Aware Scheduling for Interruptible Workloads ---")
        from finops import sustainability
        interruptible_jobs = [j for j in jobs if int(num(j["interruptible"])) == 1]
        total_kwh = sum((int(num(j["num_gpus"])) * num(j["hours_per_day"]) * int(num(j["days"])) * num(cat[j["gpu_type"]]["watts"])) / 1000.0 for j in interruptible_jobs)
        print(f"Total energy for interruptible batch jobs: {total_kwh:,.1f} kWh")
        print(f"{'Region':16}{'gCO2/kWh':>10}{'$/kWh':>8}{'Power Cost':>12}{'Carbon (kg)':>13}{'Carbon Delta':>14}")
        base_carb = (total_kwh * sustainability.REGION_CARBON["us-east-1"]) / 1000.0
        for reg, carb in sustainability.REGION_CARBON.items():
            price = sustainability.REGION_PRICE_KWH[reg]
            cost = total_kwh * price
            c_kg = (total_kwh * carb) / 1000.0
            delta_pct = (c_kg - base_carb) / base_carb * 100
            print(f"{reg:16}{carb:>10}{price:>8.3f}${cost:>11.2f}{c_kg:>12.1f} kg{delta_pct:>+13.1f}%")
        print("  Recommendation: Shift interruptible batch jobs from us-east-1 to europe-north1 (-92.1% CO2e) or us-east-wa (-54.2% power cost).")

    return {"recommendations": recs, "on_demand_monthly": round(on_demand_monthly),
            "optimized_monthly": round(optimized_monthly), "savings_pct": round(savings_pct, 1)}


if __name__ == "__main__":
    run()
