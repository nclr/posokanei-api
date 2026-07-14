# PosoKanei.gov.gr — User task map, measured times, UI/UX flaws

**Date:** 2026-07-14 (revised after evidence audit)  
**Surface:** `https://posokanei.gov.gr` (Flutter web v1.1.10)  
**Access:** kepik egress proxy (Greek IP). Direct non-GR often 403/timeout.  
**Method:** Playwright Chromium headless; cookie Accept via pixel blue-button detection; coordinate navigation.  
**Success rule:** a task is timed only when the **outcome screenshot is unique** (MD5) and visually matches the claimed UI state. Failed attempts are not reported as task times.

Evidence files: `docs/ux-audit/screens/` (all unique MD5s).  
Machine timings: `docs/ux-audit/timings.json`, `docs/ux-audit/task-timings.log`.

---

## 1. Personas

| Persona | Jobs |
|---------|------|
| Casual price checker | Search or browse → see which chain is cheapest |
| Basket planner | Lists → add products → “Καλύτερη Τιμή” across chains |
| Deal hunter | History chart, competitors, EU filters |
| Citizen support | FAQ, contact, privacy |

---

## 2. User-task map (stable IDs)

### T0 — Cold open to usable home

| | |
|--|--|
| **Entry** | `https://posokanei.gov.gr/` |
| **Steps** | Load Flutter → cookie modal → Accept/Reject → onboarding (Παράλειψη/next) → home + optional usage-guide modal |
| **Outcome** | Category home with search header |
| **Measured** | **22.7 s** cold to home-with-tour; tour dismiss **+2.7 s** |
| **Evidence** | `T0_cold_cookie.png`, `T0_home_tour_modal.png`, `T0_home_clean.png` |

### T_cookie — Analytics cookie modal

| | |
|--|--|
| **Entry** | First visit |
| **Steps** | Read “Χρήση cookies” → **Αποδοχή** or **Απόρριψη** |
| **Outcome** | Modal closed (onboarding or home underneath) |
| **Measured** | **2.42 s** |
| **Evidence** | `T_cookie_onboarding.png` (post-Accept onboarding) |

### T_onboarding — Intro carousel

| | |
|--|--|
| **Entry** | After cookies if intro not seen |
| **Steps** | Slides with demo chart → **Παράλειψη** or next → home |
| **Outcome** | Home with categories |
| **Measured** | **3.63 s** (skip path after cookie) |
| **Evidence** | `T0_home_tour_modal.png` |

### T_tour — Usage guide / coachmarks

| | |
|--|--|
| **Entry** | Home (“Οδηγός Χρήσης”) or Lists tips |
| **Steps** | **Όχι, ευχαριστώ** / **Ναι, θέλω!**; later **Τέλος** / **Επόμενο** tips |
| **Outcome** | Unblocked home/lists |
| **Measured** | **2.71 s** (dismiss home guide) |
| **Evidence** | `T0_home_tour_modal.png` → `T0_home_clean.png` |

### T1 — Product search

| | |
|--|--|
| **Entry** | Search field “Αναζήτησε προϊόντα” |
| **Steps** | Focus → type query → submit → scan result cards (price, unit price, add-to-list) |
| **Outcome** | “Αποτελέσματα για …” grid |
| **Measured** | **5.8 s** (mobile 390×844; query `γάλα`) |
| **Evidence** | `T1_search_results_mobile.png` (12 of 268 products; prices 1.30€–14.73€) |
| **Note** | Desktop header search **did not accept keyboard focus** in headless Flutter; mobile path completed. |

### T2 — Product detail: price by supermarket chain

| | |
|--|--|
| **Entry** | Product card from category list or search |
| **Steps** | Open detail → read store cards (Καλύτερη Τιμή, € and €/unit) → optional sort/filter |
| **Outcome** | Per-chain shelf prices |
| **Measured** | **6.66 s** (category → product with multi-store panel) |
| **Evidence** | `T2_product_multi_chain_prices.png` (PUMMARO: Μασούτης 1.56€, ΣΥΝ.ΚΑ 1.64€, My Market 1.73€, ΑΒ 2.10€…); also `T2_product_detail_chain.png` (single-store honey example) |

### T3 — Price history chart

| | |
|--|--|
| **Entry** | Product → **Ιστορικό Τιμής** (button on detail) |
| **Steps** | Open chart → select stores/period |
| **Outcome** | Daily price chart or empty/error |
| **Measured** | **Not completed** in headless (button visible; chart UI not opened) |
| **Evidence** | Control visible on `T2_product_multi_chain_prices.png` / `T2_product_detail_chain.png` only |

### T4 — Cheaper alternatives / competitors

| | |
|--|--|
| **Entry** | Product competitors action (app string “Ψάξε μου Φθηνότερα”; API `/products/{id}/competitors`) |
| **Steps** | Load alternatives → compare |
| **Outcome** | Competitor product list |
| **Measured** | **Not observed** in this UI pass |
| **Evidence** | — (strings + API map only) |

