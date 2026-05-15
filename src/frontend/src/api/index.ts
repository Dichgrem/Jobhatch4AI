const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

async function request(url: string, options: RequestInit = {}) {
	const token = localStorage.getItem("token");
	const headers: Record<string, string> = {
		"Content-Type": "application/json",
		...(options.headers as Record<string, string>),
	};
	if (token) headers.Authorization = `Bearer ${token}`;

	const res = await fetch(`${BASE}${url}`, { ...options, headers });

	if (!res.ok) {
		const body = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(body.detail || "请求失败");
	}

	return res.json();
}

export function login(username: string, password: string) {
	return request("/auth/login", {
		method: "POST",
		body: JSON.stringify({ username, password }),
	});
}

export function register(username: string, password: string) {
	return request("/auth/register", {
		method: "POST",
		body: JSON.stringify({ username, password }),
	});
}

export function getSummary() {
	return request("/data/summary");
}

export function getSalaryDistribution() {
	return request("/data/salary-distribution");
}

export function getEducationDistribution() {
	return request("/data/education-distribution");
}

export function getSkillWordcloud() {
	return request("/data/skill-wordcloud");
}

export async function chatStream(
	message: string,
	history: { role: string; content: string }[] = [],
) {
	const token = localStorage.getItem("token");
	const res = await fetch(`${BASE}/chat`, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			...(token ? { Authorization: `Bearer ${token}` } : {}),
		},
		body: JSON.stringify({ message, history }),
	});
	if (!res.ok) throw new Error("请求失败");
	return res.body;
}
