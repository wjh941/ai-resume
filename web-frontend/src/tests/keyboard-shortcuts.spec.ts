import { describe, expect, it, vi } from "vitest"

import {
  runPendingGuardedAction,
  resolveApplicationsCloseAction,
  resolveResumeEditorShortcutAction,
  resolveWorkspaceShortcut,
} from "../lib/keyboard-shortcuts"

const key = (overrides: Partial<KeyboardEvent>) => ({
  key: "",
  ctrlKey: false,
  metaKey: false,
  altKey: false,
  shiftKey: false,
  isComposing: false,
  repeat: false,
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

  it("requires exact modifiers for every command", () => {
    expect(resolveWorkspaceShortcut(key({ key: "s", ctrlKey: true, shiftKey: true }))).toBeNull()
    expect(resolveWorkspaceShortcut(key({ key: "s", ctrlKey: true, altKey: true }))).toBeNull()
    expect(resolveWorkspaceShortcut(key({ key: "s", ctrlKey: true, metaKey: true }))).toBeNull()
    expect(resolveWorkspaceShortcut(key({ key: "ArrowLeft", altKey: true, shiftKey: true }))).toBeNull()
    expect(resolveWorkspaceShortcut(key({ key: "ArrowLeft", altKey: true, ctrlKey: true }))).toBeNull()
    expect(resolveWorkspaceShortcut(key({ key: "Escape", shiftKey: true }))).toBeNull()
    expect(resolveWorkspaceShortcut(key({ key: "Escape", metaKey: true }))).toBeNull()
  })

  it("ignores repeated keydown events", () => {
    expect(resolveWorkspaceShortcut(key({ key: "s", ctrlKey: true, repeat: true }))).toBeNull()
    expect(resolveWorkspaceShortcut(key({ key: "ArrowLeft", altKey: true, repeat: true }))).toBeNull()
    expect(resolveWorkspaceShortcut(key({ key: "Escape", repeat: true }))).toBeNull()
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

  it("routes visible and keyboard cancel actions through the same pending guard", () => {
    const cancel = vi.fn()

    expect(runPendingGuardedAction(true, cancel)).toBe(false)
    expect(cancel).not.toHaveBeenCalled()
    expect(runPendingGuardedAction(false, cancel)).toBe(true)
    expect(cancel).toHaveBeenCalledTimes(1)
    expect(resolveResumeEditorShortcutAction("back", true)).toBe("ignore")
    expect(resolveApplicationsCloseAction("close", true, true, false)).toBeNull()
  })
})
