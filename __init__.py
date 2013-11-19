from trytond.pool import Pool

from .mmc import *
from .mmc_reports import *

def register():
    Pool.register(
        MmcReports,
        MmcSequences,
        MmcPatientData,
        MmcPatientDiseaseInfo,
        MmcVaccination,
        MmcPatientMedication,
        MmcMedicationTemplate,
        MmcPatientPregnancy,
        MmcPrenatalEvaluation,
        MmcPerinatal,
        MmcPerinatalMonitor,
        MmcPuerperiumMonitor,
        Address,
        MmcPostpartumContinuedMonitor,
        MmcPostpartumOngoingMonitor,
        module='mmc', type_='model')
    Pool.register(
        MmcPrenatalReport,
        module='mmc', type_='report')
