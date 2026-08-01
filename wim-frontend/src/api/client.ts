import axios from "axios";

// ────────────────────────────────────────────────────────────────────────
// АВТОРИЗАЦИЯ ОТКЛЮЧЕНА (30.07.2026): токен больше не добавляется к
// запросам и не проверяется бэкендом, поэтому интерцепторы для JWT и
// редирект на /login при 401 убраны.
//
// Чтобы вернуть — восстановите:
//
//   api.interceptors.request.use((config) => {
//     const token = localStorage.getItem("token");
//     if (token) config.headers.Authorization = `Bearer ${token}`;
//     return config;
//   });
//   api.interceptors.response.use(
//     (res) => res,
//     (err) => {
//       if (err.response?.status === 401) {
//         localStorage.removeItem("token");
//         window.location.href = "/login";
//       }
//       return Promise.reject(err);
//     }
//   );
// ────────────────────────────────────────────────────────────────────────

const api = axios.create({ baseURL: "/api" });

export default api;
