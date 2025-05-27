---
title: osm-parser-api
emoji: 📄
colorFrom: blue
colorTo: green
sdk: docker
app_file: main.py
pinned: false
---

# OSM Parser API

The OSM Parse API is a FastAPI-based web service that parses OpenStudio Model (.osm) files and extracts building component data through a REST API interface. 
This API is designed for building energy modeling workflows where users need to programmatically extract structured data from OpenStudio Model files. **It's specifically configured for deployment on Hugging Face Spaces platform**, making it accessible as a cloud service for processing .osm files without requiring local OpenStudio installations.

This API parses uploaded OpenStudio Model (.osm) files to extract building component data.
It uses the OpenStudio SDK (via pip) and the roruizf/OpenStudio-Toolkit.

**Endpoint:** `/parse` (POST)
- **file**: OSM file upload (required)
- **object_types**: Query parameter list (optional, e.g., `?object_types=spaces&object_types=surfaces`) - defaults to types defined in `VALID_OBJECT_TYPES`.

See the `/docs` path on the running Space for the interactive Swagger UI.