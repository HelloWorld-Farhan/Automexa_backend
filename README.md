# ⚡ Automexa Backend — Cloud AI Reasoning & RAG Intelligence Engine

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/Google%20Gemini-2.5%20Flash-8E75B2?style=for-the-badge&logo=google&logoColor=white"/>
  <img src="https://img.shields.io/badge/ChromaDB-Vector%20Store-FF6F00?style=for-the-badge&logo=databricks&logoColor=white"/>
  <img src="https://img.shields.io/badge/Render-Cloud%20Hosting-46E3B7?style=for-the-badge&logo=render&logoColor=white"/>
  <img src="https://img.shields.io/badge/License-MIT-brightgreen?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Version-1.0.0-blue?style=for-the-badge"/>
</p>

<p align="center">
  <strong>Automexa Backend</strong> is the dedicated cloud reasoning and vector intelligence microservice for the Automexa autonomous job application network. Built with FastAPI, Google Gemini 2.5 Flash, and ChromaDB, it provides sub-second contextual answers to complex job application screening questions.
</p>

---

## ✨ Features

- **Gemini 2.5 Flash Form Reasoner** — High-speed multimodal intelligence interpreting form questions, options, radio buttons, and numeric constraints.
- **Dynamic Context Vectorization** — ChromaDB vector database embedding candidate resume markdown, compensation history, and notice periods.
- **Universal CORS Middleware** — Seamless, authenticated communication with the native Automexa Android client and desktop runners.
- **Intelligent Deterministic Fallback** — Built-in safeguard ensuring continuous operation even when external cloud API quotas are constrained.
- **Render 1-Click Infrastructure Blueprint** — Native `render.yaml` configuration for automated zero-configuration continuous deployments.

---

## 🔗 Project Repositories

| Repository | Purpose | Status |
|---|---|---|
| [Automexa_backend](https://github.com/HelloWorld-Farhan/Automexa_backend) | Dedicated Cloud AI RAG & Form Reasoning Service | Active |
| [Automexa](https://github.com/HelloWorld-Farhan/Automexa) | Native Android Client, Accessibility Engine & CI/CD | Active |

---

## 🖼 Architecture

```text
Automexa Mobile / Desktop Client
              │
              ▼ (POST /api/v1/reason-field)
┌────────────────────────────────────────────────────────┐
│                   FASTAPI WEB SERVICE                  │
│                                                        │
│  1. Receive Question: "Notice period in days?"         │
│  2. ChromaDB Vector Search ──► Matches Candidate Fact: │
│                                "Notice Period: 30 days"│
│  3. Gemini 2.5 Flash ────────► Synthesizes Form Answer │
│                                { "answer": "30" }      │
└────────────────────────────────────────────────────────┘
              │
              ▼ (JSON Response)
Automexa Client Fills Input & Clicks Next
```

---

## 🚀 How to Connect with Render (Simple Step-by-Step Guide)

Follow these simple steps to deploy your backend online for free in less than 3 minutes:

### Step 1: Open Render
1. Go to **[https://render.com](https://render.com)**.
2. Sign in with your **GitHub account**.

### Step 2: Create a New Web Service
1. In your Render Dashboard, click the blue **New +** button at the top right.
2. Select **Web Service**.
3. Choose **Build and deploy from a Git repository** and click **Next**.

### Step 3: Connect Your GitHub Repository
1. In the search box, find **`Automexa_backend`** (or paste `https://github.com/HelloWorld-Farhan/Automexa_backend`).
2. Click **Connect**.

### Step 4: Configure Settings
Fill in the basic settings (Render will auto-fill most of this from `render.yaml`):
* **Name**: `automexa-backend`
* **Region**: Oregon (US West) or closest to you
* **Branch**: `main`
* **Language**: `Python 3`
* **Build Command**: `pip install -r requirements.txt`
* **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
* **Instance Type**: Select **Free** ($0/month)

### Step 5: Add Your Gemini API Key
1. Scroll down to the **Environment Variables** section.
2. Click **Add Environment Variable**:
   * **Key**: `GEMINI_API_KEY`
   * **Value**: *(Paste your Gemini API Key from Google AI Studio)*
3. Click the blue **Create Web Service** button at the bottom.

Render will build and deploy your service in about 1 minute. Once finished, you will see a public URL like:
```text
https://automexa-backend.onrender.com
```

---

## 📡 API Endpoints

### 1. Health Check
`GET /health`
```json
{
  "status": "healthy",
  "service": "Automexa Backend"
}
```

### 2. Form Field Reasoning
`POST /api/v1/reason-field`
* **Request:**
  ```json
  {
    "question": "How many years of commercial experience do you have with Kotlin?",
    "field_type": "number",
    "options": []
  }
  ```
* **Response:**
  ```json
  {
    "answer": "4",
    "confidence": 0.98,
    "reasoning": "Candidate profile confirms 4 years of professional Kotlin and Android development."
  }
  ```

### 3. Sync Candidate Profile
`POST /api/v1/sync-profile`
* **Request:**
  ```json
  {
    "user_id": "farhan",
    "full_name": "Farhan Khalid",
    "resume_markdown": "Senior Software Engineer with 4 years building native mobile and AI systems.",
    "primary_skills": ["Kotlin", "Android", "Python", "FastAPI", "Gemini"],
    "current_ctc": "12 LPA",
    "expected_ctc": "18 LPA",
    "notice_period_days": 30
  }
  ```

---

## 👨💻 Author

**Farhan Khalid**  
📧 farhankhalid17968@gmail.com  
🔗 [LinkedIn](https://www.linkedin.com/in/farhan-khalid-117514259/)  
🐙 [GitHub](https://github.com/HelloWorld-Farhan)

---

## 📄 License

```text
MIT License

Copyright (c) 2026 Farhan Khalid

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

<p align="center">Made with ❤️ — Python 3.11 · FastAPI · Google Gemini 2.5 Flash · ChromaDB · Render</p>

