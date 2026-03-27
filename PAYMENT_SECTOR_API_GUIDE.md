# Payment Sector Compliance API Examples

This guide shows how to use the new payment sector endpoints for querying historic RBI circulars.

## API Endpoints Overview

All payment sector endpoints are available at `http://localhost:8000/api/dashboard/`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/payment-sector-summary` | GET | Get overview of payment gateway and aggregator circulars |
| `/circulars-by-scope/{scope}` | GET | Get all circulars for a specific scope |
| `/search-circulars` | GET | Search circulars by keywords |
| `/circulars` | GET | Get all circulars (now with scope filtering) |

## 1. Payment Sector Summary

**Get a high-level overview of payment sector compliance requirements**

### cURL
```bash
curl -X GET "http://localhost:8000/api/dashboard/payment-sector-summary" \
  -H "Content-Type: application/json"
```

### Python
```python
import requests

url = "http://localhost:8000/api/dashboard/payment-sector-summary"
response = requests.get(url)
data = response.json()

print("Payment Gateway Circulars:", data['payment_gateway']['total'])
print("Payment Aggregator Circulars:", data['payment_aggregator']['total'])

# Show recent payment gateway circulars
for circular in data['payment_gateway']['recent']:
    print(f"  • {circular['circular_number']}: {circular['title']}")
```

### Response
```json
{
  "payment_gateway": {
    "total": 7,
    "recent": [
      {
        "id": 1,
        "circular_number": "RBI/DFS/2023-24/142",
        "title": "Payment Gateway Guidelines",
        "issue_date": "2023-10-15",
        "scope": "payment_gateway"
      },
      {
        "id": 2,
        "circular_number": "RBI/DPSS/2023-24/123",
        "title": "Unscheduled Payment Systems Regulation",
        "issue_date": "2023-09-20",
        "scope": "payment_gateway"
      }
    ]
  },
  "payment_aggregator": {
    "total": 6,
    "recent": [
      {
        "id": 8,
        "circular_number": "RBI/2023-24/65",
        "title": "Payment Aggregator Regulation",
        "issue_date": "2023-08-10",
        "scope": "payment_aggregator"
      }
    ]
  }
}
```

---

## 2. Get Circulars by Scope

**Retrieve all circulars for a specific payment sector scope**

### cURL - Payment Gateway Circulars
```bash
curl -X GET "http://localhost:8000/api/dashboard/circulars-by-scope/payment_gateway?skip=0&limit=10" \
  -H "Content-Type: application/json"
```

### cURL - Payment Aggregator Circulars
```bash
curl -X GET "http://localhost:8000/api/dashboard/circulars-by-scope/payment_aggregator?skip=0&limit=10" \
  -H "Content-Type: application/json"
```

### Python
```python
import requests

# Get payment gateway circulars
scope = "payment_gateway"
url = f"http://localhost:8000/api/dashboard/circulars-by-scope/{scope}"
params = {"skip": 0, "limit": 10}

response = requests.get(url, params=params)
data = response.json()

print(f"Found {data['total']} Payment Gateway circulars")
print(f"Showing {len(data['circulars'])} (limit: {data['limit']})\n")

for circular in data['circulars']:
    print(f"📋 {circular['circular_number']}")
    print(f"   Title: {circular['title']}")
    print(f"   Issue Date: {circular['issue_date']}")
    if circular.get('description'):
        print(f"   Details: {circular['description'][:100]}...")
    print()
```

### Response
```json
{
  "scope": "payment_gateway",
  "total": 7,
  "skip": 0,
  "limit": 10,
  "circulars": [
    {
      "id": 1,
      "circular_number": "RBI/DFS/2023-24/142",
      "title": "Guidelines on Payment Gateway Providers",
      "description": "Master circular providing comprehensive guidelines...",
      "issue_date": "2023-10-15",
      "effective_date": "2023-11-01",
      "scope": "payment_gateway",
      "related_scopes": ["cybersecurity", "data_security"],
      "is_historic": true,
      "keywords": ["payment", "gateway", "security", "rbi"]
    },
    {
      "id": 2,
      "circular_number": "RBI/DPSS/2023-24/123",
      "title": "Regulation of Unscheduled Payment Systems",
      "description": "Guidelines for providers of unscheduled payment systems...",
      "issue_date": "2023-09-20",
      "effective_date": "2023-10-01",
      "scope": "payment_gateway",
      "related_scopes": ["payment_aggregator"],
      "is_historic": true,
      "keywords": ["unscheduled", "payment", "systems"]
    }
  ]
}
```

---

## 3. Search Circulars by Keywords

**Find circulars matching specific compliance topics**

### cURL - Search for security requirements
```bash
curl -X GET "http://localhost:8000/api/dashboard/search-circulars" \
  -G \
  --data-urlencode "keywords=security,encryption,authentication" \
  --data-urlencode "skip=0" \
  --data-urlencode "limit=20"
```

### Python
```python
import requests

url = "http://localhost:8000/api/dashboard/search-circulars"
params = {
    "keywords": "fraud,detection,security",
    "skip": 0,
    "limit": 20
}

