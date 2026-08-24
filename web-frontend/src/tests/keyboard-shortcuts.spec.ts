import { describe, expect, it } from "vitest"

import {
  resolveApplicationsCloseAction,
  resolveResumeEditorShortcutAction,
  resolveWorkspaceShortcut,
} from "../lib/keyboard-shortcuts"

const key = (overrides: Partial<KeyboardEvent>) => ({
  key: "",
  ctrlKey: false,
  metaKey: false,
  altKey: false,
  isComposing: false,
  ...overrides,
}) as KeyboardEvent

describe("resolveWorkspaceShortcut", () => {
  it("maps save, back, and close commands", () => {
    expect(resolveWorkspaceShortcut(key({ key: "s", ctrlKey: true }))).toBe("save")
    expect(resolveWorkspaceShortcut(key({ key: "S", metaKey: true }))).toBe("save")
    expect(resolveWorkspaceShortcut(key({ key: "ArrowLeft", altKey: true }))).toBe("back")
    expect(resolveWorkspaceShortcut(key({ key: "Escape" }))).toBe("close")
  })

  it("ignores IME composition and unrelated keys", () => {
    expect(resolveWorkspaceShortcut(key({ key: "s", ctrlKey: true, isComposing: true }))).toBeNull()
    expect(resolveWorkspaceShortcut(key({ key: "s" }))).toBeNull()
  })

  it("keeps resume save and back inert while a save is pending", () => {
    expect(resolveResumeEditorShortcutAction("save", false)).toBe("save")
    expect(resolveResumeEditorShortcutAction("back", false)).toBe("back")
    expect(resolveResumeEditorShortcutAction("save", true)).toBe("ignore")
    expect(resolveResumeEditorShortcutAction("back", true)).toBe("ignore")
    expect(resolveResumeEditorShortcutAction("close", false)).toBeNull()
  })

  it("closes editing before an open timeline and stays inert while pending", () => {
    expect(resolveApplicationsCloseAction("close", false, true, true)).toBe("reset")
    expect(resolveApplicationsCloseAction("close", false, false, true)).toBe("collapse")
    expect(resolveApplicationsCloseAction("close", false, false, false)).toBeNull()
    expect(resolveApplicationsCloseAction("close", true, true, true)).toBeNull()
    expect(resolveApplicationsCloseAction("save", false, true, true)).toBeNull()
  })
})
