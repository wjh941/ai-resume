export type ThemePreference = "dark" | "light"

const THEME_STORAGE_KEY = "resume-web-theme"

export function readStoredTheme(): ThemePreference | null {
  try {
    const value = window.localStorage.getItem(THEME_STORAGE_KEY)
    return value === "dark" || value === "light" ? value : null
  } catch {
    // 隐私模式等 localStorage 不可用场景：退回跟随系统。
    return null
  }
}

export function storeTheme(preference: ThemePreference): void {
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, preference)
  } catch {
    // 写入失败不阻断界面，本次会话仍保持当前选择。
  }
}

function systemPrefersDark(): boolean {
  return typeof window.matchMedia === "function" && window.matchMedia("(prefers-color-scheme: dark)").matches
}

/** 初始主题：优先用户上次选择；未存储过则跟随系统。返回值对应 dark 布尔。 */
export function resolveInitialDarkTheme(): boolean {
  const stored = readStoredTheme()
  if (stored) return stored === "dark"
  return systemPrefersDark()
}

/** 未显式选择过主题时跟随系统变化；返回取消监听函数。 */
export function watchSystemTheme(onChange: (prefersDark: boolean) => void): () => void {
  if (typeof window.matchMedia !== "function") return () => {}
  const media = window.matchMedia("(prefers-color-scheme: dark)")
  const listener = (event: MediaQueryListEvent): void => onChange(event.matches)
  if (typeof media.addEventListener === "function") {
    media.addEventListener("change", listener)
    return () => media.removeEventListener("change", listener)
  }
  if (typeof media.addListener === "function") {
    media.addListener(listener)
    return () => media.removeListener(listener)
  }
  return () => {}
}
