# 🎙 Mykare Voice AI Engineer Task

**Build a real-world AI voice agent that can talk, understand, and take actions.**

## ⏱ Timeline

**24-48 hours
Expected effort:** 3-6 hours

## 🎯 What You Need to Build

A **web-based AI voice agent** that can:
● 🎤 Listen to user speech (speech recognition)
● 🧠 Understand intent
● 🗣 Respond with natural voice (synthesized voice)
● 👤 Show a talking avatar (synced with speech)
● 📅 Book & manage appointments
● 📝 Summarize the conversation
Think of it like a **front-desk AI for healthcare**

## 🛠 Suggested Tech Stack

```
Layer Options
Voice LiveKit Agents
STT Deepgram
TTS Cartesia
Avatar Tavus / Beyond Presence
LLM OpenAI / Claude / OpenRouter or any other
Backend Python
```

```
Frontend Vite / Next.js
DB SQLite/ Supabase / Any Other Database
```
## ✅ Core Requirements

### 1. 🎙 Voice Conversation

```
● Hear and understand user speech
● Handle 5+ back-and-forth exchanges
● Maintain context
● Response latency: < 3–5 sec
● The call interface
```
### 2. 👤 Avatar

```
● Display a speaking avatar
● Sync lips with voice
● Smooth experience (no lag/freezing)
```
### 3. ⚙ Tool Calling (VERY IMPORTANT)

Your agent must intelligently call these actions:
🔹 **identify_user**
● Ask phone number
● Use it as unique ID
🔹 **fetch_slots**
● Return available slots (can hardcode)
🔹 **book_appointment**
● Save in DB
● Prevent double booking
● Confirm clearly (date, time)
🔹 **retrieve_appointments**


● Show user’s past bookings
🔹 **cancel_appointment**
🔹 **modify_appointment**
🔹 **end_conversation**

### ⚠ Must Extract from conversation:

```
● Name
● Phone number
● Date
● Time
● Intent
```
### 🖥 UI Requirement

Whenever a tool is called:
● Show it visually on screen
● Example:
○ “Fetching slots...”
○ “Booking confirmed ✅”

### 4. 📝 Call Summary (Critical)

At the end:
● Summary of conversation
● List of appointments
● User preferences (if any)
● Timestamp
● Show on UI
⏱ Generate within **10 seconds**

## 📦 Deliverables

1. Backend GitHub repo
2. Frontend GitHub repo
3. Live deployed link


4. Demo Screen Recording or Screenshots

## 📊 Evaluation Criteria

### 🔴 Must Have

```
● End-to-end working system
● Voice + tool calling + DB working
● Smooth conversation flow
```
### 🟡 Good to Have

```
● Clean UI
```
### 🟢 Bonus

```
● Cost per call breakdown
● Smart edge-case handling
```

