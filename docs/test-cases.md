# MVP 1 Test Cases

## Overview

These test cases define the business-rule expectations for the BNPL Cash Flow Tracker MVP 1 rules engine before implementation begins.

Source-of-truth documents:

- `docs/data-model.md`
- `docs/calculation-rules.md`

Rules validated across these cases:

- Installment 1 occurs on `first_installment_date`.
- `BIWEEKLY` installments occur every 14 days.
- Installment amounts use decimal-safe rounding.
- Any rounding remainder is assigned to the final installment.
- Statement cycle assignment uses `previous_cycle_end_date < charge_date <= cycle_end_date`.
- Installments on statement end day belong to that closing statement.
- Payment due date is the first occurrence of `payment_due_day` after statement close.
- Cash flow obligations aggregate by credit card and payment due date.
- `cash_flow_period` is derived from payment due date using `YYYY-MM`.

## TC-001 Standard Klarna Pay In 4 Using Tangerine Mastercard

Purpose:

Validate the core MVP 1 scenario: a standard Klarna Pay in 4 plan paid with Tangerine Mastercard.

Input:

```text
Credit Card ID: card_tangerine_mastercard
Credit Card Name: Tangerine Mastercard
Statement End Day: 17
Payment Due Day: 13

BNPL Plan ID: plan_klarna_laptop_sleeve
Provider: Klarna
Plan Name: Laptop Sleeve
Purchase Amount: 120.00
Currency: CAD
Purchase Date: 2026-06-07
First Installment Date: 2026-06-07
Installment Count: 4
Installment Frequency: BIWEEKLY
Credit Card ID: card_tangerine_mastercard
```

Expected Installments:

```text
1. 2026-06-07 - 30.00 CAD
2. 2026-06-21 - 30.00 CAD
3. 2026-07-05 - 30.00 CAD
4. 2026-07-19 - 30.00 CAD
```

Expected Statement Cycle Mapping:

```text
2026-06-07 -> 2026-05-18 to 2026-06-17
2026-06-21 -> 2026-06-18 to 2026-07-17
2026-07-05 -> 2026-06-18 to 2026-07-17
2026-07-19 -> 2026-07-18 to 2026-08-17
```

Expected Due Date Mapping:

```text
2026-06-07 -> 2026-07-13 -> cash_flow_period 2026-07
2026-06-21 -> 2026-08-13 -> cash_flow_period 2026-08
2026-07-05 -> 2026-08-13 -> cash_flow_period 2026-08
2026-07-19 -> 2026-09-13 -> cash_flow_period 2026-09
```

Expected Cash Flow Obligations:

```text
2026-07-13 | Tangerine Mastercard | 2026-07 | 30.00 CAD
2026-08-13 | Tangerine Mastercard | 2026-08 | 60.00 CAD
2026-09-13 | Tangerine Mastercard | 2026-09 | 30.00 CAD
```

## TC-002 Installment Before Statement End Day

Purpose:

Validate that an installment before the statement end day belongs to the current open statement cycle.

Input:

```text
Credit Card ID: card_tangerine_mastercard
Credit Card Name: Tangerine Mastercard
Statement End Day: 17
Payment Due Day: 13

BNPL Plan ID: plan_before_statement_end
Provider: Klarna
Plan Name: Before Statement End
Purchase Amount: 40.00
Currency: CAD
Purchase Date: 2026-06-16
First Installment Date: 2026-06-16
Installment Count: 1
Installment Frequency: BIWEEKLY
Credit Card ID: card_tangerine_mastercard
```

Expected Installments:

```text
1. 2026-06-16 - 40.00 CAD
```

Expected Statement Cycle Mapping:

```text
2026-06-16 -> 2026-05-18 to 2026-06-17
```

Expected Due Date Mapping:

```text
2026-06-16 -> 2026-07-13 -> cash_flow_period 2026-07
```

Expected Cash Flow Obligations:

```text
2026-07-13 | Tangerine Mastercard | 2026-07 | 40.00 CAD
```

## TC-003 Installment Exactly On Statement End Day

Purpose:

Validate that an installment dated exactly on the statement end day belongs to that closing statement.

Input:

```text
Credit Card ID: card_tangerine_mastercard
Credit Card Name: Tangerine Mastercard
Statement End Day: 17
Payment Due Day: 13

BNPL Plan ID: plan_on_statement_end
Provider: Klarna
Plan Name: On Statement End
Purchase Amount: 40.00
Currency: CAD
Purchase Date: 2026-06-17
First Installment Date: 2026-06-17
Installment Count: 1
Installment Frequency: BIWEEKLY
Credit Card ID: card_tangerine_mastercard
```

