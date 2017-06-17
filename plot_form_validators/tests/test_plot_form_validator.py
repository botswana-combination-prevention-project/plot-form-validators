from django import forms
from django.contrib.auth.models import User, Group
from django.test import TestCase, tag

from plot.constants import ACCESSIBLE, RESIDENTIAL_HABITABLE, RESIDENTIAL_NOT_HABITABLE, INACCESSIBLE

from ..plot_form_validator import PlotFormValidator
from .models import Plot, PlotLog, PlotLogEntry


class TestAddPlot(TestCase):

    def test_cannot_add_plot_map_area_none(self):
        cleaned_data = dict(
            map_area=None, ess=False, status=RESIDENTIAL_HABITABLE)
        form_validator = PlotFormValidator(
            allow_add_plot_map_areas=[],
            instance=Plot(),
            cleaned_data=cleaned_data)
        self.assertRaises(forms.ValidationError, form_validator.validate)
        self.assertIn('invalid_new_plot', form_validator._error_codes)

    def test_cannot_add_plot_map_area_if_not_ess(self):
        cleaned_data = dict(
            map_area='leiden', ess=False, status=RESIDENTIAL_HABITABLE)
        form_validator = PlotFormValidator(
            allow_add_plot_map_areas=['leiden'],
            instance=Plot(),
            cleaned_data=cleaned_data)
        self.assertRaises(forms.ValidationError, form_validator.validate)
        self.assertIn('invalid_new_plot', form_validator._error_codes)

    def test_may_add_plot_map_area_and_is_ess(self):
        cleaned_data = dict(
            map_area='leiden', ess=True, status=RESIDENTIAL_HABITABLE,
            household_count=3, eligible_members=3)
        form_validator = PlotFormValidator(
            allow_add_plot_map_areas=['leiden'],
            instance=Plot(),
            cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f'ValidationError unexpectedly raised. Got {e}')

    def test_cannot_add_plot_not_residential(self):
        cleaned_data = dict(
            map_area='leiden', ess=True, status=RESIDENTIAL_NOT_HABITABLE)
        form_validator = PlotFormValidator(
            allow_add_plot_map_areas=['leiden'],
            instance=Plot(),
            cleaned_data=cleaned_data)
        self.assertRaises(forms.ValidationError, form_validator.validate)
        self.assertIn('invalid_new_plot', form_validator._error_codes)

    def test_may_add_plot_residential(self):
        cleaned_data = dict(
            map_area='leiden', ess=True, status=RESIDENTIAL_HABITABLE,
            household_count=3, eligible_members=3)
        form_validator = PlotFormValidator(
            allow_add_plot_map_areas=['leiden'],
            instance=Plot(),
            cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f'ValidationError unexpectedly raised. Got {e}')


class TestRequiresPlotLogEntry(TestCase):
    def setUp(self):
        self.cleaned_data = dict(
            map_area='leiden', ess=True)
        self.allow_add_plot_map_areas = ['leiden']
        self.plot = Plot.objects.create()

    def test_plot_log_required(self):
        form_validator = PlotFormValidator(
            instance=self.plot,
            cleaned_data=self.cleaned_data)
        self.assertRaises(
            forms.ValidationError,
            form_validator.validate)
        self.assertIn('plot_log', form_validator._error_codes)

    def test_plot_log_entry_required(self):
        PlotLog.objects.create(plot=self.plot)
        form_validator = PlotFormValidator(
            instance=self.plot,
            cleaned_data=self.cleaned_data)
        self.assertRaises(
            forms.ValidationError,
            form_validator.validate)
        self.assertIn('plot_log_entry', form_validator._error_codes)

    def test_ignores_plot_log_entry_inaccessible(self):
        plot_log = PlotLog.objects.create(plot=self.plot)
        PlotLogEntry.objects.create(plot_log=plot_log, log_status=INACCESSIBLE)
        form_validator = PlotFormValidator(
            instance=self.plot,
            cleaned_data=self.cleaned_data)
        self.assertRaises(
            forms.ValidationError,
            form_validator.validate)
        self.assertIn('plot_log_entry', form_validator._error_codes)

    def test_plot_log_entry_ok(self):
        plot_log = PlotLog.objects.create(plot=self.plot)
        PlotLogEntry.objects.create(plot_log=plot_log, log_status=ACCESSIBLE)
        form_validator = PlotFormValidator(
            instance=self.plot,
            cleaned_data=self.cleaned_data)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f'ValidationError unexpectedly raised. Got {e}')


