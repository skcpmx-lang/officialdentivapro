# Dentiva Pro — Database Design (v1.0, Phase 1)

Design contract for Phase 3 implementation (REQ-DB-01..04, REQ-DATA-*, ADR-003/004/005).
Conventions unless stated otherwise:

- `id INTEGER PRIMARY KEY` (rowid alias). All FKs to `id`.
- **Instants** = `INTEGER` epoch-milliseconds UTC (`*_ms`). **Human timestamps** in documents/audit = ISO-8601 UTC TEXT `Z` (CHECK format).
- **Money** = `INTEGER` poisha with `CHECK (col >= 0)` where negatives are illegal (adjustments use explicit sign columns).
- **Statuses/enums** = TEXT with `CHECK (col IN (...))` — domain lists below are the spec; implementation may use integer affinity codes only if a migration perf need is proven (not expected).
- Soft delete: `status IN ('active','archived')` (+`deleted_at_ms` where hard-delete-adjacent flows need tombstones). Never silent row removal on clinical/financial data.
- `created_at_ms/created_by`, `updated_at_ms/updated_by` on mutable business tables.
- All user text: TEXT UTF-8, NFC at intake (REQ-LOC-03). FKs `ON DELETE RESTRICT` except owned children (`CASCADE` marked ⤵ below).
- Naming: snake_case; join tables `<a>_<b>`.

## 1. ER overview (primary chain)

```
users ─┬─< sessions* (audit only)            dentists ─┬─ dentist_designations ⤵
       │                                               └─ dentist_certifications ⤵
roles ─┼─ role_permissions / user_grants      staff ─1..0?─ users (linkable)
       │
       ├─ patients ─┬─ patient_phones ⤵      visits ─┬─ visit_findings (role=cc/oe/re) ⤵
       │           ├─ attachments>files      │       ├─ visit_treatments ⤵ (chart_findings refs)
       │           ├─ notes ⤵                │       ├─ tooth_findings ⤵ → chart_tooth_conditions
       │           ├─ appointments >patients │       ├─ prescriptions ─ prescription_items ⤵
       │           ├─ invoices ─┬─ invoice_items ⤵ → treatments (ref) + snapshot
       │           │            └─ payments (ledger)
       │           ├─ referrals              └─ audit: every txn appends audit_log (hash-chained)
       │           ├─ timeline: computed projection (not stored)
       ├─ inventory: suppliers, stock_items, stock_movements (>stock_items)
       ├─ accounting: accounting_categories, accounting_entries (>staff? for salary)
       ├─ notifications (per user, dedup_key)          print_profiles (>settings)
       └─ sequences / settings / meta / activation      backup_history
```

## 2. Meta & configuration

| Table | Columns (key) | Notes |
|---|---|---|
| `meta` | `key PK, value_json, updated_at_ms` | singleton-ish KV: `schema_revision`, `setup_completed_at`, `activation{install_id, fingerprint_hash, ts, product_tag_hash}`, `shutdown_clean_flag`, `db_origin_machine`. Activation record kept here (documented location; REQ-ACT-05). |
| `settings` | `key PK, value_json, value_type CHECK('str','int','bool','json','money','date'), updated_at_ms, updated_by` | Typed store; registry defines each key's schema/default (REQ-DATA-03). |
| `print_profiles` | `id, name, doc_type CHECK('prescription','invoice','report'), printer_name NULL, paper_key CHECK('A4','A5','80mm','58mm','custom'), width_mm, height_mm, orientation, margin_mm_json, scale_pct, is_default, active` | REQ-SET-04; resolution order doc default → profile table `is_default` → system. |
| `sequences` | `name PK (invoice_no_yyyy, cn_no_yyyy, credit_note_yyyy, patient_code, rx_no, visit_no), next_value` | Gapless for legal docs (invoice numbers); patient code gaps tolerated but never reused (REQ-PAT-02). Allocation inside the same UoW txn as the document (REQ-BILL-*/REQ-TXN). |
| `clinic` | `id PK=1 CHECK(id=1), name, address_lines, phone_primary, phone_alt, email, footer_message, availability_text, currency_symbol, digit_style, date_format, logo_file_id FK→files ON DELETE SET NULL` | Single clinic per install (CONFLICT-C2) — CHECK pins the singleton *by design*, unlike forbidden singletons elsewhere (REQ-PROD-07 concerns operational entities). |
| `clinic_working_hours` | `id, clinic_id FK ⤵, weekday 0-6, open_min, close_min, slot_minutes, enabled` | Clinic hours drive appointment UX (REQ-DATE-03). |
| `dentists` | `id, full_name, preferred_title NULL, phone NULL, email NULL, signature_notes NULL, gender NULL, active` | REQ-SETUP-02; referenced by visits/appointments/rx (RESTRICT). |
| `dentist_designations` / `dentist_certifications` | `id, dentist_id FK ⤵ CASCADE, text, sort` | Multi-value relational (REQ-DB-04 forbids CSV). |

