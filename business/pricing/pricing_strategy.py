"""
Capa de Negocio → Patrón Strategy
Encapsula los algoritmos de cálculo de tarifa en clases separadas,
haciéndolos intercambiables en tiempo de ejecución.

Principios SOLID aplicados:
  - OCP : Agregar una nueva estrategia (ej. WeekendStrategy) no modifica ninguna existente.
  - LSP : Todas las estrategias son sustituibles sin alterar el comportamiento del servicio.
  - ISP : PricingStrategy solo expone calculate() y describe(). Nada innecesario.
"""
from abc import ABC, abstractmethod


# ─────────────────────────────────────────────
# Interfaz Strategy (contrato)
# ─────────────────────────────────────────────

class PricingStrategy(ABC):
    """
    Interfaz del patrón Strategy para cálculo de tarifas.
    Toda estrategia debe implementar calculate() y describe().
    """

    @abstractmethod
    def calculate(self, days: int, km: float, daily_rate: float) -> float:
        """
        Calcula el costo total del alquiler.

        Args:
            days:       Número de días del alquiler.
            km:         Kilómetros estimados a recorrer.
            daily_rate: Tarifa base diaria del vehículo.
        Returns:
            Costo total en la moneda del sistema.
        """
        ...

    @abstractmethod
    def describe(self) -> str:
        """Descripción legible de la estrategia activa."""
        ...


# ─────────────────────────────────────────────
# Estrategias concretas
# ─────────────────────────────────────────────

class DailyRateStrategy(PricingStrategy):
    """
    Estrategia: tarifa fija por día.
    Costo = daily_rate × days
    Ideal para alquileres cortos de duración conocida.
    """

    def calculate(self, days: int, km: float, daily_rate: float) -> float:
        return round(daily_rate * days, 2)

    def describe(self) -> str:
        return "Por día (tarifa_diaria × días)"


class KmRateStrategy(PricingStrategy):
    """
    Estrategia: tarifa por kilómetro recorrido.
    Costo = rate_per_km × km
    Ideal para trayectos de distancia variable.
    """

    def __init__(self, rate_per_km: float = 0.35):
        if rate_per_km <= 0:
            raise ValueError("La tarifa por km debe ser mayor a 0.")
        self._rate = rate_per_km

    def calculate(self, days: int, km: float, daily_rate: float) -> float:
        return round(self._rate * km, 2)

    def describe(self) -> str:
        return f"Por kilómetro (${self._rate:.2f}/km × km_estimados)"


class FlatRateStrategy(PricingStrategy):
    """
    Estrategia: tarifa plana fija independiente de días o km.
    Costo = flat_fee
    Ideal para paquetes promocionales o alquileres especiales.
    """

    def __init__(self, flat_fee: float):
        if flat_fee <= 0:
            raise ValueError("La tarifa plana debe ser mayor a 0.")
        self._fee = flat_fee

    def calculate(self, days: int, km: float, daily_rate: float) -> float:
        return round(self._fee, 2)

    def describe(self) -> str:
        return f"Tarifa plana fija (${self._fee:.2f})"


class WeeklyDiscountStrategy(PricingStrategy):
    """
    Estrategia: tarifa diaria con descuento semanal.
    Semanas completas pagan con descuento; días sueltos a tarifa normal.
    Costo = (semanas × 7 × daily_rate × descuento) + (días_extra × daily_rate)
    """

    def __init__(self, discount_pct: float = 0.15):
        """
        Args:
            discount_pct: Porcentaje de descuento para semanas completas (0.0–1.0).
        """
        if not 0 < discount_pct < 1:
            raise ValueError("El descuento debe estar entre 0 y 1.")
        self._discount = discount_pct

    def calculate(self, days: int, km: float, daily_rate: float) -> float:
        weeks      = days // 7
        extra_days = days %  7
        weekly_cost = weeks * 7 * daily_rate * (1 - self._discount)
        extra_cost  = extra_days * daily_rate
        return round(weekly_cost + extra_cost, 2)

    def describe(self) -> str:
        pct = int(self._discount * 100)
        return f"Semanal con {pct}% de descuento en semanas completas"


# ─────────────────────────────────────────────
# Catálogo de estrategias disponibles
# ─────────────────────────────────────────────

def get_available_strategies() -> dict[str, PricingStrategy]:
    """Retorna el catálogo de estrategias listas para usar."""
    return {
        "1": DailyRateStrategy(),
        "2": KmRateStrategy(rate_per_km=0.35),
        "3": FlatRateStrategy(flat_fee=199.99),
        "4": WeeklyDiscountStrategy(discount_pct=0.15),
    }