### T5 — EU / international compare

| | |
|--|--|
| **Entry** | Product listing **EU** chip; product EU country tools (About: largest chain/country for now) |
| **Steps** | Toggle EU / select countries |
| **Outcome** | Cross-border prices or empty state |
| **Measured** | **Partial only** — EU chip on listing (`T6_product_list_prices.png`); full country panel not captured |
| **Evidence** | EU badge on product list screens |

### T6 — Browse categories

| | |
|--|--|
| **Entry** | Home “Κατηγορίες” tiles |
| **Steps** | Root (e.g. Τρόφιμα) → subcategories → product grid |
| **Outcome** | Product grid with prices |
| **Measured** | Root **3.09 s**; next subcategory **3.66 s** |
| **Evidence** | `T6_category_trofima.png`, `T6_subcategory.png`, `T6_product_list_prices.png`, `T6_product_list_honey.png` |

### T7 — Shopping lists / basket cost

| | |
|--|--|
| **Entry** | Nav **Λίστες** |
| **Steps** | View lists (templates) → open list → add products → see **Καλύτερη Τιμή** / store filter |
| **Outcome** | List detail; empty lists show **Καλύτερη Τιμή: —** |
| **Measured** | **10.63 s** open lists index (+ detail) |
| **Evidence** | `T7_lists_index.png`, `T7_list_detail_empty.png`, `T7_list_detail_mobile.png` |

### T8 — Add product to list

| | |
|--|--|
| **Entry** | Product **Προσθήκη σε Λίστα** or list CTA |
| **Steps** | Choose list → quantity → save |
| **Outcome** | Item in list; best price recomputed |
| **Measured** | **Not completed** as a timed path (button visible on product/list UI) |
| **Evidence** | Buttons on `T2_*` and `T6_product_list_*` |

### T9 — Barcode search

| | |
|--|--|
| **Entry** | Barcode mode (app strings) |
| **Steps** | Enter EAN → lookup (API rate-limit 429 under burst) |
| **Measured** | **Not driven** in UI this pass |
| **Evidence** | API map / prior API exercise |

### T10 — About / FAQ / Contact / Privacy

| | |
|--|--|
| **Entry** | **Σχετικά** |
| **Steps** | FAQ accordion, contact form, privacy |
| **Measured** | Prior session had FAQ/contact screens; re-verified as secondary (not re-timed in strict pass) |
| **Evidence** | Feature confirmed in nav chrome on all main screens |

### T11 — Geo-blocked access

| | |
|--|--|
| **Entry** | Direct request without Greek egress |
| **Outcome** | 403 / timeout — no helpful in-app recovery |
| **Measured** | **20–30 s** fail (earlier Playwright direct timeout) |
| **Evidence** | `task-timings` notes; prior direct curl 403 |

---

## 3. Timing summary (verified only)

IDs match §2.

| Task ID | Task | Viewport | Duration (s) | Evidence file |
|---------|------|----------|-------------:|---------------|
| T0 | Cold → home | 1280×800 | **22.7** | `T0_home_tour_modal.png` |
| T_cookie | Cookie Accept | 1280×800 | **2.42** | `T_cookie_onboarding.png` |
| T_onboarding | Intro skip | 1280×800 | **3.63** | `T0_home_tour_modal.png` |
| T_tour | Dismiss guide | 1280×800 | **2.71** | `T0_home_clean.png` |
| T1 | Search product | 390×844 | **5.8** | `T1_search_results_mobile.png` |
| T2 | Product × chains | 1280×800 | **6.66** | `T2_product_multi_chain_prices.png` |
| T3 | Price history chart | — | **—** | unobserved |
| T4 | Competitors | — | **—** | unobserved |
| T5 | EU compare | — | **partial** | EU chip on list |
| T6 | Categories root | 1280×800 | **3.09** | `T6_category_trofima.png` |
| T6b | Subcategory | 1280×800 | **3.66** | `T6_subcategory.png` |
| T7 | Shopping lists | 1280×800 | **10.63** | `T7_lists_index.png` |
| T11 | Direct no-proxy fail | 1280×800 | **20–30** | fail path |

**First-run tax (measured):** cookie + onboard + tour ≈ **8.8 s** after load, plus cold load **22.7 s** ≈ **~30 s** before a clean home ready for category browse.  
**Search (warm mobile):** **~5.8 s** to results.  
**Category → multi-store product:** **~3+3.7+6.7 ≈ 13–14 s** once home is clean.

Backend API search (not UI): ~0.7–0.8 s via same proxy (`api-latency-context.log`) — shows UI overhead dominates.

---

## 4. UI/UX flaw inventory (PosoKanei-specific)

