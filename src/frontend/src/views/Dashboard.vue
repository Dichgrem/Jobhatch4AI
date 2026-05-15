<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
	getEducationDistribution,
	getSalaryDistribution,
	getSummary,
} from "../api";

const router = useRouter();
const username = localStorage.getItem("username") || "";
const summary = ref<any>({});
const salaryData = ref<any>({});
const educationData = ref<any>({});

onMounted(async () => {
	summary.value = await getSummary();
	salaryData.value = await getSalaryDistribution();
	educationData.value = await getEducationDistribution();
});

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
      <section class="cards">
        <div class="card">
          <h3>岗位总数</h3>
          <p class="num">{{ summary.total_jobs || '-' }}</p>
        </div>
        <div class="card">
          <h3>平均薪资</h3>
          <p class="num">{{ summary.avg_salary ? (summary.avg_salary / 1000).toFixed(1) + 'K' : '-' }}</p>
        </div>
        <div class="card">
          <h3>热门技能</h3>
          <p>{{ (summary.top_skills || []).slice(0, 3).join('、') || '-' }}</p>
        </div>
      </section>

      <section class="charts">
        <div class="chart-box">
          <h3>薪资分布</h3>
          <div class="bar-chart">
            <div v-for="(v, i) in salaryData.data || []" :key="i" class="bar-item">
              <span class="label">{{ salaryData.labels?.[i] }}</span>
              <div class="bar" :style="{ width: (v / Math.max(...(salaryData.data||[1])) * 100) + '%' }"></div>
              <span class="val">{{ v }}</span>
            </div>
          </div>
        </div>
        <div class="chart-box">
          <h3>学历分布</h3>
          <div class="bar-chart">
            <div v-for="(v, i) in educationData.data || []" :key="i" class="bar-item">
              <span class="label">{{ educationData.labels?.[i] }}</span>
              <div class="bar" :style="{ width: (v / Math.max(...(educationData.data||[1])) * 100) + '%' }"></div>
              <span class="val">{{ v }}</span>
            </div>
          </div>
        </div>
      </section>
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
}

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
}

.chart-box {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.chart-box h3 { font-size: 14px; color: #666; margin-bottom: 16px; }

.bar-chart { display: flex; flex-direction: column; gap: 8px; }
.bar-item { display: flex; align-items: center; gap: 8px; }
.label { width: 70px; font-size: 12px; color: #666; text-align: right; }
.bar { height: 20px; background: #1677ff; border-radius: 4px; min-width: 4px; }
.val { font-size: 12px; color: #333; width: 40px; }
</style>
