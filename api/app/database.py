"""
SQLite catalog storage for pumps and irrigation materials.
"""
import os
import sqlite3
from datetime import datetime


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "irrigation_catalog.db")


PUMP_SEED = [
    {
        "model": "Honda WB20",
        "type": "Centrifuga 2 pulg.",
        "engine": "GX160",
        "engine_power_hp": 4.8,
        "max_flow_l_min": 670,
        "max_head_m": 32,
        "max_pressure_kpa": 313.92,
        "source": "Honda Fuerza Chile",
        "source_url": "https://fuerza.honda.cl/motobomba/motobomba-honda-wb20/",
    },
    {
        "model": "Honda WB30",
        "type": "Centrifuga 3 pulg.",
        "engine": "GX160",
        "engine_power_hp": 4.8,
        "max_flow_l_min": 1100,
        "max_head_m": 23,
        "max_pressure_kpa": 225.63,
        "source": "Honda Fuerza Chile",
        "source_url": "https://fuerza.honda.cl/motobomba/motobomba-honda-wb30/",
    },
    {
        "model": "Honda WH20",
        "type": "Alta presion 2 pulg.",
        "engine": "GX160",
        "engine_power_hp": 4.8,
        "max_flow_l_min": 450,
        "max_head_m": 45,
        "max_pressure_kpa": 441.45,
        "source": "Honda Fuerza Chile",
        "source_url": "https://fuerza.honda.cl/motobomba/motobomba-honda-wh20/",
    },
    {
        "model": "Honda WT30",
        "type": "Aguas turbias 3 pulg.",
        "engine": "GX270",
        "engine_power_hp": 8.3,
        "max_flow_l_min": 1210,
        "max_head_m": 27,
        "max_pressure_kpa": 264.87,
        "source": "Honda Fuerza Chile",
        "source_url": "https://fuerza.honda.cl/motobomba/motobomba-honda-wt30/",
    },
    {
        "model": "Koshin SEV-50X",
        "type": "Centrifuga agua limpia 2 pulg.",
        "engine": "Koshin K180",
        "engine_power_hp": 4.8,
        "max_flow_l_min": 620,
        "max_head_m": 27,
        "max_pressure_kpa": 264.87,
        "source": "Koshin Pump",
        "source_url": "https://koshin-pump.com/en/product/sev-50x/",
    },
]


