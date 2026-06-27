"""
Passenger WSGI entry point for Namecheap shared hosting.
This file is auto-detected by Passenger and points to the Flask app.
"""
import sys
import os

# Ensure the app directory is on the Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import app as application
