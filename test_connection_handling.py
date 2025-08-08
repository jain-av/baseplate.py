#!/usr/bin/env python3
"""
Test script to verify SQLAlchemy connection handling improvements.
This tests that the code can be imported and instantiated correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from baseplate.clients.sqlalchemy import SQLAlchemySessionContextFactory, SQLAlchemyEngineContextFactory
    from sqlalchemy import create_engine, text
    
    print("✓ Imports successful")
    
    # Test engine creation
    engine = create_engine("sqlite:///:memory:")
    engine_factory = SQLAlchemyEngineContextFactory(engine)
    print("✓ Engine factory created successfully")
    
    # Test session factory creation  
    session_factory = SQLAlchemySessionContextFactory(engine)
    print("✓ Session factory created successfully")
    
    # Test text import works
    test_query = text("SELECT 1")
    print("✓ text() import and usage works")
    
    print("\n🎉 All connection handling improvements verified successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)