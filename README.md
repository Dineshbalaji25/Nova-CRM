# Nova CRM — Next-Gen Multi-Tenant CRM

![Nova CRM Dashboard](crm/static/img/auth-bg.png)

Nova CRM is a premium, high-performance CRM platform designed for modern, high-growth teams. Built with **Django** and **Vanilla JavaScript**, it offers a seamless, vibrant user experience with "Royal Indigo" and "Vibrant Gold" aesthetics.

## 🚀 Features

### Core CRM Modules
- **Companies & Contacts**: Manage your business relationships with a clean, searchable interface.
- **Deals Pipeline**: A drag-and-drop Kanban board for tracking your sales lifecycle.
- **Tasks & Activities**: Organize your workflow with interactive task lists and activity feeds.

### Advanced Analytics
- **Dynamic Dashboards**: Create custom visualizations with multiple chart types (Bar, Pie, Line, Metric).
- **Report Engine**: Powerful data aggregation for sales and customer insights.

### AI-Powered Insights
- **OpenRouter Integration**: Leverages state-of-the-art LLMs for smart suggestions and automated data entry.
- **Sentiment Analysis**: Understand customer needs through omnichannel communication logs.

### Enterprise Infrastructure
- **Multi-Tenancy**: Secure organization-level data isolation.
- **Omnichannel Support**: Integration points for email, calls, and webforms.
- **Workflows & Blueprints**: Automate complex business processes with a flexible node-based engine.

## 🎨 Design System

Nova CRM uses a custom-built design system defined in `global.css`, featuring:
- **Royal Indigo Palette**: Professional and trustworthy base colors.
- **Vibrant Gold (#EABF32)**: High-contrast accents for primary actions.
- **Glassmorphism**: Translucent card effects and blur filters for depth.
- **Smooth Animations**: 60fps transitions and entry effects.

## 🛠️ Tech Stack

- **Backend**: Django (Python)
- **Frontend**: Vanilla JavaScript + Lucide Icons
- **Database**: PostgreSQL / SQLite (Development)
- **Styling**: Modern CSS3 (Variables, Grid, Flexbox)
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
   ```

4. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Start Development Server**:
   ```bash
   python manage.py runserver
   ```

---
Built with ❤️ for high-performance teams.