Expected Installments:

```text
1. 2026-06-17 - 40.00 CAD
```

Expected Statement Cycle Mapping:

```text
2026-06-17 -> 2026-05-18 to 2026-06-17
```

Expected Due Date Mapping:

```text
2026-06-17 -> 2026-07-13 -> cash_flow_period 2026-07
```

Expected Cash Flow Obligations:

```text
2026-07-13 | Tangerine Mastercard | 2026-07 | 40.00 CAD
```

## TC-004 Installment After Statement End Day

Purpose:

Validate that an installment after the statement end day belongs to the next statement cycle.

Input:

```text
Credit Card ID: card_tangerine_mastercard
Credit Card Name: Tangerine Mastercard
Statement End Day: 17
Payment Due Day: 13

BNPL Plan ID: plan_after_statement_end
Provider: Klarna
Plan Name: After Statement End
Purchase Amount: 40.00
Currency: CAD
Purchase Date: 2026-06-18
First Installment Date: 2026-06-18
Installment Count: 1
Installment Frequency: BIWEEKLY
Credit Card ID: card_tangerine_mastercard
```

Expected Installments:

```text
1. 2026-06-18 - 40.00 CAD
```

Expected Statement Cycle Mapping:

```text
2026-06-18 -> 2026-06-18 to 2026-07-17
```

Expected Due Date Mapping:

```text
2026-06-18 -> 2026-08-13 -> cash_flow_period 2026-08
```

Expected Cash Flow Obligations:

```text
2026-08-13 | Tangerine Mastercard | 2026-08 | 40.00 CAD
```

## TC-005 Due Date In Same Calendar Month As Statement Close

Purpose:

Validate that when `payment_due_day` occurs after the statement close date in the same month, the due date is in that same calendar month.

Input:

```text
Credit Card ID: card_same_month_due
Credit Card Name: Same Month Mastercard
Statement End Day: 10
Payment Due Day: 25

BNPL Plan ID: plan_same_month_due
Provider: PayPal
Plan Name: Same Month Due
Purchase Amount: 40.00
Currency: CAD
Purchase Date: 2026-06-10
First Installment Date: 2026-06-10
Installment Count: 1
Installment Frequency: BIWEEKLY
Credit Card ID: card_same_month_due
```

Expected Installments:

```text
1. 2026-06-10 - 40.00 CAD
```

Expected Statement Cycle Mapping:

```text
2026-06-10 -> 2026-05-11 to 2026-06-10
```

Expected Due Date Mapping:

```text
2026-06-10 -> 2026-06-25 -> cash_flow_period 2026-06
```

Expected Cash Flow Obligations:

```text
2026-06-25 | Same Month Mastercard | 2026-06 | 40.00 CAD
```

## TC-006 Due Date In Following Calendar Month

Purpose:

Validate that when the first occurrence of `payment_due_day` after statement close falls in the following month, the due date and cash-flow period roll forward.

Input:

```text
Credit Card ID: card_tangerine_mastercard
Credit Card Name: Tangerine Mastercard
Statement End Day: 17
Payment Due Day: 13

BNPL Plan ID: plan_following_month_due
Provider: PayPal
Plan Name: Following Month Due
Purchase Amount: 40.00
Currency: CAD
Purchase Date: 2026-06-17
First Installment Date: 2026-06-17
Installment Count: 1
Installment Frequency: BIWEEKLY
Credit Card ID: card_tangerine_mastercard
```

Expected Installments:

```text
1. 2026-06-17 - 40.00 CAD
```

Expected Statement Cycle Mapping:

```text
2026-06-17 -> 2026-05-18 to 2026-06-17
```

Expected Due Date Mapping:

```text
2026-06-17 -> 2026-07-13 -> cash_flow_period 2026-07
```

Expected Cash Flow Obligations:

```text
2026-07-13 | Tangerine Mastercard | 2026-07 | 40.00 CAD
```

## TC-007 Uneven Purchase Amount Rounding

Purpose:

Validate decimal-safe installment rounding and assignment of the rounding remainder to the final installment.

Input:

```text
Credit Card ID: card_tangerine_mastercard
Credit Card Name: Tangerine Mastercard
Statement End Day: 17
Payment Due Day: 13

BNPL Plan ID: plan_uneven_rounding
Provider: Klarna
Plan Name: Uneven Rounding
Purchase Amount: 100.00
Currency: CAD
Purchase Date: 2026-06-07
First Installment Date: 2026-06-07
Installment Count: 3
Installment Frequency: BIWEEKLY
Credit Card ID: card_tangerine_mastercard
```

