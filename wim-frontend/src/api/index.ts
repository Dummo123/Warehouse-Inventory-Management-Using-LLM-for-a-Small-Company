import api from "./client";

export const login = (username: string, password: string) => {
  const form = new URLSearchParams();
  form.append("username", username);
  form.append("password", password);
  return api.post("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
};
export const getUsers = () => api.get("/auth/users");
export const createUser = (data: object) => api.post("/auth/users", data);

export const getStock = (params?: object) => api.get("/stock", { params });
export const getFinishedStock = () => api.get("/stock/finished");

export const getArticles = (article_type?: string) =>
  api.get("/articles", { params: article_type ? { article_type } : {} });
export const createArticle = (data: object) => api.post("/articles", data);
export const updateArticle = (code: string, data: object) => api.patch(`/articles/${code}`, data);
export const deleteArticle = (code: string) => api.delete(`/articles/${code}`);
export const getBOM = (code: string) => api.get(`/articles/${code}/bom`);
export const setBOM = (code: string, entries: object[]) => api.put(`/articles/${code}/bom`, entries);

export const getMovements = (params?: object) => api.get("/movements", { params });
export const postReceipt = (data: object) => api.post("/movements/receipt", data);
export const postShipment = (data: object) => api.post("/movements/shipment", data);
export const postProduction = (data: object) => api.post("/movements/production", data);
export const postReturn = (data: object) => api.post("/movements/return", data);

export const exportExcel = (date_from?: string, date_to?: string) =>
  api.get("/reports/export", { params: { date_from, date_to }, responseType: "blob" });
