# RFP Analysis Templates

Reference templates for analyzing RFP documents and generating discovery artifacts.

## Business Flow Template

### Mermaid Flowchart Structure

```mermaid
flowchart TD
    subgraph Customer["Customer (Actor)"]
        C1[Browse Products]
        C2{Items in Cart?}
        C3[Checkout]
    end
    
    subgraph System["E-commerce Platform"]
        S1[Inventory Check]
        S2[Calculate Total]
        S3[Process Payment]
    end
    
    subgraph Payment["Payment Gateway (External)"]
        P1[Authorize Card]
        P2{Payment Success?}
    end
    
    C1 --> C2
    C2 -->|Yes| C3
    C2 -->|No| C1
    C3 --> S1
    S1 --> S2
    S2 --> S3
    S3 --> P1
    P1 --> P2
    P2 -->|Yes| S4[Send Confirmation]
    P2 -->|No| S5[Show Error]
```

### Rules
- One subgraph per actor or external system
- Decision nodes use curly braces `{}`
- Max 15 nodes per diagram (split complex flows)
- Label external system boundaries clearly
- Use meaningful node IDs (C1, S1, P1 for Customer/System/Payment)

---

## User Journey Template

### Per-Actor Journey Table

| Phase | Action | Screen | Input/Output | Pain Point | Note |
|-------|--------|--------|--------------|------------|------|
| Discovery | Search for products | Product Listing | Search keywords → Filtered results | Too many irrelevant results | Consider AI-powered search |
| Selection | Add items to cart | Product Detail | Click "Add to Cart" → Cart updated | No stock indicator | Show real-time availability |
| Checkout | Enter shipping info | Checkout Form | Address, phone → Validation feedback | Form too long | Implement autofill |
| Payment | Confirm payment | Payment Gateway | Card details → Transaction status | Redirect delay | Use embedded iframe |
| Confirmation | View order summary | Order Confirmation | Order ID → Receipt email | Email delay | Send SMS backup |

### Mermaid Journey Diagram

```mermaid
journey
    title Customer Purchase Journey
    section Discovery
      Search products: 3: Customer
      Filter by category: 4: Customer
      View product details: 5: Customer
    section Selection
      Add to cart: 4: Customer
      Adjust quantity: 3: Customer
    section Checkout
      Enter shipping address: 2: Customer
      Select payment method: 3: Customer
    section Payment
      Authorize payment: 2: Customer, Payment Gateway
      Receive confirmation: 5: Customer
```

### Satisfaction Scores
- 1 = Very dissatisfied
- 2 = Dissatisfied
- 3 = Neutral
- 4 = Satisfied
- 5 = Very satisfied

---

## Screen Flow Template

### Mermaid Screen Flow

```mermaid
flowchart LR
    S1[Login Screen]
    S2[Dashboard]
    S3[Product Listing]
    S4[Product Detail]
    S5[Cart]
    S6[Checkout]
    S7[Payment]
    S8[Confirmation]
    
    S1 -->|Login| S2
    S2 -->|Browse| S3
    S3 -->|Select| S4
    S4 -->|Add to Cart| S5
    S4 -.->|Quick View Modal| S4
    S5 -->|Proceed| S6
    S6 -->|Continue| S7
    S7 -->|Success| S8
    S7 -.->|Error Popup| S7
    S8 -->|New Order| S2
```

### Screen List Table

| ID | Screen Name | Device | Level | Actors | Key Actions |
|----|-------------|--------|-------|--------|-------------|
| S1 | Login | Web, Mobile | L1 | Customer | Email/password login, social OAuth, forgot password |
| S2 | Dashboard | Web, Mobile | L1 | Customer | View order history, wishlist, profile settings |
| S3 | Product Listing | Web, Mobile | L2 | Customer | Search, filter, sort, pagination |
| S4 | Product Detail | Web, Mobile | L2 | Customer | View images, description, reviews, add to cart |
| S5 | Cart | Web, Mobile | L2 | Customer | Update quantity, remove items, apply coupon, checkout |
| S6 | Checkout | Web, Mobile | L3 | Customer | Enter/select address, choose shipping method |
| S7 | Payment | Web | L3 | Customer, Payment Gateway | Enter card details, authorize payment |
| S8 | Confirmation | Web, Mobile | L2 | Customer | View order summary, download receipt, track order |

### Device Legend
- Web: Desktop browser
- Mobile: iOS/Android app or responsive web

### Level Legend
- L1: Core screens (always needed)
- L2: Standard screens (common features)
- L3: Advanced screens (complex workflows)

### Flow Annotations
- Solid arrows: Primary navigation
- Dotted arrows: Modals, popups, overlays
- Labels on arrows: Action that triggers navigation
