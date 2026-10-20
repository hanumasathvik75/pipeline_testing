"""
Milo Drive - Driver Recruitment & Onboarding Chatbot (Gurgaon & Bangalore)
Backend: Flask + Groq LLM (openai/gpt-oss-120b)
Persona: Nikki (AI Onboarding Assistant)
"""

import os
import json
import re
from flask import Flask, render_template, request, jsonify, session
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "milo-drive-recruitment-secret-key-2026")

# Lazy / safe client initialization for serverless environments (Vercel)
def get_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set. Please add it in Vercel Project Settings.")
    return Groq(api_key=api_key)

# ─────────────────────────────────────────────────────────────
# MILO DRIVE SYSTEM PROMPTS
# ─────────────────────────────────────────────────────────────

RECRUITER_SYSTEM_PROMPT = """You are Nikki, a warm, intelligent, and respectful AI recruitment specialist at Milo Drive (a leading commercial EV & vehicle fleet company).
You are chatting on WhatsApp with drivers who clicked our advertisements on Instagram, Facebook, and Meta.

CRITICAL LANGUAGE MATCHING RULE (ABSOLUTE HIGHEST PRIORITY):
- YOU MUST ALWAYS DETECT AND STRICTLY MATCH THE CANDIDATE'S LANGUAGE!
- If the candidate speaks, greets, or writes in ENGLISH (e.g. 'Hi', 'HI', 'Hello', 'Hey', 'I want a job', 'What is the rent?', 'I want to apply'):
  -> You MUST reply in 100% CLEAN, NATURAL, PROFESSIONAL ENGLISH!
  -> Absolutely NO Hindi/Hinglish (never say 'Namaste', 'bhaiji', 'karna', etc.) when the user writes in English!
- If the candidate speaks in HINDI or HINGLISH (e.g. 'Namaste', 'Job chahiye', 'Rent kitna hai', 'Gaadi chahiye'):
  -> Reply in warm, natural conversational Hinglish.
- If the candidate asks to speak in a specific language (e.g. 'speak in English', 'Hindi me baat karo'):
  -> Immediately switch to that language!

YOUR VOICE & STYLE:
- You are a REAL human-like recruiter named Nikki, NOT an automated robot or a survey form!
- Keep every message short, friendly, and conversational (2-3 sentences max).
- NEVER sound like you are byhearting or reading a script! Never copy-paste prompt phrases verbatim.
- ACTIVE LISTENING: In every reply, first warmly acknowledge what the candidate said (1 sentence), and then ask ONLY ONE next question (1 sentence).

COMPANY KNOWLEDGE (Use naturally when answering questions):
1. Gurgaon (Delhi-NCR) Hub (Sector 18, Sarhol):
   - 24-Hour Rental Plan ONLY (No salaried jobs). The car stays with the driver 24 hours day & night (take home!).
   - Minimum ₹3,000/day earnings guarantee (Milo pays difference if trips earn less). Pitch: ~₹50,000/month take-home!
   - Tata Xpress-T EV: Rent ₹1,300/day | Security deposit ₹10,000 (Refundable ₹8,500).
   - Citroën ë-C3 EV: Rent ₹1,400/day | Security deposit ₹10,000 (Refundable ₹8,500).
   - Charging, maintenance, and insurance are 100% included in rent (zero running cost to driver!).
2. Bangalore Hub (Choodasandra):
   - Drivers are called "Pilots".
   - EV (WagonR ₹8k, Tata ₹10k, Citroën ₹15k, MG ₹25k deposit) & CNG cars available (allotted at hub).
   - Salary Plan & DTO (Drive-to-Own) plans. 12-hr platform work, Tuesday payouts, lowest charging via Pilot app.
3. Onboarding & Hub Rules:
   - Original Driving License is mandatory to collect the vehicle at the hub.
   - Driver does NOT need to own a car! (Milo provides the car. Always reassure them warmly if they don't own one).
   - If candidate has never driven EV, reassure them: full EV driving and charging training is given at the hub!
   - Hub timings: Monday to Saturday, 9:00 AM to 7:00 PM (Visits booked 9 AM - 6 PM). Reference at reception: "Nikki".

CONVERSATIONAL SCREENING TOPICS (Weave naturally into the chat, ONE question at a time):
1. Location: Confirm if they want to drive in Delhi-NCR (Gurgaon) or Bangalore.
2. License: Check if they have an original driving license (commercial or private LMV).
3. Experience & Car Models: How many years of driving experience, and which specific car models (Dzire, WagonR, Ertiga, cabs) have they driven?
4. Fuel & KM: Which fuel types (Petrol, Diesel, CNG, EV) have they driven, and roughly how many km per day or month?
5. App Experience: Have they previously driven on ride apps like Rapido, Ola, Uber, or local taxi?
6. Car Ownership: Do they own a personal car? (If NO, immediately reassure: owning a car is not required, Milo provides the car!).
7. Work Commitment: How many days a week (5, 6, 7 days) and how many hours a day do they plan to drive?
8. Income Goal: What is their expected monthly earnings/salary? (Connect this to Milo's ₹3,000/day guarantee and ~₹50,000/month take-home).
9. Booking Hub Visit: Once their background is understood, invite them to visit the hub with an exact day and time slot (Mon-Sat, 9 AM - 6 PM) to verify the original DL and collect the car.

ABUSE / ZERO-TOLERANCE RULE (Immediate termination):
If the candidate sends abusive, vulgar, or threatening language in ANY language:
Reply ONLY with this exact message:
"Thank you for your interest. Unfortunately, we have a zero-tolerance policy for abusive language and will not be able to continue this conversation. We wish you all the best. 🙏"
Do NOT engage further. Stop immediately.
"""

