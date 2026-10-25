# Lifecycle and lead status

*Placeholder content. Anything in [square brackets] needs confirming against your real setup.*

## Lifecycle stages

Lifecycle stage tells you where a contact or company is in the overall relationship. It only moves forward automatically. Moving it backwards needs [Gerard].

| Stage | Meaning at [Company] | Who sets it |
|---|---|---|
| Subscriber | Signed up for content or the newsletter only | Automatic (form) |
| Lead | We have contact details and some interest, not yet qualified | Automatic (form, import, Apollo) |
| MQL | Hit the lead score threshold of [50], or requested a demo | Automatic (workflow) |
| SQL | An SDR has had a conversation and confirmed need, budget holder and timing | SDR, manually |
| Opportunity | A deal has been created | Automatic when a deal is associated |
| Customer | Has a closed won deal | Automatic |
| Evangelist | Referenceable customer, case study or referral | CS, manually |
| Other | Partners, suppliers, students, anyone not a buyer | Manually |

**MQL vs SQL.** MQL means marketing thinks they're worth a call. SQL means a human has spoken to them and confirmed it. A demo request skips straight to MQL but still needs a conversation before SQL.

**When to move to Opportunity.** Don't set it by hand. Create the deal and associate the contact; the stage updates itself.

**Can I move a stage backwards?** No. HubSpot won't let you without clearing the field first, and doing that breaks reporting. If a contact is genuinely at the wrong stage, ask [Gerard].

**Contact stuck as Lead after a call.** Usually the call was logged but the SDR didn't set SQL. Set it yourself if you had the qualifying conversation. If they're already in a deal, check the deal is associated with the contact.

## Lead status

Lead status tracks the SDR's working state on a contact. It sits alongside lifecycle stage, it doesn't replace it.

| Status | Use when |
|---|---|
| New | Not contacted yet |
| Attempting to contact | In a sequence or calling, no reply yet |
| Connected | Spoken to them, qualification in progress |
| Nurture: next term | Interested but timing is tied to the academic calendar. Set the *Recontact Date* property too. |
| Nurture: not now | Interested, no clear timing |
| Unqualified | Not a fit. Pick a reason in *Unqualified Reason*. |
| Bad data | Wrong contact, bounced, left the institution |

**"Contact me next term".** Use *Nurture: next term* and set *Recontact Date* to the start of that term. A [workflow] creates a task for the owner two weeks before.
