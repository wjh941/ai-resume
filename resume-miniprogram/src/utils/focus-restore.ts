type Focusable = { isConnected?: boolean; focus?: () => void }
type DocumentLike = { activeElement?: Focusable | null }

export function captureFocusRestore(documentLike?: DocumentLike): () => void {
  const active = documentLike?.activeElement
  return () => {
    if (!active || active.isConnected === false) return
    active.focus?.()
  }
}
