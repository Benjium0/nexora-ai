from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from openai import OpenAI

client = OpenAI()  # uses OPENAI_API_KEY from env

STATE = {}  # per-player conversation memory (previous_response_id)

SYSTEM = (
    "You are Billy, a Roblox player in 2018.\n"
    "Rules:\n"
    "- reply in ONE short message (3–12 words)\n"
    "- casual roblox chat, lowercase\n"
    "- no emojis\n"
    "- never mention ai, openai, models, or years\n"
    "- if asked 'are you ai', say 'idk lol'\n"
    "- remember what you said earlier and stay consistent\n"
)

def clamp(text):
    t = (text or "").strip().replace("\n", " ")
    t = " ".join(t.split())
    if not t:
        return "idk"
    return t[:120]

class Handler(BaseHTTPRequestHandler):
    def _send(self, obj, code=200):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._send({"status": "ok"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8") if length else ""

        try:
            data = json.loads(body)
        except:
            return self._send({"reply": "bad json"}, 400)

        player = str(data.get("player", "player"))[:40]
        msg = str(data.get("message", ""))[:400]
        membership = str(data.get("membership", "None"))
        distance = str(data.get("distance", ""))
        look = data.get("look", {})

        prev_id = STATE.get(player)

        prompt = (
            f"player info:\n"
            f"- name: {player}\n"
            f"- membership: {membership}\n"
            f"- distance: {distance} studs\n"
            f"- look: {look}\n\n"
            f"player said: {msg}"
        )

        print(f"[IN] {player}: {msg}")

        try:
            resp = client.responses.create(
                model="gpt-4o-mini",
                input=[
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                previous_response_id=prev_id,
                store=True,
                max_output_tokens=60
            )

            STATE[player] = resp.id
            reply = clamp(resp.output_text)

            print(f"[OUT] {reply}")
            return self._send({"reply": reply})

        except Exception as e:
            print("[OPENAI ERROR]", repr(e))
            return self._send({"reply": "idk (server error)"})

print("AI server running on http://0.0.0.0:8080")
HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
