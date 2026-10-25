"""
Read-only HubSpot tools the assistant can call.

Two layers keep this read-only:
  1. The HubSpot private app token only has read scopes, so HubSpot itself
     refuses any write.
  2. The _request() function below only allows GET requests and a short list
     of POST endpoints that search or read. Even if someone added a write
     tool by mistake, it would be blocked here.
"""

import json
import os
import re

import requests

API = "https://api.hubapi.com"
TOKEN = os.environ.get("HUBSPOT_TOKEN", "")
PORTAL_ID = os.environ.get("HUBSPOT_PORTAL_ID", "")
APP_DOMAIN = os.environ.get("HUBSPOT_APP_DOMAIN", "app.hubspot.com")

# Which properties to fetch for each kind of record. Add to these lists if
# the assistant needs to see more.
PROPERTIES = {
    "contacts": [
        "firstname", "lastname", "email", "jobtitle", "lifecyclestage",
        "hs_lead_status", "hubspot_owner_id", "createdate",
        "hs_analytics_source", "hs_analytics_source_data_1",
        "recent_conversion_event_name", "recent_conversion_date",
        "num_conversion_events", "recontact_date",
    ],
    "companies": [
        "name", "domain", "website", "hubspot_owner_id", "institution_type",
        "student_numbers", "revops_region", "lifecyclestage", "createdate",
        "num_associated_contacts", "num_associated_deals",
    ],
    "deals": [
        "dealname", "pipeline", "dealstage", "amount", "closedate",
        "dealtype", "hubspot_owner_id", "createdate",
    ],
    "calls": [
        "hs_call_title", "hs_call_body", "hs_timestamp", "hs_call_direction",
        "hs_call_status", "hs_call_duration",
    ],
}

# HubSpot's internal type IDs, used to build links to records
TYPE_IDS = {"contacts": "0-1", "companies": "0-2", "deals": "0-3"}

# The only POST endpoints allowed. Both read data, neither changes it.
ALLOWED_POSTS = [
    re.compile(r"^/crm/v3/objects/\w+/search$"),
    re.compile(r"^/crm/v3/objects/\w+/batch/read$"),
]


class ReadOnlyError(Exception):
    pass


def _request(method, path, **kwargs):
    """Every call to HubSpot goes through here."""
    if method == "POST" and not any(p.match(path) for p in ALLOWED_POSTS):
        raise ReadOnlyError(f"Blocked: {method} {path} is not a read request")
    if method not in ("GET", "POST"):
        raise ReadOnlyError(f"Blocked: {method} requests are not allowed")
    resp = requests.request(
        method,
        API + path,
        headers={"Authorization": f"Bearer {TOKEN}"},
        timeout=20,
        **kwargs,
    )
    resp.raise_for_status()
    return resp.json()


def _url(object_type, record_id):
    if not PORTAL_ID or object_type not in TYPE_IDS:
        return None
    return f"https://{APP_DOMAIN}/contacts/{PORTAL_ID}/record/{TYPE_IDS[object_type]}/{record_id}"


def _clean(props):
    """Drop empty values and HubSpot's internal timestamps to keep results short."""
    skip = {"hs_object_id", "hs_lastmodifieddate", "lastmodifieddate"}
    return {k: v for k, v in props.items() if v not in (None, "") and k not in skip}


# ---------------------------------------------------------------------------
# The tools themselves
# ---------------------------------------------------------------------------

def search_records(object_type, query):
    data = _request(
        "POST",
        f"/crm/v3/objects/{object_type}/search",
        json={"query": query, "properties": PROPERTIES[object_type], "limit": 10},
    )
    return {
        "total": data.get("total", 0),
        "results": [
            {"id": r["id"], "url": _url(object_type, r["id"]), **_clean(r["properties"])}
            for r in data.get("results", [])
        ],
    }


