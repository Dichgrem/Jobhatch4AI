from app.services.rag import build_rag_prompt, load_chunks_from_dir
import tempfile
from pathlib import Path


class TestBuildRagPrompt:
    def test_basic_prompt(self):
        prompt = build_rag_prompt("什么是Python？", ["Python是一种编程语言。"])
        assert len(prompt) == 2
        assert prompt[0]["role"] == "system"
        assert prompt[1]["role"] == "user"
        assert "Python是一种编程语言" in prompt[1]["content"]
        assert "什么是Python？" in prompt[1]["content"]

    def test_multiple_chunks(self):
        chunks = ["数据1", "数据2", "数据3"]
        prompt = build_rag_prompt("测试问题", chunks)
        content = prompt[1]["content"]
        assert "数据1" in content
        assert "数据2" in content
        assert "数据3" in content
        assert "---" in content

    def test_empty_chunks(self):
        prompt = build_rag_prompt("问题", [])
        assert len(prompt) == 2
        assert prompt[1]["role"] == "user"


class TestLoadChunksFromDir:
    def test_load_txt_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "doc1.txt").write_text("数据块1")
            (Path(tmp) / "doc2.txt").write_text("数据块2")
            (Path(tmp) / "other.md").write_text("忽略")

            chunks = load_chunks_from_dir(tmp, "*.txt")
            assert len(chunks) == 2
            assert "数据块1" in chunks
            assert "数据块2" in chunks

    def test_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            chunks = load_chunks_from_dir(tmp, "*.txt")
            assert chunks == []