## 3. Identity: users, staff, roles

| Table | Key columns | Notes |
|---|---|---|
| `staff` | `id, full_name, department, role_title, dob_ms NULL, gender, address, blood_group CHECK(A+/A-…/unknown), nid_number NULL (len-checked), photo_file_id FK SET NULL, employment_status('active','inactive','resigned'), joined_on_ms, notes, created/updated` | REQ-STAFF-01; salary NOT here (financial isolation) → `staff_salary`. |
| `staff_salary` | `id, staff_id FK ⤵, amount_poisha CHECK>=0, period TEXT 'YYYY-MM', paid_on_ms NULL, method_id FK payment_method NULL, note` | `finance.view`-gated (REQ-STAFF-03); REQ-ACC-03. |
| `users` | `id, username UNIQUE COLLATE NOCASE, display_name, password_hash (PHC text), status('active','disabled'), staff_id FK NULL UNIQUE, must_change_password, failed_count, locked_until_ms, created/updated` | REQ-AUTH-*/REQ-STAFF-02. |
| `roles` | `id, name UNIQUE, description, builtin BOOL, active` | 5 built-ins seeded (REQ-RBAC-02). |
| `permissions` | `id, code UNIQUE, module, description, risk_level('normal','sensitive','critical')` | Catalog frozen in §9. |
| `role_permissions` | `(role_id, permission_id) PK` | |
| `user_role` | `user_id PK FK, role_id FK` | exactly one base role per user (service-enforced; simple and testable). |
| `user_grants` | `id, user_id FK ⤵ CASCADE, permission_id FK, effect('grant','revoke'), UNIQUE(user_id,permission_id)` | overrides (REQ-RBAC-02). |
| `grants_version` | `singleton int` | bumped on any authz-relevant change → session invalidation (REQ-RBAC-06). |
| `sessions_audit` | `id, user_id, ts_ms, event('login','logout','lock','unlock','lockfail','stepup_ok','stepup_fail'), ip_machine` | auth events (REQ-AUTH-02); no tokens. |

## 4. Patients & clinical

