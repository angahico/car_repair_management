export interface PaginationState {
  page: number
  pageSize: number
  total: number
}

export interface SortState {
  field: string
  direction: 'asc' | 'desc'
}

export interface FilterState {
  field: string
  operator: '=' | '!=' | 'like' | '>' | '<' | '>=' | '<=' | 'in' | 'not in'
  value: unknown
}

export interface ListViewState {
  pagination: PaginationState
  sort?: SortState
  filters: FilterState[]
  columns: string[]
}

export interface MenuItem {
  id: string
  label: string
  icon: string
  route?: string
  children?: MenuItem[]
  badge?: string | number
  hidden?: boolean
}

export interface BreadcrumbItem {
  label: string
  route?: string
}

export type StatusVariant = 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'info'

export interface StatusConfig {
  label: string
  variant: StatusVariant
}

export const REPAIR_ORDER_STATUSES: Record<string, StatusConfig> = {
  'Draft': { label: 'Draft', variant: 'default' },
  'Scheduled': { label: 'Scheduled', variant: 'info' },
  'In Progress': { label: 'In Progress', variant: 'primary' },
  'Awaiting Parts': { label: 'Awaiting Parts', variant: 'warning' },
  'Ready for Handover': { label: 'Ready', variant: 'success' },
  'Delivered': { label: 'Delivered', variant: 'success' },
  'Closed': { label: 'Closed', variant: 'default' },
  'On Hold': { label: 'On Hold', variant: 'warning' },
  'Cancelled': { label: 'Cancelled', variant: 'danger' },
}

export const PRIORITY_VARIANTS: Record<string, StatusVariant> = {
  'Low': 'default',
  'Normal': 'info',
  'High': 'warning',
  'Urgent': 'danger',
}
