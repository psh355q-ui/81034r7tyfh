import pytest
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

class TestKillSwitchIntegration:
    """Kill Switch 통합 테스트"""
    
    def test_kill_switch_lifecycle(self, client):
        """
        Kill Switch 전체 라이프사이클 테스트
        """
        # 1. 초기 상태 확인
        response = client.get("/monitoring/kill-switch")
        assert response.status_code == 200
        data = response.json()
        initial_state = data.get("is_active", False)
        
        # 만약 이미 켜져 있다면 끄고 시작
        if initial_state:
            deactivate_response = client.post("/monitoring/kill-switch/deactivate", json={"message": "Reset"})
            assert deactivate_response.status_code == 200
            
        # 2. 수동 활성화
        activate_payload = {
            "reason": "MANUAL",  # Enum 값(대문자) 사용해야 할 수 있음. monitoring_router Line 357 참고.
            "message": "Testing Kill Switch Trigger",
            "metadata": {"test_run_id": "12345"}
        }
        # monitoring_router.py: KillSwitchReason[request.reason.upper()]
        
        response = client.post("/monitoring/kill-switch/activate", json=activate_payload)
        # 400 에러 발생 시 디버깅을 위해 print 필요하지만 여기선 assert로 체크
        if response.status_code != 200:
            print(f"Activate Failed: {response.json()}")
            
        assert response.status_code == 200
        result = response.json()
        assert result["status"]["is_active"] is True
        
        # 3. 활성화 상태 확인
        response = client.get("/monitoring/kill-switch")
        assert response.status_code == 200
        assert response.json()["is_active"] is True
        
        # 4. 비활성화
        # deactivate_kill_switch(message: Optional[str] = None) -> Query param 'message'
        response = client.post("/monitoring/kill-switch/deactivate?message=TestComplete")
        assert response.status_code == 200
        result = response.json()
        assert result["status"]["is_active"] is False
        
        # 5. 최종 상태 확인
        response = client.get("/monitoring/kill-switch")
        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_kill_switch_persistence(self, client):
        """Kill Switch 상태가 메모리에 잘 유지되는지 확인"""
        # 활성화
        client.post("/monitoring/kill-switch/activate", json={"reason": "MANUAL", "message": "Check"})
        
        # 상태 확인
        response = client.get("/monitoring/kill-switch")
        assert response.json()["is_active"] is True
        
        # 비활성화
        client.post("/monitoring/kill-switch/deactivate")
        
        # 상태 확인
        response = client.get("/monitoring/kill-switch")
        assert response.json()["is_active"] is False
