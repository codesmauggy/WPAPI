import axios from "axios";

const apiClient = axios.create({
  baseURL: "/api/whatsapp",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error("API Error:", error);

    return Promise.reject(error);
  },
);

export default apiClient;