| ID | Flaw | Severity | Tasks | Evidence |
|----|------|----------|-------|----------|
| **F1** | Geo-block without recovery copy for non-GR clients | High | T0, T11 | Direct timeout/403 |
| **F2** | Full-screen cookie wall before any product work | Medium | T_cookie, T0 | `T0_cold_cookie.png` / post-Accept onboard |
| **F3** | Onboarding chart shows multi-series prices **without product name** | Medium | T_onboarding | Onboarding screens |
| **F4** | Mixed EL/EN chrome (“Supermarkets”, “cookies”, “barcode”) | Low–Med | T0, T1 | Screens |
| **F5** | Usage guide + coachmarks block home/lists; multi-step dismiss | High | T_tour, T6, T7 | `T0_home_tour_modal.png` |
| **F6** | Category-first home; search is a thin header control | Medium | T1, T6 | `T0_home_clean.png` |
| **F7** | Flutter web a11y off by default; DOM text empty; headless focus brittle | High | T1 (desktop fail) | Desktop search failed; mobile worked |
| **F8** | Canvas UI: no selectable prices, hard for AT/automation | Medium | All | Flutter canvas |
| **F9** | EU comparison scope (largest chain/country) easy to over-read | Medium | T5 | About FAQ (prior); EU chip only |
| **F10** | Empty lists show **Καλύτερη Τιμή: —** with weak empty-state guidance | Medium | T7 | `T7_lists_index.png`, `T7_list_detail_*` |
| **F11** | “Missing store” not distinguished (out of stock vs no feed) on product cards | Medium | T2 | Single-store honey vs multi-store passata |
| **F12** | List/cart metaphors on a non e-shop | Low | T7, T8 | Copy elsewhere; list UX |
| **F13** | Max 5 lists (string in client) | Low | T7 | App strings |
| **F14** | Barcode API 429 under burst | Medium | T9 | API exercise |
| **F15** | Contact form reCAPTCHA + long message min | Low | T10 | App strings |
| **F16** | Analytics requests after consent UX (may fail via proxy) | Low | T_cookie | failed GA tunnels earlier |
| **F17** | Desktop top nav vs mobile bottom nav IA split | Low | All | Screens |
| **F18** | High time-to-value: ~30 s cold path before productive browse | High | T0–T2 | Timing table |
| **F19** | Product may show only one chain with large white space (sparse layout) | Medium | T2 | `T2_product_detail_chain.png` |
| **F20** | “Ιστορικό Τιμής” present but hard to hit / no feedback if chart fails | Medium | T3 | Button on product; chart not opened headless |

---

## 5. Integrated map (task → time → flaws)

| Task ID | Measured | Evidence unique? | Flaws |
|---------|----------|------------------|-------|
| T0 | 22.7 s | Yes | F1, F2, F5, F7, F18 |
| T_cookie | 2.42 s | Yes | F2, F16 |
| T_onboarding | 3.63 s | Yes | F3, F4, F18 |
| T_tour | 2.71 s | Yes | F5, F18 |
| T1 | 5.8 s mobile | Yes (`T1_search_results_mobile.png`) | F6, F7, F17 |
| T2 | 6.66 s | Yes (multi-chain product) | F8, F11, F19 |
| T3 | — unobserved | Control only | F20, F8 |
| T4 | — unobserved | No | (API only) |
| T5 | partial | EU chip on list | F9 |
| T6 / T6b | 3.09 / 3.66 s | Yes | F5, F6 |
| T7 | 10.63 s | Yes | F5, F10, F12, F13 |
| T8 | — not timed | Button only | F10 |
| T11 | 20–30 s fail | Fail path | F1 |

No timed task uses a duplicate screenshot of an unrelated state.

---

## 6. Method appendix

```
Environment: agent host → HTTPS_PROXY kepik egress (Athens GR)
Browser: Playwright Chromium headless, el-GR
Cookie: pixel-cluster primary blue button (Accept) at lower modal
Onboarding: Παράλειψη (top-right) + bottom next until screenshot >150KB
Tour: click left of bottom blue "Ναι" for "Όχι, ευχαριστώ"
Success: MD5(screenshot) changes and visual QA of outcome
Limitation: Flutter canvas; desktop search focus unreliable headless
```

---

## 7. What was wrong in the first draft (corrected)

- Several files shared one MD5 (home+coachmark) but were labeled search/product/history — **removed**.
- Durations for failed coordinate loops were **removed**.
- Task IDs in the timing table now **match §2**.
- History / competitors / full EU: marked **unobserved** unless a unique screen proves them.

---

## 8. Artifact index

| Path | Role |
|------|------|
| `docs/ux-audit/UX_TASK_MAP_AND_FLAWS.md` | This report |
| `docs/ux-audit/screens/*.png` | Unique visual evidence |
| `docs/ux-audit/timings.json` | Machine-readable verified times |
| `docs/ux-audit/task-timings.log` | Human-readable timing log |
| `docs/ux-audit/browser-limit.txt` | Flutter automation limits |
