import { beforeEach, describe, expect, it, vi } from "vitest"

import { requestApi } from "../lib/api"
import { compareRoles, loadCareerRecommendations } from "../lib/career"
import { getAssessmentQuestions, submitAssessment } from "../lib/assessment"
import { listEvidence, saveEvidence } from "../lib/evidence"
import { listDrafts } from "../lib/drafts"
import { createMembershipOrder } from "../lib/membership"
import { saveApplication } from "../lib/applications"

vi.mock("../lib/api", () => ({
  requestApi: vi.fn(),
}))

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
