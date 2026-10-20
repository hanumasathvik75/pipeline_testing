# Milo Drive - AI Driver Recruitment & Onboarding Chatbot

A WhatsApp-style AI onboarding chatbot for Milo Drive (Gurgaon & Bangalore hubs) powered by Groq LLM and Flask.

## Features
- **Dual-Hub Support**:
  - **Gurgaon (Delhi-NCR)**: 24-hr EV Rental (Tata Xpress-T & Citroën ë-C3), ₹3,000/day earnings guarantee (~₹50,000/month take-home), free charging, maintenance & insurance.
  - **Bangalore**: EV & CNG fleet, Salary & DTO (Drive-To-Own) plans, Tuesday weekly payouts, Pilot app.
- **Bilingual Conversations**: Intelligent language detection supporting English, Hindi, and Hinglish with 1-click language toggles.
- **Screening & Qualification**: Explores experience, vehicle models, fuel types, daily km, car ownership, work schedule, and books hub visits.
- **Semantic Lead Scoring**: Real-time evaluation of candidate interest, eligibility, and lead category (`Hot Lead`, `Warm Lead`, `Cold Lead`).

---

## Deploy to Vercel (1-Click)

1. **Push this repository to GitHub**:
   ```bash
   git remote add origin https://github.com/hanumasathvik75/pipeline_testing.git
   git branch -M main
   git push -u origin main
   ```

2. **Import into Vercel**:
   - Go to [vercel.com](https://vercel.com) and click **"Add New..."** → **"Project"**.
   - Select your GitHub repository (`pipeline_testing`).
   - Framework Preset: **Other**.
   - Root Directory: `./` (or directory where `app.py` is located).

3. **Configure Environment Variables in Vercel**:
   - Under **Environment Variables**, add:
     - `GROQ_API_KEY`: `your_groq_api_key_here`
     - `SECRET_KEY`: `milo-drive-production-secret-2026`
   - Click **Deploy**!

Vercel will build and deploy the application with a public `https://your-project.vercel.app` URL.
