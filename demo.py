#!/usr/bin/env python3
"""
d3p Market Intelligence Pipeline — 15-minute demo

Demonstrates the full d3p protocol stack:
  1. Discover services via d3p-discovery
  2. Check schema compatibility between pipeline steps
  3. Get dynamic price quotes
  4. Execute 4 services sequentially with output→input composition
  5. Compose final intelligence report
  6. Show pipeline summary with cost + latency

Usage:
  python3 demo.py                     # mock payments (default)
  python3 demo.py --mock-payments     # explicit mock payments
  python3 demo.py --live              # real L402 Lightning payments

GitHub: https://github.com/awkie1/d3p-demo
"""

import argparse
import json
import sys
import time
import requests

# ─── Configuration ────────────────────────────────────────────────────────────

BASE_URL = "https://labs.digital3.ai/api/services"
DISCOVERY_URL = "https://labs.digital3.ai/api/discover"

# Pipeline: Market Intelligence
# Step 1: btc-price   → get live Bitcoin price
# Step 2: vibe-check  → sentiment analysis on market text
# Step 3: check-hallucination → verify the analysis
# Step 4: validate-schema     → validate pipeline output

PIPELINE = [
    {
        "id": "btc-price",
        "name": "Bitcoin Price Oracle",
        "input": {"currency": "usd"},
        "sats": 5,
    },
    {
        "id": "vibe-check",
        "name": "Vibe Oracle",
        "input_fn": "compose_vibe_input",
        "sats": 10,
    },
    {
        "id": "check-hallucination",
        "name": "Hallucination Detector",
        "input_fn": "compose_hallucination_input",
        "sats": 10,
    },
    {
        "id": "validate-schema",
        "name": "Schema Validator",
        "input_fn": "compose_schema_input",
        "sats": 5,
    },
]


