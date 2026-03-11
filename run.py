#!/usr/bin/env python
"""Application entry point"""
import os
from app import create_app
from config import config

app = create_app()

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=config.FLASK_DEBUG
    )
