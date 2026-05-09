"""
Scraper pyphoy.com — Extractor de datos de Pico y Placa Colombia
- Recorre las 123 combinaciones ciudad/categoría
- Extrae el JSON embebido en el HTML (categoryData)
- Guarda progreso incrementalmente (si se interrumpe, continúa donde quedó)
- Construye una tabla plana: una fila por día x ciudad x categoría
- Compatible con terminal y Jupyter

Uso:
    python scraper_pyphoy.py
"""

import time
import random
import json
import re
import os
import datetime
import urllib.request
import urllib.error

OUTPUT    = "pico_y_placa.json"
PAUSE_MIN = 2
PAUSE_MAX = 5
DIAS_ES   = ["Domingo", "Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado"]
BASE_URL  = "https://www.pyphoy.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; research-bot/1.0)",
    "Accept-Language": "es-CO,es;q=0.9",
}

CITIES = [
    {"name": "Armenia",              "slug": "armenia",              "categories": [{"name": "Motos", "slug": "motos"}, {"name": "Particulares", "slug": "particulares"}, {"name": "Taxis", "slug": "taxis"}]},
    {"name": "Barbosa",              "slug": "barbosa",              "categories": [{"name": "Motos", "slug": "motos"}, {"name": "Particulares", "slug": "particulares"}, {"name": "Transporte de carga", "slug": "transporte-de-carga"}]},
    {"name": "Barranquilla",         "slug": "barranquilla",         "categories": [{"name": "Taxis", "slug": "taxis"}, {"name": "Particulares", "slug": "particulares"}]},
    {"name": "Bello",                "slug": "bello",                "categories": [{"name": "Motos", "slug": "motos"}, {"name": "Particulares", "slug": "particulares"}, {"name": "Taxis", "slug": "taxis"}, {"name": "Transporte de carga", "slug": "transporte-de-carga"}]},
    {"name": "Bogota",               "slug": "bogota",               "categories": [{"name": "Carga mas de 20 anos de edad", "slug": "carga-mas-de-20-anos-de-edad"}, {"name": "Carga peso max superior a 3500kg", "slug": "carga-peso-max-superior-a-3500kg"}, {"name": "Carga peso max superior a 8500kg", "slug": "carga-peso-max-superior-a-8500kg"}, {"name": "Motos", "slug": "motos"}, {"name": "Particulares", "slug": "particulares"}, {"name": "Servicio de Transporte Especial", "slug": "servicio-de-transporte-especial"}, {"name": "Taxis", "slug": "taxis"}, {"name": "Transporte Publico Colectivo", "slug": "transporte-publico-colectivo"}, {"name": "Regional", "slug": "regional"}]},
    {"name": "Bucaramanga",          "slug": "bucaramanga",          "categories": [{"name": "Motos", "slug": "motos"}, {"name": "Particulares", "slug": "particulares"}, {"name": "Taxis", "slug": "taxis"}, {"name": "Transporte Publico Colectivo", "slug": "transporte-publico-colectivo"}]},
    {"name": "Buenaventura",         "slug": "buenaventura",         "categories": [{"name": "Particulares", "slug": "particulares"}, {"name": "Taxis", "slug": "taxis"}, {"name": "Transporte Publico Colectivo", "slug": "transporte-publico-colectivo"}]},
    {"name": "Choachi",              "slug": "choachi",              "categories": [{"name": "Regional", "slug": "regional"}]},
    {"name": "Caldas",               "slug": "caldas",               "categories": [{"name": "Motos", "slug": "motos"}, {"name": "Particulares", "slug": "particulares"}, {"name": "Taxis", "slug": "taxis"}, {"name": "Transporte de carga", "slug": "transporte-de-carga"}]},
    {"name": "Cali",                 "slug": "cali",                 "categories": [{"name": "Particulares", "slug": "particulares"}, {"name": "Taxis", "slug": "taxis"}, {"name": "Transporte Publico Colectivo", "slug": "transporte-publico-colectivo"}, {"name": "Motos", "slug": "motos"}]},
    {"name": "Cartagena",            "slug": "cartagena",            "categories": [{"name": "Motos", "slug": "motos"}, {"name": "Particulares", "slug": "particulares"}, {"name": "Taxis", "slug": "taxis"}]},
    {"name": "Copacabana",           "slug": "copacabana",           "categories": [{"name": "Motos", "slug": "motos"}, {"name": "Particulares", "slug": "particulares"}, {"name": "Transporte de carga", "slug": "transporte-de-carga"}]},
    {"name": "Cota",                 "slug": "cota",                 "categories": [{"name": "Regional", "slug": "regional"}]},
    {"name": "Cucuta",               "slug": "cucuta",               "categories": [{"name": "Motos", "slug": "motos"}, {"name": "Particulares", "slug": "particulares"}, {"name": "Taxis", "slug": "taxis"}]},
    {"name": "Dosquebradas",         "slug": "dosquebradas",         "categories": [{"name": "Motos", "slug": "motos"}, {"name": "Particulares", "slug": "particulares"}]},
    {"name": "Envigado",             "slug": "envigado",             "categories": [{"name": "Motos", "slug": "motos"}, {"name": "Particulares", "slug": "particulares"}, {"name": "Taxis", "slug": "taxis"}, {"name": "Transporte de carga", "slug": "transporte-de-carga"}]},
    {"name": "Fusagasuga",           "slug": "fusagasuga",           "categories": [{"name": "Particulares", "slug": "particulares"}]},
    {"name": "Girardota",            "slug": "girardota",            "categories": [{"name": "Motos", "slug": "motos"}, {"name": "Particulares", "slug": "particulares"}, {"name": "Transporte de carga", "slug": "transporte-de-carga"}]},
    {"name": "Girardot",             "slug": "girardot",             "categories": [{"name": "Particulares", "slug": "particulares"}]},
    {"name": "Ibague",               "slug": "ibague",               "categories": [{"name": "Motos", "slug": "motos"}, {"name": "Particulares", "slug": "particulares"}, {"name": "Taxis", "slug": "taxis"}, {"name": "Transporte Publico Colectivo", "slug": "transporte-publico-colectivo"}]},
    {"name": "Ipiales",              "slug": "ipiales",              "categories": [{"name": "Particulares", "slug": "particulares"}, {"name": "Motos", "slug": "motos"}]},
    {"name": "Itagui",               "slug": "itagui",               "categories": [{"name": "Motos", "slug": "motos"}, {"name": "Particulares", "slug": "particulares"}, {"name": "Taxis", "slug": "taxis"}, {"name": "Transporte de carga", "slug": "transporte-de-carga"}]},
    {"name": "La Calera",            "slug": "la-calera",            "categories": [{"name": "Regional", "slug": "regional"}]},
    {"name": "La Estrella",          "slug": "la-estrella",          "categories": [{"name": "Motos", "slug": "motos"}, {"name": "Particulares", "slug": "particulares"}, {"name": "Transporte de carga", "slug": "transporte-de-carga"}]},
    {"name": "Malambo",              "slug": "malambo",              "categories": [{"name": "Motocarros", "slug": "motocarros"}, {"name": "Motos", "slug": "motos"}]},
    {"name": "Manizales",            "slug": "manizales",            "categories": [{"name": "Particulares", "slug": "particulares"}, {"name": "Taxis", "slug": "taxis"}]},
    {"name": "Medellin",             "slug": "medellin",             "categories": [{"name": "Motos", "slug": "motos"}, {"name": "Particulares", "slug": "particulares"}, {"name": "Taxis", "slug": "taxis"}, {"name": "Transporte de carga", "slug": "transporte-de-carga"}]},
    {"name": "Monteria",             "slug": "monteria",             "categories": [{"name": "Particulares", "slug": "particulares"}]},
    {"name": "Murillo",              "slug": "murillo",              "categories": [{"name": "Particulares", "slug": "particulares"}, {"name": "Motos", "slug": "motos"}, {"name": "Motocarros", "slug": "motocarros"}]},
    {"name": "Ocana",                "slug": "ocana",                "categories": [{"name": "Particulares", "slug": "particulares"}, {"name": "Motos", "slug": "motos"}, {"name": "Motocarros", "slug": "motocarros"}]},
    {"name": "Pamplona",             "slug": "pamplona",             "categories": [{"name": "Motos", "slug": "motos"}, {"name": "Particulares", "slug": "particulares"}]},
    {"name": "Pasto",                "slug": "pasto",                "categories": [{"name": "Motos", "slug": "motos"}, {"name": "Particulares", "slug": "particulares"}, {"name": "Taxis", "slug": "taxis"}]},
    {"name": "Pereira",              "slug": "pereira",              "categories": [{"name": "Motos", "slug": "motos"}, {"name": "Particulares", "slug": "particulares"}, {"name": "Taxis", "slug": "taxis"}]},
    {"name": "Popayan",              "slug": "popayan",              "categories": [{"name": "Motos", "slug": "motos"}, {"name": "Particulares", "slug": "particulares"}, {"name": "Transporte de carga menor a 1500kg", "slug": "transporte-de-carga-menor-a-1500kg"}, {"name": "Transporte Publico Colectivo", "slug": "transporte-publico-colectivo"}]},
    {"name": "Quibdo",               "slug": "quibdo",               "categories": [{"name": "Motos", "slug": "motos"}, {"name": "Particulares", "slug": "particulares"}]},
    {"name": "Sabaneta",             "slug": "sabaneta",             "categories": [{"name": "Motos", "slug": "motos"}, {"name": "Particulares", "slug": "particulares"}, {"name": "Taxis", "slug": "taxis"}, {"name": "Transporte de carga", "slug": "transporte-de-carga"}]},
    {"name": "Santa Cruz de Lorica", "slug": "santa-cruz-de-lorica", "categories": [{"name": "Motos", "slug": "motos"}, {"name": "Particulares", "slug": "particulares"}]},
    {"name": "Santa Marta",          "slug": "santa-marta",          "categories": [{"name": "Motos", "slug": "motos"}, {"name": "Particulares", "slug": "particulares"}, {"name": "Taxis", "slug": "taxis"}]},
    {"name": "Sincelejo",            "slug": "sincelejo",            "categories": [{"name": "Particulares", "slug": "particulares"}]},
    {"name": "Soacha",               "slug": "soacha",               "categories": [{"name": "Transporte Publico Colectivo", "slug": "transporte-publico-colectivo"}, {"name": "Regional", "slug": "regional"}, {"name": "Particulares", "slug": "particulares"}]},
    {"name": "Soledad",              "slug": "soledad",              "categories": [{"name": "Motocarros", "slug": "motocarros"}, {"name": "Motos", "slug": "motos"}]},
    {"name": "Tunja",                "slug": "tunja",                "categories": [{"name": "Particulares", "slug": "particulares"}, {"name": "Taxis", "slug": "taxis"}]},
    {"name": "Turbaco",              "slug": "turbaco",              "categories": [{"name": "Motos", "slug": "motos"}]},
    {"name": "Villavicencio",        "slug": "villavicencio",        "categories": [{"name": "Motos", "slug": "motos"}, {"name": "Particulares", "slug": "particulares"}, {"name": "Taxis", "slug": "taxis"}, {"name": "Transporte de carga", "slug": "transporte-de-carga"}]},
]

