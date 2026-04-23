export interface RepairOrderDomain {
  id: string
  displayName: string
  status: string
  priority: string
  customerId: string
  customerName?: string
  vehicleId: string
  vehicleName?: string
  problemSummary: string
  problemDetails: string
  slaDeliveryBy?: string
  projectId?: string
  quotationId?: string
  salesOrderId?: string
  salesInvoiceId?: string
  partsCost: number
  laborCost: number
  otherCharges: number
  totalJobCost: number
  quotedAmount: number
  invoicedAmount: number
  grossMargin: number
  createdAt: string
  modifiedAt: string
}

export interface VehicleDomain {
  id: string
  displayName: string
  licensePlate?: string
  make?: string
  model?: string
  year?: number
  variant?: string
  transmission?: string
  odometer?: number
  ownerId?: string
}

export interface CustomerDomain {
  id: string
  displayName: string
  email?: string
  phone?: string
  type?: string
}

export function mapRepairOrder(raw: Record<string, unknown>): RepairOrderDomain {
  return {
    id: raw.name as string,
    displayName: raw.name as string,
    status: (raw.status as string) || 'Draft',
    priority: (raw.priority as string) || 'Normal',
    customerId: raw.customer as string,
    customerName: raw.customer_name as string | undefined,
    vehicleId: raw.vehicle as string,
    vehicleName: raw.vehicle_name as string | undefined,
    problemSummary: (raw.problem_summary as string) || '',
    problemDetails: (raw.problem_details as string) || '',
    slaDeliveryBy: raw.sla_delivery_by as string | undefined,
    projectId: raw.project as string | undefined,
    quotationId: raw.quotation as string | undefined,
    salesOrderId: raw.sales_order as string | undefined,
    salesInvoiceId: raw.sales_invoice as string | undefined,
    partsCost: (raw.parts_cost as number) || 0,
    laborCost: (raw.labor_cost as number) || 0,
    otherCharges: (raw.other_charges as number) || 0,
    totalJobCost: (raw.total_job_cost as number) || 0,
    quotedAmount: (raw.quoted_amount as number) || 0,
    invoicedAmount: (raw.invoiced_amount as number) || 0,
    grossMargin: (raw.gross_margin as number) || 0,
    createdAt: raw.creation as string,
    modifiedAt: raw.modified as string,
  }
}

export function mapVehicle(raw: Record<string, unknown>): VehicleDomain {
  return {
    id: raw.name as string,
    displayName: raw.name as string,
    licensePlate: raw.license_plate as string | undefined,
    make: raw.make as string | undefined,
    model: raw.model as string | undefined,
    year: raw.year as number | undefined,
    variant: raw.variant as string | undefined,
    transmission: raw.transmission as string | undefined,
    odometer: raw.odometer_at_last_service as number | undefined,
    ownerId: raw.owner as string | undefined,
  }
}

export function mapCustomer(raw: Record<string, unknown>): CustomerDomain {
  return {
    id: raw.name as string,
    displayName: (raw.customer_name as string) || (raw.name as string),
    email: raw.email_id as string | undefined,
    phone: raw.mobile_no as string | undefined,
    type: raw.customer_type as string | undefined,
  }
}
