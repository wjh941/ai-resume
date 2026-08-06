export function previewContact(value: string, fallback: string): string {
  return value.trim() || fallback
}

export function meaningfulEntries<T extends Record<string, string>>(entries: T[]): T[] {
  return entries.filter((entry) => Object.values(entry).some((value) => value.trim()))
}
