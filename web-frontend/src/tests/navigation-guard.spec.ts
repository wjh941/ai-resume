import { describe, expect, it, vi } from "vitest"

import { createNavigationGuardContext } from "../lib/navigation-guard"

describe("navigation guard context", () => {
  it("allows navigation before a guard is registered", () => {
    expect(createNavigationGuardContext().canNavigate()).toBe(true)
  })

  it("blocks or allows navigation from the active guard result", () => {
    const context = createNavigationGuardContext()

    context.register(() => false)
    expect(context.canNavigate()).toBe(false)

    context.register(() => true)
    expect(context.canNavigate()).toBe(true)
  })

  it("replaces the previous guard and makes unregister idempotent", () => {
    const context = createNavigationGuardContext()
    const previous = vi.fn(() => false)
    const unregister = context.register(previous)

    context.register(() => true)
    expect(context.canNavigate()).toBe(true)
    unregister()
    unregister()
    expect(context.canNavigate()).toBe(true)
    expect(previous).not.toHaveBeenCalled()
  })

  it("does not let an older unregister clear a replacement guard", () => {
    const context = createNavigationGuardContext()
    const unregisterPrevious = context.register(() => false)

    context.register(() => false)
    unregisterPrevious()

    expect(context.canNavigate()).toBe(false)
  })

  it("allows navigation after unregistering the active guard", () => {
    const context = createNavigationGuardContext()
    const unregister = context.register(() => false)

    unregister()

    expect(context.canNavigate()).toBe(true)
  })
})
