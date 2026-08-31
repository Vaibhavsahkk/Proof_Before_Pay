# Phase 4.10 — Premium Reviewer UI Architecture Specification

**Product Name:** Proof Before Pay  
**Positioning:** Evidence-Driven Pre-Payment Exception Investigator for Small Businesses  
**Design Philosophy:** Serious Fintech & Operations Grade (Mercury / Stripe / Ramp caliber) — *Not an AI Toy*.  
**Target User Experience:** Plain language, zero cognitive overhead. A small business owner should simply see:  
$$\text{Upload} \longrightarrow \text{Checking} \longrightarrow \text{Problem Found / Safe} \longrightarrow \text{Why?} \longrightarrow \text{What should I do?}$$

---

## 1. Executive Summary & User Personas

### 1.1 Target Personas

| Dimension | Persona A: Small Shop Owner ("Ramesh") | Persona B: Small Business Bookkeeper ("Sarah") |
| :--- | :--- | :--- |
| **Role & Context** | Owner/Operator of a retail hardware store with 15 suppliers. | Part-time AP accountant managing invoices for 3 local bakeries. |
| **Technical Expertise** | Non-technical. Uses WhatsApp, Excel, and banking apps. | Moderate. Uses QuickBooks / Xero, comfortable with CSVs. |
| **Accounting Depth** | Basic (knows total, tax, and bank account). | High (understands 3-way matching, POs, and GRNs). |
| **Primary Anxiety** | *"Am I paying for goods we never received? Is this supplier's bank account real?"* | *"Did we already pay this invoice last week? Did the supplier inflate prices?"* |
| **Time Budget** | < 60 seconds per invoice before authorizing a bank transfer. | 2–3 minutes per batch of daily invoices. |
| **Required Mental Model** | **Input:** Invoice & PO files $\rightarrow$ **Output:** Green/Red check with 1 plain-English action. | Clear audit breakdown showing exact discrepancies and source documents. |

---

## 2. Core User Flow & Information Hierarchy

```
┌──────────────────────────┐
│   1. CASE INTAKE SCREEN  │  Drag-and-drop evidence bundle or pick sample case
└─────────────┬────────────┘
              │  [Click "Review Payment"]
              ▼
┌──────────────────────────┐
│ 2. INVESTIGATION MONITOR │  Progressive 4-stage visual checklist (Real-time checks)
└─────────────┬────────────┘
              │  [Auto-transition on completion]
              ▼
┌──────────────────────────┐
│ 3. CLEAR RECOMMENDATION  │  Prominent Banner: PAY (Green) | HOLD (Amber) | INVESTIGATE (Blue)
└─────────────┬────────────┘
              ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. "WHY & WHAT TO DO" PANEL                                            │
│    • Plain English Finding: "Price is higher than purchase order"      │
│    • Action Box: "Contact Supplier to reissue invoice with $15 rate"   │
└─────────────┬──────────────────────────────────────────────────────────┘
              │
              ├───────────────────────────────┬───────────────────────────────┐
              ▼                               ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────┐   ┌───────────────────────────┐
│     EVIDENCE VIEWER       │   │    EXACT CALCULATIONS     │   │   AUDIT & FAILOVER LOG    │
│ Side-by-side PO vs Invoice│   │ 10 × $15 = $150 (PO $120) │   │ Timestamped tool traces   │
└───────────────────────────┘   └───────────────────────────┘   └───────────────────────────┘
```

---

## 3. Screen Map & UX Layouts

### Screen 1: Home / Case Intake Screen (`/`)
* **Hero Banner**:
  * Title: *"Proof Before Pay"*
  * Subtitle: *"Verify supplier invoices against purchase orders and bank details before releasing funds."*
* **Upload Zone**:
  * Clean, bordered drop-zone supporting JSON / PDF / Scanned Bundles.
  * Drag-and-drop state with subtle accent border on hover.
* **Quick Demo Cards**:
  * Quick-launch buttons for public test cases:
    * `Case 001: Clean Invoice` (Expected: Safe to Pay)
    * `Case 002: Duplicate Invoice` (Expected: Payment Hold)
    * `Case 004: Price Contradiction` (Expected: Payment Hold)
    * `Case 005: Bank Account Change` (Expected: Verification Needed)
* **Primary Action**: Prominent high-contrast button $\rightarrow$ `[ Review Payment ]`.

---

