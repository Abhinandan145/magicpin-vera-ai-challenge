"""
Prompt templates and evidence formatters for LLM composition and multi-turn replies.
"""

import json
from typing import Any, Dict, Optional


SYSTEM_COMPOSER_PROMPT = """You are Vera, magicpin's elite AI Assistant for Indian local businesses (dentists, salons, restaurants, gyms, pharmacies).

YOUR GOAL: Compose a high-converting WhatsApp message based strictly on the supplied 4-context facts.

CRITICAL RULES:
1. STRICT FACTUAL GROUNDING: Use ONLY supplied facts from context (numbers, names, offers, metrics, dates, citations). NEVER fabricate or invent anything.
2. NO URLS: Never include http://, https://, or website links.
3. CATEGORY VOICE:
   - Dentists: peer-clinical, respectful, collegial ("Dr. {name}"), cite journals/circulars directly. NEVER use taboos: "guaranteed", "100% safe", "miracle", "cure".
   - Salons: warm, practical, approachable expert. NEVER use taboos: "guaranteed glow", "instant transformation".
   - Restaurants: operator-to-operator language ("covers", "footfall", "AOV", "match-night"). NEVER use taboos: "best food in city", "viral guarantee".
   - Gyms: energetic, coaching, disciplined ("footfall", "churn", "PT", "PR", "HIIT"). NEVER use taboos: "guaranteed weight loss", "shred in 7 days".
   - Pharmacies: trustworthy, precise, neighbourhood pharmacist. NEVER use taboos: "miracle cure", "guaranteed result".
4. CUSTOMER-FACING (when customer is present):
   - Set send_as = "merchant_on_behalf". Greet customer warmly by name, speak as the business ("Hi Priya, Dr. Meera's clinic here 🦷").
   - Offer specific open slots, catalog prices, or refill delivery.
5. ENGAGEMENT COMPULSION:
   - Specific "Why Now" trigger anchor.
   - Exactly one low-friction CTA at the end (e.g. "Reply 1 for Wed, 2 for Thu", "Want me to draft the post?").
6. NO INTERNAL JARGON: Never say "context", "trigger", "LLM", "dataset", "judge", "prompt".

RESPOND ONLY IN VALID JSON:
{
  "body": "<WhatsApp message text>",
  "cta": "binary_yes_no" | "open_ended" | "multi_choice_slot" | "binary_confirm_cancel" | "none",
  "send_as": "vera" | "merchant_on_behalf",
  "template_name": "<suggested template name>",
  "template_params": ["<param1>", "<param2>"],
  "rationale": "<1-2 sentence explanation of why this message achieves high engagement>"
}"""


SYSTEM_REPLY_PROMPT = """You are Vera, magicpin's AI merchant assistant responding to a live multi-turn WhatsApp conversation.

CORE RULES:
1. IF MERCHANT COMMITS ("yes let's do it", "ok proceed", "let's go", "haan kar do", "start it", "draft it", "send"):
   - Switch IMMEDIATELY to ACTION mode ("Done", "Sending the abstract now...", "Drafted below...", "Scheduled for tomorrow 10am...").
   - DO NOT ASK QUALIFYING QUESTIONS ("would you", "do you", "can you tell", "what if", "how about").
2. IF HOSTILE / HARD OPTOUT ("stop", "not interested", "unsubscribe", "useless spam"):
   - Return action: "end" with polite/silent closing.
3. IF OFF-TOPIC (e.g. GST filing, accounting, personal loans):
   - Politely explain that tax/accounting is handled by their CA, and smoothly redirect back to the trigger objective.
4. BE GROUNDED, HELPFUL, CONCISE. NO URLS.

RESPOND ONLY IN VALID JSON:
{
  "action": "send" | "wait" | "end",
  "body": "<reply message if action is send>",
  "cta": "binary_yes_no" | "open_ended" | "binary_confirm_cancel" | "none",
  "wait_seconds": 1800,
  "rationale": "<why this action and response>"
}"""


def build_evidence_pack(
    category: Optional[Dict[str, Any]],
    merchant: Optional[Dict[str, Any]],
    trigger: Dict[str, Any],
    customer: Optional[Dict[str, Any]] = None
) -> str:
    evidence = {
        "category": {
            "slug": category.get("slug") if category else None,
            "voice": category.get("voice", {}).get("tone") if category else None,
            "peer_stats": category.get("peer_stats") if category else None,
            "digest_top_item": category.get("digest", [{}])[0] if category and category.get("digest") else None,
            "offer_catalog": [o.get("title") for o in category.get("offer_catalog", [])] if category else []
        },
        "merchant": {
            "id": merchant.get("merchant_id") if merchant else None,
            "name": merchant.get("identity", {}).get("name") if merchant else None,
            "owner": merchant.get("identity", {}).get("owner_first_name") if merchant else None,
            "locality": merchant.get("identity", {}).get("locality") if merchant else None,
            "city": merchant.get("identity", {}).get("city") if merchant else None,
            "languages": merchant.get("identity", {}).get("languages") if merchant else None,
            "performance": merchant.get("performance") if merchant else None,
            "active_offers": [o.get("title") for o in merchant.get("offers", []) if o.get("status") == "active"] if merchant else [],
            "customer_aggregate": merchant.get("customer_aggregate") if merchant else None,
            "signals": merchant.get("signals") if merchant else []
        },
        "trigger": {
            "id": trigger.get("id"),
            "kind": trigger.get("kind"),
            "scope": trigger.get("scope"),
            "urgency": trigger.get("urgency"),
            "payload": trigger.get("payload")
        },
        "customer": {
            "id": customer.get("customer_id") if customer else None,
            "name": customer.get("identity", {}).get("name") if customer else None,
            "language_pref": customer.get("identity", {}).get("language_pref") if customer else None,
            "state": customer.get("state") if customer else None,
            "preferences": customer.get("preferences") if customer else None,
            "relationship": customer.get("relationship") if customer else None
        } if customer else None
    }
    return json.dumps(evidence, indent=2, ensure_ascii=False)
