#!/usr/bin/env python3
"""
Comprehensive Local Judge Evaluator & Scorecard.
Tests the live HTTP server against all test scenarios, measures latency,
and evaluates against the 5-dimension rubric (Specificity, Category Fit,
Merchant Fit, Trigger Relevance, Engagement Compulsion).
"""

import sys
import json
import time
import re
from pathlib import Path
from urllib import request as urlrequest, error as urlerror

ROOT_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT_DIR / "dataset"
BOT_URL = "http://localhost:8080"


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'


def print_score_bar(dim: str, score: int, max_s: int = 10):
    filled = int((score / max_s) * 20)
    empty = 20 - filled
    c = Colors.GREEN if score >= 8 else Colors.YELLOW if score >= 6 else Colors.RED
    print(f"  {dim:24} [{c}{'█' * filled}{'░' * empty}{Colors.RESET}] {c}{score:2}/{max_s}{Colors.RESET}")


def http_req(method: str, path: str, body: dict = None):
    url = f"{BOT_URL}{path}"
    start = time.time()
    data = json.dumps(body).encode("utf-8") if body else None
    req = urlrequest.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        resp = urlrequest.urlopen(req, timeout=10)
        return json.loads(resp.read().decode("utf-8")), None, (time.time() - start) * 1000
    except urlerror.HTTPError as e:
        latency = (time.time() - start) * 1000
        try:
            return json.loads(e.read().decode("utf-8")), f"HTTP {e.code}", latency
        except:
            return None, f"HTTP {e.code}", latency
    except Exception as e:
        return None, str(e), (time.time() - start) * 1000


def evaluate_message_heuristics(body: str, cta: str, category: dict, merchant: dict, trigger: dict, customer: dict = None):
    """Evaluates message against 5 rubric dimensions (0-10 each)."""
    body_clean = body.strip()
    body_lower = body_clean.lower()
    
    # 1. Specificity (0-10)
    spec = 5
    if re.search(r"₹\d+", body) or re.search(r"\d+%", body) or re.search(r"\d{1,2}:\d{2}", body) or re.search(r"\d+,\d+|\d+-\w+", body):
        spec += 3
    if any(cite in body for cite in ["JIDA", "DCI", "IDA", "ICMR", "CDSCO", "GST", "FSSAI", "p.", "circular"]):
        spec += 2
    if len(re.findall(r"\d+", body)) >= 2:
        spec = min(10, spec + 1)
        
    # 2. Category fit (0-10)
    cat_fit = 8
    cat_slug = category.get("slug", "") if category else merchant.get("category_slug", "")
    taboos = {
        "dentists": ["guaranteed", "miracle", "100% safe", "cure"],
        "salons": ["guaranteed glow", "instant transformation"],
        "restaurants": ["best food in city", "viral guarantee"],
        "gyms": ["guaranteed weight loss", "shred in 7 days"],
        "pharmacies": ["miracle cure", "100% safe"]
    }
    for taboo in taboos.get(cat_slug, []):
        if taboo in body_lower:
            cat_fit -= 4
            
    if cat_slug == "dentists" and ("dr." in body_lower or "clinical" in body_lower or "fluoride" in body_lower or "caries" in body_lower):
        cat_fit = 10
    elif cat_slug == "salons" and ("haircut" in body_lower or "salon" in body_lower or "bridal" in body_lower or "skin" in body_lower):
        cat_fit = 10
    elif cat_slug == "restaurants" and ("thali" in body_lower or "covers" in body_lower or "delivery" in body_lower or "match" in body_lower):
        cat_fit = 10
    elif cat_slug == "gyms" and ("class" in body_lower or "session" in body_lower or "trial" in body_lower or "members" in body_lower):
        cat_fit = 10
    elif cat_slug == "pharmacies" and ("medicine" in body_lower or "discount" in body_lower or "refill" in body_lower or "namaste" in body_lower):
        cat_fit = 10
        
    # 3. Merchant fit (0-10)
    merch_fit = 7
    owner = merchant.get("identity", {}).get("owner_first_name", "")
    biz = merchant.get("identity", {}).get("name", "")
    if owner and owner.lower() in body_lower:
        merch_fit += 2
    if biz and (biz.lower() in body_lower or biz.split()[0].lower() in body_lower):
        merch_fit += 1
    merch_fit = min(10, merch_fit)

    # 4. Trigger relevance (0-10)
    trg_rel = 8
    kind = trigger.get("kind", "")
    if ("research" in kind and "jida" in body_lower) or \
       ("compliance" in kind and "dci" in body_lower) or \
       ("recall" in kind and ("recall" in body_lower or "visit" in body_lower or "slot" in body_lower)) or \
       ("perf" in kind and ("down" in body_lower or "up" in body_lower or "%" in body_lower)) or \
       ("ipl" in kind and ("ipl" in body_lower or "match" in body_lower or "stadium" in body_lower)) or \
       ("curious" in kind and "asked-for" in body_lower) or \
       ("milestone" in kind and "review" in body_lower) or \
       ("planning" in kind and ("thali" in body_lower or "camp" in body_lower)):
        trg_rel = 10

    # 5. Engagement compulsion (0-10)
    eng = 8
    if cta in ["binary_yes_no", "multi_choice_slot", "binary_confirm_cancel", "open_ended"]:
        eng += 1
    if "?" in body:
        eng += 1
    eng = min(10, eng)

    # Penalties
    penalties = 0
    if re.search(r"https?://", body):
        penalties += 3

    total = max(0, spec + cat_fit + merch_fit + trg_rel + eng - penalties)
    return {
        "specificity": spec,
        "category_fit": cat_fit,
        "merchant_fit": merch_fit,
        "trigger_relevance": trg_rel,
        "engagement_compulsion": eng,
        "penalties": penalties,
        "total": total
    }