### Screen 2: Investigation Workspace & Result Screen (`/investigate/:case_id`)
Structured into 3 clear vertical zones:

#### Zone A: The "Bottom Line" Recommendation Card (Top)
* **State 1: PAY (Safe to Pay)**
  * *Color Token:* Semantic Green (`#059669` / bg: `#ECFDF5`)
  * *Badge Text:* `PAYMENT LOOKS SAFE`
  * *Summary:* *"All 4 documents match. Bank details, line items, and arithmetic are verified."*
  * *Action:* `"Proceed with normal payment clearing. A human must make the final transfer."`
* **State 2: HOLD (Payment on Hold)**
  * *Color Token:* Semantic Amber (`#D97706` / bg: `#FFFBEB`)
  * *Badge Text:* `PAYMENT ON HOLD`
  * *Summary:* *"Discrepancy detected: Duplicate billing or price mismatch with purchase order."*
  * *Action:* `"Do not pay yet. Contact the department or vendor to verify authorized charge."`
* **State 3: INVESTIGATE (Verification Required)**
  * *Color Token:* Semantic Indigo/Blue (`#2563EB` / bg: `#EFF6FF`)
  * *Badge Text:* `VERIFICATION REQUIRED`
  * *Summary:* *"Critical evidence missing or unverified bank account details detected."*
  * *Action:* `"Call vendor using previously known phone number to verify new account details."`

#### Zone B: Extracted Facts & Discrepancies Grid (Middle)
* **Vendor Card**: Vendor Name, Tax ID, Bank Account Number.
* **Invoice Summary**: Invoice #, Date, Total Amount, Currency.
* **Discrepancy Highlight Box**: Red/Amber callout box detailing exact issue (e.g. `Price Mismatch: Line 1 billed at $20.00 vs PO rate of $15.00`).

#### Zone C: Deep-Dive Tabs (Bottom)
* **Tab 1: Matched Documents (Evidence)**: Shows status badges for Invoice, PO, Goods Receipt, Vendor Master.
* **Tab 2: Verified Calculations**: Shows exact math checks ($Quantity \times Unit Price = Line Total$, Subtotal + Tax = Total).
* **Tab 3: Connection & Audit Log**: Plain-English system log showing time elapsed, verification checks executed, and connection failover status.

---

### Screen 3: Transparent Failover & Recovery View (`Audit Tab`)
When an upstream API connection experiences rate limits or network issues, the UI presents plain, reassuring language:
```
┌────────────────────────────────────────────────────────────────────────┐
│ 🔄 SECURE CONNECTION FAILOVER                                         │
│ "Connection 1 reached its hourly limit. Your invoice was safely saved   │
│ and the check continued seamlessly on Connection 2."                   │
│                                                                        │
│ [Connection 1] ─── (Rate Limited) ───► [Connection 2] ─── (Completed) │
│ Case State: 100% Preserved. Progress not restarted.                    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Design System & Visual Tokens

### 4.1 Typography Scale
* **Font Family**: Inter, SF Pro Text, or system sans-serif (clean, high legibility).
* **Display 1 (Recommendation)**: 24px / 32px Line Height — SemiBold (`font-weight: 600`).
* **Heading 2 (Section Headers)**: 18px / 24px Line Height — SemiBold (`font-weight: 600`).
* **Body Regular**: 14px / 20px Line Height — Regular (`font-weight: 400`).
* **Body Medium / Actions**: 14px / 20px Line Height — Medium (`font-weight: 500`).
* **Mono (Amounts & IDs)**: 13px / 18px Line Height — JetBrains Mono or SF Mono (`font-weight: 500`).

### 4.2 Color Palette & Semantic Tokens
* **Neutrals (Slate/Zinc)**:
  * Background: `#F8FAFC` (Slate 50)
  * Surface Card: `#FFFFFF` (Pure White)
  * Card Border: `#E2E8F0` (Slate 200)
  * Text Primary: `#0F172A` (Slate 900)
  * Text Secondary: `#475569` (Slate 600)
  * Text Muted: `#94A3B8` (Slate 400)
* **Semantic Status**:
  * **Success (PAY)**: Border `#10B981` | Background `#ECFDF5` | Text `#065F46`
  * **Warning (HOLD)**: Border `#F59E0B` | Background `#FFFBEB` | Text `#92400E`
  * **Action Needed (INVESTIGATE)**: Border `#3B82F6` | Background `#EFF6FF` | Text `#1E40AF`
  * **Critical Error**: Border `#EF4444` | Background `#FEF2F2` | Text `#991B1B`

