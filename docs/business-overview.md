# Odoo AI Sales Agent: Business Context and System Overview

A plain-language explanation for non-technical and non-sales readers.

**Status:** The Odoo client works: it can find a customer, check stock and price, and create a draft quotation. The AI agent, the approval step and the `/chat` endpoint are in progress.

## 1. The Business Problem

A company sells products to other businesses. A customer calls and says: "We need 5 office chairs. Can you send us a quote?"

To answer that, a sales rep has to look up the customer, find the right product, check whether it is in stock, check the price and then create the quotation. That means opening several screens in the ERP (Odoo), searching through records, and copying details between them.

## 2. What This System Changes

Without the agent, the sales rep does every step by hand:

```
Open Odoo
  -> Search customer
  -> Search product
  -> Check stock and price
  -> Create quotation
```

With the agent, the sales rep types one sentence:

> "Gemini Furniture wants 5 office chairs, can we quote them?"

The agent does the lookups and prepares the quotation. The sales rep reviews it and approves it.

## 3. What the AI Agent Does

The agent sits between the sales rep and Odoo. It turns a plain-English request into actions in Odoo using three tools:

1. **Find the customer** (`find_customer`): looks up the customer in Odoo.
2. **Check stock and price** (`check_stock`): finds the product, its on-hand quantity and its list price.
3. **Ask for approval**: shows the sales rep what it is about to create.
4. **Create the draft quotation** (`create_draft_quotation`): only after approval.

**Ambiguous requests:** if a request matches several products (for example, "chair" matches Office Chair, Office Chair Black and Conference Chair), the agent asks which one is meant instead of guessing.

**Out of stock:** if the product has too little stock, the agent says so instead of quoting anyway.

## 4. Why There Is an Approval Step

Nothing is written to Odoo without the sales rep's approval. This prevents accidental quotations and keeps a person in control of every record.

```
Agent:      I can create a draft quotation for 5 Office Chairs for Gemini Furniture, total ₹350. Create it?
            (Nothing has been saved yet.)
Sales rep:  Yes.
Agent:      Draft quotation S00025 created.
```

The agent stops at a **draft** quotation. Confirming the order and sending it to the customer stay with the sales rep.

## 5. How It Works Behind the Scenes

```
Sales rep (plain English)
  -> AI agent (decides which tool to use next)
  -> Odoo client (Python, XML-RPC)
  -> Odoo ERP (customers, products, stock, quotations)
```

- **Odoo** stores the business data.
- **The Odoo client** is a small Python class that talks to Odoo over its XML-RPC API. It is the bridge between the AI and the ERP.
- **The agent loop:**

```
What information do I need?
  -> Call a tool
  -> Read the result
  -> Decide the next step (call another tool, or ask the user)
  -> Final answer
```

The loop has a maximum number of steps, so the agent can't run forever.

## 6. Why It Helps Sales Reps

- **Faster replies:** customers get a quote sooner.
- **Fewer clicks:** one sentence replaces several screens.
- **No copying between screens:** data comes straight from the ERP, so nothing is retyped.
- **One source of truth:** everyone uses the same Odoo data.

## 7. Example Conversation (real data from the demo)

```
Sales rep:  Gemini Furniture wants 5 office chairs. Can we quote them?
Agent:      I found several chairs: Office Chair, Office Chair Black, Conference Chair. Which one?
Sales rep:  Office Chair.
Agent:      Gemini Furniture found. Office Chair: 20 in stock, ₹70 each.
            5 units would total ₹350. Should I create a draft quotation?
Sales rep:  Yes.
Agent:      Draft quotation S00025 created.
```

## 8. Future Work (not built yet)

- Customer-specific prices and discounts (Odoo pricelists)
- Quotations with several products in one request
- Emailing the quotation to the customer after the sales rep confirms it

## Summary

This is an AI sales assistant for Odoo ERP. It understands a plain-English request, looks up the customer, stock and price in Odoo, prepares a quotation, explains the result, and creates a draft quotation only after the sales rep approves.