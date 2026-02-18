#!/usr/bin/env python3
"""
d3p Code Analysis Pipeline — search → CODE_ANALYZE → validate-schema

Demonstrates a developer-tools pipeline where code analysis is missing.
Step 1 (search) and Step 3 (validate-schema) work.
Step 2 (code-analyze) does not exist on d3p yet.

Usage:
    python3 code_pipeline.py
    python3 code_pipeline.py --query "Python asyncio connection pool best practices"
"""

import argparse
import json
import sys
import time
import requests

# ─── Configuration ────────────────────────────────────────────────────────────

BASE_URL = "https://labs.digital3.ai/api/services"
DISCOVERY_URL = "https://labs.digital3.ai/api/discover"

# ─── Terminal UI (matching demo.py) ───────────────────────────────────────────

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
MAGENTA = "\033[38;5;198m"

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
BLOCK = "█"

import re
def strip_ansi(text):
    return re.sub(r'\033\[[0-9;]*m', '', text)

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

def print_step_header(num, total, name, service_id, sats, status="live"):
    status_str = f"{GREEN}live{RESET}" if status == "live" else f"{RED}missing{RESET}"
    print(f"\n  {ORANGE}{BOLD}[{num}/{total}]{RESET} {WHITE}{BOLD}{name}{RESET} {DIM}({service_id}){RESET}")
    print(f"       {GRAY}cost: {YELLOW}{sats} sats{RESET} {GRAY}{DOT} status: {status_str}{RESET}")

def print_status(symbol, color, msg):
    print(f"       {color}{symbol}{RESET} {msg}")

def print_result_line(key, value, indent=7):
    print(f"{' ' * indent}{CYAN}{key}:{RESET} {WHITE}{value}{RESET}")


# ─── API Calls ────────────────────────────────────────────────────────────────

session = requests.Session()
session.headers.update({
    "Content-Type": "application/json",
    "X-D3P-Cert-Test": "true",
})

def api_post(path, data, base=BASE_URL):
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


# ─── Pipeline ─────────────────────────────────────────────────────────────────

