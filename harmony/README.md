# MediCode Harmony Review Agent

Native ArkTS/ArkUI client for the HarmonyOS Agent innovation track. It keeps
redaction and the human evidence decision on-device, then calls the MediCode
review Agent API for coding, quality checks, and the audit package.

The project deliberately uses only HarmonyOS SDK kits. Configure the intranet
MediCode endpoint and sign in as an operator before creating a review task. Do
not enter raw patient identity data: the local privacy gate blocks common phone,
identity-card, and labeled-identity patterns before upload.

Expected backend routes:

- `POST /api/v1/agent/reviews`
- `POST /api/v1/agent/reviews/{id}/advance`
- `POST /api/v1/agent/reviews/{id}/decisions`
- `GET /api/v1/agent/reviews/{id}/events`
- `GET /api/v1/agent/reviews/{id}/report`

This source tree is intentionally independent from the existing React client.
Open `harmony/` in DevEco Studio after a HarmonyOS SDK is installed, select a
phone or tablet target, and build the `entry` module. The command-line build
requires `DEVECO_SDK_HOME` to point to the DevEco `sdk` directory and
`JAVA_HOME` to point to DevEco's bundled JBR.

The intended demonstration sequence is documented in `docs/DEMO_CHECKLIST.md`.
