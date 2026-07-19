# ================================================================
# SISTEMA EXPERTO: Diagnóstico de PC
# Implementación con motor de inferencia hacia adelante
# Python puro — sin librerías externas
# ================================================================

import json

# ──────────────────────────────────────────────────────────────
# COMPONENTE 1: BASE DE CONOCIMIENTO
# Aquí vive el conocimiento del experto técnico.
# Cada regla tiene: id, descripción, condiciones (lista de síntomas
# requeridos, unidas por AND), conclusión y factor de confianza.
# ──────────────────────────────────────────────────────────────

BASE_DE_CONOCIMIENTO = [
    {
        "id": "R01",
        "descripcion": "Fuente de poder dañada",
        "condiciones": ["no_enciende", "sin_luces", "sin_sonido"],
        "conclusion": "Revisar o reemplazar la fuente de poder",
        "confianza": 0.92
    },
    {
        "id": "R02",
        "descripcion": "Falla de RAM",
        "condiciones": ["enciende", "pitidos_arranque", "sin_video"],
        "conclusion": "Probar con módulos de RAM de a uno",
        "confianza": 0.88
    },
    {
        "id": "R03",
        "descripcion": "Falla de tarjeta de video",
        "condiciones": ["enciende", "pantalla_negra", "sin_pitidos"],
        "conclusion": "Revisar tarjeta de video y conexiones del monitor",
        "confianza": 0.80
    },
    {
        "id": "R04",
        "descripcion": "Problemas de almacenamiento",
        "condiciones": ["enciende", "inicia_lento", "disco_al_100"],
        "conclusion": "Verificar salud del disco duro con herramienta SMART",
        "confianza": 0.85
    },
    {
        "id": "R05",
        "descripcion": "Infección por malware",
        "condiciones": ["enciende", "inicia_lento", "ventilador_siempre_activo"],
        "conclusion": "Escanear con antivirus y revisar procesos en segundo plano",
        "confianza": 0.72
    },
    {
        "id": "R06",
        "descripcion": "Driver o RAM dañada",
        "condiciones": ["enciende", "pantalla_azul_frecuente"],
        "conclusion": "Actualizar drivers y testear memoria RAM con MemTest86",
        "confianza": 0.87
    },
    {
        "id": "R07",
        "descripcion": "Sobrecalentamiento",
        "condiciones": ["enciende", "se_apaga_solo", "calor_excesivo"],
        "conclusion": "Limpiar ventiladores y reaplicar pasta térmica",
        "confianza": 0.90
    },
    # ── NIVEL 1: Tres reglas nuevas ─────────────────────────────
    {
        "id": "R08",
        "descripcion": "Problema de conectividad de red",
        "condiciones": ["no_internet", "otros_dispositivos_si_internet", "icono_red_con_x"],
        "conclusion": "Revisar adaptador de red, controladores o reiniciar router",
        "confianza": 0.82
    },
    {
        "id": "R09",
        "descripcion": "Periférico USB con falla",
        "condiciones": ["periferico_no_responde", "cambiar_puerto_funciona"],
        "conclusion": "Probar otro puerto USB, limpiar conectores o reemplazar cable",
        "confianza": 0.78
    },
    {
        "id": "R10",
        "descripcion": "Batería o cargador de laptop dañado",
        "condiciones": ["portatil", "no_carga", "cargador_conectado_sin_luz"],
        "conclusion": "Revisar batería, conector de carga o reemplazar cargador",
        "confianza": 0.84
    },
]


# ──────────────────────────────────────────────────────────────
# COMPONENTE 2: BASE DE HECHOS (Working Memory)
# Estado actual del caso. Usamos un set de Python para
# representar los síntomas presentes (eficiente para búsqueda).
# ──────────────────────────────────────────────────────────────

