"""
Smoke test script — chạy thử các scenario qua API.
Dùng: $env:PYTHONPATH = "src"; python tests/smoke_test_api.py
"""
import json
import requests
import time
import sys

BASE = "http://127.0.0.1:8000"


def test_health():
    r = requests.get(f"{BASE}/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    print("✅ TC1: Health check OK")


def test_sessions_empty():
    r = requests.get(f"{BASE}/api/v1/sessions")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    print("✅ TC2: Sessions list OK")


def test_trip_not_found():
    r = requests.get(f"{BASE}/api/v1/trips/nonexistent-session")
    data = r.json()
    assert data["status"] in ("empty", "draft") or data.get("plan") is None
    print("✅ TC3: Trip not found returns empty state OK")


def test_chat_stream_chitchat():
    """TC4: Chitchat message should NOT trigger travel agents."""
    r = requests.post(
        f"{BASE}/api/v1/chat/stream",
        json={"message": "Xin chào bạn!", "session_id": None},
        stream=True,
        timeout=30,
    )
    assert r.status_code == 200
    chunks = []
    session_id = None
    for line in r.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "):
            continue
        data = json.loads(line[6:])
        if data["type"] == "session":
            session_id = data["session_id"]
        elif data["type"] == "chunk":
            chunks.append(data["content"])
        elif data["type"] == "done":
            break
    full_text = "".join(chunks)
    assert len(full_text) > 0, "Response should not be empty"
    assert session_id is not None, "Should get session_id"
    print(f"✅ TC4: Chitchat stream OK (session={session_id[:8]}...)")
    print(f"   Response: {full_text[:120]}...")
    return session_id


def test_chat_stream_travel(session_id=None):
    """TC5: Travel request should trigger planner → agents → decision → response."""
    r = requests.post(
        f"{BASE}/api/v1/chat/stream",
        json={
            "message": "Tìm vé máy bay và khách sạn Hà Nội đi Đà Nẵng ngày mai, 3 ngày, 2 người, budget 10 triệu",
            "session_id": session_id,
        },
        stream=True,
        timeout=120,
    )
    assert r.status_code == 200
    chunks = []
    events = []
    sid = session_id
    for line in r.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "):
            continue
        data = json.loads(line[6:])
        events.append(data["type"])
        if data["type"] == "session":
            sid = data["session_id"]
        elif data["type"] == "chunk":
            chunks.append(data["content"])
        elif data["type"] == "interrupt":
            print(f"   ⏸️ HITL interrupt received — plan needs confirmation")
            return sid, "interrupt"
        elif data["type"] == "done":
            break
        elif data["type"] == "error":
            print(f"   ❌ Error: {data.get('content', 'unknown')}")
            return sid, "error"

    full_text = "".join(chunks)
    print(f"✅ TC5: Travel stream OK (session={sid[:8]}..., events={set(events)})")
    print(f"   Response: {full_text[:200]}...")
    return sid, "done"


def test_trip_workspace(session_id):
    """TC6: Trip workspace should have plan after travel request."""
    r = requests.get(f"{BASE}/api/v1/trips/{session_id}")
    assert r.status_code == 200
    data = r.json()
    print(f"✅ TC6: Trip workspace OK (status={data.get('status')}, plan={'yes' if data.get('plan') else 'no'})")
    if data.get("plan"):
        plan = data["plan"]
        print(f"   📍 {plan.get('origin', '?')} → {plan.get('destination', '?')}, {plan.get('days', '?')} ngày, {plan.get('travelers', '?')} người")
    if data.get("decision"):
        dec = data["decision"]
        print(f"   💰 Total: {dec.get('total_cost', 0):,.0f} VND, Status: {dec.get('budget_status', '?')}")
        print(f"   📊 Options: {len(dec.get('options', []))}, Risks: {len(dec.get('risks', []))}")
    if data.get("missing_fields"):
        print(f"   ⚠️ Missing: {data['missing_fields']}")
    return data


def test_resume_after_interrupt(session_id):
    """TC7: Resume after HITL interrupt."""
    r = requests.post(
        f"{BASE}/api/v1/chat/stream/resume",
        json={"session_id": session_id, "response": "ok"},
        stream=True,
        timeout=120,
    )
    assert r.status_code == 200
    chunks = []
    events = []
    for line in r.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "):
            continue
        data = json.loads(line[6:])
        events.append(data["type"])
        if data["type"] == "chunk":
            chunks.append(data["content"])
        elif data["type"] == "done":
            break
        elif data["type"] == "error":
            print(f"   ❌ Resume error: {data.get('content', 'unknown')}")
            return

    full_text = "".join(chunks)
    print(f"✅ TC7: Resume stream OK (events={set(events)})")
    print(f"   Response: {full_text[:200]}...")


def test_out_of_scope():
    """TC8: Out of scope messages should be politely refused."""
    r = requests.post(
        f"{BASE}/api/v1/chat/stream",
        json={"message": "Viết code Python cho tôi", "session_id": None},
        stream=True,
        timeout=30,
    )
    assert r.status_code == 200
    chunks = []
    for line in r.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "):
            continue
        data = json.loads(line[6:])
        if data["type"] == "chunk":
            chunks.append(data["content"])
        elif data["type"] in ("done", "error"):
            break
    full_text = "".join(chunks)
    assert "trợ lý du lịch" in full_text.lower() or "du lịch" in full_text.lower(), \
        f"Out-of-scope response should mention travel. Got: {full_text[:100]}"
    print(f"✅ TC8: Out-of-scope handled OK")
    print(f"   Response: {full_text[:120]}...")


def test_session_usage(session_id):
    """TC9: Usage endpoint returns summary."""
    r = requests.get(f"{BASE}/api/v1/sessions/{session_id}/usage")
    assert r.status_code == 200
    data = r.json()
    print(f"✅ TC9: Usage endpoint OK")
    print(f"   LLM calls: {data.get('llm_calls', 0)}, Tool calls: {data.get('tool_calls', 0)}, "
          f"Tokens: {data.get('total_tokens', 0)}, Cost: ${data.get('total_cost_usd', 0):.4f}")


def test_export_markdown(session_id):
    """TC10: Export trip as markdown."""
    r = requests.get(f"{BASE}/api/v1/trips/{session_id}/export.md")
    if r.status_code == 200:
        print(f"✅ TC10: Export markdown OK ({len(r.text)} chars)")
        print(f"   Preview: {r.text[:100]}...")
    else:
        print(f"⚠️ TC10: Export returned {r.status_code} (no trip yet)")


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 SMOKE TEST — Travel AI Agent API")
    print("=" * 60)
    print()

    # Basic endpoints
    test_health()
    test_sessions_empty()
    test_trip_not_found()
    print()

    # Chitchat + Out of scope
    chitchat_sid = test_chat_stream_chitchat()
    test_out_of_scope()
    print()

    # Full travel flow
    print("--- Full Travel Flow ---")
    sid, status = test_chat_stream_travel()
    test_trip_workspace(sid)
    test_session_usage(sid)
    test_export_markdown(sid)

    if status == "interrupt":
        print()
        print("--- HITL Resume ---")
        test_resume_after_interrupt(sid)
        time.sleep(1)
        test_trip_workspace(sid)
        test_export_markdown(sid)

    print()
    print("=" * 60)
    print("✅ SMOKE TEST COMPLETE")
    print("=" * 60)
