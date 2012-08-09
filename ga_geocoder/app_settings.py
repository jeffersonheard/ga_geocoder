APP_LOGGING = {
    'ga_geocoder.utils' : {
        'handlers': ['console'],
        'level': 'DEBUG',
        'propagate': False,
    },
    'ga_geocoder.geocoder' : {
        'handlers': ['console'],
        'level': 'DEBUG',
        'propagate': False,
    }
}

#: The path that geocoder indexes will be stored to
GEO_INDEX_PATH='/Users/jeff/Source/ga-1.4/ga_geocoder_indexes'

#: URLs for Nominatim OSM services for OSM geocoding.
NOMINATIM_URLS=[
    'http://nominatim.openstreetmap.org', # bad for bulk geocoding!!!
]

