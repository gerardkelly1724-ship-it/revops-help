# RevOps Help (web version)

A password-protected chat page that answers RevOps questions from your knowledge docs and looks up records in your **test** HubSpot portal, read-only.

## How it works

```
Browser (chat page)
   │  question + conversation so far
   ▼
app.py ──────────► assistant.py ──────────► Claude API
(login, web pages)  (prompt + loop)  ◄──────  "I need to look something up"
                         │
                         ▼
                  hubspot_tools.py ─────────► HubSpot API (read-only)
```

| File | What it does |
|---|---|
| `app.py` | The web server. Login page, chat page, and the `/api/chat` endpoint |
| `assistant.py` | Builds the prompt and runs the back-and-forth with Claude |
| `hubspot_tools.py` | The four HubSpot lookups Claude can use, and the read-only guard |
| `prompts/instructions.md` | How the assistant behaves (same as the project instructions) |
| `prompts/diagnose-lead-routing.md` | The routing checklist (same as the skill) |
| `knowledge/` | The seven docs |
| `templates/` | The login and chat pages |
| `tests/` | Offline tests with fake Claude and fake HubSpot |

To change what it knows, edit a file in `knowledge/`. To change how it behaves, edit `prompts/instructions.md`. No code changes needed for either.

## Setup

Takes about 30 minutes. You'll end up with four secrets. Keep them in a password manager, never in the code.

### 1. GitHub (where the code lives)

1. Create an account at github.com.
2. Click **New repository**. Name it `revops-help`, set it to **Private**, and create it.
3. On the empty repo page, click **uploading an existing file**. Drag in everything from this folder (the files and the `knowledge`, `prompts`, `templates` and `tests` folders), then click **Commit changes**.

On a Mac, files starting with a dot (`.gitignore`, `.env.example`) are hidden and may not upload. That's fine for now.

### 2. Anthropic Console (the API key)

This is separate from your Claude subscription. You pay per use.

1. Sign up at console.anthropic.com.
2. Add some credit under **Billing**. A few pounds is plenty for testing.
3. Set a monthly spend limit while you're there.
4. Go to **API keys**, create one called `revops-help`, and copy it. It starts `sk-ant-`. You only see it once.

### 3. HubSpot private app (read-only access to the test portal)

In your **test portal only**:

1. Go to **Settings > Integrations > Private Apps** and create one called `RevOps Help`. (Newer portals may list this under **Development > Legacy apps**.)
2. On the **Scopes** tab, tick read scopes only:
   - `crm.objects.contacts.read`
   - `crm.objects.companies.read`
   - `crm.objects.deals.read`
   - `crm.objects.owners.read`
3. Create the app and copy the access token. It starts `pat-`.

Read-only is now enforced by HubSpot itself. Even if the code tried to change something, HubSpot would refuse.

If call lookups fail later, the error will name the missing scope. Add it and update the token.

### 4. Render (hosting)

1. Sign up at render.com using **Sign in with GitHub**.
2. Click **New > Web Service** and pick the `revops-help` repo.
3. Fill in:
   - **Runtime:** Python 3
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app --timeout 120`
   - **Instance type:** Free
4. Under **Environment Variables**, add:

| Key | Value |
|---|---|
| `ANTHROPIC_API_KEY` | your `sk-ant-` key |
| `HUBSPOT_TOKEN` | your `pat-` token |
| `HUBSPOT_PORTAL_ID` | `148312519` |
| `HUBSPOT_APP_DOMAIN` | `app-eu1.hubspot.com` |
| `APP_PASSWORD` | a long password for the site |
| `SECRET_KEY` | any long random string (mash the keyboard for 40 characters) |

5. Click **Deploy**. After a few minutes you'll get a URL like `revops-help.onrender.com`.

The free tier sleeps after 15 minutes of no traffic and takes about a minute to wake. The first question after a break will be slow.

### 5. Test it

Sign in, then work through `test-set.csv` from the starter kit. Open the "Looked up" panel under each answer to see what it checked in HubSpot.

### 6. Your own domain (later)

1. Buy a domain from any registrar (Cloudflare, Namecheap, Google Domains' successor, etc.).
2. In Render, open the service, go to **Settings > Custom Domains**, and add something like `revops.yourdomain.com`.
3. Render shows a DNS record to add. Add it at your registrar. HTTPS is set up automatically.

## Making changes

Edit a file on GitHub (pencil icon), commit, and Render redeploys automatically within a couple of minutes.

## Costs

- Render free tier: £0
- Claude API: pay per question. A typical lookup question uses a few thousand tokens. Check usage in the Console after your first session to get a real number.
- Domain: roughly £5 to £15 a year

## Safety notes

- Only ever connect the test portal. Real company data needs company approval and a proper login, not a shared password.
- If a key leaks, delete it in the Console or HubSpot and create a new one.
- The password is shared, so anyone who has it can use your API credit. Keep the spend limit on.

## Running the tests

```
pip install -r requirements.txt pytest
python -m pytest -q
```

They use a fake Claude and fake HubSpot, so they need no keys. They check the tool loop works, the login works, and that write requests to HubSpot are blocked.

## What to learn from each file

Read them in this order:

1. **`app.py`**. A web server is just functions that run when someone visits a URL. `@app.route("/")` means "run this when someone opens the home page".
2. **`assistant.py`**. The core idea of every AI agent: call the model, and if it asks for a tool, run it and call again. That loop is about 25 lines.
3. **`hubspot_tools.py`**. Tools are normal Python functions plus a description. Claude never touches HubSpot directly. It only asks, and your code decides what actually runs.

Next upgrades, roughly in order of difficulty: show answers as they're typed (streaming), log every question to spot gaps in the docs, and replace "send all docs every time" with retrieval (RAG) once the docs get big.
