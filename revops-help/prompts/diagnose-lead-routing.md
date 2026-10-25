
# Diagnose lead routing

Use this when a colleague asks why a lead wasn't assigned, was assigned to the wrong person, or has no owner. Read-only: never change the record.

## 1. Get the record

You need the contact's HubSpot URL or exact email. If the person only gave a company name, ask which contact. Don't guess between several.

## 2. Pull these facts

From the contact:
- Contact owner and when it was set (property history)
- Create date
- Region
- Lifecycle stage and lead status
- Recent form submissions: form name and date
- Workflow history: was it enrolled in [Inbound lead routing]?

From the associated company:
- Company owner, and whether that user is still active
- Region

## 3. Work through the checks in order

Stop at the first one that explains it. The rules are in *Lead routing and ownership*.

1. **Not a routing form.** Was the latest submission one of the routing forms? If not, nothing should have routed. Explain that.
2. **Already owned.** Was an owner set before the submission? Routing never overwrites. Name the existing owner.
3. **Company owner.** Does the company have an owner? If so, the contact follows them. If that owner is deactivated, that's the cause.
4. **Region blank.** If Region is empty, routing had nowhere to send it.
5. **Not enrolled.** If the contact isn't in the routing workflow history, say so. Likely re-enrolment or a suppression rule.
6. **Everyone unavailable.** If enrolled, region set, and still no owner, round robin may have had nobody available.
7. **None of the above.** Say you couldn't find the cause and hand off to [Gerard] with everything you checked.

## 4. Reply

Keep it short:

> **Why:** [one sentence]
> **What I found:** [the 2 to 4 facts that prove it]
> **What to do:** [what the person can do themselves, if anything]

If fixing it means changing an owner they don't control, a company owner, Region, or the workflow, add the standard handoff block for [Gerard].

## Examples

**Q:** Why didn't the demo request from Keele come to me?
**A:**
> **Why:** The contact followed the company owner, and Keele is owned by Tom.
> **What I found:** Submitted *Book a demo* on 14 Oct. Company owner is Tom (active). Routing assigned the contact to Tom 5 minutes later.
> **What to do:** Nothing's broken. If Keele should be in your patch, ask [Gerard] to reassign the company.

**Q:** Lead from Bath Spa has no owner.
**A:**
> **Why:** Region is blank, so routing had nowhere to send it.
> **What I found:** Submitted *Contact sales* on 9 Oct. Enrolled in routing. Region empty on contact and company. No company owner.
> **What to do:** Needs [Gerard] to set Region and assign.
>
> **For [Gerard]:** Bath Spa contact unassigned, Region blank
> **Record(s):** [link]
> **What I checked:** Routing form, enrolled, no Region, no company owner
> **Why it needs you:** Region and owner need setting, and enrichment may be missing Bath Spa
