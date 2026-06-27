"""
Detail N Deliver — Mobile Car Detailing
"""
from flask import Flask, render_template, request, jsonify
from datetime import datetime
import json
import os
import resend

app = Flask(__name__)

# Resend setup — API key comes from Vercel environment variable
resend.api_key = os.environ.get('RESEND_API_KEY')
NOTIFY_EMAIL = 'detailndeliver@gmail.com'

BOOKINGS_FILE = os.path.join(os.path.dirname(__file__), 'bookings.json')

# ---------- Pricing config ----------
BASE_PRICES = {
    'exterior': 225,
    'full': 325,
}

VEHICLE_MULTIPLIER = {
    'sedan': 1.0,
    'suv': 1.2,
    'truck': 1.3,
    'van': 1.4,
}

ADDONS = {
    'pet_hair': {'label': 'Pet hair removal', 'price': 45},
}

SERVICE_LABELS = {
    'exterior': 'Exterior Wash & Dry',
    'full': 'Full Detail',
}
VEHICLE_LABELS = {
    'sedan': 'Sedan',
    'suv': 'SUV',
    'truck': 'Truck',
    'van': 'Van / Minivan',
}
TIME_LABELS = {
    '8-10': '8:00 AM – 10:00 AM',
    '10-12': '10:00 AM – 12:00 PM',
    '12-14': '12:00 PM – 2:00 PM',
    '14-16': '2:00 PM – 4:00 PM',
    '16-18': '4:00 PM – 6:00 PM',
}


def load_bookings():
    if os.path.exists(BOOKINGS_FILE):
        try:
            with open(BOOKINGS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_bookings(bookings):
    try:
        with open(BOOKINGS_FILE, 'w') as f:
            json.dump(bookings, f, indent=2)
    except IOError:
        pass


def send_booking_email(booking):
    """Email the booking details to detailndeliver@gmail.com."""
    if not resend.api_key:
        print("Resend API key missing — skipping email")
        return False

    service_label = SERVICE_LABELS.get(booking['service'], booking['service'])
    vehicle_label = VEHICLE_LABELS.get(booking['vehicle'], booking['vehicle'])
    time_label = TIME_LABELS.get(booking['time'], booking['time'])
    addons_text = ', '.join(
        ADDONS[a]['label'] for a in booking.get('addons', []) if a in ADDONS
    ) or 'None'

    total = booking.get('quoted_total') or 'TBD'
    if isinstance(total, (int, float)):
        total = f"${total:.0f}"

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #f5f5f5; padding: 20px;">
      <div style="background: #0A1628; color: white; padding: 24px; border-radius: 8px 8px 0 0;">
        <h1 style="margin: 0; font-size: 24px;">New Booking — Detail N Deliver</h1>
        <p style="margin: 8px 0 0; color: #5BA3F5;">Confirmation #{booking['id']}</p>
      </div>
      <div style="background: white; padding: 24px; border-radius: 0 0 8px 8px;">
        <h2 style="color: #0A1628; margin-top: 0;">Customer</h2>
        <p><strong>Name:</strong> {booking['name']}</p>
        <p><strong>Phone:</strong> <a href="tel:{booking['phone']}">{booking['phone']}</a></p>
        <p><strong>Email:</strong> <a href="mailto:{booking['email']}">{booking['email']}</a></p>
        <p><strong>Address:</strong> {booking['address']}</p>

        <h2 style="color: #0A1628;">Service</h2>
        <p><strong>Service:</strong> {service_label}</p>
        <p><strong>Vehicle:</strong> {vehicle_label}</p>
        <p><strong>Add-ons:</strong> {addons_text}</p>
        <p><strong>Estimated Total:</strong> {total}</p>

        <h2 style="color: #0A1628;">When</h2>
        <p><strong>Date:</strong> {booking['date']}</p>
        <p><strong>Time:</strong> {time_label}</p>

        {'<h2 style="color: #0A1628;">Notes</h2><p>' + booking['notes'] + '</p>' if booking.get('notes') else ''}

        <hr style="margin: 24px 0; border: none; border-top: 1px solid #ddd;">
        <p style="color: #888; font-size: 12px;">Booked at {booking['created_at']}</p>
      </div>
    </div>
    """

    try:
        resend.Emails.send({
            "from": "Detail N Deliver <onboarding@resend.dev>",
            "to": [NOTIFY_EMAIL],
            "reply_to": booking['email'],
            "subject": f"New Booking: {booking['name']} — {service_label} on {booking['date']}",
            "html": html,
        })
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


@app.route('/')
def index():
    return render_template('index.html', addons=ADDONS)


@app.route('/api/quote', methods=['POST'])
def quote():
    data = request.get_json() or {}
    service = data.get('service', 'exterior')
    vehicle = data.get('vehicle', 'sedan')
    addon_keys = data.get('addons', [])

    base = BASE_PRICES.get(service, 225)
    mult = VEHICLE_MULTIPLIER.get(vehicle, 1.0)
    subtotal = base * mult

    addon_lines = []
    addon_total = 0
    for key in addon_keys:
        if key in ADDONS:
            addon_lines.append({
                'key': key,
                'label': ADDONS[key]['label'],
                'price': ADDONS[key]['price'],
            })
            addon_total += ADDONS[key]['price']

    total = subtotal + addon_total

    return jsonify({
        'service': service,
        'vehicle': vehicle,
        'base': base,
        'multiplier': mult,
        'subtotal': round(subtotal, 2),
        'addons': addon_lines,
        'addons_total': addon_total,
        'total': round(total, 2),
    })


@app.route('/api/book', methods=['POST'])
def book():
    data = request.get_json() or {}
    required = ['name', 'email', 'phone', 'address', 'service', 'vehicle', 'date', 'time']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400

    booking = {
        'id': datetime.now().strftime('%Y%m%d%H%M%S'),
        'created_at': datetime.now().isoformat(),
        'name': data['name'],
        'email': data['email'],
        'phone': data['phone'],
        'address': data['address'],
        'service': data['service'],
        'vehicle': data['vehicle'],
        'addons': data.get('addons', []),
        'date': data['date'],
        'time': data['time'],
        'notes': data.get('notes', ''),
        'quoted_total': data.get('quoted_total'),
    }

    # Save locally (backup — won't persist on Vercel)
    bookings = load_bookings()
    bookings.append(booking)
    save_bookings(bookings)

    # Email it
    email_sent = send_booking_email(booking)

    return jsonify({
        'success': True,
        'booking_id': booking['id'],
        'email_sent': email_sent,
    })


@app.route('/admin/bookings')
def admin_bookings():
    return jsonify(load_bookings())


# Passenger / WSGI entry point
application = app


if __name__ == '__main__':
    app.run(debug=True, port=5000)