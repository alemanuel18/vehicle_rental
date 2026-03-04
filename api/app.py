"""
Capa de Presentación (Web) → API REST con Flask
Expone todos los recursos del sistema como endpoints JSON.
El frontend HTML/JS consume esta API.

Endpoints:
  GET    /api/dashboard          → estadísticas generales
  GET    /api/vehicles           → listar vehículos (?available=true)
  POST   /api/vehicles           → registrar vehículo
  DELETE /api/vehicles/<plate>   → eliminar vehículo
  GET    /api/customers          → listar clientes
  POST   /api/customers          → registrar cliente
  GET    /api/rentals            → listar reservas (?active=true)
  POST   /api/rentals            → crear reserva
  POST   /api/rentals/<id>/complete → completar reserva
  POST   /api/rentals/<id>/cancel   → cancelar reserva
  GET    /api/rentals/quote      → cotizar (?plate=&days=&km=)
  GET    /api/pricing/strategies → estrategias disponibles
  POST   /api/pricing/strategy   → cambiar estrategia activa
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from flask import Flask, jsonify, request, send_from_directory
from vehicle_rental.data.dao.json_dao import JsonVehicleDAO, JsonCustomerDAO, JsonRentalDAO
from vehicle_rental.infrastructure.adapters.insurance_adapter import InsuranceAdapterV1
from vehicle_rental.business.pricing.pricing_strategy import DailyRateStrategy, get_available_strategies
from vehicle_rental.business.service.rental_service import RentalService
from vehicle_rental.data.models.entities import RentalStatus

# ── App setup ──────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(__file__)
FRONTEND_DIR = os.path.join(BASE_DIR, '..', 'frontend')

app = Flask(
    __name__,
    static_folder  = os.path.join(FRONTEND_DIR, 'static'),
    template_folder= os.path.join(FRONTEND_DIR, 'templates'),
)

# ── CORS manual (sin flask-cors) ───────────────────────────────
@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin']  = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,DELETE,OPTIONS'
    return response

@app.route('/api/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    return jsonify({}), 200

# ── Dependency injection ───────────────────────────────────────
_pricing_strategies = get_available_strategies()
_active_strategy    = DailyRateStrategy()

service = RentalService(
    vehicle_dao   = JsonVehicleDAO(),
    customer_dao  = JsonCustomerDAO(),
    rental_dao    = JsonRentalDAO(),
    insurance_svc = InsuranceAdapterV1(),
    pricing       = _active_strategy,
)

# Seed solo si está vacío
def seed():
    if service.list_vehicles():
        return
    service.register_vehicle("car",   "ABC-001", "Toyota Corolla",      2022, 55.00)
    service.register_vehicle("car",   "DEF-202", "Honda Civic",         2023, 60.00)
    service.register_vehicle("suv",   "XYZ-999", "Ford Explorer",       2021, 85.00)
    service.register_vehicle("suv",   "GHI-444", "Jeep Grand Cherokee", 2022, 95.00)
    service.register_vehicle("truck", "TRK-111", "Chevrolet Silverado", 2020, 70.00)
    service.register_vehicle("truck", "TRK-222", "Ford F-150",          2023, 75.00)
    c1 = service.register_customer("Ana García",  "ana@mail.com",   "GT-001234")
    c2 = service.register_customer("Luis Pérez",  "luis@mail.com",  "GT-005678")
    service.register_customer("María López", "maria@mail.com", "GT-009012")
    service.create_rental("DEF-202", c1.id, days=3, km_estimate=150)
    r = service.create_rental("TRK-111", c2.id, days=5, km_estimate=300)
    service.complete_rental(r.id)

# ── Serializers ────────────────────────────────────────────────
def ser_vehicle(v):
    return {
        "plate": v.plate, "model": v.model, "year": v.year,
        "daily_rate": v.daily_rate, "type": v.vehicle_type.value,
        "available": v.available,
    }

def ser_customer(c):
    return {"id": c.id, "name": c.name, "email": c.email, "license": c.license}

def ser_rental(r):
    return {
        "id": r.id, "vehicle": ser_vehicle(r.vehicle),
        "customer": ser_customer(r.customer),
        "days": r.days, "km_estimate": r.km_estimate,
        "cost": r.cost, "policy_id": r.policy_id,
        "pricing_type": r.pricing_type,
        "status": r.status.value,
        "start_date": r.start_date.isoformat(),
        "end_date": r.end_date().isoformat(),
    }

def ok(data):      return jsonify({"ok": True,  "data": data}),  200
def created(data): return jsonify({"ok": True,  "data": data}),  201
def err(msg, code=400): return jsonify({"ok": False, "error": str(msg)}), code

# ── Serve frontend ─────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory(os.path.join(FRONTEND_DIR, 'templates'), 'index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(os.path.join(FRONTEND_DIR, 'static'), filename)

# ── Dashboard ──────────────────────────────────────────────────
@app.route('/api/dashboard')
def dashboard():
    vehicles  = service.list_vehicles()
    customers = service.list_customers()
    rentals   = service.list_rentals()
    active    = [r for r in rentals if r.status == RentalStatus.ACTIVE]
    completed = [r for r in rentals if r.status == RentalStatus.COMPLETED]
    cancelled = [r for r in rentals if r.status == RentalStatus.CANCELLED]
    revenue   = sum(r.cost for r in completed)

    type_counts = {}
    for v in vehicles:
        t = v.vehicle_type.value
        type_counts[t] = type_counts.get(t, 0) + 1

    recent = sorted(rentals, key=lambda r: r.start_date.isoformat(), reverse=True)[:5]

    return ok({
        "vehicles":        {"total": len(vehicles), "available": sum(1 for v in vehicles if v.available), "by_type": type_counts},
        "customers":       {"total": len(customers)},
        "rentals":         {"total": len(rentals), "active": len(active), "completed": len(completed), "cancelled": len(cancelled)},
        "revenue":         round(revenue, 2),
        "recent_rentals":  [ser_rental(r) for r in recent],
        "active_strategy": service.current_pricing_strategy(),
    })

# ── Vehicles ───────────────────────────────────────────────────
@app.route('/api/vehicles', methods=['GET'])
def get_vehicles():
    only_available = request.args.get('available', '').lower() == 'true'
    vehicles = service.list_vehicles(only_available=only_available)
    return ok([ser_vehicle(v) for v in vehicles])

@app.route('/api/vehicles', methods=['POST'])
def create_vehicle():
    d = request.json or {}
    try:
        v = service.register_vehicle(
            vehicle_type = d.get('type', ''),
            plate        = d.get('plate', ''),
            model        = d.get('model', ''),
            year         = int(d.get('year', 0)),
            daily_rate   = float(d.get('daily_rate', 0)),
        )
        return created(ser_vehicle(v))
    except (ValueError, KeyError) as e:
        return err(e)

@app.route('/api/vehicles/<plate>', methods=['DELETE'])
def delete_vehicle(plate):
    try:
        removed = service.remove_vehicle(plate)
        return ok({"removed": removed})
    except ValueError as e:
        return err(e)

# ── Customers ──────────────────────────────────────────────────
@app.route('/api/customers', methods=['GET'])
def get_customers():
    return ok([ser_customer(c) for c in service.list_customers()])

@app.route('/api/customers', methods=['POST'])
def create_customer():
    d = request.json or {}
    try:
        c = service.register_customer(
            name       = d.get('name', ''),
            email      = d.get('email', ''),
            license_no = d.get('license', ''),
        )
        return created(ser_customer(c))
    except ValueError as e:
        return err(e)

# ── Rentals ────────────────────────────────────────────────────
@app.route('/api/rentals', methods=['GET'])
def get_rentals():
    only_active = request.args.get('active', '').lower() == 'true'
    rentals = service.list_rentals(only_active=only_active)
    return ok([ser_rental(r) for r in rentals])

@app.route('/api/rentals', methods=['POST'])
def create_rental():
    d = request.json or {}
    try:
        r = service.create_rental(
            plate       = d.get('plate', ''),
            customer_id = d.get('customer_id', ''),
            days        = int(d.get('days', 0)),
            km_estimate = float(d.get('km_estimate', 0)),
        )
        return created(ser_rental(r))
    except ValueError as e:
        return err(e)

@app.route('/api/rentals/<rental_id>/complete', methods=['POST'])
def complete_rental(rental_id):
    try:
        r = service.complete_rental(rental_id)
        return ok(ser_rental(r))
    except ValueError as e:
        return err(e)

@app.route('/api/rentals/<rental_id>/cancel', methods=['POST'])
def cancel_rental(rental_id):
    try:
        r = service.cancel_rental(rental_id)
        return ok(ser_rental(r))
    except ValueError as e:
        return err(e)

@app.route('/api/rentals/quote', methods=['GET'])
def quote_rental():
    try:
        plate = request.args.get('plate', '')
        days  = int(request.args.get('days', 0))
        km    = float(request.args.get('km', 0))
        cost  = service.quote(plate, days, km)
        return ok({"cost": cost, "strategy": service.current_pricing_strategy()})
    except (ValueError, TypeError) as e:
        return err(e)

# ── Pricing strategies ─────────────────────────────────────────
@app.route('/api/pricing/strategies', methods=['GET'])
def get_strategies():
    strategies = get_available_strategies()
    return ok([{"key": k, "description": s.describe()} for k, s in strategies.items()])

@app.route('/api/pricing/strategy', methods=['POST'])
def set_strategy():
    d   = request.json or {}
    key = d.get('key', '')
    strategies = get_available_strategies()
    if key not in strategies:
        return err(f"Estrategia '{key}' no encontrada.")
    service.set_pricing_strategy(strategies[key])
    return ok({"active": service.current_pricing_strategy()})

# ── Entry point ────────────────────────────────────────────────
if __name__ == '__main__':
    seed()
    print("\n  🚗  Sistema de Alquiler de Vehículos")
    print("  📡  API corriendo en http://localhost:5000")
    print("  🌐  Abre http://localhost:5000 en tu navegador\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
