from osgeo import osr, ogr
from ga_geocoder.geocoder import ExactGeocoder

EXACT=0

from logging import getLogger

log = getLogger(__name__)

def geocoder_from_ogr(name, method, ogr_filename, layer, field, srid=4326, append=False, case_sensitive=False, long_codes=False):
    ds = ogr.Open(ogr_filename)

    if not ds:
        raise OSError("File not found or is not an ogr dataset")

    layer = ds.GetLayerByName(layer)

    # create a coordinate transformation to the target spatial reference system.
    t_srs = osr.SpatialReference()
    t_srs.ImportFromEPSG(srid)
    s_srs = layer.GetSpatialRef()
    crx = osr.CoordinateTransformation(s_srs, t_srs)

    coding = {}
    for feature in layer:
        code = feature.__getattr__(field)

        if code:
            g = feature.GetGeometryRef()
            g.Transform(crx)
            coding[code] = g.ExportToJson()

    log.info("Ingested {n} codes".format(n=len(coding)))

    if method == EXACT:
        coder = ExactGeocoder(name, case_sensitive, long_codes, srid, clear=not append)
        coder.bulk_load(coding, lambda x: x)
    else:
        raise NotImplemented("Only exact geocoders are supported at this time")


    return coder