import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), 'magdist.db')


def connect():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = connect()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS campaigns (
        id INTEGER PRIMARY KEY,
        name TEXT,
        packs INTEGER,
        units_per_pack INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS regions (
        id INTEGER PRIMARY KEY,
        name TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS provinces (
        id INTEGER PRIMARY KEY,
        name TEXT,
        region_id INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS cities (
        id INTEGER PRIMARY KEY,
        name TEXT,
        province_id INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS municipalities (
        id INTEGER PRIMARY KEY,
        name TEXT,
        city_id INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS neighborhoods (
        id INTEGER PRIMARY KEY,
        name TEXT,
        municipality_id INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS supervisors (
        id INTEGER PRIMARY KEY,
        name TEXT,
        campaign_id INTEGER,
        neighborhood_id INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        supervisor_id INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS areas (
        id INTEGER PRIMARY KEY,
        name TEXT,
        city TEXT,
        supervisor_id INTEGER,
        neighborhood_id INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS streets (
        id INTEGER PRIMARY KEY,
        name TEXT,
        area_id INTEGER,
        units INTEGER,
        lat REAL,
        lon REAL,
        assigned_user INTEGER,
        done INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS campaign_cache (
        id INTEGER PRIMARY KEY,
        campaign_id INTEGER,
        supervisor_id INTEGER,
        region_id INTEGER,
        province_id INTEGER,
        city_id INTEGER,
        municipality_id INTEGER,
        neighborhood_id INTEGER
    )''')
    conn.commit()
    conn.close()
    # seed minimal Belgium geography and default campaign if empty
    try:
        seed_belgium_sample()
    except Exception:
        pass


def add_supervisor(name, campaign_id=None, neighborhood_id=None):
    conn = connect()
    c = conn.cursor()
    c.execute('INSERT INTO supervisors (name, campaign_id, neighborhood_id) VALUES (?,?,?)', (name, campaign_id, neighborhood_id))
    conn.commit()
    supervisor_id = c.lastrowid
    conn.close()
    return supervisor_id


def add_user(name, supervisor_id=None):
    conn = connect()
    c = conn.cursor()
    c.execute('INSERT INTO users (name, supervisor_id) VALUES (?,?)', (name, supervisor_id))
    conn.commit()
    user_id = c.lastrowid
    conn.close()
    return user_id


def add_area(name, city, supervisor_id=None, neighborhood_id=None):
    conn = connect()
    c = conn.cursor()
    c.execute('INSERT INTO areas (name, city, supervisor_id, neighborhood_id) VALUES (?,?,?,?)', (name, city, supervisor_id, neighborhood_id))
    conn.commit()
    area_id = c.lastrowid
    conn.close()
    return area_id


def add_street(name, area_id, units, lat=None, lon=None, assigned_user=None):
    conn = connect()
    c = conn.cursor()
    c.execute('INSERT INTO streets (name, area_id, units, lat, lon, assigned_user) VALUES (?,?,?,?,?,?)',
              (name, area_id, units, lat, lon, assigned_user))
    conn.commit()
    street_id = c.lastrowid
    conn.close()
    return street_id


def assign_street_to_user(street_id, user_id):
    conn = connect()
    c = conn.cursor()
    c.execute('UPDATE streets SET assigned_user=? WHERE id=?', (user_id, street_id))
    conn.commit()
    conn.close()


def mark_street_done(street_id):
    conn = connect()
    c = conn.cursor()
    c.execute('UPDATE streets SET done=1 WHERE id=?', (street_id,))
    conn.commit()
    conn.close()


def get_supervisors():
    conn = connect()
    c = conn.cursor()
    c.execute('SELECT * FROM supervisors')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_users(supervisor_id=None):
    conn = connect()
    c = conn.cursor()
    if supervisor_id:
        c.execute('SELECT * FROM users WHERE supervisor_id=?', (supervisor_id,))
    else:
        c.execute('SELECT * FROM users')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_areas(supervisor_id=None):
    conn = connect()
    c = conn.cursor()
    if supervisor_id:
        c.execute('SELECT a.*, s.name AS supervisor_name FROM areas a LEFT JOIN supervisors s ON a.supervisor_id=s.id WHERE a.supervisor_id=?',
                  (supervisor_id,))
    else:
        c.execute('SELECT a.*, s.name AS supervisor_name FROM areas a LEFT JOIN supervisors s ON a.supervisor_id=s.id')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_unassigned_streets(supervisor_id=None):
    conn = connect()
    c = conn.cursor()
    if supervisor_id:
        c.execute('''SELECT s.*, a.name AS area_name FROM streets s
                     JOIN areas a ON s.area_id=a.id
                     WHERE s.assigned_user IS NULL AND a.supervisor_id=?''', (supervisor_id,))
    else:
        c.execute('SELECT s.*, a.name AS area_name FROM streets s JOIN areas a ON s.area_id=a.id WHERE s.assigned_user IS NULL')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_assigned_streets_for_supervisor(supervisor_id):
    conn = connect()
    c = conn.cursor()
    c.execute('''SELECT s.*, u.name AS user_name, a.name AS area_name FROM streets s
                 JOIN areas a ON s.area_id=a.id
                 LEFT JOIN users u ON s.assigned_user=u.id
                 WHERE a.supervisor_id=?''', (supervisor_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_streets_for_user(user_id):
    conn = connect()
    c = conn.cursor()
    c.execute('SELECT * FROM streets WHERE assigned_user=?', (user_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_any_user():
    conn = connect()
    c = conn.cursor()
    c.execute('SELECT * FROM users LIMIT 1')
    r = c.fetchone()
    conn.close()
    return dict(r) if r else None


def total_units_for_campaign(campaign_id):
    conn = connect()
    c = conn.cursor()
    c.execute('SELECT packs, units_per_pack FROM campaigns WHERE id=?', (campaign_id,))
    r = c.fetchone()
    conn.close()
    if not r:
        return 0
    return r['packs'] * r['units_per_pack']


def add_campaign(name, packs, units_per_pack):
    conn = connect()
    c = conn.cursor()
    c.execute('INSERT INTO campaigns (name, packs, units_per_pack) VALUES (?,?,?)', (name, packs, units_per_pack))
    conn.commit()
    campaign_id = c.lastrowid
    conn.close()
    return campaign_id


def get_street_count_for_user(user_id):
    conn = connect()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) AS count FROM streets WHERE assigned_user=?', (user_id,))
    r = c.fetchone()
    conn.close()
    return r['count'] if r else 0


# Geographic hierarchy functions
def get_campaigns():
    conn = connect()
    c = conn.cursor()
    c.execute('SELECT * FROM campaigns ORDER BY name')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_campaign_cache_entries():
    conn = connect()
    c = conn.cursor()
    c.execute('''SELECT cc.*, c.name AS campaign_name, s.name AS supervisor_name, n.name AS neighborhood_name
                 FROM campaign_cache cc
                 LEFT JOIN campaigns c ON cc.campaign_id=c.id
                 LEFT JOIN supervisors s ON cc.supervisor_id=s.id
                 LEFT JOIN neighborhoods n ON cc.neighborhood_id=n.id
                 ORDER BY cc.id''')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def clear_campaign_cache():
    conn = connect()
    c = conn.cursor()
    c.execute('DELETE FROM campaign_cache')
    conn.commit()
    conn.close()


def clear_cache_keep_campaigns():
    """Clear all application data EXCEPT campaigns (they persist across cache clears)."""
    conn = connect()
    c = conn.cursor()
    c.execute('DELETE FROM supervisors')
    c.execute('DELETE FROM users')
    c.execute('DELETE FROM areas')
    c.execute('DELETE FROM streets')
    c.execute('DELETE FROM campaign_cache')
    # campaigns table is NOT cleared — campaigns persist
    conn.commit()
    conn.close()


def clear_all_data():
    """Full reset — deletes everything including campaigns."""
    conn = connect()
    c = conn.cursor()
    c.execute('DELETE FROM supervisors')
    c.execute('DELETE FROM users')
    c.execute('DELETE FROM areas')
    c.execute('DELETE FROM streets')
    c.execute('DELETE FROM campaign_cache')
    conn.commit()
    conn.close()
    # NOTE: campaigns are intentionally preserved even in clear_all_data
    # To delete campaigns as well, drop/truncate the campaigns table explicitly.


def get_municipalities_by_province(province_id):
    conn = connect()
    c = conn.cursor()
    c.execute('''SELECT m.* FROM municipalities m
                 JOIN cities c ON m.city_id=c.id
                 WHERE c.province_id=?
                 ORDER BY m.name''', (province_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_regions():
    conn = connect()
    c = conn.cursor()
    c.execute('SELECT * FROM regions ORDER BY name')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_provinces(region_id=None):
    conn = connect()
    c = conn.cursor()
    if region_id:
        c.execute('SELECT * FROM provinces WHERE region_id=? ORDER BY name', (region_id,))
    else:
        c.execute('SELECT * FROM provinces ORDER BY name')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_cities(province_id=None):
    conn = connect()
    c = conn.cursor()
    if province_id:
        c.execute('SELECT * FROM cities WHERE province_id=? ORDER BY name', (province_id,))
    else:
        c.execute('SELECT * FROM cities ORDER BY name')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_municipalities(city_id=None):
    conn = connect()
    c = conn.cursor()
    if city_id:
        c.execute('SELECT * FROM municipalities WHERE city_id=? ORDER BY name', (city_id,))
    else:
        c.execute('SELECT * FROM municipalities ORDER BY name')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_neighborhoods(municipality_id=None):
    conn = connect()
    c = conn.cursor()
    if municipality_id:
        c.execute('SELECT * FROM neighborhoods WHERE municipality_id=? ORDER BY name', (municipality_id,))
    else:
        c.execute('SELECT * FROM neighborhoods ORDER BY name')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_region(name):
    conn = connect()
    c = conn.cursor()
    c.execute('INSERT INTO regions (name) VALUES (?)', (name,))
    conn.commit()
    region_id = c.lastrowid
    conn.close()
    return region_id


def add_province(name, region_id):
    conn = connect()
    c = conn.cursor()
    c.execute('INSERT INTO provinces (name, region_id) VALUES (?,?)', (name, region_id))
    conn.commit()
    province_id = c.lastrowid
    conn.close()
    return province_id


def add_city(name, province_id):
    conn = connect()
    c = conn.cursor()
    c.execute('INSERT INTO cities (name, province_id) VALUES (?,?)', (name, province_id))
    conn.commit()
    city_id = c.lastrowid
    conn.close()
    return city_id


def add_municipality(name, city_id):
    conn = connect()
    c = conn.cursor()
    c.execute('INSERT INTO municipalities (name, city_id) VALUES (?,?)', (name, city_id))
    conn.commit()
    municipality_id = c.lastrowid
    conn.close()
    return municipality_id


def add_neighborhood(name, municipality_id):
    conn = connect()
    c = conn.cursor()
    c.execute('INSERT INTO neighborhoods (name, municipality_id) VALUES (?,?)', (name, municipality_id))
    conn.commit()
    neighborhood_id = c.lastrowid
    conn.close()
    return neighborhood_id


def save_campaign_cache(campaign_id, supervisor_id, region_id=None, province_id=None, city_id=None, municipality_id=None, neighborhood_id=None):
    conn = connect()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS campaign_cache (
        id INTEGER PRIMARY KEY,
        campaign_id INTEGER,
        supervisor_id INTEGER,
        region_id INTEGER,
        province_id INTEGER,
        city_id INTEGER,
        municipality_id INTEGER,
        neighborhood_id INTEGER
    )''')
    # upsert by campaign_id + supervisor_id
    c.execute('SELECT id FROM campaign_cache WHERE campaign_id=? AND supervisor_id=?', (campaign_id, supervisor_id))
    r = c.fetchone()
    if r:
        c.execute('''UPDATE campaign_cache SET region_id=?, province_id=?, city_id=?, municipality_id=?, neighborhood_id=? WHERE id=?''',
                  (region_id, province_id, city_id, municipality_id, neighborhood_id, r['id']))
    else:
        c.execute('''INSERT INTO campaign_cache (campaign_id, supervisor_id, region_id, province_id, city_id, municipality_id, neighborhood_id)
                     VALUES (?,?,?,?,?,?,?)''', (campaign_id, supervisor_id, region_id, province_id, city_id, municipality_id, neighborhood_id))
    conn.commit()
    conn.close()


def get_campaign_cache(campaign_id, supervisor_id=None):
    conn = connect()
    c = conn.cursor()
    if supervisor_id:
        c.execute('SELECT * FROM campaign_cache WHERE campaign_id=? AND supervisor_id=?', (campaign_id, supervisor_id))
    else:
        c.execute('SELECT * FROM campaign_cache WHERE campaign_id=?', (campaign_id,))
    r = c.fetchone()
    conn.close()
    return dict(r) if r else None


def assign_neighborhood_to_supervisor(supervisor_id, neighborhood_id, campaign_id=None):
    conn = connect()
    c = conn.cursor()
    # update supervisor record
    if campaign_id:
        c.execute('UPDATE supervisors SET neighborhood_id=?, campaign_id=? WHERE id=?', (neighborhood_id, campaign_id, supervisor_id))
    else:
        c.execute('UPDATE supervisors SET neighborhood_id=? WHERE id=?', (neighborhood_id, supervisor_id))
    # upsert area: get neighborhood name and create/update area entry
    n = c.execute('SELECT name, municipality_id FROM neighborhoods WHERE id=?', (neighborhood_id,)).fetchone()
    if n:
        area_name = n['name']
        # try to get city name for this area via municipality
        m = c.execute('SELECT name FROM municipalities WHERE id=?', (n['municipality_id'],)).fetchone()
        city_name = m['name'] if m else ''
        existing = c.execute('SELECT id FROM areas WHERE neighborhood_id=?', (neighborhood_id,)).fetchone()
        if existing:
            c.execute('UPDATE areas SET supervisor_id=?, name=?, city=? WHERE id=?',
                      (supervisor_id, area_name, city_name, existing['id']))
        else:
            c.execute('INSERT INTO areas (name, city, supervisor_id, neighborhood_id) VALUES (?,?,?,?)',
                      (area_name, city_name, supervisor_id, neighborhood_id))
    conn.commit()
    conn.close()


def seed_belgium_sample():
    """Seed complete Belgian geography with real neighborhoods."""
    if get_regions():
        return
    # Helper: add city with neighborhoods AND seed areas + streets
    def add_city_with_streets(city_name, district_id, neighborhoods):
        """Add municipality, neighborhoods, areas table entries, and sample streets."""
        cid = add_municipality(city_name, district_id)
        import random as _rnd
        # Approximate center coordinates for major Belgian cities
        coords_map = {
            'Antwerp': (51.2195, 4.4024),
            'Brussels City': (50.8503, 4.3517),
            'Ghent': (51.0543, 3.7174),
            'Bruges': (51.2093, 3.2247),
            'Leuven': (50.8798, 4.7005),
            'Mechelen': (51.0259, 4.4776),
            'Hasselt': (50.9307, 5.3385),
            'Genk': (50.9661, 5.5021),
            'Liège': (50.6326, 5.5797),
            'Namur': (50.4673, 4.8718),
            'Mons': (50.4541, 3.9569),
            'Charleroi': (50.4114, 4.4447),
            'Kortrijk': (50.8279, 3.2648),
            'Ostend': (51.2154, 2.9286),
            'Vilvoorde': (50.9276, 4.4257),
            'Halle': (50.7366, 4.2370),
            'Sint-Niklaas': (51.1645, 4.1392),
            'Aalst': (50.9381, 4.0395),
            'Turnhout': (51.3224, 4.9446),
            'Ypres': (50.8511, 2.8853),
            'Verviers': (50.5910, 5.8642),
            'Tournai': (50.6063, 3.3892),
            'Arlon': (49.6833, 5.8167),
            'Dinant': (50.2609, 4.9122),
        }
        base_lat, base_lon = coords_map.get(city_name, (50.85, 4.35))
        street_names_nl = [
            'Kerkstraat', 'Schoolstraat', 'Molenstraat', 'Stationsstraat',
            'Veldstraat', 'Kapelstraat', 'Brugstraat', 'Marktstraat',
            'Lindelaan', 'Eikenlaan', 'Beukenlaan', 'Kastanjelaan',
            'Dorpstraat', 'Steenweg', 'Heirbaan', 'Leuvensesteenweg',
            'Mechelsesteenweg', 'Brusselsesteenweg', 'Antwerpsesteenweg',
            'Sint-Annastraat', 'Sint-Jorisstraat', 'Sint-Pietersstraat',
        ]
        street_names_fr = [
            'Rue de l\'Église', 'Rue du Centre', 'Avenue des Tilleuls',
            'Rue de la Station', 'Rue du Moulin', 'Rue de la Chapelle',
            'Grand-Rue', 'Rue Neuve', 'Boulevard du Nord', 'Rue Haute',
            'Avenue Victor Hugo', 'Rue de la Liberté', 'Place du Marché',
            'Rue des Écoles', 'Chaussée de Bruxelles',
        ]
        street_names = street_names_nl if city_name in ['Antwerp', 'Ghent', 'Bruges', 'Leuven', 'Mechelen',
            'Hasselt', 'Genk', 'Kortrijk', 'Ostend', 'Vilvoorde', 'Halle',
            'Sint-Niklaas', 'Aalst', 'Turnhout', 'Ypres', 'Edegem', 'Schoten',
            'Brasschaat', 'Deinze', 'Merelbeke', 'Lier', 'Willebroek',
            'Dendermonde', 'Zele', 'Eeklo', 'Oudenaarde', 'Ronse', 'Beveren',
            'Lokeren', 'Zaventem', 'Dilbeek', 'Tienen', 'Diest', 'Aarschot',
            'Sint-Truiden', 'Maaseik', 'Lommel', 'Tongeren', 'Bilzen',
            'Knokke-Heist', 'Diksmuide', 'Poperinge', 'Waregem', 'Menen',
            'Bredene', 'Roeselare', 'Izegem', 'Tielt', 'Veurne', 'De Panne',
            'Geel', 'Mol', 'Herentals'] else street_names_fr
        for area_name in neighborhoods:
            # Create area entry
            aid = add_area(area_name, city_name, None, None)
            # Update with neighborhood_id
            nid = add_neighborhood(area_name, cid)
            conn = connect()
            conn.execute('UPDATE areas SET neighborhood_id=? WHERE id=?', (nid, aid))
            conn.commit()
            conn.close()
            # Add 3-5 streets per area
            n_streets = _rnd.randint(3, 5)
            used_names = set()
            for _ in range(n_streets):
                sname = _rnd.choice(street_names)
                while sname in used_names:
                    sname = _rnd.choice(street_names)
                    sname = f"{sname} {_rnd.randint(2, 50)}" if sname in used_names else sname
                used_names.add(sname)
                slat = base_lat + _rnd.uniform(-0.015, 0.015)
                slon = base_lon + _rnd.uniform(-0.015, 0.015)
                units = _rnd.randint(10, 80)
                add_street(sname, aid, units, slat, slon)
        return cid

    add_city_with_areas = add_city_with_streets  # backward compat alias

    # ── Flanders ──────────────────────────────────────────────
    flanders = add_region('Flanders')

    # Antwerp
    p_antwerp = add_province('Antwerp', flanders)
    d_antw = add_city('Antwerp', p_antwerp)
    d_mech = add_city('Mechelen', p_antwerp)
    d_turn = add_city('Turnhout', p_antwerp)
    for did, cities in [
        (d_antw, {'Antwerp': ['Centrum', 'Zuid', 'Eilandje', 'Zurenborg', 'Berchem', 'Borgerhout', 'Deurne', 'Hoboken', 'Wilrijk', 'Merksem'],
                  'Brasschaat': ['Centrum', 'Maria-ter-Heide'], 'Schoten': ['Centrum'], 'Edegem': ['Centrum']}),
        (d_mech, {'Mechelen': ['Centrum', 'Nekkerspoel', 'Muizen', 'Battel'],
                  'Lier': ['Centrum', 'Koningshooikt'], 'Willebroek': ['Centrum']}),
        (d_turn, {'Turnhout': ['Centrum'], 'Geel': ['Centrum', 'Ten Aard'], 'Mol': ['Centrum', 'Achterbos'],
                  'Herentals': ['Centrum']}),
    ]:
        for cname, areas in cities.items():
            add_city_with_areas(cname, did, areas)

    # East Flanders
    p_east_fl = add_province('East Flanders', flanders)
    d_aalst = add_city('Aalst', p_east_fl)
    d_dend = add_city('Dendermonde', p_east_fl)
    d_eeklo = add_city('Eeklo', p_east_fl)
    d_gent = add_city('Ghent', p_east_fl)
    d_oud = add_city('Oudenaarde', p_east_fl)
    d_stn = add_city('Sint-Niklaas', p_east_fl)
    for did, cities in [
        (d_aalst, {'Aalst': ['Centrum', 'Mijlbeek', 'Hofstade'], 'Ninove': ['Centrum']}),
        (d_dend, {'Dendermonde': ['Centrum', 'Sint-Gillis-bij-Dendermonde'], 'Zele': ['Centrum']}),
        (d_eeklo, {'Eeklo': ['Centrum']}),
        (d_gent, {'Ghent': ['Centrum', 'Sint-Pieters', 'Ledeberg', 'Gentbrugge', 'Sint-Amandsberg', 'Mariakerke', 'Wondelgem', 'Zwijnaarde'],
                  'Deinze': ['Centrum'], 'Merelbeke': ['Centrum', 'Flora']}),
        (d_oud, {'Oudenaarde': ['Centrum'], 'Ronse': ['Centrum']}),
        (d_stn, {'Sint-Niklaas': ['Centrum', 'Nieuwkerken-Waas', 'Belsele'], 'Beveren': ['Centrum', 'Melsele'], 'Lokeren': ['Centrum']}),
    ]:
        for cname, areas in cities.items():
            add_city_with_areas(cname, did, areas)

    # Flemish Brabant
    p_fl_br = add_province('Flemish Brabant', flanders)
    d_hv = add_city('Halle-Vilvoorde', p_fl_br)
    d_leuv = add_city('Leuven', p_fl_br)
    for did, cities in [
        (d_hv, {'Halle': ['Centrum', 'Buizingen', 'Lembeek'],
                'Vilvoorde': ['Farwest', 'Koningslo', 'Houtem', 'Beauval', 'Peutie', 'Centrum'],
                'Zaventem': ['Centrum', 'Sint-Stevens-Woluwe'], 'Dilbeek': ['Centrum', 'Groot-Bijgaarden']}),
        (d_leuv, {'Leuven': ['Centrum', 'Heverlee', 'Kessel-Lo', 'Wijgmaal', 'Wilsele'],
                  'Tienen': ['Centrum'], 'Diest': ['Centrum'], 'Aarschot': ['Centrum']}),
    ]:
        for cname, areas in cities.items():
            add_city_with_areas(cname, did, areas)

    # Limburg
    p_limb = add_province('Limburg', flanders)
    d_has = add_city('Hasselt', p_limb)
    d_maa = add_city('Maaseik', p_limb)
    d_ton = add_city('Tongeren', p_limb)
    for did, cities in [
        (d_has, {'Hasselt': ['Centrum', 'Kermt', 'Kuringen', 'Runkst'],
                 'Genk': ['Centrum', 'Waterschei', 'Winterslag', 'Boxbergheide'], 'Sint-Truiden': ['Centrum']}),
        (d_maa, {'Maaseik': ['Centrum'], 'Lommel': ['Centrum', 'Barrier']}),
        (d_ton, {'Tongeren': ['Centrum'], 'Bilzen': ['Centrum']}),
    ]:
        for cname, areas in cities.items():
            add_city_with_areas(cname, did, areas)

    # West Flanders
    p_west = add_province('West Flanders', flanders)
    d_bru = add_city('Bruges', p_west)
    d_dik = add_city('Diksmuide', p_west)
    d_ypr = add_city('Ypres', p_west)
    d_kor = add_city('Kortrijk', p_west)
    d_ost = add_city('Ostend', p_west)
    d_roe = add_city('Roeselare', p_west)
    d_tie = add_city('Tielt', p_west)
    d_veu = add_city('Veurne', p_west)
    for did, cities in [
        (d_bru, {'Bruges': ['Centrum', 'Sint-Kruis', 'Assebroek', 'Sint-Michiels', 'Sint-Andries', 'Koolkerke'],
                 'Knokke-Heist': ['Knokke', 'Heist']}),
        (d_dik, {'Diksmuide': ['Centrum']}),
        (d_ypr, {'Ypres': ['Centrum', 'Zillebeke']}),
        (d_kor, {'Kortrijk': ['Centrum', 'Heule', 'Bissegem', 'Marke'], 'Waregem': ['Centrum']}),
        (d_ost, {'Ostend': ['Centrum', 'Mariakerke', 'Zandvoorde'], 'Bredene': ['Centrum']}),
        (d_roe, {'Roeselare': ['Centrum', 'Rumbeke'], 'Izegem': ['Centrum']}),
        (d_tie, {'Tielt': ['Centrum']}),
        (d_veu, {'Veurne': ['Centrum'], 'De Panne': ['Centrum', 'Adinkerke']}),
    ]:
        for cname, areas in cities.items():
            add_city_with_areas(cname, did, areas)

    # ── Wallonia ──────────────────────────────────────────────
    wallonia = add_region('Wallonia')

    # Hainaut
    p_hain = add_province('Hainaut', wallonia)
    d_ath_w = add_city('Ath', p_hain)
    d_char = add_city('Charleroi', p_hain)
    d_mons = add_city('Mons', p_hain)
    d_mous = add_city('Mouscron', p_hain)
    d_soi = add_city('Soignies', p_hain)
    d_thu = add_city('Thuin', p_hain)
    d_tou = add_city('Tournai', p_hain)
    for did, cities in [
        (d_ath_w, {'Ath': ['Centre']}),
        (d_char, {'Charleroi': ['Ville-Haute', 'Ville-Basse', 'Gilly', 'Marcinelle', 'Montignies-sur-Sambre', 'Gosselies'],
                  'Châtelet': ['Centre']}),
        (d_mons, {'Mons': ['Centre', 'Jemappes', 'Cuesmes', 'Ghlin', 'Hyon'],
                  'La Louvière': ['Centre', 'Houdeng-Aimeries']}),
        (d_mous, {'Mouscron': ['Centre', 'Dottignies']}),
        (d_soi, {'Soignies': ['Centre']}),
        (d_thu, {'Thuin': ['Centre'], 'Binche': ['Centre']}),
        (d_tou, {'Tournai': ['Centre', 'Templeuve', 'Froyennes', 'Kain']}),
    ]:
        for cname, areas in cities.items():
            add_city_with_areas(cname, did, areas)

    # Liège
    p_lg = add_province('Liège', wallonia)
    d_huy = add_city('Huy', p_lg)
    d_lg_c = add_city('Liège', p_lg)
    d_ver = add_city('Verviers', p_lg)
    d_war = add_city('Waremme', p_lg)
    for did, cities in [
        (d_huy, {'Huy': ['Centre']}),
        (d_lg_c, {'Liège': ['Centre', 'Outremeuse', 'Guillemins', 'Sainte-Marguerite', 'Vennes', 'Angleur'],
                  'Seraing': ['Centre', 'Jemeppe-sur-Meuse'], 'Herstal': ['Centre']}),
        (d_ver, {'Verviers': ['Centre', 'Heusy', 'Ensival'], 'Eupen': ['Centre', 'Kettenis'], 'Spa': ['Centre']}),
        (d_war, {'Waremme': ['Centre']}),
    ]:
        for cname, areas in cities.items():
            add_city_with_areas(cname, did, areas)

    # Luxembourg
    p_lux = add_province('Luxembourg', wallonia)
    d_arl = add_city('Arlon', p_lux)
    d_bas = add_city('Bastogne', p_lux)
    d_mar = add_city('Marche-en-Famenne', p_lux)
    d_neu = add_city('Neufchâteau', p_lux)
    d_vir = add_city('Virton', p_lux)
    for did, cities in [
        (d_arl, {'Arlon': ['Centre'], 'Aubange': ['Centre', 'Athus']}),
        (d_bas, {'Bastogne': ['Centre']}),
        (d_mar, {'Marche-en-Famenne': ['Centre'], 'Durbuy': ['Centre']}),
        (d_neu, {'Neufchâteau': ['Centre'], 'Libramont-Chevigny': ['Centre']}),
        (d_vir, {'Virton': ['Centre']}),
    ]:
        for cname, areas in cities.items():
            add_city_with_areas(cname, did, areas)

    # Namur
    p_nam = add_province('Namur', wallonia)
    d_din = add_city('Dinant', p_nam)
    d_nam_c = add_city('Namur', p_nam)
    d_phi = add_city('Philippeville', p_nam)
    for did, cities in [
        (d_din, {'Dinant': ['Centre', 'Anseremme'], 'Ciney': ['Centre']}),
        (d_nam_c, {'Namur': ['Centre', 'Jambes', 'Salzinnes', 'Bomel', 'Belgrade'], 'Gembloux': ['Centre']}),
        (d_phi, {'Philippeville': ['Centre']}),
    ]:
        for cname, areas in cities.items():
            add_city_with_areas(cname, did, areas)

    # Walloon Brabant
    p_wbr = add_province('Walloon Brabant', wallonia)
    d_niv = add_city('Nivelles', p_wbr)
    for cname, areas in [('Nivelles', ['Centre']), ('Wavre', ['Centre', 'Limal']),
                          ('Waterloo', ['Centre']), ('Ottignies-Louvain-la-Neuve', ['Centre', 'Louvain-la-Neuve']),
                          ('Braine-l\'Alleud', ['Centre'])]:
        add_city_with_areas(cname, d_niv, areas)

    # ── Brussels ──────────────────────────────────────────────
    brussels = add_region('Brussels')
    p_bxl = add_province('Brussels-Capital', brussels)
    d_bxl = add_city('Brussels-Capital', p_bxl)
    bxl_data = {
        'Brussels City': ['Sablon', 'Marolles', 'European Quarter', 'Laeken', 'Neder-Over-Heembeek'],
        'Anderlecht': ['Cureghem', 'Veeweyde', 'Neerpede'],
        'Etterbeek': ['Jourdan', 'Chasse'],
        'Forest': ['Saint-Denis', 'Altitude Cent'],
        'Ixelles': ['Matongé', 'Châtelain', 'Flagey', 'Étangs d\'Ixelles'],
        'Jette': ['Miroir', 'Dieleghem'],
        'Molenbeek-Saint-Jean': ['Maritime', 'Karreveld', 'Scheutbos'],
        'Saint-Gilles': ['Parvis', 'Porte de Hal'],
        'Saint-Josse-ten-Noode': ['Botanique', 'Saint-Lazare'],
        'Schaerbeek': ['Josaphat', 'Helmet', 'Terdelt', 'Dailly'],
        'Uccle': ['Stalle', 'Fort Jaco', 'Dieweg', 'Prince d\'Orange'],
        'Watermael-Boitsfort': ['Le Logis', 'Floréal'],
        'Woluwe-Saint-Lambert': ['Tomberg', 'Kapelleveld'],
        'Woluwe-Saint-Pierre': ['Stockel', 'Joli-Bois'],
        'Auderghem': ['Transvaal', 'Chant d\'Oiseau'],
        'Evere': ['Paduwa', 'Germinal'],
    }
    for cname, areas in bxl_data.items():
        add_city_with_areas(cname, d_bxl, areas)

    if not get_campaigns():
        add_campaign('Default Campaign', 100, 10)

