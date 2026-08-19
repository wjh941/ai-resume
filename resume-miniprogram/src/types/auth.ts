export type AuthUser = {
  userId: string
  phone: string
}

export type PhoneCodeResult = {
  phone: string
  demoCode?: string
  message: string
}
