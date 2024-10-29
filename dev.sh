#!/bin/bash
# Quick switch to run a development environment on a seperate port
gunicorn app:app --bind 0.0.0.0:$1
