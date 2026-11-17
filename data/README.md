# Synthetic HVAC company dataset

Made-up data for a residential and commercial home services company (HVAC, plumbing and electrical) in the Columbus, Ohio area. It is shaped like exports from two systems such a company typically runs:

- **ServiceTitan** (field service platform): customers, jobs, invoices, estimates, technicians, timesheets
- **QuickBooks** (accounting and payroll): employees, pay periods, payroll register

All names, IDs, emails and amounts are synthetic. Email addresses use `contoso.com`, Microsoft's fictional demo domain.

It powers three Power BI projects in this portfolio:

| Project | Main files |
| --- | --- |
| [Technician Payroll & Performance](../projects/technician-payroll.html) | `technicians`, `jobs`, `invoices`, `timesheets`, `employees`, `pay_periods`, `payroll_register` |
| [Live Sales Leaderboard](../projects/sales-leaderboard.html) | `estimates`, `salespeople`, `business_units`, `customers` |
| [Customer Retention Cohorts](../projects/customer-retention.html) | `invoices`, `customers`, `memberships`, `jobs`, `job_types` |

**Coverage:** 1 January 2025 to 16 November 2026. The export date is Monday 16 November 2026.

## Regenerate

```sh
python3 data/generate_data.py
```

It uses only the Python standard library and a fixed random seed, so the output is identical every run. Change `SEED` for a different company, or `BASE_NEW_CUSTOMERS` to scale the volume.

## Relationships

```
business_units ─┬─< job_types
                ├─< technicians ─┬─< jobs >── customers ──< memberships
                │                └─< timesheets      │
                ├─< salespeople ──< estimates >──────┘
                └─< jobs ──< invoices

employees (QuickBooks) ──< payroll_register >── pay_periods
```

ServiceTitan and QuickBooks do **not** share an ID. Link technicians to employees by name (see below).

## ServiceTitan files (`servicetitan/`)

| File | Grain | Columns |
| --- | --- | --- |
| `business_units.csv` | One row per business unit (6) | BusinessUnitID, BusinessUnitName, Trade, BusinessUnitType |
| `job_types.csv` | One row per job type (23) | JobTypeID, JobTypeName, BusinessUnitID, JobClass (Repair, Maintenance, Install) |
| `customers.csv` | One row per customer | CustomerID, CustomerName, CustomerType (Residential, Commercial), City, State, ZipCode, LeadSource, CreatedDate |
| `memberships.csv` | One row per maintenance plan | MembershipID, CustomerID, PlanName, StartDate, EndDate, AnnualPrice, Status (Active, Expired), Renewals |
| `technicians.csv` | One row per technician (current and former) | TechnicianID, TechnicianName, Email, BusinessUnitID, Position, HireDate, TerminationDate, Status, ManagerName, ManagerEmail |
| `salespeople.csv` | One row per salesperson | SalespersonID, SalespersonName, Email, BusinessUnitID, Title, HireDate, TerminationDate, Status |
| `jobs.csv` | One row per job | JobID, CustomerID, BusinessUnitID, JobTypeID, TechnicianID, CreatedDate, CompletedDate, JobStatus (Completed, Canceled, Scheduled), BillableHours |
| `invoices.csv` | One row per completed job | InvoiceID, JobID, CustomerID, InvoiceDate, BusinessUnitID, Subtotal, TaxAmount, Total |
| `estimates.csv` | One row per replacement or install quote | EstimateID, EstimateName, CustomerID, BusinessUnitID, JobTypeID, SalespersonID, OriginJobID, CreatedDate, SoldDate, Status (Sold, Dismissed, Open), EstimateTotal, InstallJobID |
| `timesheets.csv` | One row per technician per day worked | TimesheetID, TechnicianID, WorkDate, ClockIn, ClockOut, BreakMinutes, HoursWorked |

## QuickBooks files (`quickbooks/`)

| File | Grain | Columns |
| --- | --- | --- |
| `employees.csv` | One row per technician | EmployeeID, EmployeeName ("Last, First"), Department (trade), PayType, HourlyRate, CommissionRate, HireDate, ReleaseDate, Status |
| `pay_periods.csv` | One row per biweekly period, Sunday to Saturday | PayPeriodID, PeriodStart, PeriodEnd, PayDate, Status (Paid, Ready to Run, Open) |
| `payroll_register.csv` | One row per employee per paid period | PayPeriodID, PayDate, EmployeeID, RegularHours, OvertimeHours, HourlyRate, RegularPay, OvertimePay, Commission, GrossPay |

## Business rules

- **Overtime:** hours over 40 in a Sunday-to-Saturday week, paid at 1.5 × the hourly rate.
- **Commission:** service technicians (HVAC Service, Plumbing Service, Electrical) earn their `CommissionRate` on the invoice subtotal of jobs they completed in the pay period. Maintenance and install technicians earn none.
- **Memberships:** members get two tune-ups a year at no charge (invoices with a $0 subtotal) and 15% off repairs.
- **Installs:** a sold estimate becomes an install job 5 to 25 days later. `InstallJobID` is blank when the install hasn't happened yet.
- **Weekends:** service teams run a Saturday on-call rotation. Nobody works Sundays.

## Things to handle in prep

These are realistic quirks, put in on purpose:

- **Technician names don't match across systems.** ServiceTitan shows "First Last" and sometimes a nickname ("Mike Torres"); QuickBooks has the legal name as "Last, First" ("Torres, Michael"). 26 of 260 technicians need a manual mapping.
- **Customers who existed before the export.** About a third of customers were created before 2025, so their real first purchase isn't in the data. For cohort analysis, keep customers with `CreatedDate` on or after 2025-01-01.
- **Canceled and scheduled jobs** have no technician, no hours and no invoice.
- **$0 invoices** are membership tune-ups. Decide whether they count as a purchase for retention.
- **The latest pay period hasn't been run.** Period 49 (1 to 14 November 2026) is "Ready to Run": its timesheets exist but it isn't in the payroll register yet. This is the period the payroll report is for.
- **The register has keying errors.** About 1 in 130 rows has hours that don't match the timesheets, or a commission left off.

## Patterns in the data

The generator builds in a few patterns for the reports to find:

- Most customers never come back after their first job. Monthly return rates sit around 9% for non-members and 24% for members.
- Customers acquired in July and August (emergency AC calls) retain worse than those acquired in spring or fall.
- Referral customers retain best of any lead source.
- A membership follow-up program launched on 1 June 2025 raised sign-ups and renewals, so later cohorts retain slightly better.
- Demand is seasonal: AC calls peak in July, heating calls in January, and tune-ups in spring and fall. Summer brings the most overtime.
- Salespeople differ in close rate and average ticket, so the top five changes from month to month.
