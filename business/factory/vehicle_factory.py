"""
Capa de Negocio → Patrón Factory Method
Define una interfaz para crear vehículos, pero delega a las subclases
la decisión de qué clase concreta instanciar.

Principios SOLID aplicados:
  - SRP : Cada fábrica tiene una única responsabilidad: construir su vehículo.
  - OCP : Agregar un nuevo tipo (ej. Moto) no modifica ninguna fábrica existente.
  - LSP : Cualquier fábrica concreta puede usarse donde se espera VehicleFactory.
"""
from abc import ABC, abstractmethod
from vehicle_rental.data.models.entities import Vehicle, Car, Truck, SUV


# ─────────────────────────────────────────────
# Creador abstracto (Factory Method)
# ─────────────────────────────────────────────

class VehicleFactory(ABC):
    """
    Creador abstracto del patrón Factory Method.
    El método create_vehicle() es el 'factory method'.
    """

    @abstractmethod
    def create_vehicle(
        self,
        plate:      str,
        model:      str,
        year:       int,
        daily_rate: float,
        **kwargs,
    ) -> Vehicle:
        """Factory method: crea y retorna un vehículo concreto."""
        ...

    def register_and_create(
        self,
        plate:      str,
        model:      str,
        year:       int,
        daily_rate: float,
        **kwargs,
    ) -> Vehicle:
        """
        Template Method: crea el vehículo y aplica validaciones comunes
        antes de retornarlo. Evita duplicar lógica en subclases.
        """
        if daily_rate <= 0:
            raise ValueError("La tarifa diaria debe ser mayor a 0.")
        if year < 2000 or year > 2025:
            raise ValueError("El año del vehículo debe estar entre 2000 y 2025.")
        if not plate.strip():
            raise ValueError("La matrícula no puede estar vacía.")

        vehicle = self.create_vehicle(plate.upper(), model, year, daily_rate, **kwargs)
        return vehicle


# ─────────────────────────────────────────────
# Fábricas concretas (Concrete Creators)
# ─────────────────────────────────────────────

class CarFactory(VehicleFactory):
    """Fábrica concreta: crea Automóviles."""

    def create_vehicle(
        self, plate: str, model: str, year: int, daily_rate: float, **kwargs
    ) -> Car:
        doors = kwargs.get("doors", 4)
        return Car(
            plate=plate,
            model=model,
            year=year,
            daily_rate=daily_rate,
            vehicle_type=None,   # __post_init__ lo asigna
            doors=doors,
        )


class TruckFactory(VehicleFactory):
    """Fábrica concreta: crea Camionetas."""

    def create_vehicle(
        self, plate: str, model: str, year: int, daily_rate: float, **kwargs
    ) -> Truck:
        payload_kg = kwargs.get("payload_kg", 1000.0)
        return Truck(
            plate=plate,
            model=model,
            year=year,
            daily_rate=daily_rate,
            vehicle_type=None,
            payload_kg=payload_kg,
        )


class SuvFactory(VehicleFactory):
    """Fábrica concreta: crea SUVs."""

    def create_vehicle(
        self, plate: str, model: str, year: int, daily_rate: float, **kwargs
    ) -> SUV:
        awd = kwargs.get("awd", True)
        return SUV(
            plate=plate,
            model=model,
            year=year,
            daily_rate=daily_rate,
            vehicle_type=None,
            awd=awd,
        )


# ─────────────────────────────────────────────
# Registro de fábricas (OCP: extensible sin modificar)
# ─────────────────────────────────────────────

VEHICLE_FACTORIES: dict[str, VehicleFactory] = {
    "car":   CarFactory(),
    "truck": TruckFactory(),
    "suv":   SuvFactory(),
}


def get_factory(vehicle_type: str) -> VehicleFactory:
    """
    Retorna la fábrica correspondiente al tipo solicitado.
    Lanza KeyError si el tipo no está registrado.
    """
    key = vehicle_type.lower().strip()
    if key not in VEHICLE_FACTORIES:
        available = ", ".join(VEHICLE_FACTORIES.keys())
        raise KeyError(f"Tipo '{vehicle_type}' no registrado. Disponibles: {available}")
    return VEHICLE_FACTORIES[key]
