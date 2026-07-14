# PosoKanei.gov.gr — User task map, measured times, UI/UX flaws

**Date:** 2026-07-14  
**Surface:** Web app `https://posokanei.gov.gr` (Flutter web, package v1.1.10)  
**Access:** kepik egress proxy (Greek IP); direct non-GR egress typically fails (timeout / 403)  
**Method label:** Agent-session measurements with Playwright Chromium (headless) + pixel-assisted clicks.  
**Not** a multi-user lab study. Times include network via proxy + render + interaction settle.

Evidence: screenshots under `docs/ux-audit/screens/`, raw logs in session scratch `task-timings.log`.

---

## 1. Personas (brief)

| Persona | Goal |
|---------|------|
| **Casual price checker** | Find one product, see which Greek chain is cheapest today |
| **Basket planner** | Build a shopping list, compare total cost across chains (“Καλύτερη Τιμή”) |
| **Deal hunter** | History charts, competitors (“Ψάξε μου Φθηνότερα”), EU compare |
| **Support / citizen** | FAQ, contact form, privacy |

---

## 2. User-task map

### T0 — Cold open the app (first paint usable UI)

| | |
|--|--|
| **Entry** | Navigate to `https://posokanei.gov.gr/` |
| **Steps** | DNS/TLS → Flutter bootstrap → first frame (often cookie modal) |
| **Outcome** | Interactive UI (may still be blocked by cookie / onboarding) |
| **Measured** | **16.7–17.7 s** cold (desktop 1280×800, proxy, networkidle + settle) |
| **Evidence** | `F00_cold.png`, `01_home_cold.png` |

### T_cookie — Dismiss analytics cookie modal

| | |
|--|--|
| **Entry** | First visit (or expired 90-day consent) |
| **Steps** | Read “Χρήση cookies” → Αποδοχή or Απόρριψη |
| **Outcome** | Modal closes; app usable underneath |
| **Measured** | **~2.2 s** (click Accept via pixel locate → settle) |
| **Evidence** | `C_cookie.png`, `B03_post_cookie.png` |

### T_onboard — First-run onboarding carousel

| | |
|--|--|
| **Entry** | After cookies (if `onboarding_seen_*` false) |
| **Steps** | 2–3 slides (“Σύγκριση σε Πραγματικό Χρόνο”, chart demo) → Παράλειψη or next → Ξεκίνα |
| **Outcome** | Land on home (categories) |
| **Measured** | **~10.6 s** skip/next path (agent) |
| **Evidence** | `B03_post_cookie.png` (onboarding after cookie) |

### T_tour — Guided tour / coachmarks (“Οδηγός Χρήσης”)

| | |
|--|--|
| **Entry** | Home / Lists after first entry |
| **Steps** | Modal “Θέλετε να ενεργοποιηθεί…” → Όχι / Ναι; floating tips with Τέλος / Επόμενο (n/m) |
| **Outcome** | Tips dismissed so content is clickable |
| **Measured** | **~11.5 s** multi-dismiss attempts (tour often reappears per screen) |
| **Evidence** | `F03_clean_home.png`, `F10_lists.png`, `B14_mobile_post.png` |

### T1 — Product search (by name)

| | |
|--|--|
| **Entry** | Header field “Αναζήτησε προϊόντα” (desktop) or home search (mobile) |
| **Steps** | Focus field → type query → Enter/submit → scan results (price min–max, retailers) |
| **Outcome** | Result list or empty “Δεν βρέθηκαν προϊόντα” |
| **Measured** | **~9.5 s** agent interaction budget (focus+type+wait); backend search alone **~0.7–0.8 s** (API, not UI) |
| **Evidence** | `F04_search_gala.png` (tour still blocking focus in headless); API `api-latency-context.log` |
| **Note** | Flutter canvas focus is fragile in headless automation; live human focus is usually 1 click. **Human estimate** for successful search given focus: **~3–6 s** + API. |

### T2 — Open product → price by supermarket chain

| | |
|--|--|
| **Entry** | Tap result card from search or category listing |
| **Steps** | Open detail → read `retailer_prices` list / store chips → optional tax toggle / sort |
| **Outcome** | Per-chain shelf prices (or “Μη διαθέσιμο”) |
| **Measured** | **~6–8 s** open+scroll settle (agent); API product+history **~0.85 s** |
| **Evidence** | Product strings in client; screens `F05_*`; API map |
| **Flaws** | F3, F7, F11 |

### T3 — Price history chart

