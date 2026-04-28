# Nova CRM

A modern, multi-tenant enterprise CRM application built with Django and vanilla JavaScript. Nova CRM provides advanced functionality equivalent to leading platforms like Zoho CRM and Salesforce, designed for high performance and exceptional user experience.

## ✨ Features

Nova CRM includes a rich suite of enterprise features:

- **Multi-Tenant Architecture**: Robust data isolation ensuring that each registered organization operates within its own secure workspace.
- **Core Sales Pipeline**: Comprehensive management of Leads, Contacts, Companies, and Deals.
- **Territory Management**: Build sales territories with hierarchical structures and automate record assignment dynamically via rules.
- **Workflow Automation**: Visual node-based workflow builder for trigger-action automations.
- **Blueprint State Machines**: Define strict processes (Blueprints) ensuring records follow mandatory stages.
- **Lead Scoring Rules**: Dynamic point allocation engine to rank and prioritize leads.
- **Omnichannel Communication**: 
  - **Emails**: Native IMAP integration for syncing and viewing emails directly attached to CRM records.
  - **Calls**: Telephony logs to track inbound and outbound calls.
- **Advanced Analytics & Reporting**: Custom JSON-driven report builder and interactive Dashboards powered by Chart.js.
- **Partner & Customer Portals**: Admin-configurable external portals with module-level access control.
- **Modern UI/UX**: Premium, colorful design featuring custom CSS layouts, split-screen interfaces, and a stunning authentication flow.

## 🚀 Technology Stack

- **Backend**: Django, Django REST Framework
- **Frontend**: Vanilla JavaScript (ES6+), HTML5, Custom CSS
- **Authentication**: JWT (JSON Web Tokens)
- **Icons**: Lucide Icons
- **Charting**: Chart.js

## 📦 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Dineshbalaji25/Nova-CRM.git
   cd Nova-CRM
   ```

2. **Set up a virtual environment (Optional but recommended):**
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows use `env\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations:**
   ```bash
   cd crm
   python manage.py migrate
   ```

5. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

6. **Access the Application:**
   Open your browser and navigate to `http://127.0.0.1:8000`.

## 🎨 UI/UX Highlights

- The application entirely bypasses third-party UI frameworks (like Bootstrap or Tailwind) in favor of lightweight, custom Vanilla CSS.
- Implements interactive side-drawers, modals, and split-screen editor views.
- Dynamic color themes and rich abstract backgrounds.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome. Feel free to check the issues page if you want to contribute.

## 📄 License

This project is open-source and available under the MIT License.