### 4.3 Component Specifications
* **Status Badges**: Pill-shaped (`border-radius: 9999px`), 12px font size, uppercase tracking, 6px padding horizontal.
* **Cards**: Solid white background, 1px subtle border (`#E2E8F0`), soft drop shadow (`0 1px 3px rgba(0,0,0,0.05)`), `border-radius: 12px`.
* **Action Buttons**:
  * *Primary*: Slate 900 background (`#0F172A`), white text, 10px vertical padding, 16px horizontal, `border-radius: 8px`. Hover: Slate 800 (`#1E293B`).
  * *Secondary*: White background, Slate 200 border, Slate 700 text. Hover: Slate 50 background.

---

## 5. Animation & Motion Principles

1. **State-Driven Only**: Motion must communicate status change (e.g. from *Analyzing* to *Result*).
2. **Subtle & Fast**: Duration $\le 200\text{ms}$ with `cubic-bezier(0.16, 1, 0.3, 1)` easing.
3. **Progressive Card Reveal**: Findings and extracted facts animate in with slight upward fade ($y: 6\text{px} \rightarrow 0$).
4. **Reduced Motion Compliance**: Full support for `@media (prefers-reduced-motion: reduce)` which disables all transitions instantly for accessibility.

---

## 6. Plain-English Copywriting Dictionary

| Backend Anomaly Code | Jargon-Free User Heading | What the User Sees on Screen |
| :--- | :--- | :--- |
| `Duplicate Billing` | **Duplicate Invoice Detected** | *"An invoice with this exact amount and vendor number was previously recorded."* |
| `Price Contradiction` | **Price Higher than Purchase Order** | *"The unit price on this invoice does not match the pre-approved purchase order."* |
| `Quantity Mismatch` | **Quantity Greater than Received** | *"The quantity billed exceeds what the warehouse signed for on the goods receipt."* |
| `Unverified Bank Change` | **New Bank Account Not Verified** | *"The bank details on this invoice differ from historical records and lack written authorization."* |
| `Vendor Identity Mismatch` | **Vendor Details Discrepancy** | *"The vendor tax ID or legal business name does not match the vendor master file."* |
| `Math Error` | **Calculation Error on Invoice** | *"The line item total, tax calculation, or invoice subtotal contains an arithmetic mistake."* |
| `Missing PO` | **No Purchase Order Attached** | *"No matching pre-approved purchase order was provided for this transaction."* |
| `Missing GRN` | **No Delivery Receipt Found** | *"No delivery confirmation or goods receipt note was found to verify delivery."* |

---

## 7. Backend Integration & Safety Architecture Boundary

```
┌────────────────────────────────────────────────────────┐
│                   FRONTEND UI LAYER                    │
│   • Pure View Components (React / Static HTML / CSS)   │
│   • Zero Business Logic / Zero Arithmetic Calculations │
│   • Consumes ONLY output_contract.json Schema          │
└───────────────────────────▲────────────────────────────┘
                            │ Read-Only JSON Output
┌───────────────────────────┴────────────────────────────┐
│                   BACKEND CORE ENGINE                  │
│   • AgentOrchestrator & Deterministic Tools            │
│   • Multi-Key Failover (CredentialManager)             │
│   • Air-Gapped from Payment Rails (Advisory Only)      │
└────────────────────────────────────────────────────────┘
```

* **Zero Logic in UI**: The UI never decides whether an invoice is valid or performs rounding/matching. It strictly renders fields provided in `benchmark/schemas/output_contract.json` (`recommendation`, `findings`, `uncertainty`, `required_human_next_step`, `evidence_references`, `deterministic_calculation_references`).
* **Human-in-the-Loop Safeguard**: The UI explicitly presents every recommendation as **advisory**. No "Auto-Pay" button exists anywhere in the architecture.

---

## 8. What is Intentionally Excluded
* ❌ No AI chatbot bubbles or conversational typing indicators.
* ❌ No neon gradients, dark cyberpunk aesthetics, or floating particle visual effects.
* ❌ No complicated multi-tier navigation menus or nested settings trees.
* ❌ No live payment execution or bank direct-debit integration buttons.

---

## 9. Conclusion
This architecture transforms Proof Before Pay into an intuitive, serious, fintech-grade tool that empowers non-technical business owners with instant clarity, defensible evidence, and total peace of mind.
