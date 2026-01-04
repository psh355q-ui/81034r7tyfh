
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from backend.main import app

class TestDataBackfillRouter:
    """Data Backfill Router 테스트"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
        
    def test_price_backfill_validation_1m(self, client):
        """1분봉 데이터 7일 제한 검증"""
        # 8일 기간 설정 (오늘부터 8일 전)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=8)
        
        response = client.post("/api/backfill/prices", json={
            "tickers": ["AAPL"],
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "interval": "1m"
        })
        
        # 400 Bad Request 예상
        assert response.status_code == 400
        assert "7 days" in response.json()["detail"]

    def test_price_backfill_validation_1h(self, client):
        """1시간봉 데이터 730일 제한 검증"""
        # 732일 기간 설정 (약 2년 + 2일)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=732)
        
        response = client.post("/api/backfill/prices", json={
            "tickers": ["AAPL"],
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "interval": "1h"
        })
        
        # 400 Bad Request 예상
        assert response.status_code == 400
        assert "730 days" in response.json()["detail"]

    def test_price_backfill_success(self, client):
        """정상적인 일봉 데이터 요청 검증"""
        # 30일 기간 설정
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        response = client.post("/api/backfill/prices", json={
            "tickers": ["AAPL", "MSFT"],
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "interval": "1d"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
        
        # Job ID 저장
        job_id = data["job_id"]
        
        # 상태 확인
        status_res = client.get(f"/api/backfill/status/{job_id}")
        assert status_res.status_code == 200
        assert status_res.json()["job_id"] == job_id

    def test_news_backfill_success(self, client):
        """뉴스 데이터 백필 요청 검증"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=2)
        
        response = client.post("/api/backfill/news", json={
            "tickers": ["AAPL"],
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "keywords": ["Earnings", "Growth"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        
    def test_invalid_interval(self, client):
        """잘못된 인터벌 검증"""
        response = client.post("/api/backfill/prices", json={
            "tickers": ["AAPL"],
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "interval": "invalid_interval"
        })
        
        # Pydantic validation error (422) or Custom validation (400)
        assert response.status_code in [400, 422]

    def test_invalid_date_format(self, client):
        """잘못된 날짜 형식 검증"""
        response = client.post("/api/backfill/prices", json={
            "tickers": ["AAPL"],
            "start_date": "2024/01/01",  # Invalid format
            "end_date": "2024-01-31",
            "interval": "1d"
        })
        
        assert response.status_code in [400, 422]
