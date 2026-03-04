"""
Capa de Presentación → CLI Interactivo
Menú de consola que interactúa con la capa de negocio (RentalService).
No contiene lógica de dominio: solo llama al servicio y muestra resultados.

Principios SOLID:
  - SRP : Solo responsable de entrada/salida con el usuario.
  - DIP : Depende de RentalService (abstracción del negocio), no de DAOs o adapters.
"""
import os
import sys
from vehicle_rental.business.service.rental_service  import RentalService
from vehicle_rental.business.pricing.pricing_strategy import get_available_strategies


# ─────────────────────────────────────────────
# Utilidades de presentación
# ─────────────────────────────────────────────

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def line(char="─", width=60):
    print(char * width)


def header(title: str):
    clear()
    line("═")
    print(f"  🚗  SISTEMA DE ALQUILER DE VEHÍCULOS")
    line("═")
    print(f"  {title}")
    line()
    print()


def success(msg: str):
    print(f"\n  ✅  {msg}")


def error(msg: str):
    print(f"\n  ❌  {msg}")


def info(msg: str):
    print(f"  ℹ️   {msg}")


def wait():
    input("\n  Presiona ENTER para continuar...")


def ask(prompt: str, allow_empty: bool = False) -> str:
    while True:
        value = input(f"  {prompt}: ").strip()
        if value or allow_empty:
            return value
        print("  ⚠️  Este campo no puede estar vacío.")


def ask_float(prompt: str, minimum: float = 0.0) -> float:
    while True:
        try:
            value = float(ask(prompt))
            if value < minimum:
                print(f"  ⚠️  El valor mínimo es {minimum}.")
            else:
                return value
        except ValueError:
            print("  ⚠️  Ingresa un número válido.")


def ask_int(prompt: str, minimum: int = 1) -> int:
    while True:
        try:
            value = int(ask(prompt))
            if value < minimum:
                print(f"  ⚠️  El valor mínimo es {minimum}.")
            else:
                return value
        except ValueError:
            print("  ⚠️  Ingresa un número entero válido.")


def choose(options: list[str], prompt: str = "Elige una opción") -> str:
    """Muestra un menú numerado y retorna la opción elegida."""
    for i, opt in enumerate(options, 1):
        print(f"  [{i}] {opt}")
    while True:
        raw = ask(prompt)
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return raw
        print(f"  ⚠️  Opción inválida (1–{len(options)}).")


# ─────────────────────────────────────────────
# Vistas de entidades
# ─────────────────────────────────────────────

def show_vehicles(vehicles):
    if not vehicles:
        info("No hay vehículos para mostrar.")
        return
    print()
    for v in vehicles:
        estado = "🟢 Disponible" if v.available else "🔴 No disponible"
        print(f"  {'─'*54}")
        print(f"  Matrícula : {v.plate:<12}  Tipo: {v.vehicle_type.value}")
        print(f"  Modelo    : {v.year} {v.model}")
        print(f"  Tarifa    : ${v.daily_rate:.2f}/día     Estado: {estado}")
    print(f"  {'─'*54}")


def show_customers(customers):
    if not customers:
        info("No hay clientes registrados.")
        return
    print()
    for c in customers:
        print(f"  {'─'*54}")
        print(f"  ID      : {c.id}")
        print(f"  Nombre  : {c.name}")
        print(f"  Email   : {c.email}")
        print(f"  Licencia: {c.license}")
    print(f"  {'─'*54}")


def show_rentals(rentals):
    if not rentals:
        info("No hay reservas para mostrar.")
        return
    print()
    for r in rentals:
        icon = {"Activa": "🟡", "Completada": "🟢", "Cancelada": "🔴"}.get(r.status.value, "⚪")
        print(f"  {'─'*54}")
        print(f"  ID Reserva : {r.id}  {icon} {r.status.value}")
        print(f"  Vehículo   : {r.vehicle.model} ({r.vehicle.plate})")
        print(f"  Cliente    : {r.customer.name} ({r.customer.id})")
        print(f"  Días / km  : {r.days} días | {r.km_estimate:.0f} km estimados")
        print(f"  Costo      : ${r.cost:.2f}  ({r.pricing_type})")
        print(f"  Póliza     : {r.policy_id}")
        print(f"  Inicio     : {r.start_date}  →  Fin: {r.end_date()}")
    print(f"  {'─'*54}")