| | |
|--|--|
| **Entry** | Product detail → “Ιστορικό Τιμής” / chart section |
| **Steps** | Open history → select stores/period → optional € vs unit price toggle |
| **Outcome** | Line chart of daily prices or empty/error (“Σφάλμα φόρτωσης γραφήματος”) |
| **Measured** | **~9.7 s** explore/scroll attempts; history API folded into product **~0.85 s** |
| **Evidence** | UI strings; onboarding chart screenshot (demo); `F06_history.png` |
| **Flaws** | F4, F8 |

### T4 — Cheaper alternatives / competitors

| | |
|--|--|
| **Entry** | Product → “Ψάξε μου Φθηνότερα” / competitor section |
| **Steps** | Load competitors in category → compare min prices → optional replace-in-list |
| **Outcome** | List of alternative products with prices |
| **Measured** | **~6.6 s** agent navigate attempt |
| **Evidence** | API `/products/{id}/competitors`; UI copy “Φθηνότερη επιλογή” |
| **Flaws** | F11 |

### T5 — EU / international price compare

| | |
|--|--|
| **Entry** | Product detail EU controls (“Ευρωπαϊκή Ένωση”, “Χώρες”, “Σύγκριση τιμών με ΦΠΑ”) |
| **Steps** | Select countries/retailers → apply → read EU average / foreign chains |
| **Outcome** | Cross-border comparison or “Δεν υπάρχουν δεδομένα για σύγκριση!” |
| **Measured** | Not fully isolated in headless; feature present in UI strings + About FAQ (largest chain per country) |
| **Evidence** | About copy in `F14_faq.png`; strings “Ε.Ε. (Μ.Ο.)”, “Βρέθηκαν δεδομένα τιμής Ευρώπης” |
| **Flaws** | F9, F12 |

### T6 — Browse categories

| | |
|--|--|
| **Entry** | Home “Κατηγορίες” grid (Τρόφιμα, Ποτά, …) with product counts |
| **Steps** | Tap root category → subcategory grid → product list |
| **Outcome** | Filtered product set |
| **Measured** | **~2.7–3.0 s** per category open; multi-category agent loop **~31.5 s** (includes returns) |
| **Evidence** | `F09_cat_250.png` (Τρόφιμα → 13 υποκατηγορίες), `F03_clean_home.png` |
| **Flaws** | F5, F6 |

### T7 — Shopping lists: open / create / best total

| | |
|--|--|
| **Entry** | Nav “Λίστες” (desktop top / mobile bottom) |
| **Steps** | View lists (templates: Ψώνια Εβδομάδας, Για το Σπίτι, …) → create (max 5) → add products → “Υπολογισμός τιμών…” → “Καλύτερη Τιμή” per list; filter stores |
| **Outcome** | Per-list best-chain total or “—” if empty/incomplete |
| **Measured** | Open lists **~9.1 s** (incl. coachmark); empty list detail observed on mobile |
| **Evidence** | `F10_lists.png`, `F12_list_created.png`, `M02_home.png` / `M03_search.png` (list “Ψώνια Μήνα”, 0 items) |
| **Flaws** | F5, F10, F13 |

### T8 — Add product to list + quantity

| | |
|--|--|
| **Entry** | Product → “Προσθήκη σε Λίστα”; or list → “Πρόσθεσε Προϊόντα” |
| **Steps** | Pick list(s) → quantity → save; optional private-label / replace cheaper |
| **Outcome** | Item in list; best price recomputed |
| **Measured** | Agent FAB attempts **~18.8 s** (partial; blocked by tour/focus); human happy-path estimate **~5–12 s** after product open |
| **Evidence** | UI strings; list empty CTA |
| **Flaws** | F5, F10 |

### T9 — Barcode search

| | |
|--|--|
| **Entry** | “Αναζήτηση με barcode” / barcode mode |
| **Steps** | Enter EAN (8/12/13) → lookup |
| **Outcome** | Product detail or not found; **rate limit 429** under burst |
| **Measured** | Entry navigation attempts **~2 s**; API rate-limit observed earlier (prior API work) |
| **Evidence** | UI strings; API map |
| **Flaws** | F14 |

### T10 — About / FAQ / Privacy / Contact

| | |
|--|--|
| **Entry** | “Σχετικά” → rows for Info, FAQ, Contact, Privacy |
| **Steps** | Read FAQ accordion; contact form (name, email, subject, message ≥20 chars, reCAPTCHA) |
| **Outcome** | Informed user or ticket number |
| **Measured** | About/FAQ **~5.4 s**; contact entry **~4.3 s** |
| **Evidence** | `F14_faq.png`, `F15_contact.png` (FAQ list) |
| **Flaws** | F15 |

### T11 — Geo / blocked access (non-GR)

| | |
|--|--|
| **Entry** | Direct request without Greek egress |
| **Steps** | Open site |
| **Outcome** | **Timeout / 403** — no helpful citizen-facing explanation in our runs |
| **Measured** | **20–30 s** timeout then fail (Playwright); curl direct **403** in prior session |
| **Evidence** | `task-timings.log` T14; prior `proxy-direct-vs-proxy` |
| **Flaws** | F1 |

