# -------------------------------------------------------------------------------
# mmc_reports.py
#
# Custom MMC reports.
# -------------------------------------------------------------------------------
from trytond.model import ModelView, ModelSingleton, ModelSQL, fields
from trytond.pyson import Eval, Not, Bool
from trytond.pool import Pool
from trytond.report import Report

import logging

class MmcPrenatalReportData(Report):
    'Data for the DOH Master Prenatal report'
    _description = __doc__

    def parse(self, report, objects, datas, localcontext):
        mmcLog = logging.getLogger('mmc')
        mmcLog.warning('Top of parse')
        patient = {'name': 'Ginny', 'lastname': 'Smith'}
        if localcontext is None:
            localcontext = {}
        localcontext['patient'] = patient
        return super(MmcPrenatalReportData, self).parse(report, objects, datas, localcontext)

MmcPrenatalReportData()

class MmcPrenatalReport(MmcPrenatalReportData):
    _name = 'mmc.reports'

MmcPrenatalReport()