def dia_semana(fecha_iso):
    try:
        d = datetime.date.fromisoformat(fecha_iso)
        return DIAS_ES[d.weekday() + 1 if d.weekday() < 6 else 0]
    except Exception:
        return None

def build_fecha(day, month, year):
    try:
        return datetime.date(year, month, day).isoformat()
    except ValueError:
        return None

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")

def extract_category_data(html):
    segments = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html, re.DOTALL)
    full_text = html
    if segments:
        combined = ""
        for seg in segments:
            try:
                combined += seg.encode("utf-8").decode("unicode_escape", errors="replace")
            except Exception:
                combined += seg
        full_text = combined

    marker = '"categoryData":'
    idx = full_text.find(marker)
    if idx == -1:
        full_text = html
        idx = full_text.find(marker)
    if idx == -1:
        return None

    try:
        start = full_text.index("{", idx + len(marker))
    except ValueError:
        return None

    depth, end = 0, start
    for i, ch in enumerate(full_text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    obj_str = full_text[start:end]
    obj_str = re.sub(r'"excludedDays"\s*:\s*"\$[^"]*"', '"excludedDays":[0,6]', obj_str)
    obj_str = re.sub(r':\s*"\$[^"]*"', ': null', obj_str)

    try:
        parsed = json.loads(obj_str)
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict) and "data" in item:
                    return item
        return parsed
    except json.JSONDecodeError:
        data_match = re.search(r'"data"\s*:\s*(\[)', obj_str)
        if data_match:
            start_arr = data_match.start(1)
            depth2, end_arr = 0, start_arr
            for i, ch in enumerate(obj_str[start_arr:], start_arr):
                if ch == "[":
                    depth2 += 1
                elif ch == "]":
                    depth2 -= 1
                    if depth2 == 0:
                        end_arr = i + 1
                        break
            arr_str = re.sub(r':\s*"\$[^"]*"', ': null', obj_str[start_arr:end_arr])
            try:
                return {"data": json.loads(arr_str)}
            except Exception:
                pass
        return None

