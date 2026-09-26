"""
Replay and benchmark test suite using standard unittest.
"""

import unittest
from app.context_store import context_store
from app.composer import composer
from app.validators import HallucinationGuard


class TestVeraReplays(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        context_store.load_from_dir()

    def test_fnb_ipl_trigger_composition(self):
        merchant = next((m for m in context_store.merchants.values() if m.get("category_slug") == "restaurants"), None)
        trigger = next((t for t in context_store.triggers.values() if "ipl" in t.get("id", "").lower() or t.get("kind") == "seasonal_event"), None)
        
        if merchant and trigger:
            category = context_store.get_category("restaurants")
            action = composer.compose(category, merchant, trigger)
            body = action.get("body", "")
            self.assertGreater(len(body), 20)
            self.assertNotIn("http", body)
            self.assertNotIn("www.", body)

            has_taboos, taboos = HallucinationGuard.check_taboos(body, "restaurants")
            self.assertFalse(has_taboos, f"Found taboo words: {taboos}")

    def test_salon_customer_delegation_composition(self):
        salon_m = next((m for m in context_store.merchants.values() if m.get("category_slug") == "salons"), None)
        cust_t = next((t for t in context_store.triggers.values() if t.get("kind") == "customer_winback" or t.get("customer_id")), None)
        cust = next(iter(context_store.customers.values()), None)

        if salon_m and cust_t:
            cat = context_store.get_category("salons")
            action = composer.compose(cat, salon_m, cust_t, cust)
            body = action.get("body", "")
            self.assertGreater(len(body), 20)
            self.assertNotIn("http", body)
            has_taboos, taboos = HallucinationGuard.check_taboos(body, "salons")
            self.assertFalse(has_taboos, f"Found taboo words: {taboos}")

    def test_zero_taboo_words_across_all_triggers(self):
        for trigger_id, trigger in list(context_store.triggers.items())[:15]:
            category, merchant, _, customer = context_store.resolve_contexts(trigger)
            if not merchant:
                merchant = next(iter(context_store.merchants.values()), None)
            if not category and merchant:
                category = context_store.get_category(merchant.get("category_slug"))
            if not category or not merchant:
                continue
            
            action = composer.compose(category, merchant, trigger, customer)
            body = action.get("body", "")
            has_taboos, taboos = HallucinationGuard.check_taboos(body, category.get("slug"))
            self.assertFalse(has_taboos, f"Found taboo words {taboos} in trigger {trigger_id}: {body}")


if __name__ == "__main__":
    unittest.main()
