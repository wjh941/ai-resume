// @vitest-environment jsdom

import { mount } from "@vue/test-utils"
import { describe, expect, it, vi } from "vitest"

import LoginPanel from "../components/LoginPanel.vue"
import { CAPABILITIES_KEY, createCapabilityContext } from "../lib/capabilities"

vi.mock("../lib/auth", () => ({
  loginWithPassword: vi.fn(),
  loginWithPhone: vi.fn(),
  registerAccount: vi.fn(),
}))

vi.mock("../lib/api", () => ({
  requestApi: vi.fn(),
}))

describe("component runtime", () => {
  it("mounts LoginPanel with a capability context and renders the password input", () => {
    const context = createCapabilityContext()
    const wrapper = mount(LoginPanel, {
      global: {
        provide: {
          [CAPABILITIES_KEY]: context,
        },
        stubs: {
          AsyncButton: { template: "<button><slot /></button>" },
          ErrorNotice: { template: "<p><slot /></p>" },
        },
      },
    })

    expect(wrapper.find('input[type="password"]').exists()).toBe(true)
  })
})