| Table | Key columns | Notes |
|---|---|---|
| `patients` | `id, code UNIQUE ("DVP-000123"), full_name, name_bn NULL, gender('male','female','other','unknown'), dob_ms NULL, age_years_manual NULL (mutually-exclusive CHECK with dob), age_asof_ms (stored when manual), blood_group, address TEXT, note_current_complaint, note_history TEXT, referred_by_name NULL, status('active','archived'), photo_file_id FK SET NULL, created_at/by, updated_at/by` | REQ-PAT-03; DOB-or-age rule CHECK; `age_asof` keeps manual ages honest (REQ-DATE-*). |
| `patient_phones` | `id, patient_id FK ⤵ CASCADE, label('mobile','home','office','emergency','other'), phone TEXT (validated at service), is_primary, UNIQUE(patient_id,label,phone)` | REQ-PAT-03; list/search joins index `phone`. |
| `files` | `sha256 HEX PK(64), size_bytes, mime, ext, created_at_ms, created_by, deleted_at_ms NULL` | Content-addressed store (ADR-013). |
| `attachments` | `id, file_id FK RESTRICT, owner_type CHECK('patient','visit','expense','invoice','staff','referral'), owner_id, original_name, caption NULL, thumb BLOB NULL, status('linked','removed'), created_at/by` | REQ-ATT-*; per-owner UNIQUE(file_id, owner_type, owner_id) dedupe reference. |
| `patient_notes` | `id, patient_id FK ⤵, body, kind('note','complaint_history','advice'), author_user_id, visit_id NULL FK, supersedes_id NULL FK(self), created_at_ms` | versioned append chain (REQ-DATA-10). |
| `appointments` | `id, patient_id FK RESTRICT, dentist_id FK RESTRICT, start_ms, end_ms, status CHECK('scheduled','confirmed','arrived','in_progress','completed','cancelled','rescheduled','no_show'), purpose, note NULL, created/updated, cancel_reason NULL, rescheduled_from_id NULL FK(self)` | REQ-APPT-*; transition rules in service (REQ-APPT-02); `appointment_events` append table for history (`(id, appointment_id ⤵, ts_ms, from_status, to_status, actor, note)`) — attended/missed auditing without overwrite. |
| `appointment_reschedule_history` folded into `appointment_events` | | |
| `queue_entries` | `id, patient_id FK RESTRICT, dentist_id FK NULL, appointment_id FK NULL, priority int, entered_ms, left_ms NULL, completed_ms NULL, status('waiting','in_room','called','seen','left'), note` | REQ-QUEUE-*; deterministic order `priority, entered_ms`; DB-backed always (REQ-QUEUE-03). |
| `visits` | `id, visit_no UNIQUE, patient_id FK RESTRICT, dentist_id FK RESTRICT, appointment_id FK NULL, attended_on_ms, cc TEXT (free), oe TEXT, re_advice TEXT, status('draft','finalized','amended'), finalized_at_ms NULL, finalized_by NULL, doc_version INT default 0, snapshot_json TEXT NOT NULL DEFAULT '{}'` | REQ-VISIT-*; snapshot at finalize (REQ-DATA-05). C/C & O/E also as structured findings rows. |
| `visit_findings` | `id, visit_id FK ⤵ CASCADE, role CHECK('cc','oe','re_advice'), entry_id FK clinical_entries NULL, text_free NULL, sort` | one row may be NULL-entry (free text) or entry-ref — CHECK exactly-one (REQ-VISIT-02, REQ-DB-04). |
| `clinical_categories` | `id, key UNIQUE('complaint','exam_finding','advice','rx_note'), label` | |
| `clinical_entries` | `id, category_id FK RESTRICT, label, description NULL, active BOOL, sort` | seeded with the master-prompt terminology (REQ-CLINLIB-01); archive-protect (REQ-CLINLIB-04). |
| `chart_tooth_conditions` | `id, code UNIQUE('caries','restored','missing','extracted','crack','fracture','mobile','impacted','crowned','implant-planned','sensitivity','pocket','calculus','other'), label, color_token, glyph, severity_default, active` | legend configurable (REQ-CHART-04). |
| `chart_tooth_states` | `id, visit_id FK RESTRICT, patient_id FK, fdi INT CHECK range (51..55,61..65,71..75,81..85,11..18,21..28,31..38,41..48 — CHECK via (fdi/10) IN (1,2,3,4,5,6,7,8) AND (fdi%10) IN (1..8) + adult excludes >8), dentition('adult','primary'), surface_mask INT (bits O,M,D,B,L), condition_id FK, note NULL, found_on_ms` | **episodic findings** (REQ-CHART-02/03): insert-only per visit; current-status = latest per (patient,fdi,surface) derived view `v_chart_current`. Status-per-tooth treatment states (planned/in-progress/completed) live in `visit_treatments` (REQ-CHART-05). |
| `treatment_catalog` | `id, name, category, description NULL, default_price_poisha CHECK>=0, active, sort, archived_at NULL` | REQ-TREAT-*; price changes never touch invoice lines (snapshot below). |
| `visit_treatments` | `id, visit_id FK ⤵ CASCADE, catalog_treatment_id FK RESTRICT NULL, name_snapshot, qty INT CHECK>=1, tooth refs via child `visit_treatment_teeth(visit_treatment_id, fdi)` (no CSV — REQ-DB-04), status('planned','in_progress','completed'), note` | REQ-TREAT-02; performed-vs-planned status drives both chart UX and billing proposal. |
| `referrals` | `id, patient_id FK RESTRICT, direction('out','in'), to_name NULL, to_org NULL, reason, referred_on_ms, note, follow_up_due_ms NULL, follow_up_status('none','pending','done','overdue'), by_user` | REQ-DATA-08; timeline events. |