class TestRadius(TestCase):

    def setUp(self):
        self.cleaned_data = dict(
            map_area='leiden', ess=True, status=RESIDENTIAL_HABITABLE,
            household_count=3, eligible_members=3)
        self.allow_add_plot_map_areas = ['leiden']
        self.current_user = User.objects.create(username='erik')
        self.group = Group.objects.create(name='supervisor')
        # statisfy plot log validation
        self.plot = Plot.objects.create(id=1)
        plot_log = PlotLog.objects.create(plot=self.plot)
        PlotLogEntry.objects.create(plot_log=plot_log, log_status=ACCESSIBLE)

    def test_cannot_change_radius_not_supervisor(self):
        self.cleaned_data.update(target_radius=5)
        form_validator = PlotFormValidator(
            allow_add_plot_map_areas=self.allow_add_plot_map_areas,
            instance=self.plot,
            supervisor_groups=[],
            current_user=self.current_user,
            cleaned_data=self.cleaned_data)
        self.assertRaises(
            forms.ValidationError,
            form_validator.validate)
        self.assertIn('target_radius', form_validator._errors)

    def test_may_change_radius_if_supervisor(self):
        self.cleaned_data.update(target_radius=5)
        self.current_user.groups.add(self.group)
        form_validator = PlotFormValidator(
            allow_add_plot_map_areas=self.allow_add_plot_map_areas,
            instance=self.plot,
            supervisor_groups=['supervisor'],
            current_user=self.current_user,
            cleaned_data=self.cleaned_data)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f'ValidationError unexpectedly raised. Got {e}')


class TestEligibleMembers(TestCase):

    def setUp(self):
        self.cleaned_data = dict(map_area='leiden', ess=True)
        # statisfy plot log validation
        self.plot = Plot.objects.create(id=1)
        plot_log = PlotLog.objects.create(plot=self.plot)
        PlotLogEntry.objects.create(plot_log=plot_log, log_status=ACCESSIBLE)

    def test_eligible_members_required_if_residential1(self):
        self.cleaned_data.update(
            eligible_members=0, status=RESIDENTIAL_HABITABLE,
            household_count=1)
        form_validator = PlotFormValidator(
            instance=self.plot,
            cleaned_data=self.cleaned_data)
        self.assertRaises(
            forms.ValidationError,
            form_validator.validate)
        self.assertIn('eligible_members', form_validator._errors)

    def test_eligible_members_required_if_residential2(self):
        self.cleaned_data.update(
            eligible_members=1, status=RESIDENTIAL_HABITABLE,
            household_count=0)  # use household_count to raise
        form_validator = PlotFormValidator(
            instance=self.plot,
            cleaned_data=self.cleaned_data)
        self.assertRaises(
            forms.ValidationError,
            form_validator.validate)
        self.assertNotIn('eligible_members', form_validator._errors)

    def test_eligible_members_not_required_if_not_residential(self):
        self.cleaned_data.update(
            eligible_members=0, status=RESIDENTIAL_NOT_HABITABLE,
            household_count=1)  # use household_count to raise
        form_validator = PlotFormValidator(
            instance=self.plot,
            cleaned_data=self.cleaned_data)
        self.assertRaises(
            forms.ValidationError,
            form_validator.validate)
        self.assertNotIn('eligible_members', form_validator._errors)


