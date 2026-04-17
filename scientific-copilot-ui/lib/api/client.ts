import axios from 'axios'

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? '/backend'
export const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? 'dev-api-key'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
  },
  auth: {
    username: process.env.NEXT_PUBLIC_API_USER ?? 'admin',
    password: process.env.NEXT_PUBLIC_API_PASSWORD ?? 'password',
  }
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.warn('API error:', error.response?.data ?? error.message)
    return Promise.reject(error)
  }
)
