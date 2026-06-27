# Detail N Deliver — Mobile Car Detailing

Flask + HTML/CSS/JS site for a mobile car detailing service.

## What's interactive

- **Animated hero**: car drives in on load, headlight pulses, wheels spin while the page scrolls
- **Live quote calculator**: pick service, vehicle size, and add-ons — price updates from a Flask `/api/quote` endpoint
- **Receipt panel**: itemized breakdown updates in real time
- **Booking form**: submits to `/api/book`, persists to `bookings.json`, shows confirmation inline
- **Service cards → quote sync**: clicking a service card jumps to the calculator and selects it
- **Atmospheric background**: drifting headlight beams + subtle starfield

## Run it

```bash
cd detail-n-deliver
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000

## File structure

```
detail-n-deliver/
├── app.py                    # Flask backend (quote + booking APIs)
├── requirements.txt
├── templates/
│   └── index.html            # Single-page site
└── static/
    ├── css/style.css         # Dark navy automotive styling
    └── js/script.js          # Quote calculator + form submission
```

## Backend endpoints

| Method | Route                | Purpose                          |
|--------|----------------------|----------------------------------|
| GET    | `/`                  | Renders the homepage             |
| POST   | `/api/quote`         | Returns itemized price quote     |
| POST   | `/api/book`          | Saves a booking to bookings.json |
| GET    | `/admin/bookings`    | View all bookings (JSON)         |

## Pricing logic (edit in `app.py`)

- **Base prices**: Exterior $200, Full Detail $250
- **Vehicle multipliers**: Sedan 1.0×, SUV 1.2×, Truck 1.3×, Van 1.4×
- **Add-ons**: pet hair ($40), headlight restoration ($60), engine bay ($50), ceramic spray ($80), odor treatment ($45)

To change pricing, edit the `BASE_PRICES`, `VEHICLE_MULTIPLIER`, and `ADDONS` dicts at the top of `app.py`.

## Next steps you might want

- **Hook up real email**: replace the file-based booking storage with a call to SendGrid/Mailgun/SMTP so detailndeliver@gmail.com gets pinged on each booking
- **Add Stripe**: take a deposit at booking time
- **Calendar integration**: pull busy slots from Google Calendar and gray out unavailable times in the form
- **Protect `/admin/bookings`**: add basic auth or move to a real DB with an authed admin page
- **Service area enforcement**: validate the address geocodes inside your Bay Area service radius before allowing booking
