# import json
# from typing import Optional
# from openai import AsyncOpenAI
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select

# from app.core.config import settings
# from app.models.doctor import Doctor
# from app.models.user import User
# from app.models.appointment import AppointmentStatus
# from app.services.queue_service import QueueService
# from app.db.session import redis_client


# SYMPTOM_MAP = {
#     "fever": ["General Physician", "Pediatrician"],
#     "cold": ["General Physician"],
#     "cough": ["General Physician", "Pulmonologist"],
#     "chest": ["Cardiologist"],
#     "heart": ["Cardiologist"],
#     "skin": ["Dermatologist"],
#     "rash": ["Dermatologist"],
#     "acne": ["Dermatologist"],
#     "bone": ["Orthopedic"],
#     "joint": ["Orthopedic"],
#     "knee": ["Orthopedic"],
#     "back": ["Orthopedic"],
#     "headache": ["Neurologist", "General Physician"],
#     "migraine": ["Neurologist"],
#     "child": ["Pediatrician"],
#     "baby": ["Pediatrician"],
#     "stomach": ["General Physician"],
#     "eye": ["Ophthalmologist"],
#     "ear": ["ENT Specialist"],
#     "throat": ["ENT Specialist"],
#     "dental": ["Dentist"],
#     "tooth": ["Dentist"],
#     "anxiety": ["Psychiatrist"],
#     "depression": ["Psychiatrist"],
#     "diabetes": ["General Physician", "Endocrinologist"],
#     "sugar": ["General Physician"],
#     "blood pressure": ["Cardiologist", "General Physician"],
# }

# SYSTEM_PROMPT = """You are MediBot, a smart medical appointment assistant for MediQueue clinic.

# You have access to three actions. When you need to use one, output ONLY a raw JSON block
# (no markdown, no extra text) on its own line using this exact format:

#   {"action": "search_doctors", "query": "<symptom or specialization>"}
#   {"action": "get_doctor_details", "doctor_id": <integer>}
#   {"action": "book_appointment", "doctor_id": <integer>, "symptoms": "<patient symptoms>"}

# After receiving the tool result (prefixed with TOOL_RESULT:), continue the conversation normally.

# Your job:
# 1. Listen to patient symptoms and call search_doctors to find the right doctor
# 2. Show doctor options clearly: "Dr. Name (Specialization) — ₹Fee | Queue: N people | ~X min wait"
# 3. Ask for confirmation before booking — NEVER call book_appointment without explicit yes/confirm
# 4. After booking, share the token number and estimated wait time

# Rules:
# - Be warm, concise, professional
# - Show max 3 doctor options
# - If no match found, suggest General Physician
# - Never invent doctor details — only use data from TOOL_RESULT
# - Output the JSON action on its own line with no surrounding text"""


# class ChatbotService:
#     def __init__(self, db: AsyncSession, patient_id: int):
#         self.db = db
#         self.patient_id = patient_id
#         self.queue_service = QueueService(db, redis_client)

#         # ── OpenAI-compatible client pointed at NVIDIA's endpoint ──
#         self.client = AsyncOpenAI(
#             base_url=settings.NVIDIA_API_URL,   # e.g. "https://integrate.api.nvidia.com/v1"
#             api_key=settings.NVIDIA_API_KEY,
#         )

#     # ------------------------------------------------------------------ #
#     #  Tool implementations                                                #
#     # ------------------------------------------------------------------ #

#     async def _search_doctors(self, query: str) -> dict:
#         q = query.lower()
#         target_specs = []
#         for kw, specs in SYMPTOM_MAP.items():
#             if kw in q:
#                 target_specs.extend(specs)

#         result = await self.db.execute(
#             select(Doctor, User)
#             .join(User, Doctor.user_id == User.id)
#             .where(Doctor.is_available == True)
#         )
#         rows = result.all()

