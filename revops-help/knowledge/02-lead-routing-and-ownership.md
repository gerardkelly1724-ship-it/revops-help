# Lead routing and ownership

*Placeholder content. Anything in [square brackets] needs confirming against your real setup.*

## How inbound leads get assigned

1. A contact submits a demo or contact form.
2. The [Inbound lead routing] workflow runs. It waits [5 minutes] so enrichment can fill in company details.
3. If the contact's company already has an owner, the contact goes to that owner.
4. If not, it's assigned by territory using the *Region* property:
   - [England North] → [Aoife]
   - [England South & Wales] → [Liam]
   - [Scotland & Northern Ireland] → [rotating between Aoife and Liam]
   - [International] → round robin across all SDRs
5. Within a territory with more than one SDR, it's round robin. Round robin skips anyone marked unavailable in HubSpot.
6. The owner gets an email and a task due within [1 business day].

## Why a lead might not be assigned

Check these in order:

| Check | What you'll see | Cause |
|---|---|---|
| Was it a routing form? | Form name isn't on the list below | Only demo and contact forms route. Webinar and content forms don't. |
| Is *Region* empty? | Region is blank | Enrichment couldn't place them. Workflow has no branch to send it to. |
| Is the company owned by someone who's left? | Company owner is a deactivated user | Contact was "assigned" to a dead account |
| Was the contact already owned? | Owner set before the submission | Routing never overwrites an existing owner |
| Did they enrol in the workflow? | Not in the workflow history | Already enrolled before and re-enrolment is off, or they were suppressed (e.g. competitor or student email) |
| Is everyone in the territory unavailable? | All SDRs in the rotation marked out of office | Round robin had nobody to pick |

Routing forms: [Book a demo], [Contact sales], [Pricing page enquiry].

## Lead went to the wrong person

Most common reason is *Region* or company ownership. If the company is owned by an AE, every new contact at that company follows the company owner. That's on purpose so accounts stay with one person. If the company owner is wrong, ask [Gerard] to reassign the company.

## Changing ownership

You can reassign a single contact you own to a colleague if you've agreed it with them. Bulk reassignments, territory changes and company ownership changes go to [Gerard].
