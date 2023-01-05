from django import forms
from django.db.models import Q
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _
from django.db.models.fields.related import ForeignKey, ManyToManyField
from django.core.exceptions import FieldDoesNotExist, ValidationError

from geotrek.authent.models import StructureRelated, StructureOrNoneRelated
from geotrek.common.mixins.models import NoDeleteMixin


class WithStructureFormMixin:
    """Form mixin used for objects structure related"""

    def check_structure(self, obj, structure, name):
        """Check structure"""
        if hasattr(obj, 'structure'):
            if obj.structure and structure != obj.structure:
                self.add_error(name, format_lazy(_("Please select a choice related to all structures (without brackets) "
                                                   "or related to the structure {struc} (in brackets)"), struc=structure))

    def deep_remove(self, fieldslayout, name):
        """Remove deeply fieldslayout"""
        if isinstance(fieldslayout, list):
            for field in fieldslayout:
                self.deep_remove(field, name)
        elif hasattr(fieldslayout, 'fields'):
            if name in fieldslayout.fields:
                fieldslayout.fields.remove(name)
                self.fields.pop(name)
            for field in fieldslayout.fields:
                self.deep_remove(field, name)

    def filter_related_field(self, name, field):
        """Query in related fields according to user structure"""
        if not isinstance(field, forms.models.ModelChoiceField):
            return
        try:
            modelfield = self.instance._meta.get_field(name)
        except FieldDoesNotExist:
            # be careful but custom form fields, not in model
            modelfield = None
        if not isinstance(modelfield, (ForeignKey, ManyToManyField)):
            return
        model = modelfield.remote_field.model
        # Filter structured choice fields according to user's structure
        if issubclass(model, StructureRelated) and model.check_structure_in_forms:
            field.queryset = field.queryset.filter(structure=self.user.profile.structure)
        if issubclass(model, StructureOrNoneRelated) and model.check_structure_in_forms:
            field.queryset = field.queryset.filter(Q(structure=self.user.profile.structure) | Q(structure=None))
        if issubclass(model, NoDeleteMixin):
            field.queryset = field.queryset.filter(deleted=False)

    def initialize_fields_with_structure(self):
        """Set initial values according to structure"""
        if self.user.has_perm('authent.can_bypass_structure'):
            if not self.instance.pk:
                self.fields['structure'].initial = self.user.profile.structure
        else:
            for name, field in self.fields.items():
                self.filter_related_field(name, field)
            del self.fields['structure']


class FormsetMixin:
    context_name = None
    formset_class = None

    def form_valid(self, form):
        context = self.get_context_data()
        formset_form = context[self.context_name]

        if formset_form.is_valid():
            response = super().form_valid(form)
            formset_form.instance = self.object
            formset_form.save()
        else:
            response = self.form_invalid(form)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            try:
                context[self.context_name] = self.formset_class(
                    self.request.POST, instance=self.object)
            except ValidationError:
                pass
        else:
            context[self.context_name] = self.formset_class(
                instance=self.object)
        return context
