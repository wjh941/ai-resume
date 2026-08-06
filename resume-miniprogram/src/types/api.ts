export interface ApiEnvelope<T> {
  code: "ok" | string
  data: T
  message: string
}

export interface ApiError {
  code: string
  message: string
}
