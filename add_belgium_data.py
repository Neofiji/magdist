#!/usr/bin/env python3
"""
Add sample Belgium geographic hierarchy to database
"""
import models

def add_belgium_data():
    """Add Belgium regions, provinces, cities, municipalities, neighborhoods"""
    
    # Belgium Regions (Flanders, Wallonia, Brussels)
    flanders_id = models.add_region('Flanders')
    wallonia_id = models.add_region('Wallonia')
    brussels_id = models.add_region('Brussels')
    
    # Flanders Provinces
    vl_brabant = models.add_province('Flemish Brabant', flanders_id)
    west_flanders = models.add_province('West Flanders', flanders_id)
    east_flanders = models.add_province('East Flanders', flanders_id)
    limburg = models.add_province('Limburg', flanders_id)
    antwerp = models.add_province('Antwerp', flanders_id)
    
    # Wallonia Provinces
    walloon_brabant = models.add_province('Walloon Brabant', wallonia_id)
    hainaut = models.add_province('Hainaut', wallonia_id)
    liege = models.add_province('Liège', wallonia_id)
    luxembourg = models.add_province('Luxembourg', wallonia_id)
    namur = models.add_province('Namur', wallonia_id)
    
    # Brussels Capital
    brussels_prov = models.add_province('Brussels-Capital', brussels_id)
    
    # Sample cities in Flanders
    brussels_city = models.add_city('Brussels', brussels_prov)
    leuven = models.add_city('Leuven', vl_brabant)
    gent = models.add_city('Gent', east_flanders)
    brugge = models.add_city('Brugge', west_flanders)
    antwerp_city = models.add_city('Antwerp', antwerp)
    
    # Sample municipalities in Brussels
    brussels_munic = models.add_municipality('Brussels City', brussels_city)
    uccle_munic = models.add_municipality('Uccle', brussels_city)
    etterbeek_munic = models.add_municipality('Etterbeek', brussels_city)
    
    # Sample municipalities in Gent
    gent_munic = models.add_municipality('Gent', gent)
    
    # Sample municipalities in Brugge
    brugge_munic = models.add_municipality('Brugge', brugge)
    
    # Sample municipalities in Leuven
    leuven_munic = models.add_municipality('Leuven', leuven)

    # Sample neighborhoods in Brussels
    brussels_center = models.add_neighborhood('Sablon', brussels_munic)
    brussels_north = models.add_neighborhood('Schaerbeek', brussels_munic)
    uccle_south = models.add_neighborhood('Stalle', uccle_munic)
    etterbeek_east = models.add_neighborhood('Ixelles', etterbeek_munic)
    
    # Sample neighborhoods in Gent
    gent_center = models.add_neighborhood('Sint-Jacobs', gent_munic)
    gent_north = models.add_neighborhood('Citadelpark', gent_munic)
    
    # Sample neighborhoods in Brugge
    brugge_center = models.add_neighborhood('Centrum', brugge_munic)

    # Sample neighborhoods in Leuven
    leuven_center = models.add_neighborhood('Heverlee', leuven_munic)

    # Sample neighborhoods in Antwerp
    antwerp_center = models.add_neighborhood('Diamond District', antwerp_munic)
    antwerp_south = models.add_neighborhood('Deurne', antwerp_munic)
    
    print("✓ Belgium geographic data added successfully")


if __name__ == '__main__':
    models.init_db()
    add_belgium_data()
