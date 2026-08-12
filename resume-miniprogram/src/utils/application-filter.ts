import type { ApplicationRecord, ApplicationStatus } from "../types/application"

export const filterApplications = (
  items: ApplicationRecord[],
  status: "all" | ApplicationStatus,
): ApplicationRecord[] => status === "all"
  ? items
  : items.filter((item) => item.status === status)
