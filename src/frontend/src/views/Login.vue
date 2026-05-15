<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { login, register } from "../api";

const router = useRouter();
const username = ref("");
const password = ref("");
const isRegister = ref(false);
const error = ref("");

async function submit() {
	error.value = "";
	try {
		const res = isRegister.value
			? await register(username.value, password.value)
			: await login(username.value, password.value);
		localStorage.setItem("token", res.access_token);
		localStorage.setItem("username", res.username);
		router.push("/dashboard");
	} catch (e: unknown) {
		error.value = e instanceof Error ? e.message : "操作失败";
	}
}
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <h1>招聘数据智能系统</h1>
      <p class="subtitle">{{ isRegister ? '注册新账号' : '用户登录' }}</p>

      <div class="form">
        <input v-model="username" placeholder="用户名" />
        <input v-model="password" type="password" placeholder="密码" />
        <p v-if="error" class="error">{{ error }}</p>
        <button @click="submit">{{ isRegister ? '注册' : '登录' }}</button>
      </div>

      <p class="switch">
        {{ isRegister ? '已有账号？' : '没有账号？' }}
        <a href="#" @click.prevent="isRegister = !isRegister; error = ''">
          {{ isRegister ? '去登录' : '去注册' }}
        </a>
      </p>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #f0f2f5;
}

.login-card {
  background: #fff;
  padding: 40px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  width: 360px;
  text-align: center;
}

h1 { font-size: 22px; margin-bottom: 8px; }
.subtitle { color: #666; margin-bottom: 24px; }

.form { display: flex; flex-direction: column; gap: 12px; }
input {
  padding: 10px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
}
button {
  padding: 10px;
  background: #1677ff;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}
button:hover { background: #4096ff; }
.error { color: #ff4d4f; font-size: 13px; }
.switch { margin-top: 16px; font-size: 13px; color: #666; }
.switch a { color: #1677ff; }
</style>
