export type AuthUser = {
  userId: string
  phone: string
  role: "user" | "operator"
}

export type PhoneCodeResult = {
  phone: string
  demoCode?: string
  message: string
}
