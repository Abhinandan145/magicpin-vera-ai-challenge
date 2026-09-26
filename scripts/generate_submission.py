#!/usr/bin/env python3
"""
Generate canonical submission.jsonl from expanded test pairs.
Loads context store, evaluates all 30 canonical pairs via Vera composer, validates compliance,
and writes out formatted JSON Lines matching challenge evaluation requirements.
"""

import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.context_store import context_store
from app.composer import composer
from app.validators import HallucinationGuard


def main():
    root_dir = Path(__file__).parent.parent
    test_pairs_path = root_dir / "expanded" / "test_pairs.json"
    if not test_pairs_path.exists():
        test_pairs_path = root_dir / "dataset" / "test_pairs.json"

    if not test_pairs_path.exists():
        print(f"Error: test_pairs.json not found at {test_pairs_path}")
        sys.exit(1)

    with open(test_pairs_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        test_pairs = data.get("pairs", data) if isinstance(data, dict) else data

    # Initialize store from expanded directory
    context_store.load_from_dir(str(root_dir / "expanded"))

    output_path = root_dir / "submission.jsonl"
    results = []

    print(f"Generating submission messages for {len(test_pairs)} test pairs...")

    for pair in test_pairs:
        pair_id = pair.get("test_id") or pair.get("id") or pair.get("pair_id")
        merchant_id = pair.get("merchant_id")
        trigger_id = pair.get("trigger_id")
        customer_id = pair.get("customer_id")

        merchant = context_store.get_merchant(merchant_id)
        trigger = context_store.get_trigger(trigger_id)
        customer = context_store.get_customer(customer_id) if customer_id else None
        
        category_slug = merchant.get("category_slug") if merchant else None
        category = context_store.get_category(category_slug) if category_slug else None

        if not merchant or not trigger:
            print(f"Warning: Missing data for pair {pair_id} (m={merchant_id}, t={trigger_id})")
            continue

        action = composer.compose(
            category=category,
            merchant=merchant,
            trigger=trigger,
            customer=customer
        )

        body = action.get("body", "")
        has_taboos, taboos = HallucinationGuard.check_taboos(body, category_slug)
        has_urls = "http://" in body or "https://" in body or "www." in body

        record = {
            "test_id": pair_id,
            "merchant_id": merchant_id,
            "trigger_id": trigger_id,
            "customer_id": customer_id,
            "category": category_slug,
            "send_as": action.get("send_as", "vera"),
            "template_name": action.get("template_name", ""),
            "template_params": action.get("template_params", []),
            "body": body,
            "cta": action.get("cta", "open_ended"),
            "suppression_key": action.get("suppression_key", ""),
            "rationale": action.get("rationale", ""),
            "valid": not has_taboos and not has_urls,
            "length_chars": len(body),
            "word_count": len(body.split())
        }
        results.append(record)

    with open(output_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    print(f"Successfully generated {len(results)} submission entries in {output_path}")
    avg_words = sum(r["word_count"] for r in results) / len(results) if results else 0
    avg_chars = sum(r["length_chars"] for r in results) / len(results) if results else 0
    all_valid = all(r["valid"] for r in results)

    print(f"Summary Statistics:")
    print(f"  Total Pairs: {len(results)}")
    print(f"  Avg Word Count: {avg_words:.1f} words")
    print(f"  Avg Char Count: {avg_chars:.1f} chars")
    print(f"  Compliance Rate: {'100%' if all_valid else 'Issues detected'}")


if __name__ == "__main__":
    main()
