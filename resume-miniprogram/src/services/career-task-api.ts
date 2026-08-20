import { request } from "./http"

export type CareerTaskStatus = "pending" | "completed"

export type CareerTask = {
  id: string
  planId: string
  title: string
  description: string
  dueDate: string | null
  status: CareerTaskStatus
  linkToApplicationId: string | null
  linkToEvidenceId: string | null
  createdAt: string
  updatedAt: string
}

export type CareerActionPlan = {
  sevenDay: string[]
  thirtyDay: string[]
  ninetyDay: string[]
}

type BackendCareerTask = {
  id: string
  plan_id: string
  title: string
  description: string
  due_date: string | null
  status: CareerTaskStatus
  link_to_application_id: string | null
  link_to_evidence_id: string | null
  created_at: string
  updated_at: string
}

const fromBackend = (item: BackendCareerTask): CareerTask => ({
  id: item.id,
  planId: item.plan_id,
  title: item.title,
  description: item.description,
  dueDate: item.due_date,
  status: item.status,
  linkToApplicationId: item.link_to_application_id,
  linkToEvidenceId: item.link_to_evidence_id,
  createdAt: item.created_at,
  updatedAt: item.updated_at,
})

export async function listCareerTasks(planId: string): Promise<CareerTask[]> {
  const data = await request<{ items: BackendCareerTask[] }>(
    `/api/career/tasks?plan_id=${encodeURIComponent(planId)}`,
  )
  return data.items.map(fromBackend)
}

export async function generateCareerTasks(planId: string, actionPlan: CareerActionPlan): Promise<CareerTask[]> {
  const data = await request<{ items: BackendCareerTask[] }>("/api/career/tasks/generate", "POST", {
    plan_id: planId,
    action_plan: {
      seven_day: actionPlan.sevenDay,
      thirty_day: actionPlan.thirtyDay,
      ninety_day: actionPlan.ninetyDay,
    },
  })
  return data.items.map(fromBackend)
}

export async function createCareerTask(input: Omit<CareerTask, "id" | "createdAt" | "updatedAt">): Promise<CareerTask> {
  return fromBackend(await request<BackendCareerTask>("/api/career/tasks", "POST", {
    plan_id: input.planId,
    title: input.title,
    description: input.description,
    due_date: input.dueDate,
    status: input.status,
    link_to_application_id: input.linkToApplicationId,
    link_to_evidence_id: input.linkToEvidenceId,
  }))
}

export async function updateCareerTask(
  taskId: string,
  input: Partial<Pick<CareerTask, "title" | "description" | "dueDate" | "status" | "linkToApplicationId" | "linkToEvidenceId">>,
): Promise<CareerTask> {
  return fromBackend(await request<BackendCareerTask>(
    `/api/career/tasks/${encodeURIComponent(taskId)}`,
    "PATCH",
    {
      title: input.title,
      description: input.description,
      due_date: input.dueDate,
      status: input.status,
      link_to_application_id: input.linkToApplicationId,
      link_to_evidence_id: input.linkToEvidenceId,
    },
  ))
}

export async function deleteCareerTask(taskId: string): Promise<void> {
  await request(`/api/career/tasks/${encodeURIComponent(taskId)}`, "DELETE")
}
