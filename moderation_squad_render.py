# ═══════════════════════════════════════════════════════════════
#  MODERATION SQUAD — Full Platform
#  Theme : White + #C8332A Red (ModSquad brand)
#  Tunnel: Cloudflare (primary) → ngrok (fallback)
# ═══════════════════════════════════════════════════════════════
import threading, time, random, os, json
from datetime import datetime
from flask import Flask, request, session, redirect, jsonify
import requests as req

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "modsquad_2025_key_secure")

BREVO_KEY    = "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"
SENDER_EMAIL = "australiapaper33@gmail.com"
SENDER_NAME  = "Moderation Squad"
NGROK_TOKEN  = "39yG9aLiiLe8B2XYfYq9IwwmZ1x_nfhqneWAfjHSvNk7TMoN"
S_EMAIL      = "support@moderationsquad.com"
S_PHONE      = "+1 (888) 266-3763"

WHITELIST = ["australiapaper33@gmail.com","wizardacademic@gmail.com","celestinerotich969@gmail.com"]

otp_store={}; user_store={}; notif_store={}; chat_store={}; saved_store={}

# ── PIN STORE — persisted to disk so changes survive restarts ──
PIN_FILE = "/tmp/ms_pins.json"
_DEFAULT_PINS = {
    # pin = login PIN
    # devices = list of device IDs that have logged into this account
    # first_device = the first device that logged in (only one that can change PIN)
    # NO device limit — any number of devices can access the same account
    # BUT each device can only ever belong to ONE account
    "australiapaper33@gmail.com":  {"pin":"1234","devices":[],"first_device":None},
    "wizardacademic@gmail.com":    {"pin":"5678","devices":[],"first_device":None},
    "celestinerotich969@gmail.com":{"pin":"9012","devices":[],"first_device":None},
}
def load_pins():
    if os.path.exists(PIN_FILE):
        try:
            with open(PIN_FILE,"r") as f: data=json.load(f)
            # Merge defaults for missing users + migrate old format
            for k,v in _DEFAULT_PINS.items():
                if k not in data:
                    data[k]=v
                else:
                    # Migrate old single device_id format to new devices list
                    if "device_id" in data[k] and "devices" not in data[k]:
                        old_dev=data[k].pop("device_id")
                        data[k]["devices"]=[old_dev] if old_dev else []
                        data[k]["first_device"]=old_dev
            return data
        except: pass
    return dict({k:dict(v) for k,v in _DEFAULT_PINS.items()})
def save_pins():
    try:
        with open(PIN_FILE,"w") as f: json.dump(pin_store,f)
    except: pass
pin_store = load_pins()

# ── Celestine already applied for Email Response Support (persists across restarts) ──
user_store["celestinerotich969@gmail.com"] = {
    "email": "celestinerotich969@gmail.com", "name": "Celestine Rotich",
    "level": "Newcomer", "jobs_done": 0, "earned": 0.0,
    "member_since": "Feb 2025", "avatar": None,
    "applied_jobs": [{
        "title": "Email Response Support", "company": "SmallBiz Store",
        "pay": "$5/hr", "hrs": "8 hrs/wk", "icon": "📧",
        "status": "Under Review", "date": "Feb 2025", "days": 2,
    }],
    "verifications": {
        "email": True, "residence": True, "id": True,
        "tax": True, "payment": False, "background": True
    }
}

SOCIAL=[
    ("https://www.facebook.com/ModSquad/","Facebook","M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"),
    ("https://twitter.com/ModSquad","X / Twitter","M23 3a10.9 10.9 0 0 1-3.14 1.53A4.48 4.48 0 0 0 22.43.36a9 9 0 0 1-2.88 1.1A4.52 4.52 0 0 0 16.11 0c-2.5 0-4.52 2.02-4.52 4.52 0 .35.04.7.11 1.03C7.69 5.4 4.07 3.58 1.64.9a4.52 4.52 0 0 0-.61 2.27c0 1.57.8 2.95 2.01 3.76a4.5 4.5 0 0 1-2.05-.57v.06c0 2.19 1.56 4.02 3.63 4.43a4.5 4.5 0 0 1-2.04.08 4.52 4.52 0 0 0 4.22 3.14A9.06 9.06 0 0 1 0 19.54a12.77 12.77 0 0 0 6.92 2.03c8.3 0 12.84-6.88 12.84-12.85 0-.2 0-.39-.01-.58A9.17 9.17 0 0 0 23 3z"),
    ("https://www.instagram.com/modsquadinc/","Instagram","M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37zm1.5-4.87h.01M6.5 6.5h11a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-11a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2z"),
    ("https://www.linkedin.com/company/modsquad","LinkedIn","M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6zM2 9h4v12H2z M4 6a2 2 0 1 0 0-4 2 2 0 0 0 0 4z"),
    ("https://www.youtube.com/@ModSquadInc","YouTube","M22.54 6.42a2.78 2.78 0 0 0-1.95-1.96C18.88 4 12 4 12 4s-6.88 0-8.59.46A2.78 2.78 0 0 0 1.46 6.42 29 29 0 0 0 1 12a29 29 0 0 0 .46 5.58 2.78 2.78 0 0 0 1.95 1.96C5.12 20 12 20 12 20s6.88 0 8.59-.46a2.78 2.78 0 0 0 1.96-1.96A29 29 0 0 0 23 12a29 29 0 0 0-.46-5.58zM9.75 15.02V8.98L15.5 12l-5.75 3.02z"),
]

ALL_JOBS=[
 {"pg":1,"icon":"💬","title":"Basic Chat Monitor","company":"RetailBrand Co.","pay":"$5/hr","hrs":"10 hrs/wk","desc":"Monitor customer chat queues and flag inappropriate content. No experience required. Perfect first role.","locked":False},
 {"pg":1,"icon":"📧","title":"Email Response Support","company":"SmallBiz Store","pay":"$5/hr","hrs":"8 hrs/wk","desc":"Respond to customer emails using provided templates. Fully flexible schedule, work anytime you like.","locked":False},
 {"pg":1,"icon":"🛡️","title":"Forum Comment Moderator","company":"CommunityHub","pay":"$6/hr","hrs":"12 hrs/wk","desc":"Review forum posts and comments, remove policy violations. Great introduction to moderation work.","locked":False},
 {"pg":1,"icon":"🎯","title":"Standard Chat Moderator","company":"TechCorp Inc.","pay":"$12/hr","hrs":"25 hrs/wk","desc":"Full-time chat moderation for a leading tech platform with millions of daily users.","locked":False},
 {"pg":1,"icon":"📝","title":"Content Reviewer","company":"MediaFlow","pay":"$11/hr","hrs":"20 hrs/wk","desc":"Review user-generated content for policy compliance across a major media platform.","locked":False},
 {"pg":2,"icon":"📱","title":"Social Media Moderator","company":"BrandBoost","pay":"$14/hr","hrs":"30 hrs/wk","desc":"Moderate comments and posts across Facebook, Instagram, and Twitter for major brands.","locked":True,"req":"🟡 Senior (21+ jobs)"},
 {"pg":2,"icon":"🎮","title":"Gaming Community Mod","company":"GameStream Pro","pay":"$16/hr","hrs":"35 hrs/wk","desc":"Moderate live gaming streams and community Discord servers for a top gaming platform.","locked":True,"req":"🟡 Senior (21+ jobs)"},
 {"pg":2,"icon":"🌐","title":"Multilingual Content Mod","company":"GlobalReach","pay":"$15/hr","hrs":"30 hrs/wk","desc":"Moderate content in English and Spanish across global e-commerce and social platforms.","locked":True,"req":"🟡 Senior (21+ jobs)"},
 {"pg":2,"icon":"🔍","title":"Trust & Safety Analyst","company":"SafeNet Inc.","pay":"$17/hr","hrs":"35 hrs/wk","desc":"Investigate abuse reports, perform account reviews, and escalate complex violation cases.","locked":True,"req":"🟡 Senior (21+ jobs)"},
 {"pg":2,"icon":"📊","title":"Metrics & QA Reviewer","company":"DataMod LLC","pay":"$14/hr","hrs":"25 hrs/wk","desc":"Review moderation quality scores and compile weekly performance and compliance reports.","locked":True,"req":"🟡 Senior (21+ jobs)"},
 {"pg":3,"icon":"🏆","title":"Senior Moderator","company":"MegaCorp Media","pay":"$18/hr","hrs":"40 hrs/wk","desc":"Lead moderation shifts, mentor junior team members, and maintain quality standards.","locked":True,"req":"🔴 Elite (50+ jobs)"},
 {"pg":3,"icon":"👑","title":"Lead Moderator","company":"Enterprise Plus","pay":"$20/hr","hrs":"40 hrs/wk","desc":"Oversee a team of 10+ moderators across multiple client accounts and time zones.","locked":True,"req":"🔴 Elite (50+ jobs)"},
 {"pg":3,"icon":"🔐","title":"Trust & Safety Specialist","company":"SafeNet Inc.","pay":"$22/hr","hrs":"40 hrs/wk","desc":"Senior-level T&S work including policy development and cross-team collaboration.","locked":True,"req":"🔴 Elite (50+ jobs)"},
 {"pg":3,"icon":"📺","title":"Streaming Platform Mod","company":"LiveFeed TV","pay":"$19/hr","hrs":"40 hrs/wk","desc":"Real-time moderation of major live streaming events and viewer chat management.","locked":True,"req":"🔴 Elite (50+ jobs)"},
 {"pg":3,"icon":"💼","title":"Client Account Manager","company":"ModSquad HQ","pay":"$21/hr","hrs":"40 hrs/wk","desc":"Manage client relationships, SLA compliance, and moderation team performance metrics.","locked":True,"req":"🔴 Elite (50+ jobs)"},
 {"pg":4,"icon":"🤖","title":"AI Content Reviewer","company":"TechAI Labs","pay":"$20/hr","hrs":"40 hrs/wk","desc":"Review AI-generated content for safety, quality, and policy compliance at scale.","locked":True,"req":"🔴 Elite (50+ jobs)"},
 {"pg":4,"icon":"🌍","title":"Global Mod Team Lead","company":"WorldMod Co.","pay":"$22/hr","hrs":"40 hrs/wk","desc":"Lead a global team of 20+ moderators operating across 5 continents and time zones.","locked":True,"req":"🔴 Elite (50+ jobs)"},
 {"pg":4,"icon":"🎬","title":"Entertainment Mod Spec","company":"StudioX","pay":"$19/hr","hrs":"40 hrs/wk","desc":"Moderate fan communities for major entertainment brands, film studios, and award shows.","locked":True,"req":"🔴 Elite (50+ jobs)"},
 {"pg":4,"icon":"🏥","title":"Healthcare Comm Mod","company":"MedConnect","pay":"$20/hr","hrs":"35 hrs/wk","desc":"Moderate sensitive healthcare community discussions with empathy and compliance focus.","locked":True,"req":"🔴 Elite (50+ jobs)"},
 {"pg":4,"icon":"🎓","title":"EdTech Moderator","company":"LearnWorld","pay":"$18/hr","hrs":"30 hrs/wk","desc":"Moderate online learning platforms, student discussion forums, and virtual classrooms.","locked":True,"req":"🔴 Elite (50+ jobs)"},
]

COURSES=[
 {"id":0,"icon":"🛡️","title":"Chat Moderation Fundamentals","level":"Beginner","dur":"4 hrs","desc":"Learn the basics of professional chat moderation, community guidelines, and escalation procedures.","locked":False,
  "lessons":[
   ("What Is Chat Moderation?","Chat moderation is the practice of monitoring and managing online conversations to ensure they remain safe, respectful, and on-topic.\n\nAs a moderator, you are the first line of defense against harmful content. Your work directly impacts thousands of users every day.\n\n📌 KEY RESPONSIBILITIES:\n• Monitor live chat streams in real-time\n• Identify and remove policy-violating content\n• Issue warnings and bans to rule-breaking users\n• Escalate serious issues to senior staff immediately\n• Keep accurate records of all moderation actions\n\n💡 WHY IT MATTERS:\nResearch shows that 70% of users leave a platform permanently after experiencing harassment. Your role protects the community and keeps users engaged.\n\n✅ After this lesson you should understand the core purpose of chat moderation and why it matters for online platforms."),
   ("Community Guidelines","Every platform has its own community guidelines, but they share common themes.\n\n✅ GENERALLY ALLOWED:\n• Constructive criticism and respectful debate\n• Sharing personal experiences and opinions\n• Asking questions and seeking help\n• Creative content within platform theme\n\n❌ NOT ALLOWED:\n• Hate speech or discrimination\n• Harassment, bullying, or targeted attacks\n• Spam, self-promotion, or repetitive posting\n• Graphic violence or disturbing imagery\n• Doxxing — sharing private personal information\n• Threats of violence, real or implied\n\n📌 KEY PRINCIPLE — CONSISTENCY:\nApply rules the same way to every user, regardless of their status, popularity, or how long they have been on the platform.\n\n💡 PRO TIP: When unsure whether content violates guidelines, ask: 'Would this make another user feel unsafe or unwelcome?' If yes, it likely warrants action."),
   ("Handling Difficult Users","Not every user you deal with will be cooperative. Here are proven strategies:\n\n😤 TYPES OF DIFFICULT USERS:\n• The Arguer — disputes every moderation action\n• The Rule-Pusher — constantly tests boundaries\n• The Evader — creates new accounts to avoid bans\n• The Harasser — targets specific users or moderators\n• The Spammer — floods chat with repetitive content\n\n🛠️ PROVEN STRATEGIES:\n1. STAY CALM — Never respond emotionally. All actions must be professional.\n2. WARN FIRST — Give a clear, specific warning before taking action.\n3. DOCUMENT — Screenshot and log all incidents with timestamps.\n4. BE CONSISTENT — Apply rules the same way every time.\n5. ESCALATE — Know exactly when and how to escalate.\n6. SELF-CARE — Moderation can be mentally taxing. Use support resources.\n\n📝 SAMPLE WARNING MESSAGE:\n'Hi [username] — your recent message was removed for violating our community guidelines on [specific rule]. This is your first warning. A second violation will result in a temporary suspension.'\n\n⚠️ REMEMBER: You enforce platform rules, not your personal opinions."),
   ("Escalation Procedures","Knowing when and how to escalate is one of the most critical moderation skills.\n\n🚨 ALWAYS ESCALATE IMMEDIATELY FOR:\n• Any threats of violence or self-harm\n• Illegal content (CSAM, terrorism, fraud)\n• Coordinated harassment campaigns\n• Potential account hacking or identity theft\n• Viral or media-coverage incidents\n• Any situation where you feel uncertain\n\n📋 HOW TO ESCALATE PROPERLY:\n1. DO NOT delete the content before escalating — it is evidence\n2. Screenshot the content with timestamps visible\n3. Note the username, user ID, and post URL\n4. Use the designated escalation channel immediately\n5. Write a clear, factual summary — no personal opinions\n6. Follow up if no response within 1 hour\n\n💡 GOLDEN RULE: When in doubt, escalate. It is always better to escalate unnecessarily than to miss a serious incident."),
   ("Quiz & Certification 🎓","FINAL ASSESSMENT — Chat Moderation Fundamentals\n\n❓ Q1: What should you do FIRST when encountering a rule violation?\nA) Ban the user immediately\nB) Issue a clear, specific warning ✅ CORRECT\nC) Ignore it if it seems minor\nD) Ask other users what they think\n\n❓ Q2: When should you escalate an issue?\nA) Only for the most extreme content\nB) Whenever you feel uncertain ✅ CORRECT\nC) Never — handle everything yourself\nD) Only when your manager is online\n\n❓ Q3: What is doxxing?\nA) Sharing funny memes in chat\nB) Posting too many messages quickly\nC) Sharing someone's private personal information ✅ CORRECT\nD) Using multiple accounts\n\n❓ Q4: Why must you NOT delete content before escalating?\nA) It takes too much time\nB) The content may be needed as evidence ✅ CORRECT\nC) Deletion is against company policy\nD) Users might notice\n\n🎉 CONGRATULATIONS!\nYou have successfully completed Chat Moderation Fundamentals!\n\n🏆 Certificate: Chat Moderation Fundamentals — Beginner\n📅 Issued: {}\n\nThis certificate has been recorded on your profile. Complete more courses to unlock advanced positions!".format(datetime.now().strftime('%B %d, %Y')))
  ]},
 {"id":1,"icon":"📋","title":"Content Policy & Guidelines","level":"Beginner","dur":"2 hrs","desc":"Understand content policies, what to flag, and how to handle edge cases professionally.","locked":False,
  "lessons":[
   ("Types of Violating Content","Content violations are organized by severity. Knowing the difference helps you act with the right level of urgency.\n\n🔴 CRITICAL — Remove immediately AND escalate now:\n• Child sexual abuse material (CSAM) — Zero tolerance\n• Credible threats of violence against real people\n• Terrorism recruitment or glorification\n• Detailed instructions for mass violence\n\n🟡 HIGH — Remove AND issue final warning:\n• Targeted hate speech against protected groups\n• Graphic violence without clear news or artistic context\n• Sustained harassment campaigns\n• Explicit sexual content in non-designated spaces\n\n🟢 MEDIUM — Warn user, may remove:\n• Mild profanity or offensive language\n• Off-topic spam or repetitive posts\n• Minor self-promotion outside designated areas\n\n💡 When severity is unclear: Always choose to escalate rather than under-react."),
   ("Edge Cases & Grey Areas","Not everything is black and white. Here's how to handle the most common grey areas:\n\n🎭 SATIRE & PARODY:\nGenuine satire can criticize without violating. Ask:\n• Is satirical intent clear to a reasonable reader?\n• Does it punch down at vulnerable groups?\n• Could it be mistaken for a real threat?\n\n📰 NEWS & DOCUMENTARY CONTENT:\nGraphic content may have legitimate newsworthiness:\n• Is this from a credible journalistic source?\n• Is the graphic element necessary to the story?\n• Has the platform approved news content exceptions?\n\n🌍 CULTURAL CONTEXT:\n• Slang acceptable in one community may be offensive in another\n• Religious references require cultural sensitivity\n• When uncertain, consult your escalation contact\n\n✅ DECISION FRAMEWORK:\n1. Who could be harmed by this content?\n2. What is the most likely intent?\n3. What would a reasonable person think?\n4. When in doubt — escalate."),
   ("Quiz & Certificate 🎓","ASSESSMENT — Content Policy & Guidelines\n\n❓ Q1: A user posts graphic war footage with a news article link. You should:\nA) Delete it immediately\nB) Evaluate newsworthiness and escalate if unsure ✅ CORRECT\nC) Ignore it completely\nD) Ban the user immediately\n\n❓ Q2: A post uses slang that seems offensive. You should:\nA) Always delete it immediately\nB) Consider cultural context and platform norms ✅ CORRECT\nC) Ask users if they found it offensive\nD) Ignore it — slang is never a violation\n\n❓ Q3: What severity level is CSAM content?\nA) Medium\nB) High\nC) Critical — remove and escalate immediately ✅ CORRECT\nD) Low\n\n🎉 CERTIFICATE EARNED!\nContent Policy & Guidelines — Beginner\n📅 {}\n\nYour certification has been recorded on your profile!".format(datetime.now().strftime('%B %d, %Y')))
  ]},
 {"id":2,"icon":"💬","title":"Effective Communication","level":"Beginner","dur":"3 hrs","desc":"Master professional tone, empathy, and de-escalation techniques for difficult interactions.","locked":False,
  "lessons":[
   ("Professional Tone","Every message you send as a moderator represents the platform. Always be:\n\n✅ CLEAR — Be specific about what rule was broken:\n❌ Bad: 'Your post was removed.'\n✅ Good: 'Your post was removed because it contained personal information about another user, violating Section 4.2 of our Community Guidelines.'\n\n✅ NEUTRAL — Show no personal bias:\n❌ Bad: 'I personally find your opinion offensive.'\n✅ Good: 'This content does not meet our community standards for respectful discourse.'\n\n✅ FIRM — Be clear about consequences:\n❌ Bad: 'Maybe try not to do that again?'\n✅ Good: 'This is your first warning. A second violation will result in a 24-hour suspension.'\n\n✅ EMPATHETIC — Acknowledge the user's perspective:\n❌ Bad: 'You broke the rules, end of story.'\n✅ Good: 'I understand this may feel frustrating. Our guidelines apply equally to all users to keep our community safe.'\n\n📝 PERFECT MESSAGE FORMULA:\n1. Acknowledge (briefly)\n2. State the action taken\n3. Cite the specific rule\n4. State consequences for further violations\n5. Keep it under 100 words"),
   ("De-escalation","When a user is angry about a moderation action, your goal is to de-escalate without backing down.\n\n🔥 THE 5-STEP METHOD:\n\nStep 1 — ACKNOWLEDGE frustration:\n'I understand you are frustrated by this decision.'\n\nStep 2 — VALIDATE without agreeing:\n'I can see why this situation feels unfair from your perspective.'\n\nStep 3 — EXPLAIN the rule calmly:\n'Our community guidelines require [specific rule] to protect all members.'\n\nStep 4 — OFFER a path forward:\n'If you believe this was an error, you can submit an appeal through [link].'\n\nStep 5 — SET A LIMIT:\n'I am happy to help, but I will need to end this conversation if it continues to be disrespectful.'\n\n🚫 NEVER:\n• Match their emotional energy\n• Use sarcasm or passive-aggression\n• Make it personal\n• Back down from a correct moderation decision\n• Engage with insults directed at you\n\n💡 GREY ROCK METHOD:\nFor persistently abusive users, become neutral and uninteresting. Give minimal, factual responses only."),
   ("Quiz & Certificate 🎓","ASSESSMENT — Effective Communication\n\n❓ Q1: A user angrily messages after their post was removed. You should:\nA) Ignore them\nB) Apologize and restore the post\nC) Acknowledge frustration, explain the rule, offer appeal process ✅ CORRECT\nD) Immediately ban them\n\n❓ Q2: A good moderation message always includes:\nA) Your personal opinion on the content\nB) The specific rule violated and consequences ✅ CORRECT\nC) A lengthy explanation of all guidelines\nD) An apology\n\n❓ Q3: The Grey Rock Method means:\nA) Banning rude users immediately\nB) Becoming neutral, giving minimal responses to abusive users ✅ CORRECT\nC) Ignoring all messages from difficult users\nD) Escalating every hostile interaction\n\n🎉 CERTIFICATE EARNED!\nEffective Communication — Beginner\n📅 {}\n\nExcellent work! You have completed all available beginner courses. Intermediate courses unlock at Junior level.".format(datetime.now().strftime('%B %d, %Y')))
  ]},
 {"id":3,"icon":"🔒","title":"Trust & Safety Basics","level":"Intermediate","dur":"5 hrs","desc":"Introduction to trust and safety operations, abuse detection, and professional reporting.","locked":True,"lessons":[]},
 {"id":4,"icon":"📊","title":"Data & Reporting","level":"Intermediate","dur":"3 hrs","desc":"Learn to track moderation metrics and write professional incident reports.","locked":True,"lessons":[]},
 {"id":5,"icon":"🏆","title":"Advanced Moderation Techniques","level":"Senior","dur":"6 hrs","desc":"Advanced strategies for high-volume platforms and complex moderation scenarios.","locked":True,"lessons":[]},
]