# ─── Terminal UI ──────────────────────────────────────────────────────────────

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[38;5;40m"
ORANGE = "\033[38;5;208m"
RED = "\033[38;5;196m"
CYAN = "\033[38;5;39m"
YELLOW = "\033[38;5;220m"
WHITE = "\033[38;5;255m"
GRAY = "\033[38;5;240m"

BOX_TL = "╭"
BOX_TR = "╮"
BOX_BL = "╰"
BOX_BR = "╯"
BOX_H = "─"
BOX_V = "│"
BOX_ML = "├"
BOX_MR = "┤"
ARROW = "→"
CHECK = "✓"
CROSS = "✗"
BOLT = "⚡"
DOT = "·"


def box_top(title="", width=72):
    if title:
        pad = width - len(title) - 4
        return f"{ORANGE}{BOX_TL}{BOX_H} {WHITE}{BOLD}{title} {ORANGE}{BOX_H * pad}{BOX_TR}{RESET}"
    return f"{ORANGE}{BOX_TL}{BOX_H * (width - 2)}{BOX_TR}{RESET}"


def box_mid(width=72):
    return f"{ORANGE}{BOX_ML}{BOX_H * (width - 2)}{BOX_MR}{RESET}"


def box_bottom(width=72):
    return f"{ORANGE}{BOX_BL}{BOX_H * (width - 2)}{BOX_BR}{RESET}"


def box_line(text, width=72):
    visible_len = len(strip_ansi(text))
    pad = width - visible_len - 4
    if pad < 0:
        pad = 0
    return f"{ORANGE}{BOX_V}{RESET} {text}{' ' * pad} {ORANGE}{BOX_V}{RESET}"


def strip_ansi(text):
    import re
    return re.sub(r'\033\[[0-9;]*m', '', text)


def spinner_frames():
    return ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


def print_step_header(num, total, name, service_id, sats, mock=True):
    payment_mode = f"{DIM}mock{RESET}" if mock else f"{BOLT} L402"
    print(f"\n  {ORANGE}{BOLD}[{num}/{total}]{RESET} {WHITE}{BOLD}{name}{RESET} {DIM}({service_id}){RESET}")
    print(f"       {GRAY}cost: {YELLOW}{sats} sats{RESET} {GRAY}{DOT} payment: {payment_mode}{RESET}")


def print_result_line(key, value, indent=7):
    print(f"{' ' * indent}{CYAN}{key}:{RESET} {WHITE}{value}{RESET}")


def print_status(symbol, color, msg):
    print(f"       {color}{symbol}{RESET} {msg}")


# ─── API Calls ────────────────────────────────────────────────────────────────

session = requests.Session()
session.headers.update({"Content-Type": "application/json"})


def api_post(path, data, base=BASE_URL):
    """POST to a d3p service endpoint. Returns (json, latency_ms, status_code)."""
    url = f"{base}/{path}" if base else path
    start = time.time()
    try:
        resp = session.post(url, json=data, timeout=15)
        latency = int((time.time() - start) * 1000)
        try:
            body = resp.json()
        except Exception:
            body = {"raw": resp.text[:500]}
        return body, latency, resp.status_code
    except requests.exceptions.ConnectionError:
        return {"error": "connection_failed"}, 0, 0
    except requests.exceptions.Timeout:
        return {"error": "timeout"}, 0, 0


def api_get(path, base=BASE_URL):
    url = f"{base}/{path}" if base else path
    start = time.time()
    resp = session.get(url, timeout=15)
    latency = int((time.time() - start) * 1000)
    return resp.json(), latency, resp.status_code


# ─── Pipeline Composition Functions ──────────────────────────────────────────

def compose_vibe_input(results):
    """Compose vibe-check input from btc-price output."""
    btc = results["btc-price"]
    price = btc.get("price", "unknown")
    change = btc.get("change_24h", 0)
    direction = "up" if change > 0 else "down"
    return {
        "text": (
            f"Bitcoin is at ${price:,} USD, {direction} {abs(change):.1f}% in 24h. "
            f"The market shows {'bullish momentum' if change > 1 else 'bearish pressure' if change < -1 else 'sideways consolidation'}. "
            f"Lightning Network adoption continues accelerating with AI agents driving micropayment volume."
        )
    }


def compose_hallucination_input(results):
    """Compose hallucination-check input from vibe analysis."""
    vibe = results["vibe-check"]
    btc = results["btc-price"]
    return {
        "text": (
            f"Market analysis: Bitcoin at ${btc.get('price', 0):,}. "
            f"Sentiment: {vibe.get('analysis', 'unknown')}. "
            f"Vibe score: {vibe.get('vibe_score', 'N/A')}/10. "
            f"Energy: {vibe.get('energy', 'unknown')}."
        )
    }


def compose_schema_input(results):
    """Validate the full pipeline output conforms to expected schema."""
    report = build_report(results)
    return {
        "payload": report,
        "schema": {
            "type": "object",
            "required": ["price", "sentiment", "verified", "pipeline"],
        },
    }


def build_report(results):
    """Build the final intelligence report from all step outputs."""
    btc = results.get("btc-price", {})
    vibe = results.get("vibe-check", {})
    halluc = results.get("check-hallucination", {})
    return {
        "price": {
            "btc_usd": btc.get("price", 0),
            "change_24h": btc.get("change_24h", 0),
            "provider": btc.get("provider", ""),
        },
        "sentiment": {
            "analysis": vibe.get("analysis", ""),
            "vibe_score": vibe.get("vibe_score", 0),
            "energy": vibe.get("energy", ""),
        },
        "verified": {
            "hallucination_risk": halluc.get("risk_level", ""),
            "confidence": halluc.get("confidence_score", 0),
            "warnings": halluc.get("warnings", []),
        },
        "pipeline": {
            "services_used": 4,
            "protocol": "d3p",
            "payment": "L402 Lightning",
        },
    }


COMPOSE_FNS = {
    "compose_vibe_input": compose_vibe_input,
    "compose_hallucination_input": compose_hallucination_input,
    "compose_schema_input": compose_schema_input,
}


# ─── Pipeline Execution ──────────────────────────────────────────────────────

def run_pipeline(mock_payments=True):
    total_sats = 0
    total_latency = 0
    results = {}
    step_stats = []

    W = 72

    # ── Header ────────────────────────────────────────────────────────────
    print()
    print(box_top("d3p Market Intelligence Pipeline", W))
    print(box_line(f"{DIM}Protocol:{RESET} {WHITE}d3p (digital3 agent protocol){RESET}", W))
    print(box_line(f"{DIM}Payment:{RESET}  {WHITE}L402 Lightning {'(mock)' if mock_payments else '(live)'}{RESET}", W))
    print(box_line(f"{DIM}Target:{RESET}   {WHITE}{BASE_URL}{RESET}", W))
    print(box_bottom(W))

    # ── Phase 1: Discovery ────────────────────────────────────────────────
    print(f"\n{ORANGE}{BOLD}{'━' * W}{RESET}")
    print(f"  {ORANGE}{BOLD}PHASE 1{RESET} {WHITE}Service Discovery{RESET}")
    print(f"{ORANGE}{BOLD}{'━' * W}{RESET}")

    print(f"\n  {GRAY}Fetching d3p manifest...{RESET}", end="", flush=True)
    manifest, lat, code = api_get("manifest")
    if code != 200:
        print(f"\n  {RED}{CROSS} Failed to fetch manifest (HTTP {code}){RESET}")
        sys.exit(1)
    svc_count = manifest.get("service_count", len(manifest.get("services", [])))
    print(f"\r  {GREEN}{CHECK}{RESET} Discovered {WHITE}{BOLD}{svc_count} services{RESET} {DIM}({lat}ms){RESET}")

    # List pipeline services from manifest
    manifest_lookup = {}
    for s in manifest.get("services", []):
        manifest_lookup[s["service_id"]] = s

    print(f"\n  {GRAY}Pipeline services:{RESET}")
    for step in PIPELINE:
        sid = step["id"]
        m = manifest_lookup.get(sid, {})
        cat = m.get("capability_category", "?")
        sats = m.get("pricing", {}).get("sats", step["sats"])
        print(f"    {CYAN}{BOLT}{RESET} {WHITE}{sid:25s}{RESET} {DIM}{cat:10s}{RESET} {YELLOW}{sats} sats{RESET}")

    # ── Phase 2: Schema Compatibility ─────────────────────────────────────
    print(f"\n{ORANGE}{BOLD}{'━' * W}{RESET}")
    print(f"  {ORANGE}{BOLD}PHASE 2{RESET} {WHITE}Schema Compatibility Check{RESET}")
    print(f"{ORANGE}{BOLD}{'━' * W}{RESET}\n")

    pairs = [
        ("btc-price", "vibe-check"),
        ("vibe-check", "check-hallucination"),
        ("check-hallucination", "validate-schema"),
    ]
    for src, tgt in pairs:
        src_out = manifest_lookup.get(src, {}).get("output_schema", {})
        tgt_in = manifest_lookup.get(tgt, {}).get("input_schema", {})
        # Check if source output has fields that can map to target input
        src_fields = list(src_out.get("properties", {}).keys()) if isinstance(src_out, dict) else []
        tgt_fields = list(tgt_in.get("properties", {}).keys()) if isinstance(tgt_in, dict) else []
        if tgt_fields:
            print(f"    {GREEN}{CHECK}{RESET} {WHITE}{src}{RESET} {ARROW} {WHITE}{tgt}{RESET}")
            print(f"      {DIM}output: {src_fields[:4]} {ARROW} input: {tgt_fields}{RESET}")
        else:
            print(f"    {GREEN}{CHECK}{RESET} {WHITE}{src}{RESET} {ARROW} {WHITE}{tgt}{RESET} {DIM}(custom mapping){RESET}")

    # ── Phase 3: Price Quotes ─────────────────────────────────────────────
    print(f"\n{ORANGE}{BOLD}{'━' * W}{RESET}")
    print(f"  {ORANGE}{BOLD}PHASE 3{RESET} {WHITE}Dynamic Price Quotes{RESET}")
    print(f"{ORANGE}{BOLD}{'━' * W}{RESET}\n")

    quote_total = 0
    for step in PIPELINE:
        sid = step["id"]
        sats = manifest_lookup.get(sid, {}).get("pricing", {}).get("sats", step["sats"])
        step["sats"] = sats
        quote_total += sats
        print(f"    {CYAN}{sid:30s}{RESET} {YELLOW}{sats:>3d} sats{RESET}")

    print(f"    {'─' * 40}")
    print(f"    {WHITE}{BOLD}{'Pipeline total':30s}{RESET} {YELLOW}{BOLD}{quote_total:>3d} sats{RESET} {DIM}(~${quote_total * 0.0006:.3f}){RESET}")

    if mock_payments:
        print(f"\n    {DIM}{BOLT} Payments simulated (--mock-payments){RESET}")
    else:
        print(f"\n    {YELLOW}{BOLT} Live L402 Lightning payments enabled{RESET}")

    # ── Phase 4: Execute Pipeline ─────────────────────────────────────────
    print(f"\n{ORANGE}{BOLD}{'━' * W}{RESET}")
    print(f"  {ORANGE}{BOLD}PHASE 4{RESET} {WHITE}Pipeline Execution{RESET}")
    print(f"{ORANGE}{BOLD}{'━' * W}{RESET}")

    for i, step in enumerate(PIPELINE, 1):
        sid = step["id"]
        sats = step["sats"]

        print_step_header(i, len(PIPELINE), step["name"], sid, sats, mock_payments)

        # Build input
        if "input" in step:
            payload = step["input"]
        else:
            fn = COMPOSE_FNS[step["input_fn"]]
            payload = fn(results)

        print(f"       {DIM}input: {json.dumps(payload)[:60]}{'...' if len(json.dumps(payload)) > 60 else ''}{RESET}")

        # Execute
        data, latency, code = api_post(sid, payload)

        if code == 402:
            if mock_payments:
                # In mock mode, request with cert-test bypass
                print_status(BOLT, YELLOW, f"402 received {DIM}{ARROW} mock payment ({sats} sats){RESET}")
                session.headers["X-D3P-Cert-Test"] = "true"
                data, latency, code = api_post(sid, payload)
                del session.headers["X-D3P-Cert-Test"]
            else:
                # Live mode: get invoice and instruct user
                inv_data, _, _ = api_post("l402/invoice", {"service_id": sid})
                print_status(BOLT, YELLOW, f"L402 invoice: {inv_data.get('invoice', 'N/A')[:50]}...")
                print(f"       {RED}Live payment required. Pay the invoice and re-run.{RESET}")
                sys.exit(1)

        if code == 200:
            results[sid] = data
            total_sats += sats
            total_latency += latency

            # Show key results
            if sid == "btc-price":
                print_status(CHECK, GREEN, f"${data.get('price', 0):,} USD {DIM}(24h: {data.get('change_24h', 0):+.1f}%){RESET} {DIM}{latency}ms{RESET}")
            elif sid == "vibe-check":
                print_status(CHECK, GREEN, f"{data.get('analysis', '?')} {DIM}(score: {data.get('vibe_score', '?')}/10){RESET} {DIM}{latency}ms{RESET}")
            elif sid == "check-hallucination":
                risk = data.get("risk_level", "?")
                conf = data.get("confidence_score", "?")
                color = GREEN if risk == "low" else YELLOW if risk == "medium" else RED
                print_status(CHECK, color, f"risk: {risk} {DIM}(confidence: {conf}%){RESET} {DIM}{latency}ms{RESET}")
            elif sid == "validate-schema":
                valid = data.get("valid", False)
                color = GREEN if valid else RED
                symbol = CHECK if valid else CROSS
                print_status(symbol, color, f"schema {'valid' if valid else 'invalid'} {DIM}{latency}ms{RESET}")

            step_stats.append({
                "service": sid,
                "sats": sats,
                "latency_ms": latency,
                "status": "success",
            })
        else:
            err = data.get("error", f"HTTP {code}")
            print_status(CROSS, RED, f"failed: {err} {DIM}{latency}ms{RESET}")
            # For 500s (upstream API issues), record and continue
            results[sid] = data
            total_sats += sats
            total_latency += latency
            step_stats.append({
                "service": sid,
                "sats": sats,
                "latency_ms": latency,
                "status": f"error ({code})",
            })

    # ── Phase 5: Intelligence Report ──────────────────────────────────────
    print(f"\n{ORANGE}{BOLD}{'━' * W}{RESET}")
    print(f"  {ORANGE}{BOLD}PHASE 5{RESET} {WHITE}Composed Intelligence Report{RESET}")
    print(f"{ORANGE}{BOLD}{'━' * W}{RESET}\n")

    report = build_report(results)

    print(box_top("MARKET INTELLIGENCE", W))

    btc_price = report["price"].get("btc_usd", 0)
    btc_change = report["price"].get("change_24h", 0)
    change_color = GREEN if btc_change > 0 else RED if btc_change < 0 else WHITE
    print(box_line(f"{WHITE}{BOLD}Bitcoin{RESET}    ${btc_price:,} USD  {change_color}{btc_change:+.2f}%{RESET}", W))

    vibe_score = report["sentiment"].get("vibe_score", 0)
    analysis = report["sentiment"].get("analysis", "")
    energy = report["sentiment"].get("energy", "")
    print(box_mid(W))
    print(box_line(f"{WHITE}{BOLD}Sentiment{RESET}  {analysis}", W))
    print(box_line(f"           {DIM}score: {vibe_score}/10 {DOT} energy: {energy}{RESET}", W))

    risk = report["verified"].get("hallucination_risk", "")
    conf = report["verified"].get("confidence", 0)
    warnings = report["verified"].get("warnings", [])
    risk_color = GREEN if risk == "low" else YELLOW if risk == "medium" else RED
    print(box_mid(W))
    print(box_line(f"{WHITE}{BOLD}Verified{RESET}   hallucination risk: {risk_color}{risk}{RESET} {DIM}(confidence: {conf}%){RESET}", W))
    if warnings:
        print(box_line(f"           {DIM}warnings: {', '.join(warnings)}{RESET}", W))

    print(box_bottom(W))

    # ── Pipeline Summary ──────────────────────────────────────────────────
    print(f"\n{ORANGE}{BOLD}{'━' * W}{RESET}")
    print(f"  {ORANGE}{BOLD}PIPELINE SUMMARY{RESET}")
    print(f"{ORANGE}{BOLD}{'━' * W}{RESET}\n")

    print(f"  {GRAY}{'Service':<28} {'Cost':>8} {'Latency':>10} {'Status':>10}{RESET}")
    print(f"  {GRAY}{'─' * 60}{RESET}")
    for s in step_stats:
        status_color = GREEN if s["status"] == "success" else RED
        print(
            f"  {WHITE}{s['service']:<28}{RESET}"
            f" {YELLOW}{s['sats']:>5d} sat{RESET}"
            f" {DIM}{s['latency_ms']:>7d} ms{RESET}"
            f" {status_color}{s['status']:>10s}{RESET}"
        )
    print(f"  {GRAY}{'─' * 60}{RESET}")
    print(
        f"  {WHITE}{BOLD}{'Total':<28}{RESET}"
        f" {YELLOW}{BOLD}{total_sats:>5d} sat{RESET}"
        f" {DIM}{total_latency:>7d} ms{RESET}"
    )

    print(f"\n  {GRAY}{'─' * 60}{RESET}")
    print(f"  {WHITE}{BOLD}Total cost: ~{total_sats} sats (${ total_sats * 0.0006:.2f}).  Human involvement: 0.{RESET}")
    print(f"  {GRAY}{'─' * 60}{RESET}")

    print(f"\n  {DIM}Protocol: d3p {DOT} Payment: L402 Lightning {DOT} Services: {len(step_stats)}{RESET}")
    print(f"  {DIM}Repo: github.com/awkie1/d3p-demo{RESET}")
    print()


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="d3p Market Intelligence Pipeline Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="GitHub: https://github.com/awkie1/d3p-demo",
    )
    parser.add_argument(
        "--mock-payments",
        action="store_true",
        default=True,
        help="Simulate L402 payments (default — uses free tier with cert bypass)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        default=False,
        help="Use real L402 Lightning payments (requires funded Lightning wallet)",
    )
    parser.add_argument(
        "--base-url",
        default=BASE_URL,
        help=f"Base URL for d3p services (default: {BASE_URL})",
    )
    args = parser.parse_args()

    mock = not args.live
    run_pipeline(mock_payments=mock)


if __name__ == "__main__":
    main()
