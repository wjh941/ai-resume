export function showErrorToast(title: string): void {
  uni.showToast({ title, icon: "none", duration: 2600, mask: false })
}
