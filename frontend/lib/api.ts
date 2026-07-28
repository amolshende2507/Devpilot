const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface RequestOptions extends RequestInit {
  token?: string;
}

export async function apiFetch<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { token, headers, ...rest } = options;

  const defaultHeaders: Record<string, string> = {
    "Content-Type": "application/json",
  };

  const savedToken = typeof window !== "undefined" ? localStorage.getItem("devpilot_token") : null;
  const activeToken = token || savedToken;

  if (activeToken) {
    defaultHeaders["Authorization"] = `Bearer ${activeToken}`;
  }

  const mergedHeaders = {
    ...defaultHeaders,
    ...headers,
  };

  const response = await fetch(`${API_URL}${endpoint}`, {
    headers: mergedHeaders,
    ...rest,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const errorMessage = errorData.detail || `Request failed with status ${response.status}`;
    throw new Error(errorMessage);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json() as Promise<T>;
}