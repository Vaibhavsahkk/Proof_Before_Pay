# LOCKED PROBLEM

## Project name
Evidence-Driven Pre-Payment Exception Investigator for Small Businesses

## Problem statement
Small businesses often need to investigate supplier invoices before payment because the evidence required to decide whether an invoice is legitimate is spread across multiple records and may contain discrepancies in price, quantity, tax, vendor identity, duplicate billing, or payment-detail changes.

## Solution statement
An agentic investigator gathers and reconciles that evidence, calls deterministic verification tools for exact financial checks, and produces an evidence-linked PAY / HOLD / INVESTIGATE recommendation for a human reviewer.

## Core principle
**AI reasons over evidence. Deterministic tools calculate. Human decides.**

## Hard boundaries
The prototype must NOT:
- execute a payment
- change real bank details
- label a supplier as definitely fraudulent
- send external payment instructions
- use private real-world financial data in the repository

## Intended evidence bundle
- supplier invoice
- purchase order
- goods receipt / delivery record
- vendor master record
- optional prior-payment history
- optional payment/bank-change evidence

## Primary user
Small-business finance/AP staff or owners who must review supplier invoices before payment.
