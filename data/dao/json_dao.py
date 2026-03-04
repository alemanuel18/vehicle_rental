"""
Capa de Datos → Implementaciones DAO con persistencia JSON
Reemplazan a InMemoryVehicleDAO, InMemoryCustomerDAO e InMemoryRentalDAO
sin modificar ninguna otra capa del sistema (OCP + DIP en acción).

Cada entidad se serializa a JSON y se guarda en un archivo separado:
  data/db/vehicles.json
  data/db/customers.json
  data/db/rentals.json

El formato interno de cada archivo es:
  { "id_clave": { ...campos de la entidad... }, ... }
"""
import json
import os
from datetime import date
from typing import Optional

from vehicle_rental.data.dao.dao import BaseDAO
from vehicle_rental.data.models.entities import (
    Vehicle, Car, Truck, SUV,
    Customer, Rental,
    VehicleType, RentalStatus,
)


# ─────────────────────────────────────────────
# Directorio de almacenamiento
# ─────────────────────────────────────────────

DB_DIR = os.path.join(os.path.dirname(__file__), "..", "db")


def _ensure_db_dir():
    """Crea el directorio data/db/ si no existe."""
    os.makedirs(DB_DIR, exist_ok=True)


def _db_path(filename: str) -> str:
    return os.path.join(DB_DIR, filename)


# ─────────────────────────────────────────────
# Serialización / Deserialización
# ─────────────────────────────────────────────

def _vehicle_to_dict(v: Vehicle) -> dict:
    base = {
        "plate":        v.plate,
        "model":        v.model,
        "year":         v.year,
        "daily_rate":   v.daily_rate,
        "vehicle_type": v.vehicle_type.name,
        "available":    v.available,
    }
    if isinstance(v, Car):
        base["subtype"] = "Car"
        base["doors"]   = v.doors
    elif isinstance(v, Truck):
        base["subtype"]     = "Truck"
        base["payload_kg"]  = v.payload_kg
    elif isinstance(v, SUV):
        base["subtype"] = "SUV"
        base["awd"]     = v.awd
    else:
        base["subtype"] = "Vehicle"
    return base


def _dict_to_vehicle(d: dict) -> Vehicle:
    subtype = d.get("subtype", "Vehicle")
    common  = dict(
        plate        = d["plate"],
        model        = d["model"],
        year         = d["year"],
        daily_rate   = d["daily_rate"],
        vehicle_type = VehicleType[d["vehicle_type"]],
        available    = d["available"],
    )
    if subtype == "Car":
        v = Car(**common, doors=d.get("doors", 4))
    elif subtype == "Truck":
        v = Truck(**common, payload_kg=d.get("payload_kg", 1000.0))
    elif subtype == "SUV":
        v = SUV(**common, awd=d.get("awd", True))
    else:
        v = Vehicle(**common)
    return v


def _customer_to_dict(c: Customer) -> dict:
    return {"id": c.id, "name": c.name, "email": c.email, "license": c.license}


def _dict_to_customer(d: dict) -> Customer:
    return Customer(id=d["id"], name=d["name"], email=d["email"], license=d["license"])


def _rental_to_dict(r: Rental) -> dict:
    return {
        "id":           r.id,
        "vehicle":      _vehicle_to_dict(r.vehicle),
        "customer":     _customer_to_dict(r.customer),
        "days":         r.days,
        "km_estimate":  r.km_estimate,
        "cost":         r.cost,
        "policy_id":    r.policy_id,
        "pricing_type": r.pricing_type,
        "status":       r.status.name,
        "start_date":   r.start_date.isoformat(),
    }


def _dict_to_rental(d: dict) -> Rental:
    r = Rental(
        id           = d["id"],
        vehicle      = _dict_to_vehicle(d["vehicle"]),
        customer     = _dict_to_customer(d["customer"]),
        days         = d["days"],
        km_estimate  = d["km_estimate"],
        cost         = d["cost"],
        policy_id    = d["policy_id"],
        pricing_type = d["pricing_type"],
        status       = RentalStatus[d["status"]],
        start_date   = date.fromisoformat(d["start_date"]),
    )
    return r


