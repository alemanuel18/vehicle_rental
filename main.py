"""
main.py — Punto de entrada del sistema
Ensambla todas las dependencias (Dependency Injection) y arranca el CLI.

Persistencia: los datos se guardan en vehicle_rental/data/db/*.json
  vehicles.json  → vehículos registrados
  customers.json → clientes registrados
  rentals.json   → reservas (activas, completadas, canceladas)
"""
from vehicle_rental.data.dao.json_dao import (
    JsonVehicleDAO  as VehicleDAO,
    JsonCustomerDAO as CustomerDAO,
    JsonRentalDAO   as RentalDAO,
)
from vehicle_rental.infrastructure.adapters.insurance_adapter import InsuranceAdapterV1
from vehicle_rental.business.pricing.pricing_strategy import DailyRateStrategy
from vehicle_rental.business.service.rental_service   import RentalService
from vehicle_rental.presentation.cli                  import main_menu


def seed_data(service: RentalService):
    """Carga datos de ejemplo solo en la primera ejecución."""
    service.register_vehicle("car",   "ABC-001", "Toyota Corolla",      2022, 55.00)
    service.register_vehicle("car",   "DEF-202", "Honda Civic",         2023, 60.00)
    service.register_vehicle("suv",   "XYZ-999", "Ford Explorer",       2021, 85.00)
    service.register_vehicle("suv",   "GHI-444", "Jeep Grand Cherokee", 2022, 95.00)
    service.register_vehicle("truck", "TRK-111", "Chevrolet Silverado", 2020, 70.00)
    service.register_vehicle("truck", "TRK-222", "Ford F-150",          2023, 75.00)

    c1 = service.register_customer("Ana Garcia",  "ana@mail.com",   "GT-001234")
    c2 = service.register_customer("Luis Perez",  "luis@mail.com",  "GT-005678")
    service.register_customer("Maria Lopez", "maria@mail.com", "GT-009012")

    service.create_rental("DEF-202", c1.id, days=3, km_estimate=150)
    rental = service.create_rental("TRK-111", c2.id, days=5, km_estimate=300)
    service.complete_rental(rental.id)


def build_service() -> RentalService:
    """Construye el servicio inyectando JSON DAOs."""
    return RentalService(
        vehicle_dao   = VehicleDAO(),
        customer_dao  = CustomerDAO(),
        rental_dao    = RentalDAO(),
        insurance_svc = InsuranceAdapterV1(),
        pricing       = DailyRateStrategy(),
    )


if __name__ == "__main__":
    service = build_service()
    if not service.list_vehicles():
        print("  Primera ejecucion — cargando datos de ejemplo...")
        seed_data(service)
    main_menu(service)
