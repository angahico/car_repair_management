# Roles & Permissions

## Overview

The app uses Frappe's role-based permission system with custom roles for workshop operations.

## Key Roles

### Workshop Roles (from Workspace)
| Role | Purpose |
|---|---|
| **Workshop Manager** | Full control over repair orders, operations, and workshop |
| **Service Advisor** | Creates ROs, manages customer interactions |
| **Technician** | Assigned to operations, updates task status |
| **Stores User** | Manages parts, stock entries, material requests |
| **Accounts User** | Handles invoicing, quotations, financial reports |
| **System Manager** | Full system administration |

### Fleet Roles (from Vehicle permissions)
| Role | Vehicle Access | Description |
|---|---|---|
| **Fleet Manager** | Read, Create, Write | Full vehicle management |
| **Delivery Manager** | Read, Write | Vehicle delivery operations |
| **Delivery User** | Read only | View vehicle information |

### Other Roles
| Role | Purpose |
|---|---|
| **Employee** | Base role for all employees |
| **Maintenance Manager** | Maintenance oversight |
| **Maintenance User** | Maintenance operations |
| **Support Team** | Issue management (read/create on Issue DocType) |

## Permission Matrix

### Repair Order
Created with standard System Manager permissions. Additional access via Workshop Manager, Service Advisor roles.

### Vehicle
| Role | Read | Create | Write |
|---|---|---|---|
| Fleet Manager | ✓ | ✓ | ✓ |
| Delivery Manager | ✓ | ✗ | ✓ |
| Delivery User | ✓ | ✗ | ✗ |

### Issue (Frappe Core)
| Role | Read | Create | Write |
|---|---|---|---|
| Support Team | ✓ | ✓ | ✓ |

**Note**: The `create_issue` API uses `ignore_permissions=True` for insert, allowing any authenticated user to create issues via the frontend regardless of their Issue DocType permissions.

## User Permissions

Frappe's User Permission system can restrict records by Company. This affects:
- `frappe.client.get_list` calls (respects User Permissions)
- Standard LinkField searches

**Workaround**: The app provides custom search APIs (`search_vehicles`, `search_link_options`) that use `ignore_permissions=True` to bypass company-scoped restrictions in the issue and work order creation forms.

## Permission Patterns in the API

### Pattern 1: ignore_permissions on Insert
Most API methods that create records use `ignore_permissions=True`:
```python
doc.insert(ignore_permissions=True)
```
This ensures the frontend workflows work regardless of the user's DocType permissions.

### Pattern 2: Custom Search APIs
For vehicle and customer/company searches in forms where User Permissions would incorrectly filter results:
```python
@frappe.whitelist()
def search_vehicles(txt=None, limit_page_length=20):
    return frappe.get_all("Vehicle", ..., ignore_permissions=True)
```

### Pattern 3: Role-Based Workflow
The issue workflow determines available actions based on the creator's role relative to the vehicle (driver, custodian, or other) rather than Frappe roles.

## Recommendations

1. **Fleet Manager** role should be assigned to users who need to manage vehicles
2. **Support Team** role is needed for users who need native Frappe Desk access to Issues
3. All frontend SPA users need at minimum the **Employee** role
4. **User Permissions** for Company should be set carefully — mismatched company names can cause empty vehicle lists
