import { apiUrl } from "../services/http"

type DownloadFileOptions = {
  url: string
  success: (result: { tempFilePath: string; statusCode?: number }) => void
  fail: (reason: unknown) => void
}

type SaveFileOptions = {
  tempFilePath: string
  success: (result: unknown) => void
  fail: (reason: unknown) => void
}

type UniDownloadApi = {
  downloadFile?: (options: DownloadFileOptions) => void
  saveFile?: (options: SaveFileOptions) => void
  setClipboardData?: (options: { data: string }) => void
  showToast?: (options: { title: string; icon?: string }) => void
}

function uniApi(): UniDownloadApi {
  return (globalThis as typeof globalThis & { uni?: UniDownloadApi }).uni ?? {}
}

function showFallback(url: string): void {
  const uni = uniApi()
  uni.setClipboardData?.({ data: url })
  uni.showToast?.({ title: `下载链接已复制，请在浏览器打开：${url}`, icon: "none" })
}

export function appendFilename(downloadUrl: string, filename: string): string {
  const hashIndex = downloadUrl.indexOf("#")
  const hash = hashIndex >= 0 ? downloadUrl.slice(hashIndex) : ""
  const withoutHash = hashIndex >= 0 ? downloadUrl.slice(0, hashIndex) : downloadUrl
  const separator = withoutHash.includes("?") ? (withoutHash.endsWith("?") || withoutHash.endsWith("&") ? "" : "&") : "?"
  return `${withoutHash}${separator}filename=${encodeURIComponent(filename)}${hash}`
}

function downloadToMiniProgram(url: string): Promise<void> {
  const uni = uniApi()
  if (!uni.downloadFile || !uni.saveFile) return Promise.reject(new Error("当前运行环境不支持文件下载"))
  return new Promise((resolve, reject) => {
    uni.downloadFile!({
      url,
      success: ({ tempFilePath, statusCode }) => {
        if (statusCode !== undefined && (statusCode < 200 || statusCode > 299)) {
          reject(new Error(`下载请求失败：${statusCode}`))
          return
        }
        uni.saveFile!({ tempFilePath, success: () => resolve(), fail: reject })
      },
      fail: reject,
    })
  })
}

export async function downloadExport(
  downloadUrl: string,
  filename: string,
  platform: "h5" | "mp-weixin",
): Promise<void> {
  const url = appendFilename(apiUrl(downloadUrl), filename)
  if (platform === "h5") {
    const browser = (globalThis as typeof globalThis & { window?: { open?: (url: string, target?: string) => void } }).window
    if (browser?.open) browser.open(url, "_blank")
    else showFallback(url)
    return
  }
  try {
    await downloadToMiniProgram(url)
    uniApi().showToast?.({ title: "文件已保存", icon: "success" })
  } catch {
    showFallback(url)
  }
}