def brevo(to, subject, html):
    try:
        r=req.post("https://api.brevo.com/v3/smtp/email",
            json={"sender":{"name":SENDER_NAME,"email":SENDER_EMAIL},"to":[{"email":to}],"subject":subject,"htmlContent":html},
            headers={"accept":"application/json","api-key":BREVO_KEY,"content-type":"application/json"},timeout=10)
        print(f"[Brevo] {r.status_code} -> {r.text}")
    except Exception as e:
        print(f"[Brevo ERROR] {e}")

def send_otp(email, otp):
    brevo(email,"Moderation Squad — Secure Login Code",f"""
<div style="font-family:Arial,sans-serif;background:#f5f5f5;padding:40px 0;">
<div style="max-width:560px;margin:0 auto;background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
<div style="background:#C8332A;padding:32px;text-align:center;">
<p style="color:#fff;font-size:20px;font-weight:900;letter-spacing:4px;margin:0;">MODERATION SQUAD</p>
<p style="color:rgba(255,255,255,0.75);font-size:11px;letter-spacing:3px;margin:8px 0 0;">SECURE LOGIN CODE</p></div>
<div style="padding:40px;">
<p style="font-size:15px;color:#1a0a0a;font-weight:600;">Dear Moderator,</p>
<p style="font-size:14px;color:#555;line-height:1.8;">Your one-time secure login code is below. Valid for <strong>10 minutes</strong>.</p>
<div style="text-align:center;margin:32px 0;"><div style="display:inline-block;border:2px dashed #C8332A;border-radius:14px;padding:24px 56px;">
<p style="font-size:10px;color:#999;letter-spacing:3px;margin:0 0 10px;">YOUR CODE</p>
<p style="font-size:48px;font-weight:900;color:#C8332A;letter-spacing:12px;margin:0;">{otp}</p></div></div>
<p style="font-size:12px;color:#888;text-align:center;">⏱ Expires in 10 minutes &nbsp;·&nbsp; 🔒 Never share this code</p></div>
<div style="background:#1a0a0a;padding:18px;text-align:center;">
<p style="color:rgba(255,255,255,0.5);font-size:11px;margin:0;">© 2025 Moderation Squad · {S_EMAIL}</p></div></div></div>""")

def send_app_email(email, name, title, company, pay, days):
    brevo(email,f"Application Received — {title} at {company}",f"""
<div style="font-family:Arial,sans-serif;background:#f5f5f5;padding:40px 0;">
<div style="max-width:560px;margin:0 auto;background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
<div style="background:#C8332A;padding:32px;text-align:center;">
<p style="color:#fff;font-size:20px;font-weight:900;letter-spacing:4px;margin:0;">MODERATION SQUAD</p>
<p style="color:rgba(255,255,255,0.75);font-size:11px;letter-spacing:3px;margin:8px 0 0;">APPLICATION CONFIRMATION</p></div>
<div style="padding:40px;">
<p style="font-size:15px;color:#1a0a0a;font-weight:600;">Dear {name},</p>
<p style="font-size:14px;color:#555;line-height:1.8;">Your application has been received! We will respond within <strong>{days} business day{'s' if days>1 else ''}</strong>.</p>
<div style="background:#fff8f8;border-left:4px solid #C8332A;border-radius:8px;padding:18px 22px;margin:24px 0;">
<p style="font-size:11px;color:#999;letter-spacing:1px;text-transform:uppercase;margin:0 0 8px;">Application Details</p>
<p style="font-size:17px;font-weight:700;color:#1a0a0a;margin:0 0 5px;">💼 {title}</p>
<p style="font-size:13px;color:#555;margin:0 0 5px;">🏢 {company}</p>
<p style="font-size:14px;color:#C8332A;font-weight:700;margin:0;">💵 {pay}</p></div>
<p style="font-size:13px;color:#555;line-height:1.8;">While waiting, ensure your profile is fully verified — verified moderators get hired <strong>3x faster</strong>.</p></div>
<div style="background:#1a0a0a;padding:18px;text-align:center;">
<p style="color:rgba(255,255,255,0.5);font-size:11px;margin:0;">© 2025 Moderation Squad · {S_EMAIL} · {S_PHONE}</p></div></div></div>""")

def add_notif(email, msg):
    notif_store.setdefault(email,[]).insert(0,{"msg":msg,"time":datetime.now().strftime("%b %d, %I:%M %p")})
    notif_store[email]=notif_store[email][:20]