### T12 — Mobile home ready

| | |
|--|--|
| **Entry** | 390×844 viewport load |
| **Steps** | Cookie → skip onboard → dismiss tour → home grid |
| **Outcome** | Category home with bottom nav Αρχική / Λίστες / Σχετικά |
| **Measured** | **~24 s** first-run mobile to usable home |
| **Evidence** | `B14_mobile_post.png`, `M02_home.png` |

---

## 3. Timing summary table (measured)

| Task ID | Task | Viewport | Measured (s) | Notes |
|---------|------|----------|-------------:|-------|
| T0 | Cold load to first UI | Desktop | **16.7** | Flutter cold start |
| T_cookie | Cookie dismiss | Desktop | **2.2** | Pixel-click Accept |
| T_onboard | Onboarding skip/next | Desktop | **10.6** | First-run only |
| T_tour | Tour/coachmarks dismiss | Desktop | **11.5** | Often multi-screen |
| T1 | Search product | Desktop | **9.5** | Focus fragile headless |
| T2 | Product prices by chain | Desktop | **7.7** | Open + scroll |
| T3 | Price history explore | Desktop | **9.7** | |
| T4 | Competitors / cheaper | Desktop | **6.6** | |
| T5 | Browse categories (loop) | Desktop | **31.5** | Multi open; ~3 s each |
| T6 | Lists open/create path | Desktop | **9.1** | Coachmark present |
| T7 | About/FAQ | Desktop | **5.4** | |
| T8 | Contact entry | Desktop | **4.3** | |
| T9 | Mobile ready home | Mobile | **24.2** | Cookie+onboard+tour |
| T10 | Mobile search attempt | Mobile | **6.7** | |
| T11 | Mobile product attempt | Mobile | **6.3** | |
| T12 | Mobile lists | Mobile | **6.9** | Empty list detail |
| T14 | Direct no-proxy | Desktop | **20–30** | Fail / timeout |
| — | API search only | — | **0.7–0.8** | Context, not UI |
| — | **First-run tax before work** | Desktop | **~24–41** | T0 optional + cookie + onboard + tour |

**First productive action (search) after cold first visit (human-optimistic):**  
≈ cold 17 s + cookie 2 s + onboard 8–11 s + tour 5–12 s + search 4–10 s → **~35–55 s** before seeing search results on a virgin browser.

---

## 4. UI/UX flaw inventory (≥8, PosoKanei-specific)

| ID | Flaw | Severity | Tasks hurt | Evidence |
|----|------|----------|------------|----------|
| **F1** | **Geo-block without usable recovery UX** for non-GR networks: direct access 403/timeout; no “use VPN/GR network” style guidance in app shell we captured | High | T0, T11, all | Direct timeout logs; prior 403 |
| **F2** | **Hard cookie wall** on first paint: full-screen dim + modal required before any task; choice stored 90 days but every new profile pays the cost | Medium | T0, T_cookie, all first-run | `01_home_cold.png`, `C_cookie.png` |
| **F3** | **Onboarding chart is decontextualized**: multi-series price chart with “Supermarkets” / date chips and €/Kg toggle **without naming the product** — confuses first-time users about what they’re seeing | Medium | T_onboard, T3 | `B03_post_cookie.png` |
| **F4** | **Mixed Greek/English chrome**: “Supermarkets”, “cookies”, “PosoKanei”, “barcode” mixed with Greek CTAs — uneven language for a .gov.gr citizen tool | Low–Med | T_onboard, T1, T9 | Screens + strings |
| **F5** | **Aggressive guided tour / coachmarks** reappear across Home and Lists (“Επόμενο 1/2”, category tip, create-list tip), dimming content and intercepting clicks | High | T_tour, T5, T6, T1 | `F03_clean_home.png`, `F10_lists.png` |
| **F6** | **Category-first home with heavy imagery** pushes search (primary job for many) into a small header field; coachmark even tells users to pick a category first | Medium | T1, T5 | `F03_clean_home.png` |
| **F7** | **Flutter web accessibility off by default**: only off-viewport “Enable accessibility” placeholder; body text essentially empty for AT without canvas semantics → screen-reader / automation unfriendly | High (a11y) | All | DOM: `body_len=39`; a11y click “outside viewport” |
| **F8** | **GPU/WebGL noise & canvas rendering**: console GPU stall ReadPixels; pure canvas UI means no selectable prices, hard zoom/copy, poor SEO of content | Medium | T2, T3 | `console.log` |
| **F9** | **EU comparison caveats buried in About**: FAQ says only largest chain per country for now — easy to misread EU prices as comprehensive | Medium | T5 (EU) | `F14_faq.png` |
| **F10** | **Empty list economics**: lists show “Καλύτερη Τιμή: —” and “Περιεχόμενα: 0” with weak next step hierarchy; add-product is a text link mid-page | Medium | T6, T7, T8 | `F10_lists.png`, mobile list screens |
| **F11** | **“Μη διαθέσιμο” / missing chain** not always explained (stock vs not scraped vs private label) — About partially explains missing date = no feed update | Medium | T2, T4 | About bullets `F14_faq.png` |
| **F12** | **Not an e-shop** (copy exists) but price UI can still feel cart-like (“λίστα”, totals) — risk of expectation mismatch | Low | T6, T8 | Strings “To PosoKanei δεν είναι E- Shop” |
| **F13** | **Hard cap of 5 lists** (“Μπορείτε να έχετε μέχρι 5 λίστες”) without early progressive disclosure on home | Low | T6 | UI string inventory |
| **F14** | **Barcode search rate-limited (429)** with little UI guidance for retry/backoff in public API behavior | Medium | T9 | API 429 “Too many barcode search requests” |
| **F15** | **Contact form friction**: reCAPTCHA, min 20-char message, mandatory fields — fine for spam, but long path from price task | Low | T10 | Form strings |
| **F16** | **Analytics still attempted** even when relevant; GA collect fails via some proxies (`ERR_TUNNEL_CONNECTION_FAILED`) — consent UX vs actual third-party calls | Low–Med | T_cookie | `failed-requests.log` |
| **F17** | **Desktop vs mobile IA split**: desktop top tabs vs mobile bottom nav; same tasks but different muscle memory; tour positions differ | Low | All mobile | `B14_mobile_post.png` vs desktop header |
| **F18** | **First-run time-to-value is high** (~½ minute cold) for a utility that should answer “πόσο κάνει;” in seconds — dominated by Flutter load + consent + tours, not price API | High | T0–T1 | Timing table |