## 5. Prescriptions

| Table | Key columns | Notes |
|---|---|---|
| `prescriptions` | `id, rx_no UNIQUE, patient_id FK RESTRICT, dentist_id FK RESTRICT, visit_id FK NULL, created_at_ms, status('draft','finalized','amended','voided'), finalized_at/by, doc_version, snapshot_json (full print material incl. dentist designation/cert lines at time of finalization)` | REQ-RX-*, REQ-FINALIZE-01, REQ-DATA-05/06. |
| `prescription_items` | `id, rx_id FK ⤵ CASCADE, med_name, strength NULL ('500 mg'), form_id FK rx_options NULL, freq_morning/noon/night BOOL triple (canonical), freq_label NULL (custom text), food_relation CHECK('before','after','either',NULL), duration_days INT NULL, duration_note NULL ('1 week course'), instruction TEXT NULL, prn BOOL default 0, prn_condition TEXT NULL, sort` | REQ-RX-02/03. Booleans give exact semantics; label allows "2×night" custom — printer prefers label when set. |
| `rx_options` | `id, kind CHECK('form','frequency','food','advice_template'), label, active, sort` | REQ-FORMOPT-01 configurable lists. |

## 6. Billing ledger

| Table | Key columns | Notes |
|---|---|---|
| `invoices` | `id, invoice_no UNIQUE, patient_id FK RESTRICT, visit_id FK NULL, status('draft','finalized','voided'), doc_version, issued_at_ms, subtotal_poisha, discount_poisha, adjustment_poisha (signed), total_poisha, snapshot_json (patient/clinic blocks as printed), void_reason NULL, voided_at NULL` | **No `paid`/`balance` columns** — ledger-derived only (REQ-BILL-03/08, C10). Line-level discount via item column. |
| `invoice_items` | `id, invoice_id FK ⤵ CASCADE, catalog_treatment_id NULL FK, name, qty INT CHECK>=1, unit_price_poisha, line_total_poisha, tooth_fdis child `invoice_item_teeth`, source_visit_treatment_id NULL, note` | unit/line totals frozen at creation (REQ-TREAT-03). |
| `payments` | `id, invoice_id FK RESTRICT, patient_id FK RESTRICT, paid_at_ms, amount_poisha CHECK>0, method_id FK payment_method, tx_ref NULL, note NULL, received_by_user FK` | append-only ledger (REQ-BILL-05); void of payment = `reversal_of_id` row, not deletion. |
| `payment_methods` | `id, kind CHECK('cash','bank','card','mobile_wallet','other'), label UNIQUE, provider NULL('bKash','Nagad','Rocket','Upay','Bank','Other'), active, sort` | seeded (REQ-BILL-06). |
| `invoice_status` derived | view: `paid_poisha = SUM(payments.amount) WHERE invoice_id`, balance = total − paid; status derived thresholds | service computes; report SQL parity tested. |

## 7. Inventory & accounting

| Table | Key columns | Notes |
|---|---|---|
| `suppliers` | `id, name, phone, address, note, active` | |
| `stock_items` | `id, name, category, unit_label, supplier_id NULL FK, purchase_date_ms NULL, unit_cost_poisha NULL, min_level INT CHECK>=0, batch_no NULL, expiry_ms NULL, active/archived, created/updated` | REQ-INV-01. |
| `stock_movements` | `id, stock_item_id FK RESTRICT, kind CHECK('purchase','consume','adjust','waste','return'), qty_signed INT CHECK!=0, unit_cost_poisha NULL, supplier_invoice_ref NULL, batch_no NULL, expiry_ms NULL, reason NULL, occurred_ms, actor_user, stock_entry_id NULL FK (link to expense when REQ-INV-05), note` | append-only ledger; **current stock = cached column + recomputable** (`stock_items.current_qty` updated in same txn; periodic parity check in backup verification). |
| `accounting_categories` | `id, name UNIQUE, direction('income','expense'), seed_key NULL('rent','electricity','internet','equipment','salary','maintenance','misc'), active` | REQ-ACC-01. |
| `accounting_entries` | `id, occurred_ms, category_id FK RESTRICT, direction, amount_poisha CHECK>0, sign_applied via direction, description, payee NULL, staff_id NULL FK (salary), payment_method_id NULL, linked_stock_movement_id NULL UNIQUE, attachment via attachments owner, status('posted','voided'), reversal_of_id NULL, created/by` | REQ-ACC-02/03/05; voids via reversal rows (REQ-FINALIZE-01). Clinic revenue for reports = payments ledger (never re-entered). |

