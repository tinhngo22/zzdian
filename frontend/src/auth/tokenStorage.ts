// The only module that knows where the access token lives.
const KEY = "hanzi.access_token";

export function getToken(): string | null {
  try {
    return localStorage.getItem(KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string) {
  localStorage.setItem(KEY, token);
}

export function clearToken() {
  try {
    localStorage.removeItem(KEY);
  } catch {
    // storage unavailable: nothing to clear
  }
}
