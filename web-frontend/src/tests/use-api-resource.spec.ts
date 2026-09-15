// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils"
import { defineComponent, h } from "vue"
import { describe, expect, it, vi } from "vitest"

import { useApiResource, type UseApiResourceOptions, type UseApiResourceReturn } from "../composables/useApiResource"
import { ApiRequestError } from "../lib/api"

function mountResource<T>(loader: () => Promise<T>, options: UseApiResourceOptions = {}) {
  let resource!: UseApiResourceReturn<T>
  const Host = defineComponent({
    setup() {
      resource = useApiResource<T>(loader, options)
      return () => h("div", JSON.stringify(resource.data.value))
    },
  })
  const wrapper = mount(Host)
  return { wrapper, resource }
}

describe("useApiResource", () => {
  it("成功时写入 data 并复位 loading/error", async () => {
    const { resource } = mountResource(async () => "payload")
    expect(resource.loading.value).toBe(false)

    const done = resource.run()
    expect(resource.loading.value).toBe(true)
    expect(resource.error.value).toBeNull()

    await done
    expect(resource.data.value).toBe("payload")
    expect(resource.loading.value).toBe(false)
    expect(resource.error.value).toBeNull()
  })

  it("失败时写入兜底文案并进入可重试状态", async () => {
    const { resource } = mountResource(() => Promise.reject(new Error("boom")), { fallbackMessage: "暂时无法读取，请稍后重试" })

    await resource.run()

    expect(resource.data.value).toBeNull()
    expect(resource.error.value).toBe("暂时无法读取，请稍后重试")
    expect(resource.loading.value).toBe(false)
    expect(resource.retryable.value).toBe(true)
  })

  it("失败映射复用共享的 getApiErrorMessage（401 等可归类错误优先于兜底文案）", async () => {
    const { resource } = mountResource(() => Promise.reject(new ApiRequestError("expired", 401)), { fallbackMessage: "不应使用兜底文案" })

    await resource.run()

    expect(resource.error.value).toBe("登录已过期，请重新登录后继续")
  })

  it("requestId 守卫：过期的慢响应不会覆盖最新一次请求的结果", async () => {
    let resolveSlow!: (value: string) => void
    const loader = vi.fn()
      .mockImplementationOnce(() => new Promise<string>((resolve) => { resolveSlow = resolve }))
      .mockImplementationOnce(async () => "fast-latest")
    const { resource } = mountResource(loader)

    const stale = resource.run()
    await flushPromises()
    await resource.run()
    await flushPromises()
    expect(resource.data.value).toBe("fast-latest")

    resolveSlow("stale-slow")
    await stale
    await flushPromises()

    expect(resource.data.value).toBe("fast-latest")
    expect(resource.loading.value).toBe(false)
    expect(resource.error.value).toBeNull()
  })

  it("requestId 守卫：过期的慢失败不会写入最新一次请求的错误状态", async () => {
    let rejectSlow!: (reason: Error) => void
    const loader = vi.fn()
      .mockImplementationOnce(() => new Promise<string>((_, reject) => { rejectSlow = reject }))
      .mockImplementationOnce(async () => "latest")
    const { resource } = mountResource(loader, { fallbackMessage: "兜底文案" })

    const stale = resource.run()
    await resource.run()
    await flushPromises()

    rejectSlow(new Error("stale failure"))
    await stale
    await flushPromises()

    expect(resource.data.value).toBe("latest")
    expect(resource.error.value).toBeNull()
    expect(resource.retryable.value).toBe(false)
  })

  it("组件卸载后不再写入 data/loading 状态", async () => {
    let resolve!: (value: string) => void
    const loader = () => new Promise<string>((done) => { resolve = done })
    const { wrapper, resource } = mountResource(loader)

    const pending = resource.run()
    expect(resource.loading.value).toBe(true)
    wrapper.unmount()

    resolve("late-response")
    await pending
    await flushPromises()

    expect(resource.data.value).toBeNull()
    expect(resource.loading.value).toBe(true)
    expect(resource.error.value).toBeNull()
  })

  it("组件卸载后失败的请求也不会写入 error", async () => {
    let reject!: (reason: Error) => void
    const loader = () => new Promise<string>((_, fail) => { reject = fail })
    const { wrapper, resource } = mountResource(loader, { fallbackMessage: "兜底文案" })

    const pending = resource.run()
    wrapper.unmount()

    reject(new Error("boom"))
    await pending
    await flushPromises()

    expect(resource.error.value).toBeNull()
    expect(resource.retryable.value).toBe(false)
  })

  it("retry 复用 run：仅在最近一次失败后重新调用同一 loader", async () => {
    const loader = vi.fn()
      .mockImplementationOnce(async () => { throw new Error("boom") })
      .mockImplementationOnce(async () => "recovered")
    const { resource } = mountResource(loader, { fallbackMessage: "兜底文案" })

    await resource.run()
    expect(resource.error.value).toBe("兜底文案")
    expect(resource.retryable.value).toBe(true)

    await resource.retry()
    expect(loader).toHaveBeenCalledTimes(2)
    expect(resource.data.value).toBe("recovered")
    expect(resource.error.value).toBeNull()
    expect(resource.retryable.value).toBe(false)
  })

  it("没有可重试失败时 retry 是 no-op", async () => {
    const loader = vi.fn(async () => "ok")
    const { resource } = mountResource(loader)

    await resource.run()
    await resource.retry()

    expect(loader).toHaveBeenCalledTimes(1)
    expect(resource.data.value).toBe("ok")
  })

  it("clearRetry 清除可重试状态，retry 随之变为 no-op", async () => {
    const loader = vi.fn()
      .mockImplementationOnce(async () => { throw new Error("boom") })
      .mockImplementationOnce(async () => "second")
    const { resource } = mountResource(loader, { fallbackMessage: "兜底文案" })

    await resource.run()
    expect(resource.retryable.value).toBe(true)

    resource.clearRetry()
    await resource.retry()
    expect(loader).toHaveBeenCalledTimes(1)
    expect(resource.data.value).toBeNull()
  })

  it("immediate 时初始即为 loading 并在挂载后自动加载", async () => {
    const loader = vi.fn(async () => "boot")
    const { resource } = mountResource(loader, { immediate: true })

    expect(loader).toHaveBeenCalledTimes(1)
    expect(resource.loading.value).toBe(true)

    await flushPromises()
    expect(resource.data.value).toBe("boot")
    expect(resource.loading.value).toBe(false)
  })
})
