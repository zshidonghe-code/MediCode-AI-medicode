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

## Scope boundary

HarmonyOS is a native review client and evidence-confirmation surface. It is an
independent client for the existing MediCode Agent API, not a second
implementation of the React web application.

| Capability | Native implementation |
|---|---|
| Local privacy gate | `entry/src/main/ets/service/LocalPrivacyGate.ets` checks common identity, phone, and ID-card patterns before upload. |
| Authentication | `entry/src/main/ets/service/AuthGateway.ets` signs in against the backend. |
| Review orchestration | `entry/src/main/ets/service/ReviewGateway.ets` calls create, advance, decision, event, and report routes. |
| Evidence decision | `entry/src/main/ets/pages/Index.ets` presents conflicts and records the operator's selected source. |
| Continuation state | `entry/src/main/ets/service/ContinuationState.ets` keeps recoverable task state for network or version errors. |
| Review report | `entry/src/main/ets/pages/Index.ets` renders the redacted summary, coding, risks, evidence, and event timeline returned by the Agent API. |

The backend remains responsible for NLP extraction, ICD coding, quality checks,
DRG grouping, and rejection-risk assessment. The HarmonyOS client does not claim
to replace coders, make unattended final coding decisions, or represent a
hospital production deployment. Competition materials should describe the
HarmonyOS contribution as the native privacy, evidence-confirmation, and
auditable review experience mapped above.
