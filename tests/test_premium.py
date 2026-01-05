from fastapi.testclient import TestClient
from main import app
from services.user_progress import get_progress

client = TestClient(app)


def test_free_premium_granted_on_new_user():
    uid = "test_user_1"
    progress = get_progress(uid)
    assert progress.is_premium is True
    assert progress.premium_until is not None


def test_watch_ad_for_premium_returns_message():
    user_id = 5555
    progress = get_progress(user_id)
    # Ensure user is premium
    assert progress.is_premium is True
    resp = client.post(f"/reward/ad?user_id={user_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("message") == "Premium user"


def test_buy_premium_simple_endpoint():
    user_id = 7777
    resp = client.post(f"/premium/buy?user_id={user_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("is_premium") is True or data.get("is_premium") == "True"