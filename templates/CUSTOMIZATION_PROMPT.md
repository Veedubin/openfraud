# OpenFraud Customization Prompt

Use this prompt to customize the OpenFraud framework for your specific fraud detection project.

## Instructions

1. Copy this template and fill in the [BRACKETED] sections with your project details
2. Share the completed prompt with the Orchestrator agent
3. The agents will adapt their analysis to your domain

---

## Project Customization Template

### 1. Project Overview

**Project Name:** [Your project name]

**Domain:** [e.g., E-commerce, Banking, Healthcare, Insurance, Telecommunications]

**Fraud Type:** [e.g., payment fraud, account takeover, claims fraud, identity theft]

**Data Scale:**
- Number of entities (users/accounts/providers): [e.g., 100,000]
- Number of transactions/events: [e.g., 10 million]
- Time period: [e.g., 12 months]
- Data size: [e.g., 50 GB]

### 2. Entity Definitions

**Primary Entity Type:** [e.g., User, Account, Merchant, Provider]

**Entity Identifier Column:** [e.g., user_id, account_number]

**Entity Attributes:**
- [e.g., registration_date, account_type, country]
- [e.g., verification_status, risk_tier]

**Related Entities:**
- [e.g., Device - devices used by accounts]
- [e.g., IP_Address - IP addresses associated with logins]
- [e.g., Merchant - vendors receiving payments]

### 3. Transaction/Event Definitions

**Transaction Type:** [e.g., payment, transfer, claim, order]

**Key Fields:**
- Transaction ID: [column name]
- Timestamp: [column name]
- Amount: [column name]
- Currency: [column name or fixed value]
- Status: [e.g., completed, failed, pending]

**Transaction Attributes:**
- [e.g., payment_method, device_fingerprint]
- [e.g., merchant_category, geo_location]

### 4. Physical Constraints (Hard Rules)

Define mathematical impossibilities in your domain:

**Velocity Limits:**
- Maximum transactions per hour: [e.g., 60]
- Maximum transactions per day: [e.g., 1000]
- Maximum amount per transaction: [e.g., $100,000]
- Maximum amount per day: [e.g., $500,000]

**Ratio Limits:**
- Maximum [ratio name]: [e.g., refund rate] < [e.g., 50%]
- Maximum [ratio name]: [e.g., chargeback rate] < [e.g., 5%]

**Business Rules:**
- [e.g., New accounts cannot transact > $1000 in first 24h]
- [e.g., Transfers to unverified accounts limited to $500]

### 5. Peer Group Definitions

How should entities be grouped for comparison?

**Primary Grouping:** [e.g., account_type, merchant_category, user_segment]

**Secondary Grouping:** [e.g., country, registration_month]

**Rationale:** [Why these groupings make sense]

### 6. Network Relationships

**Node Types:**
- Primary: [e.g., Account]
- Secondary: [e.g., Device, IP_Address, Merchant]

**Relationship Types:**
- [e.g., Account -> TRANSACTED_WITH -> Merchant]
- [e.g., Account -> USED -> Device]
- [e.g., Account -> LOGGED_FROM -> IP_Address]

**Suspicious Patterns to Detect:**
- [e.g., Many accounts sharing one device]
- [e.g., Circular money transfers]
- [e.g., Accounts with no device fingerprint]

### 7. Historical Fraud Labels

Do you have labeled fraud data?

**Label Available:** [Yes/No]

**Label Column:** [column name]

**Label Definition:** [e.g., 1 = confirmed fraud, 0 = legitimate]

**Label Source:** [e.g., chargebacks, manual review, regulatory report]

**Class Balance:** [e.g., 2% fraud rate]

### 8. Investigation Workflow

**Who investigates flagged entities?**
[Analyst team, automated system, etc.]

**Investigation Tools:**
[Internal dashboards, external databases, etc.]

**Response Times:**
- Critical: [e.g., immediate freeze]
- High: [e.g., within 4 hours]
- Medium: [e.g., within 24 hours]

**Actions Available:**
- [e.g., Account suspension]
- [e.g., Transaction review queue]
- [e.g], KYC request]

### 9. Success Metrics

**Detection Goals:**
- Target recall: [e.g., catch 80% of fraud]
- Acceptable false positive rate: [e.g., <5%]

**Business Metrics:**
- Fraud loss reduction target: [e.g., 30%]
- Investigation efficiency: [e.g., 20 cases per analyst per day]

### 10. Data Access

**Data Location:** [e.g., S3 bucket, local files, database]

**Data Format:** [e.g., Parquet, CSV, JSON]

**Update Frequency:** [e.g., daily, real-time]

**Sample Data Available:** [Yes/No]

---

## Example Completed Template

### Project: E-commerce Payment Fraud

**Domain:** E-commerce
**Fraud Type:** Payment fraud (stolen cards, account takeover)
**Data Scale:** 500K users, 50M transactions, 18 months

**Primary Entity:** User (user_id)
**Transaction:** Order (order_id, created_at, amount_usd, status)

**Hard Rules:**
- Max 10 orders/hour
- Max $10K per order
- New users (<7 days) max $1K/day

**Peer Groups:** By user_segment (new, regular, premium) and country

**Network:** User -> ORDERED_FROM -> Merchant, User -> USED -> Device

**Fraud Labels:** Yes, from chargeback data (1.5% fraud rate)

---

## Agent Adaptation Checklist

Once you provide this information, each agent will adapt:

- [ ] **Orchestrator:** Creates domain-specific task plan
- [ ] **Forensic Accountant:** Configures hard violation rules
- [ ] **ML Architect:** Selects appropriate features and thresholds
- [ ] **Graph Architect:** Defines node/relationship schema
- [ ] **Investigator:** Sets up investigation workflows

---

## Quick Start (Use Default Agents)

If you don't want to customize, the agents work as general-purpose fraud detection tools:

- **Forensic Accountant** will use universal patterns (Benford's Law, Z-scores)
- **ML Architect** will auto-detect features and train models
- **Graph Architect** will use generic node/relationship analysis
- **Investigator** will produce general risk reports

Simply provide your data and say "Use default configuration."
