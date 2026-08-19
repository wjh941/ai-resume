type FileSystemManager = {
  writeFile(options: {
    filePath: string
    data: string
    encoding: "utf8"
    success: () => void
    fail: (reason: unknown) => void
  }): void
  readFile(options: {
    filePath: string
    encoding: "utf8"
    success: (result: { data?: string }) => void
    fail: (reason: unknown) => void
  }): void
}

type FileChoice = { tempFiles?: Array<{ path?: string }> }
type BackupFileUni = {
  env?: { USER_DATA_PATH?: string }
  getFileSystemManager?: () => FileSystemManager
  chooseFile?: (options: {
    count: number
    type: "file"
    extension: string[]
    success: (result: FileChoice) => void
    fail: (reason: unknown) => void
  }) => void
}

function getUni(): BackupFileUni | undefined {
  return (globalThis as typeof globalThis & { uni?: BackupFileUni }).uni
}

function backupFilename(): string {
  return `resume-career-backup-${new Date().toISOString().slice(0, 10)}.json`
}

export async function exportLocalBackupFile(content: string): Promise<void> {
  if (typeof document !== "undefined" && typeof URL !== "undefined") {
    const file = new Blob([content], { type: "application/json;charset=utf-8" })
    const url = URL.createObjectURL(file)
    const link = document.createElement("a")
    link.href = url
    link.download = backupFilename()
    link.style.display = "none"
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
    return
  }

  const platform = getUni()
  const manager = platform?.getFileSystemManager?.()
  const path = platform?.env?.USER_DATA_PATH
  if (!manager || !path) throw new Error("Local backup export is not available in this environment.")
  await new Promise<void>((resolve, reject) => {
    manager.writeFile({
      filePath: `${path}/${backupFilename()}`,
      data: content,
      encoding: "utf8",
      success: resolve,
      fail: reject,
    })
  })
}

export async function importLocalBackupFile(): Promise<string> {
  if (typeof document !== "undefined") {
    return new Promise<string>((resolve, reject) => {
      const input = document.createElement("input")
      input.type = "file"
      input.accept = "application/json,.json"
      input.onchange = async () => {
        const file = input.files?.[0]
        if (!file) return reject(new Error("No backup file was selected."))
        try {
          resolve(await file.text())
        } catch (reason) {
          reject(reason)
        }
      }
      input.click()
    })
  }

  const platform = getUni()
  const manager = platform?.getFileSystemManager?.()
  if (!platform?.chooseFile || !manager) throw new Error("Local backup import is not available in this environment.")
  const choice = await new Promise<FileChoice>((resolve, reject) => {
    platform.chooseFile?.({ count: 1, type: "file", extension: ["json"], success: resolve, fail: reject })
  })
  const path = choice.tempFiles?.[0]?.path
  if (!path) throw new Error("No backup file was selected.")
  return new Promise<string>((resolve, reject) => {
    manager.readFile({
      filePath: path,
      encoding: "utf8",
      success: (result) => resolve(result.data ?? ""),
      fail: reject,
    })
  })
}
