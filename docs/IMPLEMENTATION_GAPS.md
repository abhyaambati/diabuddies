# Diabuddies Implementation Gaps

This document tracks features described in the [Product Description](PRODUCT_DESCRIPTION.md) that are not yet fully implemented.

## 🔴 Critical Features (High Priority)

### 1. Time In Range (TIR) Metrics
**Status:** ❌ Not Implemented  
**Description:** Doctor dashboard should prominently display Time In Range (TIR) percentage - the percentage of glucose readings within target range.  
**Location:** `frontend/public/provider.html` - Dashboard and Insights tabs  
**Implementation Notes:**
- Calculate TIR from glucose logs vs. care plan targets
- Display as primary metric in patient cards
- Add to weekly/monthly reports

### 2. SMS Alerts for Critical Readings
**Status:** ❌ Not Implemented  
**Description:** When a patient logs a critically low or high reading, send SMS alert to patient or emergency contact.  
**Location:** `backend/services.py` - `check_glucose_alerts()` function  
**Current State:** Only creates alerts in database, no SMS sending  
**Implementation Notes:**
- Integrate Twilio SMS API (already have Twilio for voice)
- Send SMS when `severity == 'critical'`
- Allow patient to configure emergency contact phone number

### 3. SMS Reminders
**Status:** ❌ Not Implemented  
**Description:** Proactive SMS reminders for medication, glucose checks, meals.  
**Location:** `backend/services.py` - `generate_reminders()` function  
**Implementation Notes:**
- Schedule SMS reminders based on care plan
- Use Twilio SMS API
- Allow patient to opt-in/opt-out

### 4. Offline Instant Feedback Cards
**Status:** ⚠️ Partially Implemented  
**Description:** After logging glucose, show instant instruction card with actionable guidance (works offline).  
**Location:** `frontend/public/index.html` - Tracker tab  
**Current State:** Alerts are created but not displayed as prominent instruction cards  
**Implementation Notes:**
- Add offline logic to categorize readings (Target, Warning Low, Critical High)
- Display prominent instruction card immediately after logging
- Store guidance text locally (no API call needed)

### 5. Local Carb Guide
**Status:** ❌ Not Implemented  
**Description:** Regional food carb counts (biscuits, grits, etc.) stored locally on device.  
**Location:** `frontend/public/index.html` - New section or modal  
**Implementation Notes:**
- Create JSON file with regional foods and carb counts
- Store in localStorage or bundled with app
- Accessible from meal logging interface

### 6. Local Emergency Contacts
**Status:** ❌ Not Implemented  
**Description:** Emergency contacts stored locally on device for offline access.  
**Location:** `frontend/public/index.html` - New section  
**Implementation Notes:**
- Allow patient to add/edit emergency contacts
- Store in localStorage
- Display prominently in emergency situations

## 🟡 Important Features (Medium Priority)

### 7. Visual Glucose Charting in Doctor Dashboard
**Status:** ⚠️ Partially Implemented  
**Description:** Clean graphs plotting patient's recent glucose readings to spot patterns.  
**Location:** `frontend/public/provider.html` - Insights tab  
**Current State:** Reports show data but no visual charts  
**Implementation Notes:**
- Add chart.js or similar library
- Plot glucose readings over time
- Highlight patterns (post-dinner spikes, nighttime lows)

### 8. Offline Data Staging with Intelligent Sync
**Status:** ⚠️ Partially Implemented  
**Description:** Logs saved locally first, then synced when connection available.  
**Location:** `frontend/public/index.html` - All logging functions  
**Current State:** Data sent directly to API, no offline queue  
**Implementation Notes:**
- Implement service worker or localStorage queue
- Queue logs when offline
- Sync when connection restored
- Show sync status to user

### 9. Doctor Reporting Toggle
**Status:** ❌ Not Implemented  
**Description:** Patient must explicitly enable "Doctor Reporting" to share data.  
**Location:** `frontend/public/index.html` - Settings section  
**Implementation Notes:**
- Add toggle in patient settings
- Store preference in patient model
- Respect preference in data sync

### 10. Aggregated Data Sync
**Status:** ⚠️ Partially Implemented  
**Description:** When syncing, send aggregated summary (TIR, Averages, Extremes) not raw logs.  
**Location:** `backend/main.py` - Patient endpoints  
**Current State:** All logs synced individually  
**Implementation Notes:**
- Create summary endpoint
- Calculate TIR, averages, extremes
- Send summary instead of all logs

## 🟢 Nice-to-Have Features (Low Priority)

### 11. Regional Activity Recommendations
**Status:** ⚠️ Partially Implemented  
**Description:** AI recommends low-cost, local activities for exercise (rural context).  
**Location:** `backend/agents/buddy_agent.py`  
**Current State:** Generic activity recommendations  
**Implementation Notes:**
- Add rural Georgia context to AI prompts
- Include local activity suggestions

### 12. Enhanced Pattern Detection
**Status:** ⚠️ Partially Implemented  
**Description:** Detect patterns like "consistent post-dinner spikes" or "unexplained nighttime lows".  
**Location:** `backend/services.py` - Report generation  
**Current State:** Basic pattern detection  
**Implementation Notes:**
- Enhance pattern detection algorithms
- Add time-of-day analysis
- Surface patterns in reports

---

## Implementation Priority

1. **Phase 1 (Critical):** TIR metrics, SMS alerts, offline feedback cards
2. **Phase 2 (Important):** Visual charts, offline sync, local resources
3. **Phase 3 (Enhancement):** Regional recommendations, enhanced patterns

---

## Notes

- Twilio is already integrated for voice calls, so SMS integration should be straightforward
- localStorage is already used for some data, can be extended for offline functionality
- Chart.js or similar can be added for visualizations
- All features should maintain the "rural-first" design philosophy

