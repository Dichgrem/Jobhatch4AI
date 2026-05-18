<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
  getClusters,
  getEducationDistribution,
  getSalaryDistribution,
  getSkillWordcloud,
  getSummary,
} from "../api";

const router = useRouter();
const username = localStorage.getItem("username") || "";
const summary = ref<{
	total_jobs: number;
	avg_salary: number;
	top_skills: string[];
}>({
	total_jobs: 0,
	avg_salary: 0,
	top_skills: [],
});
const salaryData = ref<{ labels: string[]; data: number[] }>({
	labels: [],
	data: [],
});
const educationData = ref<{ labels: string[]; data: number[] }>({
	labels: [],
	data: [],
});
const wordcloud = ref<{ word: string; count: number }[]>([]);
const clusters = ref<{
	n_clusters: number;
	clusters: {
		cluster_id: number;
		count: number;
		percentage: number;
		top_skills: { skill: string; count: number }[];
	}[];
}>({ n_clusters: 0, clusters: [] });
const loading = ref(true);
const error = ref("");
const uploading = ref(false);
const uploadMsg = ref("");

async function reload() {
  loading.value = true;
  error.value = "";
  try {
    const [s, sal, edu, wc, cls] = await Promise.all([
      getSummary(),
      getSalaryDistribution(),
      getEducationDistribution(),
      getSkillWordcloud(),
      getClusters(),
    ]);
    summary.value = s;
    salaryData.value = sal;
    educationData.value = edu;
    wordcloud.value = wc.words || [];
    clusters.value = cls || { n_clusters: 0, clusters: [] };
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "加载失败";
  } finally {
    loading.value = false;
  }
}

