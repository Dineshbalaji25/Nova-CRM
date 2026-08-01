---
title: Nova CRM
emoji: 🚀
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Nova CRM — World-Class Enterprise CRM

![Nova CRM Dashboard](crm/static/img/auth-bg.png)

Nova CRM is a premium, production-grade CRM platform engineered for high-performance teams. Inspired by industry leaders like **Linear**, **Stripe**, and **Attio**, it delivers a modern, dark-first SaaS experience that is fast, elegant, and enterprise-ready.

---

## ✨ Premium UI/UX

Nova CRM has been transformed with a world-class design system:
- **Modern Dark-First UI**: A sophisticated palette using `#111827` background and `#4F46E5` primary accents.
- **Glassmorphism & Depth**: Layered surfaces with subtle blurs and elegant spacing.
- **Micro-interactions**: Smooth 150ms-250ms transitions and animated active states.
- **Responsive Layout**: A floating, collapsible modern sidebar and a clean, data-focused content area.

---

## 🚀 Key Features

### Core CRM Modules
- **Advanced Lead & Deal Management**: Interactive Kanban boards with drag-and-drop workflow and stage probabilities.
- **Relationship Intelligence**: Manage Companies and Contacts with high-performance, sticky-header data tables.
- **Customer Profiles**: Deep-dive into customer data with an activity-centric profile view.
- **Notes, Activities & Scoring Rules**: Automated lead assignment and scoring engines.

### Omnichannel Communications & Support
- **Telephony Integration**: Phone integrations for call logging, call summaries, and transcripts.
- **IMAP / SMTP Email Sync**: Integrated email client linking messages to leads, contacts, and deals.
- **Live Support Chat**: Real-time support messaging system.

### Sales, Invoicing & Billing
- **Product Catalog & Price Books**: Manage SKUs, custom pricing, and product lines.
- **Quotes & Sales Orders**: Generate and track enterprise quotes and order fulfillments.
- **Invoicing & Billing**: Invoice generation and automated Stripe webhook integration.

### Workflows, Marketing & Integrations
- **Automation Engine**: Triggers, actions, and step-by-step process Blueprints.
- **Marketing Campaigns & Web Forms**: Lead capture forms with custom fields and campaign ROI tracking.
- **Zoho CRM v8 API Layer**: Compatible API endpoints for third-party integrations.

---

## 🧪 Comprehensive Feature Testing

Nova CRM includes an end-to-end automated test suite covering all API endpoints, auth flows, CRUD operations, multi-tenancy, security, and edge cases.

### Test Results Summary
- **Total Test Cases**: **157**
- **Passed**: **155** (98.7% Success Rate)
- **Failed**: **0** (0.0%)
- **Warnings**: **2** (Strict tenant headers & stored raw inputs)

### Running the Test Suite

1. **Start the Django Development Server**:
   ```bash
   python crm/manage.py runserver 8000
   ```

2. **Execute the Comprehensive Test Suite**:
   ```bash
   python crm/comprehensive_test.py
   ```

   *Detailed results are saved to `test_report.json`.*

---

## 🛠️ Tech Stack

- **Backend**: Django & Django REST Framework (Python 3.12)
- **Frontend**: Tailwind CSS + Vanilla JavaScript (Optimized Build)
- **Icons**: Lucide Icons
- **Database**: SQLite / PostgreSQL
- **Integrations**: Stripe Webhooks, OpenRouter AI, Twilio Telephony

---

## 🚦 Getting Started

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Dineshbalaji25/Nova-CRM.git
   cd Nova-CRM
   ```

2. **Activate Environment & Install Dependencies**:
   ```bash
   source env/bin/activate
   pip install -r requirements.txt
   ```

3. **Set up Environment Variables**:
   Create a `.env` file with:
   ```env
   SECRET_KEY=your_django_secret
   STRIPE_WEBHOOK_SECRET=your_stripe_secret
   ```

4. **Run Migrations**:
   ```bash
   python crm/manage.py migrate
   ```

5. **Start Development Server**:
   ```bash
   python crm/manage.py runserver 8000
   ```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---
Built with ❤️ for high-performance teams.
