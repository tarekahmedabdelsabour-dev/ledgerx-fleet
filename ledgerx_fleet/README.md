# LedgerX Fleet

Complete fleet management for ERPNext / Frappe **v16** (Arabic + English), from a handful of cars to a
multi-branch fleet. A separate Frappe app: it extends ERPNext's `Vehicle` and `Driver` with custom fields
and does not touch ERPNext or HRMS code.

Requires: `erpnext`, `hrms` (version-16).

## What is inside (22 DocTypes, 5 reports)

| Area | Records |
| --- | --- |
| Core | Vehicle (extended), Driver (extended), Vehicle Type, Fleet Assignment (driver history), Fleet Document + Fleet Document Type (registration, insurance, licenses... with expiry status and daily alerts), Vehicle Tire |
| Maintenance | Service Plan (+tasks), Service Schedule (km / days, Due Soon / Overdue), Fleet Work Order (tasks, parts, labor, stock issue, journal entry), Fuel Log (consumption per 100 km) |
| Operations | Fleet Trip (dispatch, expenses, revenue, Sales Invoice), Rental Contract (multi-vehicle, free km, extra km, damage, invoice), Traffic Fine (charged to company / driver / customer, salary deduction), Fleet Incident (accident, insurance claim, net loss) |
| Integration | GPS Device, Fleet GPS Position, HTTP endpoint for GPS providers, optional Journal Entry posting |
| Reports | Document Expiry, Maintenance Due, Vehicle Cost Analysis, Fuel Consumption, Trip Profitability |
| Scale | Company and Cost Center on every record (use User Permissions per branch), roles Fleet Manager / Fleet Operator, daily jobs, GPS log retention |

## Install

```bash
cd ~/frappe-bench-v16
bench get-app https://github.com/<your-user>/ledgerx-fleet
bench --site mysite.localhost install-app ledgerx_fleet
bench --site mysite.localhost migrate
bench --site mysite.localhost clear-cache
bench restart     # or stop/start bench start
```

Then: **Fleet Settings** (company, accounts, items, GPS token) and give users the *Fleet Manager* or
*Fleet Operator* role. Starter document types and vehicle types are created on install.

## GPS endpoint

`POST /api/method/ledgerx_fleet.api.gps.ingest` with the token from Fleet Settings in the
`X-Fleet-Token` header (or `token` parameter). Accepts one position or a list; common field names
(`id/imei/device_id`, `lat/lon`, `speed`, `timestamp`...) are understood.

## Development

`tools/spec.py` defines every DocType; `python3 tools/gen.py` regenerates the JSON and `ar.csv`
(controllers and JS are never overwritten). Before a release: `python3 tools/validate.py`,
`python3 tools/check_sql.py`, `python3 -m unittest ledgerx_fleet.tests.test_logic`.

## Status

Written and statically verified (JSON/schema, SQL, Python compile, pure-logic tests). It has not yet run
inside a live bench, so run the install on a test site first and report any error text.
