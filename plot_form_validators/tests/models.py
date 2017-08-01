from django.db import models


class Plot(models.Model):

    plot_identifier = models.CharField(max_length=25, null=True)

    map_area = models.CharField(max_length=25, null=True)

    status = models.CharField(max_length=25, null=True)

    target_radius = models.IntegerField(null=True)

    eligible_members = models.IntegerField(null=True)

    location_name = models.CharField(max_length=25, null=True)

    confirmed = models.BooleanField(default=False)


class PlotLog(models.Model):

    plot = models.OneToOneField(Plot)


class PlotLogEntry(models.Model):

    plot_log = models.ForeignKey(PlotLog)

    log_status = models.CharField(max_length=25, null=True)