#         matched = []
#         for doctor, user in rows:
#             score = 0
#             spec_l = doctor.specialization.lower()
#             if target_specs:
#                 for ts in target_specs:
#                     if ts.lower() in spec_l:
#                         score += 10
#             if q in spec_l:
#                 score += 5
#             if q in user.full_name.lower():
#                 score += 3

#             if score > 0 or not target_specs:
#                 ql = await self.queue_service.get_queue_length(doctor.id)
#                 matched.append({
#                     "id": doctor.id,
#                     "name": f"Dr. {user.full_name}",
#                     "specialization": doctor.specialization,
#                     "qualification": doctor.qualification,
#                     "experience_years": doctor.experience_years,
#                     "fee": doctor.consultation_fee,
#                     "avg_visit_minutes": doctor.avg_consultation_minutes,
#                     "queue_length": ql,
#                     "estimated_wait_minutes": round(ql * doctor.avg_consultation_minutes),
#                     "available_from": doctor.available_from,
#                     "available_to": doctor.available_to,
#                     "rating": doctor.rating,
#                     "score": score,
#                 })

#         matched.sort(key=lambda x: (-x["score"], x["queue_length"]))

#         if not matched:
#             fallback = await self.db.execute(
#                 select(Doctor, User)
#                 .join(User, Doctor.user_id == User.id)
#                 .where(Doctor.is_available == True)
#             )
#             for doc, usr in (fallback.all())[:3]:
#                 ql = await self.queue_service.get_queue_length(doc.id)
#                 matched.append({
#                     "id": doc.id,
#                     "name": f"Dr. {usr.full_name}",
#                     "specialization": doc.specialization,
#                     "qualification": doc.qualification,
#                     "experience_years": doc.experience_years,
#                     "fee": doc.consultation_fee,
#                     "avg_visit_minutes": doc.avg_consultation_minutes,
#                     "queue_length": ql,
#                     "estimated_wait_minutes": round(ql * doc.avg_consultation_minutes),
#                     "available_from": doc.available_from,
#                     "available_to": doc.available_to,
#                     "rating": doc.rating,
#                     "score": 0,
#                 })

#         return {"doctors": matched[:3], "total_found": len(matched)}

#     async def _get_doctor_details(self, doctor_id: int) -> dict:
#         result = await self.db.execute(
#             select(Doctor, User)
#             .join(User, Doctor.user_id == User.id)
#             .where(Doctor.id == doctor_id)
#         )
#         row = result.first()
#         if not row:
#             return {"error": "Doctor not found"}
#         doctor, user = row
#         ql = await self.queue_service.get_queue_length(doctor.id)
#         return {
#             "id": doctor.id,
#             "name": f"Dr. {user.full_name}",
#             "specialization": doctor.specialization,
#             "fee": doctor.consultation_fee,
#             "queue_length": ql,
#             "estimated_wait_minutes": round(ql * doctor.avg_consultation_minutes),
#             "is_available": doctor.is_available,
#         }

#     async def _book_appointment(self, doctor_id: int, symptoms: str) -> dict:
#         from app.services.appointment_service import AppointmentService
#         from app.schemas.appointment import AppointmentCreate
#         try:
#             svc = AppointmentService(self.db, redis_client)
#             appt = await svc.create_appointment(
#                 patient_id=self.patient_id,
#                 data=AppointmentCreate(doctor_id=doctor_id, symptoms=symptoms),
#             )
#             result = await self.db.execute(
#                 select(Doctor, User)
#                 .join(User, Doctor.user_id == User.id)
#                 .where(Doctor.id == doctor_id)
#             )
#             row = result.first()
#             doctor_name = f"Dr. {row[1].full_name}" if row else "the doctor"
#             return {
#                 "success": True,
#                 "appointment_id": appt.id,
#                 "token_number": appt.token_number,
#                 "queue_position": appt.queue_position,
#                 "doctor_name": doctor_name,
#                 "status": appt.status,
#             }
#         except Exception as e:
#             return {"success": False, "error": str(e)}