MATERIAL_SEED = [
    ("main_pipe", "HDPE matriz principal", "HDPE 32-50 mm PN 6/10", 40, "PN 6", "Recomendado para matriz principal flexible y enterrada.", "Conducir caudal desde fuente al sector.", "https://images.prom.ua/4676789559_w640_h640_truba-dlya-poliva.jpg", "https://prom.ua/p2045721726-truba-dlya-poliva.html"),
    ("main_pipe", "PVC hidraulico presion", "PVC presion 32-50 mm", 40, "PN 10", "Alternativa rigida para tramos rectos y cabezales.", "Conduccion principal protegida de radiacion UV.", "https://www.keyhole.com.tw/wp-content/uploads/2020/01/KHP-PBV06-2-inch-plastic-ball-valve-socket-connection-sch80_02.jpg", "https://storage.googleapis.com/dzxtzwuaybacve/irrigation-system-ball-valve.html"),
    ("main_pipe", "PE agricola reforzado", "PE agricola 32-40 mm", 32, "PN 4", "Opcion flexible para conduccion secundaria.", "Sectores pequenos o baja presion.", "https://images.prom.ua/4676789559_w640_h640_truba-dlya-poliva.jpg", "https://prom.ua/p2045721726-truba-dlya-poliva.html"),
    ("laterals", "Tuberia PE lateral", "PE 16 mm para goteros insertados", 16, "", "Lateral reutilizable para goteros insertados.", "Lineas de cultivo con mantenimiento recurrente.", "https://cdn.salla.sa/NzYZr/c525c3e9-0b3e-4da3-bd3b-8fea8f06a203-1000x1000-EbXyeIqUoixgrxUVRXLDwbv0ftFhS3kUvorWvTcW.png", "https://mygarden.com.sa/ar/AzDwnpZ"),
    ("laterals", "Cinta de riego", "Cinta 16 mm con emisores integrados", 16, "", "Solucion economica para cultivos en hileras.", "Temporadas definidas y marcos regulares.", "https://cdn.salla.sa/NzYZr/c525c3e9-0b3e-4da3-bd3b-8fea8f06a203-1000x1000-EbXyeIqUoixgrxUVRXLDwbv0ftFhS3kUvorWvTcW.png", "https://mygarden.com.sa/ar/AzDwnpZ"),
    ("laterals", "Manguera con gotero integrado", "Lateral 16 mm con gotero integrado", 16, "", "Reduce errores de instalacion.", "Cultivos con espaciamiento estable.", "https://cdn.salla.sa/NzYZr/c525c3e9-0b3e-4da3-bd3b-8fea8f06a203-1000x1000-EbXyeIqUoixgrxUVRXLDwbv0ftFhS3kUvorWvTcW.png", "https://mygarden.com.sa/ar/AzDwnpZ"),
    ("valves", "Valvula bola PVC/HDPE", "Valvula bola 32-50 mm", 40, "PN 10", "Corte manual rapido para matriz o sector.", "Aislar sectores de riego.", "https://www.keyhole.com.tw/wp-content/uploads/2020/01/KHP-PBV06-2-inch-plastic-ball-valve-socket-connection-sch80_02.jpg", "https://storage.googleapis.com/dzxtzwuaybacve/irrigation-system-ball-valve.html"),
    ("valves", "Valvula de compuerta", "Compuerta PVC presion", 40, "PN 10", "Permite apertura gradual.", "Cabezales o tramos principales.", "https://www.keyhole.com.tw/wp-content/uploads/2020/01/KHP-PBV06-2-inch-plastic-ball-valve-socket-connection-sch80_02.jpg", "https://storage.googleapis.com/dzxtzwuaybacve/irrigation-system-ball-valve.html"),
    ("valves", "Valvula sectorial", "Valvula para subunidad de riego", 32, "PN 6", "Control por zona de riego.", "Manejo de turnos por sector.", "https://www.keyhole.com.tw/wp-content/uploads/2020/01/KHP-PBV06-2-inch-plastic-ball-valve-socket-connection-sch80_02.jpg", "https://storage.googleapis.com/dzxtzwuaybacve/irrigation-system-ball-valve.html"),
    ("emitters", "Gotero 2 L/h", "Gotero boton 2 L/h", None, "", "Emisor de baja descarga.", "Aplicacion localizada en cultivo.", "https://cfrouting.zoeysite.com/cdn-cgi/image/format%3Dauto%2Cquality%3D85%2Cfit%3Dscale-down/https%3A//s3.amazonaws.com/zcom-media/sites/a0i0L00000Scsq8QAB/media/catalog/product/d/0/d014-072519-1.jpg", "https://www.dripirrigation.com/d014"),
    ("emitters", "Gotero autocompensado", "Gotero PC 2-4 L/h", None, "", "Mantiene caudal mas estable.", "Terrenos con pendiente o laterales largos.", "https://cfrouting.zoeysite.com/cdn-cgi/image/format%3Dauto%2Cquality%3D85%2Cfit%3Dscale-down/https%3A//s3.amazonaws.com/zcom-media/sites/a0i0L00000Scsq8QAB/media/catalog/product/d/0/d014-072519-1.jpg", "https://www.dripirrigation.com/d014"),
    ("emitters", "Conectores y terminales", "Tee, union, codo y terminal 16 mm", 16, "", "Accesorios para derivar y cerrar laterales.", "Armado del trazado final.", "https://cfrouting.zoeysite.com/cdn-cgi/image/format%3Dauto%2Cquality%3D85%2Cfit%3Dscale-down/https%3A//s3.amazonaws.com/zcom-media/sites/a0i0L00000Scsq8QAB/media/catalog/product/d/0/d014-072519-1.jpg", "https://www.dripirrigation.com/d014"),
]


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS motobombas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT NOT NULL UNIQUE,
                type TEXT NOT NULL,
                engine TEXT,
                engine_power_hp REAL NOT NULL,
                max_flow_l_min REAL NOT NULL,
                max_head_m REAL NOT NULL,
                max_pressure_kpa REAL NOT NULL,
                source TEXT,
                source_url TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS materiales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                material_type TEXT NOT NULL,
                name TEXT NOT NULL,
                component TEXT NOT NULL,
                diameter_mm REAL,
                pressure_class TEXT,
                description TEXT,
                use_case TEXT,
                image_url TEXT,
                source_url TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(material_type, name)
            );
            """
        )
        _seed_pumps(conn)
        _seed_materials(conn)


def _seed_pumps(conn):
    now = datetime.utcnow().isoformat()
    for pump in PUMP_SEED:
        conn.execute(
            """
            INSERT OR IGNORE INTO motobombas
            (model, type, engine, engine_power_hp, max_flow_l_min, max_head_m,
             max_pressure_kpa, source, source_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pump["model"],
                pump["type"],
                pump["engine"],
                pump["engine_power_hp"],
                pump["max_flow_l_min"],
                pump["max_head_m"],
                pump["max_pressure_kpa"],
                pump["source"],
                pump["source_url"],
                now,
            ),
        )


