export type WorkspaceShortcut = "save" | "back" | "close"
export type ResumeEditorShortcutAction = "save" | "back" | "ignore"
export type ApplicationsCloseAction = "reset" | "collapse"

export function resolveWorkspaceShortcut(event: KeyboardEvent): WorkspaceShortcut | null {
  if (event.isComposing || event.repeat) return null
  if (event.ctrlKey !== event.metaKey && !event.altKey && !event.shiftKey && event.key.toLowerCase() === "s") return "save"
  if (event.altKey && !event.ctrlKey && !event.metaKey && !event.shiftKey && event.key === "ArrowLeft") return "back"
  if (!event.ctrlKey && !event.metaKey && !event.altKey && !event.shiftKey && event.key === "Escape") return "close"
  return null
}

export function resolveResumeEditorShortcutAction(
  shortcut: WorkspaceShortcut | null,
  saving: boolean,
): ResumeEditorShortcutAction | null {
  if (shortcut !== "save" && shortcut !== "back") return null
  if (saving) return "ignore"
  return shortcut
}

export function resolveApplicationsCloseAction(
  shortcut: WorkspaceShortcut | null,
  pending: boolean,
  editing: boolean,
  timelineOpen: boolean,
): ApplicationsCloseAction | null {
  if (shortcut !== "close" || pending) return null
  if (editing) return "reset"
  return timelineOpen ? "collapse" : null
}