def procesar(city, cat):
    url = f"{BASE_URL}/{city['slug']}/{cat['slug']}"
    rows = []
    try:
        html = fetch(url)
        cat_data = extract_category_data(html)

        if not cat_data or not isinstance(cat_data, dict):
            print(f"Sin datos")
            return rows

        data = cat_data.get("data", [])
        if not isinstance(data, list):
            print(f"data no es lista")
            return rows

        for entry in data:
            if not isinstance(entry, dict):
                continue
            day   = entry.get("day")
            month = entry.get("month")
            year  = entry.get("year")
            fecha = build_fecha(day, month, year)
            if not fecha:
                continue

            numbers    = entry.get("numbers") or []
            hours_list = entry.get("hours") or []
            franjas = []
            for h in hours_list:
                if not isinstance(h, dict):
                    continue
                for franja in h.get("hours", []):
                    if isinstance(franja, list) and len(franja) == 2:
                        franjas.append(f"{franja[0]}-{franja[1]}")
            horario = " / ".join(franjas) if franjas else None

            rows.append({
                "fecha":                fecha,
                "dia_semana":           dia_semana(fecha),
                "ciudad":               city["name"],
                "ciudad_slug":          city["slug"],
                "categoria":            cat["name"],
                "categoria_slug":       cat["slug"],
                "tiene_restriccion":    len(numbers) > 0,
                "digitos_restringidos": ",".join(str(n) for n in numbers) if numbers else "",
                "horario":              horario,
                "esquema":              entry.get("scheme"),
                "excluye_fds":          bool(entry.get("excludedDays")),
                "excluye_festivos":     entry.get("skipHolidays", False),
            })

    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}")
    except Exception as e:
        print(f"Error: {e}")
    return rows

