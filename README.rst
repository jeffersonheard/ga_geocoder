ga_geocoder - Flexible geocoding for geoanalytics
#################################################

ga_geocoder is a flexible geocoder for Geoanalytics.  It requires
ga_spatialnosql and the "requests" library (``pip install requests``).  There
are a number of geocoders in ga_gecoder/geocoder.py that you can use to geocode
either to open streetmap data (although you'll want to install your own version
of Nominatim if you want to do bulk geocoding) or codes in your own geographic
data (such as US Census FIPS codes or other kinds of meaningful names).
Documentation is scant right now, as I've just finished coding the initial run
of coders.  There will soon be an NGram based geocoder as well that will handle
geocoding with spelling mistakes in a manner similar to the exact-geocoding on
well-known names.  

Geocodes are returned as Python dicts that conform to the GeoJSON spec (if you
do a json.dumps(code) you will get a GeoJSON document).  See the tests.py for
examples of usage.  