#     # ------------------------------------------------------------------ #
#     #  Streaming call — no tool_choice, plain text response               #
#     # ------------------------------------------------------------------ #

#     async def _call_model_streaming(self, messages: list) -> str:
#         """
#         Calls the model with streaming and returns the fully assembled reply text.
#         No tools/tool_choice are passed — the model expresses actions as JSON lines.
#         """
#         stream = await self.client.chat.completions.create(
#             model=settings.NVIDIA_MODEL,
#             messages=messages,
#             max_tokens=1024,
#             temperature=0.7,
#             top_p=0.95,
#             stream=True,
#         )

#         reply_text = ""
#         async for chunk in stream:
#             if not getattr(chunk, "choices", None):
#                 continue
#             content = chunk.choices[0].delta.content
#             if content:
#                 reply_text += content

#         return reply_text

#     # ------------------------------------------------------------------ #
#     #  Parse a JSON action line from the model's reply                     #
#     # ------------------------------------------------------------------ #

#     def _extract_action(self, text: str) -> Optional[dict]:
#         """
#         Scans the reply line-by-line for a JSON object that contains an 'action' key.
#         Returns the parsed dict if found, else None.
#         """
#         for line in text.splitlines():
#             line = line.strip()
#             if line.startswith("{") and "action" in line:
#                 try:
#                     data = json.loads(line)
#                     if "action" in data:
#                         return data
#                 except json.JSONDecodeError:
#                     continue
#         return None

#     # ------------------------------------------------------------------ #
#     #  Public chat entry point                                             #
#     # ------------------------------------------------------------------ #

#     async def chat(self, messages: list) -> dict:
#         conversation = [{"role": "system", "content": SYSTEM_PROMPT}]
#         conversation.extend(messages)

#         booked = False
#         print("Conversation start:", conversation)
#         for _ in range(6):
#             reply_text = await self._call_model_streaming(conversation)
#             print("Model reply:", reply_text)
#             action = self._extract_action(reply_text)

#             if action:
#                 # Append assistant message (hide the raw JSON from the user)
#                 conversation.append({"role": "assistant", "content": reply_text})

#                 # Dispatch the requested action
#                 action_name = action.get("action", "")
#                 if action_name == "search_doctors":
#                     result = await self._search_doctors(action.get("query", ""))
#                 elif action_name == "get_doctor_details":
#                     result = await self._get_doctor_details(action.get("doctor_id", 0))
#                 elif action_name == "book_appointment":
#                     result = await self._book_appointment(
#                         action.get("doctor_id", 0),
#                         action.get("symptoms", ""),
#                     )
#                     if result.get("success"):
#                         booked = True
#                 else:
#                     result = {"error": "Unknown action"}

#                 # Feed the tool result back as a user message so the model can continue
#                 conversation.append({
#                     "role": "user",
#                     "content": f"TOOL_RESULT: {json.dumps(result)}",
#                 })
#                 continue  # Let the model produce its next reply

#             # No action found → this is the final conversational reply
#             # Strip any stray JSON lines before returning to the user
#             clean_reply = "\n".join(
#                 line for line in reply_text.splitlines()
#                 if not (line.strip().startswith("{") and "action" in line)
#             ).strip() or "I'm sorry, I couldn't process that."

#             return {
#                 "reply": clean_reply,
#                 "action": "appointment_booked" if booked else None,
#                 "action_data": None,
#             }

#         return {
#             "reply": "I'm having trouble processing your request. Please try again.",
#             "action": None,
#             "action_data": None,
#         }
    

import json
import re
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.doctor import Doctor
from app.models.user import User
from app.services.queue_service import QueueService
from app.db.session import redis_client

