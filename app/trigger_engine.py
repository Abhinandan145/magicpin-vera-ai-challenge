"""
Trigger prioritization, deduplication, suppression filtering, and tick orchestration.
"""

from datetime import datetime
from typing import Any, Dict, List
from app.context_store import context_store
from app.composer import composer
from app.config import settings


class TriggerEngine:
    def process_tick(self, available_trigger_ids: List[str], now_str: str) -> List[Dict[str, Any]]:
        actions: List[Dict[str, Any]] = []
        now_dt = None
        try:
            now_dt = datetime.fromisoformat(now_str.replace("Z", "+00:00"))
        except Exception:
            pass

        messaged_merchants = set()

        for trg_id in available_trigger_ids:
            if len(actions) >= settings.MAX_ACTIONS_PER_TICK:
                break
                
            trigger = context_store.get_trigger(trg_id)
            if not trigger:
                continue

            supp_key = trigger.get("suppression_key")
            if supp_key and context_store.is_suppressed(supp_key):
                continue


            category, merchant, resolved_trigger, customer = context_store.resolve_contexts(trigger)
            if not merchant:
                continue

            merchant_id = merchant.get("merchant_id")
            if merchant_id and context_store.is_merchant_suppressed(merchant_id):
                continue

            if merchant_id in messaged_merchants:
                continue

            action = composer.compose(category, merchant, trigger, customer)
            
            final_supp_key = action.get("suppression_key") or supp_key
            if final_supp_key:
                context_store.suppress(final_supp_key)

            if merchant_id:
                messaged_merchants.add(merchant_id)

            conv_id = action.get("conversation_id", f"conv_{merchant_id}_{trg_id}")
            context_store.record_turn(
                conv_id,
                from_role="bot",
                message=action.get("body", ""),
                cta=action.get("cta"),
                action="send"
            )

            actions.append(action)

        return actions


trigger_engine = TriggerEngine()