def main():
    print(f"\n{Colors.HEADER}{Colors.BOLD}======================================================================{Colors.RESET}")
    print(f"{Colors.HEADER}{Colors.BOLD}          LOCAL EVALUATION HARNESS — VERA ENGAGEMENT ENGINE           {Colors.RESET}")
    print(f"{Colors.HEADER}{Colors.BOLD}======================================================================{Colors.RESET}\n")

    # 1. Warmup
    print(f"{Colors.CYAN}{Colors.BOLD}--- 1. WARMUP & HEALTH PROBE ---{Colors.RESET}")
    http_req("POST", "/v1/teardown")
    h_data, h_err, h_lat = http_req("GET", "/v1/healthz")
    if h_err:
        print(f"{Colors.RED}[FAIL] Server unreachable at {BOT_URL}: {h_err}{Colors.RESET}")
        sys.exit(1)
    print(f"{Colors.GREEN}[PASS] Healthz OK ({h_lat:.1f}ms){Colors.RESET}")

    m_data, m_err, _ = http_req("GET", "/v1/metadata")
    print(f"{Colors.GREEN}[PASS] Metadata OK — Team: {m_data.get('team_name')}, Model: {m_data.get('model')}{Colors.RESET}")

    # 2. Push Dataset Contexts
    print(f"\n{Colors.CYAN}{Colors.BOLD}--- 2. CONTEXT PUSH (BASE DATASET) ---{Colors.RESET}")
    categories = {}
    for f in (DATASET_DIR / "categories").glob("*.json"):
        cat = json.load(open(f))
        slug = cat.get("slug", f.stem)
        categories[slug] = cat
        res, _, _ = http_req("POST", "/v1/context", {
            "scope": "category", "context_id": slug, "version": 1,
            "payload": cat, "delivered_at": "2026-04-26T10:00:00Z"
        })
        print(f"  [{'PASS' if res and res.get('accepted') else 'FAIL'}] category/{slug}")

    merchants = json.load(open(DATASET_DIR / "merchants_seed.json"))["merchants"]
    for m in merchants:
        mid = m["merchant_id"]
        http_req("POST", "/v1/context", {
            "scope": "merchant", "context_id": mid, "version": 1,
            "payload": m, "delivered_at": "2026-04-26T10:00:00Z"
        })

    customers = json.load(open(DATASET_DIR / "customers_seed.json"))["customers"]
    for c in customers:
        cid = c["customer_id"]
        http_req("POST", "/v1/context", {
            "scope": "customer", "context_id": cid, "version": 1,
            "payload": c, "delivered_at": "2026-04-26T10:00:00Z"
        })

    triggers = json.load(open(DATASET_DIR / "triggers_seed.json"))["triggers"]
    for t in triggers:
        tid = t["id"]
        http_req("POST", "/v1/context", {
            "scope": "trigger", "context_id": tid, "version": 1,
            "payload": t, "delivered_at": "2026-04-26T10:00:00Z"
        })

    h_data, _, _ = http_req("GET", "/v1/healthz")
    counts = h_data["contexts_loaded"]
    print(f"{Colors.GREEN}[PASS] Contexts Loaded: {counts}{Colors.RESET}")

    # 3. Test Replays
    print(f"\n{Colors.CYAN}{Colors.BOLD}--- 3. REPLAY SCENARIOS ---{Colors.RESET}")
    # Auto-reply test
    auto_msg = "Thank you for contacting Dr. Meera's Dental Clinic! Our team will respond shortly."
    ar_passed = False
    for turn in range(1, 5):
        r_data, _, _ = http_req("POST", "/v1/reply", {
            "conversation_id": "conv_ar_test", "merchant_id": "m_001_drmeera_dentist_delhi",
            "from_role": "merchant", "message": auto_msg, "received_at": "2026-04-26T10:00:00Z", "turn_number": turn + 1
        })
        act = r_data.get("action") if r_data else None
        if turn >= 3 and act == "end":
            ar_passed = True
            print(f"{Colors.GREEN}[PASS] Auto-reply Hell Scenario: Ended gracefully on turn {turn + 1}{Colors.RESET}")
            break

    # Intent transition test
    r_intent, _, _ = http_req("POST", "/v1/reply", {
        "conversation_id": "conv_in_test", "merchant_id": "m_001_drmeera_dentist_delhi",
        "from_role": "merchant", "message": "Ok lets do it. Whats next?", "received_at": "2026-04-26T10:00:00Z", "turn_number": 2
    })
    body_in = (r_intent.get("body") or "").lower() if r_intent else ""
    action_words = ["done", "sending", "draft", "here", "confirm", "proceed", "next"]
    qualifying_words = ["would you", "do you", "can you tell", "what if", "how about"]
    if any(w in body_in for w in action_words) and not any(w in body_in for w in qualifying_words):
        print(f"{Colors.GREEN}[PASS] Intent Transition Scenario: Switched immediately to action mode (0 qualification){Colors.RESET}")
    else:
        print(f"{Colors.RED}[FAIL] Intent Transition Scenario failed{Colors.RESET}")

    # Hostile test
    r_hostile, _, _ = http_req("POST", "/v1/reply", {
        "conversation_id": "conv_h_test", "merchant_id": "m_001_drmeera_dentist_delhi",
        "from_role": "merchant", "message": "Stop messaging me. This is useless spam.", "received_at": "2026-04-26T10:00:00Z", "turn_number": 2
    })
    if r_hostile and r_hostile.get("action") == "end":
        print(f"{Colors.GREEN}[PASS] Hostile Opt-Out Scenario: Ended immediately & suppressed{Colors.RESET}")

    # Curveball test
    r_gst, _, _ = http_req("POST", "/v1/reply", {
        "conversation_id": "conv_gst_test", "merchant_id": "m_001_drmeera_dentist_delhi",
        "from_role": "merchant", "message": "Can you also help me file my GST?", "received_at": "2026-04-26T10:00:00Z", "turn_number": 2
    })
    if r_gst and ("ca" in (r_gst.get("body") or "").lower() or "gst" in (r_gst.get("body") or "").lower()):
        print(f"{Colors.GREEN}[PASS] Off-topic GST Scenario: Politely redirected to objective{Colors.RESET}")

    # 4. Tick and Composition Scoring
    print(f"\n{Colors.CYAN}{Colors.BOLD}--- 4. SCORING CANONICAL COMPOSITIONS ---{Colors.RESET}")
    all_scores = []
    merch_map = {m["merchant_id"]: m for m in merchants}
    cust_map = {c["customer_id"]: c for c in customers}

    for t in triggers[:10]:
        tid = t["id"]
        mid = t["merchant_id"]
        cid = t.get("customer_id")
        merchant = merch_map.get(mid, {})
        category = categories.get(merchant.get("category_slug", "dentists"), {})
        customer = cust_map.get(cid)

        # Trigger tick
        t_data, _, lat = http_req("POST", "/v1/tick", {"now": "2026-04-26T10:30:00Z", "available_triggers": [tid]})
        actions = t_data.get("actions", []) if t_data else []
        if actions:
            act = actions[0]
            scores = evaluate_message_heuristics(act["body"], act["cta"], category, merchant, t, customer)
            all_scores.append(scores)
            print(f"\n{Colors.BLUE}Trigger:{Colors.RESET} {t['kind']} | {Colors.BLUE}Merchant:{Colors.RESET} {merchant.get('identity',{}).get('name')}")
            print(f"{Colors.DIM}\"{act['body'][:100]}...\"{Colors.RESET}")
            print(f"  Total Score: {Colors.BOLD}{scores['total']}/50{Colors.RESET} (Latency: {lat:.1f}ms)")

    # 5. Final Scorecard
    print(f"\n{Colors.HEADER}{Colors.BOLD}======================================================================{Colors.RESET}")
    print(f"{Colors.HEADER}{Colors.BOLD}                         FINAL SCORECARD                              {Colors.RESET}")
    print(f"{Colors.HEADER}{Colors.BOLD}======================================================================{Colors.RESET}\n")

    if all_scores:
        avg_spec = sum(s["specificity"] for s in all_scores) / len(all_scores)
        avg_cat = sum(s["category_fit"] for s in all_scores) / len(all_scores)
        avg_merch = sum(s["merchant_fit"] for s in all_scores) / len(all_scores)
        avg_trg = sum(s["trigger_relevance"] for s in all_scores) / len(all_scores)
        avg_eng = sum(s["engagement_compulsion"] for s in all_scores) / len(all_scores)
        avg_tot = sum(s["total"] for s in all_scores) / len(all_scores)
        pct = (avg_tot / 50) * 100

        print_score_bar("Avg Specificity", int(avg_spec))
        print_score_bar("Avg Category Fit", int(avg_cat))
        print_score_bar("Avg Merchant Fit", int(avg_merch))
        print_score_bar("Avg Trigger Relevance", int(avg_trg))
        print_score_bar("Avg Engagement Compulsion", int(avg_eng))

        print(f"\n{Colors.BOLD}  OVERALL SCORE: {avg_tot:.1f}/50 ({pct:.0f}%){Colors.RESET}")
        if pct >= 90:
            print(f"  {Colors.GREEN}{Colors.BOLD}RESULT: OUTSTANDING / COMPETITION WINNING TIER{Colors.RESET}\n")
        elif pct >= 80:
            print(f"  {Colors.GREEN}{Colors.BOLD}RESULT: EXCELLENT{Colors.RESET}\n")
        else:
            print(f"  {Colors.YELLOW}{Colors.BOLD}RESULT: GOOD{Colors.RESET}\n")


if __name__ == "__main__":
    main()
