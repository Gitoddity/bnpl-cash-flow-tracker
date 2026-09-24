# Create Profile screen

Date: 2026-09-24

## User prompt

Implement the **Create Profile** screen in the existing DueMap React + Vite frontend, using the Google Stitch design as the visual reference.

- Stitch project ID: `6921387155947892246`
- Create Profile screen ID: `36f0f225698343c98d37859d1704f40d`

Keep the design’s layout and styling, with these copy updates:

- Description: “Create a profile to organize your credit cards and Klarna, Afterpay, and Sezzle plans.”
- Profile Name placeholder: “e.g., Personal, Household, Travel”
- Information box: **“No sign-up required.”** “Profiles are saved on this computer by the local server. Closing this tab won’t delete them. JSON export is coming later.”

**Behavior:** Clicking **Create New Profile** on the landing page opens this screen. On this screen, clicking **Create Profile** validates the name using the existing profile rules, saves the profile through FastAPI, makes it the active profile, and navigates to that profile’s empty state with a clear **Add Credit Card** action. Show validation errors beside the field without clearing what the user typed. **Back** returns to the landing page. **Import Profile** uses the existing import flow.

Preserve the working landing page and existing Streamlit app. Reuse the repository’s profile logic rather than creating a separate set of rules in React. Verify the create, validation, and navigation flow, then tell me what you changed and how to test it locally.

## Outcome

Dedicated screen replaces the dialog; scoped Stitch styles and exact copy. Existing
FastAPI profile operation owns all validation/persistence. Active profile is represented
in a hash route and restored from the profile list on reload. Empty state includes
Add Credit Card; card-entry implementation remains the next slice. Existing import
operation is shared by both screens. No backend or Streamlit behavior changes.

Validation: 10 frontend tests, production build, and 30 API/Streamlit tests pass.
Browser visual verification unavailable (no connected browser).
