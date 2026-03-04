"""
Capa de Infraestructura → Patrón Adapter
Traduce la interfaz del servicio externo de seguros a la interfaz
interna que espera la capa de negocio.

Principios SOLID aplicados:
  - OCP : Cambiar de proveedor de seguros solo requiere un nuevo Adapter.
  - DIP : La capa de negocio depende de InsuranceService (abstracción),
          nunca de ExternalInsuranceAPI (detalle).
  - ISP : InsuranceService expone solo lo necesario: issue_policy().
"""
from abc import ABC, abstractmethod
from datetime import datetime
import random
import string


# ─────────────────────────────────────────────
# Interfaz interna esperada por la capa de negocio (DIP)
# ─────────────────────────────────────────────

class InsuranceService(ABC):
    """
    Contrato que la capa de negocio conoce.
    Cualquier proveedor de seguros debe implementar esta interfaz.
    """

    @abstractmethod
    def issue_policy(
        self,
        vehicle_id:  str,
        customer_id: str,
        days:        int,
    ) -> str:
        """
        Emite una póliza de seguro.
        Retorna el identificador único de la póliza.
        """
        ...

    @abstractmethod
    def cancel_policy(self, policy_id: str) -> bool:
        """Cancela una póliza activa. Retorna True si tuvo éxito."""
        ...


# ─────────────────────────────────────────────
# API Externa simulada (Adaptee)
# Interfaz incompatible con InsuranceService
# ─────────────────────────────────────────────

class ExternalInsuranceAPI:
    """
    Simula una API REST externa de seguros con firma diferente.
    Su interfaz NO coincide con lo que necesita RentalService.
    """

    def create_insurance(self, payload: dict) -> dict:
        """
        Espera un dict con: vehicle_plate, holder_id, duration_days.
        Retorna un dict con policy_number, status, premium.
        """
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        premium = payload["duration_days"] * 8.50
        return {
            "policy_number": f"EXT-{payload['vehicle_plate']}-{suffix}",
            "status":        "APPROVED",
            "premium":       round(premium, 2),
            "issued_at":     datetime.now().isoformat(),
        }

    def void_insurance(self, policy_number: str) -> dict:
        """
        Cancela una póliza en el sistema externo.
        Retorna dict con status y message.
        """
        return {
            "policy_number": policy_number,
            "status":        "VOIDED",
            "message":       "Policy cancelled successfully.",
        }


class ExternalInsuranceAPIv2:
    """
    Simula una segunda versión de la API externa con otra firma.
    Demuestra que el Adapter puede envolver cualquier implementación.
    """

    def request_coverage(self, vehicle: str, client: str, days: int) -> str:
        suffix = "".join(random.choices(string.digits, k=8))
        return f"V2-{vehicle}-{client[:4].upper()}-{suffix}"

    def revoke_coverage(self, coverage_id: str) -> bool:
        return True


# ─────────────────────────────────────────────
# Adapter concreto para ExternalInsuranceAPI (v1)
# ─────────────────────────────────────────────

class InsuranceAdapterV1(InsuranceService):
    """
    Adapter que envuelve ExternalInsuranceAPI (v1).
    Traduce issue_policy() → create_insurance()
    y cancel_policy() → void_insurance().
    """

    def __init__(self):
        self._api = ExternalInsuranceAPI()   # Envuelve el adaptee

    def issue_policy(self, vehicle_id: str, customer_id: str, days: int) -> str:
        # Traduce la interfaz interna a la del adaptee
        payload = {
            "vehicle_plate": vehicle_id,
            "holder_id":     customer_id,
            "duration_days": days,
        }
        result = self._api.create_insurance(payload)
        return result["policy_number"]

    def cancel_policy(self, policy_id: str) -> bool:
        result = self._api.void_insurance(policy_id)
        return result["status"] == "VOIDED"


# ─────────────────────────────────────────────
# Adapter concreto para ExternalInsuranceAPIv2
# ─────────────────────────────────────────────

class InsuranceAdapterV2(InsuranceService):
    """
    Adapter que envuelve ExternalInsuranceAPIv2.
    Mismo contrato, diferente implementación interna.
    """

    def __init__(self):
        self._api = ExternalInsuranceAPIv2()

    def issue_policy(self, vehicle_id: str, customer_id: str, days: int) -> str:
        return self._api.request_coverage(vehicle_id, customer_id, days)

    def cancel_policy(self, policy_id: str) -> bool:
        return self._api.revoke_coverage(policy_id)
