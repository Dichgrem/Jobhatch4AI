import csv

from app.services.pipeline import load_pipeline_state, run_pipeline, save_pipeline_state


def _make_csv(path: str, rows: list[dict]) -> str:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    return path


class TestPipeline:
    def test_run_basic(self, temp_db):
        rows = [
            {
                "keyword": "精通Java Spring Boot MySQL开发",
                "salary": "15K-25K",
                "education": "本科",
            },
            {
                "keyword": "熟悉Python Django机器学习",
                "salary": "20K-35K",
                "education": "硕士",
            },
            {
                "keyword": "C++嵌入式Linux开发经验",
                "salary": "12K-18K",
                "education": "本科",
            },
            {"keyword": "Java后端微服务架构", "salary": "18K-28K", "education": "本科"},
            {
                "keyword": "Python数据分析pandas numpy",
                "salary": "10K-15K",
                "education": "大专",
            },
            {"keyword": "Go开发高并发服务", "salary": "25K-40K", "education": "本科"},
        ]
        path = "/tmp/test_pipeline_basic.csv"
        _make_csv(path, rows)
        state = run_pipeline(path)
        assert state["total_jobs"] == 6
        assert len(state["top_skills"]) > 0
        assert sum(state["salary_distribution"]["data"]) == 6

    def test_avg_salary(self, temp_db):
        rows = [
            {"keyword": "test", "salary": "10K-20K"},
            {"keyword": "test", "salary": "20K-30K"},
        ]
        path = "/tmp/test_pipeline_salary.csv"
        _make_csv(path, rows)
        state = run_pipeline(path)
        assert state["avg_salary"] == 20000

    def test_missing_columns(self, temp_db):
        rows = [{"keyword": "Java开发工程师"}]
        path = "/tmp/test_pipeline_minimal.csv"
        _make_csv(path, rows)
        state = run_pipeline(path)
        assert state["total_jobs"] == 1

    def test_save_load(self, temp_db):
        state = {"total_jobs": 100, "avg_salary": 15000}
        save_pipeline_state(state)
        loaded = load_pipeline_state()
        assert loaded["total_jobs"] == 100
        assert loaded["avg_salary"] == 15000
        assert "salary_distribution" in loaded

    def test_load_default(self, temp_db):
        import app.services.database as db

        old = str(db.DB_PATH)
        db.DB_PATH = type(db.DB_PATH)(db.DB_PATH.parent / "nonexistent.db")
        state = load_pipeline_state()
        assert state["total_jobs"] == 0
        db.DB_PATH = type(db.DB_PATH)(old)