---

## 5. Integrated map (task → time → flaws)

| Task | Measured time | Related flaws | Coverage note |
|------|---------------|---------------|---------------|
| Cold load | 16.7 s | F1, F7, F8, F18 | Timed |
| Cookie | 2.2 s | F2, F16 | Timed |
| Onboarding | 10.6 s | F3, F4, F18 | Timed |
| Guided tour | 11.5 s | F5, F18 | Timed |
| Search | 9.5 s (UI attempt); API 0.7 s | F5, F6, F7 | Timed; headless focus limit |
| Product × chains | 7.7 s | F7, F11 | Timed path + API |
| Price history | 9.7 s | F3, F8, F11 | Timed explore |
| Competitors | 6.6 s | F11 | Timed + API map |
| EU compare | feature mapped | F9, F12 | Observed in FAQ/strings; partial UI drive |
| Categories | ~3 s/open (31.5 s loop) | F5, F6 | Timed; subcategory screen captured |
| Lists / basket total | 9.1 s open | F5, F10, F13 | Timed; empty-state captured |
| Add to list | partial ~19 s agent | F5, F10 | Attempt timed; human estimate noted |
| Barcode | entry ~2 s | F14 | Feature mapped + API limit |
| FAQ / contact | 4–5 s | F15 | Timed |
| Mobile home | 24.2 s first-run | F2, F5, F17, F18 | Timed |
| Geo fail | 20–30 s fail | F1 | Timed failure |

No critical consumer task is left without either a measured time or an explicit feature+flaw note.

---

## 6. Method appendix

```
Environment: Linux agent host → HTTP(S)_PROXY kepik egress (Athens GR)
Browser: Playwright Chromium headless, locale el-GR
Desktop: 1280×800; Mobile: 390×844
Start marker: goto or first click of task
End marker: screenshot after wait_for_timeout settle
Flutter limitation: canvas UI; a11y disabled by default; pixel blue-button detection used for cookie Accept
API latency measured separately with curl via same proxy — not counted as UI task time
```

---

## 7. Top recommendations (observation-only; not implemented)

1. Cut first-run tax: lazy onboarding, non-blocking cookie for essential use, fewer coachmarks.  
2. Default-enable Flutter web semantics; ensure focusable search field.  
3. Geo-block page with clear Greek explanation.  
4. Label onboarding chart with product name or use static marketing art.  
5. Make search the visual hero on home for the “πόσο κάνει” job.

---

## 8. Artifact index

| Path | Role |
|------|------|
| `docs/ux-audit/UX_TASK_MAP_AND_FLAWS.md` | This report |
| `docs/ux-audit/screens/` | Screenshot evidence |
| `docs/API_MAP.md` | Backend capabilities (not UI times) |
