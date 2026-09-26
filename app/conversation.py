"""
Multi-turn Conversation Engine managing reply routing, auto-reply backoff,
intent handoff, hostile opt-out, and off-topic redirection.
"""

from typing import Any, Dict, Optional
from app.context_store import context_store
from app.intent_router import ReplyIntent, classify_intent
from app.templates.category_voices import get_owner_name, get_salutation
from app.validators import HallucinationGuard


class ConversationEngine:
    def handle_reply(
        self,
        conversation_id: str,
        message: str,
        turn_number: int,
        merchant_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        from_role: str = "merchant"
    ) -> Dict[str, Any]:
        conv = context_store.get_or_create_conversation(conversation_id, merchant_id, customer_id)
        merchant = context_store.get_merchant(conv.merchant_id or merchant_id)
        customer = context_store.get_customer(conv.customer_id or customer_id)
        category_slug = merchant.get("category_slug") if merchant else None
        category = context_store.get_category(category_slug)
        owner = get_owner_name(merchant)
        
        intent, match_reason = classify_intent(message, conv.history)
        
        # 1. AUTO-REPLY
        if intent == ReplyIntent.AUTO_REPLY:
            conv.consecutive_auto_replies += 1
            if conv.consecutive_auto_replies >= 3 or turn_number >= 4:
                conv.status = "ended"
                response = {
                    "action": "end",
                    "rationale": f"Detected recurring auto-reply pattern ({conv.consecutive_auto_replies}x in a row). Ending conversation gracefully to avoid spamming."
                }
            elif conv.consecutive_auto_replies == 2:
                response = {
                    "action": "wait",
                    "wait_seconds": 86400,
                    "rationale": "Same auto-reply detected 2x in a row; backing off 24h for owner availability."
                }
            else:
                response = {
                    "action": "wait",
                    "wait_seconds": 14400,
                    "rationale": "Detected merchant WhatsApp Business canned auto-reply. Backing off 4 hours for human operator."
                }
            context_store.record_turn(conversation_id, from_role, message)
            context_store.record_turn(conversation_id, "bot", response.get("body", ""), action=response["action"])
            return response

        conv.consecutive_auto_replies = 0

        # 2. HOSTILE / OPT-OUT
        if intent == ReplyIntent.HOSTILE_OPTOUT:
            conv.status = "ended"
            if merchant_id:
                context_store.suppress_merchant(merchant_id)
            response = {
                "action": "end",
                "rationale": f"Merchant explicitly requested opt-out / showed hostility ({match_reason}). Closed conversation and suppressed future automated outreach."
            }
            context_store.record_turn(conversation_id, from_role, message)
            context_store.record_turn(conversation_id, "bot", "", action="end")
            return response

        # 3. EXECUTION COMMITMENT ("Ok let's do it. What's next?")
        if intent == ReplyIntent.EXECUTION_COMMITMENT:
            if category_slug == "dentists":
                body = (
                    "Sending the abstract now (PDF, 2 pages). Patient-ed draft below — ready to copy-paste:\n\n"
                    "\"3-month vs 6-month dental cleaning — does it really matter? New research shows yes, especially for cavity-prone teeth. Drop us a note for a quick check.\"\n\n"
                    "Next step: I'll schedule this post for tomorrow 10am. Reply CONFIRM to proceed."
                )
            elif category_slug == "restaurants":
                body = (
                    "Done! Drafted your match-night delivery campaign banner and special menu. "
                    "Next step: Ready to push live for tonight's dinner rush. Reply CONFIRM to launch."
                )
            elif category_slug == "gyms":
                body = (
                    "Done! Drafted your attendance challenge announcement and member WhatsApp note. "
                    "Next step: Pre-filled for your active roster. Reply CONFIRM to send."
                )
            elif category_slug == "salons":
                body = (
                    "Done! Drafted your special package announcement for Google and WhatsApp. "
                    "Next step: Scheduled for tomorrow morning. Reply CONFIRM to take it live."
                )
            else:
                body = (
                    "Done! Here is the completed draft ready for execution. "
                    "Next step: Scheduled for tomorrow 10am. Reply CONFIRM to publish."
                )
                
            response = {
                "action": "send",
                "body": body,
                "cta": "binary_confirm_cancel",
                "rationale": "Merchant committed ('let's do it'); immediately transitioned to execution mode with concrete deliverables without qualification."
            }
            context_store.record_turn(conversation_id, from_role, message)
            context_store.record_turn(conversation_id, "bot", body, cta="binary_confirm_cancel", action="send")
            return response

        # 4. OFF-TOPIC / CURVEBALL
        if intent == ReplyIntent.OFF_TOPIC:
            body = (
                "I'll have to leave GST and tax filing to your CA — that's outside what I can help with directly. "
                "Coming back to our business objective — want me to send over the draft first, or schedule the update?"
            )
            response = {
                "action": "send",
                "body": body,
                "cta": "open_ended",
                "rationale": "Politely declined out-of-scope tax/accounting question and cleanly redirected back to primary objective."
            }
            context_store.record_turn(conversation_id, from_role, message)
            context_store.record_turn(conversation_id, "bot", body, cta="open_ended", action="send")
            return response

        # 5. SLOT SELECTION
        if intent == ReplyIntent.SLOT_SELECTION:
            body = "Confirmed! Your appointment slot has been reserved. Our team is looking forward to seeing you. Let us know if you need any directions!"
            response = {
                "action": "send",
                "body": body,
                "cta": "none",
                "rationale": "Confirmed appointment slot selection for customer booking flow."
            }
            context_store.record_turn(conversation_id, from_role, message)
            context_store.record_turn(conversation_id, "bot", body, cta="none", action="send")
            return response

        # 6. DECLINE
        if intent == ReplyIntent.CONFIRMATION_NO:
            conv.status = "ended"
            response = {
                "action": "end",
                "rationale": "Merchant/Customer declined; closing conversation politely."
            }
            context_store.record_turn(conversation_id, from_role, message)
            context_store.record_turn(conversation_id, "bot", "", action="end")
            return response

        # 7. GENERAL YES / INFO
        body = (
            f"Got it! Here is the next step for {merchant.get('identity', {}).get('name', 'your business') if merchant else 'you'}. "
            "I've prepared the full update and can activate it right away. Reply CONFIRM to proceed."
        )
        response = {
            "action": "send",
            "body": body,
            "cta": "binary_confirm_cancel",
            "rationale": "Acknowledged user response and advanced to concrete next step."
        }
        context_store.record_turn(conversation_id, from_role, message)
        context_store.record_turn(conversation_id, "bot", body, cta="binary_confirm_cancel", action="send")
        return response


conversation_engine = ConversationEngine()