async function uploadCSV(e: Event) {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  uploading.value = true;
  uploadMsg.value = "";
  try {
    const token = localStorage.getItem("token");
    const form = new FormData();
    form.append("file", file);
    const res = await fetch("/api/data/upload", {
      method: "POST",
      body: form,
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error((await res.json()).detail || "上传失败");
    const data = await res.json();
    uploadMsg.value = `已处理 ${data.total_jobs} 条数据`;
    await reload();
  } catch (e: unknown) {
    uploadMsg.value = e instanceof Error ? e.message : "上传失败";
  } finally {
    uploading.value = false;
    input.value = "";
  }
}

function maxVal(data: number[]): number {
	return Math.max(...data, 1);
}

onMounted(reload);

function goChat() {
	router.push("/chat");
}

function logout() {
	localStorage.removeItem("token");
	localStorage.removeItem("username");
	router.push("/login");
}
</script>

<template>
  <div class="dashboard">
    <aside class="sidebar">
      <h2>招聘数据智能系统</h2>
      <nav>
        <a class="active">数据可视化</a>
        <a @click="goChat">智能客服</a>
      </nav>
      <div class="user-info">
        <span>{{ username }}</span>
        <button @click="logout">退出</button>
      </div>
    </aside>

    <main class="content">
      <div v-if="loading" class="loading">加载中...</div>
      <p v-if="error" class="error">{{ error }}</p>

      <template v-if="!loading && !error">
        <section class="upload-bar">
          <label class="upload-btn">
            {{ uploading ? "上传中..." : "上传 CSV 数据" }}
            <input type="file" accept=".csv" @change="uploadCSV" :disabled="uploading" hidden />
          </label>
          <span v-if="uploadMsg" class="upload-msg">{{ uploadMsg }}</span>
        </section>

        <section class="cards">
          <div class="card">
            <h3>岗位总数</h3>
            <p class="num">{{ summary.total_jobs.toLocaleString() }}</p>
          </div>
          <div class="card">
            <h3>平均薪资</h3>
            <p class="num">{{ summary.avg_salary ? (summary.avg_salary / 1000).toFixed(1) + 'K' : '-' }}</p>
          </div>
          <div class="card">
            <h3>热门技能</h3>
            <p>{{ summary.top_skills?.slice(0, 4).join('、') || '-' }}</p>
          </div>
        </section>

        <section class="charts">
          <div class="chart-box">
            <h3>薪资分布</h3>
            <div v-if="salaryData.data.length" class="bar-chart">
              <div v-for="(v, i) in salaryData.data" :key="i" class="bar-item">
                <span class="label">{{ salaryData.labels[i] }}</span>
                <div class="bar" :style="{ width: (v / maxVal(salaryData.data) * 100) + '%' }" />
                <span class="val">{{ v.toLocaleString() }}</span>
              </div>
            </div>
            <p v-else class="empty">暂无数据，请先上传 CSV</p>
          </div>

          <div class="chart-box">
            <h3>学历分布</h3>
            <div v-if="educationData.data.length" class="bar-chart">
              <div v-for="(v, i) in educationData.data" :key="i" class="bar-item">
                <span class="label">{{ educationData.labels[i] }}</span>
                <div class="bar" :style="{ width: (v / maxVal(educationData.data) * 100) + '%' }" />
                <span class="val">{{ v.toLocaleString() }}</span>
              </div>
            </div>
            <p v-else class="empty">暂无数据，请先上传 CSV</p>
          </div>
        </section>

        <section class="wordcloud-section" v-if="wordcloud.length">
          <div class="chart-box full-width">
            <h3>技能词云</h3>
            <div class="wordcloud">
              <span
                v-for="w in wordcloud.slice(0, 30)"
                :key="w.word"
                class="tag"
                :style="{ fontSize: (12 + (w.count / maxVal(wordcloud.map(x => x.count))) * 20) + 'px', opacity: 0.5 + (w.count / maxVal(wordcloud.map(x => x.count))) * 0.5 }"
              >{{ w.word }}</span>
            </div>
          </div>
        </section>

        <section class="cluster-section" v-if="clusters.clusters.length">
          <div class="chart-box full-width">
            <h3>Kmeans 聚类分析 ({{ clusters.n_clusters }} 类)</h3>
            <div class="cluster-grid">
              <div v-for="c in clusters.clusters" :key="c.cluster_id" class="cluster-card">
                <h4>聚类 {{ c.cluster_id + 1 }}</h4>
                <p class="cluster-count">{{ c.count.toLocaleString() }} 条 ({{ c.percentage }}%)</p>
                <div class="cluster-skills">
                  <span v-for="s in c.top_skills.slice(0, 5)" :key="s.skill" class="skill-tag">{{ s.skill }} <small>{{ s.count }}</small></span>
                </div>
              </div>
            </div>
          </div>
        </section>
      </template>
    </main>
  </div>
</template>

<style scoped>
.dashboard {
  display: flex;
  min-height: 100vh;
  background: #f0f2f5;
}

.sidebar {
  width: 220px;
  background: #001529;
  color: #fff;
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
}

.sidebar h2 {
  font-size: 16px;
  margin-bottom: 24px;
  text-align: center;
}

.sidebar nav a {
  display: block;
  padding: 10px 12px;
  border-radius: 4px;
  cursor: pointer;
  color: #ccc;
  margin-bottom: 4px;
}

.sidebar nav a.active,
.sidebar nav a:hover {
  background: #1677ff;
  color: #fff;
}

.user-info {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.user-info button {
  padding: 6px;
  background: #ff4d4f;
  border: none;
  color: #fff;
  border-radius: 4px;
  cursor: pointer;
}

.content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.loading, .error { text-align: center; padding: 40px; }
.error { color: #ff4d4f; }

.upload-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.upload-btn {
  display: inline-block;
  padding: 8px 16px;
  background: #1677ff;
  color: #fff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}

.upload-btn:hover { background: #4096ff; }
.upload-msg { font-size: 13px; color: #52c41a; }

.cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.card {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.card h3 { font-size: 14px; color: #666; margin-bottom: 8px; }
.card .num { font-size: 28px; font-weight: 700; color: #1677ff; }
.card p { font-size: 14px; color: #333; }

.charts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.chart-box {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.chart-box h3 { font-size: 14px; color: #666; margin-bottom: 16px; }
.empty { color: #bbb; font-size: 13px; text-align: center; padding: 20px; }

.bar-chart { display: flex; flex-direction: column; gap: 8px; }
.bar-item { display: flex; align-items: center; gap: 8px; }
.label { width: 70px; font-size: 12px; color: #666; text-align: right; }
.bar { height: 20px; background: #1677ff; border-radius: 4px; transition: width 0.5s; }
.val { font-size: 12px; color: #333; width: 60px; }

.full-width { grid-column: 1 / -1; }

.wordcloud {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  justify-content: center;
  padding: 10px;
}

.tag {
  color: #1677ff;
  font-weight: 500;
  transition: all 0.2s;
}

.tag:hover { transform: scale(1.1); }

.cluster-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.cluster-card {
  background: #f7f8fa;
  padding: 14px;
  border-radius: 6px;
}

.cluster-card h4 { font-size: 13px; color: #1677ff; margin-bottom: 6px; }

.cluster-count { font-size: 18px; font-weight: 700; color: #333; margin-bottom: 8px; }

.cluster-skills {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.skill-tag {
  background: #e6f0ff;
  color: #1677ff;
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 12px;
}

.skill-tag small { color: #999; }
</style>
