import { beforeEach, describe, expect, it, vi } from "vitest"

import { ApiRequestError, requestApi } from "../lib/api"
import { compareRoles, listCareerTasks, loadCareerRecommendations } from "../lib/career"
import { getAssessmentQuestions, submitAssessment } from "../lib/assessment"
import { getEvidenceSuggestions, listEvidence, saveEvidence } from "../lib/evidence"
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

  it("maps application and timeline list envelopes to camelCase", async () => {
    requestMock
      .mockResolvedValueOnce({ items: [{
        id: "a-1", company: "Acme", role_name: "Engineer", city: "Shanghai", source: "official",
        status: "saved", applied_at: null, next_action_at: null, interview_notes: "", draft_id: null,
        notes: "", created_at: "t1", updated_at: "t2",
      }] })
      .mockResolvedValueOnce({ items: [{ id: "event-1", title: "Applied", description: "", occurred_at: "t1" }] })

    const applications = await listApplications()
    const timeline = await listTimeline("a-1")

    expect(applications[0]).toMatchObject({ id: "a-1", roleName: "Engineer" })
    expect(timeline[0]).toMatchObject({ id: "event-1", occurredAt: "t1" })
  })

  it("maps applications returned directly as an array", async () => {
    requestMock.mockResolvedValue([
      {
        id: "a-direct",
        company: "Acme",
        role_name: "Designer",
        city: "Shanghai",
        source: "official",
        status: "saved",
        applied_at: null,
        next_action_at: null,
        interview_notes: "",
        draft_id: null,
        notes: "",
        contact_info: "",
        attachment_ref: "",
        next_interview_at: null,
        timeline: [],
        created_at: "t1",
        updated_at: "t2",
      },
    ])

    const applications = await listApplications({ status: "saved" })

    expect(applications[0]).toMatchObject({ id: "a-direct", roleName: "Designer" })
    expect(requestMock).toHaveBeenCalledWith("/api/applications?status=saved")
  })

  it("maps timeline records returned directly as an array", async () => {
    requestMock.mockResolvedValue([
      { id: "event-direct", title: "Interview", description: "", occurred_at: "t1" },
    ])

    const timeline = await listTimeline("a-direct")

    expect(timeline[0]).toMatchObject({ id: "event-direct", occurredAt: "t1" })
    expect(requestMock).toHaveBeenCalledWith("/api/applications/a-direct/timeline")
  })

  it("maps career task list envelopes to camelCase", async () => {
    requestMock.mockResolvedValue({ items: [{
      id: "task-1", plan_id: "plan-1", title: "Task", description: "", due_date: null,
      status: "pending", created_at: "t1", updated_at: "t2",
    }] })

    const tasks = await listCareerTasks("plan-1")

    expect(tasks[0]).toMatchObject({ id: "task-1", planId: "plan-1" })
  })

  it("maps career tasks returned directly as an array", async () => {
    requestMock.mockResolvedValue([
      {
        id: "task-direct",
        plan_id: "plan-direct",
        title: "Task",
        description: "",
        due_date: "2026-09-01",
        status: "pending",
        created_at: "t1",
        updated_at: "t2",
      },
    ])

    const tasks = await listCareerTasks("plan-direct")

    expect(tasks[0]).toMatchObject({ id: "task-direct", planId: "plan-direct", dueDate: "2026-09-01" })
    expect(requestMock).toHaveBeenCalledWith("/api/career/tasks?plan_id=plan-direct")
  })

  it("maps membership package and order list envelopes to camelCase", async () => {
    requestMock
      .mockResolvedValueOnce({ items: [{
        package_type: "monthly", name: "Monthly", vip_level: "plus", duration_days: 30,
        total_amount: 29, benefits: [],
      }] })
      .mockResolvedValueOnce({ items: [{
        order_id: "order-1", package_type: "monthly", total_amount: 29, payment_status: "paid",
        payment_channel: "demo", create_time: "t1", entitlement_expire_time: null,
      }] })

    const packages = await listMembershipPackages()
    const orders = await listOrders()

    expect(packages[0]).toMatchObject({ packageType: "monthly", durationDays: 30 })
    expect(orders[0]).toMatchObject({ orderId: "order-1", paymentStatus: "paid" })
  })

  it("maps membership packages returned directly as an array", async () => {
    requestMock.mockResolvedValue([
      {
        package_type: "annual",
        name: "Annual",
        vip_level: "pro",
        duration_days: 365,
        total_amount: 299,
        benefits: ["priority"],
      },
    ])

    const packages = await listMembershipPackages()

    expect(packages[0]).toMatchObject({ packageType: "annual", durationDays: 365 })
    expect(requestMock).toHaveBeenCalledWith("/api/pay/package-list")
  })

  it("maps orders returned directly as an array", async () => {
    requestMock.mockResolvedValue([
      {
        order_id: "order-direct",
        package_type: "annual",
        total_amount: 299,
        payment_status: "paid",
        payment_channel: "demo",
        create_time: "t1",
        entitlement_expire_time: "t2",
      },
    ])

    const orders = await listOrders()

    expect(orders[0]).toMatchObject({ orderId: "order-direct", paymentStatus: "paid" })
    expect(requestMock).toHaveBeenCalledWith("/api/user/order-list")
  })

  it("maps evidence suggestion envelopes to camelCase", async () => {
    requestMock.mockResolvedValue({ items: [{
      source_evidence_id: "e-1",
      source_title: "Launch",
      target_section: "project",
      title: "Platform launch",
      role: "Lead",
      description: "Built the platform",
      risk_note: "Verify metrics",
    }] })

    const suggestions = await getEvidenceSuggestions("Data Engineer")

    expect(suggestions[0]).toMatchObject({
      sourceEvidenceId: "e-1",
      sourceTitle: "Launch",
      targetSection: "project",
      riskNote: "Verify metrics",
    })
    expect(requestMock).toHaveBeenCalledWith("/api/resume/evidence-suggestions", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ role_name: "Data Engineer" }),
    }))
  })

  it("maps evidence suggestions returned directly as an array", async () => {
    requestMock.mockResolvedValue([
      {
        source_evidence_id: "e-direct",
        source_title: "Launch",
        target_section: "employment",
        title: "Platform launch",
        role: "Lead",
        description: "Built the platform",
        risk_note: "Verify metrics",
      },
    ])

    const suggestions = await getEvidenceSuggestions("Data Engineer")

    expect(suggestions[0]).toMatchObject({
      sourceEvidenceId: "e-direct",
      sourceTitle: "Launch",
      targetSection: "employment",
      riskNote: "Verify metrics",
    })
    expect(requestMock).toHaveBeenCalledWith("/api/resume/evidence-suggestions", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ role_name: "Data Engineer" }),
    }))
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
