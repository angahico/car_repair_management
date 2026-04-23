import { frappeRequest } from 'frappe-ui'
import type { DoctypeMeta, FieldMeta, SchemaRegistry, DomainModel } from './types'
import { CORE_DOCTYPES } from './types'

const FIELD_TYPE_PRIORITY = {
  title: ['title', 'subject', 'name', 'template_name', 'full_name', 'customer_name'],
  status: ['status', 'workflow_state', 'docstatus'],
  date: [
    'posting_date',
    'transaction_date',
    'creation',
    'modified',
    'due_date',
    'schedule_date',
    'sla_delivery_by',
  ],
}

export async function checkAuth(): Promise<string | null> {
  try {
    const res = await frappeRequest({
      url: '/api/method/frappe.auth.get_logged_user',
    })
    return res.message !== 'Guest' ? res.message : null
  } catch {
    return null
  }
}

async function fetchDoctypeMeta(doctype: string): Promise<DoctypeMeta | null> {
  try {
    // Use frappe.client.get_meta - the correct API for getting DocType metadata
    const res = await frappeRequest({
      url: '/api/method/frappe.client.get_meta',
      method: 'POST',
      body: { doctype },
    })
    const meta = res.message

    if (!meta) {
      console.warn(`No meta returned for ${doctype}, trying inference...`)
      return inferDoctypeFromList(doctype)
    }

    const fields: FieldMeta[] = (meta.fields || [])
      .filter((f: any) => !['Section Break', 'Column Break', 'Tab Break'].includes(f.fieldtype))
      .map((f: any) => ({
        fieldname: f.fieldname,
        label: f.label || f.fieldname,
        fieldtype: f.fieldtype,
        required: !!f.reqd,
        options: f.options,
        linkDoctype: f.fieldtype === 'Link' ? f.options : undefined,
        inListView: !!f.in_list_view,
        defaultValue: f.default,
      }))

    const childTables = (meta.fields || [])
      .filter((f: any) => f.fieldtype === 'Table')
      .map((f: any) => ({ fieldname: f.fieldname, doctype: f.options }))

    let titleField = 'name'
    if (meta.title_field) {
      titleField = meta.title_field
    } else {
      for (const candidate of FIELD_TYPE_PRIORITY.title) {
        if (fields.some((f) => f.fieldname === candidate)) {
          titleField = candidate
          break
        }
      }
    }

    let statusField: string | undefined
    for (const candidate of FIELD_TYPE_PRIORITY.status) {
      if (fields.some((f) => f.fieldname === candidate)) {
        statusField = candidate
        break
      }
    }

    const dateFields = fields
      .filter((f) => ['Date', 'Datetime'].includes(f.fieldtype))
      .map((f) => f.fieldname)

    return {
      name: doctype,
      module: meta.module || '',
      titleField,
      statusField,
      dateFields,
      fields,
      childTables,
      isSubmittable: !!meta.is_submittable,
    }
  } catch (e) {
    console.warn(`Cannot fetch DocType meta for ${doctype}, trying inference...`)
    return inferDoctypeFromList(doctype)
  }
}

async function inferDoctypeFromList(doctype: string): Promise<DoctypeMeta | null> {
  try {
    // Use GET to fetch a sample list of documents
    const res = await frappeRequest({
      url: `/api/resource/${encodeURIComponent(doctype)}`,
      method: 'GET',
      params: { limit_page_length: 5 },
    })

    if (!res.data || res.data.length === 0) {
      return null
    }

    const sample = res.data[0]
    const fieldNames = Object.keys(sample).filter((k) => !k.startsWith('_'))

    const fields: FieldMeta[] = fieldNames.map((fn) => ({
      fieldname: fn,
      label: fn.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
      fieldtype: inferFieldType(sample[fn], fn),
      required: false,
      inListView: true,
    }))

    let titleField = 'name'
    for (const candidate of FIELD_TYPE_PRIORITY.title) {
      if (fieldNames.includes(candidate)) {
        titleField = candidate
        break
      }
    }

    let statusField: string | undefined
    for (const candidate of FIELD_TYPE_PRIORITY.status) {
      if (fieldNames.includes(candidate)) {
        statusField = candidate
        break
      }
    }

    const dateFields = fields
      .filter((f) => ['Date', 'Datetime'].includes(f.fieldtype))
      .map((f) => f.fieldname)

    return {
      name: doctype,
      module: '',
      titleField,
      statusField,
      dateFields,
      fields,
      childTables: [],
      isSubmittable: false,
    }
  } catch {
    return null
  }
}

function inferFieldType(value: unknown, fieldname: string): string {
  if (value === null || value === undefined) {
    if (fieldname.includes('date')) return 'Date'
    if (fieldname.includes('amount') || fieldname.includes('cost') || fieldname.includes('price'))
      return 'Currency'
    return 'Data'
  }
  if (typeof value === 'number') {
    if (fieldname.includes('amount') || fieldname.includes('cost') || fieldname.includes('price'))
      return 'Currency'
    return Number.isInteger(value) ? 'Int' : 'Float'
  }
  if (typeof value === 'boolean') return 'Check'
  if (typeof value === 'string') {
    if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return 'Date'
    if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/.test(value)) return 'Datetime'
    return 'Data'
  }
  return 'Data'
}

function buildDomainModel(doctype: string, meta: DoctypeMeta): DomainModel {
  return {
    doctype,
    displayName: doctype,
    idField: 'name',
    titleField: meta.titleField,
    statusField: meta.statusField,
    fieldMappings: meta.fields.reduce(
      (acc, f) => {
        acc[f.fieldname] = f.fieldname
        return acc
      },
      {} as Record<string, string>
    ),
  }
}

export async function discoverSchema(): Promise<SchemaRegistry> {
  const doctypes: Record<string, DoctypeMeta> = {}
  const domains: Record<string, DomainModel> = {}

  const results = await Promise.all(
    CORE_DOCTYPES.map(async (dt) => {
      const meta = await fetchDoctypeMeta(dt)
      return { doctype: dt, meta }
    })
  )

  for (const { doctype, meta } of results) {
    if (meta) {
      doctypes[doctype] = meta
      domains[doctype.replace(/\s+/g, '')] = buildDomainModel(doctype, meta)
    }
  }

  return {
    doctypes,
    domains,
    discoveredAt: new Date().toISOString(),
  }
}

export function saveSchemaToStorage(registry: SchemaRegistry): void {
  try {
    localStorage.setItem('crm_schema_registry', JSON.stringify(registry))
  } catch (e) {
    console.warn('Failed to save schema to localStorage', e)
  }
}

export function loadSchemaFromStorage(): SchemaRegistry | null {
  try {
    const stored = localStorage.getItem('crm_schema_registry')
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (e) {
    console.warn('Failed to load schema from localStorage', e)
  }
  return null
}
