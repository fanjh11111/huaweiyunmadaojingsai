const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api'

export const apiBaseUrl = configuredBaseUrl.replace(/\/+$/, '')

/** Build an API URL that works both behind Nginx in production and Vite locally. */
export function apiUrl(path: string): string {
  return `${apiBaseUrl}/${path.replace(/^\/+/, '')}`
}