def cargar_progreso():
    if not os.path.exists(OUTPUT):
        return [], set()
    try:
        with open(OUTPUT, "r", encoding="utf-8") as f:
            data = json.load(f)
        registros = data.get("data", [])
        claves = set(f"{r['ciudad_slug']}/{r['categoria_slug']}" for r in registros)
        print(f"  Retomando: {len(registros)} registros, {len(claves)} combinaciones ya procesadas\n")
        return registros, claves
    except Exception:
        return [], set()

def guardar(registros, ahora):
    output = {
        "generado_en":     ahora,
        "total_registros": len(registros),
        "ciudades":        len(CITIES),
        "data":            registros,
    }
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

def main():
    ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*60}")
    print(f"  SCRAPER PYPHOY.COM - {ahora}")
    print(f"  Pausa entre peticiones: {PAUSE_MIN}-{PAUSE_MAX}s")
    print(f"{'='*60}\n")

    todas_las_filas, ya_procesadas = cargar_progreso()
    total_urls = sum(len(c["categories"]) for c in CITIES)
    contador = 0

    for city in CITIES:
        for cat in city["categories"]:
            contador += 1
            clave = f"{city['slug']}/{cat['slug']}"

            if clave in ya_procesadas:
                print(f"[{contador:>3}/{total_urls}] (ya procesada) {clave}")
                continue

            print(f"[{contador:>3}/{total_urls}] {clave} ...", end=" ", flush=True)

            filas = procesar(city, cat)
            todas_las_filas.extend(filas)
            ya_procesadas.add(clave)

            print(f"OK {len(filas)} dias")

            guardar(todas_las_filas, ahora)

            if contador < total_urls:
                time.sleep(random.uniform(PAUSE_MIN, PAUSE_MAX))

    print(f"\n{'='*60}")
    print(f"  Completado")
    print(f"  Total registros: {len(todas_las_filas)}")
    print(f"  Guardado en:     {OUTPUT}")
    print(f"{'='*60}\n")

main()