# Diccionario de preguntas asociadas a cada síntoma.
PREGUNTAS = {
    "no_enciende":                  "¿El equipo NO enciende (sin luces, sin sonido)?",
    "sin_luces":                    "¿No hay ninguna luz LED encendida?",
    "sin_sonido":                   "¿No se escucha ningún sonido al encender?",
    "enciende":                     "¿El equipo SÍ enciende (hay luces y/o sonido)?",
    "pitidos_arranque":             "¿Se escuchan pitidos (beeps) al encender?",
    "sin_video":                    "¿La pantalla no muestra absolutamente nada?",
    "pantalla_negra":               "¿La pantalla queda en negro (sin pitidos)?",
    "sin_pitidos":                  "¿No se escuchan pitidos?",
    "inicia_lento":                 "¿El equipo tarda más de 3 minutos en iniciar?",
    "disco_al_100":                 "¿El administrador de tareas muestra disco al 100%?",
    "ventilador_siempre_activo":    "¿El ventilador está siempre a máxima velocidad?",
    "pantalla_azul_frecuente":      "¿Aparece pantalla azul (BSOD) con frecuencia?",
    "se_apaga_solo":                "¿El equipo se apaga solo sin advertencia?",
    "calor_excesivo":               "¿El chasis está muy caliente al tacto?",
    # Preguntas para las reglas nuevas
    "no_internet":                  "¿No tienes conexión a Internet en este equipo?",
    "otros_dispositivos_si_internet": "¿Otros dispositivos SÍ tienen Internet en la misma red?",
    "icono_red_con_x":              "¿Aparece el icono de red con una X o triángulo amarillo?",
    "periferico_no_responde":       "¿Algún teclado, mouse o periférico no responde?",
    "cambiar_puerto_funciona":      "¿Funciona si lo conectas a otro puerto USB?",
    "portatil":                     "¿Es una computadora portátil (laptop)?",
    "no_carga":                     "¿La batería no carga o no mantiene carga?",
    "cargador_conectado_sin_luz":   "¿El cargador está conectado pero el LED no enciende?",
}


def crear_base_de_hechos():
    """Crea una base de hechos vacía (un conjunto)."""
    return set()


# ──────────────────────────────────────────────────────────────
# COMPONENTE 3: MOTOR DE INFERENCIA
# Funciones de equiparación y resolución de conflictos
# ──────────────────────────────────────────────────────────────

def equiparar(base_conocimiento, hechos):
    """
    Proceso de equiparación (pattern matching).
    Retorna todas las reglas cuyas condiciones están satisfechas
    por los hechos actuales. Es el 'conflict set'.
    """
    conflict_set = []
    for regla in base_conocimiento:
        if set(regla['condiciones']).issubset(hechos):
            conflict_set.append(regla)
    return conflict_set


def resolver_conflictos(conflict_set):
    """
    Estrategia de resolución de conflictos:
    1. Mayor confianza.
    2. Si hay empate, preferir la regla con más condiciones (más específica).
    Retorna una única regla o None.
    """
    if not conflict_set:
        return None
    return max(
        conflict_set,
        key=lambda r: (r['confianza'], len(r['condiciones']))
    )


def diagnosticos_ordenados(conflict_set):
    """
    NIVEL 2: retorna TODOS los diagnósticos aplicables ordenados
    por confianza descendente y, en caso de empate, por cantidad
    de condiciones (mayor especificidad primero).
    """
    return sorted(
        conflict_set,
        key=lambda r: (r['confianza'], len(r['condiciones'])),
        reverse=True
    )


