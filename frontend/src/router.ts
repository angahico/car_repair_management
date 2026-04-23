import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useSessionStore } from '@/stores/session'

const routes: RouteRecordRaw[] = [
  // Auth routes
  {
    path: '/auth/login',
    name: 'Login',
    component: () => import('@/pages/auth/Login.vue'),
    meta: { public: true },
  },
  {
    path: '/auth/forgot',
    name: 'ForgotPassword',
    component: () => import('@/pages/auth/ForgotPassword.vue'),
    meta: { public: true },
  },
  
  // Protected routes
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/pages/Dashboard.vue'),
  },
  {
    path: '/repair-orders',
    name: 'RepairOrders',
    component: () => import('@/pages/repair-orders/RepairOrderList.vue'),
  },
  {
    path: '/repair-orders/new',
    name: 'RepairOrderNew',
    component: () => import('@/pages/repair-orders/RepairOrderForm.vue'),
    props: { isNew: true },
  },
  {
    path: '/repair-orders/:id',
    name: 'RepairOrderDetail',
    component: () => import('@/pages/repair-orders/RepairOrderDetail.vue'),
    props: true,
  },
  {
    path: '/repair-orders/:id/edit',
    name: 'RepairOrderEdit',
    component: () => import('@/pages/repair-orders/RepairOrderForm.vue'),
    props: true,
  },
  {
    path: '/repair-orders/:roId/operations/:opId',
    name: 'OperationDetail',
    component: () => import('@/pages/repair-orders/OperationDetail.vue'),
    props: true,
  },
  // Vehicle routes
  {
    path: '/vehicles',
    name: 'Vehicles',
    component: () => import('@/pages/vehicles/VehicleList.vue'),
  },
  {
    path: '/vehicles/new',
    name: 'VehicleNew',
    component: () => import('@/pages/vehicles/VehicleForm.vue'),
    props: { isNew: true },
  },
  {
    path: '/vehicles/assignments',
    name: 'VehicleAssignments',
    component: () => import('@/pages/vehicles/VehicleAssignments.vue'),
  },
  {
    path: '/vehicles/meter-history',
    name: 'MeterHistory',
    component: () => import('@/pages/vehicles/MeterHistory.vue'),
  },
  {
    path: '/vehicles/expense-history',
    name: 'ExpenseHistory',
    component: () => import('@/pages/vehicles/ExpenseHistory.vue'),
  },
  {
    path: '/vehicles/replacement-analysis',
    name: 'ReplacementAnalysis',
    component: () => import('@/pages/vehicles/ReplacementAnalysis.vue'),
  },
  {
    path: '/vehicles/aging-analysis',
    name: 'VehicleAgingAnalysis',
    component: () => import('@/pages/vehicles/AgingAnalysis.vue'),
  },
  {
    path: '/vehicles/:id',
    name: 'VehicleDetail',
    component: () => import('@/pages/vehicles/VehicleDetail.vue'),
    props: true,
  },
  {
    path: '/vehicles/:id/edit',
    name: 'VehicleEdit',
    component: () => import('@/pages/vehicles/VehicleForm.vue'),
    props: true,
  },
  {
    path: '/customers',
    name: 'Customers',
    component: () => import('@/pages/customers/CustomerList.vue'),
  },
  {
    path: '/customers/:id',
    name: 'CustomerDetail',
    component: () => import('@/pages/customers/CustomerDetail.vue'),
    props: true,
  },
  // Employee routes
  {
    path: '/employees',
    name: 'Employees',
    component: () => import('@/pages/employees/EmployeeList.vue'),
  },
  {
    path: '/employees/:id',
    name: 'EmployeeDetail',
    component: () => import('@/pages/employees/EmployeeDetail.vue'),
    props: true,
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: () => import('@/pages/Tasks.vue'),
  },
  // Inspection routes
  {
    path: '/inspections',
    name: 'Inspections',
    component: () => import('@/pages/inspections/InspectionHistory.vue'),
  },
  {
    path: '/inspections/:id',
    name: 'InspectionDetail',
    component: () => import('@/pages/inspections/InspectionDetail.vue'),
    props: true,
  },
  {
    path: '/inspections/item-failures',
    name: 'ItemFailures',
    component: () => import('@/pages/inspections/ItemFailure.vue'),
  },
  {
    path: '/inspections/item-failures/:id',
    name: 'ItemFailureDetail',
    component: () => import('@/pages/inspections/ItemFailureDetail.vue'),
    props: true,
  },
  {
    path: '/inspections/schedules',
    name: 'InspectionSchedules',
    component: () => import('@/pages/inspections/Schedules.vue'),
  },
  {
    path: '/inspections/schedules/:id',
    name: 'ScheduleDetail',
    component: () => import('@/pages/inspections/ScheduleDetail.vue'),
    props: true,
  },
  {
    path: '/inspections/forms',
    name: 'InspectionForms',
    component: () => import('@/pages/inspections/Forms.vue'),
  },
  {
    path: '/inspections/forms/:id',
    name: 'FormTemplateDetail',
    component: () => import('@/pages/inspections/FormDetail.vue'),
    props: true,
  },
  // Issue routes
  {
    path: '/issues',
    name: 'Issues',
    component: () => import('@/pages/issues/IssueList.vue'),
  },
  {
    path: '/issues/new',
    name: 'IssueNew',
    component: () => import('@/pages/issues/IssueForm.vue'),
  },
  {
    path: '/issues/:id',
    name: 'IssueDetail',
    component: () => import('@/pages/issues/IssueDetail.vue'),
    props: true,
  },
  {
    path: '/issues/faults',
    name: 'Faults',
    component: () => import('@/pages/issues/Faults.vue'),
  },
  {
    path: '/issues/faults/:id',
    name: 'FaultDetail',
    component: () => import('@/pages/issues/FaultDetail.vue'),
    props: true,
  },
  {
    path: '/issues/recalls',
    name: 'Recalls',
    component: () => import('@/pages/issues/Recalls.vue'),
  },
  {
    path: '/issues/recalls/:id',
    name: 'RecallDetail',
    component: () => import('@/pages/issues/RecallDetail.vue'),
    props: true,
  },
  {
    path: '/expenses',
    name: 'Expenses',
    component: () => import('@/pages/expenses/ExpenseList.vue'),
  },
  {
    path: '/expenses/new',
    name: 'ExpenseNew',
    component: () => import('@/pages/expenses/ExpenseForm.vue'),
    props: { isNew: true },
  },
  {
    path: '/expenses/:id',
    name: 'ExpenseDetail',
    component: () => import('@/pages/expenses/ExpenseDetail.vue'),
    props: true,
  },
  {
    path: '/expenses/:id/edit',
    name: 'ExpenseEdit',
    component: () => import('@/pages/expenses/ExpenseForm.vue'),
    props: true,
  },
  {
    path: '/parts',
    name: 'Parts',
    component: () => import('@/pages/parts/PartList.vue'),
  },
  {
    path: '/parts/new',
    name: 'PartNew',
    component: () => import('@/pages/parts/PartForm.vue'),
    props: { isNew: true },
  },
  {
    path: '/parts/:id',
    name: 'PartDetail',
    component: () => import('@/pages/parts/PartDetail.vue'),
    props: true,
  },
  {
    path: '/parts/:id/edit',
    name: 'PartEdit',
    component: () => import('@/pages/parts/PartForm.vue'),
    props: true,
  },
  {
    path: '/invoices',
    name: 'Invoices',
    component: () => import('@/pages/invoices/InvoiceList.vue'),
  },
  {
    path: '/invoices/:id',
    name: 'InvoiceDetail',
    component: () => import('@/pages/invoices/InvoiceDetail.vue'),
    props: true,
  },
  // Report routes
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('@/pages/reports/Overview.vue'),
  },
  {
    path: '/reports/library',
    name: 'ReportsLibrary',
    component: () => import('@/pages/reports/Library.vue'),
  },
  {
    path: '/reports/saved',
    name: 'SavedReports',
    component: () => import('@/pages/reports/SavedReports.vue'),
  },
  {
    path: '/reports/scheduled',
    name: 'ScheduledReports',
    component: () => import('@/pages/reports/ScheduledReports.vue'),
  },
  {
    path: '/reports/view/:id',
    name: 'ReportView',
    component: () => import('@/pages/reports/ReportView.vue'),
    props: true,
  },

  // Settings routes
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/pages/settings/SettingsHome.vue'),
  },
  {
    path: '/settings/:category',
    name: 'SettingsCategory',
    component: () => import('@/pages/settings/SettingsCategory.vue'),
    props: true,
  },
  
  // Fuel routes
  {
    path: '/fuel',
    name: 'FuelList',
    component: () => import('@/pages/fuel/FuelList.vue'),
  },
  {
    path: '/fuel/new',
    name: 'FuelNew',
    component: () => import('@/pages/fuel/FuelForm.vue'),
  },
  {
    path: '/fuel/quotas',
    name: 'FuelQuotas',
    component: () => import('@/pages/fuel/FuelQuotaList.vue'),
  },
  {
    path: '/fuel/:id',
    name: 'FuelDetail',
    component: () => import('@/pages/fuel/FuelDetail.vue'),
    props: true,
  },

  // Catch-all
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/pages/NotFound.vue'),
  },
]

const router = createRouter({
  history: createWebHistory('/workshop'),
  routes,
})

router.beforeEach((to, _from, next) => {
  const sessionStore = useSessionStore()
  
  // Allow public routes
  if (to.meta.public) {
    if (sessionStore.isLoggedIn && to.name === 'Login') {
      next({ name: 'Dashboard' })
    } else {
      next()
    }
    return
  }
  
  // Redirect to login if not authenticated
  if (!sessionStore.isLoggedIn) {
    window.location.href = '/login?redirect-to=/workshop'
    return
  }
  
  next()
})

export default router
