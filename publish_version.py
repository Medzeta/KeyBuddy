#!/usr/bin/env python3
"""
Script för att publicera en ny version av KeyBuddy
Ökar versionen med 0.01 för varje publicering
"""

import sys
import os
sys.path.append('src')

from src.core.version_manager import VersionManager

def publish_new_version():
    """Publicera ny version"""
    print("=== KeyBuddy Version Publisher ===")
    
    version_manager = VersionManager()
    current_version = version_manager.get_current_version()
    
    print(f"Nuvarande version: {current_version}")
    
    # Öka versionen
    new_version = version_manager.increment_version('minor')
    
    print(f"Ny version: {new_version}")
    print(f"Build nummer: {version_manager.get_build_number(new_version)}")
    
    # Visa version info
    version_info = version_manager.get_version_info()
    print(f"Fullständig version info: {version_info}")
    
    print("✅ Version publicerad!")
    return new_version

if __name__ == "__main__":
    publish_new_version()
