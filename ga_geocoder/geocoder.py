from django.contrib.gis.geos.geometry import GEOSGeometry
from django.conf import settings
import app_settings
import UserDict
from ga_spatialnosql.db.mongo import GeoJSONCollection
from ga_geocoder.parsers.independent import ci_code, ci_shortcode, cs_code, cs_shortcode
import json
from logging import getLogger

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
            db=settings.MONGODB_ROUTES['ga_geocoder'],
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
            'properties' : { 'code' : code, 'original' : orig },
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
                'properties' : { 'code' : code, 'original' : orig }
            })

        log.debug('bulk_load got {n} features'.format(n=len(features)))


        fc['features'] = features
        self.code_store.insert_features(fc)

    def __getitem__(self, code):
        val = self.code_store.coll.find_one(code)
        if val:
            return val
        else:
            raise KeyError(code)


    def __delitem__(self, code):
        self.code_store.coll.remove(code)

    def keys(self):
        return self.code_store.keys()

    def bulk_geocode(self, codes):
        chunks = _chunk(codes)
        for chunk in chunks:
            features = self.code_store.find_features(spec={ "_id" : { "$in" : chunk }})
            for feature in features:
                yield feature['_id'], feature

    def reverse_geocode(self, geometry):
        val = self.code_store.find_features(geo_query={'bboverlaps' : geometry})
        try:
            return val.next()['_id']
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

    def bulk_geocode(self, codes):
        pass

    def reverse_geocode(self, geometry):
        pass

    def drop(self):
        pass

class OpenStreetMapGeocoder(object):
    def __init__(self):
        pass

    def __getitem__(self, code):
        pass

    def bulk_geocode(self, codes):
        pass

    def reverse_geocode(self, geometry):
        pass

class GoogleGeocoder(object):
    def __init__(self):
        pass

    def __getitem__(self, code):
        pass