def inferir(base_conocimiento, hechos, modo_ranking=False):
    """
    Motor de inferencia principal.
    Ejecuta el ciclo de equiparación -> resolución -> ejecución.

    Si modo_ranking=True, muestra el ranking completo de diagnósticos
    posibles (Nivel 2). Si es False, muestra solo el de mayor confianza
    (comportamiento original).
    """
    print()
    print('━' * 60)
    print('  MOTOR DE INFERENCIA INICIADO')
    print('━' * 60)
    print(f'  Hechos ingresados: {sorted(hechos)}')
    print()

    conflict_set = equiparar(base_conocimiento, hechos)

    if not conflict_set:
        print('  ⚠ No se encontraron reglas aplicables.')
        print('  Considera agregar más síntomas o revisar la base de conocimiento.')
        return

    print(f'  Reglas que aplican (conflict set): {[r["id"] for r in conflict_set]}')
    print()

    if modo_ranking:
        ranking = diagnosticos_ordenados(conflict_set)
        print('  RANKING DE DIAGNÓSTICOS')
        print('  ──────────────────────────────────────────────────────')
        for i, regla in enumerate(ranking, 1):
            print(f'  {i}. {regla["id"]} — {regla["descripcion"]}')
            print(f'     Recomendación: {regla["conclusion"]}')
            print(f'     Confianza: {regla["confianza"] * 100:.0f}%')
            print(f'     Síntomas activadores: {regla["condiciones"]}')
            print()
        mejor = ranking[0]
    else:
        mejor = resolver_conflictos(conflict_set)
        print('  DIAGNÓSTICO PRINCIPAL')
        print('  ──────────────────────────────────────────────────────')
        print(f'  Regla aplicada: {mejor["id"]} — {mejor["descripcion"]}')
        print(f'  Recomendación:  {mejor["conclusion"]}')
        print(f'  Confianza:      {mejor["confianza"] * 100:.0f}%')
        print()

    # COMPONENTE 4: INTERFAZ DE EXPLICACIÓN
    print('  TRAZABILIDAD DEL RAZONAMIENTO')
    print('  ──────────────────────────────────────────────────────')
    if not modo_ranking:
        print(f'  Síntomas que activaron la regla: {mejor["condiciones"]}')
    if len(conflict_set) > 1:
        descartadas = [r['id'] for r in conflict_set if r['id'] != mejor['id']]
        print(f'  Reglas descartadas o en competencia: {descartadas}')
    print('━' * 60)


# ──────────────────────────────────────────────────────────────
# NIVEL 3: ENCADENAMIENTO HACIA ATRÁS
# ──────────────────────────────────────────────────────────────

def backward_chain(meta, base_conocimiento, hechos, visitados=None):
    """
    Dado un diagnóstico (meta), determina recursivamente qué síntomas
    habría que confirmar para llegar a esa conclusión.

    - Si la meta ya es un hecho confirmado, se considera satisfecha.
    - Si existe una regla cuya conclusión es la meta, se explora cada
      condición como una submeta.
    - Si no existe regla para la meta, es un síntoma que debe preguntarse
      al usuario.
    """
    if visitados is None:
        visitados = set()

    if meta in hechos:
        return {"tipo": "hecho", "nombre": meta, "satisfecho": True}

    if meta in visitados:
        return {"tipo": "ciclo", "nombre": meta}

    visitados.add(meta)

    for regla in base_conocimiento:
        if regla["conclusion"] == meta:
            requisitos = []
            for cond in regla["condiciones"]:
                requisitos.append(
                    backward_chain(cond, base_conocimiento, hechos, set(visitados))
                )
            return {
                "tipo": "regla",
                "regla_id": regla["id"],
                "meta": meta,
                "necesita": requisitos
            }

    return {"tipo": "pregunta", "nombre": meta, "satisfecho": False}


def imprimir_arbol_backward(nodo, nivel=0):
    """Imprime de forma legible el árbol generado por backward_chain."""
    indent = "  " * nivel
    tipo = nodo.get("tipo")
    nombre = nodo.get("nombre", nodo.get("meta", ""))

    if tipo == "hecho":
        print(f"{indent}✓ {nombre} (confirmado)")
    elif tipo == "pregunta":
        pregunta = PREGUNTAS.get(nombre, f"¿El síntoma '{nombre}' está presente?")
        print(f"{indent}? {pregunta}  -> {nombre}")
    elif tipo == "regla":
        regla_id = nodo.get("regla_id", "")
        print(f"{indent}▶ Para concluir '{nodo.get('meta')}' se aplica {regla_id}:")
        for hijo in nodo.get("necesita", []):
            imprimir_arbol_backward(hijo, nivel + 1)
    elif tipo == "ciclo":
        print(f"{indent}⚠ Ciclo detectado en '{nombre}'")


