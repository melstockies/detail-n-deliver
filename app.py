"""
Detail N Deliver — Mobile Car Detailing
Flask backend serving the booking site + quote/booking APIs.
"""
from flask import Flask, render_template, request, jsonify
from datetime import datetime
import json
import os

app = Flask(__name__)

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

    bookings = load_bookings()
    bookings.append(booking)
    save_bookings(bookings)

    return jsonify({'success': True, 'booking_id': booking['id']})


@app.route('/admin/bookings')
def admin_bookings():
    return jsonify(load_bookings())


# Passenger (Namecheap) entry point
application = app


if __name__ == '__main__':
    app.run(debug=True, port=5000)
