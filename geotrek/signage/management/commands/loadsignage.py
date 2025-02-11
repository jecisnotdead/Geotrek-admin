import os.path

from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import Point
from django.contrib.gis.geos.error import GEOSException
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from geotrek.authent.models import default_structure
from geotrek.authent.models import Structure
from geotrek.core.models import Topology
from geotrek.signage.models import Signage, SignageType
from geotrek.infrastructure.models import InfrastructureCondition
from django.conf import settings


class Command(BaseCommand):
    help = 'Load a layer with point geometries in te structure model\n'
    can_import_settings = True
    counter = 0

    def add_arguments(self, parser):
        parser.add_argument('point_layer')
        parser.add_argument('--use-structure', action='store_true', dest='use_structure', default=False,
                            help='Allow to use structure for condition and type of infrastructures')
        parser.add_argument('--encoding', '-e', action='store', dest='encoding', default='utf-8',
                            help='File encoding, default utf-8')
        parser.add_argument('--name-field', '-n', action='store', dest='name_field', help='Name of the field that will be mapped to the Name field in Geotrek')
        parser.add_argument('--type-field', '-t', action='store', dest='type_field', help='Name of the field that will be mapped to the Type field in Geotrek')
        parser.add_argument('--condition-field', '-c', action='store', dest='condition_field', help='Name of the field that will be mapped to the Condition field in Geotrek')
        parser.add_argument('--structure-field', '-s', action='store', dest='structure_field', help='Name of the field that will be mapped to the Structure field in Geotrek')
        parser.add_argument('--description-field', '-d', action='store', dest='description_field', help='Name of the field that will be mapped to the Description field in Geotrek')
        parser.add_argument('--year-field', '-y', action='store', dest='year_field', help='Name of the field that will be mapped to the Year field in Geotrek')
        parser.add_argument('--code-field', action='store', dest='code_field', help='Name of the field that will be mapped to the Code field in Geotrek')
        parser.add_argument('--type-default', action='store', dest='type_default', help='Default value for Type field')
        parser.add_argument('--name-default', action='store', dest='name_default', help='Default value for Name field')
        parser.add_argument('--condition-default', action='store', dest='condition_default', help='Default value for Condition field')
        parser.add_argument('--structure-default', action='store', dest='structure_default', help='Default value for Structure field')
        parser.add_argument('--description-default', action='store', dest='description_default', default="",
                            help='Default value for Description field')
        parser.add_argument('--eid-field', action='store', dest='eid_field', help='External ID field')
        parser.add_argument('--year-default', action='store', dest='year_default', help='Default value for Year field')
        parser.add_argument('--code-default', action='store', dest='code_default', default="", help='Default value for Code field')

    def handle(self, *args, **options):
        verbosity = options.get('verbosity')

        filename = options['point_layer']

        if not os.path.exists(filename):
            raise CommandError('File does not exists at: %s' % filename)

        data_source = DataSource(filename, encoding=options.get('encoding'))

        use_structure = options.get('use_structure')
        field_name = options.get('name_field')
        field_infrastructure_type = options.get('type_field')
        field_condition_type = options.get('condition_field')
        field_structure_type = options.get('structure_field')
        field_description = options.get('description_field')
        field_implantation_year = options.get('year_field')
        field_code = options.get('code_field')
        field_eid = options.get('eid_field')

        sid = transaction.savepoint()
        structure_default = options.get('structure_default')

        try:
            for layer in data_source:
                if verbosity >= 2:
                    self.stdout.write("- Layer '{}' with {} objects found".format(layer.name, layer.num_feat))
                available_fields = layer.fields
                if (field_infrastructure_type and field_infrastructure_type not in available_fields)\
                        or (not field_infrastructure_type and not options.get('type_default')):
                    self.stdout.write(self.style.ERROR(
                        "Field '{}' not found in data source.".format(field_infrastructure_type)))
                    self.stdout.write(self.style.ERROR(
                        "Set it with --type-field, or set a default value with --type-default"))
                    break
                if (field_name and field_name not in available_fields)\
                        or (not field_name and not options.get('name_default')):
                    self.stdout.write(self.style.ERROR(
                        "Field '{}' not found in data source.".format(field_name)))
                    self.stdout.write(self.style.ERROR(
                        "Set it with --name-field, or set a default value with --name-default"))
                    break
                if field_condition_type and field_condition_type not in available_fields:
                    self.stdout.write(self.style.ERROR(
                        "Field '{}' not found in data source.".format(field_condition_type)))
                    self.stdout.write(self.style.ERROR(
                        "Change your --condition-field option"))
                    break
                if field_structure_type and field_structure_type not in available_fields:
                    self.stdout.write(self.style.ERROR(
                        "Field '{}' not found in data source.".format(field_structure_type)))
                    self.stdout.write(self.style.ERROR(
                        "Change your --structure-field option"))
                    break
                elif not field_structure_type and not structure_default:
                    structure = default_structure()
                elif not field_structure_type and structure_default:
                    try:
                        structure = Structure.objects.get(name=structure_default)
                        if verbosity > 0:
                            self.stdout.write("Signages will be linked to {}".format(structure))
                    except Structure.DoesNotExist:
                        self.stdout.write("Structure {} set in options doesn't exist".format(structure_default))
                        break
                if field_description and field_description not in available_fields:
                    self.stdout.write(self.style.ERROR(
                        "Field '{}' not found in data source.".format(field_description)))
                    self.stdout.write(self.style.ERROR(
                        "Change your --description-field option"))
                    break

                if field_implantation_year and field_implantation_year not in available_fields:
                    self.stdout.write(
                        self.style.ERROR("Field '{}' not found in data source.".format(field_implantation_year)))
                    self.stdout.write(self.style.ERROR(
                        "Change your --year-field option"))
                    break

                if field_eid and field_eid not in available_fields:
                    self.stdout.write(
                        self.style.ERROR("Field '{}' not found in data source.".format(field_eid)))
                    self.stdout.write(self.style.ERROR(
                        "Change your --eid-field option"))
                    break

                if field_code and field_code not in available_fields:
                    self.stdout.write(
                        self.style.ERROR("Field '{}' not found in data source.".format(field_code)))
                    self.stdout.write(self.style.ERROR(
                        "Change your --code-field option"))
                    break

                for feature in layer:
                    feature_geom = feature.geom
                    name = feature.get(field_name) if field_name in available_fields else options.get('name_default')
                    if feature_geom.geom_type == 'MultiPoint':
                        self.stdout.write(self.style.NOTICE("This object is a MultiPoint : %s" % name))
                        if len(feature_geom) < 2:
                            feature_geom = feature_geom[0].geos
                        else:
                            raise CommandError("One of your geometry is a MultiPoint object with multiple points")
                    type = feature.get(
                        field_infrastructure_type) if field_infrastructure_type in available_fields else options.get(
                        'type_default')
                    if field_condition_type in available_fields:
                        condition = feature.get(field_condition_type)
                    else:
                        condition = options.get('condition_default')
                    structure = Structure.objects.get(name=feature.get(field_structure_type)) \
                        if field_structure_type in available_fields else structure
                    description = feature.get(
                        field_description) if field_description in available_fields else options.get(
                        'description_default')
                    year = int(feature.get(
                        field_implantation_year)) if field_implantation_year in available_fields and feature.get(
                        field_implantation_year).isdigit() else options.get('year_default')
                    eid = feature.get(field_eid) if field_eid in available_fields else None
                    code = feature.get(field_code) if field_code in available_fields else options.get('code_default')

                    self.create_signage(feature_geom, name, type, condition, structure, description, year,
                                        verbosity, eid, use_structure, code)

            transaction.savepoint_commit(sid)
            if verbosity >= 2:
                self.stdout.write(self.style.NOTICE("{} objects created.".format(self.counter)))

        except Exception:
            self.stdout.write(self.style.ERROR("An error occured, rolling back operations."))
            transaction.savepoint_rollback(sid)
            raise

    def create_signage(self, geometry, name, type,
                       condition, structure, description, year, verbosity, eid, use_structure, code):

        infra_type, created = SignageType.objects.get_or_create(label=type,
                                                                structure=structure if use_structure else None)
        if created and verbosity:
            self.stdout.write("- SignageType '{}' created".format(infra_type))

        if condition:
            condition_type, created = InfrastructureCondition.objects.get_or_create(
                label=condition,
                structure=structure if use_structure else None)
            if created and verbosity:
                self.stdout.write("- Condition Type '{}' created".format(condition_type))
        else:
            condition_type = None

        with transaction.atomic():
            fields_without_eid = {
                'type': infra_type,
                'name': name,
                'condition': condition_type,
                'structure': structure,
                'description': description,
                'implantation_year': year,
                'code': code,
            }
            if eid:
                infra, created = Signage.objects.update_or_create(
                    eid=eid,
                    defaults=fields_without_eid
                )
                if verbosity > 0 and not created:
                    self.stdout.write("Update : %s with eid %s" % (name, eid))
            else:
                infra = Signage.objects.create(**fields_without_eid)
        if settings.TREKKING_TOPOLOGY_ENABLED:
            try:
                geometry = geometry.transform(settings.API_SRID, clone=True)
                geometry.coord_dim = 2
                serialized = '{"lng": %s, "lat": %s}' % (geometry.x, geometry.y)
                topology = Topology.deserialize(serialized)
                infra.mutate(topology)
            except IndexError:
                raise GEOSException('Invalid Geometry type.')
        else:
            if geometry.geom_type != 'Point':
                raise GEOSException('Invalid Geometry type.')
            geometry = geometry.transform(settings.SRID, clone=True)
            infra.geom = Point(geometry.x, geometry.y)
            infra.save()
        self.counter += 1

        return infra
