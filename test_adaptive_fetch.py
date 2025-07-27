#!/usr/bin/env python3
"""
Test script to verify adaptive fetching logic for Trakt lists
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from core.business_logic import init_globals, _get_trakt_list
from media.trakt import Trakt

def test_boxoffice_adaptive_fetch():
    """Test adaptive fetching for boxoffice list"""
    
    # Initialize with config
    init_globals('/home/weaver/apps/media-streaming/config/config.json', '', '')
    
    # Import after init
    from core.business_logic import cfg, log
    
    print("Testing Trakt boxoffice list fetching...")
    
    # Create Trakt instance
    trakt = Trakt(cfg)
    
    # Test 1: Fetch small limit
    print("\n=== Test 1: Fetch 3 items ===")
    result1 = _get_trakt_list(
        trakt, 'movies', 'boxoffice', None, False, None, 
        None, None, None, None, None, limit=3
    )
    if result1:
        print(f"✓ Fetched {len(result1)} movies with limit=3")
        for i, movie in enumerate(result1[:3]):
            title = movie['movie']['title']
            year = movie['movie']['year']
            print(f"  {i+1}. {title} ({year})")
    else:
        print("✗ Failed to fetch movies")
        return
    
    # Test 2: Fetch larger limit
    print("\n=== Test 2: Fetch 10 items ===")
    result2 = _get_trakt_list(
        trakt, 'movies', 'boxoffice', None, False, None,
        None, None, None, None, None, limit=10
    )
    if result2:
        print(f"✓ Fetched {len(result2)} movies with limit=10")
        print(f"Comparison: limit=3 got {len(result1)}, limit=10 got {len(result2)}")
    else:
        print("✗ Failed to fetch movies with larger limit")
    
    # Test 3: Fetch unlimited
    print("\n=== Test 3: Fetch all available ===")
    result3 = _get_trakt_list(
        trakt, 'movies', 'boxoffice', None, False, None,
        None, None, None, None, None, limit=None
    )
    if result3:
        print(f"✓ Fetched {len(result3)} movies with no limit")
        print(f"Total available in boxoffice list: {len(result3)}")
        
        # Show what the adaptive fetching would be working with
        print(f"\n📊 Analysis for adaptive fetching:")
        print(f"   - Total available: {len(result3)}")
        print(f"   - If you want 1 movie but all {min(3, len(result3))} fetched exist in Radarr")
        print(f"   - Logic should try to fetch more (up to {len(result3)} total)")
        
        if len(result3) <= 3:
            print(f"   ⚠️  Limited list: Only {len(result3)} items total, can't fetch more")
        else:
            print(f"   ✓ Sufficient items: Can fetch up to {len(result3)} for adaptive logic")
    else:
        print("✗ Failed to fetch all movies")

if __name__ == "__main__":
    test_boxoffice_adaptive_fetch()
