"""
Master Engagement Composer integrating deterministic domain intelligence,
category voice modulation, LLM augmentation, and post-generation hallucination guards.
"""

from typing import Any, Dict, Optional
from app.templates.trigger_handlers import compose_trigger_message
from app.validators import HallucinationGuard
from app.llm.client import llm_client
from app.llm.prompts import SYSTEM_COMPOSER_PROMPT, build_evidence_pack


class EngagementComposer:
    def compose(
        self,
        category: Optional[Dict[str, Any]],
        merchant: Optional[Dict[str, Any]],
        trigger: Dict[str, Any],
        customer: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        category_slug = category.get("slug") if category else (merchant.get("category_slug") if merchant else None)
        
        deterministic_action = compose_trigger_message(category, merchant, trigger, customer)
        final_action = deterministic_action
        
        if llm_client.is_available():
            try:
                evidence = build_evidence_pack(category, merchant, trigger, customer)
                prompt = f"Compose outbound WhatsApp message based strictly on this evidence pack:\n{evidence}"
                llm_res = llm_client.complete_json(prompt, SYSTEM_COMPOSER_PROMPT)
                
                if llm_res and isinstance(llm_res, dict) and llm_res.get("body"):
                    candidate_body = llm_res.get("body", "")
                    sanitized_body = HallucinationGuard.validate_and_sanitize(candidate_body, category_slug)
                    
                    has_taboos, _ = HallucinationGuard.check_taboos(sanitized_body, category_slug)
                    if not has_taboos and len(sanitized_body) >= 20:
                        final_action["body"] = sanitized_body
                        if llm_res.get("cta"):
                            final_action["cta"] = llm_res.get("cta")
                        if llm_res.get("rationale"):
                            final_action["rationale"] = llm_res.get("rationale")
                        if llm_res.get("template_name"):
                            final_action["template_name"] = llm_res.get("template_name")
                        if llm_res.get("template_params"):
                            final_action["template_params"] = llm_res.get("template_params")
            except Exception:
                pass

        final_action["body"] = HallucinationGuard.validate_and_sanitize(final_action["body"], category_slug)
        return final_action


composer = EngagementComposer()
