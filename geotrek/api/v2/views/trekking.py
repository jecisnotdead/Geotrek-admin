from django.conf import settings
from django.contrib.gis.db.models.functions import Transform
from django.db.models import F, Prefetch, Q
from django.db.models.aggregates import Count
from django.forms.fields import IntegerField
from django.utils.translation import activate
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from geotrek.api.v2 import filters as api_filters, serializers as api_serializers, viewsets as api_viewsets
from geotrek.api.v2.decorators import cache_response_detail
from geotrek.api.v2.functions import Length3D
from geotrek.api.v2.renderers import SVGProfileRenderer
from geotrek.common.models import Attachment, AccessibilityAttachment
from geotrek.common.utils import intersecting
from geotrek.core.models import Topology
from geotrek.trekking import models as trekking_models
from geotrek.api.v2.cache import ListCacheResponseMixin
from hashlib import md5
from django_filters import rest_framework as filters  # noqa
from django_filters import Filter  # noqa
from geotrek.trekking.models import Trek


class WebLinkCategoryViewSet(api_viewsets.GeotrekViewSet):
    serializer_class = api_serializers.WebLinkCategorySerializer
    queryset = trekking_models.WebLinkCategory.objects.all()


class TrekViewSet(api_viewsets.GeotrekGeometricViewset):
    filter_backends = api_viewsets.GeotrekGeometricViewset.filter_backends + (
        api_filters.GeotrekTrekQueryParamsFilter,
        api_filters.NearbyContentFilter,
        api_filters.UpdateOrCreateDateFilter,
        api_filters.GeotrekRatingsFilter
    )
    serializer_class = api_serializers.TrekSerializer

    def get_queryset(self):
        activate(self.request.GET.get('language'))
        return trekking_models.Trek.objects.existing() \
            .select_related('topo_object') \
            .prefetch_related('topo_object__aggregations', 'accessibilities',
                              Prefetch('attachments',
                                       queryset=Attachment.objects.select_related('license', 'filetype', 'filetype__structure')),
                              Prefetch('attachments_accessibility',
                                       queryset=AccessibilityAttachment.objects.select_related('license')),
                              Prefetch('web_links',
                                       queryset=trekking_models.WebLink.objects.select_related('category'))) \
            .annotate(geom3d_transformed=Transform(F('geom_3d'), settings.API_SRID),
                      length_3d_m=Length3D('geom_3d')) \
            .order_by("name")  # Required for reliable pagination

    @cache_response_detail()
    def retrieve(self, request, pk=None, format=None):
        """ Return detail view even for unpublished treks that are children of other published treks """
        qs_filtered = self.filter_published_lang_retrieve(request, self.get_queryset())
        trek = get_object_or_404(qs_filtered, pk=pk)
        return Response(self.get_serializer(trek).data)

    def filter_published_lang_retrieve(self, request, queryset):
        """ filter trek by publication language (including parents publication language) """
        qs = queryset
        language = request.GET.get('language', 'all')
        associated_published_fields = [f.name for f in qs.model._meta.get_fields() if f.name.startswith('published')]

        if language == 'all':
            # no language specified. Check for all.
            q = Q()
            for lang in settings.MODELTRANSLATION_LANGUAGES:
                field_name = 'published_{}'.format(lang)
                if field_name in associated_published_fields:
                    field_name_parent = 'trek_parents__parent__published_{}'.format(lang)
                    q |= Q(**{field_name: True}) | Q(**{field_name_parent: True})
            qs = qs.filter(q)
        else:
            # one language is specified
            field_name = 'published_{}'.format(language)
            field_name_parent = 'trek_parents__parent__published_{}'.format(language)
            qs = qs.filter(Q(**{field_name: True}) | Q(**{field_name_parent: True}))
        return qs.distinct()

    @action(detail=True, url_name="dem")
    @cache_response_detail()
    def dem(self, request, *args, **kwargs):
        trek = self.get_object()
        return Response(trek.get_elevation_area())

    @action(detail=True, url_name="profile",
            renderer_classes=api_viewsets.GeotrekGeometricViewset.renderer_classes + [SVGProfileRenderer, ])
    @cache_response_detail()
    def profile(self, request, *args, **kwargs):
        trek = self.get_object()
        if request.accepted_renderer.format == 'svg':
            content = trek.get_elevation_profile_and_limits()
        else:
            content = trek.get_formatted_elevation_profile_and_limits()
        return Response(content)


class TourViewSet(TrekViewSet):
    serializer_class = api_serializers.TourSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.annotate(count_children=Count('trek_children'))\
            .filter(count_children__gt=0)
        return qs