# ──────────────────────────────────────────────────────────────
# NIVEL 4: EXPORTAR RED DE INFERENCIA
# ──────────────────────────────────────────────────────────────

def exportar_red(base_conocimiento):
    """
    Recorre la base de conocimiento y genera un diccionario Python
    que representa el grafo de inferencia: nodos (hechos y conclusiones)
    y aristas (condiciones -> conclusión, etiquetadas por regla).
    """
    nodos = set()
    aristas = []

    for regla in base_conocimiento:
        for cond in regla["condiciones"]:
            nodos.add(cond)
            aristas.append({
                "desde": cond,
                "hacia": regla["conclusion"],
                "regla": regla["id"]
            })
        nodos.add(regla["conclusion"])

    return {
        "nodos": sorted(nodos),
        "aristas": aristas
    }


# ──────────────────────────────────────────────────────────────
# COMPONENTE 5: INTERFAZ DE USUARIO
# ──────────────────────────────────────────────────────────────

def consultar(base_conocimiento, preguntas):
    """
    Interactúa con el usuario preguntando por cada síntoma posible.
    Luego ejecuta el motor de inferencia.
    """
    hechos = crear_base_de_hechos()

    print()
    print('=' * 60)
    print('  SISTEMA EXPERTO: Diagnóstico de Computador')
    print('  Responde s (sí), n (no) o Enter para omitir')
    print('=' * 60)
    print()

    for sintoma, pregunta in preguntas.items():
        resp = input(f'  {pregunta} [s/n]: ').strip().lower()
        if resp == 's':
            hechos.add(sintoma)
        elif resp == 'q':
            print('  Consulta cancelada.')
            return hechos

    return hechos


def menu():
    """Menú simple para elegir modo de ejecución."""
    print()
    print('=' * 60)
    print('  SISTEMA EXPERTO: Diagnóstico de PC')
    print('=' * 60)
    print('  1. Diagnóstico principal (un resultado)')
    print('  2. Ranking de diagnósticos (Nivel 2)')
    print('  3. Encadenamiento hacia atrás (Nivel 3)')
    print('  4. Exportar red de inferencia a JSON (Nivel 4)')
    print('  5. Salir')
    print()

    opcion = input('  Selecciona una opción [1-5]: ').strip()
    return opcion


def main():
    while True:
        opcion = menu()

        if opcion == '1':
            hechos = consultar(BASE_DE_CONOCIMIENTO, PREGUNTAS)
            inferir(BASE_DE_CONOCIMIENTO, hechos, modo_ranking=False)

        elif opcion == '2':
            hechos = consultar(BASE_DE_CONOCIMIENTO, PREGUNTAS)
            inferir(BASE_DE_CONOCIMIENTO, hechos, modo_ranking=True)

        elif opcion == '3':
            print()
            meta = input('  Ingresa el diagnóstico/meta a verificar: ').strip()
            if not meta:
                continue
            hechos = consultar(BASE_DE_CONOCIMIENTO, PREGUNTAS)
            arbol = backward_chain(meta, BASE_DE_CONOCIMIENTO, hechos)
            print()
            print('  ÁRBOL DE RAZONAMIENTO HACIA ATRÁS')
            print('  ──────────────────────────────────────────────────────')
            imprimir_arbol_backward(arbol)
            print('━' * 60)

        elif opcion == '4':
            red = exportar_red(BASE_DE_CONOCIMIENTO)
            print()
            print('  RED DE INFERENCIA (JSON)')
            print('  ──────────────────────────────────────────────────────')
            print(json.dumps(red, indent=2, ensure_ascii=False))
            print('━' * 60)

        elif opcion == '5':
            print('  Saliendo...')
            break

        else:
            print('  Opción no válida.')


# Ejecutar si se invoca directamente
if __name__ == '__main__':
    main()
