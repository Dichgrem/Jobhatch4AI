from app.services.preprocess import (
    tokenize,
    build_vocab,
    text_to_bow,
    extract_tech_terms,
    TECH_TERMS,
)
import numpy as np


class TestTokenize:
    def test_basic_chinese(self):
        result = tokenize("机器学习工程师招聘")
        assert (
            "机器" in result
            or "学习" in result
            or "工程师" in result
            or "招聘" in result
        )
        assert "" not in result

    def test_empty_string(self):
        result = tokenize("")
        assert result == []

    def test_single_char_filtered(self):
        result = tokenize("Python工程师")
        for w in result:
            assert len(w) > 1

    def test_lowercase(self):
        result = tokenize("Python Java PYTHON")
        assert all(w.islower() for w in result)

    def test_mixed_content(self):
        result = tokenize("熟悉Python、Java开发，了解机器学习算法")
        assert len(result) > 0


class TestBuildVocab:
    def test_min_freq(self):
        tokens = [["python", "python", "java"], ["python"]]
        vocab = build_vocab(tokens, min_freq=2)
        assert "python" in vocab
        assert "java" not in vocab

    def test_max_size(self):
        tokens = [["a", "b", "c", "d", "e"]]
        vocab = build_vocab(tokens, min_freq=1, max_size=3)
        assert len(vocab) <= 3

    def test_empty_input(self):
        vocab = build_vocab([])
        assert vocab == []


class TestTextToBow:
    def test_basic_vector(self):
        vocab = ["python", "java", "c++"]
        vec = text_to_bow(["python", "python", "java"], vocab)
        assert vec[0] == 2
        assert vec[1] == 1
        assert vec[2] == 0

    def test_missing_terms_ignored(self):
        vocab = ["python"]
        vec = text_to_bow(["golang"], vocab)
        assert vec[0] == 0

    def test_return_type(self):
        vocab = ["a", "b"]
        vec = text_to_bow(["a"], vocab)
        assert isinstance(vec, np.ndarray)
        assert vec.dtype == np.float32


class TestExtractTechTerms:
    def test_matching_terms(self):
        tokens = ["python", "django", "nodejs", "unknown"]
        result = extract_tech_terms(tokens, TECH_TERMS)
        assert "python" in result
        assert "django" in result
        assert "unknown" not in result

    def test_empty_tokens(self):
        result = extract_tech_terms([], TECH_TERMS)
        assert result == []

    def test_no_matches(self):
        result = extract_tech_terms(["foo", "bar", "baz"], TECH_TERMS)
        assert result == []


class TestTechTerms:
    def test_has_core_terms(self):
        assert "python" in TECH_TERMS
        assert "java" in TECH_TERMS
        assert "pytorch" in TECH_TERMS
        assert "docker" in TECH_TERMS
        assert "kubernetes" in TECH_TERMS
        assert "mysql" in TECH_TERMS
