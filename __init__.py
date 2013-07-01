from trytond.pool import Pool
from mmc import *

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
