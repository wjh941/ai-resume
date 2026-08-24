export async function runWithLoading<T>(
  setLoading: (loading: boolean) => void,
  operation: () => Promise<T>,
): Promise<T> {
  setLoading(true)
  try {
    return await operation()
  } finally {
    setLoading(false)
  }
}