## 8. Operations: notifications, backups, audit, search

| Table | Key columns | Notes |
|---|---|---|
| `notifications` | `id, dedup_key UNIQUE, user_id FK (audience), severity('info','success','warning','danger'), title, body, route_type, route_id, created_ms, read_at NULL, dismissed_at NULL, valid_until_ms NULL` | per-user state (REQ-NOTIF-02); generation re-checks perms at insert time (REQ-NOTIF-03). |
| `notification_rules` | `id, key UNIQUE('appt_upcoming','appt_missed','stock_low','stock_expiry','receivable_outstanding','backup_due','backup_failed','restore_notice','system'), params_json, enabled, user_scope('all','finance_only','admins')` | REQ-NOTIF-01; user visibility derived from scope ∧ perms. |
| `backup_history` | `id, kind('manual','auto','pre-restore'), path, bytes, sha256, status('success','failed','partial'), started_ms, finished_ms, actor, message` | REQ-BKP-07. |
| `audit_log` | `seq INTEGER PRIMARY KEY, ts_iso, user_id NULL, action (catalog code), entity_type NULL, entity_id NULL, summary, detail_json, hash_prev, hash_cur` | append-only; UPDATE/DELETE blocked by triggers; chain per ADR-009. |
| `app_events` (in-app bus) | memory only | view invalidation; never persisted. |
| FTS5: `patient_fts`, `note_fts`, `doc_text_fts` | content='patients' style external-content tables; rowid=patient id; columns: name, code, phone (denorm for search), notes; synced via SQLAlchemy events (ADR-004) | REQ-PAT-05, REQ-SEARCH-01 (per-module readers use plain indexes where FTS is overkill). |

## 9. Permission catalog (stable codes; REQ-RBAC-01)

Modules & codes (full list ~40): `patient.read, patient.create, patient.edit,
patient.archive`; `appointment.read, appointment.create, appointment.update,
appointment.cancel`; `queue.manage`; `clinical.visit.create,
clinical.visit.finalize, clinical.visit.amend, clinical.chart.edit,
clinical.library.manage`; `rx.create, rx.finalize, rx.print`;
`treatment.manage`; `billing.invoice.create, billing.invoice.finalize,
billing.invoice.void, billing.invoice.print, billing.payment.record`;
`finance.view` (independent), `inventory.read, inventory.manage`;
`accounting.view, accounting.edit`; `staff.read, staff.manage`;
`user.manage, role.manage`; `settings.manage`; `backup.operate`;
`audit.read`; `report.view, report.print`; `ops.destructive`.
`risk_level`: critical = `ops.destructive, role.manage, user.manage, backup.operate (restore mode), finance.view grants/revocations`.