# ─────────────────────────────────────────────
# Submenús
# ─────────────────────────────────────────────

def menu_vehicles(service: RentalService):
    while True:
        header("GESTIÓN DE VEHÍCULOS")
        opt = choose([
            "Registrar nuevo vehículo",
            "Ver todos los vehículos",
            "Ver vehículos disponibles",
            "Eliminar vehículo",
            "← Volver al menú principal",
        ])
        if opt == "1":
            header("REGISTRAR VEHÍCULO")
            print("  Tipo de vehículo:")
            v_type = choose(["Automóvil (car)", "Camioneta (truck)", "SUV (suv)"])
            type_map = {"1": "car", "2": "truck", "3": "suv"}
            try:
                vehicle = service.register_vehicle(
                    vehicle_type = type_map[v_type],
                    plate        = ask("Matrícula (ej. ABC-123)"),
                    model        = ask("Marca y modelo (ej. Toyota Corolla)"),
                    year         = ask_int("Año (2000–2025)", minimum=2000),
                    daily_rate   = ask_float("Tarifa diaria ($)", minimum=1.0),
                )
                success(f"Vehículo registrado: {vehicle}")
            except (ValueError, KeyError) as e:
                error(str(e))
            wait()

        elif opt == "2":
            header("TODOS LOS VEHÍCULOS")
            show_vehicles(service.list_vehicles())
            wait()

        elif opt == "3":
            header("VEHÍCULOS DISPONIBLES")
            show_vehicles(service.list_vehicles(only_available=True))
            wait()

        elif opt == "4":
            header("ELIMINAR VEHÍCULO")
            show_vehicles(service.list_vehicles())
            plate = ask("Matrícula a eliminar")
            try:
                removed = service.remove_vehicle(plate)
                if removed:
                    success(f"Vehículo '{plate.upper()}' eliminado.")
                else:
                    error("Vehículo no encontrado.")
            except ValueError as e:
                error(str(e))
            wait()

        elif opt == "5":
            break


def menu_customers(service: RentalService):
    while True:
        header("GESTIÓN DE CLIENTES")
        opt = choose([
            "Registrar nuevo cliente",
            "Ver todos los clientes",
            "Ver reservas de un cliente",
            "← Volver al menú principal",
        ])
        if opt == "1":
            header("REGISTRAR CLIENTE")
            try:
                customer = service.register_customer(
                    name       = ask("Nombre completo"),
                    email      = ask("Correo electrónico"),
                    license_no = ask("Número de licencia"),
                )
                success(f"Cliente registrado: {customer}")
            except ValueError as e:
                error(str(e))
            wait()

        elif opt == "2":
            header("TODOS LOS CLIENTES")
            show_customers(service.list_customers())
            wait()

        elif opt == "3":
            header("RESERVAS POR CLIENTE")
            show_customers(service.list_customers())
            cid = ask("ID del cliente")
            try:
                rentals = service.get_customer_rentals(cid)
                show_rentals(rentals)
            except ValueError as e:
                error(str(e))
            wait()

        elif opt == "4":
            break


def menu_pricing(service: RentalService):
    header("ESTRATEGIA DE PRECIO")
    info(f"Estrategia actual: {service.current_pricing_strategy()}")
    print()
    strategies = get_available_strategies()
    print("  Estrategias disponibles:")
    for key, strat in strategies.items():
        print(f"  [{key}] {strat.describe()}")
    print()
    opt = ask("Elige estrategia (1–4) o ENTER para cancelar", allow_empty=True)
    if opt in strategies:
        service.set_pricing_strategy(strategies[opt])
        success(f"Estrategia cambiada a: {strategies[opt].describe()}")
    elif opt == "":
        info("Sin cambios.")
    else:
        error("Opción inválida.")
    wait()


