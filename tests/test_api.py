"""
Unit and Integration tests for Vera FastAPI endpoints and core handlers.
"""

import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.context_store import context_store

client = TestClient(app)


class TestVeraAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        context_store.load_from_dir()

    def test_healthz(self):
        response = client.get("/v1/healthz")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("uptime_seconds", data)
        self.assertIn("contexts_loaded", data)

    def test_metadata(self):
        response = client.get("/v1/metadata")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("team_name", data)
        self.assertIn("version", data)
        self.assertIn("approach", data)

    def test_context_push_and_conflict(self):
        # 1. Successful push
        payload = {
            "scope": "merchant",
            "context_id": "m_test_spec_01",
            "version": 2,
            "payload": {
                "merchant_id": "m_test_spec_01",
                "category_slug": "restaurants",
                "identity": {
                    "name": "Hyderabadi Spice",
                    "owner_first_name": "Faizan",
                    "locality": "Koramangala",
                    "city": "Bangalore"
                }
            },
            "delivered_at": "2026-09-26T18:00:00Z"
        }
        resp = client.post("/v1/context", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["accepted"])
        self.assertIsNotNone(data["ack_id"])

        # 2. Conflict test with older version
        conflict_payload = {
            "scope": "merchant",
            "context_id": "m_test_spec_01",
            "version": 1,
            "payload": {},
            "delivered_at": "2026-09-26T18:01:00Z"
        }
        resp = client.post("/v1/context", json=conflict_payload)
        self.assertEqual(resp.status_code, 409)
        c_data = resp.json()
        self.assertFalse(c_data["accepted"])
        self.assertEqual(c_data["reason"], "stale_version")
        self.assertEqual(c_data["current_version"], 2)

    def test_tick_evaluation(self):
        payload = {
            "now": "2026-09-26T18:00:00Z",
            "available_triggers": ["trg_013_corporate_thali_planning", "trg_001_ipl_season_rush"]
        }
        resp = client.post("/v1/tick", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("actions", data)
        self.assertIsInstance(data["actions"], list)

    def test_reply_auto_reply_backoff(self):
        # Turn 1 auto-reply
        p1 = {
            "conversation_id": "conv_test_ar_01",
            "merchant_id": "m_001",
            "message": "Thank you for contacting us. We will get back to you shortly.",
            "received_at": "2026-09-26T18:00:00Z",
            "turn_number": 1
        }
        r1 = client.post("/v1/reply", json=p1).json()
        self.assertEqual(r1["action"], "wait")
        self.assertEqual(r1["wait_seconds"], 14400)

        # Turn 2 consecutive auto-reply
        p2 = {
            "conversation_id": "conv_test_ar_01",
            "merchant_id": "m_001",
            "message": "Thanks for reaching out! We are currently away.",
            "received_at": "2026-09-26T18:05:00Z",
            "turn_number": 2
        }
        r2 = client.post("/v1/reply", json=p2).json()
        self.assertEqual(r2["action"], "wait")
        self.assertEqual(r2["wait_seconds"], 86400)

        # Turn 3 consecutive auto-reply -> end
        p3 = {
            "conversation_id": "conv_test_ar_01",
            "merchant_id": "m_001",
            "message": "Auto reply: Our office hours are 9am to 6pm.",
            "received_at": "2026-09-26T18:10:00Z",
            "turn_number": 3
        }
        r3 = client.post("/v1/reply", json=p3).json()
        self.assertEqual(r3["action"], "end")

    def test_reply_commitment_action_mode(self):
        p = {
            "conversation_id": "conv_test_commit_01",
            "merchant_id": "m_001",
            "message": "Ok lets do it. Whats next?",
            "received_at": "2026-09-26T18:00:00Z",
            "turn_number": 2
        }
        r = client.post("/v1/reply", json=p).json()
        self.assertEqual(r["action"], "send")
        body_lower = (r.get("body") or "").lower()
        self.assertTrue(any(w in body_lower for w in ["done", "sending", "live", "draft", "set", "scheduled", "confirm", "ready"]))
        self.assertNotIn("would you like", body_lower)
        self.assertNotIn("do you want", body_lower)

    def test_reply_hostile_opt_out(self):
        p = {
            "conversation_id": "conv_test_hostile_01",
            "merchant_id": "m_test_hostile_mid",
            "message": "Stop spamming me! Unsubscribe immediately!",
            "received_at": "2026-09-26T18:00:00Z",
            "turn_number": 1
        }
        r = client.post("/v1/reply", json=p).json()
        self.assertEqual(r["action"], "end")
        self.assertTrue(context_store.is_merchant_suppressed("m_test_hostile_mid"))

    def test_reply_offtopic_gst_redirection(self):
        p = {
            "conversation_id": "conv_test_gst_01",
            "merchant_id": "m_001",
            "message": "What is the new GST rate on luxury hair styling products?",
            "received_at": "2026-09-26T18:00:00Z",
            "turn_number": 1
        }
        r = client.post("/v1/reply", json=p).json()
        self.assertEqual(r["action"], "send")
        body = (r.get("body") or "").lower()
        self.assertTrue("gst" in body or "tax" in body or "magicpin" in body or "growth" in body)


if __name__ == "__main__":
    unittest.main()
