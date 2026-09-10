# Sprint 0 validation

Validated on Windows on 2026-09-08. No Sprint 1 work was started.

| Check | Result |
| --- | --- |
| New independent directory | Created factory-network-management-v2 in the existing workspace; no old source read, imported or modified |
| Frontend dependency installation | Passed, pnpm 11.19.0; reproducible lockfile included |
| Lint | Passed, ESLint 10.10.0, no errors or warnings |
| Production build | Passed, Vite 7.3.6; 36 transformed modules |
| Output size | HTML 0.58 kB, CSS 20.02 kB, JavaScript 199.01 kB; gzip CSS 5.07 kB / JS 62.88 kB |
| Tailwind | Vite integration built; rendered flex and gap utilities checked in Edge |
| Backend installation | Passed in isolated .venv; exact transitive requirements.lock.txt included |
| Flask startup | Passed, loopback port 5050, debug off |
| Health contract | HTTP 200, exact status/application payload, both direct and via Vite proxy |
| Backend tests | 2 passed: health contract and absent business endpoint |
| Navigation | All six planned routes navigate to placeholders; Catalog included; active link semantics verified |
| Responsive layout | 1366×768, 1920×1080, 768×1024, 390×844, 320×740; no page-level horizontal overflow |
| UI Showcase | All sections rendered; desktop/mobile screenshots reviewed |
| Search | Input accepts text, leaves all three sample rows unchanged |
| Selection | No checkboxes normally; selection count, preview action and cancel/reset verified |
| Table | Empty state, row selection and visible View action verified |
| Dropdown | Opening, keyboard selection, disabled future actions and action feedback verified |
| Dialog | Confirmation, Cancel, Escape, Tab/Shift+Tab containment and focus restoration verified |
| Mobile navigation | Toggle and close-on-navigation verified; hidden sidebar excluded from keyboard navigation |
| Browser errors | No console or page errors in final run |
| Production boundary | Default Dashboard placeholder; Showcase route unavailable and sample strings absent from built JS |
| Git exclusions | node_modules, dist, .venv and validation artifacts ignored |
| Source footprint | 39 files, approximately 129 KiB including lockfiles/docs; dependencies, build output and artifacts excluded |

## Notes

- Port 5000 returned a different pre-existing API payload. V2 uses 5050 to leave that service untouched.
- Build tooling required the environment's approved execution outside its filesystem sandbox; no application workaround or absolute runtime path was added.
- Browser checks used environment-provided Playwright with installed Microsoft Edge. No Playwright dependency was added to the product. Temporary harnesses/screenshots are in ignored artifacts/ and excluded from source size.
- Font fallback was verified with SF Distant Galaxy absent. The actual font and its appearance can only be reviewed after the user supplies it.
- Glass uses subtle transparency/blur over a quiet surface; its effect is intentionally restrained.
- Native dialogs and modern CSS target current factory browsers. Other browser engines and assistive technology were not exhaustively tested.
- No production server, LAN deployment or packaging was implemented. Dependency installation requires internet or a prepared cache.
- Existing workspace Git metadata is reused; no nested repository, commit or tag was created automatically. Suggested approved milestone: sprint-0-foundation.

Review typography, density at 1366×768, rounded controls, neutral badges, glass cards, table View/Select behavior and keyboard focus before approving Sprint 1.