def menu_rentals(service: RentalService):
    while True:
        header("GESTIÓN DE RESERVAS")
        info(f"Estrategia de precio activa: {service.current_pricing_strategy()}")
        print()
        opt = choose([
            "Crear nueva reserva",
            "Ver todas las reservas",
            "Ver reservas activas",
            "Completar reserva",
            "Cancelar reserva",
            "Cotizar reserva (sin crear)",
            "← Volver al menú principal",
        ])

        if opt == "1":
            header("CREAR RESERVA")
            print("  Vehículos disponibles:")
            show_vehicles(service.list_vehicles(only_available=True))
            print()
            print("  Clientes registrados:")
            show_customers(service.list_customers())
            print()
            try:
                plate       = ask("Matrícula del vehículo")
                customer_id = ask("ID del cliente")
                days        = ask_int("Cantidad de días")
                km          = ask_float("Kilómetros estimados", minimum=0)
                print()
                # Mostrar cotización previa
                quote = service.quote(plate, days, km)
                info(f"Costo estimado: ${quote:.2f}  ({service.current_pricing_strategy()})")
                confirm = ask("¿Confirmar reserva? (s/n)").lower()
                if confirm == "s":
                    rental = service.create_rental(plate, customer_id, days, km)
                    print()
                    success("Reserva creada exitosamente:")
                    show_rentals([rental])
                else:
                    info("Reserva cancelada.")
            except ValueError as e:
                error(str(e))
            wait()

        elif opt == "2":
            header("TODAS LAS RESERVAS")
            show_rentals(service.list_rentals())
            wait()

        elif opt == "3":
            header("RESERVAS ACTIVAS")
            show_rentals(service.list_rentals(only_active=True))
            wait()

        elif opt == "4":
            header("COMPLETAR RESERVA")
            show_rentals(service.list_rentals(only_active=True))
            rid = ask("ID de la reserva a completar")
            try:
                rental = service.complete_rental(rid)
                success(f"Reserva '{rental.id}' completada. Vehículo liberado.")
            except ValueError as e:
                error(str(e))
            wait()

        elif opt == "5":
            header("CANCELAR RESERVA")
            show_rentals(service.list_rentals(only_active=True))
            rid = ask("ID de la reserva a cancelar")
            try:
                rental = service.cancel_rental(rid)
                success(f"Reserva '{rental.id}' cancelada. Póliza anulada.")
            except ValueError as e:
                error(str(e))
            wait()

        elif opt == "6":
            header("COTIZAR RESERVA")
            show_vehicles(service.list_vehicles(only_available=True))
            try:
                plate = ask("Matrícula del vehículo")
                days  = ask_int("Cantidad de días")
                km    = ask_float("Kilómetros estimados", minimum=0)
                quote = service.quote(plate, days, km)
                print()
                info(f"Estrategia : {service.current_pricing_strategy()}")
                info(f"Costo total: ${quote:.2f}")
            except ValueError as e:
                error(str(e))
            wait()

        elif opt == "7":
            break


# ─────────────────────────────────────────────
# Menú principal
# ─────────────────────────────────────────────

def main_menu(service: RentalService):
    while True:
        header("MENÚ PRINCIPAL")
        info(f"Estrategia activa : {service.current_pricing_strategy()}")
        info(f"Vehículos totales  : {len(service.list_vehicles())}")
        info(f"Clientes registrados: {len(service.list_customers())}")
        info(f"Reservas activas   : {len(service.list_rentals(only_active=True))}")
        print()
        opt = choose([
            "Gestión de Vehículos",
            "Gestión de Clientes",
            "Gestión de Reservas",
            "Cambiar Estrategia de Precio",
            "Salir",
        ])
        if opt == "1":
            menu_vehicles(service)
        elif opt == "2":
            menu_customers(service)
        elif opt == "3":
            menu_rentals(service)
        elif opt == "4":
            menu_pricing(service)
        elif opt == "5":
            clear()
            print("\n  ¡Hasta pronto! 👋\n")
            sys.exit(0)
