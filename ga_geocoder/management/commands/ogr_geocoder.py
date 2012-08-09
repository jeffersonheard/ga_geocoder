from django.core.management.base import BaseCommand, make_option
from ga_geocoder import utils

class Command(BaseCommand):
    args = "<name method ogr_dataset layer field ...>"
    help = "Creates a geocoder from an ogr dataset"

    option_list = BaseCommand.option_list + (
        make_option('--case-sensitive', action='store_true', dest='case_sensitive', default=False, help=''),
        make_option('--long-codes', action='store_true',  dest='long_codes', default=False, help=''),
        make_option('--overwrite', action='store_true',  dest='append', default=False, help=''),
        make_option('--srid', action='store',  dest='srid', default=4326, help=''),
    )

    def handle(self, *args, **options):
        options['name']=args[0]
        options['method']=args[1]
        options['ogr_filename']=args[2]
        options['layer']=args[4]
        options['field']=args[3]
        options['srid']=int(options['srid'])

        utils.geocoder_from_ogr(**options)