# ── LIGHT THEME CSS ──────────────────────────────────────────────
CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Space+Mono:wght@400;700&display=swap');
:root{
  --bg:#f4f6f9;--panel:#ffffff;--card:#ffffff;--sb:#ffffff;
  --red:#C8332A;--red2:#a01f18;--red-light:#fff0ef;--red-mid:#fde0de;
  --text:#1a0a0a;--muted:#6b7280;--bdr:#e5e7eb;--bdr2:#f3f4f6;
  --ok:#16a34a;--ok-bg:#f0fdf4;--ok-bdr:#bbf7d0;
  --warn:#d97706;--warn-bg:#fffbeb;--warn-bdr:#fde68a;
  --bad:#dc2626;--pur:#7c3aed;--pur-bg:#f5f3ff;
  --shadow:0 1px 3px rgba(0,0,0,0.08),0 1px 2px rgba(0,0,0,0.05);
  --shadow-md:0 4px 16px rgba(0,0,0,0.08);
  --shadow-lg:0 10px 32px rgba(0,0,0,0.1);
}
*{margin:0;padding:0;box-sizing:border-box;}
body{background:var(--bg);color:var(--text);font-family:'Plus Jakarta Sans',sans-serif;min-height:100vh;}
a{text-decoration:none;color:inherit;}
::-webkit-scrollbar{width:5px;}::-webkit-scrollbar-track{background:var(--bg);}
::-webkit-scrollbar-thumb{background:var(--bdr);border-radius:3px;}
::-webkit-scrollbar-thumb:hover{background:#C8332A;}

/* ── LAYOUT ── */
.layout{display:flex;min-height:100vh;}
.sb{width:240px;background:var(--sb);border-right:1px solid var(--bdr);display:flex;flex-direction:column;position:fixed;height:100vh;z-index:50;overflow-y:auto;box-shadow:var(--shadow);}
.sb-logo{padding:20px;border-bottom:1px solid var(--bdr);background:var(--red);}
.sb-logo h2{font-size:11px;font-weight:900;letter-spacing:3px;color:#fff;}
.sb-logo p{font-size:9px;color:rgba(255,255,255,0.7);letter-spacing:2px;margin-top:2px;}
.nb-sec{padding:14px 16px 5px;font-size:9px;letter-spacing:2px;color:var(--muted);text-transform:uppercase;font-weight:700;}
.ni{display:flex;align-items:center;gap:11px;padding:10px 16px;color:var(--muted);font-size:13px;font-weight:500;transition:all 0.18s;border-left:3px solid transparent;margin:1px 0;}
.ni:hover{color:var(--red);background:var(--red-light);border-left-color:var(--red);}
.ni.active{color:var(--red);background:var(--red-light);border-left-color:var(--red);font-weight:600;}
.ni svg{width:16px;height:16px;flex-shrink:0;}
.nbadge{margin-left:auto;background:var(--red);color:#fff;font-size:9px;font-weight:700;padding:2px 7px;border-radius:999px;}
.sb-bottom{margin-top:auto;border-top:1px solid var(--bdr);}
.sb-sup{background:var(--red-light);border:1px solid var(--red-mid);border-radius:10px;padding:12px;margin:10px;font-size:11px;color:var(--muted);line-height:1.8;}
.sb-sup a{color:var(--red);font-weight:600;}
.sb-sup strong{color:var(--text);}
.sb-logout{display:flex;align-items:center;gap:11px;padding:12px 16px;color:var(--bad);font-size:13px;font-weight:600;transition:all 0.18s;border-left:3px solid transparent;cursor:pointer;margin:4px 0 12px;}
.sb-logout:hover{background:#fef2f2;border-left-color:var(--bad);}
.sb-logout svg{width:16px;height:16px;}

.mc{margin-left:240px;flex:1;padding:24px 28px;min-height:100vh;}
.topbar{display:flex;align-items:center;justify-content:space-between;margin-bottom:24px;flex-wrap:wrap;gap:12px;}
.topbar h1{font-size:20px;font-weight:800;letter-spacing:-0.5px;color:var(--text);}
.topbar p{font-size:12px;color:var(--muted);margin-top:3px;}
.tr{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}

/* ── BADGES ── */
.bdg{display:inline-flex;align-items:center;gap:5px;padding:4px 11px;border-radius:999px;font-size:10px;font-weight:700;}
.b-red{background:var(--red-light);color:var(--red);border:1px solid var(--red-mid);}
.b-green{background:var(--ok-bg);color:var(--ok);border:1px solid var(--ok-bdr);}
.b-warn{background:var(--warn-bg);color:var(--warn);border:1px solid var(--warn-bdr);}
.b-pur{background:var(--pur-bg);color:var(--pur);border:1px solid #ddd6fe;}
.b-blue{background:#eff6ff;color:#2563eb;border:1px solid #bfdbfe;}
.b-grey{background:var(--bdr2);color:var(--muted);border:1px solid var(--bdr);}

/* ── CARDS ── */
.card{background:var(--card);border:1px solid var(--bdr);border-radius:14px;padding:20px;box-shadow:var(--shadow);}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:16px;}
.g3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;}
.g4{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;}

/* ── STAT CARDS ── */
.sc{background:var(--card);border:1px solid var(--bdr);border-radius:14px;padding:18px;position:relative;overflow:hidden;box-shadow:var(--shadow);}
.sc::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;}
.c1::before{background:var(--red);}
.c2::before{background:var(--ok);}
.c3::before{background:var(--pur);}
.c4::before{background:var(--warn);}
.sl{font-size:10px;color:var(--muted);letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;font-weight:600;}
.sv{font-size:26px;font-weight:800;letter-spacing:-1px;margin-bottom:4px;}
.ss{font-size:11px;color:var(--muted);}
.si2{position:absolute;top:14px;right:14px;font-size:22px;opacity:0.12;}

/* ── BUTTONS ── */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:7px;padding:9px 18px;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;border:none;transition:all 0.18s;font-family:'Plus Jakarta Sans',sans-serif;white-space:nowrap;letter-spacing:0.1px;}
.bp{background:var(--red);color:#fff;}
.bp:hover{background:var(--red2);transform:translateY(-1px);box-shadow:0 6px 18px rgba(200,51,42,0.3);}
.bo{background:#fff;color:var(--text);border:1px solid var(--bdr);}
.bo:hover{border-color:var(--red);color:var(--red);}
.bs{background:var(--ok-bg);color:var(--ok);border:1px solid var(--ok-bdr);}
.bl{background:var(--bdr2);color:var(--muted);cursor:not-allowed;border:1px solid var(--bdr);opacity:0.6;}
.bsm{padding:7px 14px;font-size:12px;}

/* ── JOB CARDS ── */
.jc{background:var(--card);border:1px solid var(--bdr);border-radius:13px;padding:18px;transition:all 0.2s;display:flex;flex-direction:column;box-shadow:var(--shadow);}
.jc:not(.lk):hover{border-color:var(--red);transform:translateY(-2px);box-shadow:var(--shadow-md);}
.jc.lk{opacity:0.45;pointer-events:none;}
.jt{font-size:14px;font-weight:700;margin-bottom:3px;line-height:1.3;color:var(--text);}
.jco{font-size:11px;color:var(--muted);margin-bottom:9px;}
.jd{font-size:12px;color:var(--muted);line-height:1.7;margin-bottom:10px;flex:1;}
.jm{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:12px;}
.tg{font-size:10px;padding:3px 8px;border-radius:5px;font-weight:600;}
.tp{background:var(--ok-bg);color:var(--ok);}
.tt{background:#eff6ff;color:#2563eb;}
.tl{background:var(--pur-bg);color:var(--pur);}
.tn{background:var(--red-light);color:var(--red);}

/* ── PROGRESS ── */
.pb{width:100%;height:7px;background:var(--bdr);border-radius:999px;overflow:hidden;}
.pf{height:100%;border-radius:999px;background:var(--red);transition:width 1.2s ease;}

/* ── VERIFY ITEMS ── */
.vi{display:flex;align-items:center;justify-content:space-between;padding:13px 14px;background:var(--bg);border-radius:10px;margin-bottom:7px;border:1px solid var(--bdr);}
.vl{display:flex;align-items:center;gap:11px;}
.vic{width:36px;height:36px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0;}
.vd-bg{background:var(--ok-bg);border:1px solid var(--ok-bdr);}
.vw-bg{background:var(--warn-bg);border:1px solid var(--warn-bdr);}
.vn{font-size:13px;font-weight:600;color:var(--text);}
.vs2{font-size:11px;color:var(--muted);margin-top:2px;}
.vst{font-size:11px;font-weight:700;padding:3px 11px;border-radius:999px;}
.vst-ok{background:var(--ok-bg);color:var(--ok);border:1px solid var(--ok-bdr);}
.vst-warn{background:var(--warn-bg);color:var(--warn);border:1px solid var(--warn-bdr);}

/* ── AVATAR ── */
.avw{position:relative;width:82px;height:82px;flex-shrink:0;}
.av{width:82px;height:82px;border-radius:50%;background:linear-gradient(135deg,var(--red),var(--red2));display:flex;align-items:center;justify-content:center;font-size:28px;font-weight:800;color:#fff;overflow:hidden;border:3px solid var(--red-mid);}
.av img{width:100%;height:100%;object-fit:cover;}
.ave{position:absolute;bottom:0;right:0;width:26px;height:26px;background:var(--red);border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;border:2px solid #fff;font-size:12px;box-shadow:0 2px 6px rgba(0,0,0,0.15);}

/* ── FORMS ── */
.form-group{margin-bottom:16px;}
.form-label{font-size:11px;color:var(--muted);font-weight:600;margin-bottom:6px;display:block;letter-spacing:0.5px;text-transform:uppercase;}
.form-input{width:100%;background:#fff;border:1px solid var(--bdr);border-radius:8px;padding:10px 13px;font-size:13px;color:var(--text);font-family:'Plus Jakarta Sans',sans-serif;transition:all 0.18s;outline:none;}
.form-input:focus{border-color:var(--red);box-shadow:0 0 0 3px rgba(200,51,42,0.08);}

/* ── TOAST ── */
.toast{position:fixed;bottom:22px;right:22px;padding:12px 20px;border-radius:10px;font-size:13px;font-weight:600;opacity:0;transform:translateY(10px);transition:all 0.3s;z-index:9999;pointer-events:none;max-width:320px;line-height:1.5;box-shadow:var(--shadow-lg);}
.toast.show{opacity:1;transform:translateY(0);}
.ts{background:#16a34a;color:#fff;}.te{background:#dc2626;color:#fff;}.ti{background:var(--red);color:#fff;}

/* ── SECTION HEADER ── */
.sh{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;}
.sh h2{font-size:14px;font-weight:700;color:var(--text);}

/* ── NOTIF BELL ── */
.nbell{position:relative;cursor:pointer;padding:8px;border-radius:9px;border:1px solid var(--bdr);background:#fff;transition:all 0.18s;box-shadow:var(--shadow);}
.nbell:hover{border-color:var(--red);}
.ndot{position:absolute;top:5px;right:5px;width:8px;height:8px;background:var(--red);border-radius:50%;border:2px solid #fff;}
.ndrop{position:absolute;top:44px;right:0;width:300px;background:#fff;border:1px solid var(--bdr);border-radius:14px;z-index:300;display:none;box-shadow:var(--shadow-lg);}
.ndrop.open{display:block;}

/* ── CHAT ── */
.chat-wrap{display:flex;flex-direction:column;height:450px;background:#fff;border-radius:12px;border:1px solid var(--bdr);overflow:hidden;box-shadow:var(--shadow);}
.chat-msgs{flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:10px;background:var(--bg);}
.cmsg{max-width:78%;padding:11px 14px;border-radius:12px;font-size:13px;line-height:1.6;}
.cmsg.sup{background:#fff;border:1px solid var(--bdr);align-self:flex-start;border-radius:4px 14px 14px 14px;box-shadow:var(--shadow);}
.cmsg.usr{background:var(--red);color:#fff;align-self:flex-end;border-radius:14px 4px 14px 14px;}
.cmsg.usr .mt{color:rgba(255,255,255,0.7);}
.mt{font-size:10px;color:var(--muted);margin-top:4px;}
.chat-inp{display:flex;gap:8px;padding:12px;border-top:1px solid var(--bdr);background:#fff;}
.cinput{flex:1;background:var(--bg);border:1px solid var(--bdr);border-radius:8px;padding:10px 13px;font-size:13px;color:var(--text);font-family:'Plus Jakarta Sans',sans-serif;outline:none;resize:none;}
.cinput:focus{border-color:var(--red);background:#fff;}
.chat-hdr{display:flex;align-items:center;gap:10px;padding:13px 16px;border-bottom:1px solid var(--bdr);background:#fff;}

/* ── MODAL ── */
.modal{position:fixed;inset:0;background:rgba(0,0,0,0.45);z-index:500;display:none;align-items:flex-start;justify-content:center;padding:20px;overflow-y:auto;}
.modal.open{display:flex;}
.mbox{background:#fff;border:1px solid var(--bdr);border-radius:16px;width:100%;max-width:700px;margin:auto;box-shadow:var(--shadow-lg);}
.mhdr{display:flex;align-items:center;justify-content:space-between;padding:18px 22px;border-bottom:1px solid var(--bdr);}
.mbody{padding:22px;font-size:13px;line-height:1.95;color:var(--text);white-space:pre-line;max-height:62vh;overflow-y:auto;}
.mfoot{padding:14px 22px;border-top:1px solid var(--bdr);display:flex;align-items:center;justify-content:space-between;}

/* ── PAGINATION ── */
.pgn{display:flex;gap:8px;justify-content:center;margin-top:22px;}
.pgn-btn{width:38px;height:38px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;cursor:pointer;border:1px solid var(--bdr);background:#fff;color:var(--muted);transition:all 0.18s;text-decoration:none;box-shadow:var(--shadow);}
.pgn-btn:hover,.pgn-btn.active{background:var(--red);color:#fff;border-color:var(--red);}

/* ── FAQ ── */
.faq-item{border:1px solid var(--bdr);border-radius:10px;overflow:hidden;margin-bottom:8px;box-shadow:var(--shadow);}
.faq-q{padding:14px 18px;cursor:pointer;font-size:13px;font-weight:600;display:flex;justify-content:space-between;align-items:center;background:#fff;color:var(--text);transition:background 0.18s;}
.faq-q:hover{background:var(--red-light);}
.faq-a{display:none;padding:14px 18px;font-size:12px;color:var(--muted);line-height:1.85;border-top:1px solid var(--bdr);background:var(--bg);}

/* ── ANIMATIONS ── */
@keyframes fadeUp{from{opacity:0;transform:translateY(14px);}to{opacity:1;transform:none;}}
.fi{animation:fadeUp 0.45s ease forwards;}
.fi1{animation-delay:0.04s;opacity:0;}.fi2{animation-delay:0.1s;opacity:0;}.fi3{animation-delay:0.17s;opacity:0;}.fi4{animation-delay:0.24s;opacity:0;}.fi5{animation-delay:0.31s;opacity:0;}

/* ── SOCIAL ── */
.soc-icon{width:34px;height:34px;border-radius:7px;display:flex;align-items:center;justify-content:center;transition:all 0.18s;background:var(--red-light);border:1px solid var(--red-mid);}
.soc-icon:hover{background:var(--red);border-color:var(--red);}
.soc-icon:hover svg{stroke:#fff;}
.soc-icon svg{stroke:var(--red);}

/* ── MOBILE ── */
@media(max-width:900px){.sb{width:200px;}.mc{margin-left:200px;padding:14px;}.g4{grid-template-columns:repeat(2,1fr);}.g3{grid-template-columns:1fr 1fr;}}
@media(max-width:640px){.sb{display:none;}.mc{margin-left:0;padding:11px;}.g4{grid-template-columns:repeat(2,1fr);}.g3{grid-template-columns:1fr;}.g2{grid-template-columns:1fr;}.topbar h1{font-size:16px;}}
</style>"""

def soc_sidebar():
    parts=[]
    for url,name,path in SOCIAL:
        parts.append(f'<a href="{url}" target="_blank" class="soc-icon" title="{name}"><svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="{path}"/></svg></a>')
    return '<div style="display:flex;gap:7px;flex-wrap:wrap;padding:10px 12px 14px;">'+("".join(parts))+'</div>'

def sidebar_html(active, user={}):
    name=user.get("name","Moderator")
    email=user.get("email","")
    nc=len(notif_store.get(email,[]))
    av=f'<img src="{user["avatar"]}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">' if user.get("avatar") else f'<span style="font-size:13px;font-weight:800;color:#fff;">{name[0].upper()}</span>'
    def ni(k,lb,ic,bg=""):
        cls="ni active" if active==k else "ni"
        badge=f'<span class="nbadge">{bg}</span>' if bg else ""
        return f'<a href="/{k}" class="{cls}">{ic}<span>{lb}</span>{badge}</a>'
    I=lambda p: f'<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" width="16" height="16"><path d="{p}"/></svg>'
    n_apps = len(user.get("applied_jobs", []))
    nav1=[
        ni("dashboard","Dashboard",I("M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z M9 22V12h6v10")),
        ni("jobs","Browse Jobs",I("M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"),"20"),
        ni("applications","My Applications",I("M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2 M9 5a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2 M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2 M12 12h.01 M12 16h.01"),str(n_apps) if n_apps else ""),
        ni("profile","My Profile",I("M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2 M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z")),
        ni("earnings","Earnings",I("M12 1v22 M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6")),
    ]
    nav2=[
        ni("notifications","Notifications",I("M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9 M13.73 21a2 2 0 0 1-3.46 0"),str(nc) if nc else ""),
        ni("schedule","My Schedule",I("M8 6h13 M8 12h13 M8 18h13 M3 6h.01 M3 12h.01 M3 18h.01")),
        ni("training","Training",I("M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"),"New"),
        ni("livechat","Live Support",I("M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z")),
        ni("support","Help & FAQ",I("M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3 M12 17h.01")),
    ]
    return f"""<div class="sb">
<div class="sb-logo"><h2>MODERATION SQUAD</h2><p>MODERATOR PORTAL</p></div>
<div style="padding:10px;border-bottom:1px solid var(--bdr);">
  <div style="display:flex;align-items:center;gap:9px;padding:10px;background:var(--red-light);border:1px solid var(--red-mid);border-radius:10px;">
    <div style="width:34px;height:34px;border-radius:50%;flex-shrink:0;background:linear-gradient(135deg,var(--red),var(--red2));display:flex;align-items:center;justify-content:center;overflow:hidden;">{av}</div>
    <div style="overflow:hidden;flex:1;"><div style="font-size:12px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--text);">{name}</div><div style="font-size:9px;color:var(--red);font-weight:700;">🔵 Newcomer</div></div>
    <div style="width:7px;height:7px;border-radius:50%;background:var(--ok);box-shadow:0 0 5px var(--ok);flex-shrink:0;" title="Online"></div>
  </div>
</div>
<div class="nb-sec">Main</div>{"".join(nav1)}
<div class="nb-sec">Tools</div>{"".join(nav2)}
<div class="sb-bottom">
  {soc_sidebar()}
  <div class="sb-sup">
    <strong>📞 Support</strong>
    <div style="margin-top:5px;">📧 <a href="mailto:{S_EMAIL}">{S_EMAIL}</a></div>
    <div>📱 <a href="tel:{S_PHONE}">{S_PHONE}</a></div>
    <div style="font-size:10px;margin-top:3px;color:var(--muted);">Mon–Fri 9AM–6PM EST</div>
  </div>
  <a href="/logout" class="sb-logout">
    <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
    <span>Sign Out</span>
  </a>
</div>
</div>"""

def setup_routes():
    @app.route("/")
    def index(): return landing()

    @app.route("/login", methods=["GET","POST"])
    def login():
        if request.method=="POST":
            data=request.json or {}
            email=data.get("email","").strip().lower()
            pin=data.get("pin","").strip()
            device_id=data.get("device_id","").strip()
            if email not in [e.lower() for e in WHITELIST]:
                return jsonify({"success":False,"message":"⛔ Access Denied. Your email is not on our approved list."})
            rec=pin_store.get(email)
            if not rec: return jsonify({"success":False,"message":"⛔ Account not found."})
            if rec["pin"]!=pin: return jsonify({"success":False,"message":"❌ Incorrect PIN. Please try again."})
            # Device check — each device can only ever belong to ONE account
            devices = rec.get("devices", [])
            if device_id not in devices:
                # Check: is this device already registered to a DIFFERENT account?
                for other_email, other_rec in pin_store.items():
                    if other_email != email and device_id in other_rec.get("devices", []):
                        return jsonify({"success":False,"message":f"⛔ Access denied. This device is already linked to a different account. One device = one account only. Contact {S_EMAIL} to reset."})
                # New device for this account — register it
                pin_store[email].setdefault("devices",[]).append(device_id)
                if not pin_store[email].get("first_device"):
                    pin_store[email]["first_device"]=device_id
                save_pins()
            session["user"]=email
            if email not in user_store:
                name=email.split("@")[0].replace("."," ").replace("_"," ").title()
                user_store[email]={"email":email,"name":name,"level":"Newcomer","jobs_done":0,
                    "earned":0.0,"member_since":datetime.now().strftime("%b %Y"),
                    "avatar":None,"applied_jobs":[],
                    "verifications":{"email":True,"residence":True,"id":True,"tax":True,"payment":False,"background":True}}
                add_notif(email,f"🎉 Welcome to Moderation Squad, {name}! Your account is verified and ready.")
            return jsonify({"success":True})
        return login_pg()

    @app.route("/change_pin", methods=["POST"])
    def change_pin():
        if "user" not in session: return jsonify({"success":False,"message":"Not logged in."})
        data=request.json or {}
        email=session["user"]
        device_id=data.get("device_id","").strip()
        old_pin=data.get("old_pin","").strip()
        new_pin=data.get("new_pin","").strip()
        rec=pin_store.get(email)
        if not rec: return jsonify({"success":False,"message":"Account not found."})
        # Only the first registered device (PIN-change master) can change PIN
        first=rec.get("first_device")
        if first and first!=device_id:
            return jsonify({"success":False,"message":"⛔ PIN can only be changed from your first registered device. Any device can log in, but only your original device can change the PIN. Contact support if you need a reset."})
        if rec["pin"]!=old_pin:
            return jsonify({"success":False,"message":"❌ Current PIN is incorrect."})
        if len(new_pin)<4 or not new_pin.isdigit():
            return jsonify({"success":False,"message":"❌ New PIN must be at least 4 digits."})
        if new_pin==old_pin:
            return jsonify({"success":False,"message":"❌ New PIN must be different from current PIN."})
        pin_store[email]["pin"]=new_pin
        save_pins()
        add_notif(email,"🔐 Your PIN was successfully changed.")
        return jsonify({"success":True})

    @app.route("/dashboard")
    def dashboard():
        if "user" not in session: return redirect("/login")
        return dash_pg(user_store.get(session["user"],{}))

    @app.route("/jobs")
    def jobs():
        if "user" not in session: return redirect("/login")
        pg=int(request.args.get("pg",1))
        return jobs_pg(user_store.get(session["user"],{}),pg)

    @app.route("/profile")
    def profile():
        if "user" not in session: return redirect("/login")
        return profile_pg(user_store.get(session["user"],{}))

    @app.route("/earnings")
    def earnings():
        if "user" not in session: return redirect("/login")
        return earnings_pg(user_store.get(session["user"],{}))

    @app.route("/notifications")
    def notifications():
        if "user" not in session: return redirect("/login")
        return notif_pg(user_store.get(session["user"],{}))

    @app.route("/schedule")
    def schedule():
        if "user" not in session: return redirect("/login")
        return schedule_pg(user_store.get(session["user"],{}))

    @app.route("/training")
    def training():
        if "user" not in session: return redirect("/login")
        cid=request.args.get("c")
        lid=int(request.args.get("l","0"))
        if cid is not None:
            return course_pg(user_store.get(session["user"],{}),int(cid),lid)
        return training_pg(user_store.get(session["user"],{}))

    @app.route("/livechat")
    def livechat():
        if "user" not in session: return redirect("/login")
        return livechat_pg(user_store.get(session["user"],{}))

    @app.route("/support")
    def support():
        if "user" not in session: return redirect("/login")
        return support_pg(user_store.get(session["user"],{}))

    @app.route("/applications")
    def applications():
        if "user" not in session: return redirect("/login")
        return applications_pg(user_store.get(session["user"],{}))

    @app.route("/save_job", methods=["POST"])
    def save_job():
        if "user" not in session: return jsonify({"success":False})
        data=request.json or {}; email=session["user"]
        job={"title":data.get("title",""),"company":data.get("company",""),"pay":data.get("pay",""),"icon":data.get("icon","💼")}
        saved=saved_store.setdefault(email,[])
        # Toggle — remove if already saved
        for i,s in enumerate(saved):
            if s["title"]==job["title"]:
                saved.pop(i)
                return jsonify({"success":True,"action":"removed"})
        saved.insert(0,job)
        return jsonify({"success":True,"action":"saved"})

    @app.route("/apply_job", methods=["POST"])
    def apply_job():
        if "user" not in session: return jsonify({"success":False})
        data=request.json or {}
        email=session["user"]; user=user_store.get(email,{})
        t,c,p=data.get("title",""),data.get("company",""),data.get("pay","")
        icon=data.get("icon","💼"); hrs=data.get("hrs","")
        # Prevent duplicate applications
        already=[j for j in user.get("applied_jobs",[]) if j["title"]==t]
        if already: return jsonify({"success":False,"message":"Already applied"})
        days=random.randint(1,3)
        user.setdefault("applied_jobs",[]).append({
            "title":t,"company":c,"pay":p,"hrs":hrs,"icon":icon,
            "status":"Under Review","date":datetime.now().strftime("%b %d, %Y"),"days":days
        })
        add_notif(email,f"✅ Applied for {t} at {c}. Response expected within {days} business day{'s' if days>1 else ''}.")
        threading.Thread(target=send_app_email,args=(email,user.get("name","Moderator"),t,c,p,days)).start()
        return jsonify({"success":True,"days":days})

    @app.route("/upload_avatar", methods=["POST"])
    def upload_avatar():
        if "user" not in session: return jsonify({"success":False})
        img=(request.json or {}).get("image","")
        email=session["user"]
        if email in user_store: user_store[email]["avatar"]=img; add_notif(email,"📸 Profile picture updated successfully!")
        return jsonify({"success":True})

    @app.route("/chat_msg", methods=["POST"])
    def chat_msg():
        if "user" not in session: return jsonify({"success":False})
        data=request.json or {}; email=session["user"]; msg=data.get("msg","").strip()
        if not msg: return jsonify({"success":False})
        chat_store.setdefault(email,[])
        chat_store[email].append({"role":"user","msg":msg,"time":datetime.now().strftime("%I:%M %p")})
        ml=msg.lower()
        kb={"pay":"Our Newcomer pay starts at $5–$6/hr. Level up through Junior ($10–$12), Senior ($13–$18), and Elite ($18–$22/hr). Payouts every Friday!",
            "payment":"We support Direct Deposit (ACH), PayPal, Payoneer, Tipalti, and Paper Check. Set up your method in the Earnings section.",
            "job":"You have 3 open Newcomer positions! Browse Jobs and click Apply Now. Complete 6 jobs to unlock Junior level with better pay.",
            "verify":"Your profile is almost fully verified! The only remaining step is setting up your Payment Method in Earnings.",
            "level":"You are Newcomer. Complete 6 jobs → Junior, 21 jobs → Senior, 50 jobs → Elite. Each level unlocks better-paying positions!",
            "train":"Training Center has 3 free beginner courses: Chat Moderation Fundamentals, Content Policy, and Effective Communication. Click Training in the sidebar!",
            "schedule":"Set your weekly availability in My Schedule. Pick days and time slots (EST) and clients will schedule you accordingly.",
            "payout":"Payouts process every Friday for the prior week. Minimum $10. Make sure your payment method is set up in Earnings first.",
            "hello":"Hi there! 👋 I'm your Moderation Squad support agent. How can I help you today?",
            "hi":"Hello! 👋 I'm here to help! Ask me about pay, jobs, verification, training, scheduling, or anything else.",
            "help":"Happy to help! I can answer questions about: pay rates, job applications, profile verification, training courses, scheduling, and account issues. What do you need?",
            "logout":"You can sign out by clicking the Sign Out button at the bottom of the left sidebar, or by visiting /logout directly.",
            "background":"Your background check has already been completed and verified! Only your payment method setup remains.",
            "w9":"Your W-9 tax form has already been submitted and verified. Only your payment method setup remains!",
            "id":"Your Government ID has already been verified! Only your payment method setup remains."}
        reply="Thanks for reaching out! I can help with pay rates, job applications, verification, training, scheduling, and more. What specifically do you need?"
        for k,v in kb.items():
            if k in ml: reply=v; break
        chat_store[email].append({"role":"support","msg":reply,"time":datetime.now().strftime("%I:%M %p")})
        return jsonify({"success":True,"reply":reply,"time":datetime.now().strftime("%I:%M %p")})

    @app.route("/check_device", methods=["POST"])
    def check_device():
        data=request.json or {}
        email=data.get("email","").strip().lower()
        device_id=data.get("device_id","").strip()
        rec=pin_store.get(email,{})
        first=rec.get("first_device")
        # PIN change only allowed from first registered device
        same=(first is None or first==device_id)
        return jsonify({"same_device":same})

    @app.route("/change_pin_preauth", methods=["POST"])
    def change_pin_preauth():
        # Change PIN before login (from login screen)
        data=request.json or {}
        email=data.get("email","").strip().lower()
        device_id=data.get("device_id","").strip()
        old_pin=data.get("old_pin","").strip()
        new_pin=data.get("new_pin","").strip()
        rec=pin_store.get(email)
        if not rec: return jsonify({"success":False,"message":"⛔ Email not found."})
        first=rec.get("first_device")
        if first and first!=device_id:
            return jsonify({"success":False,"message":"⛔ PIN can only be changed from your first registered device. Any of your 2 devices can log in, but only your first device controls the PIN. Contact support to reset."})
        if rec["pin"]!=old_pin:
            return jsonify({"success":False,"message":"❌ Current PIN is incorrect."})
        if len(new_pin)<4 or not new_pin.isdigit():
            return jsonify({"success":False,"message":"❌ New PIN must be at least 4 digits."})
        if new_pin==old_pin:
            return jsonify({"success":False,"message":"❌ New PIN must be different from current PIN."})
        pin_store[email]["pin"]=new_pin
        save_pins()
        return jsonify({"success":True})

    @app.route("/check_email", methods=["POST"])
    def check_email():
        data=request.json or {}
        email=data.get("email","").strip().lower()
        device_id=data.get("device_id","").strip()
        # Check if this device is already bound to a DIFFERENT account
        for bound_email, rec in pin_store.items():
            if bound_email != email and device_id in rec.get("devices", []):
                return jsonify({"allowed":False,"message":f"⛔ Access denied. This device is already linked to a different account. One device can only belong to one account. Contact {S_EMAIL} to reset."})
        return jsonify({"allowed":True})

    @app.route("/admin_reset_devices", methods=["POST"])
    def admin_reset_devices():
        # Secret admin route to wipe all device bindings (keeps PINs)
        data=request.json or {}
        if data.get("secret")!="modsquad_admin_2025":
            return jsonify({"success":False})
        target=data.get("email","all")
        if target=="all":
            for k in pin_store:
                pin_store[k]["devices"]=[]
                pin_store[k]["first_device"]=None
        elif target in pin_store:
            pin_store[target]["devices"]=[]
            pin_store[target]["first_device"]=None
        save_pins()
        return jsonify({"success":True,"message":f"Devices reset for: {target}"})

    @app.route("/ping")
    def ping(): return "ok"

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect("/")


# ── LANDING PAGE ──────────────────────────────────────────────────
def landing():
    imgs=["https://images.unsplash.com/photo-1600880292203-757bb62b4baf?w=1400&q=80",
          "https://images.unsplash.com/photo-1521737711867-e3b97375f902?w=1400&q=80",
          "https://images.unsplash.com/photo-1553877522-43269d4ea984?w=1400&q=80",
          "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=1400&q=80"]
    slides="".join(f'<div class="hsl" style="background-image:url(\'{u}\')"></div>' for u in imgs)
    soc_f="".join(f'<a href="{u}" target="_blank" style="width:36px;height:36px;border-radius:8px;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);transition:all 0.2s;" onmouseover="this.style.background=\'rgba(255,255,255,0.25)\'" onmouseout="this.style.background=\'rgba(255,255,255,0.1)\'" title="{n}"><svg width="16" height="16" fill="none" stroke="white" stroke-width="2" viewBox="0 0 24 24"><path d="{p}"/></svg></a>' for u,n,p in SOCIAL)
    tests=[("Sarah K.","Texas, USA","Went from Newcomer to Elite in 8 months. Now earning $22/hr working from home full time. Life-changing!","⭐⭐⭐⭐⭐"),
           ("Marcus T.","California, USA","Training is excellent and the team is incredibly supportive. Got my first job within 2 weeks of joining.","⭐⭐⭐⭐⭐"),
           ("Aisha R.","New York, USA","Finally a platform that pays fairly and treats moderators like true professionals. Payouts are always on time.","⭐⭐⭐⭐⭐")]
    tests_h="".join(f'<div style="background:#fff;border:1px solid #e5e7eb;border-radius:16px;padding:26px;box-shadow:0 2px 12px rgba(0,0,0,0.05);"><p style="font-size:13px;color:#6b7280;line-height:1.85;margin-bottom:18px;font-style:italic;">"{q}"</p><div style="display:flex;align-items:center;gap:10px;"><div style="width:38px;height:38px;border-radius:50%;background:#C8332A;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:800;color:#fff;flex-shrink:0;">{n[0]}</div><div><div style="font-size:13px;font-weight:700;color:#1a0a0a;">{n}</div><div style="font-size:11px;color:#6b7280;">{lo}</div></div><div style="margin-left:auto;font-size:13px;">{st}</div></div></div>' for n,lo,q,st in tests)
    photos=[("https://images.unsplash.com/photo-1600880292203-757bb62b4baf?w=600&q=80","🌟 Elite Team"),
            ("https://images.unsplash.com/photo-1553877522-43269d4ea984?w=600&q=80","🏠 100% Remote"),
            ("https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=600&q=80","🤝 Community")]
    photo_h="".join(f'<div style="border-radius:16px;overflow:hidden;position:relative;height:220px;"><img src="{u}" style="width:100%;height:100%;object-fit:cover;display:block;"><div style="position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,0.65),transparent);display:flex;align-items:flex-end;padding:16px;"><span style="color:#fff;font-size:13px;font-weight:700;">{lb}</span></div></div>' for u,lb in photos)
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Moderation Squad — Professional Chat Moderation</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
:root{{--red:#C8332A;--red2:#a01f18;}}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:'Plus Jakarta Sans',sans-serif;background:#fff;color:#1a0a0a;overflow-x:hidden;}}
a{{text-decoration:none;color:inherit;}}
.btn{{display:inline-flex;align-items:center;gap:7px;padding:10px 22px;border-radius:8px;font-size:13px;font-weight:700;cursor:pointer;border:none;transition:all 0.2s;font-family:'Plus Jakarta Sans',sans-serif;}}
.br{{background:var(--red);color:#fff;}}.br:hover{{background:var(--red2);transform:translateY(-1px);box-shadow:0 6px 20px rgba(200,51,42,0.35);}}
.bo{{background:transparent;color:var(--red);border:2px solid var(--red);}}.bo:hover{{background:var(--red);color:#fff;}}
.bw{{background:#fff;color:var(--red);font-weight:700;}}.bw:hover{{background:#fde0de;}}
.nav{{display:flex;align-items:center;justify-content:space-between;padding:0 40px;height:66px;position:sticky;top:0;z-index:100;background:rgba(255,255,255,0.97);backdrop-filter:blur(14px);border-bottom:1px solid #e5e7eb;box-shadow:0 1px 12px rgba(0,0,0,0.06);}}
.nlogo{{display:flex;align-items:center;gap:10px;}}
.nring{{width:36px;height:36px;border-radius:50%;border:3px solid var(--red);display:flex;align-items:center;justify-content:center;}}
.nltxt{{font-size:12px;font-weight:900;letter-spacing:2.5px;color:#1a0a0a;}}
.nlinks{{display:flex;gap:30px;}}.nlinks a{{font-size:13px;color:#6b7280;font-weight:500;transition:color 0.2s;}}.nlinks a:hover{{color:var(--red);}}
.hero{{position:relative;height:100vh;overflow:hidden;display:flex;align-items:center;justify-content:center;}}
.hero-s{{position:absolute;inset:0;}}.hsl{{position:absolute;inset:0;background-size:cover;background-position:center;opacity:0;transition:opacity 1.4s ease;}}.hsl.act{{opacity:1;}}
.hov{{position:absolute;inset:0;background:linear-gradient(135deg,rgba(26,5,5,0.88) 0%,rgba(200,51,42,0.22) 100%);}}
.hcnt{{position:relative;z-index:2;text-align:center;padding:0 20px;max-width:840px;}}
.hbdg{{font-size:10px;letter-spacing:4px;color:rgba(255,255,255,0.75);font-weight:700;text-transform:uppercase;margin-bottom:22px;padding:5px 18px;background:rgba(200,51,42,0.35);border:1px solid rgba(200,51,42,0.55);border-radius:999px;display:inline-block;}}
.hcnt h1{{font-size:clamp(32px,6.5vw,72px);font-weight:800;color:#fff;line-height:1.05;margin-bottom:20px;letter-spacing:-2px;}}
.hcnt h1 em{{font-style:normal;color:#ff8a7a;}}
.hcnt p{{font-size:clamp(14px,2vw,18px);color:rgba(255,255,255,0.72);max-width:520px;margin:0 auto 36px;line-height:1.85;}}
.hbtns{{display:flex;gap:14px;flex-wrap:wrap;justify-content:center;}}
.hdots{{position:absolute;bottom:28px;left:50%;transform:translateX(-50%);display:flex;gap:8px;z-index:3;}}
.hdot{{width:8px;height:8px;border-radius:50%;background:rgba(255,255,255,0.35);cursor:pointer;transition:all 0.3s;border:none;}}
.hdot.act{{background:#fff;width:26px;border-radius:4px;}}
.sbar{{background:var(--red);padding:22px 40px;display:flex;justify-content:center;gap:64px;flex-wrap:wrap;}}
.si{{text-align:center;}}.si h3{{font-size:28px;font-weight:800;color:#fff;letter-spacing:-1px;}}.si p{{font-size:11px;color:rgba(255,255,255,0.72);margin-top:2px;letter-spacing:1px;}}
.sec{{padding:80px 40px;max-width:1100px;margin:0 auto;}}
.st{{font-size:clamp(24px,4vw,38px);font-weight:800;text-align:center;margin-bottom:10px;letter-spacing:-1px;}}.st span{{color:var(--red);}}
.ss{{text-align:center;color:#6b7280;font-size:14px;margin-bottom:52px;}}
.feat-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:20px;}}
.fc{{background:#fff;border:1px solid #e5e7eb;border-radius:16px;padding:26px;transition:all 0.3s;box-shadow:0 1px 4px rgba(0,0,0,0.05);}}
.fc:hover{{border-color:var(--red);transform:translateY(-4px);box-shadow:0 16px 40px rgba(200,51,42,0.1);}}
.fic{{width:46px;height:46px;border-radius:12px;margin-bottom:16px;background:#fff0ef;display:flex;align-items:center;justify-content:center;font-size:22px;}}
.fc h3{{font-size:15px;font-weight:700;margin-bottom:7px;}}.fc p{{font-size:12px;color:#6b7280;line-height:1.75;}}
.bg-light{{background:#f8f9fa;padding:80px 40px;}}
.ptable{{width:100%;border-collapse:collapse;}}.ptable th{{text-align:left;padding:12px 16px;font-size:10px;letter-spacing:2px;color:#6b7280;text-transform:uppercase;border-bottom:2px solid #e5e7eb;}}.ptable td{{padding:15px 16px;font-size:13px;border-bottom:1px solid #f3f4f6;}}.ptable tr:hover td{{background:#fff8f7;}}.pay{{color:var(--red);font-weight:700;font-family:monospace;}}
.hgrid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:0;}}
.hs{{text-align:center;padding:32px 18px;position:relative;}}
.hs:not(:last-child)::after{{content:'→';position:absolute;right:-10px;top:50%;transform:translateY(-50%);font-size:22px;color:#e5e7eb;}}
.hnum{{width:52px;height:52px;border-radius:50%;background:var(--red);display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:800;color:#fff;margin:0 auto 14px;}}
.hs h3{{font-size:14px;font-weight:700;margin-bottom:7px;}}.hs p{{font-size:12px;color:#6b7280;line-height:1.75;}}
.dsec{{background:linear-gradient(135deg,#1a0505,#2d0f0f);padding:80px 40px;text-align:center;}}
.dsec h2{{font-size:32px;font-weight:800;color:#fff;margin-bottom:12px;letter-spacing:-1px;}}.dsec p{{color:rgba(255,255,255,0.6);font-size:15px;margin-bottom:30px;}}
footer{{background:#1a0505;padding:44px 40px;}}
.fg{{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:32px;max-width:1100px;margin:0 auto 32px;}}
.flogo{{font-size:12px;font-weight:900;letter-spacing:3px;color:var(--red);margin-bottom:10px;}}
.fdesc{{font-size:12px;color:rgba(255,255,255,0.38);line-height:1.75;}}
.fcol h4{{font-size:10px;letter-spacing:2px;color:rgba(255,255,255,0.4);text-transform:uppercase;margin-bottom:13px;}}
.fcol a{{display:block;font-size:12px;color:rgba(255,255,255,0.38);margin-bottom:8px;transition:color 0.2s;}}.fcol a:hover{{color:var(--red);}}
.fbot{{max-width:1100px;margin:0 auto;padding-top:24px;border-top:1px solid rgba(255,255,255,0.07);display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;}}
.fbot p{{font-size:11px;color:rgba(255,255,255,0.25);}}
.promo{{background:linear-gradient(135deg,var(--red),#e03030);padding:42px;border-radius:20px;text-align:center;margin:0 40px 60px;}}
.promo h3{{font-size:26px;font-weight:800;color:#fff;margin-bottom:10px;}}.promo p{{color:rgba(255,255,255,0.8);font-size:14px;margin-bottom:26px;}}
@media(max-width:768px){{.nlinks{{display:none;}}.sec{{padding:52px 16px;}}.sbar{{gap:28px;padding:18px 16px;}}.fg{{grid-template-columns:1fr 1fr;}}.promo{{margin:0 16px 40px;padding:28px 18px;}}.hs::after{{display:none;}}}}
</style>
</head><body>
<nav class="nav">
  <div class="nlogo">
    <div class="nring"><svg width="17" height="17" fill="none" stroke="#C8332A" stroke-width="2.5" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/></svg></div>
    <span class="nltxt">MODERATION SQUAD</span>
  </div>
  <div class="nlinks"><a href="#features">Features</a><a href="#pay">Pay Rates</a><a href="#how">How It Works</a><a href="#reviews">Reviews</a><a href="#contact">Contact</a></div>
  <a href="/login" class="btn br">Access Portal →</a>
</nav>
<section class="hero">
  <div class="hero-s">{slides}</div><div class="hov"></div>
  <div class="hcnt">
    <div class="hbdg">🇺🇸 USA-Based · Remote · Invite Only</div>
    <h1>Professional Chat<br>Moderation, <em>Elevated.</em></h1>
    <p>Join an elite network of professional moderators. Real pay, real flexibility, real career growth — from anywhere in the USA.</p>
    <div class="hbtns">
      <a href="/login" class="btn br" style="font-size:15px;padding:13px 30px;">Access Your Account →</a>
      <a href="#how" class="btn" style="background:rgba(255,255,255,0.12);color:#fff;border:1px solid rgba(255,255,255,0.3);font-size:15px;padding:13px 30px;">Learn More</a>
    </div>
  </div>
  <div class="hdots" id="hdts">
    <button class="hdot act" onclick="goS(0)"></button><button class="hdot" onclick="goS(1)"></button>
    <button class="hdot" onclick="goS(2)"></button><button class="hdot" onclick="goS(3)"></button>
  </div>
</section>
<div class="sbar">
  <div class="si"><h3>2,400+</h3><p>Active Moderators</p></div>
  <div class="si"><h3>98%</h3><p>Client Satisfaction</p></div>
  <div class="si"><h3>$18/hr</h3><p>Average Pay Rate</p></div>
  <div class="si"><h3>500+</h3><p>Partner Brands</p></div>
  <div class="si"><h3>7 Yrs</h3><p>In Business</p></div>
</div>
<div class="sec" id="features">
  <h2 class="st">Why <span>Moderation Squad?</span></h2><p class="ss">Everything you need to build a professional moderation career</p>
  <div class="feat-grid">
    <div class="fc"><div class="fic">💰</div><h3>Honest, Growing Pay</h3><p>Start at $5/hr as a Newcomer and grow up to $22/hr as Elite. No hidden deductions. Weekly Friday payouts.</p></div>
    <div class="fc"><div class="fic">🕐</div><h3>True Flexibility</h3><p>Work 8–40 hours per week entirely on your own schedule. You set your availability — we fit around you.</p></div>
    <div class="fc"><div class="fic">📈</div><h3>Real Career Growth</h3><p>4 clear levels: Newcomer → Junior → Senior → Elite. Complete jobs to level up and access better pay.</p></div>
    <div class="fc"><div class="fic">🛡️</div><h3>USA Verified</h3><p>All moderators verified with confirmed US location, government ID, and full tax compliance.</p></div>
    <div class="fc"><div class="fic">📚</div><h3>Free Training</h3><p>Full library of moderation courses and certifications. Learn at your own pace, completely free.</p></div>
    <div class="fc"><div class="fic">💬</div><h3>Live Support</h3><p>Real-time chat, email and phone support Monday–Friday. A real human always answers.</p></div>
  </div>
</div>
<div class="sec" style="padding-top:0;"><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;">{photo_h}</div></div>
<div class="bg-light" id="pay">
  <div style="max-width:1000px;margin:0 auto;">
    <h2 class="st">Pay <span>Rates</span></h2><p class="ss">Transparent compensation — no surprises, ever</p>
    <div style="background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.07);">
      <table class="ptable">
        <thead><tr style="background:#f8f9fa;"><th>Role</th><th>Level</th><th>Pay Range</th><th>Hours/Week</th></tr></thead>
        <tbody>
          <tr><td>Basic Chat Monitor / Email Support</td><td style="color:#C8332A;font-weight:600;">🔵 Newcomer</td><td class="pay">$5–$6/hr</td><td>8–20 hrs</td></tr>
          <tr><td>Standard Moderator / Content Reviewer</td><td style="color:#16a34a;font-weight:600;">🟢 Junior</td><td class="pay">$10–$12/hr</td><td>15–30 hrs</td></tr>
          <tr><td>Social Media / Trust & Safety Analyst</td><td style="color:#d97706;font-weight:600;">🟡 Senior</td><td class="pay">$13–$17/hr</td><td>20–40 hrs</td></tr>
          <tr><td>Lead Moderator / T&S Specialist</td><td style="color:#C8332A;font-weight:600;">🔴 Elite</td><td class="pay">$18–$22/hr</td><td>Full-time</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</div>
<div class="sec" id="how">
  <h2 class="st">How It <span>Works</span></h2><p class="ss">From signup to first paycheck in 4 simple steps</p>
  <div class="hgrid">
    <div class="hs"><div class="hnum">1</div><h3>Get Approved</h3><p>Receive your invite. Login securely with your email OTP — no passwords needed.</p></div>
    <div class="hs"><div class="hnum">2</div><h3>Verify Profile</h3><p>Complete USA verification, upload your ID, and submit your W-9 tax form.</p></div>
    <div class="hs"><div class="hnum">3</div><h3>Apply to Jobs</h3><p>Browse 20+ positions matched to your level. Apply with one click and get instant email confirmation.</p></div>
    <div class="hs"><div class="hnum">4</div><h3>Get Paid</h3><p>Complete work and receive weekly payouts every Friday via your preferred method.</p></div>
  </div>
</div>
<div class="promo">
  <h3>🚀 Ready to Start Your Moderation Career?</h3>
  <p>Join 2,400+ professional moderators earning real income from home. Invite-only — check if you're approved.</p>
  <a href="/login" class="btn bw" style="font-size:15px;padding:13px 30px;">Access Your Account →</a>
</div>
<div class="bg-light" id="reviews">
  <div style="max-width:1000px;margin:0 auto;">
    <h2 class="st">What Our <span>Mods Say</span></h2><p class="ss">Real stories from real moderators</p>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px;">{tests_h}</div>
  </div>
</div>
<div class="sec" id="contact">
  <h2 class="st">Get In <span>Touch</span></h2><p class="ss">Have questions? We're here to help</p>
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:18px;">
    <div style="background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:26px;text-align:center;box-shadow:0 1px 6px rgba(0,0,0,0.05);"><div style="font-size:34px;margin-bottom:12px;">📧</div><h3 style="font-size:15px;font-weight:700;margin-bottom:6px;">Email</h3><p style="font-size:12px;color:#6b7280;margin-bottom:14px;">24–48hr response</p><a href="mailto:{S_EMAIL}" class="btn br" style="font-size:11px;padding:8px 14px;">{S_EMAIL}</a></div>
    <div style="background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:26px;text-align:center;box-shadow:0 1px 6px rgba(0,0,0,0.05);"><div style="font-size:34px;margin-bottom:12px;">📞</div><h3 style="font-size:15px;font-weight:700;margin-bottom:6px;">Phone</h3><p style="font-size:12px;color:#6b7280;margin-bottom:14px;">Mon–Fri 9AM–6PM EST</p><a href="tel:{S_PHONE}" class="btn bo" style="font-size:11px;padding:8px 14px;">{S_PHONE}</a></div>
    <div style="background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:26px;text-align:center;box-shadow:0 1px 6px rgba(0,0,0,0.05);"><div style="font-size:34px;margin-bottom:12px;">💼</div><h3 style="font-size:15px;font-weight:700;margin-bottom:6px;">Recruiting</h3><p style="font-size:12px;color:#6b7280;margin-bottom:14px;">Join the team</p><a href="https://join.modsquad.com" target="_blank" class="btn br" style="font-size:11px;padding:8px 14px;">Contact Recruiting</a></div>
  </div>
</div>
<div class="dsec">
  <h2>Join the Squad Today</h2><p>Access is invite-only. If you have an approved email, your account is waiting.</p>
  <a href="/login" class="btn br" style="font-size:15px;padding:14px 32px;">Access Your Account →</a>
</div>
<footer>
  <div class="fg">
    <div><div class="flogo">MODERATION SQUAD</div><p class="fdesc">Professional chat moderation services. USA-based invite-only platform for elite professional moderators.</p>
      <div style="display:flex;gap:9px;margin-top:16px;">{soc_f}</div></div>
    <div class="fcol"><h4>Platform</h4><a href="/login">Access Portal</a><a href="/login">Browse Jobs</a><a href="/login">Training Center</a><a href="/login">Earnings</a></div>
    <div class="fcol"><h4>Company</h4><a href="https://www.modsquad.com" target="_blank">ModSquad.com</a><a href="https://join.modsquad.com" target="_blank">About The Mods</a><a href="https://join.modsquad.com" target="_blank">Careers</a><a href="https://join.modsquad.com" target="_blank">Mod of the Month</a></div>
    <div class="fcol"><h4>Support</h4><a href="mailto:{S_EMAIL}">Email Support</a><a href="tel:{S_PHONE}">Call Us</a><a href="/login">Live Chat</a><a href="/login">FAQ</a></div>
  </div>
  <div class="fbot"><p>© 2025 Moderation Squad, Inc. All rights reserved.</p><p>Privacy Policy · Do Not Sell My Data</p></div>
</footer>
<script>
let cs=0;const sls=document.querySelectorAll('.hsl'),dts=document.querySelectorAll('.hdot');
function goS(n){{sls[cs].classList.remove('act');dts[cs].classList.remove('act');cs=n;sls[cs].classList.add('act');dts[cs].classList.add('act');}}
sls[0].classList.add('act');setInterval(()=>goS((cs+1)%sls.length),5000);
</script></body></html>"""

def login_pg():
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sign In — Moderation Squad</title>{CSS}
<style>
body{{background:#f4f6f9;display:flex;align-items:center;justify-content:center;min-height:100vh;}}
.aw{{width:100%;max-width:400px;padding:14px;}}
.ac{{background:#fff;border:1px solid #e5e7eb;border-radius:18px;padding:36px;box-shadow:0 4px 24px rgba(0,0,0,0.08);}}
.alg{{background:var(--red);margin:-36px -36px 28px;border-radius:14px 14px 0 0;padding:28px;text-align:center;}}
.err{{background:#fef2f2;border:1px solid #fecaca;color:var(--bad);padding:10px 13px;border-radius:8px;font-size:12px;margin-bottom:12px;display:none;line-height:1.5;}}
.pin-wrap{{display:flex;gap:8px;justify-content:center;margin:20px 0;}}
.pin-dot{{width:14px;height:14px;border-radius:50%;background:var(--bdr);border:2px solid var(--bdr);transition:all 0.2s;}}
.pin-dot.filled{{background:var(--red);border-color:var(--red);}}
.pin-input{{position:absolute;opacity:0;width:1px;height:1px;}}
.pin-pad{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:16px 0;}}
.pk{{background:var(--bg);border:1.5px solid var(--bdr);border-radius:12px;padding:16px;font-size:20px;font-weight:700;font-family:'Space Mono',monospace;cursor:pointer;transition:all 0.15s;color:var(--text);text-align:center;}}
.pk:hover{{border-color:var(--red);background:var(--red-light);color:var(--red);}}
.pk:active{{transform:scale(0.95);}}
.pk.del{{font-size:14px;}}
</style></head><body>
<div class="aw"><div class="ac">
  <div class="alg">
    <p style="color:#fff;font-size:12px;font-weight:900;letter-spacing:3px;margin:0;">MODERATION SQUAD</p>
    <p style="color:rgba(255,255,255,0.7);font-size:9px;letter-spacing:2px;margin:6px 0 0;">MODERATOR PORTAL · INVITE ONLY</p>
  </div>

  <!-- Step 1: Email -->
  <div id="s1">
    <h2 style="font-size:18px;font-weight:800;margin-bottom:5px;color:var(--text);">Welcome back</h2>
    <p style="font-size:12px;color:var(--muted);margin-bottom:20px;line-height:1.6;">Enter your approved email address to continue.</p>
    <div id="e1" class="err" style="font-size:12px;line-height:1.6;"></div>
    <div class="form-group"><label class="form-label">Email Address</label>
      <input type="email" id="ein" class="form-input" placeholder="yourname@email.com" onkeydown="if(event.key==='Enter')goPin()"></div>
    <button class="btn bp" style="width:100%;padding:12px;" onclick="goPin()">Continue →</button>
    <div style="background:var(--red-light);border:1px solid var(--red-mid);border-radius:9px;padding:11px;font-size:11px;color:var(--muted);text-align:center;margin-top:14px;line-height:1.7;">
      🔒 <strong>Invite-only platform.</strong> Only pre-approved emails.<br>Contact <a href="mailto:{S_EMAIL}" style="color:var(--red);font-weight:600;">{S_EMAIL}</a></div>
  </div>

  <!-- Step 2: PIN pad -->
  <div id="s2" style="display:none;">
    <h2 style="font-size:18px;font-weight:800;margin-bottom:5px;color:var(--text);">Enter your PIN</h2>
    <p id="p2sub" style="font-size:12px;color:var(--muted);margin-bottom:16px;line-height:1.6;"></p>
    <div id="e2" class="err"></div>
    <div class="pin-wrap">
      <div class="pin-dot" id="pd1"></div>
      <div class="pin-dot" id="pd2"></div>
      <div class="pin-dot" id="pd3"></div>
      <div class="pin-dot" id="pd4"></div>
    </div>
    <div class="pin-pad">
      <button class="pk" onclick="pk('1')">1</button>
      <button class="pk" onclick="pk('2')">2</button>
      <button class="pk" onclick="pk('3')">3</button>
      <button class="pk" onclick="pk('4')">4</button>
      <button class="pk" onclick="pk('5')">5</button>
      <button class="pk" onclick="pk('6')">6</button>
      <button class="pk" onclick="pk('7')">7</button>
      <button class="pk" onclick="pk('8')">8</button>
      <button class="pk" onclick="pk('9')">9</button>
      <button class="pk del" onclick="clearPin()">✕</button>
      <button class="pk" onclick="pk('0')">0</button>
      <button class="pk del" onclick="delPin()">⌫</button>
    </div>
    <!-- Bottom links -->
    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:12px;gap:8px;">
      <button onclick="backToEmail()" style="background:none;border:none;color:var(--muted);font-size:11px;cursor:pointer;font-family:'Plus Jakarta Sans',sans-serif;">← Different email</button>
      <button onclick="openChangePinModal()" style="background:none;border:none;color:var(--red);font-size:11px;cursor:pointer;font-weight:600;font-family:'Plus Jakarta Sans',sans-serif;">🔐 Change PIN</button>
    </div>
    <!-- Different device notice -->
    <div id="device-notice" style="display:none;background:#fef2f2;border:1px solid #fecaca;border-radius:9px;padding:11px 13px;margin-top:12px;font-size:11px;color:var(--bad);line-height:1.7;text-align:center;">
      🔒 <strong>Access denied on this device.</strong><br>
      This account is locked to its own registered devices.<br>
      Even with the correct PIN, unregistered devices cannot log in.<br>
      <a href="mailto:{S_EMAIL}" style="color:var(--red);font-weight:700;">Contact support to reset →</a>
    </div>
  </div>
</div></div>

<!-- Change PIN Modal (on login screen) -->
<div id="cp-modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.55);z-index:1000;align-items:center;justify-content:center;">
  <div style="background:#fff;border-radius:18px;padding:32px;width:100%;max-width:380px;margin:14px;box-shadow:0 20px 60px rgba(0,0,0,0.2);">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;">
      <h3 style="font-size:16px;font-weight:800;color:var(--text);">🔐 Change PIN</h3>
      <button onclick="closeChangePinModal()" style="background:none;border:none;font-size:22px;cursor:pointer;color:var(--muted);">✕</button>
    </div>
    <div id="cp-err" style="background:#fef2f2;border:1px solid #fecaca;color:var(--bad);padding:10px 13px;border-radius:8px;font-size:12px;margin-bottom:14px;display:none;"></div>
    <div id="cp-device-warn" style="display:none;background:#fef3c7;border:1px solid #fde68a;border-radius:8px;padding:11px 13px;margin-bottom:14px;font-size:11px;color:#92400e;line-height:1.7;">
      🔒 <strong>PIN change locked to your first registered device.</strong><br><br>
      ✅ Both your registered devices (phone + laptop) can <strong>log in freely</strong>.<br>
      🔒 But only the <strong>first device</strong> that ever logged in can <strong>change the PIN</strong>.<br><br>
      Use that original device, or <a href="mailto:{S_EMAIL}" style="color:var(--red);font-weight:700;">contact support</a> to reset.
    </div>
    <div id="cp-form">
      <div style="background:var(--warn-bg);border:1px solid var(--warn-bdr);border-radius:8px;padding:10px 13px;margin-bottom:16px;font-size:11px;color:var(--warn);line-height:1.6;">
        ⚠️ You must enter your <strong>current PIN</strong> to set a new one.<br>
      ✅ Any device can <strong>log in</strong> · 🔒 Only your first device can <strong>change PIN</strong>
      </div>
      <div class="form-group"><label class="form-label">Current PIN</label>
        <input type="password" id="cp-old" class="form-input" placeholder="Enter current PIN" inputmode="numeric" maxlength="8"></div>
      <div class="form-group"><label class="form-label">New PIN</label>
        <input type="password" id="cp-new" class="form-input" placeholder="Min. 4 digits" inputmode="numeric" maxlength="8"></div>
      <div class="form-group"><label class="form-label">Confirm New PIN</label>
        <input type="password" id="cp-confirm" class="form-input" placeholder="Repeat new PIN" inputmode="numeric" maxlength="8"></div>
      <div style="display:flex;gap:8px;margin-top:4px;">
        <button onclick="closeChangePinModal()" class="btn bo bsm" style="flex:1;">Cancel</button>
        <button onclick="doChangePin()" class="btn bp bsm" style="flex:1;">Save PIN →</button>
      </div>
    </div>
  </div>
</div>

<script>
let em='', pin='';

function getDeviceId(){{
  let d=localStorage.getItem('ms_device_id');
  if(!d){{d='dev_'+Math.random().toString(36).substr(2,16)+'_'+Date.now();localStorage.setItem('ms_device_id',d);}}
  return d;
}}

function goPin(){{
  em=document.getElementById('ein').value.trim();
  if(!em){{showErr('e1','Please enter your email address.');return;}}
  hideErr('e1');
  // Check if this device is allowed to access this account BEFORE showing PIN pad
  fetch('/check_email',{{method:'POST',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{email:em,device_id:getDeviceId()}})}})
  .then(r=>r.json()).then(d=>{{
    if(!d.allowed){{
      showErr('e1',d.message);
      return;
    }}
    document.getElementById('p2sub').textContent='Signing in as '+em;
    document.getElementById('s1').style.display='none';
    document.getElementById('s2').style.display='block';
    pin=''; updateDots();
  }});
}}

function backToEmail(){{
  document.getElementById('s2').style.display='none';
  document.getElementById('s1').style.display='block';
  pin=''; updateDots();
}}

function pk(d){{
  if(pin.length>=4) return;
  pin+=d; updateDots();
  if(pin.length===4) setTimeout(doLogin,200);
}}

function delPin(){{ if(pin.length>0){{pin=pin.slice(0,-1); updateDots();}} }}
function clearPin(){{ pin=''; updateDots(); }}

function updateDots(){{
  for(let i=1;i<=4;i++){{
    document.getElementById('pd'+i).classList.toggle('filled', i<=pin.length);
  }}
}}

function doLogin(){{
  hideErr('e2');
  fetch('/login',{{method:'POST',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{email:em,pin:pin,device_id:getDeviceId()}})}})
  .then(r=>r.json()).then(d=>{{
    if(d.success){{window.location.href='/dashboard';}}
    else{{
      showErr('e2',d.message);
      pin=''; updateDots();
      // Show device notice if device blocked
      if(d.message && d.message.includes('device')){{
        document.getElementById('device-notice').style.display='block';
      }}
    }}
  }});
}}

function openChangePinModal(){{
  if(!em){{ showErr('e2','Please enter your email first.'); return; }}
  document.getElementById('cp-modal').style.display='flex';
  document.getElementById('cp-err').style.display='none';
  document.getElementById('cp-old').value='';
  document.getElementById('cp-new').value='';
  document.getElementById('cp-confirm').value='';
  // Check if same device
  fetch('/check_device',{{method:'POST',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{email:em,device_id:getDeviceId()}})}})
  .then(r=>r.json()).then(d=>{{
    if(!d.same_device){{
      document.getElementById('cp-device-warn').style.display='block';
      document.getElementById('cp-form').style.display='none';
    }} else {{
      document.getElementById('cp-device-warn').style.display='none';
      document.getElementById('cp-form').style.display='block';
    }}
  }});
}}

function closeChangePinModal(){{ document.getElementById('cp-modal').style.display='none'; }}

function doChangePin(){{
  const op=document.getElementById('cp-old').value.trim();
  const np=document.getElementById('cp-new').value.trim();
  const cp=document.getElementById('cp-confirm').value.trim();
  const err=document.getElementById('cp-err');
  err.style.display='none';
  if(!op||!np||!cp){{err.textContent='Please fill in all fields.';err.style.display='block';return;}}
  if(np!==cp){{err.textContent='New PINs do not match.';err.style.display='block';return;}}
  if(np.length<4||!/^[0-9]+$/.test(np)){{err.textContent='PIN must be at least 4 digits.';err.style.display='block';return;}}
  fetch('/change_pin_preauth',{{method:'POST',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{email:em,old_pin:op,new_pin:np,device_id:getDeviceId()}})}})
  .then(r=>r.json()).then(d=>{{
    if(d.success){{
      closeChangePinModal();
      showErr('e2',''); hideErr('e2');
      document.getElementById('p2sub').textContent='✅ PIN changed! Sign in with your new PIN.';
      pin=''; updateDots();
    }} else {{
      err.textContent=d.message; err.style.display='block';
    }}
  }});
}}

function showErr(id,msg){{const e=document.getElementById(id);e.textContent=msg;e.style.display='block';}}
function hideErr(id){{document.getElementById(id).style.display='none';}}
</script>
</body></html>"""


def dash_pg(user):
    name=user.get("name","Moderator"); since=user.get("member_since","—")
    v=user.get("verifications",{}); done=sum(1 for val in v.values() if val); total_v=len(v); pct=int(done/max(total_v,1)*100)
    notifs=notif_store.get(user.get("email",""),[])
    applied=user.get("applied_jobs",[])
    app_h=""
    for j in applied[-5:]:
        app_h+=f'<div style="display:flex;align-items:center;justify-content:space-between;padding:11px 14px;background:var(--bg);border-radius:9px;margin-bottom:7px;border:1px solid var(--bdr);"><div><div style="font-size:12px;font-weight:600;color:var(--text);">{j["title"]}</div><div style="font-size:10px;color:var(--muted);">{j["company"]} · {j["date"]} · ~{j.get("days",2)} day response</div></div><span class="bdg b-warn" style="font-size:9px;">Under Review</span></div>'
    if not applied: app_h='<div style="text-align:center;padding:24px;color:var(--muted);font-size:12px;">No applications yet. <a href="/jobs" style="color:var(--red);font-weight:600;">Browse jobs →</a></div>'
    nd_h=''.join(f'<div style="padding:10px 14px;border-bottom:1px solid var(--bdr);font-size:12px;line-height:1.5;"><div style="color:var(--text);">{n["msg"]}</div><div style="font-size:10px;color:var(--muted);margin-top:3px;">{n["time"]}</div></div>' for n in notifs[:5]) if notifs else '<div style="padding:20px;text-align:center;color:var(--muted);font-size:12px;">No notifications yet</div>'
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Dashboard — Moderation Squad</title>{CSS}</head><body>
<div class="layout">{sidebar_html("dashboard",user)}<div class="mc">
  <div class="topbar fi"><div><h1>👋 Welcome, {name}!</h1><p>{datetime.now().strftime("%A, %B %d, %Y")} · Newcomer Account</p></div>
    <div class="tr">
      <span class="bdg b-green">🇺🇸 USA Verified</span>
      <span class="bdg b-red">🔵 Newcomer</span>
      <div class="nbell" onclick="this.querySelector('.ndrop').classList.toggle('open')" style="position:relative;">
        <svg width="17" height="17" fill="none" stroke="#374151" stroke-width="2" viewBox="0 0 24 24"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
        {'<div class="ndot"></div>' if notifs else ''}
        <div class="ndrop"><div style="padding:12px 14px;border-bottom:1px solid var(--bdr);font-size:12px;font-weight:700;color:var(--text);">🔔 Notifications ({len(notifs)})</div>{nd_h}<div style="padding:8px;border-top:1px solid var(--bdr);text-align:center;"><a href="/notifications" style="font-size:11px;color:var(--red);font-weight:600;">View all →</a></div></div>
      </div>
    </div>
  </div>
  <div class="card fi fi1" style="margin-bottom:16px;background:linear-gradient(135deg,var(--red-light),#fff);border-color:var(--red-mid);">
    <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
      <div><h2 style="font-size:17px;font-weight:800;margin-bottom:6px;color:var(--text);">🚀 You're just getting started!</h2>
        <p style="font-size:12px;color:var(--muted);line-height:1.7;max-width:500px;">Set up your payment method to complete your profile. Verified moderators get hired <strong style="color:var(--red);">3× faster</strong>.</p></div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;"><a href="/earnings" class="btn bo bsm">💳 Setup Payment</a><a href="/jobs" class="btn bp bsm">Browse Jobs →</a></div>
    </div></div>
  <div class="g4 fi fi2" style="margin-bottom:16px;">
    <div class="sc c1"><div class="si2">💼</div><div class="sl">Jobs Done</div><div class="sv" style="color:var(--red);">0</div><div class="ss">Apply to get started</div></div>
    <div class="sc c2"><div class="si2">💰</div><div class="sl">Total Earned</div><div class="sv" style="color:var(--ok);">$0.00</div><div class="ss">Payouts every Friday</div></div>
    <div class="sc c3"><div class="si2">⭐</div><div class="sl">Rating</div><div class="sv" style="color:var(--pur);">—</div><div class="ss">Complete a job first</div></div>
    <div class="sc c4"><div class="si2">📅</div><div class="sl">Member Since</div><div class="sv" style="color:var(--warn);font-size:18px;">{since}</div><div class="ss">Account active</div></div>
  </div>
  <div class="g2 fi fi3" style="margin-bottom:16px;">
    <div class="card"><div class="sh"><h2>Account Level</h2><span class="bdg b-red">🔵 Newcomer</span></div>
      <p style="font-size:11px;color:var(--muted);margin-bottom:12px;line-height:1.6;">Complete 6 jobs to reach 🟢 Junior and unlock higher-paying roles</p>
      <div style="display:flex;justify-content:space-between;margin-bottom:5px;"><span style="font-size:10px;color:var(--muted);font-weight:600;">Progress to Junior</span><span style="font-size:10px;color:var(--red);font-weight:700;">0 / 6 jobs</span></div>
      <div class="pb" style="margin-bottom:16px;"><div class="pf" style="width:0%"></div></div>
      <div style="display:flex;justify-content:space-between;">
        <div style="text-align:center;"><div style="width:10px;height:10px;border-radius:50%;background:var(--red);margin:0 auto 4px;box-shadow:0 0 6px rgba(200,51,42,0.4);"></div><span style="font-size:8px;color:var(--red);font-weight:700;">NEWCOMER</span></div>
        <div style="text-align:center;"><div style="width:10px;height:10px;border-radius:50%;background:var(--bdr);margin:0 auto 4px;"></div><span style="font-size:8px;color:var(--muted);font-weight:600;">JUNIOR</span></div>
        <div style="text-align:center;"><div style="width:10px;height:10px;border-radius:50%;background:var(--bdr);margin:0 auto 4px;"></div><span style="font-size:8px;color:var(--muted);font-weight:600;">SENIOR</span></div>
        <div style="text-align:center;"><div style="width:10px;height:10px;border-radius:50%;background:var(--bdr);margin:0 auto 4px;"></div><span style="font-size:8px;color:var(--muted);font-weight:600;">ELITE</span></div>
      </div>
    </div>
    <div class="card"><div class="sh"><h2>Profile Completion</h2><span style="font-size:22px;font-weight:800;color:var(--red);">{pct}%</span></div>
      <div class="pb" style="margin-bottom:10px;"><div class="pf" style="width:{pct}%"></div></div>
      <p style="font-size:11px;color:var(--muted);margin-bottom:12px;line-height:1.6;">Almost done — just set up your payment method to reach 100%!</p>
      <div style="background:var(--warn-bg);border:1px solid var(--warn-bdr);border-radius:8px;padding:10px 12px;margin-bottom:10px;"><p style="font-size:11px;color:var(--warn);font-weight:700;">⚠️ 1 Step Remaining</p><p style="font-size:10px;color:var(--muted);margin-top:2px;">Set up your Payment Method to complete your profile.</p></div>
      <div style="background:var(--ok-bg);border:1px solid var(--ok-bdr);border-radius:8px;padding:10px 12px;"><p style="font-size:11px;color:var(--ok);font-weight:700;">✅ {done} Verified</p><p style="font-size:10px;color:var(--muted);margin-top:2px;">Email · USA Residence · Gov ID · W-9 Tax · Background Check</p></div>
    </div>
  </div>
  <div class="card fi fi4" style="margin-bottom:16px;"><div class="sh"><h2>My Applications</h2><a href="/applications" class="btn bp bsm">View All →</a></div>{app_h}</div>
  <div class="card fi fi5"><h2 style="font-size:14px;font-weight:700;margin-bottom:12px;color:var(--text);">Quick Actions</h2>
    <div style="display:flex;gap:8px;flex-wrap:wrap;">
      <a href="/jobs" class="btn bp bsm">💼 Jobs</a>
      <a href="/earnings" class="btn bo bsm">💳 Payment Setup</a>
      <a href="/training" class="btn bo bsm">📚 Training</a>
      <a href="/schedule" class="btn bo bsm">📅 Schedule</a>
      <a href="/livechat" class="btn bo bsm">💬 Live Chat</a>
      <a href="/support" class="btn bo bsm">❓ Help</a>
      <a href="/notifications" class="btn bo bsm">🔔 Notifications</a>
      <a href="/logout" class="btn" style="background:#fef2f2;color:var(--bad);border:1px solid #fecaca;padding:7px 14px;font-size:12px;">🚪 Sign Out</a>
    </div></div>
</div></div>
<script>document.addEventListener('click',e=>{{if(!e.target.closest('.nbell'))document.querySelectorAll('.ndrop').forEach(d=>d.classList.remove('open'));}});</script>
</body></html>"""

def jobs_pg(user, pg=1):
    page_jobs=[j for j in ALL_JOBS if j["pg"]==pg]; total_pages=4
    applied_titles=[j["title"] for j in user.get("applied_jobs",[])]
    saved_titles=[s["title"] for s in saved_store.get(user.get("email",""),[])]
    def jcard(j):
        if j["locked"]:
            return f'<div class="jc lk"><div class="jt" style="color:var(--muted);">🔒 {j["icon"]} {j["title"]}</div><div class="jco">🏢 {j["company"]}</div><div class="jm"><span class="tg tp">💵 {j["pay"]}</span><span class="tg tt">🕐 {j["hrs"]}</span></div><div style="font-size:10px;color:var(--muted);background:var(--bdr2);padding:6px 10px;border-radius:6px;margin-bottom:10px;">🔒 {j.get("req","")}</div><button class="btn bl bsm" disabled>🔒 Locked</button></div>'
        t=j["title"].replace("'","\\'"); c=j["company"].replace("'","\\'")
        p=j["pay"]; ic=j["icon"]; hrs=j["hrs"]
        already = j["title"] in applied_titles
        is_saved = j["title"] in saved_titles
        apply_btn = (f'<button class="btn bs bsm" disabled>✅ Applied</button>' if already else
                     f'<button class="btn bp bsm" id="ab_{t[:8].replace(" ","")}" onclick="applyJob(this,\'{t}\',\'{c}\',\'{p}\',\'{ic}\',\'{hrs}\')">Apply Now</button>')
        save_btn = f'<button class="btn {"bs" if is_saved else "bo"} bsm" onclick="saveJob(this,\'{t}\',\'{c}\',\'{p}\',\'{ic}\')" title="{"Saved" if is_saved else "Save job"}">{"🔖 Saved" if is_saved else "💾 Save"}</button>'
        status_badge = '<span class="bdg b-warn" style="font-size:9px;">📋 Applied</span>' if already else '<span class="bdg b-green" style="font-size:9px;">✅ Open</span>'
        return f'<div class="jc"><div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:5px;"><div class="jt">{ic} {j["title"]}</div>{status_badge}</div><div class="jco">🏢 {j["company"]}</div><div class="jd">{j["desc"]}</div><div class="jm"><span class="tg tp">💵 {j["pay"]}</span><span class="tg tt">🕐 {j["hrs"]}</span><span class="tg tl">📍 Remote·USA</span><span class="tg tn">🔵 Newcomer</span></div><div style="display:flex;gap:7px;">{apply_btn}{save_btn}</div></div>'
    cards="".join(jcard(j) for j in page_jobs)
    pgn="".join(f'<a href="/jobs?pg={i}" class="pgn-btn {"active" if i==pg else ""}">{i}</a>' for i in range(1,total_pages+1))
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Jobs — Moderation Squad</title>{CSS}
<style>.jg{{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:14px;}}</style>
</head><body><div class="layout">{sidebar_html("jobs",user)}<div class="mc">
  <div class="topbar fi"><div><h1>Browse Jobs</h1><p>Page {pg} of {total_pages} · 20 total positions</p></div>
    <div class="tr"><span class="bdg b-red">🔵 Newcomer</span><a href="/applications" class="btn bo bsm">📋 My Applications</a></div></div>
  <div class="card fi fi1" style="margin-bottom:18px;background:var(--red-light);border-color:var(--red-mid);">
    <p style="font-size:12px;color:var(--muted);line-height:1.7;">💡 <strong style="color:var(--text);">Newcomer Access:</strong> Page 1 has 5 open positions. Apply Now sends an instant email confirmation. Applied jobs move to <a href="/applications" style="color:var(--red);font-weight:600;">My Applications →</a> — the listing stays visible so you can track it.</p></div>
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;" class="fi fi2">
    <h2 style="font-size:14px;font-weight:700;color:var(--text);">{"✅ Open + Preview Positions" if pg==1 else "🔒 Locked — Level Up to Unlock"}</h2>
    <span style="font-size:12px;color:var(--muted);">{len(page_jobs)} positions on this page</span></div>
  <div class="jg fi fi2" style="margin-bottom:22px;">{cards}</div>
  <div class="pgn fi fi3">{pgn}<a href="/jobs?pg={min(pg+1,total_pages)}" class="pgn-btn" style="width:auto;padding:0 14px;font-size:12px;">Next →</a></div>
</div></div>
<div class="toast" id="toast"></div>
<script>
function applyJob(btn,t,c,p,ic,hrs){{
  btn.textContent='⏳ Submitting...';btn.disabled=true;
  fetch('/apply_job',{{method:'POST',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{title:t,company:c,pay:p,icon:ic,hrs:hrs}})}}).then(r=>r.json()).then(d=>{{
    if(d.success){{
      btn.textContent='✅ Applied';btn.className='btn bs bsm';
      // Update badge on card
      const card=btn.closest('.jc');
      const badge=card.querySelector('.bdg');
      if(badge){{badge.textContent='📋 Applied';badge.className='bdg b-warn';badge.style.fontSize='9px';}}
      showT('✅ Applied for '+t+'! Check your email — response in '+d.days+' day'+(d.days>1?'s':'')+'. <a href="/applications" style="color:#fff;text-decoration:underline;">View My Applications →</a>');
    }} else {{btn.textContent='Apply Now';btn.disabled=false;showT('Already applied for this position.');}}
  }});
}}
function saveJob(btn,t,c,p,ic){{
  fetch('/save_job',{{method:'POST',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{title:t,company:c,pay:p,icon:ic}})}}).then(r=>r.json()).then(d=>{{
    if(d.action==='saved'){{btn.textContent='🔖 Saved';btn.className='btn bs bsm';showT('💾 Job saved! View saved jobs in My Applications.');}}
    else{{btn.textContent='💾 Save';btn.className='btn bo bsm';showT('Removed from saved jobs.');}}
  }});
}}
function showT(m){{const t=document.getElementById('toast');t.innerHTML=m;t.className='toast ti show';setTimeout(()=>t.classList.remove('show'),5000);}}
</script></body></html>"""

def profile_pg(user):
    name=user.get("name","Moderator"); email=user.get("email","—"); since=user.get("member_since","—")
    avatar=user.get("avatar",""); v=user.get("verifications",{})
    vitems=[
        ("email","📧","Email Address","Verified via OTP secure login",True),
        ("residence","🇺🇸","USA Residence","Physical location confirmed — United States",True),
        ("id","🪪","Government ID","Valid US government-issued photo ID verified",True),
        ("tax","📋","W-9 Tax Form","Tax compliance form submitted and approved",True),
        ("payment","💳","Payment Method","Set up your preferred payout method",False),
        ("background","🔒","Background Check","Standard background verification complete",True),
    ]
    done=sum(1 for *_,ok in vitems if ok); pct=int(done/len(vitems)*100)
    avc=f'<img src="{avatar}" style="width:100%;height:100%;object-fit:cover;">' if avatar else f'<span>{name[0].upper()}</span>'
    rows="".join(f'<div class="vi"><div class="vl"><div class="vic {"vd-bg" if ok else "vw-bg"}">{ic}</div><div><div class="vn">{lb}</div><div class="vs2">{sb2}</div></div></div><span class="vst {"vst-ok" if ok else "vst-warn"}">{"✅ Verified" if ok else "⚠️ Required"}</span></div>' for k,ic,lb,sb2,ok in vitems)
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Profile — Moderation Squad</title>{CSS}</head><body>
<div class="layout">{sidebar_html("profile",user)}<div class="mc">
  <div class="topbar fi"><div><h1>My Profile</h1><p>Manage account and verifications</p></div>
    <div class="tr"><span class="bdg b-green">🇺🇸 USA Verified</span>
    <a href="/logout" class="btn" style="background:#fef2f2;color:var(--bad);border:1px solid #fecaca;font-size:12px;padding:7px 14px;">🚪 Sign Out</a></div></div>
  <div class="g2 fi fi1" style="margin-bottom:16px;">
    <div class="card"><div style="display:flex;align-items:center;gap:14px;margin-bottom:18px;">
        <div class="avw"><div class="av" id="avd">{avc}</div><div class="ave" onclick="document.getElementById('af').click()">✏️</div><input type="file" id="af" accept="image/*" style="display:none" onchange="upAv(this)"></div>
        <div><h2 style="font-size:17px;font-weight:800;color:var(--text);">{name}</h2><p style="font-size:11px;color:var(--muted);margin-top:2px;">Chat Moderator</p>
          <div style="display:flex;gap:6px;margin-top:8px;flex-wrap:wrap;"><span class="bdg b-red" style="font-size:9px;">🔵 Newcomer</span><span class="bdg b-green" style="font-size:9px;">🇺🇸 USA</span></div></div></div>
      <div style="border-top:1px solid var(--bdr);padding-top:14px;display:grid;grid-template-columns:1fr 1fr;gap:12px;">
        <div><div style="font-size:9px;color:var(--muted);margin-bottom:3px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;">Email</div><div style="font-size:12px;word-break:break-all;color:var(--text);">{email}</div></div>
        <div><div style="font-size:9px;color:var(--muted);margin-bottom:3px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;">Member Since</div><div style="font-size:12px;color:var(--text);">{since}</div></div>
        <div><div style="font-size:9px;color:var(--muted);margin-bottom:3px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;">Jobs Done</div><div style="font-size:12px;color:var(--red);font-weight:700;">0</div></div>
        <div><div style="font-size:9px;color:var(--muted);margin-bottom:3px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;">Level</div><div style="font-size:12px;color:var(--red);font-weight:700;">🔵 Newcomer</div></div>
        <div><div style="font-size:9px;color:var(--muted);margin-bottom:3px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;">Location</div><div style="font-size:12px;color:var(--text);">🇺🇸 United States</div></div>
        <div><div style="font-size:9px;color:var(--muted);margin-bottom:3px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;">Rating</div><div style="font-size:12px;color:var(--muted);">No ratings yet</div></div>
      </div>
      <div style="margin-top:14px;padding-top:14px;border-top:1px solid var(--bdr);display:flex;gap:8px;">
        <a href="/logout" class="btn" style="background:#fef2f2;color:var(--bad);border:1px solid #fecaca;font-size:12px;padding:7px 14px;flex:1;justify-content:center;">🚪 Sign Out</a>
        <button onclick="openPinModal()" class="btn bo bsm" style="flex:1;border-color:var(--red);color:var(--red);">🔐 Change PIN</button>
        <a href="/earnings" class="btn bp bsm" style="flex:1;">💳 Setup Payment</a>
      </div>
    </div>
    <div class="card"><div class="sh"><h2>Profile Completion</h2><span style="font-size:22px;font-weight:800;color:var(--red);">{pct}%</span></div>
      <div class="pb" style="margin-bottom:10px;"><div class="pf" style="width:{pct}%"></div></div>
      <p style="font-size:11px;color:var(--muted);margin-bottom:14px;line-height:1.6;">Almost complete — just your payment method remaining.</p>
      <div style="background:var(--ok-bg);border:1px solid var(--ok-bdr);border-radius:9px;padding:12px;margin-bottom:10px;">
        <p style="font-size:11px;color:var(--ok);font-weight:700;margin-bottom:4px;">✅ {done} of {len(vitems)} Verified</p>
        <p style="font-size:10px;color:var(--muted);">Email · USA Residence · Gov ID · W-9 Tax Form · Background Check</p></div>
      <div style="background:var(--warn-bg);border:1px solid var(--warn-bdr);border-radius:9px;padding:12px;margin-bottom:14px;">
        <p style="font-size:11px;color:var(--warn);font-weight:700;margin-bottom:4px;">⚠️ 1 Step Remaining</p>
        <p style="font-size:10px;color:var(--muted);">Set up your Payment Method to complete your profile and receive earnings.</p></div>
      <a href="/earnings" class="btn bp bsm" style="width:100%;">💳 Setup Payment Method →</a>
    </div>
  </div>
  <div class="card fi fi2"><div class="sh"><h2>Verification Status</h2><span style="font-size:11px;color:var(--muted);">{done}/{len(vitems)} complete</span></div>{rows}</div>
</div></div>
<div class="toast" id="toast"></div>
<script>
function upAv(input){{const file=input.files[0];if(!file)return;const r=new FileReader();
  r.onload=e=>{{document.getElementById('avd').innerHTML=`<img src="${{e.target.result}}" style="width:100%;height:100%;object-fit:cover;">`;
    fetch('/upload_avatar',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{image:e.target.result}})}}).then(r=>r.json()).then(d=>{{
      if(d.success){{const t=document.getElementById('toast');t.textContent='📸 Profile picture updated!';t.className='toast ts show';setTimeout(()=>t.classList.remove('show'),3000);}}}});}};r.readAsDataURL(file);}}
function getDeviceId(){{let d=localStorage.getItem('ms_device_id');if(!d){{d='dev_'+Math.random().toString(36).substr(2,16)+'_'+Date.now();localStorage.setItem('ms_device_id',d);}}return d;}}
function openPinModal(){{document.getElementById('pin-modal').style.display='flex';document.getElementById('pm-err').style.display='none';document.getElementById('old-pin').value='';document.getElementById('new-pin').value='';document.getElementById('confirm-pin').value='';}}
function closePinModal(){{document.getElementById('pin-modal').style.display='none';}}
function submitPinChange(){{
  const op=document.getElementById('old-pin').value.trim();
  const np=document.getElementById('new-pin').value.trim();
  const cp=document.getElementById('confirm-pin').value.trim();
  const err=document.getElementById('pm-err');
  err.style.display='none';
  if(!op||!np||!cp){{err.textContent='Please fill in all fields.';err.style.display='block';return;}}
  if(np!==cp){{err.textContent='New PINs do not match.';err.style.display='block';return;}}
  if(np.length<4||!/^[0-9]+$/.test(np)){{err.textContent='PIN must be at least 4 digits.';err.style.display='block';return;}}
  fetch('/change_pin',{{method:'POST',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{old_pin:op,new_pin:np,device_id:getDeviceId()}})}})
  .then(r=>r.json()).then(d=>{{
    if(d.success){{closePinModal();const t=document.getElementById('toast');t.textContent='🔐 PIN changed successfully!';t.className='toast ts show';setTimeout(()=>t.classList.remove('show'),3500);}}
    else{{err.textContent=d.message;err.style.display='block';}}
  }});
}}
</script>
<div id="pin-modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:1000;align-items:center;justify-content:center;">
  <div style="background:#fff;border-radius:18px;padding:32px;width:100%;max-width:380px;margin:14px;box-shadow:0 20px 60px rgba(0,0,0,0.2);">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;">
      <h3 style="font-size:16px;font-weight:800;color:var(--text);">🔐 Change PIN</h3>
      <button onclick="closePinModal()" style="background:none;border:none;font-size:20px;cursor:pointer;color:var(--muted);">✕</button>
    </div>
    <div id="pm-err" style="background:#fef2f2;border:1px solid #fecaca;color:var(--bad);padding:10px 13px;border-radius:8px;font-size:12px;margin-bottom:14px;display:none;"></div>
    <div style="background:var(--warn-bg);border:1px solid var(--warn-bdr);border-radius:8px;padding:10px 13px;margin-bottom:16px;font-size:11px;color:var(--warn);line-height:1.6;">
      ✅ <strong>Login:</strong> Up to 2 devices per account (e.g. phone + laptop).<br>
      🔒 <strong>Change PIN:</strong> Only your first registered device can change the PIN.<br>
      🚫 <strong>Security:</strong> No other account can access your account. Ever.<br>
      Need help? <a href="mailto:{S_EMAIL}" style="color:var(--red);font-weight:600;">Contact support</a>.
    </div>
    <div class="form-group"><label class="form-label">Current PIN</label>
      <input type="password" id="old-pin" class="form-input" placeholder="Enter current PIN" inputmode="numeric" maxlength="8"></div>
    <div class="form-group"><label class="form-label">New PIN</label>
      <input type="password" id="new-pin" class="form-input" placeholder="Min. 4 digits" inputmode="numeric" maxlength="8"></div>
    <div class="form-group"><label class="form-label">Confirm New PIN</label>
      <input type="password" id="confirm-pin" class="form-input" placeholder="Repeat new PIN" inputmode="numeric" maxlength="8"></div>
    <div style="display:flex;gap:8px;margin-top:4px;">
      <button onclick="closePinModal()" class="btn bo bsm" style="flex:1;">Cancel</button>
      <button onclick="submitPinChange()" class="btn bp bsm" style="flex:1;">Save New PIN →</button>
    </div>
  </div>
</div>
</body></html>"""

def applications_pg(user):
    email = user.get("email","")
    applied = user.get("applied_jobs",[])
    saved = saved_store.get(email,[])

    def app_row(j, idx):
        icon = j.get("icon","💼")
        status_cl = "b-warn" if j["status"]=="Under Review" else "b-green"
        status_lbl = "⏳ Under Review" if j["status"]=="Under Review" else "✅ " + j["status"]
        return f"""<div style="background:#fff;border:1px solid var(--bdr);border-radius:13px;padding:18px;box-shadow:var(--shadow);margin-bottom:10px;">
          <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:10px;">
            <div style="display:flex;align-items:center;gap:12px;">
              <div style="width:42px;height:42px;border-radius:10px;background:var(--red-light);border:1px solid var(--red-mid);display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0;">{icon}</div>
              <div>
                <div style="font-size:14px;font-weight:700;color:var(--text);">{j["title"]}</div>
                <div style="font-size:11px;color:var(--muted);margin-top:2px;">🏢 {j["company"]}</div>
                <div style="display:flex;gap:6px;margin-top:6px;flex-wrap:wrap;">
                  <span class="tg tp">💵 {j["pay"]}</span>
                  <span class="tg tt">🕐 {j.get("hrs","Flexible")}</span>
                  <span class="tg tl">📍 Remote · USA</span>
                </div>
              </div>
            </div>
            <div style="text-align:right;flex-shrink:0;">
              <span class="bdg {status_cl}" style="font-size:10px;display:block;margin-bottom:6px;">{status_lbl}</span>
              <div style="font-size:10px;color:var(--muted);">Applied {j["date"]}</div>
              <div style="font-size:10px;color:var(--muted);">~{j.get("days",2)} day response</div>
            </div>
          </div>
          <div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--bdr);display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
            <div style="background:var(--warn-bg);border:1px solid var(--warn-bdr);border-radius:7px;padding:6px 12px;font-size:11px;color:var(--warn);font-weight:600;">
              ⏳ Awaiting response — check your email for updates
            </div>
            <a href="/livechat" class="btn bo bsm" style="font-size:11px;">💬 Ask Support</a>
          </div>
        </div>"""

    def saved_row(s):
        return f"""<div style="background:#fff;border:1px solid var(--bdr);border-radius:13px;padding:16px;box-shadow:var(--shadow);margin-bottom:10px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">
          <div style="display:flex;align-items:center;gap:11px;">
            <div style="width:38px;height:38px;border-radius:9px;background:var(--bdr2);display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;">{s.get("icon","💼")}</div>
            <div>
              <div style="font-size:13px;font-weight:700;color:var(--text);">{s["title"]}</div>
              <div style="font-size:11px;color:var(--muted);">{s["company"]} · {s["pay"]}</div>
            </div>
          </div>
          <div style="display:flex;gap:7px;">
            <a href="/jobs" class="btn bp bsm" style="font-size:11px;">Apply Now</a>
            <button class="btn bo bsm" style="font-size:11px;" onclick="unsave(this,'{s["title"].replace("'","\\'")}')">🗑 Remove</button>
          </div>
        </div>"""

    applied_html = "".join(app_row(j,i) for i,j in enumerate(reversed(applied))) if applied else \
        '<div style="text-align:center;padding:40px;color:var(--muted);font-size:13px;"><div style="font-size:40px;margin-bottom:12px;">📋</div><p>No applications yet.</p><a href="/jobs" class="btn bp bsm" style="margin-top:12px;">Browse Jobs →</a></div>'

    saved_html = "".join(saved_row(s) for s in saved) if saved else \
        '<div style="text-align:center;padding:30px;color:var(--muted);font-size:12px;"><div style="font-size:32px;margin-bottom:10px;">🔖</div><p>No saved jobs. Click 💾 Save on any job to bookmark it here.</p></div>'

    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>My Applications — Moderation Squad</title>{CSS}</head><body>
<div class="layout">{sidebar_html("applications",user)}<div class="mc">
  <div class="topbar fi"><div><h1>My Applications</h1><p>Track every job you've applied for</p></div>
    <div class="tr"><span class="bdg b-warn">{len(applied)} Applied</span><a href="/jobs" class="btn bp bsm">Browse More Jobs →</a></div></div>

  <!-- Stats row -->
  <div class="g3 fi fi1" style="margin-bottom:18px;">
    <div class="sc c1"><div class="si2">📋</div><div class="sl">Total Applied</div><div class="sv" style="color:var(--red);">{len(applied)}</div><div class="ss">All time</div></div>
    <div class="sc c4"><div class="si2">⏳</div><div class="sl">Under Review</div><div class="sv" style="color:var(--warn);">{sum(1 for j in applied if j["status"]=="Under Review")}</div><div class="ss">Awaiting response</div></div>
    <div class="sc c2"><div class="si2">🔖</div><div class="sl">Saved Jobs</div><div class="sv" style="color:var(--ok);">{len(saved)}</div><div class="ss">Ready to apply</div></div>
  </div>

  <!-- Info banner -->
  <div class="card fi fi1" style="margin-bottom:18px;background:var(--red-light);border-color:var(--red-mid);">
    <p style="font-size:12px;color:var(--muted);line-height:1.8;">
      📧 <strong style="color:var(--text);">Email confirmations</strong> are sent automatically when you apply. Check your inbox (and spam folder) for response updates.
      Response times are <strong style="color:var(--text);">1–3 business days</strong>. The job listing stays open after you apply — each position can have multiple moderators.
    </p>
  </div>

  <!-- Applied jobs -->
  <div class="card fi fi2" style="margin-bottom:18px;">
    <div class="sh" style="margin-bottom:14px;"><h2>📋 Applied Jobs ({len(applied)})</h2>
      <span style="font-size:11px;color:var(--muted);">Most recent first</span></div>
    {applied_html}
  </div>

  <!-- Saved jobs -->
  <div class="card fi fi3">
    <div class="sh" style="margin-bottom:14px;"><h2>🔖 Saved Jobs ({len(saved)})</h2>
      <a href="/jobs" class="btn bo bsm" style="font-size:11px;">Browse More</a></div>
    {saved_html}
  </div>
</div></div>
<div class="toast" id="toast"></div>
<script>
function unsave(btn,t){{
  fetch('/save_job',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{title:t,company:'',pay:'',icon:''}})}})
    .then(r=>r.json()).then(d=>{{btn.closest('div[style*="border-radius:13px"]').remove();
      const t2=document.getElementById('toast');t2.textContent='Removed from saved jobs.';t2.className='toast ti show';setTimeout(()=>t2.classList.remove('show'),3000);}});
}}
</script></body></html>"""

def earnings_pg(user):
    mo=datetime.now().strftime("%B %Y")
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Earnings — Moderation Squad</title>{CSS}</head><body>
<div class="layout">{sidebar_html("earnings",user)}<div class="mc">
  <div class="topbar fi"><div><h1>Earnings & Payments</h1><p>Payouts every Friday</p></div><span class="bdg b-green">🇺🇸 Verified</span></div>
  <div class="g4 fi fi1" style="margin-bottom:16px;">
    <div class="sc c1"><div class="si2">📅</div><div class="sl">This Week</div><div class="sv" style="color:var(--red);">$0.00</div><div class="ss">No assignments yet</div></div>
    <div class="sc c2"><div class="si2">📆</div><div class="sl">This Month</div><div class="sv" style="color:var(--ok);">$0.00</div><div class="ss">{mo}</div></div>
    <div class="sc c3"><div class="si2">💰</div><div class="sl">Total Earned</div><div class="sv" style="color:var(--pur);">$0.00</div><div class="ss">Lifetime</div></div>
    <div class="sc c4"><div class="si2">🗓️</div><div class="sl">Next Payout</div><div class="sv" style="color:var(--warn);font-size:17px;">—</div><div class="ss">Set up payment first</div></div>
  </div>
  <div class="g2 fi fi2" style="margin-bottom:16px;">
    <div class="card">
      <h2 style="font-size:14px;font-weight:700;margin-bottom:5px;color:var(--text);">💳 Payment Method</h2>
      <p style="font-size:11px;color:var(--muted);margin-bottom:14px;">Choose how you'd like to receive your weekly earnings.</p>
      <div style="background:var(--warn-bg);border:1px solid var(--warn-bdr);border-radius:9px;padding:11px 13px;margin-bottom:14px;">
        <p style="font-size:11px;color:var(--warn);font-weight:700;">⚠️ Payment method not set up yet</p>
        <p style="font-size:10px;color:var(--muted);margin-top:2px;">This is the last step to complete your profile.</p></div>
      <div style="display:flex;flex-direction:column;gap:7px;">
        <button class="btn bo bsm" style="justify-content:space-between;" onclick="pk('Direct Deposit (ACH)')"><span>🏦 Direct Deposit (ACH)</span><span style="font-size:9px;color:var(--ok);background:var(--ok-bg);border:1px solid var(--ok-bdr);padding:2px 6px;border-radius:4px;">Recommended</span></button>
        <button class="btn bo bsm" onclick="pk('PayPal')">💰 PayPal</button>
        <button class="btn bo bsm" onclick="pk('Payoneer')">🌐 Payoneer</button>
        <button class="btn bo bsm" onclick="pk('Tipalti')">🧾 Tipalti (US Only)</button>
        <button class="btn bo bsm" onclick="pk('Paper Check')">📬 Paper Check</button>
      </div>
    </div>
    <div class="card">
      <h2 style="font-size:14px;font-weight:700;margin-bottom:5px;color:var(--text);">📋 Tax Information</h2>
      <p style="font-size:11px;color:var(--muted);margin-bottom:14px;">W-9 required for all US moderators earning over $600/year.</p>
      <div class="vi" style="margin-bottom:7px;"><div class="vl"><div class="vic vd-bg">📋</div><div><div class="vn">W-9 Tax Form</div><div class="vs2">US tax compliance</div></div></div><span class="vst vst-ok">✅ Submitted</span></div>
      <div class="vi" style="margin-bottom:14px;"><div class="vl"><div class="vic vd-bg">✅</div><div><div class="vn">Tax ID Verified</div><div class="vs2">IRS compliance confirmed</div></div></div><span class="vst vst-ok">✅ Verified</span></div>
      <div style="background:var(--ok-bg);border:1px solid var(--ok-bdr);border-radius:8px;padding:10px 13px;">
        <p style="font-size:11px;color:var(--ok);font-weight:700;">✅ Tax compliance complete</p>
        <p style="font-size:10px;color:var(--muted);margin-top:2px;">No further action needed. Just set up your payment method above.</p></div>
    </div>
  </div>
  <div class="card fi fi3"><div class="sh"><h2>Payment History</h2><span style="font-size:11px;color:var(--muted);">No transactions yet</span></div>
    <div style="text-align:center;padding:48px 20px;">
      <div style="font-size:48px;margin-bottom:14px;">💳</div>
      <h3 style="font-size:17px;font-weight:800;margin-bottom:7px;color:var(--text);">No payments yet</h3>
      <p style="font-size:12px;color:var(--muted);max-width:320px;margin:0 auto 22px;line-height:1.7;">Payment history will appear here after your first completed assignment and Friday payout.</p>
      <a href="/jobs" class="btn bp bsm">Browse Available Jobs →</a></div></div>
</div></div>
<div class="toast" id="toast"></div>
<script>
function pk(m){{const t=document.getElementById('toast');t.textContent='💳 '+m+' selected! Complete setup to activate payouts.';t.className='toast ti show';setTimeout(()=>t.classList.remove('show'),4000);}}
</script></body></html>"""

def notif_pg(user):
    notifs=notif_store.get(user.get("email",""),[])
    rows=''.join(f'<div style="display:flex;gap:12px;padding:15px;background:#fff;border-radius:11px;margin-bottom:8px;border:1px solid var(--bdr);box-shadow:var(--shadow);"><div style="font-size:20px;flex-shrink:0;">🔔</div><div><div style="font-size:13px;line-height:1.6;color:var(--text);">{n["msg"]}</div><div style="font-size:10px;color:var(--muted);margin-top:5px;">{n["time"]}</div></div></div>' for n in notifs) if notifs else '<div style="text-align:center;padding:48px;color:var(--muted);font-size:13px;">No notifications yet. Apply for jobs to get started!</div>'
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Notifications — Moderation Squad</title>{CSS}</head><body>
<div class="layout">{sidebar_html("notifications",user)}<div class="mc">
  <div class="topbar fi"><div><h1>Notifications</h1><p>{len(notifs)} total notifications</p></div></div>
  <div class="card fi fi1">{rows}</div>
</div></div></body></html>"""

def schedule_pg(user):
    days=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    slots=["Morning (6AM–12PM)","Afternoon (12PM–6PM)","Evening (6PM–12AM)","Night (12AM–6AM)"]
    rows="".join(f"<tr><td style='padding:12px 16px;font-size:12px;font-weight:600;border-bottom:1px solid var(--bdr);color:var(--text);'>{d}</td>"+"".join(f"<td style='padding:12px;text-align:center;border-bottom:1px solid var(--bdr);border-left:1px solid var(--bdr);'><input type='checkbox' style='width:16px;height:16px;accent-color:var(--red);cursor:pointer;' onchange='sv()'></td>" for _ in slots)+"</tr>" for d in days)
    hds="".join(f"<th style='padding:10px 12px;text-align:center;font-size:9px;color:var(--muted);letter-spacing:1px;text-transform:uppercase;border-bottom:2px solid var(--bdr);border-left:1px solid var(--bdr);font-weight:700;'>{s}</th>" for s in slots)
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Schedule — Moderation Squad</title>{CSS}</head><body>
<div class="layout">{sidebar_html("schedule",user)}<div class="mc">
  <div class="topbar fi"><div><h1>My Schedule</h1><p>Set your weekly availability — all times Eastern (EST)</p></div><button class="btn bp bsm" onclick="sv()">💾 Save Schedule</button></div>
  <div class="card fi fi1" style="margin-bottom:16px;background:var(--red-light);border-color:var(--red-mid);">
    <p style="font-size:12px;color:var(--muted);line-height:1.7;">📅 Select your available time slots. Clients will schedule you based on what you check. All times are <strong style="color:var(--text);">Eastern Time (EST)</strong>. You can update this at any time.</p></div>
  <div class="card fi fi2" style="overflow-x:auto;">
    <table style="width:100%;border-collapse:collapse;min-width:480px;">
      <thead><tr><th style="padding:11px 16px;text-align:left;font-size:9px;color:var(--muted);letter-spacing:1px;text-transform:uppercase;border-bottom:2px solid var(--bdr);font-weight:700;">Day</th>{hds}</tr></thead>
      <tbody>{rows}</tbody></table></div>
</div></div>
<div class="toast" id="toast"></div>
<script>function sv(){{const t=document.getElementById('toast');t.textContent='✅ Schedule saved successfully!';t.className='toast ts show';setTimeout(()=>t.classList.remove('show'),3000);}}</script>
</body></html>"""

def training_pg(user):
    cards="".join(f"""<div class="card" style="{'opacity:0.42;' if c['locked'] else 'cursor:pointer;transition:all 0.2s;'}" {"onclick=\"window.location='/training?c="+str(c['id'])+"'\"" if not c['locked'] else ''} {"onmouseover=\"this.style.borderColor='var(--red)';this.style.boxShadow='var(--shadow-md)';this.style.transform='translateY(-2px)'\" onmouseout=\"this.style.borderColor='var(--bdr)';this.style.boxShadow='var(--shadow)';this.style.transform='none'\"" if not c['locked'] else ''}>
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;">
        <div style="font-size:28px;">{c['icon']}</div>
        <div style="display:flex;gap:5px;">
          <span class="bdg {"b-green" if c["level"]=="Beginner" else "b-warn" if c["level"]=="Intermediate" else "b-pur"}" style="font-size:9px;">{c['level']}</span>
          <span class="bdg b-blue" style="font-size:9px;">🕐 {c['dur']}</span>
        </div>
      </div>
      <h3 style="font-size:14px;font-weight:700;margin-bottom:7px;color:var(--text);">{c['title']}</h3>
      <p style="font-size:11px;color:var(--muted);line-height:1.7;margin-bottom:14px;">{c['desc']}</p>
      {'<div style="font-size:10px;color:var(--muted);background:var(--bdr2);padding:5px 10px;border-radius:6px;margin-bottom:12px;">🔒 Unlocks at '+c["level"]+' level</div>' if c['locked'] else f'<div style="font-size:10px;color:var(--ok);margin-bottom:11px;font-weight:600;background:var(--ok-bg);border:1px solid var(--ok-bdr);padding:5px 10px;border-radius:6px;">✅ {len(c["lessons"])} interactive lessons · Quiz · Certificate</div>'}
      <button class="btn {"bl" if c["locked"] else "bp"} bsm" style="width:100%;" {"disabled" if c["locked"] else "onclick=\"window.location='/training?c="+str(c["id"])+"'\""}>{"🔒 Locked" if c["locked"] else "▶ Start Course"}</button>
    </div>""" for c in COURSES)
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Training — Moderation Squad</title>{CSS}</head><body>
<div class="layout">{sidebar_html("training",user)}<div class="mc">
  <div class="topbar fi"><div><h1>Training Center</h1><p>Build skills and unlock better opportunities</p></div><span class="bdg b-green">✨ 3 Free Courses Available</span></div>
  <div class="card fi fi1" style="margin-bottom:20px;background:var(--red-light);border-color:var(--red-mid);">
    <p style="font-size:12px;color:var(--muted);line-height:1.7;">📚 <strong style="color:var(--text);">Free Training:</strong> All Beginner courses are completely free with full interactive lessons, quizzes, and certificates. <strong style="color:var(--red);">Click any beginner course to start learning immediately</strong> — no waiting required.</p></div>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:16px;" class="fi fi2">{cards}</div>
</div></div></body></html>"""

def course_pg(user, cid, lid):
    if cid>=len(COURSES): return redirect("/training")
    course=COURSES[cid]
    if course["locked"]: return redirect("/training")
    lessons=course["lessons"]
    if lid>=len(lessons): lid=len(lessons)-1
    ltitle,lcontent=lessons[lid]
    total=len(lessons); is_last=(lid==total-1)
    prog=int((lid/(total-1))*100) if total>1 else 100
    pills="".join(f'<a href="/training?c={cid}&l={i}" style="display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;border-radius:50%;font-size:11px;font-weight:700;{"background:var(--red);color:#fff;" if i==lid else "background:var(--ok-bg);color:var(--ok);border:1px solid var(--ok-bdr);" if i<lid else "background:var(--bdr2);color:var(--muted);border:1px solid var(--bdr);"}text-decoration:none;transition:all 0.2s;" title="Lesson {i+1}">{i+1}</a>' for i in range(total))
    content_h=lcontent.replace("\n","<br>")
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{course['title']} — Moderation Squad</title>{CSS}</head><body>
<div class="layout">{sidebar_html("training",user)}<div class="mc">
  <div class="topbar fi">
    <div><a href="/training" style="font-size:12px;color:var(--muted);display:flex;align-items:center;gap:5px;margin-bottom:6px;font-weight:500;">← Back to Training</a>
      <h1 style="font-size:18px;">{course['icon']} {course['title']}</h1><p>Lesson {lid+1} of {total} · {course['dur']}</p></div>
    <span class="bdg {"b-green" if is_last else "b-red"}">{prog}% Complete</span></div>
  <div class="card fi fi1" style="margin-bottom:16px;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
      <span style="font-size:10px;color:var(--muted);font-weight:700;text-transform:uppercase;letter-spacing:1px;">Course Progress</span>
      <span style="font-size:11px;color:var(--red);font-weight:700;">Lesson {lid+1} / {total}</span></div>
    <div class="pb" style="margin-bottom:12px;"><div class="pf" style="width:{prog}%"></div></div>
    <div style="display:flex;gap:6px;flex-wrap:wrap;">{pills}</div></div>
  <div class="card fi fi2" style="margin-bottom:16px;">
    <div style="display:flex;align-items:center;gap:11px;margin-bottom:18px;padding-bottom:14px;border-bottom:1px solid var(--bdr);">
      <div style="width:38px;height:38px;border-radius:10px;background:var(--red-light);border:1px solid var(--red-mid);display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;">{course['icon']}</div>
      <div><h2 style="font-size:16px;font-weight:800;color:var(--text);">{ltitle}</h2><p style="font-size:11px;color:var(--muted);">{course['title']} · Lesson {lid+1}</p></div>
    </div>
    <div style="font-size:13px;line-height:2;color:var(--text);">{content_h}</div></div>
  <div class="card fi fi3" style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
    <div>{"<a href='/training?c="+str(cid)+"&l="+str(lid-1)+"' class='btn bo bsm'>← Previous Lesson</a>" if lid>0 else '<span style="font-size:12px;color:var(--muted);">First lesson</span>'}</div>
    <div style="font-size:12px;color:var(--muted);font-weight:600;">{lid+1} / {total} lessons</div>
    <div>{"<a href='/training' class='btn bp bsm'>🎓 Complete Course ✓</a>" if is_last else "<a href='/training?c="+str(cid)+"&l="+str(lid+1)+"' class='btn bp bsm'>Next Lesson →</a>"}</div>
  </div>
</div></div></body></html>"""

def livechat_pg(user):
    name=user.get("name","Moderator"); email=user.get("email","")
    history=chat_store.get(email,[])
    hist_h=''.join(f'<div class="cmsg {"sup" if m["role"]=="support" else "usr"}"><div>{m["msg"]}</div><div class="mt">{m["time"]}</div></div>' for m in history)
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Live Support — Moderation Squad</title>{CSS}</head><body>
<div class="layout">{sidebar_html("livechat",user)}<div class="mc">
  <div class="topbar fi"><div><h1>Live Support Chat</h1><p>Real-time help from our support team</p></div><span class="bdg b-green">🟢 Online Now</span></div>
  <div class="g2 fi fi1" style="margin-bottom:16px;">
    <div class="sc c1"><div class="si2">⚡</div><div class="sl">Avg Response</div><div class="sv" style="color:var(--red);font-size:20px;">&lt;2 min</div><div class="ss">Business hours</div></div>
    <div class="sc c2"><div class="si2">🕐</div><div class="sl">Hours</div><div class="sv" style="color:var(--ok);font-size:16px;">Mon–Fri</div><div class="ss">9AM–6PM Eastern</div></div></div>
  <div class="card fi fi2">
    <div class="chat-hdr">
      <div style="width:40px;height:40px;border-radius:50%;background:var(--red);display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;">👩‍💼</div>
      <div><div style="font-size:13px;font-weight:700;color:var(--text);">ModSquad Support Agent</div><div style="font-size:10px;color:var(--ok);font-weight:600;">● Online — typically replies in under 2 minutes</div></div>
      <div style="margin-left:auto;display:flex;gap:7px;"><a href="mailto:{S_EMAIL}" class="btn bo bsm">📧 Email</a><a href="tel:{S_PHONE}" class="btn bo bsm">📞 Call</a></div>
    </div>
    <div class="chat-wrap" style="border:none;border-radius:0;">
      <div class="chat-msgs" id="msgs">
        <div class="cmsg sup"><div>👋 Hi {name}! I'm your Moderation Squad support agent. I can help with:<br><br>• Pay rates &amp; earnings<br>• Job applications<br>• Profile verification<br>• Training courses<br>• Schedule &amp; availability<br>• Account questions</div><div class="mt">Now</div></div>
        {hist_h}
      </div>
      <div class="chat-inp">
        <textarea class="cinput" id="ci" rows="2" placeholder="Type your message… (Enter to send, Shift+Enter for new line)" onkeydown="if(event.key==='Enter'&&!event.shiftKey){{event.preventDefault();sendMsg();}}"></textarea>
        <button class="btn bp" onclick="sendMsg()" style="min-width:52px;align-self:stretch;">
          <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
        </button>
      </div>
    </div>
  </div>
  <div class="card fi fi3" style="margin-top:14px;">
    <h2 style="font-size:13px;font-weight:700;margin-bottom:12px;color:var(--text);">⚡ Quick Questions</h2>
    <div style="display:flex;gap:7px;flex-wrap:wrap;">
      <button class="btn bo bsm" onclick="quick('What is my current pay rate?')">💰 Pay rate?</button>
      <button class="btn bo bsm" onclick="quick('How do I apply for a job?')">💼 How to apply?</button>
      <button class="btn bo bsm" onclick="quick('What verification do I still need?')">✅ Verification?</button>
      <button class="btn bo bsm" onclick="quick('When do I get paid?')">📅 Payout dates?</button>
      <button class="btn bo bsm" onclick="quick('How do I level up?')">📈 Level up?</button>
      <button class="btn bo bsm" onclick="quick('Tell me about training courses')">📚 Training?</button>
      <button class="btn bo bsm" onclick="quick('How do I sign out?')">🚪 Sign out?</button>
    </div>
  </div>
</div></div>
<script>
function sendMsg(){{const ci=document.getElementById('ci');const msg=ci.value.trim();if(!msg)return;addMsg(msg,'usr');ci.value='';
  const typing=addMsg('⏳ Support agent is typing...','sup');
  fetch('/chat_msg',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{msg}})}}).then(r=>r.json()).then(d=>{{
    if(d.success){{typing.querySelector('div:first-child').innerHTML=d.reply;typing.querySelector('.mt').textContent=d.time;}}}});}}
function quick(m){{document.getElementById('ci').value=m;sendMsg();}}
function addMsg(text,role){{const c=document.getElementById('msgs');const d=document.createElement('div');d.className='cmsg '+role;
  d.innerHTML='<div>'+text+'</div><div class="mt">'+new Date().toLocaleTimeString([],{{hour:'2-digit',minute:'2-digit'}})+'</div>';
  c.appendChild(d);c.scrollTop=c.scrollHeight;return d;}}
document.getElementById('msgs').scrollTop=99999;
</script></body></html>"""

def support_pg(user):
    faqs=[
        ("How do I get my first job?","Browse the Jobs section and click Apply Now on any open position. You'll get an instant email confirmation with the expected response time (1–3 business days)."),
        ("When do I get paid?","Payouts process every Friday for work completed the prior week. Minimum $10 payout. You must have a payment method set up in Earnings first."),
        ("How do I set up payment?","Go to Earnings in the sidebar and choose from: Direct Deposit (ACH), PayPal, Payoneer, Tipalti, or Paper Check. ACH is recommended for fastest transfers."),
        ("What is a W-9 form?","A W-9 is a US IRS tax form required for independent contractors. Yours has already been processed — no further action needed. Contact support if you have questions."),
        ("How do I level up?","Complete jobs successfully: 6 jobs → Junior (unlocks $10–$12/hr roles), 21 jobs → Senior ($13–$18/hr), 50 jobs → Elite ($18–$22/hr)."),
        ("Can I work part-time?","Yes! Work as few as 8 hours per week as a Newcomer. Set your available days and time slots in My Schedule. Clients match you based on availability."),
        ("How do I change my profile photo?","Go to My Profile and click the ✏️ pencil icon on your avatar. Select a photo from your device — it updates instantly."),
        ("How do I sign out?","Click Sign Out at the bottom of the left sidebar, or use the Sign Out button on your Profile page, or visit /logout directly."),
        ("What payment methods are available?","Direct Deposit (ACH), PayPal, Payoneer, Tipalti, and Paper Check. All available in the Earnings section."),
        ("How do training courses work?","Click Training in the sidebar. Select any free Beginner course and click Start Course. Lessons open interactively — read each lesson, use Next Lesson to advance, and complete the quiz at the end to earn your certificate."),
    ]
    fh="".join(f'<div class="faq-item"><div class="faq-q" onclick="tf(this)"><span>{q}</span><span style="color:var(--red);font-size:18px;font-weight:300;transition:transform 0.25s;">+</span></div><div class="faq-a">{a}</div></div>' for q,a in faqs)
    soc_h="".join(f'<a href="{u}" target="_blank" class="btn bo bsm" style="font-size:11px;">{n}</a>' for u,n,_ in SOCIAL)
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Help & Support — Moderation Squad</title>{CSS}</head><body>
<div class="layout">{sidebar_html("support",user)}<div class="mc">
  <div class="topbar fi"><div><h1>Help & Support</h1><p>We're here to help you succeed</p></div></div>
  <div class="g3 fi fi1" style="margin-bottom:18px;">
    <div class="card" style="text-align:center;padding:26px;"><div style="font-size:34px;margin-bottom:12px;">📧</div><h3 style="font-size:15px;font-weight:700;margin-bottom:5px;color:var(--text);">Email</h3><p style="font-size:11px;color:var(--muted);margin-bottom:13px;">24–48hr response time</p><a href="mailto:{S_EMAIL}" class="btn bp bsm" style="font-size:11px;">{S_EMAIL}</a></div>
    <div class="card" style="text-align:center;padding:26px;"><div style="font-size:34px;margin-bottom:12px;">📞</div><h3 style="font-size:15px;font-weight:700;margin-bottom:5px;color:var(--text);">Phone</h3><p style="font-size:11px;color:var(--muted);margin-bottom:13px;">Mon–Fri 9AM–6PM EST</p><a href="tel:{S_PHONE}" class="btn bo bsm" style="font-size:11px;">{S_PHONE}</a></div>
    <div class="card" style="text-align:center;padding:26px;"><div style="font-size:34px;margin-bottom:12px;">💬</div><h3 style="font-size:15px;font-weight:700;margin-bottom:5px;color:var(--text);">Live Chat</h3><p style="font-size:11px;color:var(--muted);margin-bottom:13px;">Instant responses</p><a href="/livechat" class="btn bp bsm" style="font-size:11px;">Start Chat →</a></div>
  </div>
  <div class="card fi fi2" style="margin-bottom:16px;"><div class="sh"><h2>Frequently Asked Questions</h2><span style="font-size:11px;color:var(--muted);">{len(faqs)} questions</span></div>{fh}</div>
  <div class="card fi fi3" style="margin-bottom:14px;border-color:var(--red-mid);background:var(--red-light);">
    <h2 style="font-size:14px;font-weight:700;margin-bottom:5px;color:var(--text);">📬 Send a Message</h2>
    <p style="font-size:11px;color:var(--muted);margin-bottom:14px;">Can't find what you need? We'll respond within 24–48 hours.</p>
    <div class="form-group"><label class="form-label">Subject</label><input type="text" class="form-input" placeholder="What do you need help with?"></div>
    <div class="form-group"><label class="form-label">Message</label><textarea class="form-input" rows="4" placeholder="Describe your issue in detail..."></textarea></div>
    <button class="btn bp bsm" onclick="showT()">Send Message →</button>
  </div>
  <div class="card fi fi4">
    <h2 style="font-size:13px;font-weight:700;margin-bottom:12px;color:var(--text);">🔗 Follow ModSquad</h2>
    <div style="display:flex;gap:8px;flex-wrap:wrap;">{soc_h}</div>
  </div>
</div></div>
<div class="toast" id="toast"></div>
<script>
function tf(el){{const c=el.nextElementSibling,ic=el.querySelector('span:last-child'),op=c.style.display==='block';c.style.display=op?'none':'block';ic.textContent=op?'+':'−';}}
function showT(){{const t=document.getElementById('toast');t.textContent='✅ Message sent! We will reply within 24–48 hours.';t.className='toast ts show';setTimeout(()=>t.classList.remove('show'),4000);}}
</script></body></html>"""


# ── START (Render + gunicorn compatible) ──────────────────────────
# setup_routes() called at module level so gunicorn can find the app
setup_routes()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
