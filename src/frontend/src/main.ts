import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";
import "./style.css";
import App from "./App.vue";
import Chat from "./views/Chat.vue";
import Dashboard from "./views/Dashboard.vue";
import Login from "./views/Login.vue";

const routes = [
	{ path: "/", redirect: "/login" },
	{ path: "/login", component: Login },
	{ path: "/dashboard", component: Dashboard },
	{ path: "/chat", component: Chat },
];

const router = createRouter({
	history: createWebHistory(),
	routes,
});

router.beforeEach((to) => {
	const token = localStorage.getItem("token");
	if (to.path !== "/login" && !token) {
		return "/login";
	}
});

const app = createApp(App);
app.use(router);
app.mount("#app");
