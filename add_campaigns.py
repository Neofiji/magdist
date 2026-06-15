#!/usr/bin/env python3
"""
Add sample campaigns to database
"""
import models

def add_sample_campaigns():
    """Add sample magazine distribution campaigns"""
    
    campaigns = [
        ('Winter Campaign 2026', 500, 12),
        ('Spring Campaign 2026', 600, 10),
        ('Summer Campaign 2026', 800, 15),
        ('Fall Campaign 2026', 700, 12),
    ]
    
    for name, packs, units_per_pack in campaigns:
        models.add_campaign(name, packs, units_per_pack)
        print(f"✓ Added campaign: {name}")


if __name__ == '__main__':
    models.init_db()
    add_sample_campaigns()