# ─────────────────────────────────────────────────────────────────────────────
#  Symptom → specialization map
# ─────────────────────────────────────────────────────────────────────────────
SYMPTOM_MAP = {
    "fever":          ["General Physician", "Pediatrician"],
    "cold":           ["General Physician"],
    "cough":          ["General Physician", "Pulmonologist"],
    "chest":          ["Cardiologist"],
    "heart":          ["Cardiologist"],
    "skin":           ["Dermatologist"],
    "rash":           ["Dermatologist"],
    "acne":           ["Dermatologist"],
    "bone":           ["Orthopedic"],
    "joint":          ["Orthopedic"],
    "knee":           ["Orthopedic"],
    "back":           ["Orthopedic"],
    "headache":       ["Neurologist", "General Physician"],
    "migraine":       ["Neurologist"],
    "child":          ["Pediatrician"],
    "baby":           ["Pediatrician"],
    "stomach":        ["General Physician"],
    "eye":            ["Ophthalmologist"],
    "ear":            ["ENT Specialist"],
    "throat":         ["ENT Specialist"],
    "dental":         ["Dentist"],
    "tooth":          ["Dentist"],
    "anxiety":        ["Psychiatrist"],
    "depression":     ["Psychiatrist"],
    "diabetes":       ["General Physician", "Endocrinologist"],
    "sugar":          ["General Physician"],
    "blood pressure": ["Cardiologist", "General Physician"],
}

# ─────────────────────────────────────────────────────────────────────────────
#  System prompt  –  plain-JSON tool protocol (no OpenAI function-calling)
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are MediBot, a smart medical appointment assistant for MediQueue clinic.

You have access to three actions. When you need to use one, output ONLY a raw JSON object
(no markdown, no code fences, no extra text) on its own line:

  {"action": "search_doctors", "query": "<symptom or specialization>"}
  {"action": "get_doctor_details", "doctor_id": <integer>}
  {"action": "book_appointment", "doctor_id": <integer>, "symptoms": "<patient symptoms>"}

After receiving the tool result (prefixed with TOOL_RESULT:), continue the conversation normally.

CRITICAL RULES FOR doctor_id:
- ALWAYS use the exact numeric "id" field returned in TOOL_RESULT — never guess or invent an ID.
- When a patient selects a doctor by name, look up the matching "id" from the most recent
  search_doctors TOOL_RESULT and use that exact integer.
- If you are unsure of the doctor_id, call search_doctors again first.

Your job:
1. Listen to patient symptoms and call search_doctors to find the right doctor.
2. Show doctor options clearly:
   "Dr. Name (Specialization) — ₹Fee | Queue: N people | ~X min wait  [ID: <id>]"
3. Ask for confirmation before booking — NEVER call book_appointment without explicit yes/confirm.
4. After booking, share the token number and estimated wait time.

