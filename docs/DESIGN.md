# DESIGN: KrushiNeel Setu

## 1. Users and their reality

| User | Context | Design consequence |
|---|---|---|
| Vegetable / paddy farmer | Budget Android or feature phone, patchy data, Odia first | Big targets, icons + Odia text, SMS path, minimal typing |
| FPO manager | Manages cold room, many farmers | Dashboard, bulk actions, reports |
| Fisher (Puri, Ganjam, Kendrapara, Balasore, Chilika) | At sea or landing site, poor signal, wet hands, glare | Offline-first, one-tap check-in, high contrast, SMS fallback |
| Buyer / trader | Wants volume and freshness | Search, alerts, contact on accept |
| Platform admin | Demo / ops | Stats, user and alert management |

## 2. Principles

1. **Odia first, English second.** Language switch always visible; all alerts available in both.
2. **Offline is normal.** Show "saved, will sync" states, never block on network.
3. **One thing per screen.** Primary action is the biggest element.
4. **Colour never alone.** Green / amber / red always paired with an icon and word.
5. **Explain advice.** Every hold/sell or risk message shows the "why" in one sentence.
6. **Low literacy friendly.** Icons for crops, fish species, actions; voice-readable text (future: TTS).
7. **Safety honesty.** Safety screens say alerts supplement official warnings.

## 3. Visual system

- **Palette:** deep teal (primary, sea), leaf green (agri), warm amber (caution), signal red (danger), off-white background, near-black text. Dark/high-contrast mode for sunlight and night use.
- **Type:** Noto Sans Oriya for Odia, Inter for Latin; base 18px, minimum tap target 48px.
- **Components:** large cards, status chips, bottom tab bar (max 5 items), sticky primary button.
- **Motion:** minimal; only for state change (alert pulse, sync spinner).

## 4. Information architecture

```
Home (role-aware)
├── ColdWatch     Rooms ▸ Room detail (live, chart, batches, alerts)
├── GradeLens     Capture ▸ Result ▸ Certificate ▸ History
├── Sagar         Trip (start/check-in/end) · Weather risk · Map/zones · Contacts
├── Mandi         Prices · Forecast · Sell/Hold advice · Price alerts
├── Matsya        My listings · Post catch · Buyers/Matches
└── Me            Profile · Language · Notifications · Help
```

Bottom tab bar adapts by role: farmer (Mandi, Grade, ColdWatch, Me), fisher (Sagar, Matsya, Mandi, Me), FPO (ColdWatch, Grade, Mandi, Me), buyer (Matsya, Mandi, Me).

## 5. Key screens (wireframe-level)

**Home (fisher):** large status banner (today's sea risk: green / amber / red), big "Start trip" or "I'm safe" button, next check-in countdown, latest price tile.

**Trip / check-in:** timer ring, one big **"I'm safe"** button, small **"Need help"** button (long-press), offline badge, last-sent time.

**ColdWatch room detail:** current temp/humidity with range band, status chip, 24h line chart, batch list with remaining-days bars, alert list with Acknowledge. A sticky **Log reading** button (two taps), CSV import, and a SIMULATED badge on demo data.

**GradeLens result:** photo, grade letter in a large badge, confidence bar, "Low confidence, ask for review" notice when needed, Share certificate.

**Mandi advice:** price sparkline, forecast band, verdict card "Hold 5 days" / "Sell today" with one-sentence reason in Odia and the expected gain after storage cost.

**Matsya listing:** species icon grid, quantity stepper, price field, landing-site dropdown, Post; matches appear as cards with Accept / Decline.

## 6. SMS and feature-phone design

Short, memorisable commands; replies always echo what was understood.

| Command | Example | Reply |
|---|---|---|
| `SAFE` | `SAFE B123` | "Check-in saved 10:42. Next by 13:42." |
| `TRIP` | `TRIP B123 12H` | "Trip started. Return by 22:00." |
| `HELP` | `HELP B123` | "Alert sent to contacts. Stay calm." |
| `PRICE` | `PRICE TOMATO BBSR` | "Tomato Bhubaneswar 1800-2200, trend up." |
| `SELL` | `SELL HILSA 40 450 PURI` | "Listing saved. Buyers will be notified." |
| `WEATHER` | `WEATHER PURI` | "Puri: waves 2.1m, wind 28 km/h. AMBER." |

Odia keywords accepted as transliterations; unknown input returns a help message. Note Odia SMS segments are shorter (UCS-2).

## 7. Alert copy rules

- Lead with the action, then the reason: "Move produce to Room 2. Room 1 is at 14°C for 20 min."
- Severity words: `INFO`, `WARNING`, `DANGER`, mirrored in Odia.
- No jargon; avoid false certainty ("risk", "likely").
- Every red safety alert ends with the official helpline reminder (insert verified numbers).

## 8. Accessibility checklist

- [ ] Contrast at least 4.5:1, tested in sunlight mode
- [ ] Tap targets at least 48px
- [ ] Screen-reader labels on icon buttons
- [ ] Works at 360px width and on low-end Android
- [ ] No time-limited interactions on critical flows
- [ ] Odia strings reviewed by a native speaker

## 9. Hackathon demo flow (3 minutes)

1. **Problem (20s):** Spoilage, price crashes, unsafe sea trips, one platform.
2. **ColdWatch (40s):** start the demo simulator (labelled simulated), trigger a power-cut scenario, alert hits phone by SMS, spoilage score drops; show a manual log and a CSV import.
3. **MandiMitra (30s):** tomato forecast and "hold 4 days" advice in Odia.
4. **GradeLens (30s):** photograph a tomato, instant grade, certificate.
5. **SagarSuraksha (40s):** amber sea alert, check-in via SMS, missed check-in escalation.
6. **MatsyaConnect (20s):** post hilsa catch, buyer match notification.
7. **Close (10s):** one platform, offline-first, deployable today.