def get_record(object_type, record_id, owner_history=False):
    assoc = {
        "contacts": "companies,deals,calls",
        "companies": "contacts,deals",
        "deals": "contacts,companies",
    }[object_type]
    params = {
        "properties": ",".join(PROPERTIES[object_type]),
        "associations": assoc,
    }
    if owner_history:
        params["propertiesWithHistory"] = "hubspot_owner_id"
    data = _request("GET", f"/crm/v3/objects/{object_type}/{record_id}", params=params)

    result = {
        "id": data["id"],
        "url": _url(object_type, data["id"]),
        "properties": _clean(data.get("properties", {})),
        "associations": {
            name: [a["id"] for a in group.get("results", [])]
            for name, group in (data.get("associations") or {}).items()
        },
    }
    if owner_history:
        result["owner_history"] = [
            {"value": h.get("value"), "set_at": h.get("timestamp"), "source": h.get("sourceType")}
            for h in (data.get("propertiesWithHistory") or {}).get("hubspot_owner_id", [])
        ]
    return result


def get_calls(call_ids):
    if not call_ids:
        return {"results": []}
    data = _request(
        "POST",
        "/crm/v3/objects/calls/batch/read",
        json={"inputs": [{"id": str(i)} for i in call_ids[:20]], "properties": PROPERTIES["calls"]},
    )
    return {"results": [{"id": r["id"], **_clean(r["properties"])} for r in data.get("results", [])]}


def list_owners():
    active = _request("GET", "/crm/v3/owners", params={"archived": "false", "limit": 100})
    inactive = _request("GET", "/crm/v3/owners", params={"archived": "true", "limit": 100})

    def fmt(o, is_active):
        name = f"{o.get('firstName', '')} {o.get('lastName', '')}".strip()
        return {"owner_id": o["id"], "name": name or o.get("email"), "active": is_active}

    return {
        "owners": [fmt(o, True) for o in active.get("results", [])]
        + [fmt(o, False) for o in inactive.get("results", [])]
    }


# ---------------------------------------------------------------------------
# Descriptions Claude reads to decide which tool to use
# ---------------------------------------------------------------------------

OBJECT_TYPE = {"type": "string", "enum": ["contacts", "companies", "deals"]}

TOOLS = [
    {
        "name": "search_records",
        "description": "Search HubSpot contacts, companies or deals by name, email or domain. Returns up to 10 matches with key properties and a link.",
        "input_schema": {
            "type": "object",
            "properties": {
                "object_type": OBJECT_TYPE,
                "query": {"type": "string", "description": "Name, email, domain or deal name to search for"},
            },
            "required": ["object_type", "query"],
        },
    },
    {
        "name": "get_record",
        "description": "Get one record by ID with its key properties and the IDs of associated contacts, companies, deals and calls. Set owner_history to see when and how the owner was set.",
        "input_schema": {
            "type": "object",
            "properties": {
                "object_type": OBJECT_TYPE,
                "record_id": {"type": "string"},
                "owner_history": {"type": "boolean", "default": False},
            },
            "required": ["object_type", "record_id"],
        },
    },
    {
        "name": "get_calls",
        "description": "Read logged calls by ID (get the IDs from a contact's associations). Returns title, notes, date and outcome.",
        "input_schema": {
            "type": "object",
            "properties": {"call_ids": {"type": "array", "items": {"type": "string"}}},
            "required": ["call_ids"],
        },
    },
    {
        "name": "list_owners",
        "description": "List all HubSpot owners with their owner_id and whether they are active or deactivated. Use this to turn an owner ID into a name.",
        "input_schema": {"type": "object", "properties": {}},
    },
]

FUNCTIONS = {
    "search_records": search_records,
    "get_record": get_record,
    "get_calls": get_calls,
    "list_owners": list_owners,
}


def run_tool(name, args):
    """Run a tool and always return text, including when something goes wrong,
    so Claude can explain the problem instead of the app crashing."""
    try:
        result = FUNCTIONS[name](**args)
        text = json.dumps(result, default=str)
    except requests.HTTPError as e:
        text = json.dumps({"error": f"HubSpot returned {e.response.status_code}", "detail": e.response.text[:500]})
    except Exception as e:  # noqa: BLE001
        text = json.dumps({"error": str(e)})
    return text[:12000]
