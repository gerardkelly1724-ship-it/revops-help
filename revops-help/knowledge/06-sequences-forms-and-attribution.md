# Sequences, forms and attribution

*Placeholder content. Anything in [square brackets] needs confirming against your real setup.*

## Why a sequence stops or a contact unenrols

HubSpot unenrols a contact automatically when:

- They reply to any email in the sequence
- They book a meeting through your meetings link
- An email bounces
- They unsubscribe
- Someone else at the same company replies, if *Unenrol other contacts at the company* is on in your sequence settings

If none of those happened, check whether your email inbox has disconnected (**Settings > General > Email**). A disconnected inbox pauses every sequence you own.

A contact can only be in one sequence at a time.

**Sent from the wrong address.** Sequences send from the inbox connected to the person who enrolled the contact. If someone enrolled on your behalf, it comes from them.

## Forms

Only [Book a demo], [Contact sales] and [Pricing page enquiry] trigger sales routing. Webinar forms add contacts to the [Webinar attendees] list and nurture only.

**Webinar sign-ups not showing.** Webinar registrations come through the [Zoom] integration, not a HubSpot form, so they won't appear as form submissions. Check the contact's timeline for the webinar event instead. If they aren't there at all, that's a sync issue for [Gerard].

## Attribution

UTM parameters are captured on the first page view of a session. They come through as *Original Source Drill-Down 1 and 2* and the [UTM Campaign] property.

UTMs go missing when:
- The link points to a page that redirects and drops the parameters
- The person accepts cookies after the first page loads
- The link has a typo in the parameter name (e.g. `utm_campagin`)

If a whole campaign is affected, send [Gerard] an example link.
