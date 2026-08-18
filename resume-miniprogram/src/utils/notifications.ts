type ToastOptions = { title: string; icon?: "success" | "none" }

type UniNotificationApi = {
  showToast?: (options: ToastOptions) => void
  showLoading?: (options: { title: string; mask?: boolean }) => void
  hideLoading?: () => void
}

function uniApi(): UniNotificationApi {
  return (globalThis as typeof globalThis & { uni?: UniNotificationApi }).uni ?? {}
}

function toast(title: string, icon: "success" | "none") {
  uniApi().showToast?.({ title, icon })
}

export const notify = {
  success(title: string) {
    toast(title, "success")
  },
  error(title: string) {
    toast(title, "none")
  },
  info(title: string) {
    toast(title, "none")
  },
  loading(title: string) {
    uniApi().showLoading?.({ title, mask: true })
  },
  clearLoading() {
    uniApi().hideLoading?.()
  },
}
