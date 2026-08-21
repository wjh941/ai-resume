export type LocalJobMatchItem = {
  roleName: string
  company: string
  city: string
  salaryRange: string
  category: string
  matchScore: number
  matchScoreReference: number | null
  responsibilities: string[]
  requirements: string[]
}

export type LocalJobMatchResult = {
  items: LocalJobMatchItem[]
  sourceNotice: string
}
