import axios from 'axios'

export const api = axios.create({
  baseURL: '/api/v1',
  timeout: 20000
})

api.interceptors.response.use(undefined, (error) => {
  const message = error?.response?.data?.error || error.message || 'Network error'
  return Promise.reject(new Error(message))
})
