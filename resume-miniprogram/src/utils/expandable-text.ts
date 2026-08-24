export function isExpandableText(text: string, expandAt: number): boolean {
  return text.trim().length > expandAt
}
