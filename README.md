# Nova CRM — World-Class Enterprise CRM

![Nova CRM Dashboard](crm/static/img/auth-bg.png)

Nova CRM is a premium, production-grade CRM platform engineered for high-performance teams. Inspired by industry leaders like **Linear**, **Stripe**, and **Attio**, it delivers a modern, dark-first SaaS experience that is fast, elegant, and enterprise-ready.

## ✨ Premium UI/UX

Nova CRM has been transformed with a world-class design system:
- **Modern Dark-First UI**: A sophisticated palette using `#111827` background and `#4F46E5` primary accents.
- **Glassmorphism & Depth**: Layered surfaces with subtle blurs and elegant spacing.
- **Micro-interactions**: Smooth 150ms-250ms transitions and animated active states.
- **Responsive Layout**: A floating, collapsible modern sidebar and a clean, data-focused content area.

## 🚀 Key Features

### Core CRM Modules
- **Advanced Lead Management**: Modern Kanban boards with drag-and-drop feel and pipeline visualization.
- **Relationship Intelligence**: Manage Companies and Contacts with high-performance, sticky-header data tables.
- **Customer Profiles**: Deep-dive into customer data with an elegant, activity-centric profile view.

### Command & Control
- **Command Palette (Ctrl + K)**: A global search and action hub for lightning-fast navigation.
- **Global Search**: Instantly find leads, deals, and tasks from anywhere.
- **Quick Actions**: Streamlined workflows for creating records and logging activities.

### Intelligence & Automation
- **AI-Powered Insights**: Integrated with OpenRouter to provide smart suggestions and automated data entry.
- **Activity Timelines**: A visually polished timeline of all customer interactions.
- **Real-time Analytics**: Beautifully animated charts and KPI cards for data-driven decisions.

## 🛠️ Tech Stack

- **Backend**: Django (Python)
- **Frontend**: Tailwind CSS + Vanilla JavaScript (Optimized Build)
- **Icons**: Lucide Icons
- **Animations**: CSS Transitions + JavaScript Micro-interactions
- **Database**: PostgreSQL / SQLite
- **AI**: OpenRouter API

## 🚦 Getting Started

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Dineshbalaji25/Nova-CRM.git
   ```

2. **Set up Environment**:
   Create a `.env` file with:
   ```env
   OPENROUTER_API_KEY=your_key
   SECRET_KEY=your_django_secret
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   npm install
   ```

4. **Build Styles**:
   ```bash
   npm run build
   ```

5. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Start Development Server**:
   ```bash
   python manage.py runserver
   ```

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---
Built with ❤️ for high-performance teams.
