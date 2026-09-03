import { describe, expect, it } from "vitest"

import { clearWorkspaceSnapshot, readWorkspaceSnapshot, writeWorkspaceSnapshot } from "../lib/workspace-recovery"

class MemoryStorage implements Storage {
  private values = new Map<string, string>()
  get length(): number { return this.values.size }
  clear(): void { this.values.clear() }
  getItem(key: string): string | null { return this.values.get(key) ?? null }
  key(index: number): string | null { return [...this.values.keys()][index] ?? null }
  removeItem(key: string): void { this.values.delete(key) }
  setItem(key: string, value: string): void { this.values.set(key, value) }
}

describe("workspace recovery", () => {
  it("round-trips snapshots under a user-scoped feature key", () => {
    const storage = new MemoryStorage()
    writeWorkspaceSnapshot(storage, "user-a", "assessment", { q1: 4 })

    expect(readWorkspaceSnapshot(storage, "user-a", "assessment")).toEqual({ q1: 4 })
    expect(readWorkspaceSnapshot(storage, "user-b", "assessment")).toBeNull()
  })

  it("clears only the requested user and feature snapshot", () => {
    const storage = new MemoryStorage()
    writeWorkspaceSnapshot(storage, "user-a", "assessment", { q1: 4 })
    writeWorkspaceSnapshot(storage, "user-a", "comparison", ["Analyst", "Designer"])

    clearWorkspaceSnapshot(storage, "user-a", "assessment")

    expect(readWorkspaceSnapshot(storage, "user-a", "assessment")).toBeNull()
    expect(readWorkspaceSnapshot(storage, "user-a", "comparison")).toEqual(["Analyst", "Designer"])
  })

  it("degrades to null and no-op for malformed or unavailable storage", () => {
    const malformed = new MemoryStorage()
    malformed.setItem("workspace-recovery:user-a:assessment", "{")
    const unavailable = {
      getItem: () => { throw new Error("blocked") },
      setItem: () => { throw new Error("blocked") },
      removeItem: () => { throw new Error("blocked") },
    } as unknown as Storage

    expect(readWorkspaceSnapshot(malformed, "user-a", "assessment")).toBeNull()
    expect(() => writeWorkspaceSnapshot(unavailable, "user-a", "assessment", {})).not.toThrow()
    expect(() => clearWorkspaceSnapshot(unavailable, "user-a", "assessment")).not.toThrow()
    expect(readWorkspaceSnapshot(unavailable, "user-a", "assessment")).toBeNull()
  })
})