def _seed_materials(conn):
    now = datetime.utcnow().isoformat()
    for item in MATERIAL_SEED:
        conn.execute(
            """
            INSERT OR IGNORE INTO materiales
            (material_type, name, component, diameter_mm, pressure_class, description,
             use_case, image_url, source_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (*item, now),
        )


def list_pumps():
    with get_connection() as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM motobombas ORDER BY engine_power_hp, max_flow_l_min")]


def add_pump(data):
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO motobombas
            (model, type, engine, engine_power_hp, max_flow_l_min, max_head_m,
             max_pressure_kpa, source, source_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["model"],
                data.get("type") or "Motobomba",
                data.get("engine"),
                float(data["engine_power_hp"]),
                float(data["max_flow_l_min"]),
                float(data["max_head_m"]),
                float(data.get("max_pressure_kpa") or float(data["max_head_m"]) * 9.81),
                data.get("source"),
                data.get("source_url"),
                now,
            ),
        )
        data["id"] = cursor.lastrowid
        data["created_at"] = now
        return data


def delete_pump(pump_id):
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM motobombas WHERE id = ?", (pump_id,))
        if cursor.rowcount == 0:
            raise ValueError("No existe una motobomba con ese identificador.")
        return {"id": pump_id}


def list_materials(material_type=None):
    with get_connection() as conn:
        if material_type:
            rows = conn.execute(
                "SELECT * FROM materiales WHERE material_type = ? ORDER BY id",
                (material_type,),
            )
        else:
            rows = conn.execute("SELECT * FROM materiales ORDER BY material_type, id")
        return [dict(row) for row in rows]


def add_material(data):
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        try:
            cursor = conn.execute(
                """
                INSERT INTO materiales
                (material_type, name, component, diameter_mm, pressure_class, description,
                 use_case, image_url, source_url, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["material_type"],
                    data["name"],
                    data["component"],
                    float(data["diameter_mm"]) if data.get("diameter_mm") not in (None, "") else None,
                    data.get("pressure_class"),
                    data.get("description"),
                    data.get("use_case"),
                    data.get("image_url"),
                    data.get("source_url"),
                    now,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("Ya existe un material con ese nombre en la misma categoria.") from exc
        except ValueError as exc:
            raise ValueError("El diametro debe ser un numero valido.") from exc
        data["id"] = cursor.lastrowid
        data["created_at"] = now
        return data


def delete_material(material_id):
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM materiales WHERE id = ?", (material_id,))
        if cursor.rowcount == 0:
            raise ValueError("No existe un material con ese identificador.")
        return {"id": material_id}
