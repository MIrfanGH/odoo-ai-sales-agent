# Odoo AI Sales Agent: Business Context and System Overview

A plain-language explanation for non-technical and non-sales readers.

**Status:** Working end to end: customer lookup, stock and price check, approval, and draft quotation creation in Odoo.

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
3. **Create the draft quotation** (`create_draft_quotation`): this is the only tool that writes to Odoo, and it runs only after the sales rep approves.

Before step 3 runs, the system pauses and shows the sales rep exactly what will be created.

**Ambiguous requests:** if a request matches several products (for example, "Office Chair" matches Office Chair and Office Chair Black), the agent asks which one is meant instead of guessing.

**Out of stock:** if the product has too little stock, the agent says so instead of quoting anyway.

**Unknown customer:** if the customer isn't in Odoo, the agent says so and stops. It never invents data.

## 4. Why There Is an Approval Step

Nothing is written to Odoo without the sales rep's approval. This prevents accidental quotations and keeps a person in control of every record. The approval is enforced by the system, not by the AI: the AI cannot skip it.

```
Agent:      Ready to create draft quotation: customer id 11, product id 5, qty 5.
            Approval needed. (Nothing has been saved yet.)
Sales rep:  No, make it 3 instead.
Agent:      Ready to create draft quotation: customer id 11, product id 5, qty 3.
            Approval needed. (Still nothing saved.)
Sales rep:  Yes.
Agent:      Draft quotation created: Office Chair, quantity 3, total 210.
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

The loop has a maximum number of steps (15), so the agent can't run forever.

## 6. Why It Helps Sales Reps

- **Faster replies:** customers get a quote sooner.
- **Fewer clicks:** one sentence replaces several screens.
- **No copying between screens:** data comes straight from the ERP, so nothing is retyped.
- **One source of truth:** everyone uses the same Odoo data.

## 7. Example Conversation (real data from the demo)

```
Sales rep:  Quote 5 Office Chair for Gemini Furniture
Agent:      Found Gemini Furniture. Two products match:
            1. Office Chair, 20 in stock, unit price 70
            2. Office Chair Black, 10 in stock, unit price 120.5
            Which product?
Sales rep:  Office chair, id 5
Agent:      Ready to create draft quotation: customer id 11, product id 5, qty 5.
            Approval needed.
Sales rep:  Yes
Agent:      Draft quotation S00030 created for Gemini Furniture, Office Chair, quantity 5, total 350.
```

## 8. Future Work (not built yet)

- Customer-specific prices and discounts (Odoo pricelists)
- Quotations with several products in one request
- Emailing the quotation to the customer after the sales rep confirms it
- Showing customer and product names (not only ids) in the approval message
- Login for sales reps, and saved conversations that survive a restart

## Summary

This is an AI sales assistant for Odoo ERP. It understands a plain-English request, looks up the customer, stock and price in Odoo, prepares a quotation, explains the result, and creates a draft quotation only after the sales rep approves.