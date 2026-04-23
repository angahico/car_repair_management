export interface FieldMeta {
  fieldname: string
  label: string
  fieldtype: string
  required: boolean
  options?: string
  linkDoctype?: string
  defaultValue?: unknown
  inListView: boolean
}

export interface DoctypeMeta {
  name: string
  module: string
  titleField: string
  statusField?: string
  dateFields: string[]
  fields: FieldMeta[]
  childTables: { fieldname: string; doctype: string }[]
  isSubmittable: boolean
}

export interface DomainModel {
  doctype: string
  displayName: string
  idField: string
  titleField: string
  statusField?: string
  fieldMappings: Record<string, string>
}

export interface SchemaRegistry {
  doctypes: Record<string, DoctypeMeta>
  domains: Record<string, DomainModel>
  discoveredAt: string
}

export const CORE_DOCTYPES = [
  'Repair Order',
  'Service Template',
  'Job Costing',
  'Vehicle',
  'Customer',
  'Project',
  'Task',
  'Quotation',
  'Sales Invoice',
  'Material Request',
] as const

export type CoreDoctype = (typeof CORE_DOCTYPES)[number]
