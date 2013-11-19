# -------------------------------------------------------------------------------
# mmc_reports.py
#
# Custom MMC reports.
# -------------------------------------------------------------------------------
from trytond.model import ModelView, ModelSingleton, ModelSQL, fields
from trytond.pyson import Eval, Not, Bool
from trytond.pool import Pool
from trytond.report import Report
from trytond.transaction import Transaction

import datetime

import logging

mmcLog = logging.getLogger('mmcReports')

__all__ = [
    'MmcPrenatalReport'
    ]


class MmcPrenatalReport(Report):
    '''
    Generates MMC report to fulfill Philippines Department of Health
    requirements for a master prenatal report. This is a two page
    report that is printed in landscape mode on long bond paper.
    '''
    __name__ = 'gnuhealth.patient.doh.prenatal'

    @classmethod
    def parse(cls, report, records, data, localcontext):

        # --------------------------------------------------------
        # TODO: set the date range.
        # --------------------------------------------------------
        evals = Pool().get('gnuhealth.patient.prenatal.evaluation').search([])
        pregnancies = list(set([e.name for e in evals]))

        recs = []
        for preg in pregnancies:
            rec = {}
            # --------------------------------------------------------
            # Page 1
            # --------------------------------------------------------

            # --------------------------------------------------------
            # General information.
            # --------------------------------------------------------
            rec['lastname'] = preg.name.lastname
            rec['firstname'] = preg.name.name.name
            rec['dob'] = preg.name.dob.strftime("%m/%d/%Y")
            rec['age'] = preg.name.age.split(" ")[0].rstrip('y')
            rec['lmp'] = preg.lmp.strftime("%m/%d/%Y")
            rec['edd'] = preg.pdd.strftime("%m/%d/%Y")

            # --------------------------------------------------------
            # TODO: check if this logic is right to get the address.
            # Assumes first address is of the patient.
            # --------------------------------------------------------
            rec['address'] = preg.name.name.addresses[0].street

            # --------------------------------------------------------
            # Date of registration.
            # Find the earliest prenatal evaluation for this pregnancy and use that
            # as the registration date.
            # --------------------------------------------------------
            rec['dateReg'] = min([e.eval_date_only for e in \
                preg.prenatal_evaluations]).strftime("%m/%d/%Y")

            # --------------------------------------------------------
            # GPAS.
            # --------------------------------------------------------
            g,p,a,s = [((x and x) or 0) for x in [preg.name.gravida, \
                preg.name.para, preg.name.abortions, preg.name.stillbirths]]
            rec['gpas'] = "%d , %d , %d , %d" % (g,p,a,s)

            # --------------------------------------------------------
            # Prenatal visits.
            # --------------------------------------------------------
            weeks12Cut = preg.pdd - datetime.timedelta(weeks=28)
            weeks27Cut = preg.pdd - datetime.timedelta(weeks=13)
            rec['weeksTo12'] = " ".join([e.eval_date_only.strftime("%m/%d/%Y") \
                    for e in preg.prenatal_evaluations \
                    if e.eval_date_only < weeks12Cut])
            rec['weeksTo27'] = " ".join([e.eval_date_only.strftime("%m/%d/%Y") \
                    for e in preg.prenatal_evaluations \
                    if e.eval_date_only > weeks12Cut and e.eval_date_only < weeks27Cut])
            rec['weeksTo40'] = " ".join([e.eval_date_only.strftime("%m/%d/%Y") \
                    for e in preg.prenatal_evaluations \
                    if e.eval_date_only > weeks27Cut])

            # --------------------------------------------------------
            # Page 2 of the report.
            # --------------------------------------------------------

            # --------------------------------------------------------
            # Risk code.
            # --------------------------------------------------------
            rec['riskcode'] = 'TBD'

            # --------------------------------------------------------
            # Tetanus.
            # --------------------------------------------------------
            vacs = preg.name.vaccinations
            ttprev = []
            ttcurr = []
            for v in vacs:
                vdate = v.cdate
                if vdate < preg.lmp:
                    ttprev.append(vdate)
                else:
                    ttcurr.append(vdate)
            rec['ttprev'] = " ".join(d.strftime("%m/%d/%Y") for d in ttprev)
            rec['ttcurr'] = " ".join(d.strftime("%m/%d/%Y") for d in ttcurr)

            # --------------------------------------------------------
            # Doctor/Dentist consultations.
            # --------------------------------------------------------
            rec['doctor_consult'] = preg.doctor_consult_date
            rec['dentist_consult'] = preg.dentist_consult_date

            rec['phil_health'] = (preg.name.phil_health and 'Y') or 'N'

            # --------------------------------------------------------
            # Per Krys, this is hard-coded.
            # --------------------------------------------------------
            rec['partner'] = 'Midwife'

            rec['mb_book'] = (preg.mb_book and 'Y') or 'N'
            rec['iodized_salt'] = (preg.iodized_salt and 'Y') or 'N'

            # --------------------------------------------------------
            # 'Quality' prenatal care depends upon:
            #   - A doctor and dentist consultation.
            #   - A prenatal visit in each of the first 2 trimesters.
            #   - 2 prenatal visits in the 3rd trimester.
            # --------------------------------------------------------
            rec['quality'] = ((rec['doctor_consult'] and
                            rec['dentist_consult'] and
                            rec['weeksTo12'] and
                            rec['weeksTo27'] and
                            len(rec['weeksTo40'].split()) >= 2) and 'Y') or 'N'

            rec['where_deliver'] = preg.where_deliver

            recs.append(rec)

        records = recs
        return super(MmcPrenatalReport, cls).parse(report, records, data, localcontext)