Role seeds (REQ-RBAC-02/04): Owner=all · Dentist=patient.\*,
clinical.\*, rx.\*, appointment.\*, queue.manage, report.view(+print),
billing.invoice.create, billing.payment.record — no finance.view ·
Front desk=patient.read/create/edit, appointment.\*, queue.manage,
billing.invoice.create, billing.invoice.finalize, billing.payment.record —
**no finance.view, no report.view** (the prompt's exact scenario, REQ-RBAC-04) ·
Billing clerk=finance.view, billing.\*, report.view, patient.read,
payments.print · Inventory=inventory.\*, staff.read(no salary), accounting.view.

## 10. Indexes (initial spec; verified by schema-conformance test)

`patients(created_at_ms)`, `patients(full_name)`, `patient_phones(phone)`,
`appointments(start_ms)`, `appointments(dentist_id,start_ms)`,
`appointments(patient_id,start_ms)`, `visits(patient_id, attended_on_ms)`,
`chart_tooth_findings(patient_id, fdi, found_on_ms)`,
`prescriptions(patient_id, created_at_ms)`, `invoices(patient_id,
issued_at_ms)`, `invoices(status)` (via derived CTE — index on
`payments(invoice_id, paid_at_ms)`), `payments(paid_at_ms)`,
`stock_movements(stock_item_id, occurred_ms)`, `stock_items(expiry_ms)`,
`stock_items(min_level)` partial, `accounting_entries(occurred_ms,
direction)`, `audit_log(seq)` PK, `notifications(user_id, read_at)`,
`files(sha256)` PK, `queue_entries(status, priority, entered_ms)`.
Plus FTS trigram off (unicode61 tokenizer, remove_diacritics 2 — BN safe).

## 11. Migration & versioning strategy (REQ-DB-03)

Alembic `env.py` bound to `meta.schema_revision` + `PRAGMA user_version`;
linear chain, forward-only post-release; every revision script idempotent-safe
rehearsal on fixture DBs in CI; "from each historical revision → head" job
(ADR-004). First revision `0001_initial` created in Phase 3 = this document's
tables; conformance test compares `sqlite_master` introspection to §2–§8
inventory (names, keys, CHECKs presence) — doc and DB cannot drift.

## 12. Seeds (created at setup completion, one transaction)

`clinical_categories` + terms (pain, G. caries, swelling, gum bleeding, bad
breath, sensitivity, caries, BDR, BDC, gingivitis, periodontal pocket,
periodontitis, pulpitis, impacted teeth, dry socket, attrition, erosion +
common additions) · `rx_options` forms (tablet, capsule, syrup, cream,
ointment, injection, drops, suppository, inhaler), frequencies (morning, noon,
night + combos + q-id labels), food relations · `payment_methods` (Cash,
Bank, Card, bKash, Nagad, Rocket, Upay, Other) ·
`accounting_categories` (rent, electricity, internet, equipment, salary,
maintenance, misc, other income) · roles & permissions · `notification_rules`
defaults · 3 print profiles (Rx A4, Invoice A4, Receipt 80mm) · treatment
catalog: **empty by design** (no fake records — REQ-PROD-06); clinic enters
its own.

## 13. Snapshot semantics (REQ-DATA-05; the historical/current split)

`snapshot_json` on every finalized document stores the full rendered payload:
patient block (name/age/gender/phone as of print), clinic block, dentist block
(designations/certs as lists at that time), charged lines (name + amount),
numbering, currency presentation flags. Amending a finalized document bumps
`doc_version` and writes a new snapshot version row inside
`amendments(doc_type, doc_id, version, snapshot_json, amended_by, ts)`; the
document row keeps current finalized snapshot pointer. Reprints use the stored
snapshot + `REPRINT` marker (REQ-FINALIZE-01). Master-data edits (phone,
designation, price, clinic address) only affect **future** documents — tested
per document type (REQ-PAT-11, REQ-RX-06, REQ-TREAT-03).

## 14. Deletion/cascade policy summary (REQ-DEL-02, REQ-DATA-07)

| Entity | Delete policy |
|---|---|
| Patient | archive default; hard delete only via `ops.destructive` + backup + cascade allowed to draft visits/notes/attachments; finalized clinical/billing rows RESTRICT → cannot vanish silently (archive blocks future use, keeps history) |
| Visit | drafts deletable; finalized → void/amend flow only |
| Invoice | drafts deletable; finalized → void (+reversing payments); payments never deleted (reversals) |
| Rx | as visit |
| Catalog/library items | inactivate (REQ-CLINLIB-04); no hard delete when referenced |
| Stock items | archive; movements immutable |
| Users | disable; delete only when no audit attribution? No — delete allowed for never-used accounts; otherwise disable (REQ-STAFF-04) |
| Staff | archive/resign |
| Attachments | soft remove; file prune utility (ADR-013) |

## 15. Open items (for Phase 3, not blockers)

Exact CHECK-list wording for status domains; FTS tokenization micro-tuning;
`v_chart_current` performance validation at 200k findings; index additions from
EXPLAIN reviews; Alembic split of seed vs structure revisions; possible
`amendments` partition if volume demands (not expected).
