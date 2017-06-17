# coding=utf-8

from django import forms
from django.core.exceptions import ObjectDoesNotExist

from edc_base.modelform_validators import FormValidator
from edc_constants.utils import get_display

from plot.choices import PLOT_STATUS
from plot.constants import ACCESSIBLE, RESIDENTIAL_HABITABLE


class PlotFormValidator(FormValidator):

    def __init__(self, add_plot_map_areas=None, special_locations=None,
                 supervisor_groups=None, current_user=None, cleaned_data=None, **kwargs):
        super().__init__(cleaned_data=cleaned_data, **kwargs)
        self.add_plot_map_areas = add_plot_map_areas or []
        self.current_user = current_user
        self.is_ess = cleaned_data.get('ess')
        self.map_area = cleaned_data.get('map_area')
        self.is_residential = True if cleaned_data.get(
            'status') == RESIDENTIAL_HABITABLE else False
        self.special_locations = special_locations or []
        self.supervisor_groups = supervisor_groups
        self.target_radius = cleaned_data.get('target_radius')
        self.eligible_members = cleaned_data.get('eligible_members')
        self.location_name = cleaned_data.get('location_name')
        self.household_count = cleaned_data.get('household_count')
        self.time_of_week = cleaned_data.get('time_of_week')
        self.time_of_day = cleaned_data.get('time_of_day')

    def clean(self):
        if not self.instance.id:
            self.allow_new_plot_or_raise()
        else:
            if self.location_name in self.special_locations:
                raise forms.ValidationError(
                    f'Plot may not be changed. Plot is listed as a special location. '
                    f'Got \'{self.location_name}\'.', code='special_location')
            self.validate_plot_log()

        self.required_if(
            RESIDENTIAL_HABITABLE,
            field='status',
            field_required='household_count')

        self.required_if(
            RESIDENTIAL_HABITABLE,
            field='status',
            field_required='eligible_members')

        self.required_if_true(self.eligible_members, 'time_of_week')
        self.required_if_true(self.eligible_members, 'time_of_day')

        self.validate_radius_increase()

    def validate_plot_log(self):
        try:
            if not self.instance.plotlog.plotlogentry_set.filter(
                    log_status=ACCESSIBLE).exists():
                raise forms.ValidationError(
                    'Complete the plot log "entry" before attempting '
                    'to modify this plot.', code='plot_log_entry')
        except ObjectDoesNotExist:
            raise forms.ValidationError(
                'Complete the plot log before attempting '
                'to modify this plot.', code='plot_log')

    def validate_radius_increase(self):
        if self.target_radius != self.instance.target_radius:
            if not self.current_user.groups.filter(
                    name__in=self.supervisor_groups).exists():
                raise forms.ValidationError(
                    {'target_radius': 'Insufficient permissions to change.'})

    def allow_new_plot_or_raise(self):
        """Raise if new plots not in allowed map_area and not ess
        and not residential.
        """
        if self.map_area not in self.add_plot_map_areas:
            raise forms.ValidationError(
                f'Plots may not be added in this map area. '
                f'Got map area=\'{self.map_area}\'.', code='invalid_new_plot')
        elif not self.is_ess:
            raise forms.ValidationError(
                'Only ESS plots may be added. See Categories.', code='invalid_new_plot')
        elif not self.is_residential:
            raise forms.ValidationError(
                f'Only \'{get_display(PLOT_STATUS, RESIDENTIAL_HABITABLE)}\' plots may be added.',
                code='invalid_new_plot')
