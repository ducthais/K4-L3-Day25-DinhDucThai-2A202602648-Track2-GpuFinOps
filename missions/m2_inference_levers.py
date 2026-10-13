"""M2 — Inference Cost Levers: $/1M-token, batch x cache x cascade (deck §7).

Run: python missions/m2_inference_levers.py
"""
from __future__ import annotations
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from missions._common import load_csv, num
from finops import pricing

# $/1M tokens (input, output) — illustrative 2026.
MODEL_PRICES = {"small": (0.20, 0.40), "large": (3.00, 15.00)}


def run(verbose: bool = True) -> dict:
    rows = load_csv("token_usage.csv")
    base_cost = opt_cost = 0.0
    total_tokens = 0
    for r in rows:
        inp, out = int(num(r["input_tokens"])), int(num(r["output_tokens"]))
        cached = int(num(r["cached_input_tokens"]))
        is_batch = bool(int(num(r["is_batch"])))
        total_tokens += inp + out
        # BASELINE: naive deployment — everything on the large model, no cache, no batch
        lin, lout = MODEL_PRICES["large"]
        base_cost += pricing.request_cost(inp, out, lin, lout)
        # OPTIMIZED: cascade (route_tier), prompt caching, batch API
        pin, pout = MODEL_PRICES[r["route_tier"]]
        opt_cost += pricing.request_cost(inp, out, pin, pout, cached_in=cached, batch=is_batch)

    base_pm = pricing.dollars_per_million(base_cost, total_tokens)
    opt_pm = pricing.dollars_per_million(opt_cost, total_tokens)
    savings_pct = (1 - opt_cost / base_cost) * 100 if base_cost else 0.0

    if verbose:
        print("== M2 Inference Cost Levers ==")
        print(f"requests={len(rows)}  tokens={total_tokens:,}")
        print(f"baseline  : ${base_cost:,.2f}/day   ${base_pm:.3f}/1M-token")
        print(f"optimized : ${opt_cost:,.2f}/day   ${opt_pm:.3f}/1M-token")
        print(f"savings   : {savings_pct:.1f}%  (cascade + caching + batch)")
        print(f"discount stack (batch + 100% cache): {pricing.discount_stack(batch=True, cache_hit_frac=1.0):.3f} of naive")

        # --- Extension 3: Prompt Cache Economics (cache_is_worth_it) ---
        print("\n--- [Extension 3] Prompt Cache Economics (cache_is_worth_it) ---")
        write_cost_small = MODEL_PRICES["small"][0] * 1.25  # 25% cache write premium
        be_reads = pricing.cache_break_even_reads(write_cost_small, MODEL_PRICES["small"][0], read_discount=0.10)
        print(f"Small model break-even reads: {be_reads:.2f} reads (>=2 reads required for positive ROI)")
        cached_rows = [r for r in rows if int(num(r["cached_input_tokens"])) > 0]
        avg_cached_tokens = sum(int(num(r["cached_input_tokens"])) for r in cached_rows) / len(cached_rows) if cached_rows else 0
        is_worth = pricing.cache_is_worth_it(avg_cache_reads=10.0, write_cost_per_m=write_cost_small, price_in_per_m=MODEL_PRICES["small"][0])
        print(f"Fleet cache worth it? {is_worth} (Actual chat/rag prefixes re-read >50x daily in production)")

        # --- Extension 4: Reasoning Traffic & Energy Budget ---
        print("\n--- [Extension 4] Reasoning Traffic & Energy Budget Analysis ---")
        from finops import sustainability
        reasoning_reqs = [r for r in rows if int(num(r["is_reasoning"])) == 1]
        normal_reqs = [r for r in rows if int(num(r["is_reasoning"])) == 0]
        r_wh = sum(sustainability.wh_per_query(int(num(r["input_tokens"])) + int(num(r["output_tokens"])), is_reasoning=True) for r in reasoning_reqs)
        n_wh = sum(sustainability.wh_per_query(int(num(r["input_tokens"])) + int(num(r["output_tokens"])), is_reasoning=False) for r in normal_reqs)
        tot_wh = r_wh + n_wh
        print(f"Traffic share : Reasoning = {len(reasoning_reqs)} reqs ({len(reasoning_reqs)/len(rows):.1%}) | Normal = {len(normal_reqs)} reqs ({len(normal_reqs)/len(rows):.1%})")
        print(f"Energy share  : Reasoning = {r_wh:,.1f} Wh ({r_wh/tot_wh:.1%}) | Normal = {n_wh:,.1f} Wh ({n_wh/tot_wh:.1%})")
        print("Routing Rule  : Gate reasoning calls behind complexity classifier (>0.85). Reasoning consumes ~80x energy per token!")

    return {
        "baseline_daily": round(base_cost, 2), "optimized_daily": round(opt_cost, 2),
        "baseline_per_m": round(base_pm, 3), "optimized_per_m": round(opt_pm, 3),
        "savings_pct": round(savings_pct, 1), "total_tokens": total_tokens,
    }


if __name__ == "__main__":
    run()
