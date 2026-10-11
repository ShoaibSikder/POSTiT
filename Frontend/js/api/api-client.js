import { API_BASE_URL, API_ORIGIN } from "../config.js";

export class ApiError extends Error {
  constructor(message, { status = 0, data = null } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

function detailFrom(data, status) {
  if (typeof data === "string") return data;
  if (Array.isArray(data?.detail)) return data.detail.join(" ");
  if (typeof data?.detail === "string") return data.detail;
  if (typeof data?.message === "string") return data.message;
  if (data && typeof data === "object") {
    const messages = Object.entries(data)
      .flatMap(([field, value]) => {
        const values = Array.isArray(value) ? value : [value];
        return values.map((message) =>
          typeof message === "string"
            ? `${field === "non_field_errors" ? "" : `${field}: `}${message}`
            : "",
        );
      })
      .filter(Boolean);
    if (messages.length) return messages.join(" ");
  }
  if (status === 401 || status === 403) {
    return "Your session may have expired or you may not have permission. Please sign in again.";
  }
  return `The request could not be completed (HTTP ${status}).`;
}

async function csrfToken() {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/auth/csrf/`, {
      credentials: "include",
      headers: { Accept: "application/json" },
    });
  } catch (error) {
    if (error instanceof TypeError) {
      throw new ApiError(
        `POSTiT could not reach the backend at ${API_ORIGIN}. Start Django and check the API address in js/config.js.`,
      );
    }
    throw error;
  }
  if (!response.ok) {
    throw new ApiError(
      "Could not establish a secure connection to POSTiT. Check the backend and API address.",
      { status: response.status },
    );
  }
  const payload = await response.json();
  return payload.csrfToken;
}

export async function request(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const headers = new Headers(options.headers || {});
  headers.set("Accept", "application/json");
  let body = options.body;

  if (body !== undefined && !(body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(body);
  }

  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    headers.set("X-CSRFToken", await csrfToken());
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      method,
      headers,
      body,
      credentials: "include",
    });
  } catch (error) {
    if (error instanceof TypeError) {
      throw new ApiError(
        `POSTiT could not reach the backend at ${API_ORIGIN}. Start Django and check the API address in js/config.js.`,
      );
    }
    throw error;
  }

  if (response.status === 204) return null;
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    throw new ApiError(detailFrom(data, response.status), {
      status: response.status,
      data,
    });
  }
  return data;
}

export function withQuery(path, params = {}) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && String(value).trim() !== "") {
      query.set(key, String(value).trim());
    }
  }
  const suffix = query.toString();
  return suffix ? `${path}?${suffix}` : path;
}

export function getResults(data) {
  if (Array.isArray(data)) return data;
  return Array.isArray(data?.results) ? data.results : [];
}

export function getNextPage(data) {
  if (!data?.next) return null;
  try {
    return new URL(data.next).searchParams.get("page");
  } catch {
    return null;
  }
}