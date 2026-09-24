# Cards overview and payment-plan entry

Date: 2026-09-24

## User request

Update the post-save Credit Card flow and rebuild the Credit Cards Overview using the existing Google Stitch design.

### Stitch references

- Project ID: `6921387155947892246`
- Credit Cards Overview screen ID: `df4b497260154bc6a212b62a668a7522`
- Add Payment Plan screen ID: `394c5bab3c614a038accd189cd42ba9c`

Continue working on the existing `feature/react-ui-enhancement` branch. Preserve the working profile and Add Credit Card flows.

## Credit Cards Overview design

After a card is saved, navigate to the Credit Cards Overview and render it using the referenced Stitch screen, including:

- DueMap branding
- Active profile information
- Navigation for Credit Cards, Payment Plans, and Projection
- Saved card tiles
- Add Credit Card action
- Responsive desktop and mobile layouts

Use actual backend data. Do not display invented card numbers, networks, limits, or APR values.

## Success notification

The success notification is currently missing. After a card is saved successfully, show an accessible notification near the top of the overview:

“{cardNickname} added successfully.”

Requirements:

- Show it only after a successful save.
- Include a success icon.
- Include a close button.
- Automatically dismiss it after approximately four seconds.
- Use `role="status"` or an appropriate live region.
- Do not show it after refreshing or normally reopening the overview.
- Include an **Add Another Card** action that opens a fresh Add Credit Card form.
- Ensure the newly saved card appears immediately without requiring a refresh.

## Display complete upcoming dates

The overview currently displays:

- “Statement closing day — Day 18”
- “Payment due day — Day 12”

Replace these with resolved upcoming calendar dates that include the month and year:

- **Next statement closes:** `October 18, 2026`
- **Next payment is due:** `October 12, 2026`

The examples above are illustrative. Always calculate the actual upcoming dates from the saved card schedule and the application’s `as_of_date`.

Requirements:

- Use the existing Python billing-cycle and due-date rules.
- Expose the resolved dates through FastAPI if they are not already returned.
- Do not reproduce billing date calculations in React.
- Handle month and year rollover correctly.
- Continue supporting schedules where the due-day number is earlier than the statement-closing-day number because the due date may fall in the following month.
- Format dates using readable month names.
- Optionally show the recurring schedule as secondary text, such as “Closes on the 18th of each month.”

## Continue to payment plans

Add a clear next-step panel below the saved cards:

Heading: **Done adding your cards?**

Description: “Add your Klarna, Afterpay, and Sezzle plans and connect each plan to the card it will be charged to.”

Primary action: **Add Payment Plan**

Clicking **Add Payment Plan** should open the Add Payment Plan screen for the active profile. The card dropdown on that screen must contain the cards saved under the active profile.

Keep **Add Credit Card** available so the user can add additional cards at any time.

## Empty and populated states

- If there are no cards, show the existing Add Your First Credit Card state.
- If one or more cards exist, show the Stitch Credit Cards Overview with all saved cards.
- Show the Add Payment Plan next step only when at least one card exists.
- Keep cards isolated to their owning profile.

## Verification

Verify:

- Saving a card redirects to the Stitch-based overview.
- The success notification appears once.
- The saved card appears immediately.
- Resolved statement-closing and payment-due dates include the correct month and year.
- Month and year rollover follow the backend rules.
- Add Another Card opens an empty card form.
- Add Payment Plan opens the plan form.
- The plan form lists only cards belonging to the active profile.
- Refreshing preserves the cards without repeating the success notification.

Run the relevant frontend and backend checks, then summarize the files changed, date fields added to the API, and how to test the full flow locally.

## Clarification and outcomes

When asked whether to include complete plan saving, the user selected **Form and
card selector only**. Keep submission disabled with an explicit unsaved notice.
Reuse application billing helpers for schedule occurrences, including short-month
clamping. Dates are response-only, never persisted in the portable document. Use
one server date per request. Scroll to the top on navigation and use synchronous
history updates so a queued hash event cannot hide the save notification.
