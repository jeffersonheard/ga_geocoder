from django.contrib.gis.geos.geometry import GEOSGeometry, Point, Polygon
from django.conf import settings
import app_settings
import UserDict
from ga_spatialnosql.db.mongo import GeoJSONCollection
from ga_geocoder.parsers.independent import ci_code, ci_shortcode, cs_code, cs_shortcode
import json
from logging import getLogger
import requests

log = getLogger(__name__)

def _chunk(seq, size=1000):
    chunk = []
    N = 0
    for it in seq:
        chunk.append(it)
        N += 1
        if N == size:
            yield chunk
            N=0
            del chunk[:]
    if chunk:
        yield chunk

class ExactGeocoder(object, UserDict.DictMixin):
    def __init__(self, name, case_sensitive=False, long_codes=False, srid=4326, fc=None, clear=False):
        self.code_store = GeoJSONCollection(
            db=settings.MONGODB_ROUTES['ga_geocoder'] if 'ga_geocoder' in settings.MONGODB_ROUTES else settings.MONGODB_ROUTES['default'],
            collection=name,
            index_path=app_settings.GEO_INDEX_PATH,
            srid=srid,
            fc=fc,
            clear=clear
        )
        self.code_store['kind'] = 'exact'

        self.serialize = lambda x: x.json
        self.deserialize = lambda x: GEOSGeometry(x, srid=self.code_store.srid)

        #
        # setup parser
        #
        case_sensitive = self.code_store['case_sensitive'] if 'case_sensitive' in self.code_store else case_sensitive
        long_codes = self.code_store['long_codes'] if 'long_codes' in self.code_store else long_codes

        self.code_store['name'] = name
        self.code_store['case_sensitive'] = case_sensitive
        self.code_store['long_codes'] = long_codes

        if case_sensitive and long_codes:
            self.parse = ci_shortcode
        elif case_sensitive:
            self.parse = ci_code
        elif long_codes:
            self.parse = cs_shortcode
        else:
            self.parse = cs_code

    def __setitem__(self, code, geometry):
        orig = code
        code = self.parse(code)

        self.code_store.insert_features({
            "_id" : code,
            'type' : 'Feature',
            'properties' : { 'code' : code, 'name' : orig },
            'geometry' : self.serialize(geometry)
        })

    def bulk_load(self, code_to_geom, geom_serializer=None):
        fc = {
          'type' : "FeatureCollection",
        }

        log.debug("Beginning bulk load of {name}".format(name=self.code_store['name']))

        features = []
        for code, geom in code_to_geom.items():
            if geom_serializer:
                geom = json.loads(geom_serializer(geom))
            else:
                geom = json.loads(self.serialize(geom))

            orig = code
            code = self.parse(code)
            features.append({
                '_id' : code,
                'geometry' : geom,
                'properties' : { 'code' : code, 'name' : orig }
            })

        log.debug('bulk_load got {n} features'.format(n=len(features)))


        fc['features'] = features
        self.code_store.insert_features(fc)

    def __getitem__(self, code):
        srid=None
        if isinstance(code, tuple):
            code, srid = code

        val = self.code_store.coll.find_one(code)
        if val:
            if srid:
                g = GEOSGeometry(json.dumps(val['geometry']), srid=self.code_store.srid)
                g.transform(srid)
                val['geometry'] = json.loads(g.json)
            return val
        else:
            raise KeyError(code)


    def __delitem__(self, code):
        self.code_store.coll.remove(code)

    def keys(self):
        return self.code_store.keys()

    def bulk_geocode(self, codes, srid=None):
        chunks = _chunk(codes)
        for chunk in chunks:
            features = self.code_store.find_features(spec={ "_id" : { "$in" : chunk }})
            if srid:
                for feature in features:
                    g = GEOSGeometry(json.dumps(feature['geometry']), srid=self.code_store.srid)
                    g.transform(srid)
                    feature['geometry'] = json.loads(g.json)
                    yield feature['_id'], feature
            else:
                for feature in features:
                    yield feature['_id'], feature

    def reverse_geocode(self, geometry):
        val = self.code_store.find_features(geo_query={'bboverlaps' : geometry})
        try:
            return val.next()
        except StopIteration:
            return None

    def drop(self):
        self.code_store.drop()
        self.code_store = None

class NGramGeocoder(object):
    def __init__(self, name, srid=4326, fc=None, clear=False):
        pass

    def __getitem__(self, code):
        pass

    def __delitem__(self, code):
        pass

    def __setitem__(self, code, geometry):
        pass

    def bulk_geocode(self, codes, srid=None):
        pass

    def reverse_geocode(self, geometry):
        pass

    def drop(self):
        pass

class OpenStreetMapGeocoder(object):
    HOUSE=0
    COUNTRY=18

    def __init__(self):
        self.index = 0

    def _get_url(self):
        self.index = (self.index+1) if (self.index+1) < len(app_settings.NOMINATIM_URLS) else 0
        return app_settings.NOMINATIM_URLS[self.index]

    def __getitem__(self, name):
        srid=None
        transform = lambda x,y:[float(x),float(y)]
        if isinstance(name, tuple):
            name, srid = name
            def transform(x, y):
                a = Point(float(x), float(y), srid=4326)
                a.transform(srid)
                return [a.x, a.y]

        r = requests.get(self._get_url() + "/search", params={'q' : name, 'format' : 'json'})
        if r.status_code == requests.codes.ok:
            locations = r.json
            if len(locations) == 0:
                raise KeyError(name)
            else:
                # convert the response to GeoJSON
                locations = [{
                    'type' : 'Feature',
                    "_id" : location['place_id'],
                    'geometry' : { "type" : "Point", "coordinates" : transform(location['lon'], location['lat']) },
                    'properties' : dict(name=location['display_name'], **location),
                } for location in locations]
                location = locations[0]
                location['properties']['alternates'] = locations[1:]

                return location
        else:
            raise IOError(str((name, r.status_code, r.text)))


    def bulk_geocode(self, names, srid=None):
        if srid:
            for name in names:
                try:
                    location = self[name, srid]
                    yield location['properties']['display_name'], location
                except KeyError:
                    pass
        else:
            for name in names:
                try:
                    location = self[name]
                    yield location['properties']['display_name'], location
                except KeyError:
                    pass



    def reverse_geocode(self, geometry, lod=HOUSE):
        if geometry.srid is not None and geometry.srid != 4326:
            geometry.transform(4326)

        r = requests.get(self._get_url() + "/reverse", params={ "format" : "json", "zoom" : lod, "lon" : geometry.x, "lat" : geometry.y, "addressdetails" : 1 })
        if r.status_code == requests.codes.ok:
            location = r.json
            if 'polygonpoints' in location:
                geom = Polygon(tuple(
                    [(float(x),float(y)) for x, y in location['polygonpoints']]
                ), srid=4326)
            else:
                geom = Point(float(location['lon']), float(location['lat']), srid=4326)

            if geometry.srid is not None and geometry.srid != 4326:
                geom.transform(geometry.srid)

            return {
                'type' : "Feature",
                'geometry' : geom.json,
                'properties' : dict(_id=location['place_id'], **location)
            }
        else:
            raise IOError(str(((geometry.x, geometry.y, geometry.srid), r.status_code, r.text)))
