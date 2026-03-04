"""
Capa de Negocio → RentalService
Servicio central que orquesta todos los patrones de diseño:

  ┌──────────────────────────────────────────────────────┐
  │  Factory Method → crea vehículos tipados             │
  │  Strategy       → calcula tarifa intercambiable      │
  │  Adapter        → emite pólizas sin acoplar a la API │
  │  DAO            → persiste entidades sin SQL directo │
  └──────────────────────────────────────────────────────┘

Principios SOLID:
  - SRP : RentalService solo coordina flujos de negocio.
  - OCP : Cambiar estrategia, DAO o seguro no lo modifica.
  - DIP : Recibe todas las dependencias por constructor (inyección).
"""
from vehicle_rental.data.models.entities   import Vehicle, Customer, Rental, RentalStatus
from vehicle_rental.data.dao.dao            import BaseDAO, InMemoryVehicleDAO, InMemoryCustomerDAO, InMemoryRentalDAO
from vehicle_rental.business.factory.vehicle_factory import get_factory
from vehicle_rental.business.pricing.pricing_strategy import PricingStrategy, DailyRateStrategy
from vehicle_rental.infrastructure.adapters.insurance_adapter import InsuranceService


class RentalService:
    """
    Servicio de dominio central.
    Recibe todas sus dependencias por inyección de constructor (DIP/SRP).
    """

    def __init__(
        self,
        vehicle_dao:   BaseDAO,
        customer_dao:  BaseDAO,
        rental_dao:    BaseDAO,
        insurance_svc: InsuranceService,
        pricing:       PricingStrategy = None,
    ):
        self._vehicle_dao   = vehicle_dao
        self._customer_dao  = customer_dao
        self._rental_dao    = rental_dao
        self._insurance_svc = insurance_svc
        self._pricing       = pricing or DailyRateStrategy()

    # ─────────────────────────────────────────
    # Strategy: cambio de estrategia en runtime
    # ─────────────────────────────────────────

    def set_pricing_strategy(self, strategy: PricingStrategy) -> None:
        """Intercambia la estrategia de precio en tiempo de ejecución."""
        self._pricing = strategy

    def current_pricing_strategy(self) -> str:
        """Retorna descripción de la estrategia activa."""
        return self._pricing.describe()

    # ─────────────────────────────────────────
    # Gestión de Vehículos (Factory Method + DAO)
    # ─────────────────────────────────────────

    def register_vehicle(
        self,
        vehicle_type: str,
        plate:        str,
        model:        str,
        year:         int,
        daily_rate:   float,
        **kwargs,
    ) -> Vehicle:
        """
        Crea un vehículo usando Factory Method y lo persiste con DAO.
        Lanza ValueError si la matrícula ya existe.
        """
        if self._vehicle_dao.find_by_id(plate.upper()):
            raise ValueError(f"Ya existe un vehículo con matrícula '{plate.upper()}'.")

        factory = get_factory(vehicle_type)
        vehicle = factory.register_and_create(plate, model, year, daily_rate, **kwargs)
        self._vehicle_dao.save(vehicle)
        return vehicle

    def get_vehicle(self, plate: str) -> Vehicle:
        vehicle = self._vehicle_dao.find_by_id(plate.upper())
        if not vehicle:
            raise ValueError(f"Vehículo '{plate}' no encontrado.")
        return vehicle

    def list_vehicles(self, only_available: bool = False) -> list[Vehicle]:
        if only_available:
            return self._vehicle_dao.find_available()
        return self._vehicle_dao.find_all()

    def remove_vehicle(self, plate: str) -> bool:
        """Elimina un vehículo si no tiene reservas activas."""
        rentals = self._rental_dao.find_active()
        in_use  = any(r.vehicle.plate == plate.upper() for r in rentals)
        if in_use:
            raise ValueError(f"El vehículo '{plate}' tiene una reserva activa y no puede eliminarse.")
        return self._vehicle_dao.delete(plate.upper())

    # ─────────────────────────────────────────
    # Gestión de Clientes (DAO)
    # ─────────────────────────────────────────

    def register_customer(self, name: str, email: str, license_no: str) -> Customer:
        """Registra un nuevo cliente. Lanza ValueError si el email ya existe."""
        if self._customer_dao.find_by_email(email):
            raise ValueError(f"Ya existe un cliente con el email '{email}'.")
        customer = Customer(name=name, email=email, license=license_no)
        self._customer_dao.save(customer)
        return customer

    def get_customer(self, customer_id: str) -> Customer:
        customer = self._customer_dao.find_by_id(customer_id.upper())
        if not customer:
            raise ValueError(f"Cliente '{customer_id}' no encontrado.")
        return customer

    def list_customers(self) -> list[Customer]:
        return self._customer_dao.find_all()

    # ─────────────────────────────────────────
    # Gestión de Reservas (Strategy + Adapter + DAO)
    # ─────────────────────────────────────────

    def create_rental(
        self,
        plate:       str,
        customer_id: str,
        days:        int,
        km_estimate: float,
    ) -> Rental:
        """
        Crea una reserva orquestando todos los patrones:
          1. DAO        → verifica vehículo y cliente
          2. Strategy   → calcula costo de alquiler
          3. Adapter    → emite póliza de seguro
          4. DAO        → persiste la reserva y actualiza vehículo
        """
        # 1. Validaciones via DAO
        vehicle  = self.get_vehicle(plate)
        customer = self.get_customer(customer_id)

        if not vehicle.available:
            raise ValueError(f"El vehículo '{plate}' no está disponible para alquiler.")
        if days <= 0:
            raise ValueError("La cantidad de días debe ser mayor a 0.")
        if km_estimate < 0:
            raise ValueError("La estimación de km no puede ser negativa.")

        # 2. Strategy: calcula costo
        cost = self._pricing.calculate(days, km_estimate, vehicle.daily_rate)

        # 3. Adapter: emite póliza de seguro (sin conocer la API externa)
        policy_id = self._insurance_svc.issue_policy(
            vehicle_id=vehicle.plate,
            customer_id=customer.id,
            days=days,
        )

        # 4. DAO: persiste
        rental           = Rental(
            vehicle      = vehicle,
            customer     = customer,
            days         = days,
            km_estimate  = km_estimate,
            cost         = cost,
            policy_id    = policy_id,
            pricing_type = self._pricing.describe(),
        )
        vehicle.available = False
        self._vehicle_dao.save(vehicle)
        self._rental_dao.save(rental)

        return rental

    def complete_rental(self, rental_id: str) -> Rental:
        """Marca una reserva como completada y libera el vehículo."""
        rental = self._rental_dao.find_by_id(rental_id.upper())
        if not rental:
            raise ValueError(f"Reserva '{rental_id}' no encontrada.")
        if rental.status != RentalStatus.ACTIVE:
            raise ValueError(f"La reserva '{rental_id}' ya no está activa.")

        rental.status            = RentalStatus.COMPLETED
        rental.vehicle.available = True
        self._vehicle_dao.save(rental.vehicle)
        self._rental_dao.save(rental)
        return rental

    def cancel_rental(self, rental_id: str) -> Rental:
        """Cancela una reserva activa y libera el vehículo."""
        rental = self._rental_dao.find_by_id(rental_id.upper())
        if not rental:
            raise ValueError(f"Reserva '{rental_id}' no encontrada.")
        if rental.status != RentalStatus.ACTIVE:
            raise ValueError(f"La reserva '{rental_id}' ya no está activa.")

        self._insurance_svc.cancel_policy(rental.policy_id)
        rental.status            = RentalStatus.CANCELLED
        rental.vehicle.available = True
        self._vehicle_dao.save(rental.vehicle)
        self._rental_dao.save(rental)
        return rental

    def list_rentals(self, only_active: bool = False) -> list[Rental]:
        if only_active:
            return self._rental_dao.find_active()
        return self._rental_dao.find_all()

    def get_customer_rentals(self, customer_id: str) -> list[Rental]:
        self.get_customer(customer_id)   # valida que existe
        return self._rental_dao.find_by_customer(customer_id.upper())

    # ─────────────────────────────────────────
    # Cálculo de cotización (sin crear reserva)
    # ─────────────────────────────────────────

    def quote(self, plate: str, days: int, km_estimate: float) -> float:
        """Calcula el costo estimado sin crear ninguna reserva."""
        vehicle = self.get_vehicle(plate)
        return self._pricing.calculate(days, km_estimate, vehicle.daily_rate)