class PracticeViewSet(api_viewsets.GeotrekViewSet):
    filter_backends = api_viewsets.GeotrekViewSet.filter_backends + (api_filters.TrekRelatedPortalFilter,)
    serializer_class = api_serializers.PracticeSerializer
    queryset = trekking_models.Practice.objects.all()

    @cache_response_detail()
    def retrieve(self, request, pk=None, format=None):
        # Allow to retrieve objects even if not visible in list view
        elem = get_object_or_404(trekking_models.Practice, pk=pk)
        serializer = api_serializers.PracticeSerializer(elem, many=False, context={'request': request})
        return Response(serializer.data)


class TrekRatingScaleViewSet(api_viewsets.GeotrekViewSet):
    filter_backends = api_viewsets.GeotrekViewSet.filter_backends + (api_filters.GeotrekRatingScaleFilter, )
    serializer_class = api_serializers.TrekRatingScaleSerializer
    queryset = trekking_models.RatingScale.objects \
        .order_by('pk')  # Required for reliable pagination


class TrekRatingViewSet(api_viewsets.GeotrekViewSet):
    filter_backends = api_viewsets.GeotrekViewSet.filter_backends + (
        api_filters.GeotrekRatingFilter,
        api_filters.TrekRelatedPortalFilter,
    )
    serializer_class = api_serializers.TrekRatingSerializer
    queryset = trekking_models.Rating.objects \
        .order_by('order', 'name', 'pk')  # Required for reliable pagination


class NetworkViewSet(api_viewsets.GeotrekViewSet):
    filter_backends = api_viewsets.GeotrekViewSet.filter_backends + (api_filters.TrekRelatedPortalFilter,)
    serializer_class = api_serializers.NetworkSerializer
    queryset = trekking_models.TrekNetwork.objects.all()

    @cache_response_detail()
    def retrieve(self, request, pk=None, format=None):
        # Allow to retrieve objects even if not visible in list view
        elem = get_object_or_404(trekking_models.TrekNetwork, pk=pk)
        serializer = api_serializers.NetworkSerializer(elem, many=False, context={'request': request})
        return Response(serializer.data)


class DifficultyViewSet(api_viewsets.GeotrekViewSet):
    filter_backends = api_viewsets.GeotrekViewSet.filter_backends + (api_filters.TrekRelatedPortalFilter,)
    serializer_class = api_serializers.TrekDifficultySerializer
    queryset = trekking_models.DifficultyLevel.objects.all()

    @cache_response_detail()
    def retrieve(self, request, pk=None, format=None):
        # Allow to retrieve objects even if not visible in list view
        elem = get_object_or_404(trekking_models.DifficultyLevel, pk=pk)
        serializer = api_serializers.TrekDifficultySerializer(elem, many=False, context={'request': request})
        return Response(serializer.data)


# Une classe qui sert juste de signal pour les filtres où il faut vérifier la datetime de dernier
# changement dans la table stats pour le cache des list endpoints.
class LinkedObjectFilter(Filter):
    model = None


class NearTrekFilter(LinkedObjectFilter):

    model = Trek
    field_class = IntegerField

    def filter(self, qs, value):
        # Le traitement du filtre 'trek' précédemment dans le POI FilterBackend
        trek = value
        if trek is not None:
            try:
                t = Trek.objects.get(pk=trek)
            except Trek.DoesNotExist:
                return qs.none()
            if settings.TREKKING_TOPOLOGY_ENABLED:
                qs = Topology.overlapping(t, qs)
            else:
                qs = intersecting(qs, t)
            qs = qs.exclude(pk__in=t.pois_excluded.all())

        return qs


# Ce qui pourrait remplacer le POI FilterBackend à terme
class POIFilterSet(filters.FilterSet):

    # Du coup fini les 500 si la valeur de 'trek' n'est pas un ID
    trek = NearTrekFilter(
        label="trek_id", min_value=1,
        help_text="Filter by a trek id. It will show only the POIs related to this trek."
    )
    # Transfert des descriptions des filtres de l'API :
    # `help_text` param est utilisé par `DjangoFilterBackend.get_schema_fields`,
    # on laisserait tomber la localisation du nom du filtre -> n'a pas de sens et pas traduit,
    # on peut utiliser `label` pour le placeholder (`DjangoFilterBackend.get_schema_fields` toujours).


# dummy value pour tester en attendant la table stats
LAST_CHANGE = '2022-01-27T16:10:00+00:01'


