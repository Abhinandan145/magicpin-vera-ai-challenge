"""
Auto-reply detection engine to eliminate WhatsApp Business canned response loops.
"""

import re
from typing import Any, Dict, List, Tuple


AUTO_REPLY_PATTERNS = [
    r"thank\s+you\s+for\s+(contacting|messaging|reaching\s+out|your\s+message)",
    r"thanks\s+for\s+(contacting|messaging|reaching\s+out|your\s+message)",
    r"our\s+team\s+will\s+(respond|reply|get\s+back)\s+shortly",
    r"will\s+get\s+back\s+to\s+you\s+(as\s+soon\s+as\s+possible|shortly|soon)",
    r"we\s+are\s+currently\s+(away|unavailable|closed)",
    r"our\s+business\s+hours\s+are",
    r"our\s+office\s+hours\s+are",
    r"our\s+working\s+hours\s+are",
    r"office\s+hours\s+are",
    r"this\s+is\s+an\s+automated\s+(response|message|reply)",
    r"i\s+am\s+an\s+automated\s+assistant",
    r"automated\s+(greeting|reply|response)",
    r"^auto\s*reply\b",
    r"\bauto\s*reply\b",
    r"welcome\s+to\s+.*how\s+can\s+we\s+help\s+you",
    r"please\s+leave\s+your\s+(details|query|contact)",
    
    r"aapki\s+jaankari\s+ke\s+liye\s+(bahut\s+)?shukriya",
    r"aapki\s+madad\s+ke\s+liye\s+shukriya",
    r"sampark\s+karne\s+ke\s+liye\s+dhanyawad",
    r"sampark\s+karne\s+ke\s+liye\s+shukriya",
    r"hamari\s+team\s+(aapko|tak)\s+pahuncha",
    r"hamari\s+team\s+jaldi\s+hi\s+sampark\s+karegi",
    r"main\s+ek\s+automated\s+assistant\s+hoon",
    r"hum\s+jaldi\s+hi\s+aapse\s+sampark\s+karenge",
    r"dhanyawad\s+hum\s+aapki\s+madad",
    r"shukriya.*team.*respond"
]

COMPILED_AUTO_PATTERNS = [re.compile(p, re.IGNORECASE) for p in AUTO_REPLY_PATTERNS]


def is_auto_reply(message: str, history: List[Dict[str, Any]]) -> Tuple[bool, str]:
    msg_clean = message.strip()
    msg_lower = msg_clean.lower()
    
    for pat in COMPILED_AUTO_PATTERNS:
        if pat.search(msg_lower):
            return True, f"Matched auto-reply pattern: '{pat.pattern}'"
            
    merchant_past_msgs = [
        h.get("message", "").strip().lower() 
        for h in history 
        if h.get("from") == "merchant"
    ]
    
    if merchant_past_msgs:
        repeat_count = sum(1 for m in merchant_past_msgs if m == msg_lower)
        if repeat_count >= 1:
            return True, f"Identical merchant message sent {repeat_count + 1} times in conversation"
            
    return False, ""
