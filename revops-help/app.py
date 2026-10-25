"""
The web server. Three jobs:
  - show a login page and check the password
  - show the chat page
  - receive questions from the chat page and return Claude's answers
"""

import hmac
import os
from functools import wraps

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

import assistant

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]  # signs the login cookie
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
if os.environ.get("RENDER"):  # on the live site, only send the cookie over https
    app.config["SESSION_COOKIE_SECURE"] = True

APP_PASSWORD = os.environ["APP_PASSWORD"]
MAX_HISTORY = 20  # only send the last 20 messages, to keep cost down


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Not logged in"}), 401
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        # compare_digest avoids leaking the password through timing differences
        if hmac.compare_digest(request.form.get("password", ""), APP_PASSWORD):
            session["logged_in"] = True
            return redirect(url_for("chat"))
        error = "That's not the password."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def chat():
    return render_template("chat.html")


@app.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    history = (request.get_json(silent=True) or {}).get("messages", [])
    history = [
        {"role": m["role"], "content": str(m["content"])[:4000]}
        for m in history
        if m.get("role") in ("user", "assistant") and m.get("content")
    ][-MAX_HISTORY:]
    if not history or history[-1]["role"] != "user":
        return jsonify({"error": "No question received"}), 400

    try:
        reply, tools_used = assistant.answer(history)
    except Exception as e:  # noqa: BLE001
        app.logger.exception("Chat failed")
        return jsonify({"error": f"Something went wrong: {type(e).__name__}"}), 500
    return jsonify({"reply": reply, "tools_used": tools_used})


@app.route("/health")
def health():
    return "ok"


if __name__ == "__main__":
    app.run(debug=True, port=5000)
