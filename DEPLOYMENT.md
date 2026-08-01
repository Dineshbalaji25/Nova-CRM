# Deployment Guide: Nova CRM

This document provides step-by-step instructions for deploying Nova CRM to **Hugging Face Spaces** and **Vercel**.

---

## 1. Hugging Face Spaces Deployment (Docker SDK)

Hugging Face Spaces allows you to host Docker-based applications for free.

### Step 1: Create a Space on Hugging Face
1. Log in to [Hugging Face](https://huggingface.co/) and click **New Space**.
2. Set a **Space Name** (e.g. `nova-crm`).
3. Select **Docker** as the Space SDK (Blank template).
4. Choose **Public** or **Private** visibility.

### Step 2: Push Repository to Hugging Face
Clone your Space repository and copy the project files, or push this repository directly to HF Spaces:

```bash
git remote add hf https://huggingface.co/spaces/<YOUR_USERNAME>/<SPACE_NAME>
git push hf main
```

### Step 3: Configure Environment Variables
In your Hugging Face Space settings under **Variables and Secrets**, add the following environment variables:

| Key | Example / Value | Description |
|-----|-----------------|-------------|
| `SECRET_KEY` | `your-django-secret-key-here` | Production Django secret key |
| `ALLOWED_HOSTS` | `*.hf.space,localhost` | Allowed domain names |
| `DEBUG` | `False` | Turn off debug mode in production |
| `DATABASE_URL` | `postgres://user:pass@host:5432/dbname` | Managed PostgreSQL DB (Neon/Supabase) |

> **Note**: If `DATABASE_URL` is omitted, the application will automatically fall back to an internal SQLite database for quick evaluation.

---

## 2. Vercel Deployment (Serverless WSGI)

Vercel provides instant global serverless deployment for Python WSGI applications.

### Step 1: Install Vercel CLI & Login
```bash
npm install -g vercel
vercel login
```

### Step 2: Deploy to Vercel
Run the deploy command from the repository root:

```bash
vercel
```

For production deployment:
```bash
vercel --prod
```

### Step 3: Configure Environment Variables in Vercel
In your Vercel Project Dashboard (**Settings -> Environment Variables**), add:

| Key | Example / Value | Description |
|-----|-----------------|-------------|
| `SECRET_KEY` | `your-django-secret-key-here` | Django secret key |
| `ALLOWED_HOSTS` | `.vercel.app,localhost` | Allowed host patterns |
| `DEBUG` | `False` | Production mode |
| `DATABASE_URL` | `postgres://user:pass@ep-xyz.neon.tech/neondb` | External PostgreSQL Database |

---

## 3. Architecture & Static Assets Notes

- **Static Files**: Managed automatically using `WhiteNoise`. When deploying, `collectstatic` compiles assets to `staticfiles/`.
- **Database**: Production deployments on Hugging Face or Vercel recommended to use hosted PostgreSQL (e.g., [Neon.tech](https://neon.tech), [Supabase](https://supabase.com), or AWS RDS).
