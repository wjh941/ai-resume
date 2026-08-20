export type AuthUser = {
  userId: string
  phone: string
  role: "user" | "operator"
  account?: string
}

export type PhoneCodeResult = {
  phone: string
  demoCode?: string
  message: string
}
