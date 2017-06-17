from django import forms

from edc_base.modelform_validators import FormValidator

from plot.constants import INACCESSIBLE, ACCESSIBLE


class PlotLogEntryFormValidator(FormValidator):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        plot_log = self.cleaned_data.get('plot_log')
        self.is_confirmed = plot_log.plot.confirmed
        self.accessible = True if self.cleaned_data.get(
            'log_status') == ACCESSIBLE else False

    def clean(self):
        if not self.accessible and self.is_confirmed:
            raise forms.ValidationError(
                {'log_status':
                 'This plot has been \'confirmed\'. Must be accessible.'})
        self.required_if(INACCESSIBLE, field='log_status',
                         field_required='reason')
        self.validate_other_specify(field='reason')
