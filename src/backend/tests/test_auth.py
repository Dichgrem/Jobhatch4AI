from app.services import auth


class TestAuth:
    def test_hash_password_consistent(self):
        h1 = auth.hash_password("test123")
        h2 = auth.hash_password("test123")
        assert h1 == h2
        assert len(h1) == 64

    def test_hash_password_different(self):
        h1 = auth.hash_password("test123")
        h2 = auth.hash_password("test456")
        assert h1 != h2

    def test_register_new_user(self, temp_db):
        token = auth.register("testuser", "pass123")
        assert token is not None
        assert auth.get_username_by_token(token) == "testuser"

    def test_register_duplicate(self, temp_db):
        auth.register("testuser", "pass123")
        token = auth.register("testuser", "pass456")
        assert token is None

    def test_authenticate_success(self, temp_db):
        auth.register("testuser", "pass123")
        token = auth.authenticate("testuser", "pass123")
        assert token is not None

    def test_authenticate_wrong_password(self, temp_db):
        auth.register("testuser", "pass123")
        token = auth.authenticate("testuser", "wrongpass")
        assert token is None

    def test_authenticate_nonexistent(self, temp_db):
        token = auth.authenticate("nobody", "pass123")
        assert token is None

    def test_remove_token(self, temp_db):
        token = auth.register("testuser", "pass123")
        auth.remove_token(token)
        assert auth.get_username_by_token(token) is None

    def test_generate_token_unique(self):
        t1 = auth.generate_token()
        t2 = auth.generate_token()
        assert t1 != t2
        assert len(t1) == 64
