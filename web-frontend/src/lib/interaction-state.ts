export function canStartInteraction(loading: boolean): boolean {
  return !loading
}

export function pendingLabel(loading: boolean, idle: string, active: string): string {
  return loading ? active : idle
}
