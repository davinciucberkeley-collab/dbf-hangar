---
id: davinci-openapi-v2
title: DaVinci public API v2 OpenAPI specification
authors: Celedon (DaVinci)
year: unknown
url: https://docs.davinci-app.com/openapi/davinci-public.v2.yaml
type: website
retrieved: 2026-11-24
verified: true
---

## Summary
Machine-readable spec for the DaVinci v2 REST API. Downloaded with curl on 2026-11-24 and read for route list, parameters, scopes and response descriptions. No DaVinci API call was made to produce this entry.

## Usable rules / numbers
- Routes used in this work: GET /api/v2/usage (scope usage:read); GET /api/v2/projects/{projectId}/tree (scope projects:read; branch as query, default main) (openapi.yaml ~lines 1141-1175, 2988, 3102).
- POST /api/v2/projects/{projectId}/sessions/{sessionId}/tools/invoke runs one tool, scope projects:write, description says it incurs no LLM charges (openapi.yaml ~lines 2988-2998).
- ProjectId may be compound {projectId}--{branchName} (openapi.yaml ~line 6693).
- Project delete is a soft delete: storage is released from the owner's balance; a system administrator can restore within a retention window (openapi.yaml ~lines 473-475).
- Usage totals are eventually consistent; check asOf before treating a total as final (openapi.yaml ~lines 3110-3115). Per-project usage route at ~line 3188.
- Accounting limits and balances are named as /api/v2/users/me/accounting (openapi.yaml ~line 109).
- A RateLimited response with Retry-After is defined (openapi.yaml ~lines 7406-7412). The per-minute range quoted in the DBF notes is not in this file.
- Tree reads show uncommitted state and support ETag / If-None-Match (openapi.yaml ~lines 1150-1160).

## How we could use it
Reference for the read-only GET calls and for the invokeTool scope. Feeds the cost and limit sections of davinci-api-facts.