class TestSpecialLocations(TestCase):

    def setUp(self):
        self.cleaned_data = dict(map_area='leiden', ess=True)
        plot = Plot.objects.create()
        plot_log = PlotLog.objects.create(plot=plot)
        PlotLogEntry.objects.create(plot_log=plot_log, log_status=ACCESSIBLE)
        self.plot = Plot.objects.create(location_name='clinic')
        plot_log = PlotLog.objects.create(plot=self.plot)
        PlotLogEntry.objects.create(plot_log=plot_log, log_status=ACCESSIBLE)
        self.current_user = User.objects.create(username='erik')
        self.group = Group.objects.create(name='supervisor')

    def test_location(self):
        self.cleaned_data.update(target_radius=5, location_name='clinic')
        form_validator = PlotFormValidator(
            instance=self.plot,
            supervisor_groups=['supervisor'],
            current_user=self.current_user,
            special_locations=['clinic'],
            cleaned_data=self.cleaned_data)
        self.assertRaises(
            forms.ValidationError,
            form_validator.validate)
        self.assertIn('special_location', form_validator._error_codes)

# class TestForms(PlotTestMixin, TestCase):
#
#     def test_add_ess_plot_form(self):
#         plot = mommy.prepare_recipe(
#             'plot.plot',
#             ess=True,
#             status=RESIDENTIAL_HABITABLE,
#             time_of_week='weekdays',
#             time_of_day='morning',
#             household_count=1,
#             eligible_members=1,
#             gps_confirmed_latitude=fake.confirmed_latitude,
#             gps_confirmed_longitude=fake.confirmed_longitude,
#         )
#         form = PlotForm(data=plot.__dict__)
#         self.assertTrue(form.is_valid())
#
#     def test_cannot_add_non_ess_plot_form(self):
#         plot = mommy.prepare_recipe(
#             'plot.plot',
#             ess=False,
#             status=RESIDENTIAL_HABITABLE,
#             time_of_week='weekdays',
#             time_of_day='morning',
#             household_count=1,
#             eligible_members=1,
#             gps_confirmed_latitude=fake.confirmed_latitude,
#             gps_confirmed_longitude=fake.confirmed_longitude,
#         )
#         form = PlotForm(data=plot.__dict__)
#         self.assertFalse(form.is_valid())
#
#     def test_cannot_add_non_ess_non_residential_plot_form(self):
#         plot = mommy.prepare_recipe(
#             'plot.plot',
#             ess=True,
#             status=RESIDENTIAL_NOT_HABITABLE,
#             gps_confirmed_latitude=fake.confirmed_latitude,
#             gps_confirmed_longitude=fake.confirmed_longitude,
#         )
#         form = PlotForm(data=plot.__dict__)
#         self.assertFalse(form.is_valid())
#
#     def test_plot_log_entry_form(self):
#         """Add a plot log entry.
#         """
#         plot = self.make_confirmed_plot(household_count=1)
#         plot_log = PlotLog.objects.get(plot=plot)
#         form = PlotLogEntryForm(
#             data=dict(
#                 plot_log=plot_log.id,
#                 report_datetime=self.get_utcnow(),
#                 log_status=ACCESSIBLE))
#         self.assertTrue(form.is_valid())
#
#     def test_attempt_to_add_many_plot_log_entry_per_day(self):
#         """Attempt to add more than one plot log entry in a day.
#         """
#         plot = self.make_confirmed_plot(household_count=1)
#         plot_log = PlotLog.objects.get(plot=plot)
#         plot_log_entry = PlotLogEntry.objects.get(plot_log=plot_log)
#         # edit existing
#         form = PlotLogEntryForm(
#             data=dict(
#                 plot_log=plot_log.id,
#                 report_datetime=plot_log_entry.report_datetime,
#                 log_status=plot_log_entry.log_status),
#             instance=plot_log_entry)
#         self.assertTrue(form.is_valid())
#         form.save()
#         # try to add duplicate
#         form = PlotLogEntryForm(
#             data=dict(
#                 plot_log=plot_log.id,
#                 report_datetime=plot_log_entry.report_datetime,
#                 log_status=plot_log_entry.log_status))
#         self.assertFalse(form.is_valid())
