import os
from typing import Any, Dict
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from openai import OpenAI

app = FastAPI()
client = OpenAI()

STATE: Dict[str, str] = {}

SYSTEM = (
    "You are Billy, a Roblox player in 2018.\n"
    "Rules:\n"
    "- reply in ONE short message (3–12 words)\n"
    "- casual roblox chat, lowercase\n"
    "- no emojis\n"
    "- never mention ai/openai/models/years\n"
    "- if asked 'are you ai', say 'idk lol'\n"
    "- remember what you said earlier and stay consistent\n"
)

def clamp(text: str) -> str:
    t = (text or "").strip().replace("\n", " ")
    t = " ".join(t.split())
    return (t[:120] if t else "idk")

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/")
async def chat(req: Request):
    try:
        data: Dict[str, Any] = await req.json()
    except Exception:
        return JSONResponse({"reply": "bad json"}, status_code=400)

    player = str(data.get("player", "player"))[:40]
    msg = str(data.get("message", ""))[:400]
    membership = str(data.get("membership", "None"))[:40]
    distance = str(data.get("distance", ""))[:10]
    look = data.get("look", {})
    if not isinstance(look, dict):
        look = {}

    prev_id = STATE.get(player)

    prompt = (
        f"player info:\n"
        f"- name: {player}\n"
        f"- membership: {membership}\n"
        f"- distance: {distance} studs\n"
        f"- look: {look}\n\n"
        f"player said: {msg}"
    )

    try:
        resp = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt},
            ],
            previous_response_id=prev_id,
            store=True,
            max_output_tokens=60,
        )

        STATE[player] = resp.id
        return {"reply": clamp(resp.output_text)}

    except Exception as e:
        print("[OPENAI ERROR]", repr(e))
        return {"reply": "idk (openai error)"}

if __name__ == "__main__":
    # For local testing only (Railway uses Procfile command)
    import uvicorn
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
