"""
Capa de Datos → Modelos de dominio
Entidades puras del negocio, sin lógica de persistencia.
"""
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
import uuid


# ─────────────────────────────────────────────
# Enumeraciones
# ─────────────────────────────────────────────

class VehicleType(Enum):
    CAR   = "Automóvil"
    TRUCK = "Camioneta"
    SUV   = "SUV"


class RentalStatus(Enum):
    ACTIVE    = "Activa"
    COMPLETED = "Completada"
    CANCELLED = "Cancelada"


# ─────────────────────────────────────────────
# Entidades
# ─────────────────────────────────────────────

@dataclass
class Vehicle:
    """Entidad vehículo del dominio."""
    plate:       str
    model:       str
    year:        int
    daily_rate:  float
    vehicle_type: VehicleType
    available:   bool = True

    def __str__(self) -> str:
        status = "Disponible" if self.available else "No disponible"
        return (f"[{self.plate}] {self.year} {self.model} "
                f"({self.vehicle_type.value}) | ${self.daily_rate:.2f}/día | {status}")


@dataclass
class Car(Vehicle):
    """Automóvil estándar."""
    doors: int = 4

    def __post_init__(self):
        self.vehicle_type = VehicleType.CAR


@dataclass
class Truck(Vehicle):
    """Camioneta de carga."""
    payload_kg: float = 1000.0

    def __post_init__(self):
        self.vehicle_type = VehicleType.TRUCK


@dataclass
class SUV(Vehicle):
    """Vehículo deportivo utilitario."""
    awd: bool = True

    def __post_init__(self):
        self.vehicle_type = VehicleType.SUV


@dataclass
class Customer:
    """Entidad cliente del dominio."""
    name:    str
    email:   str
    license: str
    id:      str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())

    def __str__(self) -> str:
        return f"[{self.id}] {self.name} | {self.email} | Lic: {self.license}"


@dataclass
class Rental:
    """Entidad reserva del dominio."""
    vehicle:      Vehicle
    customer:     Customer
    days:         int
    km_estimate:  float
    cost:         float
    policy_id:    str
    pricing_type: str
    status:       RentalStatus = RentalStatus.ACTIVE
    start_date:   date         = field(default_factory=date.today)
    id:           str          = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())

    def end_date(self) -> date:
        from datetime import timedelta
        return self.start_date + timedelta(days=self.days)

    def __str__(self) -> str:
        return (f"[{self.id}] {self.vehicle.model} → {self.customer.name} | "
                f"{self.days} días | ${self.cost:.2f} | Póliza: {self.policy_id} | "
                f"{self.status.value}")