# ─────────────────────────────────────────────
# Utilidades de lectura/escritura JSON
# ─────────────────────────────────────────────

def _load(filename: str) -> dict:
    """Lee el archivo JSON y retorna el dict. Si no existe, retorna {}."""
    _ensure_db_dir()
    path = _db_path(filename)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(filename: str, data: dict) -> None:
    """Escribe el dict como JSON con indentación legible."""
    _ensure_db_dir()
    with open(_db_path(filename), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────
# JSON DAOs concretos
# ─────────────────────────────────────────────

class JsonVehicleDAO(BaseDAO[Vehicle]):
    """
    DAO de vehículos con persistencia en data/db/vehicles.json.
    Misma interfaz que InMemoryVehicleDAO — intercambiable sin cambiar nada más.
    """

    FILE = "vehicles.json"

    def save(self, entity: Vehicle) -> None:
        data = _load(self.FILE)
        data[entity.plate] = _vehicle_to_dict(entity)
        _save(self.FILE, data)

    def find_by_id(self, entity_id: str) -> Optional[Vehicle]:
        data = _load(self.FILE)
        raw  = data.get(entity_id)
        return _dict_to_vehicle(raw) if raw else None

    def find_all(self) -> list[Vehicle]:
        return [_dict_to_vehicle(v) for v in _load(self.FILE).values()]

    def delete(self, entity_id: str) -> bool:
        data = _load(self.FILE)
        if entity_id not in data:
            return False
        del data[entity_id]
        _save(self.FILE, data)
        return True

    def find_available(self) -> list[Vehicle]:
        return [v for v in self.find_all() if v.available]

    def find_by_type(self, vehicle_type: VehicleType) -> list[Vehicle]:
        return [v for v in self.find_all() if v.vehicle_type == vehicle_type]


class JsonCustomerDAO(BaseDAO[Customer]):
    """
    DAO de clientes con persistencia en data/db/customers.json.
    """

    FILE = "customers.json"

    def save(self, entity: Customer) -> None:
        data = _load(self.FILE)
        data[entity.id] = _customer_to_dict(entity)
        _save(self.FILE, data)

    def find_by_id(self, entity_id: str) -> Optional[Customer]:
        data = _load(self.FILE)
        raw  = data.get(entity_id)
        return _dict_to_customer(raw) if raw else None

    def find_all(self) -> list[Customer]:
        return [_dict_to_customer(c) for c in _load(self.FILE).values()]

    def delete(self, entity_id: str) -> bool:
        data = _load(self.FILE)
        if entity_id not in data:
            return False
        del data[entity_id]
        _save(self.FILE, data)
        return True

    def find_by_email(self, email: str) -> Optional[Customer]:
        return next((c for c in self.find_all() if c.email == email), None)


class JsonRentalDAO(BaseDAO[Rental]):
    """
    DAO de reservas con persistencia en data/db/rentals.json.
    """

    FILE = "rentals.json"

    def save(self, entity: Rental) -> None:
        data = _load(self.FILE)
        data[entity.id] = _rental_to_dict(entity)
        _save(self.FILE, data)

    def find_by_id(self, entity_id: str) -> Optional[Rental]:
        data = _load(self.FILE)
        raw  = data.get(entity_id)
        return _dict_to_rental(raw) if raw else None

    def find_all(self) -> list[Rental]:
        return [_dict_to_rental(r) for r in _load(self.FILE).values()]

    def delete(self, entity_id: str) -> bool:
        data = _load(self.FILE)
        if entity_id not in data:
            return False
        del data[entity_id]
        _save(self.FILE, data)
        return True

    def find_by_customer(self, customer_id: str) -> list[Rental]:
        return [r for r in self.find_all() if r.customer.id == customer_id]

    def find_active(self) -> list[Rental]:
        return [r for r in self.find_all() if r.status == RentalStatus.ACTIVE]
