export function toggleComparisonRole(selected: string[], role: string, maxSelectable = 4): string[] {
  if (selected.includes(role)) return selected.filter((item) => item !== role)
  return selected.length < maxSelectable ? [...selected, role] : selected
}

export function canCompareRoles(selected: string[], minSelectable = 2, maxSelectable = 4): boolean {
  return selected.length >= minSelectable && selected.length <= maxSelectable && new Set(selected).size === selected.length
}