response = requests.get(url, params=params)
data = response.json()

print(f"Search: {data['keywords']}")
print(f"Found {data['total']} matching circulars\n")

for circular in data['circulars']:
    print(f"• {circular['circular_number']}: {circular['title']}")
    print(f"  Scope: {circular.get('scope', 'General')}\n")
```

### Available Keywords to Search
- **Security**: "security", "encryption", "authentication", "tokenization"
- **KYC/AML**: "kyc", "know_your_customer", "aml", "anti_money_laundering"
- **Operations**: "settlement", "reconciliation", "reporting"
- **Data**: "data_protection", "privacy", "pii", "confidentiality"
- **Fraud**: "fraud", "detection", "chargeback", "dispute"
- **Compliance**: "compliance", "audit", "reporting", "documentation"

### Response
```json
{
  "keywords": ["security", "encryption", "tokenization"],
  "total": 5,
  "skip": 0,
  "limit": 20,
  "circulars": [
    {
      "id": 1,
      "circular_number": "RBI/DFS/2023-24/142",
      "title": "Guidelines on Payment Gateway Providers",
      "description": "...includes comprehensive security requirements for tokenization...",
      "issue_date": "2023-10-15",
      "scope": "payment_gateway",
      "is_historic": true
    },
    {
      "id": 3,
      "circular_number": "RBI/DPSS/2022-23/76",
      "title": "Cyber Security Framework",
      "description": "...encryption standards and security protocols...",
      "issue_date": "2022-11-30",
      "scope": "cybersecurity",
      "is_historic": true
    }
  ]
}
```

---

## 4. Get All Circulars (with Scope Filter)

**Retrieve all circulars with optional scope filtering**

### cURL - All circulars
```bash
curl -X GET "http://localhost:8000/api/dashboard/circulars?skip=0&limit=20" \
  -H "Content-Type: application/json"
```

### cURL - Payment scope only
```bash
curl -X GET "http://localhost:8000/api/dashboard/circulars?scope=payment_gateway&skip=0&limit=10" \
  -H "Content-Type: application/json"
```

### cURL - Include/Exclude historic circulars
```bash
# Include historic circulars (default)
curl -X GET "http://localhost:8000/api/dashboard/circulars?include_historic=true" \
  -H "Content-Type: application/json"

# Exclude historic, show only new circulars
curl -X GET "http://localhost:8000/api/dashboard/circulars?include_historic=false" \
  -H "Content-Type: application/json"
```

### Python
```python
import requests

# Get payment gateway circulars, exclude other scopes
url = "http://localhost:8000/api/dashboard/circulars"
params = {
    "scope": "payment_gateway",
    "include_historic": True,
    "skip": 0,
    "limit": 50
}

response = requests.get(url, params=params)
data = response.json()

print(f"Showing {len(data['circulars'])} of {data['total']} circulars")
print("Payment Gateway Scope:", data.get('scope', 'All')[:])

for c in data['circulars']:
    status = "📋 HISTORIC" if c.get('is_historic') else "🆕 NEW"
    print(f"{status} {c['circular_number']}: {c['title']}")
```

### Response
```json
{
  "total": 15,
  "skip": 0,
  "limit": 20,
  "scope": "payment_gateway",
  "circulars": [
    {
      "id": 1,
      "circular_number": "RBI/DFS/2023-24/142",
      "title": "Guidelines on Payment Gateway Providers",
      "issue_date": "2023-10-15",
      "effective_date": "2023-11-01",
      "scope": "payment_gateway",
      "related_scopes": ["cybersecurity", "data_security"],
      "is_historic": true,
      "status": "ANALYZED"
    }
  ]
}
```

---

## 5. Practical Workflows

### Workflow 1: Daily Security Check
```python
import requests
from datetime import datetime

# Check for security-related compliance items
url = "http://localhost:8000/api/dashboard/search-circulars"
params = {"keywords": "security,compliance,fraud"}

response = requests.get(url, params=params)
data = response.json()

if data['total'] > 0:
    print(f"⚠️ Found {data['total']} security circulars:")
    for c in data['circulars']:
        print(f"  • {c['circular_number']}: {c['title']}")
else:
    print("✓ No new security concerns")
```

### Workflow 2: Check Payment Gateway Compliance Status
```python
import requests

# Get payment gateway summary
url = "http://localhost:8000/api/dashboard/payment-sector-summary"
response = requests.get(url)
data = response.json()

gateway_total = data['payment_gateway']['total']
aggregator_total = data['payment_aggregator']['total']

print(f"Payment Gateway Requirements: {gateway_total}")
print(f"Payment Aggregator Requirements: {aggregator_total}")
print(f"Total Payment Sector Circulars: {gateway_total + aggregator_total}")

# Show recent requirements
print("\nRecent Payment Gateway circulars:")
for c in data['payment_gateway']['recent'][:3]:
    print(f"  • {c['circular_number']} ({c['issue_date']})")
```

### Workflow 3: Get All Pending Payment Sector Action Items
```python
import requests

# This would typically integrate with your action item tracking system

