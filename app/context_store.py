"""
Stateful Context Store for categories, merchants, customers, triggers,
suppression tracking, and conversation state.
"""

import threading
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field


@dataclass
class ConversationState:
    conversation_id: str
    merchant_id: Optional[str] = None
    customer_id: Optional[str] = None
    trigger_id: Optional[str] = None
    category_slug: Optional[str] = None
    history: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "active"  # "active", "waiting", "ended"
    consecutive_auto_replies: int = 0
    last_action: Optional[str] = None
    last_body: Optional[str] = None
    last_cta: Optional[str] = None
    objective: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class ContextStore:
    def __init__(self):
        self._lock = threading.RLock()
        self.categories: Dict[str, Dict[str, Any]] = {}
        self.merchants: Dict[str, Dict[str, Any]] = {}
        self.customers: Dict[str, Dict[str, Any]] = {}
        self.triggers: Dict[str, Dict[str, Any]] = {}
        self.versions: Dict[Tuple[str, str], int] = {}
        self.suppression_keys: Set[str] = set()
        self.suppressed_merchants: Set[str] = set()
        self.conversations: Dict[str, ConversationState] = {}

    def push_context(self, scope: str, context_id: str, version: int, payload: Dict[str, Any], delivered_at: str) -> Tuple[bool, Optional[str], Optional[int]]:
        with self._lock:
            key = (scope, context_id)
            cur_version = self.versions.get(key)
            
            if cur_version is not None and cur_version > version:
                return False, "stale_version", cur_version
            
            self.versions[key] = version
            
            if scope == "category":
                slug = payload.get("slug", context_id)
                self.categories[slug] = payload
                self.categories[context_id] = payload
            elif scope == "merchant":
                mid = payload.get("merchant_id", context_id)
                self.merchants[mid] = payload
                self.merchants[context_id] = payload
            elif scope == "customer":
                cid = payload.get("customer_id", context_id)
                self.customers[cid] = payload
                self.customers[context_id] = payload
            elif scope == "trigger":
                tid = payload.get("id", context_id)
                self.triggers[tid] = payload
                self.triggers[context_id] = payload
            
            ack_id = f"ack_{context_id}_v{version}"
            return True, ack_id, version

    def get_counts(self) -> Dict[str, int]:
        with self._lock:
            counts = {"category": 0, "merchant": 0, "customer": 0, "trigger": 0}
            for (scope, _), _ in self.versions.items():
                if scope in counts:
                    counts[scope] += 1
            return counts

    def get_category(self, slug_or_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not slug_or_id:
            return None
        with self._lock:
            return self.categories.get(slug_or_id)

    def get_merchant(self, merchant_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not merchant_id:
            return None
        with self._lock:
            return self.merchants.get(merchant_id)

    def get_customer(self, customer_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not customer_id:
            return None
        with self._lock:
            return self.customers.get(customer_id)

    def get_trigger(self, trigger_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not trigger_id:
            return None
        with self._lock:
            return self.triggers.get(trigger_id)

    def resolve_contexts(self, trigger_dict_or_id: Any) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        with self._lock:
            trigger: Optional[Dict[str, Any]] = None
            if isinstance(trigger_dict_or_id, str):
                trigger = self.get_trigger(trigger_dict_or_id)
            elif isinstance(trigger_dict_or_id, dict):
                trigger = trigger_dict_or_id
            
            if not trigger:
                return None, None, None, None
            
            merchant_id = trigger.get("merchant_id") or trigger.get("payload", {}).get("merchant_id")
            customer_id = trigger.get("customer_id") or trigger.get("payload", {}).get("customer_id")
            
            merchant = self.get_merchant(merchant_id) if merchant_id else None
            customer = self.get_customer(customer_id) if customer_id else None
            
            category_slug = None
            if merchant:
                category_slug = merchant.get("category_slug") or merchant.get("identity", {}).get("category")
            if not category_slug and trigger:
                category_slug = trigger.get("category") or trigger.get("payload", {}).get("category")
                if not category_slug:
                    # check kind
                    kind = trigger.get("kind", "")
                    if "dent" in kind or "clinical" in kind or "flouride" in str(trigger):
                        category_slug = "dentists"
                    elif "gym" in kind or "yoga" in kind or "fitness" in str(trigger):
                        category_slug = "gyms"
                    elif "salon" in kind or "hair" in str(trigger) or "beauty" in str(trigger):
                        category_slug = "salons"
                    elif "pharm" in kind or "drug" in str(trigger) or "med" in str(trigger):
                        category_slug = "pharmacies"
                    elif "food" in kind or "rest" in kind or "thali" in str(trigger) or "match" in str(trigger):
                        category_slug = "restaurants"

            category = self.get_category(category_slug) if category_slug else None

            if not merchant:
                if category_slug:
                    for m in self.merchants.values():
                        m_cat = m.get("category_slug") or m.get("identity", {}).get("category")
                        if m_cat == category_slug and not self.is_merchant_suppressed(m.get("merchant_id")):
                            merchant = m
                            break
                if not merchant and self.merchants:
                    merchant = next(iter(self.merchants.values()))

            return category, merchant, trigger, customer


    def is_suppressed(self, suppression_key: Optional[str]) -> bool:
        if not suppression_key:
            return False
        with self._lock:
            return suppression_key in self.suppression_keys

    def suppress(self, suppression_key: Optional[str]) -> None:
        if suppression_key:
            with self._lock:
                self.suppression_keys.add(suppression_key)

    def suppress_merchant(self, merchant_id: Optional[str]) -> None:
        if merchant_id:
            with self._lock:
                self.suppressed_merchants.add(merchant_id)

    def is_merchant_suppressed(self, merchant_id: Optional[str]) -> bool:
        if not merchant_id:
            return False
        with self._lock:
            return merchant_id in self.suppressed_merchants

    def get_or_create_conversation(self, conversation_id: str, merchant_id: Optional[str] = None, customer_id: Optional[str] = None) -> ConversationState:
        with self._lock:
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = ConversationState(
                    conversation_id=conversation_id,
                    merchant_id=merchant_id,
                    customer_id=customer_id
                )
            conv = self.conversations[conversation_id]
            if merchant_id and not conv.merchant_id:
                conv.merchant_id = merchant_id
            if customer_id and not conv.customer_id:
                conv.customer_id = customer_id
            return conv

    def record_turn(self, conversation_id: str, from_role: str, message: str, cta: Optional[str] = None, action: Optional[str] = None) -> ConversationState:
        with self._lock:
            conv = self.get_or_create_conversation(conversation_id)
            conv.history.append({
                "from": from_role,
                "message": message,
                "cta": cta,
                "action": action,
                "ts": datetime.utcnow().isoformat() + "Z"
            })
            if from_role == "bot":
                conv.last_body = message
                conv.last_cta = cta
                conv.last_action = action
            conv.updated_at = datetime.utcnow().isoformat() + "Z"
            return conv

    def clear(self):
        with self._lock:
            self.categories.clear()
            self.merchants.clear()
            self.customers.clear()
            self.triggers.clear()
            self.versions.clear()
            self.suppression_keys.clear()
            self.suppressed_merchants.clear()
            self.conversations.clear()

    def load_from_dir(self, base_dir: Optional[str] = None):
        import os
        import json
        from pathlib import Path

        if not base_dir:
            root = Path(__file__).parent.parent
            if (root / "expanded").exists():
                base_dir = str(root / "expanded")
            else:
                base_dir = str(root / "dataset")

        base_path = Path(base_dir)

        # 1. Categories
        cat_dir = base_path / "categories"
        if cat_dir.exists():
            for f in cat_dir.glob("*.json"):
                try:
                    with open(f, "r", encoding="utf-8") as fp:
                        data = json.load(fp)
                        slug = data.get("slug", f.stem)
                        self.push_context("category", slug, 1, data, datetime.utcnow().isoformat() + "Z")
                except Exception:
                    pass

        # 2. Merchants
        merch_dir = base_path / "merchants"
        if merch_dir.exists():
            for f in merch_dir.glob("*.json"):
                try:
                    with open(f, "r", encoding="utf-8") as fp:
                        data = json.load(fp)
                        mid = data.get("merchant_id", f.stem)
                        self.push_context("merchant", mid, 1, data, datetime.utcnow().isoformat() + "Z")
                except Exception:
                    pass
        elif (base_path / "merchants_seed.json").exists():
            with open(base_path / "merchants_seed.json", "r", encoding="utf-8") as fp:
                for m in json.load(fp):
                    mid = m.get("merchant_id")
                    if mid:
                        self.push_context("merchant", mid, 1, m, datetime.utcnow().isoformat() + "Z")

        # 3. Customers
        cust_dir = base_path / "customers"
        if cust_dir.exists():
            for f in cust_dir.glob("*.json"):
                try:
                    with open(f, "r", encoding="utf-8") as fp:
                        data = json.load(fp)
                        cid = data.get("customer_id", f.stem)
                        self.push_context("customer", cid, 1, data, datetime.utcnow().isoformat() + "Z")
                except Exception:
                    pass
        elif (base_path / "customers_seed.json").exists():
            with open(base_path / "customers_seed.json", "r", encoding="utf-8") as fp:
                for c in json.load(fp):
                    cid = c.get("customer_id")
                    if cid:
                        self.push_context("customer", cid, 1, c, datetime.utcnow().isoformat() + "Z")

        # 4. Triggers
        trg_dir = base_path / "triggers"
        if trg_dir.exists():
            for f in trg_dir.glob("*.json"):
                try:
                    with open(f, "r", encoding="utf-8") as fp:
                        data = json.load(fp)
                        tid = data.get("id", f.stem)
                        self.push_context("trigger", tid, 1, data, datetime.utcnow().isoformat() + "Z")
                except Exception:
                    pass
        elif (base_path / "triggers_seed.json").exists():
            with open(base_path / "triggers_seed.json", "r", encoding="utf-8") as fp:
                for t in json.load(fp):
                    tid = t.get("id")
                    if tid:
                        self.push_context("trigger", tid, 1, t, datetime.utcnow().isoformat() + "Z")


context_store = ContextStore()
store = context_store

