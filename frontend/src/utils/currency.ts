/**
 * Format a number as currency using the provided currency code.
 * Falls back to a simple prefix format if Intl doesn't support the currency.
 */
export function formatCurrency(value: number | null | undefined, currency = 'ETB'): string {
  if (value === null || value === undefined) return '—'
  try {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
      maximumFractionDigits: 0,
    }).format(value)
  } catch {
    return `${currency} ${value.toLocaleString()}`
  }
}