class POIViewSet(ListCacheResponseMixin, api_viewsets.GeotrekGeometricViewset):
    filter_backends = api_viewsets.GeotrekGeometricViewset.filter_backends + (
        api_filters.GeotrekPOIFilter,
        api_filters.NearbyContentFilter,
        api_filters.UpdateOrCreateDateFilter
    )
    serializer_class = api_serializers.POISerializer
    filterset_class = POIFilterSet
    queryset = trekking_models.POI.objects.existing() \
        .select_related('topo_object', 'type', ) \
        .prefetch_related('topo_object__aggregations',
                          Prefetch('attachments',
                                   queryset=Attachment.objects.select_related('license', 'filetype', 'filetype__structure'))) \
        .annotate(geom3d_transformed=Transform(F('geom_3d'), settings.API_SRID)) \
        .order_by('pk')  # Required for reliable pagination

    @staticmethod
    def get_last_change_datetime(*args, **kwargs):
        # TODO: fetch last change datetime from the stats table, handle a model as param
        return LAST_CHANGE

    def get_related_entities_cache_key(self):
        last_changes = []
        for field, filter_klass in self.filterset_class.get_filters().items():
            if isinstance(filter_klass, LinkedObjectFilter):
                last_change_dt = self.get_last_change_datetime(filter_klass.model)
                last_changes.append(field + "-" + last_change_dt)
        last_changes.sort()
        return ":".join(last_changes)

    def get_list_cache_key(self):
        """ return specific list cache key based on list last_update object """
        last_update = self.get_queryset().model.last_update_and_count.get('last_update')
        last_update = last_update.isoformat() if last_update else '0000-00-00'

        related_last_updates = self.get_related_entities_cache_key()

        return f"{self.get_base_cache_string()}:{last_update}:{related_last_updates}"

    def list_cache_key_func(self, **kwargs):
        list_cache_key = self.get_list_cache_key()
        print("list_cache_key", list_cache_key)
        return md5(list_cache_key.encode("utf-8")).hexdigest()


class POITypeViewSet(api_viewsets.GeotrekViewSet):
    serializer_class = api_serializers.POITypeSerializer
    queryset = trekking_models.POIType.objects.all()


class AccessibilityViewSet(api_viewsets.GeotrekViewSet):
    filter_backends = api_viewsets.GeotrekViewSet.filter_backends + (api_filters.TrekRelatedPortalFilter,)
    serializer_class = api_serializers.AccessibilitySerializer
    queryset = trekking_models.Accessibility.objects.all()


class AccessibilityLevelViewSet(api_viewsets.GeotrekViewSet):
    filter_backends = api_viewsets.GeotrekViewSet.filter_backends + (api_filters.TrekRelatedPortalFilter,)
    serializer_class = api_serializers.AccessibilityLevelSerializer
    queryset = trekking_models.AccessibilityLevel.objects.all()


class RouteViewSet(api_viewsets.GeotrekViewSet):
    filter_backends = api_viewsets.GeotrekViewSet.filter_backends + (api_filters.TrekRelatedPortalFilter,)
    serializer_class = api_serializers.RouteSerializer
    queryset = trekking_models.Route.objects.all()

    @cache_response_detail()
    def retrieve(self, request, pk=None, format=None):
        # Allow to retrieve objects even if not visible in list view
        elem = get_object_or_404(trekking_models.Route, pk=pk)
        serializer = api_serializers.RouteSerializer(elem, many=False, context={'request': request})
        return Response(serializer.data)


class ServiceTypeViewSet(api_viewsets.GeotrekViewSet):
    serializer_class = api_serializers.ServiceTypeSerializer
    queryset = trekking_models.ServiceType.objects.all().order_by('pk')

    @cache_response_detail()
    def retrieve(self, request, pk=None, format=None):
        # Allow to retrieve objects even if not visible in list view
        elem = get_object_or_404(trekking_models.ServiceType, pk=pk)
        serializer = api_serializers.ServiceTypeSerializer(elem, many=False, context={'request': request})
        return Response(serializer.data)


class ServiceViewSet(api_viewsets.GeotrekGeometricViewset):
    filter_backends = api_viewsets.GeotrekGeometricViewset.filter_backends + (api_filters.NearbyContentFilter, api_filters.UpdateOrCreateDateFilter, api_filters.GeotrekServiceFilter)
    serializer_class = api_serializers.ServiceSerializer
    queryset = trekking_models.Service.objects.all() \
        .select_related('topo_object', 'type', ) \
        .prefetch_related('topo_object__aggregations',
                          Prefetch('attachments',
                                   queryset=Attachment.objects.select_related('license', 'filetype', 'filetype__structure')),) \
        .annotate(geom3d_transformed=Transform(F('geom_3d'), settings.API_SRID)) \
        .order_by('pk')
