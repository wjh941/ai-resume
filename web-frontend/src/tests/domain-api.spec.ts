import { beforeEach, describe, expect, it, vi } from "vitest"

import { ApiRequestError, requestApi } from "../lib/api"
import { compareRoles, listCareerTasks, loadCareerRecommendations } from "../lib/career"
import { getAssessmentQuestions, submitAssessment } from "../lib/assessment"
import { listEvidence, saveEvidence } from "../lib/evidence"
import { listDrafts } from "../lib/drafts"
import { createMembershipOrder, listMembershipPackages, listOrders } from "../lib/membership"
import { listApplications, listTimeline, saveApplication } from "../lib/applications"

vi.mock("../lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../lib/api")>()
  return { ...actual, requestApi: vi.fn() }
})

const requestMock = vi.mocked(requestApi)

beforeEach(() => {
  requestMock.mockReset()
})

describe("typed domain adapters", () => {
  it("maps draft list records to camelCase", async () => {
    requestMock.mockResolvedValue({
      items: [{
        id: "d-1",
        job_title: "Data Engineer",
        template_id: "technology",
        resume: { basic: { name: "A" } },
        job_intelligence: null,
        created_at: "2026-08-24T00:00:00Z",
        updated_at: "2026-08-24T01:00:00Z",
      }],
    })

    const drafts = await listDrafts()

    expect(drafts[0]).toMatchObject({
      id: "d-1",
      jobTitle: "Data Engineer",
      templateId: "technology",
      jobIntelligence: null,
      updatedAt: "2026-08-24T01:00:00Z",
    })
    expect(requestMock).toHaveBeenCalledWith("/api/draft/list")
  })

  it("maps a backend draft list returned directly as an array", async () => {
    requestMock.mockResolvedValue([
      {
        id: "d-2",
        job_title: "Product Designer",
        template_id: "technology",
        resume: { basic: { name: "B" } },
        job_intelligence: null,
        created_at: "2026-08-24T00:00:00Z",
        updated_at: "2026-08-24T01:00:00Z",
      },
    ])

    const drafts = await listDrafts()

    expect(drafts).toHaveLength(1)
    expect(drafts[0]).toMatchObject({ id: "d-2", jobTitle: "Product Designer" })
  })

  it("posts an application with the existing backend field names", async () => {
    requestMock.mockResolvedValue({ id: "a-1", role_name: "Product Ops", company: "Acme", status: "saved" })

    await saveApplication({
      id: "a-1",
      company: "Acme",
      roleName: "Product Ops",
      city: "Shanghai",
      source: "official",
      status: "saved",
      appliedAt: null,
      nextActionAt: null,
      interviewNotes: "",
      draftId: null,
      notes: "",
      contactInfo: "",
      attachmentRef: "",
      nextInterviewAt: null,
    })

    expect(requestMock).toHaveBeenCalledWith("/api/applications", expect.objectContaining({
      method: "POST",
      body: expect.stringContaining('"role_name":"Product Ops"'),
    }))
  })

  it("maps and saves evidence", async () => {
    requestMock.mockResolvedValue({
      id: "e-1",
      client_id: "u-1",
      kind: "project",
      title: "Launch",
      context: "",
      actions: "Built",
      outcome: "",
      proof_note: "",
      verified: true,
      created_at: "t1",
      updated_at: "t2",
    })

    const evidence = await saveEvidence({
      kind: "project",
      title: "Launch",
      context: "",
      actions: "Built",
      outcome: "",
      proofNote: "",
      verified: true,
    })

    expect(evidence).toMatchObject({ id: "e-1", clientId: "u-1", proofNote: "", verified: true })
    expect(requestMock).toHaveBeenCalledWith("/api/evidence", expect.objectContaining({
      method: "POST",
      body: expect.stringContaining('"proof_note":""'),
    }))
  })

  it("maps evidence list envelopes", async () => {
    requestMock.mockResolvedValue({
      items: [{
        id: "e-1",
        client_id: "u-1",
        kind: "project",
        title: "Launch",
        context: "",
        actions: "Built",
        outcome: "",
        proof_note: "",
        verified: true,
        created_at: "t1",
        updated_at: "t2",
      }],
    })

    const result = await listEvidence()
    expect(result[0]).toMatchObject({ id: "e-1", clientId: "u-1" })
  })

  it("maps evidence lists returned directly as an array", async () => {
    requestMock.mockResolvedValue([
      {
        id: "e-2",
        client_id: "u-2",
        kind: "project",
        title: "Direct",
        context: "",
        actions: "Built",
        outcome: "",
        proof_note: "",
        verified: false,
        created_at: "t1",
        updated_at: "t2",
      },
    ])

    const result = await listEvidence()
    expect(result).toHaveLength(1)
    expect(result[0]).toMatchObject({ id: "e-2", clientId: "u-2" })
  })

  it("rejects malformed evidence list payloads with status zero", async () => {
    requestMock.mockResolvedValue({ items: "invalid" })

    await expect(listEvidence()).rejects.toMatchObject({
      name: "ApiRequestError",
      status: 0,
    } satisfies Partial<ApiRequestError>)
  })

  it("maps application and timeline lists returned directly as arrays", async () => {
    requestMock
      .mockResolvedValueOnce([{
        id: "a-1", company: "Acme", role_name: "Engineer", city: "Shanghai", source: "official",
        status: "saved", applied_at: null, next_action_at: null, interview_notes: "", draft_id: null,
        notes: "", created_at: "t1", updated_at: "t2",
      }])
      .mockResolvedValueOnce([{ id: "event-1", title: "Applied", description: "", occurred_at: "t1" }])

    const applications = await listApplications()
    const timeline = await listTimeline("a-1")

    expect(applications[0]).toMatchObject({ id: "a-1", roleName: "Engineer" })
    expect(timeline[0]).toMatchObject({ id: "event-1", occurredAt: "t1" })
  })

  it("maps career task lists returned directly as an array", async () => {
    requestMock.mockResolvedValue([{
      id: "task-1", plan_id: "plan-1", title: "Task", description: "", due_date: null,
      status: "pending", created_at: "t1", updated_at: "t2",
    }])

    const tasks = await listCareerTasks("plan-1")

    expect(tasks[0]).toMatchObject({ id: "task-1", planId: "plan-1" })
  })

  it("maps membership package and order lists returned directly as arrays", async () => {
    requestMock
      .mockResolvedValueOnce([{
        package_type: "monthly", name: "Monthly", vip_level: "plus", duration_days: 30,
        total_amount: 29, benefits: [],
      }])
      .mockResolvedValueOnce([{
        order_id: "order-1", package_type: "monthly", total_amount: 29, payment_status: "paid",
        payment_channel: "demo", create_time: "t1", entitlement_expire_time: null,
      }])

    const packages = await listMembershipPackages()
    const orders = await listOrders()

    expect(packages[0]).toMatchObject({ packageType: "monthly", durationDays: 30 })
    expect(orders[0]).toMatchObject({ orderId: "order-1", paymentStatus: "paid" })
  })

  it("creates membership orders with package and renewal fields", async () => {
    requestMock.mockResolvedValue({
      order_id: "o-1",
      package_type: "monthly",
      total_amount: 29,
      payment_status: "pending",
      payment_channel: null,
      create_time: "t1",
      entitlement_expire_time: null,
    })

    const order = await createMembershipOrder("monthly", true)

    expect(order).toMatchObject({ orderId: "o-1", paymentStatus: "pending" })
    expect(requestMock).toHaveBeenCalledWith("/api/pay/create-order", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ package_type: "monthly", auto_renew: true }),
    }))
  })

  it("maps assessment question responses and submits report mode", async () => {
    requestMock
      .mockResolvedValueOnce({ items: [{ key: "q1", group: "interest", dimension: "analysis", title: "Question" }], notice: "notice" })
      .mockResolvedValueOnce({ client_id: "u-1", version: 1, answers: { q1: 4 }, result: {}, updated_at: "t1" })

    const questions = await getAssessmentQuestions()
    await submitAssessment({ q1: 4 }, "professional")

    expect(questions.items[0].key).toBe("q1")
    expect(requestMock).toHaveBeenNthCalledWith(2, "/api/career/assessment/submit", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ answers: { q1: 4 }, report_mode: "professional" }),
    }))
  })

  it("loads recommendations and compares selected roles", async () => {
    requestMock.mockResolvedValueOnce({ tiers: { stable: [{ role: { roleName: "Data Engineer" } }] } })
    requestMock.mockResolvedValueOnce({ items: [{ role: { roleName: "Data Engineer" } }, { role: { roleName: "Analyst" } }] })

    const recommendations = await loadCareerRecommendations()
    const comparison = await compareRoles(["Data Engineer", "Analyst"])

    expect(recommendations.tiers.stable).toHaveLength(1)
    expect(comparison.items).toHaveLength(2)
    expect(requestMock).toHaveBeenNthCalledWith(2, "/api/career/compare", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ role_names: ["Data Engineer", "Analyst"] }),
    }))
  })

  it("propagates domain request failures", async () => {
    const failure = new Error("offline")
    requestMock.mockRejectedValue(failure)

    await expect(listEvidence()).rejects.toBe(failure)
  })
})
