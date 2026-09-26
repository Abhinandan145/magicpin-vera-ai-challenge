"""
Intent Router for classifying inbound merchant/customer messages and guiding response mode.
"""

import re
from enum import Enum
from typing import Any, Dict, List, Tuple
from app.auto_reply import is_auto_reply


class ReplyIntent(str, Enum):
    AUTO_REPLY = "auto_reply"
    HOSTILE_OPTOUT = "hostile_optout"
    EXECUTION_COMMITMENT = "execution_commitment"
    OFF_TOPIC = "off_topic"
    SLOT_SELECTION = "slot_selection"
    REQUEST_INFO = "request_info"
    CONFIRMATION_YES = "confirmation_yes"
    CONFIRMATION_NO = "confirmation_no"
    UNCERTAIN = "uncertain"


HOSTILE_PATTERNS = [
    r"\b(stop\s+messaging|stop\s+sending|stop\s+bothering|don'?t\s+message|don'?t\s+contact|don'?t\s+text|do\s+not\s+text)\b",
    r"\b(not\s+interested|no\s+interest|uninterested)\b",
    r"\b(remove\s+me|unsubscribe|opt\s+out|block|delete\s+my\s+number|delete\s+number)\b",
    r"\b(useless\s+spam|spam\s+message|this\s+is\s+spam|stop\s+this\s+spam|scam|scammer|fraud)\b",
    r"\b(why\s+are\s+you\s+bothering\s+me|leave\s+me\s+alone|harass)\b",
    r"\b(nahi\s+chahiye|band\s+karo|mat\s+bhejo|message\s+mat\s+karo|faltu\s+hai)\b",
    r"^\s*stop\s*$"
]

EXECUTION_PATTERNS = [
    r"\b(let'?s\s+do\s+it|lets\s+do\s+it|let'?s\s+go|lets\s+go)\b",
    r"\b(ok\s+lets\s+do\s+it|ok\s+let'?s\s+do\s+it|okay\s+let'?s\s+do\s+it)\b",
    r"\b(yes\s+please|yes\s+send|please\s+send|send\s+the\s+abstract|draft\s+the\s+patient)\b",
    r"\b(proceed|go\s+ahead|start\s+it|start\s+now|confirm|confirm\s+now)\b",
    r"\b(haan?\s+kar\s+do|ha\s+kar\s+do|kar\s+do|chalega\s+bhejo|bilkul\s+bhejo)\b",
    r"\b(whats\s+next|what'?s\s+next|take\s+it\s+live|publish\s+it)\b",
    r"\b(yes\s+schedule|schedule\s+it|draft\s+it|send\s+it|sign\s+me\s+up)\b",
    r"^\s*(yes|proceed|confirm|go\s+ahead|start|done)\s*$"
]

OFF_TOPIC_PATTERNS = [
    r"\b(gst|file\s+my\s+gst|income\s+tax|tax\s+rate|tax\s+filing|tax\s+audit|itr\s+filing|ca\s+work|accounting|balance\s+sheet)\b",
    r"\b(personal\s+loan|business\s+loan|credit\s+card\s+apply)\b",
    r"\b(crypto|bitcoin|mutual\s+funds|stock\s+market|shares\s+tips)\b",
    r"\b(weather\s+in|cricket\s+tickets|railway\s+booking|train\s+ticket)\b"
]


def classify_intent(message: str, history: List[Dict[str, Any]]) -> Tuple[ReplyIntent, str]:
    msg_clean = message.strip()
    msg_lower = msg_clean.lower()
    
    is_auto, auto_reason = is_auto_reply(msg_clean, history)
    if is_auto:
        return ReplyIntent.AUTO_REPLY, auto_reason
        
    for pat in HOSTILE_PATTERNS:
        if re.search(pat, msg_lower):
            return ReplyIntent.HOSTILE_OPTOUT, f"Matched hostile/opt-out pattern: {pat}"
            
    for pat in OFF_TOPIC_PATTERNS:
        if re.search(pat, msg_lower):
            return ReplyIntent.OFF_TOPIC, f"Matched off-topic pattern: {pat}"
            
    for pat in EXECUTION_PATTERNS:
        if re.search(pat, msg_lower):
            return ReplyIntent.EXECUTION_COMMITMENT, f"Matched execution intent: {pat}"
            
    if re.match(r"^\s*(1|2|3|wed|wednesday|thu|thursday|fri|friday|sat|saturday|sun|sunday|\d{1,2}\s*(am|pm))\b", msg_lower):
        return ReplyIntent.SLOT_SELECTION, "Customer selected slot/option"
        
    if re.search(r"\b(what\s+is|how\s+much|how\s+does\s+it|tell\s+me\s+more|details|cost|pricing|kya\s+hai|batao)\b", msg_lower):
        return ReplyIntent.REQUEST_INFO, "User requested info/clarification"
        
    if re.match(r"^\s*(no|nope|not\s+now|nahi|nah)\b", msg_lower):
        return ReplyIntent.CONFIRMATION_NO, "User declined"
        
    if re.match(r"^\s*(yes|yep|ha|haan|sure|ok|okay)\b", msg_lower):
        return ReplyIntent.CONFIRMATION_YES, "User confirmed"
        
    return ReplyIntent.UNCERTAIN, "General conversational reply"
