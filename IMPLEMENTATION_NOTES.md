# Audience frontend merged fix

This package intentionally merges the working CSV import implementation with the newer Audience right-panel + View Members multi-select/delete design.

Frontend files included:
- frontend/src/components/audience/AudienceDetails.tsx
- frontend/src/App.css

Backend is not included and must not be changed.

CSV import remains available inside Add Members > Import CSV.
View Members remains a separate dialog with multi-select and Delete Selected.
