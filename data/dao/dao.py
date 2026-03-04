"""
Capa de Datos → Patrón DAO
Abstrae el acceso a datos. La capa de negocio solo conoce las interfaces.

Principios SOLID aplicados:
  - SRP : Cada DAO tiene una única responsabilidad (persistir una entidad).
  - OCP : Agregar nueva persistencia (SQLite, Postgres) no modifica las interfaces.
  - DIP : RentalService depende de BaseDAO, no de implementaciones concretas.
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional

from vehicle_rental.data.models.entities import Vehicle, Customer, Rental, RentalStatus

T = TypeVar("T")


# ─────────────────────────────────────────────
# Interfaz genérica DAO (DIP)
# ─────────────────────────────────────────────

class BaseDAO(ABC, Generic[T]):
    """
    Interfaz genérica del patrón DAO.
    Define el contrato CRUD que toda implementación debe cumplir.
    """

    @abstractmethod
    def save(self, entity: T) -> None:
        """Persiste o actualiza una entidad."""
        ...

    @abstractmethod
    def find_by_id(self, entity_id: str) -> Optional[T]:
        """Busca una entidad por su identificador único."""
        ...

    @abstractmethod
    def find_all(self) -> list[T]:
        """Retorna todas las entidades almacenadas."""
        ...

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Elimina una entidad. Retorna True si existía."""
        ...


# ─────────────────────────────────────────────
# Implementaciones en memoria (OCP: intercambiables)
# ─────────────────────────────────────────────

class InMemoryVehicleDAO(BaseDAO[Vehicle]):
    """
    Implementación en memoria del DAO de vehículos.
    Clave primaria: plate (matrícula).
    """

    def __init__(self):
        self._store: dict[str, Vehicle] = {}

    def save(self, entity: Vehicle) -> None:
        self._store[entity.plate] = entity

    def find_by_id(self, entity_id: str) -> Optional[Vehicle]:
        return self._store.get(entity_id)

    def find_all(self) -> list[Vehicle]:
        return list(self._store.values())

    def delete(self, entity_id: str) -> bool:
        if entity_id in self._store:
            del self._store[entity_id]
            return True
        return False

    # Consulta adicional específica del dominio
    def find_available(self) -> list[Vehicle]:
        """Retorna solo los vehículos disponibles para alquiler."""
        return [v for v in self._store.values() if v.available]

    def find_by_type(self, vehicle_type) -> list[Vehicle]:
        """Filtra vehículos por tipo."""
        return [v for v in self._store.values() if v.vehicle_type == vehicle_type]


class InMemoryCustomerDAO(BaseDAO[Customer]):
    """
    Implementación en memoria del DAO de clientes.
    Clave primaria: customer.id (UUID corto).
    """

    def __init__(self):
        self._store: dict[str, Customer] = {}

    def save(self, entity: Customer) -> None:
        self._store[entity.id] = entity

    def find_by_id(self, entity_id: str) -> Optional[Customer]:
        return self._store.get(entity_id)

    def find_all(self) -> list[Customer]:
        return list(self._store.values())

    def delete(self, entity_id: str) -> bool:
        if entity_id in self._store:
            del self._store[entity_id]
            return True
        return False

    def find_by_email(self, email: str) -> Optional[Customer]:
        """Búsqueda por email (único)."""
        return next((c for c in self._store.values() if c.email == email), None)


class InMemoryRentalDAO(BaseDAO[Rental]):
    """
    Implementación en memoria del DAO de reservas.
    Clave primaria: rental.id (UUID corto).
    """

    def __init__(self):
        self._store: dict[str, Rental] = {}

    def save(self, entity: Rental) -> None:
        self._store[entity.id] = entity

    def find_by_id(self, entity_id: str) -> Optional[Rental]:
        return self._store.get(entity_id)

    def find_all(self) -> list[Rental]:
        return list(self._store.values())

    def delete(self, entity_id: str) -> bool:
        if entity_id in self._store:
            del self._store[entity_id]
            return True
        return False

    def find_by_customer(self, customer_id: str) -> list[Rental]:
        """Retorna todas las reservas de un cliente."""
        return [r for r in self._store.values() if r.customer.id == customer_id]

    def find_active(self) -> list[Rental]:
        """Retorna solo las reservas activas."""
        return [r for r in self._store.values() if r.status == RentalStatus.ACTIVE]
