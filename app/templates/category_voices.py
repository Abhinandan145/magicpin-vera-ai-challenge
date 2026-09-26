"""
Category-specific voice profiles, salutations, and tone modulators.
"""

from typing import Any, Dict, Optional


def get_owner_name(merchant: Optional[Dict[str, Any]]) -> str:
    if not merchant:
        return "there"
    
    identity = merchant.get("identity", {})
    owner_first = identity.get("owner_first_name")
    if owner_first:
        return owner_first.strip()
        
    name = identity.get("name", "")
    if name.lower().startswith("dr.") or name.lower().startswith("dr "):
        parts = name.split()
        if len(parts) >= 2:
            doc_name = parts[1].replace("'s", "").rstrip("s")
            return f"Dr. {doc_name}"
        return "Doctor"
        
    words = name.split()
    if words and len(words[0]) > 2:
        return words[0]
        
    return "there"


def get_salutation(merchant: Optional[Dict[str, Any]], category: Optional[Dict[str, Any]], customer: Optional[Dict[str, Any]] = None) -> str:
    if customer:
        cust_name = customer.get("identity", {}).get("name", "").strip()
        lang_pref = customer.get("identity", {}).get("language_pref", "")
        if "senior" in customer.get("identity", {}).get("age_band", "") or "hi" in lang_pref:
            if cust_name:
                return f"Namaste {cust_name}"
            return "Namaste"
        return f"Hi {cust_name}" if cust_name else "Hi there"
        
    category_slug = ""
    if category:
        category_slug = category.get("slug", "")
    elif merchant:
        category_slug = merchant.get("category_slug", "")
        
    owner = get_owner_name(merchant)
    
    if category_slug == "dentists":
        if not owner.startswith("Dr."):
            return f"Dr. {owner}"
        return owner
    elif category_slug == "gyms":
        return f"Hi {owner}"
    elif category_slug in ("salons", "restaurants", "pharmacies"):
        return f"Hi {owner}"
    
    return f"Hi {owner}"


def should_use_hinglish(merchant: Optional[Dict[str, Any]], customer: Optional[Dict[str, Any]] = None) -> bool:
    if customer:
        lang_pref = customer.get("identity", {}).get("language_pref", "").lower()
        if "hi" in lang_pref:
            return True
        return False
        
    if merchant:
        languages = merchant.get("identity", {}).get("languages", [])
        if any("hi" in str(l).lower() for l in languages):
            return True
            
    return False