Expected Installments:

```text
1. 2026-06-07 - 33.33 CAD
2. 2026-06-21 - 33.33 CAD
3. 2026-07-05 - 33.34 CAD
```

Expected Statement Cycle Mapping:

```text
2026-06-07 -> 2026-05-18 to 2026-06-17
2026-06-21 -> 2026-06-18 to 2026-07-17
2026-07-05 -> 2026-06-18 to 2026-07-17
```

Expected Due Date Mapping:

```text
2026-06-07 -> 2026-07-13 -> cash_flow_period 2026-07
2026-06-21 -> 2026-08-13 -> cash_flow_period 2026-08
2026-07-05 -> 2026-08-13 -> cash_flow_period 2026-08
```

Expected Cash Flow Obligations:

```text
2026-07-13 | Tangerine Mastercard | 2026-07 | 33.33 CAD
2026-08-13 | Tangerine Mastercard | 2026-08 | 66.67 CAD
```

Validation:

The sum of all generated installments must equal the original purchase amount exactly.

The sum of all aggregated cash-flow obligations must equal the original purchase amount exactly.

```text
33.33 + 33.33 + 33.34 = 100.00
33.33 + 66.67 = 100.00
```

## TC-008 Multiple BNPL Plans Same Card Same Due Date

Purpose:

Validate that installments from separate BNPL plans aggregate under the same credit card and payment due date.

Input:

```text
Credit Card ID: card_tangerine_mastercard
Credit Card Name: Tangerine Mastercard
Statement End Day: 17
Payment Due Day: 13

BNPL Plan ID: plan_klarna_keyboard
Provider: Klarna
Plan Name: Keyboard
Purchase Amount: 80.00
Currency: CAD
Purchase Date: 2026-06-21
First Installment Date: 2026-06-21
Installment Count: 1
Installment Frequency: BIWEEKLY
Credit Card ID: card_tangerine_mastercard

BNPL Plan ID: plan_paypal_mouse
Provider: PayPal
Plan Name: Mouse
Purchase Amount: 50.00
Currency: CAD
Purchase Date: 2026-07-05
First Installment Date: 2026-07-05
Installment Count: 1
Installment Frequency: BIWEEKLY
Credit Card ID: card_tangerine_mastercard
```

Expected Installments:

```text
plan_klarna_keyboard 1. 2026-06-21 - 80.00 CAD
plan_paypal_mouse 1. 2026-07-05 - 50.00 CAD
```

Expected Statement Cycle Mapping:

```text
2026-06-21 -> 2026-06-18 to 2026-07-17
2026-07-05 -> 2026-06-18 to 2026-07-17
```

Expected Due Date Mapping:

```text
2026-06-21 -> 2026-08-13 -> cash_flow_period 2026-08
2026-07-05 -> 2026-08-13 -> cash_flow_period 2026-08
```

Expected Cash Flow Obligations:

```text
2026-08-13 | Tangerine Mastercard | 2026-08 | 130.00 CAD
```

## TC-009 Multiple Cards With Different Statement And Due Days

Purpose:

Validate that the same installment date maps differently when assigned to cards with different statement and due days.

Input:

```text
Credit Card ID: card_tangerine_mastercard
Credit Card Name: Tangerine Mastercard
Statement End Day: 17
Payment Due Day: 13

Credit Card ID: card_rbc_mastercard
Credit Card Name: RBC Mastercard
Statement End Day: 6
Payment Due Day: 27

BNPL Plan ID: plan_tangerine_shared_date
Provider: Klarna
Plan Name: Tangerine Shared Date
Purchase Amount: 40.00
Currency: CAD
Purchase Date: 2026-06-12
First Installment Date: 2026-06-12
Installment Count: 1
Installment Frequency: BIWEEKLY
Credit Card ID: card_tangerine_mastercard

BNPL Plan ID: plan_rbc_shared_date
Provider: PayPal
Plan Name: RBC Shared Date
Purchase Amount: 60.00
Currency: CAD
Purchase Date: 2026-06-12
First Installment Date: 2026-06-12
Installment Count: 1
Installment Frequency: BIWEEKLY
Credit Card ID: card_rbc_mastercard
```

Expected Installments:

```text
plan_tangerine_shared_date 1. 2026-06-12 - 40.00 CAD
plan_rbc_shared_date 1. 2026-06-12 - 60.00 CAD
```

Expected Statement Cycle Mapping:

```text
Tangerine Mastercard: 2026-06-12 -> 2026-05-18 to 2026-06-17
RBC Mastercard: 2026-06-12 -> 2026-06-07 to 2026-07-06
```

Expected Due Date Mapping:

```text
Tangerine Mastercard: 2026-06-12 -> 2026-07-13 -> cash_flow_period 2026-07
RBC Mastercard: 2026-06-12 -> 2026-07-27 -> cash_flow_period 2026-07
```

Expected Cash Flow Obligations:

```text
2026-07-13 | Tangerine Mastercard | 2026-07 | 40.00 CAD
2026-07-27 | RBC Mastercard | 2026-07 | 60.00 CAD
```

## TC-010 December To January Year Rollover

Purpose:

Validate installment generation, statement cycle mapping, due dates, and cash-flow periods across a calendar year boundary.

Input:

```text
Credit Card ID: card_tangerine_mastercard
Credit Card Name: Tangerine Mastercard
Statement End Day: 17
Payment Due Day: 13

BNPL Plan ID: plan_year_rollover
Provider: Klarna
Plan Name: Year Rollover
Purchase Amount: 120.00
Currency: CAD
Purchase Date: 2026-12-10
First Installment Date: 2026-12-10
Installment Count: 4
Installment Frequency: BIWEEKLY
Credit Card ID: card_tangerine_mastercard
```

Expected Installments:

```text
1. 2026-12-10 - 30.00 CAD
2. 2026-12-24 - 30.00 CAD
3. 2027-01-07 - 30.00 CAD
4. 2027-01-21 - 30.00 CAD
```

Expected Statement Cycle Mapping:

```text
2026-12-10 -> 2026-11-18 to 2026-12-17
2026-12-24 -> 2026-12-18 to 2027-01-17
2027-01-07 -> 2026-12-18 to 2027-01-17
2027-01-21 -> 2027-01-18 to 2027-02-17
```

Expected Due Date Mapping:

```text
2026-12-10 -> 2027-01-13 -> cash_flow_period 2027-01
2026-12-24 -> 2027-02-13 -> cash_flow_period 2027-02
2027-01-07 -> 2027-02-13 -> cash_flow_period 2027-02
2027-01-21 -> 2027-03-13 -> cash_flow_period 2027-03
```

Expected Cash Flow Obligations:

```text
2027-01-13 | Tangerine Mastercard | 2027-01 | 30.00 CAD
2027-02-13 | Tangerine Mastercard | 2027-02 | 60.00 CAD
2027-03-13 | Tangerine Mastercard | 2027-03 | 30.00 CAD
```

## TC-011 Leap Year Handling

Purpose:

Validate that February 29, 2028 is treated as a valid calendar date, BIWEEKLY installment generation uses 14-day date arithmetic, and statement cycle, due date, and cash-flow aggregation remain correct around leap day.

Input:

```text
Credit Card ID: card_tangerine_mastercard
Credit Card Name: Tangerine Mastercard
Statement End Day: 17
Payment Due Day: 13

BNPL Plan ID: plan_klarna_leap_year_validation
Provider: Klarna
Plan Name: Leap Year Validation
Purchase Amount: 120.00
Currency: CAD
Purchase Date: 2028-02-15
First Installment Date: 2028-02-15
Installment Count: 4
Installment Frequency: BIWEEKLY
Credit Card ID: card_tangerine_mastercard
```

Expected Installments:

```text
1. 2028-02-15 - 30.00 CAD
2. 2028-02-29 - 30.00 CAD
3. 2028-03-14 - 30.00 CAD
4. 2028-03-28 - 30.00 CAD
```

Expected Statement Cycle Mapping:

```text
2028-02-15 -> 2028-01-18 to 2028-02-17
2028-02-29 -> 2028-02-18 to 2028-03-17
2028-03-14 -> 2028-02-18 to 2028-03-17
2028-03-28 -> 2028-03-18 to 2028-04-17
```

Expected Due Date Mapping:

```text
2028-02-15 -> 2028-03-13 -> cash_flow_period 2028-03
2028-02-29 -> 2028-04-13 -> cash_flow_period 2028-04
2028-03-14 -> 2028-04-13 -> cash_flow_period 2028-04
2028-03-28 -> 2028-05-13 -> cash_flow_period 2028-05
```

Expected Cash Flow Obligations:

```text
2028-03-13 | Tangerine Mastercard | 2028-03 | 30.00 CAD
2028-04-13 | Tangerine Mastercard | 2028-04 | 60.00 CAD
2028-05-13 | Tangerine Mastercard | 2028-05 | 30.00 CAD
```