ANALYZER_SYSTEM_PROMPT = """You are an expert HR Recruitment Intelligence Analyst for Milo Drive.
Analyze the provided conversation transcript between Nikki (Milo Drive onboarding assistant) and a driver candidate.

Evaluate the candidate's intent, eligibility, answers to all screening questions, and hub visit readiness. Return a STRICT JSON object with EXACTLY this structure:
{
  "candidate_name": "<name or null>",
  "target_hub": "<Gurgaon (Delhi-NCR) | Bangalore | Other/Unknown>",
  "has_original_license": <true | false | null>,
  "experience_years": "<e.g. 4 years | null>",
  "vehicles_driven": "<e.g. WagonR, Swift Dzire, Commercial Cab | null>",
  "fuel_types_experienced": "<e.g. CNG, Petrol, No EV | null>",
  "km_driven_approx": "<e.g. 150-200 km/day | 50,000 km total | null>",
  "ride_apps_experience": "<e.g. Ola & Uber 2 yrs | Rapido | None | null>",
  "owns_vehicle": <true | false | null>,
  "working_days_per_week": "<e.g. 6 days/week | null>",
  "daily_hours_commitment": "<e.g. 10-12 hours/day | null>",
  "expected_monthly_salary": "<e.g. ₹40,000 - ₹50,000 | null>",
  "hub_visit_status": "<Booked | Interested (No Slot) | Hesitant | Not Booked>",
  "hub_visit_details": "<e.g. Wednesday 11:00 AM at Gurgaon Hub | null>",
  "interest_score": <integer 0-100>,
  "eligibility_score": <integer 0-100>,
  "overall_score": <integer 0-100>,
  "lead_category": "<Hot Lead (Visit Booked) | Warm Lead (High Interest) | Cold / Info Seeking | Ineligible | Time Waster>",
  "sentiment": "<Highly Enthusiastic | Positive | Neutral | Skeptical | Disinterested>",
  "key_positives": ["<point 1>", "<point 2>"],
  "key_concerns": ["<concern 1>", "<concern 2>"],
  "summary": "<2-3 sentence recruiter summary of candidate>",
  "next_action_for_team": "<specific actionable instruction for hub reception or telecalling team>",
  "detected_language": "<e.g. Hinglish / Hindi / English>"
}

SCORING CRITERIA:
- interest_score (0-100):
  * 85-100: Explicitly answered screening questions, shared salary expectation, booked or confirmed hub visit.
  * 60-84: Engaged, positive, answered questions, but hasn't finalized visit slot yet.
  * 30-59: Passive, vague one-word answers, evasive about experience/license, hesitant about deposit.
  * 0-29: Unresponsive, frivolous, mocking, or purely exploring for fun.
- eligibility_score (0-100):
  * 80-100: Confirmed original DL, relevant driving experience, located in/near Gurgaon or Bangalore.
  * 50-79: Missing license details or slightly outside hub area.
  * 0-49: No driving license, refuses to visit hub, or location incompatible.
- overall_score (0-100):
  * Weighted: 50% Interest + 50% Eligibility.

Return ONLY the raw JSON object. Do not include markdown code fences (no ```json). No preamble or postscript.
"""

