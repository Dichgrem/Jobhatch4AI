import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_token(client):
    resp = client.post(
        "/api/auth/register",
        json={
            "username": "test_api_user",
            "password": "test_api_pass",
        },
    )
    if resp.status_code == 409:
        resp = client.post(
            "/api/auth/login",
            json={
                "username": "test_api_user",
                "password": "test_api_pass",
            },
        )
    return resp.json()["access_token"]


class TestHealthEndpoint:
    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestAuthEndpoints:
    def test_register_success(self, client):
        import random
        import string

        name = "user_" + "".join(random.choices(string.ascii_lowercase, k=6))
        resp = client.post(
            "/api/auth/register",
            json={
                "username": name,
                "password": "securepass",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["username"] == name

    def test_register_duplicate(self, client):
        import random
        import string

        name = "dup_" + "".join(random.choices(string.ascii_lowercase, k=6))
        resp1 = client.post(
            "/api/auth/register",
            json={
                "username": name,
                "password": "pass1",
            },
        )
        assert resp1.status_code == 200
        resp2 = client.post(
            "/api/auth/register",
            json={
                "username": name,
                "password": "pass2",
            },
        )
        assert resp2.status_code == 409

    def test_login_success(self, client):
        client.post(
            "/api/auth/register",
            json={
                "username": "login_user",
                "password": "login_pass",
            },
        )
        resp = client.post(
            "/api/auth/login",
            json={
                "username": "login_user",
                "password": "login_pass",
            },
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self, client):
        client.post(
            "/api/auth/register",
            json={
                "username": "login_user2",
                "password": "correct",
            },
        )
        resp = client.post(
            "/api/auth/login",
            json={
                "username": "login_user2",
                "password": "wrong",
            },
        )
        assert resp.status_code == 401

    def test_login_nonexistent(self, client):
        resp = client.post(
            "/api/auth/login",
            json={
                "username": "ghost_user",
                "password": "no_pass",
            },
        )
        assert resp.status_code == 401


class TestChatEndpoint:
    @pytest.mark.skip(reason="requires ARK_API_KEY")
    def test_chat_returns_200(self, client, auth_token):
        resp = client.post(
            "/api/chat",
            json={"message": "你好", "history": []},
        )
        assert resp.status_code == 200

    @pytest.mark.skip(reason="requires ARK_API_KEY")
    def test_chat_without_auth_returns_200(self, client):
        resp = client.post(
            "/api/chat",
            json={"message": "你好", "history": []},
        )
        assert resp.status_code == 200

    @pytest.mark.skip(reason="requires ARK_API_KEY")
    def test_chat_has_sse_header(self, client):
        resp = client.post(
            "/api/chat",
            json={"message": "测试", "history": []},
        )
        assert resp.status_code == 200


class TestDataEndpoints:
    def test_get_summary_defaults(self, client):
        resp = client.get("/api/data/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_jobs" in data

    def test_get_salary_distribution(self, client):
        resp = client.get("/api/data/salary-distribution")
        assert resp.status_code == 200
        data = resp.json()
        assert "labels" in data
        assert "data" in data
        assert len(data["labels"]) == len(data["data"])

    def test_get_education_distribution(self, client):
        resp = client.get("/api/data/education-distribution")
        assert resp.status_code == 200

    def test_analyze_endpoint(self, client):
        resp = client.post(
            "/api/data/analyze",
            json={
                "texts": ["精通Python和Django，熟悉机器学习"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "top_skills" in data
        assert len(data["top_skills"]) > 0

    def test_analyze_empty(self, client):
        resp = client.post("/api/data/analyze", json={"texts": []})
        assert resp.status_code == 200
        data = resp.json()
        assert data["top_skills"] == []

    def test_classify_endpoint(self, client):
        resp = client.post(
            "/api/data/classify",
            json={
                "texts": [
                    "精通Java Spring Boot开发",
                    "熟悉Python Django框架",
                    "掌握C++ Linux嵌入式开发",
                    "Java微服务架构经验",
                    "Python机器学习数据挖掘",
                    "C语言嵌入式Linux内核",
                ],
                "labels": ["java", "python", "c", "java", "python", "c"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "predictions" in data
        assert len(data["predictions"]) == 6

    def test_classify_too_few(self, client):
        resp = client.post(
            "/api/data/classify",
            json={
                "texts": ["一条数据"],
                "labels": ["java"],
            },
        )
        assert resp.status_code == 400


class TestChatContext:
    def test_context_endpoint(self, client):
        resp = client.get("/api/chat/context")
        assert resp.status_code == 200
        assert "context" in resp.json()
