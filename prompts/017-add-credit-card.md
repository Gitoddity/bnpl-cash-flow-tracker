Implement the **Add Credit Card flow** in the existing DueMap React + TypeScript + Vite frontend and FastAPI backend.

Use the existing Google Stitch screens as visual references:

* Stitch project ID: `6921387155947892246`
* Add Credit Card screen ID: `df771cad37d943d4a953784da7e501e8`
* Add Credit Card validation screen ID: `c1b39fb32b544238bfeb5c7d59e82e6`
* Credit Cards Overview screen ID: `df4b497260154bc6a212b62a668a7522`

Continue working on the existing `feature/react-ui-enhancement` branch. Preserve the completed landing page, profile creation flow, FastAPI integration, existing Streamlit application, and Python calculation pipeline.

## Navigation

* Clicking **Add Credit Card** from the active profile’s empty state opens the Add Credit Card screen.
* **Cancel** returns to the Credit Cards Overview without saving.
* Keep the active profile selected throughout the flow.

## Branding

Replace any remaining “CashFlow” branding on these screens with:

**DueMap**

Use the tagline where appropriate:

**“See what’s due. Know what’s left.”**

## Page introduction

Heading:

**Add a Credit Card**

Description:

**“Add the card’s billing schedule so DueMap can place your Klarna, Afterpay, and Sezzle installments into the correct credit card dues.”**

## Privacy notice

Add a prominent but calm information panel above the form.

Heading:

**No card credentials required**

Body:

**“DueMap does not need your card number, expiry date, CVV, PIN, or online banking login. It cannot access your account or charge your card.”**

Supporting line:

**“Only enter a card nickname, its current balance, and the billing dates shown on your statement.”**

Do not collect or store:

* Cardholder name
* Full or partial card number
* Expiry date
* CVV
* PIN
* Online banking credentials
* APR
* Card network

## Form fields

Reuse the existing backend card model and profile logic. Do not duplicate financial rules in React.

### Card Nickname

Placeholder:

**“e.g., TD Visa, RBC Mastercard”**

Supporting text:

**“Used to identify this card and connect payment plans to it.”**

This field is required.

### Current Balance

Supporting text:

**“The amount already owed on this card. DueMap includes it when projecting your upcoming credit card dues.”**

Use a currency input with an example such as `$500.00`.

### Statement Closing Day

Placeholder:

**“Day of month, e.g., 18”**

Supporting text:

**“Used to determine which statement receives each installment charge.”**

### Payment Due Day

Placeholder:

**“Day of month, e.g., 12”**

Supporting text:

**“Used to estimate when the resulting credit card due must be paid.”**

Accept values from 1 through 31. Do not require the due-day number to be greater than the closing-day number because the due date may fall in the following month.

Remove **Credit Limit** because it is not needed for the existing projection.

## Validation

Use backend validation as the source of truth and map validation errors to the relevant fields.

Handle at least:

* Missing card nickname
* Invalid current balance
* Statement closing day outside 1–31
* Payment due day outside 1–31

When validation or saving fails:

* Remain on the form.
* Preserve every value the user entered.
* Show field-specific errors beside the relevant fields.
* Show a form-level message for errors that cannot be assigned to one field.
* Prevent duplicate submissions while a save request is in progress.

## Save behaviour

When the user clicks **Save Card**:

1. Validate and save the card through FastAPI under the active profile.

2. After a successful save, navigate to the Credit Cards Overview.

3. Display the newly saved card immediately.

4. Show an accessible success notification:

   **“{cardNickname} added successfully.”**

5. Include an **Add Another Card** action in the success notification or prominently on the overview.

6. Clicking **Add Another Card** opens a fresh Add Credit Card form.

7. Automatically dismiss the notification after approximately four seconds.

8. Include a close button.

9. Use `role="status"` or an appropriate accessible live region.

10. Show the notification only after a successful save. Do not show it after refresh or when the overview is opened normally.

## Credit Cards Overview

Render cards using the existing Stitch overview design and actual backend data. Each saved card should show only the supported, noncredential information needed by the user, such as:

* Card nickname
* Current balance
* Statement closing day
* Payment due day

Do not display invented card numbers, networks, credit limits, or APR values.

Include a persistent **Add Credit Card** button so the user can add more cards at any time.

## Verification

Add focused verification for:

* Opening the form from the active profile
* Successful card creation
* Field validation and preservation of entered values
* Correct profile association
* Success notification behaviour
* Adding another card
* Persistence after browser refresh
* No collection of card credentials

Check the screen at desktop and mobile widths. Run the relevant backend and frontend tests, then summarize:

* Files changed
* FastAPI endpoints used or added
* Validation behaviour
* How to test the flow locally
* Anything remaining before implementing payment plans
