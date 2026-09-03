import type { InjectionKey } from "vue"

export type NavigationGuard = () => boolean

export interface NavigationGuardContext {
  register: (guard: NavigationGuard) => () => void
  canNavigate: () => boolean
}

export const NAVIGATION_GUARD_KEY: InjectionKey<NavigationGuardContext> = Symbol("navigation-guard")

export function createNavigationGuardContext(): NavigationGuardContext {
  let active: { guard: NavigationGuard } | null = null

  return {
    register(guard) {
      const registration = { guard }
      active = registration
      let registered = true

      return () => {
        if (!registered) return
        registered = false
        if (active === registration) active = null
      }
    },
    canNavigate() {
      return active?.guard() ?? true
    },
  }
}
