import type { ApplicationRecord, ApplicationTimelineEvent } from "./applications"

export function replaceApplication(items: ApplicationRecord[], updated: ApplicationRecord): ApplicationRecord[] {
  return items.map((item) => item.id === updated.id ? updated : item)
}

export function removeApplication(items: ApplicationRecord[], id: string): ApplicationRecord[] {
  return items.filter((item) => item.id !== id)
}

export function appendTimelineEvent(item: ApplicationRecord, event: ApplicationTimelineEvent): ApplicationRecord {
  return { ...item, timeline: [...item.timeline, event] }
}
