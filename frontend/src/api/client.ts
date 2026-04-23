import { createResource } from 'frappe-ui'

// Custom fetch wrapper that ensures credentials are included
async function frappeRequest(options: {
  url: string
  method?: string
  params?: Record<string, unknown>
  body?: Record<string, unknown>
}): Promise<any> {
  const { url, method = 'GET', params, body } = options
  
  let finalUrl = url
  if (params && method === 'GET') {
    const searchParams = new URLSearchParams()
    for (const [key, value] of Object.entries(params)) {
      searchParams.append(key, String(value))
    }
    finalUrl = `${url}?${searchParams.toString()}`
  }
  
  const headers: Record<string, string> = {
    'Accept': 'application/json',
    'Content-Type': 'application/json; charset=utf-8',
    'X-Frappe-Site-Name': window.location.hostname,
  }
  
  // Add CSRF token if available
  const csrfToken = (window as any).csrf_token
  if (csrfToken && csrfToken !== '{{ csrf_token }}') {
    headers['X-Frappe-CSRF-Token'] = csrfToken
  }
  
  const fetchOptions: RequestInit = {
    method,
    headers,
    credentials: 'include', // Important: include cookies for authentication
  }
  
  if (body && method !== 'GET') {
    fetchOptions.body = JSON.stringify(body)
  }
  
  const response = await fetch(finalUrl, fetchOptions)
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    const error = new Error(errorData.message || response.statusText)
    ;(error as any).response = response
    ;(error as any).data = errorData
    throw error
  }
  
  return response.json()
}

export interface ListParams {
  doctype: string
  fields?: string[]
  filters?: Record<string, unknown> | unknown[][]
  orderBy?: string
  limitStart?: number
  limitPageLength?: number
  groupBy?: string
}

export interface ResourceResponse<T> {
  data: T
  message?: string
}

export async function apiList<T = unknown>(params: ListParams): Promise<T[]> {
  const { doctype, fields, filters, orderBy, limitStart = 0, limitPageLength = 20 } = params
  
  const queryParams: Record<string, unknown> = {
    limit_start: limitStart,
    limit_page_length: limitPageLength,
  }
  
  if (fields?.length) {
    queryParams.fields = JSON.stringify(fields)
  }
  
  if (filters) {
    queryParams.filters = JSON.stringify(filters)
  }
  
  if (orderBy) {
    queryParams.order_by = orderBy
  }

  try {
    const res = await frappeRequest({
      url: `/api/resource/${encodeURIComponent(doctype)}`,
      method: 'GET',
      params: queryParams,
    })
    return res?.data || []
  } catch (e) {
    console.error(`Failed to list ${doctype}:`, e)
    return []
  }
}

export async function apiGet<T = unknown>(doctype: string, name: string): Promise<T | null> {
  try {
    const res = await frappeRequest({
      url: `/api/resource/${encodeURIComponent(doctype)}/${encodeURIComponent(name)}`,
      method: 'GET',
    })
    return res?.data || null
  } catch (e) {
    console.error(`Failed to get ${doctype}/${name}:`, e)
    return null
  }
}

export async function apiCreate<T = unknown>(doctype: string, data: Record<string, unknown>): Promise<T> {
  const res = await frappeRequest({
    url: `/api/resource/${encodeURIComponent(doctype)}`,
    method: 'POST',
    body: data,
  })
  return res.data
}

export async function apiUpdate<T = unknown>(
  doctype: string,
  name: string,
  data: Record<string, unknown>
): Promise<T> {
  const res = await frappeRequest({
    url: `/api/resource/${encodeURIComponent(doctype)}/${encodeURIComponent(name)}`,
    method: 'PUT',
    body: data,
  })
  return res.data
}

export async function apiDelete(doctype: string, name: string): Promise<void> {
  await frappeRequest({
    url: `/api/resource/${encodeURIComponent(doctype)}/${encodeURIComponent(name)}`,
    method: 'DELETE',
  })
}

export async function apiCall<T = unknown>(
  method: string,
  args?: Record<string, unknown>
): Promise<T> {
  const res = await frappeRequest({
    url: `/api/method/${method}`,
    method: 'POST',
    body: args,
  })
  return res.message
}

export async function apiGetCount(
  doctype: string,
  filters?: Record<string, unknown> | unknown[][]
): Promise<number> {
  try {
    const params: Record<string, string> = { doctype }
    if (filters) {
      params.filters = JSON.stringify(filters)
    }
    const res = await frappeRequest({
      url: '/api/method/frappe.client.get_count',
      method: 'GET',
      params,
    })
    return res?.message ?? 0
  } catch (e) {
    console.warn(`Failed to get count for ${doctype}:`, e)
    return 0
  }
}

// Search for link field options using frappe.client.get_list
export async function apiSearchLink(
  doctype: string,
  txt: string = '',
  filters?: Record<string, unknown>,
  titleField?: string
): Promise<{ value: string; label: string; description?: string }[]> {
  try {
    // Build filters for search
    const searchFilters: Record<string, unknown> = { ...filters }
    
    // Add text search filter if provided
    if (txt && txt.trim()) {
      // Search on name or title field
      const searchField = titleField || 'name'
      searchFilters[searchField] = ['like', `%${txt}%`]
    }
    
    const params: Record<string, string> = {
      doctype,
      fields: JSON.stringify(['name', titleField || 'name']),
      filters: JSON.stringify(searchFilters),
      limit_page_length: '20',
      order_by: 'modified desc',
    }
    
    const res = await frappeRequest({
      url: '/api/method/frappe.client.get_list',
      method: 'GET',
      params,
    })
    
    const results = res?.message || []
    return results.map((item: any) => ({
      value: item.name,
      label: titleField && item[titleField] ? item[titleField] : item.name,
      description: titleField && item[titleField] !== item.name ? item.name : undefined,
    }))
  } catch (e) {
    console.warn(`Failed to search ${doctype}:`, e)
    return []
  }
}

// Re-export helpers
export { frappeRequest, createResource }
