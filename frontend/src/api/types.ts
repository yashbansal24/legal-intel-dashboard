export type Dashboard = {
  agreement_types: Record<string, number>
  jurisdictions: Record<string, number>
  industries: Record<string, number>
  geographies: Record<string, number>
  count_documents: number
}

export type QueryResult = {
  columns: string[]
  rows: Record<string, string | number | null>[]
}

export type DocHit = {
  document: string
  governing_law?: string | null
}
