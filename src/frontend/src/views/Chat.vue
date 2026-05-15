<script setup lang="ts">
import { nextTick, ref } from "vue";
import { useRouter } from "vue-router";
import { chatStream } from "../api";

const router = useRouter();
const username = localStorage.getItem("username") || "";
const messages = ref<{ role: string; content: string }[]>([]);
const input = ref("");
const loading = ref(false);
const chatEl = ref<HTMLElement | null>(null);

function goDashboard() {
	router.push("/dashboard");
}

function logout() {
	localStorage.removeItem("token");
	localStorage.removeItem("username");
	router.push("/login");
}

async function send() {
	const text = input.value.trim();
	if (!text || loading.value) return;

	messages.value.push({ role: "user", content: text });
	input.value = "";
	loading.value = true;

	messages.value.push({ role: "assistant", content: "" });
	const aiMsg = messages.value[messages.value.length - 1];

	const history = messages.value
		.slice(0, -2)
		.map((m) => ({ role: m.role, content: m.content }));
	const body = await chatStream(text, history);
	if (!body) {
		loading.value = false;
		return;
	}

	const reader = body.getReader();
	const decoder = new TextDecoder();

	while (true) {
		const { done, value } = await reader.read();
		if (done) break;
		const chunk = decoder.decode(value);
		const lines = chunk.split("\n");
		for (const line of lines) {
			if (line.startsWith("data: ") && line !== "data: [DONE]") {
				aiMsg.content += line.slice(6);
				await nextTick();
				chatEl.value?.scrollTo({
					top: chatEl.value.scrollHeight,
					behavior: "smooth",
				});
			}
		}
	}

	loading.value = false;
}

function keydown(e: KeyboardEvent) {
	if (e.key === "Enter" && !e.shiftKey) {
		e.preventDefault();
		send();
	}
}
</script>

<template>
  <div class="chat-layout">
    <aside class="sidebar">
      <h2>招聘数据智能系统</h2>
      <nav>
        <a @click="goDashboard">数据可视化</a>
        <a class="active">智能客服</a>
      </nav>
      <div class="user-info">
        <span>{{ username }}</span>
        <button @click="logout">退出</button>
      </div>
    </aside>

    <main class="chat-main">
      <div class="chat-box" ref="chatEl">
        <div v-if="messages.length === 0" class="welcome">
          <p>你好，我是招聘数据分析助手</p>
          <p class="hint">可以问我关于薪资趋势、热门岗位、求职建议等问题</p>
        </div>
        <div v-for="(m, i) in messages" :key="i" :class="['message', m.role]">
          <div class="avatar">{{ m.role === 'user' ? '我' : 'AI' }}</div>
          <div class="bubble">{{ m.content }}</div>
        </div>
      </div>

      <div class="input-area">
        <input
          v-model="input"
          @keydown="keydown"
          placeholder="输入你的问题..."
          :disabled="loading"
        />
        <button @click="send" :disabled="loading">
          {{ loading ? '...' : '发送' }}
        </button>
      </div>
    </main>
  </div>
</template>

<style scoped>
.chat-layout {
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

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chat-box {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.welcome {
  text-align: center;
  margin-top: 120px;
  color: #999;
}

.welcome p { margin-bottom: 8px; }
.welcome .hint { font-size: 13px; color: #bbb; }

.message { display: flex; gap: 10px; max-width: 80%; }
.message.user { align-self: flex-end; flex-direction: row-reverse; }
.message.assistant { align-self: flex-start; }

.avatar {
  width: 32px; height: 32px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; color: #fff; flex-shrink: 0;
}
.message.user .avatar { background: #1677ff; }
.message.assistant .avatar { background: #52c41a; }

.bubble {
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
}
.message.user .bubble { background: #1677ff; color: #fff; }
.message.assistant .bubble { background: #fff; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }

.input-area {
  display: flex;
  padding: 16px 24px;
  background: #fff;
  border-top: 1px solid #e8e8e8;
  gap: 12px;
}

.input-area input {
  flex: 1;
  padding: 10px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
}

.input-area button {
  padding: 10px 24px;
  background: #1677ff;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.input-area button:hover { background: #4096ff; }
.input-area button:disabled { background: #91caff; cursor: not-allowed; }
</style>
