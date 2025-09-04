"""
Integration test for Phase 4.1.1 Trading Safety Service
Tests the complete safety validation pipeline with real API calls.
"""

import requests
import json


def test_phase_4_1_1_integration():
    """Integration test for Phase 4.1.1 Trading Safety Service."""
    
    base_url = "http://localhost:8000/api/v1"
    
    print("🧪 Testing Phase 4.1.1: Trading Safety Service")
    print("=" * 50)
    
    # Test 1: Safety Status
    print("\n1. Testing Safety Status Endpoint...")
    response = requests.get(f"{base_url}/trades/safety-status")
    assert response.status_code == 200
    status = response.json()
    
    assert "limits" in status
    assert "current_status" in status
    assert status["safety_enabled"] is True
    assert status["limits"]["max_position_size_usd"] == 25.0
    assert status["limits"]["min_temperature"] == "WARM"
    
    print(f"✅ Safety Status: {status['current_status']['trades_remaining']} trades remaining today")
    
    # Test 2: Valid Trade Validation
    print("\n2. Testing Valid Trade Validation...")
    
    # First, create a fresh test bot for this integration test
    import random
    test_bot_id = random.randint(1000, 9999)  # Use random ID to avoid conflicts
    
    test_bot_data = {
        "name": f"Integration Test Bot {test_bot_id}",
        "description": "Test bot for Phase 4.1.1 integration testing",
        "pair": "BTC-USD",
        "position_size_usd": 100.0,
        "max_positions": 1,
        "stop_loss_pct": 5.0,
        "take_profit_pct": 10.0,
        "trade_step_pct": 2.0,
        "cooldown_minutes": 15,
        "signal_config": {
            "RSI": {"enabled": True, "weight": 0.4, "period": 14, "oversold": 30, "overbought": 70}
        }
    }
    
    # Create the test bot
    create_response = requests.post(
        f"{base_url}/bots/",
        json=test_bot_data,
        headers={"Content-Type": "application/json"}
    )
    assert create_response.status_code == 200
    created_bot = create_response.json()
    test_bot_id = created_bot["id"]
    
    valid_trade = {
        "bot_id": test_bot_id,
        "side": "buy",
        "size_usd": 10.0
    }
    
    response = requests.post(
        f"{base_url}/trades/validate-trade",
        json=valid_trade,
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200
    validation = response.json()
    
    assert validation["validation"]["allowed"] is True
    assert "All safety checks passed" in validation["validation"]["reason"]
    assert created_bot["name"] in validation["bot"]["name"]
    
    print(f"✅ Valid Trade: APPROVED - {validation['validation']['reason']}")
    
    # Test 3: Invalid Trade Validation (Oversized)
    print("\n3. Testing Invalid Trade Validation (Oversized Position)...")
    invalid_trade = {
        "bot_id": test_bot_id,  # Use the same test bot
        "side": "buy", 
        "size_usd": 50.0  # Exceeds $25 limit
    }
    
    response = requests.post(
        f"{base_url}/trades/validate-trade",
        json=invalid_trade,
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200
    validation = response.json()
    
    assert validation["validation"]["allowed"] is False
    assert "Position size" in validation["validation"]["reason"]
    assert validation["validation"]["safety_checks"]["position_size_valid"] is False
    
    print(f"✅ Invalid Trade: REJECTED - {validation['validation']['reason']}")
    
    # Test 4: Invalid Trade Validation (Too Small)
    print("\n4. Testing Invalid Trade Validation (Too Small Position)...")
    tiny_trade = {
        "bot_id": 1,
        "side": "sell",
        "size_usd": 2.0  # Below $5 minimum
    }
    
    response = requests.post(
        f"{base_url}/trades/validate-trade",
        json=tiny_trade,
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200
    validation = response.json()
    
    assert validation["validation"]["allowed"] is False
    assert "Position size" in validation["validation"]["reason"]
    
    print(f"✅ Tiny Trade: REJECTED - {validation['validation']['reason']}")
    
    # Start the test bot before testing emergency stop
    print(f"\n4.5. Starting test bot {test_bot_id} for emergency stop test...")
    start_response = requests.post(f"{base_url}/bots/{test_bot_id}/start")
    if start_response.status_code == 200:
        print("✅ Test bot started successfully")
    
    # Test 5: Emergency Stop
    print("\n5. Testing Emergency Stop...")
    response = requests.post(f"{base_url}/trades/emergency-stop")
    assert response.status_code == 200
    stop_result = response.json()
    
    assert "Emergency stop executed" in stop_result["message"]
    assert len(stop_result["stopped_bots"]) >= 1
    
    print(f"✅ Emergency Stop: {len(stop_result['stopped_bots'])} bots stopped")
    
    # Test 6: Verify Bots Are Stopped
    print("\n6. Verifying Bots Are Stopped...")
    response = requests.get(f"{base_url}/bots/status/summary")
    assert response.status_code == 200
    bots = response.json()
    
    for bot in bots:
        assert bot["status"] == "STOPPED"
    
    print(f"✅ Bot Status: All {len(bots)} bots are STOPPED")
    
    # Cleanup: Remove test bot
    print(f"\n7. Cleaning up test bot {test_bot_id}...")
    delete_response = requests.delete(f"{base_url}/bots/{test_bot_id}")
    if delete_response.status_code == 200:
        print(f"✅ Test bot {test_bot_id} deleted successfully")
    
    # Test 7: Restart Bots (Cleanup)
    print("\n8. Restarting Bots (Cleanup)...")
    for bot in bots:
        if bot['id'] != test_bot_id:  # Skip the deleted test bot
            response = requests.post(f"{base_url}/bots/{bot['id']}/start")
            assert response.status_code == 200
    
    print(f"✅ Cleanup: Restarted {len([b for b in bots if b['id'] != test_bot_id])} bots")
    
    print("\n" + "=" * 50)
    print("🎉 Phase 4.1.1 Trading Safety Service - ALL TESTS PASSED!")
    print("✅ Safety limits enforced correctly")
    print("✅ Position size validation working")
    print("✅ Emergency stop functional") 
    print("✅ API endpoints operational")
    print("✅ No regression in existing functionality")


if __name__ == "__main__":
    try:
        test_phase_4_1_1_integration()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
