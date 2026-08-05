git add -A && git commit -m "Sprint C1_C4: QR labels, ticket attachments, EULA acceptance, asset accept/decline" -m "
- C1: Asset QR label print page (/print/asset-labels) with multi-select, deep-link QR, print CSS @media
- C2: /api/tickets/[id]/attachments CRUD + TicketAttachments dropzone UI; TICKET/TICKET_ATTACHMENT ItemType values
- C3: EulaAcceptance table + acceptEulaCmd + EulaModal integrated into CheckoutAssetModal gate
- C4: /api/assets/[id]/accept-decline + AssetAcceptanceBanner for assigned user

Schema:
- Added EulaAcceptance model + sprint_c3_eula_acceptance.sql migration
- Extended ActionType (ACCEPTED/DECLINED pre-existing) and ItemType (TICKET, TICKET_ATTACHMENT)
" 2>&1 | Select-Object -Last 8