General rules:
- Be warm, concise, professional.
- Show max 3 doctor options.
- If no match found, suggest General Physician.
- Never invent doctor details — only use data from TOOL_RESULT.
- Output the JSON action on its own line with no surrounding text and no markdown fences."""


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────
_JSON_ACTION_RE = re.compile(r'\{[^{}]*"action"\s*:[^{}]*\}', re.DOTALL)
_FENCE_RE = re.compile(r'```(?:json)?\s*(.*?)\s*```', re.DOTALL)


def _extract_action(text: str) -> dict | None:
    """
    Pull the first action JSON object out of the model reply.
    Handles markdown fences and stray surrounding text gracefully.
    """
    # 1. strip markdown fences if present
    fenced = _FENCE_RE.search(text)
    candidate = fenced.group(1) if fenced else text

    # 2. find a JSON object that contains "action"
    match = _JSON_ACTION_RE.search(candidate)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # 3. try the whole stripped candidate as JSON
    try:
        obj = json.loads(candidate.strip())
        if isinstance(obj, dict) and "action" in obj:
            return obj
    except json.JSONDecodeError:
        pass

    return None


def _text_without_action(text: str) -> str:
    """Remove the raw JSON action line (and any fences) from visible reply text."""
    text = _FENCE_RE.sub("", text)
    text = _JSON_ACTION_RE.sub("", text)
    return text.strip()


# ─────────────────────────────────────────────────────────────────────────────
#  Service
# ─────────────────────────────────────────────────────────────────────────────
class ChatbotService:
    def __init__(self, db: AsyncSession, patient_id: int):
        self.db = db
        self.patient_id = patient_id
        self.queue_service = QueueService(db, redis_client)
        self.client = AsyncOpenAI(
            base_url=settings.NVIDIA_API_URL,
            api_key=settings.NVIDIA_API_KEY,
        )

    # ── DB helpers ────────────────────────────────────────────────────────────

    async def _search_doctors(self, query: str) -> dict:
        q = query.lower()
        target_specs: list[str] = []
        for kw, specs in SYMPTOM_MAP.items():
            if kw in q:
                target_specs.extend(specs)

        result = await self.db.execute(
            select(Doctor, User)
            .join(User, Doctor.user_id == User.id)
            .where(Doctor.is_available == True)
        )
        rows = result.all()

        matched = []
        for doctor, user in rows:
            score = 0
            spec_l = doctor.specialization.lower()
            for ts in target_specs:
                if ts.lower() in spec_l:
                    score += 10
            if q in spec_l:
                score += 5
            if q in user.full_name.lower():
                score += 3

            if score > 0 or not target_specs:
                ql = await self.queue_service.get_queue_length(doctor.id)
                matched.append({
                    "id":                     doctor.id,   # ← real DB id
                    "name":                   f"Dr. {user.full_name}",
                    "specialization":         doctor.specialization,
                    "qualification":          doctor.qualification,
                    "experience_years":       doctor.experience_years,
                    "fee":                    doctor.consultation_fee,
                    "avg_visit_minutes":      doctor.avg_consultation_minutes,
                    "queue_length":           ql,
                    "estimated_wait_minutes": round(ql * doctor.avg_consultation_minutes),
                    "available_from":         doctor.available_from,
                    "available_to":           doctor.available_to,
                    "rating":                 doctor.rating,
                    "score":                  score,
                })

        matched.sort(key=lambda x: (-x["score"], x["queue_length"]))

        # fallback: return any available doctors
        if not matched:
            fallback = await self.db.execute(
                select(Doctor, User)
                .join(User, Doctor.user_id == User.id)
                .where(Doctor.is_available == True)
            )
            for doc, usr in (fallback.all())[:3]:
                ql = await self.queue_service.get_queue_length(doc.id)
                matched.append({
                    "id":                     doc.id,
                    "name":                   f"Dr. {usr.full_name}",
                    "specialization":         doc.specialization,
                    "qualification":          doc.qualification,
                    "experience_years":       doc.experience_years,
                    "fee":                    doc.consultation_fee,
                    "avg_visit_minutes":      doc.avg_consultation_minutes,
                    "queue_length":           ql,
                    "estimated_wait_minutes": round(ql * doc.avg_consultation_minutes),
                    "available_from":         doc.available_from,
                    "available_to":           doc.available_to,
                    "rating":                 doc.rating,
                    "score":                  0,
                })

        top3 = matched[:3]
        return {
            "doctors":     top3,
            "total_found": len(matched),
            # Flat name→id map so the model can look up IDs by doctor name easily
            "id_reference": {d["name"]: d["id"] for d in top3},
        }

    async def _get_doctor_details(self, doctor_id: int) -> dict:
        result = await self.db.execute(
            select(Doctor, User)
            .join(User, Doctor.user_id == User.id)
            .where(Doctor.id == doctor_id)
        )
        row = result.first()
        if not row:
            return {"error": f"Doctor with id {doctor_id} not found"}
        doctor, user = row
        ql = await self.queue_service.get_queue_length(doctor.id)
        return {
            "id":                     doctor.id,
            "name":                   f"Dr. {user.full_name}",
            "specialization":         doctor.specialization,
            "fee":                    doctor.consultation_fee,
            "queue_length":           ql,
            "estimated_wait_minutes": round(ql * doctor.avg_consultation_minutes),
            "is_available":           doctor.is_available,
        }

    async def _book_appointment(self, doctor_id: int, symptoms: str) -> dict:
        from app.services.appointment_service import AppointmentService
        from app.schemas.appointment import AppointmentCreate
        try:
            svc  = AppointmentService(self.db, redis_client)
            appt = await svc.create_appointment(
                patient_id=self.patient_id,
                data=AppointmentCreate(doctor_id=doctor_id, symptoms=symptoms),
            )
            result = await self.db.execute(
                select(Doctor, User)
                .join(User, Doctor.user_id == User.id)
                .where(Doctor.id == doctor_id)
            )
            row         = result.first()
            doctor_name = f"Dr. {row[1].full_name}" if row else "the doctor"
            return {
                "success":        True,
                "appointment_id": appt.id,
                "token_number":   appt.token_number,
                "queue_position": appt.queue_position,
                "doctor_name":    doctor_name,
                "status":         appt.status,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _dispatch_tool(self, action: dict) -> tuple[str, bool]:
        """Execute the tool described by `action`.
        Returns (tool_result_json_string, appointment_was_booked)."""
        name   = action.get("action", "")
        booked = False

        if name == "search_doctors":
            result = await self._search_doctors(action.get("query", ""))
            return json.dumps(result), False

        if name == "get_doctor_details":
            result = await self._get_doctor_details(int(action["doctor_id"]))
            return json.dumps(result), False

        if name == "book_appointment":
            result = await self._book_appointment(
                int(action["doctor_id"]), action.get("symptoms", "")
            )
            booked = result.get("success", False)
            return json.dumps(result), booked

        return json.dumps({"error": f"Unknown action: {name}"}), False

    # ── LLM call ──────────────────────────────────────────────────────────────

    async def _call_model(self, messages: list) -> str:
        """Call the model with streaming and return the fully assembled reply text."""
        stream = await self.client.chat.completions.create(
            model=settings.NVIDIA_MODEL,
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
            top_p=0.95,
            stream=True,
        )
        text = ""
        async for chunk in stream:
            if not getattr(chunk, "choices", None):
                continue
            delta = chunk.choices[0].delta
            if delta.content:
                text += delta.content
        return text

    # ── Public entry point ────────────────────────────────────────────────────

    async def chat(self, messages: list) -> dict:
        """
        Run the plain-JSON tool-use agentic loop.
        `messages` is the full conversation history (without the system prompt).
        """
        conversation = [{"role": "system", "content": SYSTEM_PROMPT}]
        conversation.extend(messages)

        booked = False

        for _ in range(8):                          # max 8 LLM turns per request
            raw_reply = await self._call_model(conversation)
            action    = _extract_action(raw_reply)

            if action:
                # ── tool call detected ──
                tool_result, did_book = await self._dispatch_tool(action)
                if did_book:
                    booked = True

                # Append the model's turn (contains the action JSON)
                conversation.append({"role": "assistant", "content": raw_reply})

                # Append tool result — remind model to use real IDs
                tool_msg = (
                    f"TOOL_RESULT: {tool_result}\n\n"
                    "IMPORTANT: Use the exact 'id' integer values shown above. "
                    "Do NOT use any other number as doctor_id."
                )
                conversation.append({"role": "user", "content": tool_msg})
                continue

            # ── no action → final human-readable reply ──
            visible_reply = _text_without_action(raw_reply) or "I'm sorry, I couldn't process that."
            return {
                "reply":       visible_reply,
                "action":      "appointment_booked" if booked else None,
                "action_data": None,
            }

        return {
            "reply":       "I'm having trouble processing your request. Please try again.",
            "action":      None,
            "action_data": None,
        }