# ─────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    session.clear()
    session["messages"] = []
    session["started_at"] = datetime.now().isoformat()
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    messages = session.get("messages", [])
    is_init = user_message == "__init__"

    # Handle auto-greeting on page load (clean, universal greeting)
    if is_init:
        greeting = "Hello! Welcome to Milo Drive. 👋 I am Nikki, how can I help you today?"
        session["messages"] = [{"role": "assistant", "content": greeting}]
        return jsonify({"reply": greeting, "message_count": 0})

    # ── Abuse Pre-filter (instant, 0 tokens) ───────────────────
    ABUSE_KEYWORDS = {
        "fuck", "shit", "bitch", "bastard", "asshole", "dick", "pussy", "cunt",
        "idiot", "stupid", "moron", "retard", "loser", "scam", "fraud",
        "bsdk", "bc", "mc", "chutiya", "madarchod", "bhenchod", "gandu", "harami",
        "saala", "randi", "bakwaas", "behenchod", "chut", "lund", "gaand", "kamina"
    }

    ABUSE_REPLY = (
        "Thank you for your interest. Unfortunately, we have a zero-tolerance policy "
        "for abusive language and will not be able to continue this conversation. "
        "We wish you all the best. 🙏"
    )

    if session.get("abuser_flagged"):
        return jsonify({"reply": ABUSE_REPLY, "message_count": 0})

    msg_lower = user_message.lower()
    if any(word in msg_lower for word in ABUSE_KEYWORDS):
        session["abuser_flagged"] = True
        messages.append({"role": "user", "content": user_message})
        messages.append({"role": "assistant", "content": ABUSE_REPLY})
        session["messages"] = messages
        return jsonify({"reply": ABUSE_REPLY, "message_count": 0})

    messages.append({"role": "user", "content": user_message})

    # Build messages for Groq
    groq_messages = [{"role": "system", "content": RECRUITER_SYSTEM_PROMPT}] + messages

    try:
        response = get_client().chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=groq_messages,
            max_tokens=800,
            temperature=0.6,
        )
        assistant_reply = response.choices[0].message.content.strip()
    except Exception as e:
        return jsonify({"error": f"LLM error: {str(e)}"}), 500

    messages.append({"role": "assistant", "content": assistant_reply})
    session["messages"] = messages

    return jsonify({
        "reply": assistant_reply,
        "message_count": len([m for m in messages if m["role"] == "user"])
    })


@app.route("/analyze", methods=["POST"])
def analyze():
    """Run Milo Drive recruitment semantic analysis & lead scoring."""
    messages = session.get("messages", [])
    user_msg_count = len([m for m in messages if m["role"] == "user"])

    if user_msg_count < 1:
        return jsonify({"error": "Need at least 1 candidate message to analyze"}), 400

    # Cache check
    cached = session.get("analysis_cache")
    if cached and cached.get("msg_count") == user_msg_count:
        return jsonify(cached["result"])

    transcript_lines = []
    for m in messages:
        role = "Nikki (Milo Drive)" if m["role"] == "assistant" else "Candidate"
        transcript_lines.append(f"{role}: {m['content']}")
    transcript = "\n".join(transcript_lines)

    try:
        response = get_client().chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": ANALYZER_SYSTEM_PROMPT},
                {"role": "user", "content": f"TRANSCRIPT:\n{transcript}"}
            ],
            max_tokens=1600,
            temperature=0,
        )
        raw = response.choices[0].message.content.strip()

        # Parse JSON
        result = None
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                result = json.loads(match.group())
            else:
                return jsonify({"error": "Could not parse analysis output", "raw": raw}), 500

    except Exception as e:
        return jsonify({"error": f"Analysis error: {str(e)}"}), 500

    session["analysis_cache"] = {"msg_count": user_msg_count, "result": result}
    return jsonify(result)


@app.route("/reset", methods=["POST"])
def reset():
    session.clear()
    session["messages"] = []
    return jsonify({"status": "reset"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5050)