def run_pipeline(query="Python asyncio connection pool best practices"):
    W = 72
    total_sats = 0
    total_latency = 0
    step_stats = []

    # ── Header ────────────────────────────────────────────────────────────
    print()
    print(box_top("d3p Code Analysis Pipeline", W))
    print(box_line(f"{DIM}Pipeline:{RESET} {WHITE}search {ARROW} code-analyze {ARROW} validate-schema{RESET}", W))
    print(box_line(f"{DIM}Goal:{RESET}     {WHITE}Find code patterns, analyze quality, validate{RESET}", W))
    print(box_line(f"{DIM}Query:{RESET}    {WHITE}{query[:52]}{RESET}", W))
    print(box_bottom(W))

    # ── Phase 1: Discovery ────────────────────────────────────────────────
    print(f"\n{ORANGE}{BOLD}{'━' * W}{RESET}")
    print(f"  {ORANGE}{BOLD}PHASE 1{RESET} {WHITE}Service Discovery{RESET}")
    print(f"{ORANGE}{BOLD}{'━' * W}{RESET}")

    print(f"\n  {GRAY}Querying d3p discovery for pipeline services...{RESET}")

    manifest, lat, code = api_get("manifest")
    if code != 200:
        print(f"\n  {RED}{CROSS} Cannot reach d3p manifest (HTTP {code}){RESET}")
        sys.exit(1)

    available = {s["service_id"] for s in manifest.get("services", [])}

    pipeline_steps = [
        {"id": "ext-search-v2",   "name": "AI Web Search",      "capability": "search",        "sats": 10, "route": "search"},
        {"id": "code-analyze",    "name": "Code Analyzer",      "capability": "code_analysis", "sats": 25, "route": "code-analyze"},
        {"id": "validate-schema", "name": "Schema Validator",   "capability": "validation",    "sats": 5,  "route": "validate-schema"},
    ]

    print(f"\n  {GRAY}Pipeline requirements:{RESET}\n")
    for step in pipeline_steps:
        exists = step["id"] in available
        if exists:
            print(f"    {GREEN}{CHECK}{RESET} {WHITE}{step['name']:25s}{RESET} {DIM}({step['id']}){RESET} {GREEN}available{RESET}")
        else:
            print(f"    {RED}{CROSS}{RESET} {WHITE}{step['name']:25s}{RESET} {DIM}({step['id']}){RESET} {RED}not found{RESET}")

    # Discovery query for code analysis
    print(f"\n  {GRAY}Searching d3p network for code_analysis capability...{RESET}")
    disco, dlat, dcode = api_post("query", {"capability": "code_analysis"}, base=DISCOVERY_URL)
    results_count = disco.get("result_count", 0) if dcode == 200 else 0
    if results_count > 0:
        print(f"  {GREEN}{CHECK}{RESET} Found {results_count} code analysis services")
    else:
        print(f"  {RED}{CROSS}{RESET} No services with capability: code_analysis {DIM}({dlat}ms){RESET}")

    # ── Phase 2: Execute ──────────────────────────────────────────────────
    print(f"\n{ORANGE}{BOLD}{'━' * W}{RESET}")
    print(f"  {ORANGE}{BOLD}PHASE 2{RESET} {WHITE}Pipeline Execution{RESET}")
    print(f"{ORANGE}{BOLD}{'━' * W}{RESET}")

    outputs = {}

    # Step 1: Search (EXISTS)
    print_step_header(1, 3, "AI Web Search", "search", 10, "live")
    payload = {"query": query}
    print(f"       {DIM}input: {json.dumps(payload)[:60]}{RESET}")

    data, latency, code = api_post("search", payload)
    if code == 200:
        outputs["search"] = data
        total_sats += 10
        total_latency += latency
        answer = data.get("answer", data.get("result", ""))[:80]
        print_status(CHECK, GREEN, f"{DIM}{latency}ms{RESET}")
        print_result_line("answer", f"{answer}...")
        source = data.get("source", "")
        if source:
            print_result_line("source", source[:60])
        step_stats.append({"service": "search", "sats": 10, "latency_ms": latency, "status": "success"})
    else:
        print_status(CROSS, RED, f"failed (HTTP {code}) {DIM}{latency}ms{RESET}")
        step_stats.append({"service": "search", "sats": 10, "latency_ms": latency, "status": f"error ({code})"})

    # Step 2: Code Analyze (MISSING)
    print_step_header(2, 3, "Code Analyzer", "code-analyze", 25, "missing")

    # Show what the input WOULD look like
    search_text = outputs.get("search", {}).get("answer", "")[:200]
    would_be_input = {
        "code": "# extracted from search results...",
        "language": "python",
        "checks": ["security", "performance", "style"],
    }

    print(f"       {DIM}would send: {json.dumps(would_be_input)[:55]}...{RESET}")
    print()
    print(f"       {RED}{BLOCK * 50}{RESET}")
    print(f"       {RED}{BOLD}PIPELINE BLOCKED{RESET}")
    print(f"       {WHITE}No service for capability: {YELLOW}code_analysis{RESET}")
    print(f"       {RED}{BLOCK * 50}{RESET}")
    print()
    print(f"       {GRAY}The d3p network has no code analysis service.{RESET}")
    print(f"       {GRAY}This pipeline needs:{RESET}")
    print(f"       {GRAY}  input:  {CYAN}{{\"code\": \"...\", \"language\": \"python\",{RESET}")
    print(f"       {GRAY}           {CYAN}\"checks\": [\"security\", \"performance\"]}}{RESET}")
    print(f"       {GRAY}  output: {CYAN}{{\"issues\": [...], \"score\": 85,{RESET}")
    print(f"       {GRAY}           {CYAN}\"suggestions\": [...], \"complexity\": N}}{RESET}")
    print()
    print(f"       {GRAY}Potential integrations:{RESET}")
    print(f"       {GRAY}  {DOT} Static analysis  (AST-based, 15-25 sats){RESET}")
    print(f"       {GRAY}  {DOT} LLM code review  (GPT/Claude, 25-50 sats){RESET}")
    print(f"       {GRAY}  {DOT} Security scanner  (SAST/DAST, 20-40 sats){RESET}")
    print()
    print(f"       {ORANGE}{BOLD}{BOLT} Register yours at digital3.ai/docs{RESET}")
    print(f"       {DIM}pip install d3p-sdk && d3p register my-code-analyzer{RESET}")

    step_stats.append({"service": "code-analyze", "sats": 0, "latency_ms": 0, "status": "MISSING"})

    # Step 3: Validate Schema (EXISTS — validate a sample code analysis report)
    print_step_header(3, 3, "Schema Validator", "validate-schema", 5, "live")

    # Build a mock payload that WOULD come from code-analyze, to show the validator works
    mock_analysis = {
        "issues": [
            {"severity": "warning", "line": 32, "message": "Connection not returned to pool"},
            {"severity": "info", "line": 45, "message": "Consider using async context manager"},
        ],
        "score": 72,
        "language": "python",
        "pipeline_note": "mock data — code-analyze service not available",
    }

    payload = {
        "payload": mock_analysis,
        "schema": {
            "type": "object",
            "required": ["issues", "score", "language"],
            "properties": {
                "issues": {"type": "array"},
                "score": {"type": "number", "minimum": 0, "maximum": 100},
                "language": {"type": "string"},
            },
        },
    }
    print(f"       {DIM}input: validating mock analysis report structure{RESET}")
    print(f"       {YELLOW}note: using mock data (step 2 was blocked){RESET}")

    data, latency, code = api_post("validate-schema", payload)
    if code == 200:
        outputs["validate-schema"] = data
        total_sats += 5
        total_latency += latency
        valid = data.get("valid", False)
        color = GREEN if valid else RED
        symbol = CHECK if valid else CROSS
        print_status(symbol, color, f"schema {'valid' if valid else 'invalid'} {DIM}{latency}ms{RESET}")
        if data.get("details"):
            print_result_line("details", str(data["details"])[:60])
        step_stats.append({"service": "validate-schema", "sats": 5, "latency_ms": latency, "status": "success"})
    else:
        print_status(CROSS, RED, f"failed (HTTP {code}) {DIM}{latency}ms{RESET}")
        step_stats.append({"service": "validate-schema", "sats": 5, "latency_ms": latency, "status": f"error ({code})"})

    # ── Pipeline Summary ──────────────────────────────────────────────────
    print(f"\n{ORANGE}{BOLD}{'━' * W}{RESET}")
    print(f"  {ORANGE}{BOLD}PIPELINE SUMMARY{RESET}")
    print(f"{ORANGE}{BOLD}{'━' * W}{RESET}\n")

    print(f"  {GRAY}{'Service':<28} {'Cost':>8} {'Latency':>10} {'Status':>10}{RESET}")
    print(f"  {GRAY}{'─' * 60}{RESET}")
    for s in step_stats:
        if s["status"] == "MISSING":
            color = MAGENTA
        elif s["status"] == "success":
            color = GREEN
        else:
            color = RED
        print(
            f"  {WHITE}{s['service']:<28}{RESET}"
            f" {YELLOW}{s['sats']:>5d} sat{RESET}"
            f" {DIM}{s['latency_ms']:>7d} ms{RESET}"
            f" {color}{s['status']:>10s}{RESET}"
        )
    print(f"  {GRAY}{'─' * 60}{RESET}")
    print(
        f"  {WHITE}{BOLD}{'Total (completed steps)':<28}{RESET}"
        f" {YELLOW}{BOLD}{total_sats:>5d} sat{RESET}"
        f" {DIM}{total_latency:>7d} ms{RESET}"
    )

    # ── Gap Analysis ──────────────────────────────────────────────────────
    print(f"\n{ORANGE}{BOLD}{'━' * W}{RESET}")
    print(f"  {ORANGE}{BOLD}GAP ANALYSIS{RESET}")
    print(f"{ORANGE}{BOLD}{'━' * W}{RESET}\n")

    print(box_top("MISSING CAPABILITY: code_analysis", W))
    print(box_line(f"{WHITE}Pipeline:{RESET} search {GREEN}{CHECK}{RESET} {ARROW} code-analyze {RED}{CROSS}{RESET} {ARROW} validate {GREEN}{CHECK}{RESET}", W))
    print(box_mid(W))
    print(box_line(f"{WHITE}What's needed:{RESET}", W))
    print(box_line(f"  {CYAN}Service ID:{RESET}   code-analyze", W))
    print(box_line(f"  {CYAN}Category:{RESET}     code_analysis", W))
    print(box_line(f"  {CYAN}Input:{RESET}        {{code, language, checks[]}}", W))
    print(box_line(f"  {CYAN}Output:{RESET}       {{issues[], score, suggestions[], complexity}}", W))
    print(box_line(f"  {CYAN}Est. price:{RESET}   15-50 sats per analysis", W))
    print(box_mid(W))
    print(box_line(f"{WHITE}Developer pipeline market:{RESET} Every AI coding agent", W))
    print(box_line(f"{WHITE}needs code review. This is a high-volume gap.{RESET}", W))
    print(box_mid(W))
    print(box_line(f"{ORANGE}{BOLD}{BOLT} Register: digital3.ai/docs{RESET}", W))
    print(box_bottom(W))
    print()


def main():
    parser = argparse.ArgumentParser(description="d3p Code Analysis Pipeline Demo")
    parser.add_argument("--query", default="Python asyncio connection pool best practices",
                        help="Code topic to search for")
    args = parser.parse_args()
    run_pipeline(query=args.query)


if __name__ == "__main__":
    main()
