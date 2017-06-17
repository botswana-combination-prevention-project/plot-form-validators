from django import forms
from django.test import TestCase, tag

from edc_constants.constants import OTHER

from plot.constants import ACCESSIBLE, INACCESSIBLE

from ..plot_log_entry_form_validator import PlotLogEntryFormValidator
from .models import Plot, PlotLog


class TestAddPlotLogEntry(TestCase):

    def test_add_log_entry(self):
        plot = Plot.objects.create()
        plot_log = PlotLog.objects.create(plot=plot)
        cleaned_data = dict(plot_log=plot_log, log_status=ACCESSIBLE)
        form_validator = PlotLogEntryFormValidator(cleaned_data=cleaned_data)
        form_validator.validate()
        self.assertNotIn('log_status', form_validator._errors)

    def test_add_log_entry_inaccessible_requires_reason1(self):
        plot = Plot.objects.create()
        plot_log = PlotLog.objects.create(plot=plot)
        cleaned_data = dict(plot_log=plot_log, log_status=INACCESSIBLE)
        form_validator = PlotLogEntryFormValidator(cleaned_data=cleaned_data)
        self.assertRaises(
            forms.ValidationError, form_validator.validate)
        self.assertIn('reason', form_validator._errors)

    def test_add_log_entry_inaccessible_requires_reason2(self):
        plot = Plot.objects.create()
        plot_log = PlotLog.objects.create(plot=plot)
        cleaned_data = dict(
            plot_log=plot_log,
            log_status=INACCESSIBLE,
            reason='happiness')
        form_validator = PlotLogEntryFormValidator(cleaned_data=cleaned_data)
        form_validator.validate()
        self.assertNotIn('reason', form_validator._errors)

    def test_add_log_entry_inaccessible_requires_reason_other(self):
        plot = Plot.objects.create()
        plot_log = PlotLog.objects.create(plot=plot)
        cleaned_data = dict(
            plot_log=plot_log,
            log_status=INACCESSIBLE,
            reason=OTHER)
        form_validator = PlotLogEntryFormValidator(cleaned_data=cleaned_data)
        self.assertRaises(
            forms.ValidationError, form_validator.validate)
        self.assertIn('reason_other', form_validator._errors)

    def test_cannot_add_log_entry_as_inaccessible_for_confirmed_plot(self):
        plot = Plot.objects.create(confirmed=True)
        plot_log = PlotLog.objects.create(plot=plot)
        cleaned_data = dict(plot_log=plot_log, log_status=INACCESSIBLE)
        form_validator = PlotLogEntryFormValidator(cleaned_data=cleaned_data)
        self.assertRaises(
            forms.ValidationError,
            form_validator.validate)
        self.assertIn('log_status', form_validator._errors)

    def test_add_log_entry_plot_confirmed(self):
        plot = Plot.objects.create(confirmed=True)
        plot_log = PlotLog.objects.create(plot=plot)
        cleaned_data = dict(plot_log=plot_log)
        form_validator = PlotLogEntryFormValidator(cleaned_data=cleaned_data)
        self.assertRaises(
            forms.ValidationError,
            form_validator.validate)
        self.assertIn('log_status', form_validator._errors)