# Option 1: Get via payment sector summary first
url = "http://localhost:8000/api/dashboard/payment-sector-summary"
summary = requests.get(url).json()

# Option 2: Then get individual circular details if needed
for circular in summary['payment_gateway']['recent']:
    circ_id = circular['id']
    detail_url = f"http://localhost:8000/api/dashboard/circulars/{circ_id}"
    detail = requests.get(detail_url).json()
    
    # Process circular details
    print(f"Circular: {detail['circular_number']}")
    print(f"Requirements: {detail['description']}")
```

---

## 6. Available Scopes

All scope values are lowercase with underscores:

```
payment_gateway
payment_aggregator
upi
neft_rtgs
digital_wallet
kyc_aml
cybersecurity
data_security
lending
deposits
cards
forex
general
```

---

## 7. Error Handling

### Invalid Scope
```bash
curl -X GET "http://localhost:8000/api/dashboard/circulars-by-scope/invalid_scope"
```

Response:
```json
{
  "detail": "Invalid scope: invalid_scope. Must be one of: payment_gateway, payment_aggregator, ..."
}
```

### No Results
```json
{
  "scope": "forex",
  "total": 0,
  "skip": 0,
  "limit": 10,
  "circulars": []
}
```

---

## 8. Testing All Endpoints

### Bash Script to Test All Endpoints
```bash
#!/bin/bash

BASE_URL="http://localhost:8000/api/dashboard"

echo "1. Testing Payment Sector Summary..."
curl -s "$BASE_URL/payment-sector-summary" | jq '.payment_gateway.total, .payment_aggregator.total'

echo -e "\n2. Testing Payment Gateway Circulars..."
curl -s "$BASE_URL/circulars-by-scope/payment_gateway?limit=3" | jq '.total, .circulars[].circular_number'

echo -e "\n3. Testing Search Circulars..."
curl -s "$BASE_URL/search-circulars?keywords=security" | jq '.total, .circulars[0].title'

echo -e "\n4. Testing Circulars with Scope Filter..."
curl -s "$BASE_URL/circulars?scope=payment_aggregator&limit=3" | jq '.total, .circulars[].circular_number'

echo -e "\n✓ All endpoints responding"
```

---

## 9. Integration Examples

### Dashboard Widget
```javascript
// Get payment sector summary for dashboard display
async function loadPaymentSectorWidget() {
  const response = await fetch('/api/dashboard/payment-sector-summary');
  const data = await response.json();
  
  document.getElementById('gateway-count').textContent = data.payment_gateway.total;
  document.getElementById('aggregator-count').textContent = data.payment_aggregator.total;
  
  // Show recent circulars
  const recentList = document.getElementById('recent-circulars');
  data.payment_gateway.recent.forEach(c => {
    const li = document.createElement('li');
    li.innerHTML = `
      <strong>${c.circular_number}</strong><br>
      ${c.title}<br>
      <small>${c.issue_date}</small>
    `;
    recentList.appendChild(li);
  });
}
```

### Notification System Integration
```python
# When a new payment sector circular is detected, notify teams

def notify_payment_sector_circular(circular_id: int):
    """Send notification to payment sector teams"""
    
    # Get circular details
    response = requests.get(f"http://localhost:8000/api/dashboard/circulars/{circular_id}")
    circular = response.json()
    
    if circular['scope'] == 'payment_gateway':
        notification = {
            'to': 'payment-systems-team@company.com',
            'subject': f"New Payment Gateway Requirement: {circular['circular_number']}",
            'body': f"Action required: {circular['title']}\n\n{circular['description']}"
        }
    elif circular['scope'] == 'payment_aggregator':
        notification = {
            'to': 'payment-operations@company.com',
            'subject': f"New Payment Aggregator Requirement: {circular['circular_number']}",
            'body': f"Action required: {circular['title']}\n\n{circular['description']}"
        }
    
    # Send notification
    send_email_notification(notification)
```

---

## 10. Troubleshooting

### Endpoint Not Found (404)
- Ensure server is running: `python main.py`
- Check URL spelling (use `/api/dashboard/`, not `/api/dashboard`)
- Verify circular_id exists in database

### Invalid Scope Parameter
- Use lowercase scope names with underscores
- Valid: `payment_gateway`, not `PaymentGateway` or `payment-gateway`
- Check against list in Section 6

### No Results
- Check if database is seeded: `python manage.py seed`
- Verify scopes exist: `python manage.py stats`
- Try broader search or remove filters

---

## 11. Performance Notes

- Endpoints support pagination via `skip` and `limit` parameters
- Default limit: 20 records
- Maximum recommended limit: 100
- Use `skip + limit` for pagination through large result sets

```python
# Example: Pagination through all payment gateway circulars
page_size = 10
skip = 0

while True:
    response = requests.get(
        f"http://localhost:8000/api/dashboard/circulars-by-scope/payment_gateway",
        params={"skip": skip, "limit": page_size}
    )
    data = response.json()
    
    if not data['circulars']:
        break  # No more results
    
    # Process this page
    for circular in data['circulars']:
        process_circular(circular)
    
    # Next page
    skip += page_size
```
