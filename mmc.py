# -------------------------------------------------------------------------------
# mmc.py
#
# Customization of GnuHealth for the needs of Mercy Maternity Clinic, Inc.
# -------------------------------------------------------------------------------
from trytond.model import ModelView, ModelSingleton, ModelSQL, fields
from trytond.pyson import Eval, Not, Bool, Or, And
from trytond.pool import Pool

import datetime
import logging

__all__ = [
    'MmcReports',
    'MmcSequences',
    'MmcPatientData',
    'MmcPatientDiseaseInfo',
    'MmcVaccination',
    'MmcPatientMedication',
    'MmcMedicationTemplate',
    'MmcPatientPregnancy',
    'MmcPrenatalEvaluation',
    'MmcPerinatal',
    'MmcPerinatalMonitor',
    'MmcPuerperiumMonitor',
    'Address',
    'MmcPostpartumContinuedMonitor',
    'MmcPostpartumOngoingMonitor',
    ]

mmcLog = logging.getLogger('mmc')

def month_num_to_abbrev(num):
    mon = {}
    mon['01'] = 'Jan'
    mon['02'] = 'Feb'
    mon['03'] = 'Mar'
    mon['04'] = 'Apr'
    mon['05'] = 'May'
    mon['06'] = 'Jun'
    mon['07'] = 'Jul'
    mon['08'] = 'Aug'
    mon['09'] = 'Sep'
    mon['10'] = 'Oct'
    mon['11'] = 'Nov'
    mon['12'] = 'Dec'
    return mon[num]

class MmcReports(ModelSingleton, ModelSQL, ModelView):
    'Class for custom reports'
    __name__ = 'mmc.reports'


class MmcSequences(ModelSingleton, ModelSQL, ModelView):
    "Sequences for MMC"

    __name__ = "mmc.sequences"

    doh_sequence = fields.Property(fields.Many2One('ir.sequence',
        'DOH Sequence', domain=[('code', '=', 'mmc.doh')],
        required=True))



class MmcPatientData(ModelSQL, ModelView):
    'Patient related information'
    __name__ = 'gnuhealth.patient'

    # --------------------------------------------------------
    # Hide these fields
    # --------------------------------------------------------
    family = fields.Many2One('gnuhealth.family', 'x',
            states={'invisible': True})

    primary_care_doctor = fields.Many2One('gnuhealth.physician', 'x',
            states={'invisible': True})

    current_insurance = fields.Many2One('gnuhealth.insurance', 'x',
            states={'invisible': True})


    # --------------------------------------------------------
    # Expand the selection list of these fields.
    # --------------------------------------------------------
    marital_status = fields.Function(
        fields.Selection([
            (None, ''),
            ('l', 'Live-in'),
            ('s', 'Single'),
            ('m', 'Married'),
            ('c', 'Concubinage'),
            ('w', 'Widowed'),
            ('d', 'Divorced'),
            ('x', 'Separated'),
            ], 'Marital Status', sort=False), 'get_patient_marital_status')

    rh = fields.Selection([
        ('u', 'Unknown'),
        ('+', '+'),
        ('-', '-'),
        ], 'Rh')

    # --------------------------------------------------------
    # Change the label on these fields.
    # --------------------------------------------------------
    diseases = fields.One2Many('gnuhealth.patient.disease', 'name', 'Condition')
    gravida = fields.Integer ('G', required=True)
    abortions = fields.Integer('A')
    stillbirths = fields.Integer('S')

    # --------------------------------------------------------
    # Add Pregnancy fields.
    # --------------------------------------------------------
    living = fields.Integer('L')        # number of live births
    para = fields.Integer('P')          # number of times given birth
    term = fields.Integer('Term')       # number of pregnancies to full term
    preterm = fields.Integer('Preterm') # number of pregnancies not to full term

    # --------------------------------------------------------
    # Add Phil Health related fields.
    # --------------------------------------------------------
    phil_health = fields.Boolean('Phil Health',
        help='Mark if the patient has Phil Health')

    phil_health_mcp = fields.Boolean('MCP',
        help="If MCP applies",
        states={'invisible': Not(Bool(Eval('phil_health')))},
        depends=['phil_health'])

    phil_health_ncp = fields.Boolean('NCP',
        help="If NCP applies",
        states={'invisible': Not(Bool(Eval('phil_health')))},
        depends=['phil_health'])

    phil_health_id = fields.Char('PHIC#',
        size=14,
        help="The patients Phil Health ID number",
        states={
            'invisible': Not(Bool(Eval('phil_health'))),
            'required': Bool(Eval('phil_health'))
        },
        on_change=['phil_health_id'],
        depends=['phil_health'])


    # --------------------------------------------------------
    # Add new screening related fields.
    # --------------------------------------------------------
    gram_stain = fields.Boolean('Gram Stain',
        help="Check if gram stain was done")

    breast_self_exam_taught = fields.Boolean('Taught breast self exam',
        help="Check if patient has been taught how to do breast self exams")


    # --------------------------------------------------------
    # Department of Health required id (aka MMC ID#).
    # --------------------------------------------------------
    doh_id = fields.Char('MMC ID',
        size=8,
        help="Dept of Health id", required=False,
        select=True, on_change=['doh_id'])

    # --------------------------------------------------------
    # Format DOH ID # in the customary fashion after the user
    # types it in. User can type with hyphens or not. But don't
    # change anything unless the field seems correct.
    # --------------------------------------------------------
    def on_change_doh_id(self):
        origFld = self.doh_id
        doh = origFld.replace('-', '')
        val = origFld
        if ((len(doh) == 6) and (doh.isdigit())):
            val = "{0}-{1}-{2}".format(doh[:2], doh[2:4], doh[4:6])
        return {'doh_id': val}


    # --------------------------------------------------------
    # Format PHIC# in the customary fashion after the user
    # types it in. User can type with hyphens or not. But don't
    # change anything unless the field seems correct.
    # --------------------------------------------------------
    def on_change_phil_health_id(self):
        origFld = self.phil_health_id
        phic = origFld.replace('-', '')
        val = origFld
        if ((len(phic) == 12) and (phic.isdigit())):
            val = "{0}-{1}-{2}".format(phic[:2], phic[2:11], phic[-1])
        return {'phil_health_id': val}

    # --------------------------------------------------------
    # Validate the DOH ID.
    # --------------------------------------------------------
    @staticmethod
    def validate_doh_id(ids):
        for patientData in ids:
            if (patientData.doh_id == None or len(patientData.doh_id) == 0):
                return True
            doh = patientData.doh_id.replace('-', '')
            if (len(doh) != 6):
                return False
            if (not doh.isdigit()):
                return False
            return True

    # --------------------------------------------------------
    # Validate the PHIC #.
    # --------------------------------------------------------
    @staticmethod
    def validate_phil_health_id(ids):
        for patientData in ids:
            if not patientData.phil_health:
                # if Phil Health does not apply, then we are fine.
                return True
            phic = patientData.phil_health_id.replace('-', '')
            if (len(phic) != 12):
                mmcLog.info('Phil Health id is not the correct length')
                return False
            if (not phic.isdigit()):
                mmcLog.info('Phil Health id is not a number')
                return False
            return True

    # --------------------------------------------------------
    # Set a reasonable default sex for a maternity clinic.
    # --------------------------------------------------------
    @staticmethod
    def default_sex():
        return 'f'


    # --------------------------------------------------------
    # 99.4% of all people in the Philippines are RH positive.
    # Oftentimes blood tests do not even test for this. But
    # because it is not tested for sometimes, it should be
    # set to unknown unless explicitly set.
    # --------------------------------------------------------
    @staticmethod
    def default_rh():
        return 'u'


    # --------------------------------------------------------
    # Add our validations to the class.
    # --------------------------------------------------------
    @classmethod
    def __setup__(cls):
        super(MmcPatientData, cls).__setup__()
        cls._sql_constraints = [
            ('name_uniq', 'UNIQUE(name)', 'The Patient already exists !'),
            ('doh_uniq', 'UNIQUE(doh_id)', 'The MMC ID already exists !'),
        ]
        cls._constraints += [
            ('validate_phil_health_id', 'phil_health_id_format'),
            ('validate_doh_id', 'validate_doh_id_format'),
        ]
        cls._error_messages.update({
            'phil_health_id_format': 'PHIC# must be 12 numbers',
            'validate_doh_id_format': 'Department of Health ID must be 6 numbers'
        })

    # --------------------------------------------------------
    # Create a Department of Health id automatically, but it
    # can be overridden by the user, if desired, to another
    # number or a blank value.
    # --------------------------------------------------------
    @classmethod
    def create(cls, values):
        if not values.get('doh_id'):
            values = values.copy()
            sequence_obj = Pool().get('ir.sequence')
            config_obj = Pool().get('mmc.sequences')
            config = config_obj(1)
            # --------------------------------------------------------
            # The sequence is prefixed with the current 4 digit year
            # but we need only a two digit year and we like it formatted
            # a certain way.
            # --------------------------------------------------------
            seq = sequence_obj.get_id(config.doh_sequence.id)[2:]
            values['doh_id'] = "{0}-{1}-{2}".format(seq[:2], seq[2:4], seq[4:6])

        return super(MmcPatientData, cls).create(values)




class MmcPatientDiseaseInfo(ModelSQL, ModelView):
    'Patient Disease History'
    __name__ = 'gnuhealth.patient.disease'

    # --------------------------------------------------------
    # Change the label of these fields.
    # --------------------------------------------------------
    pathology = fields.Many2One('gnuhealth.pathology', 'Condition',
        required=True, help='Disease')

    status = fields.Selection([
        ('a', 'acute'),
        ('c', 'chronic'),
        ('u', 'unchanged'),
        ('h', 'healed'),
        ('i', 'improving'),
        ('w', 'worsening'),
        ], 'Status of the condition', select=True, sort=False)

    is_infectious = fields.Boolean('Infectious Condition',
        help='Check if the patient has an infectious / transmissible condition')

    is_active = fields.Boolean('Active condition')




class MmcVaccination(ModelSQL, ModelView):
    'Patient Vaccination information'
    __name__ = 'gnuhealth.vaccination'

    # --------------------------------------------------------
    # Was the vaccine administered by MMC?
    # --------------------------------------------------------
    vaccine_by_mmc = fields.Boolean('Administered by MMC',
        help="Check if this vaccine was administered by Mercy Maternity Clinic")


    # --------------------------------------------------------
    # Hide these unnecessary fields.
    # --------------------------------------------------------
    vaccine_expiration_date = fields.Date('x', states={'invisible': True})
    vaccine_lot = fields.Char('x', states={'invisible': True})
    institution = fields.Many2One('party.party', 'x', states={'invisible': True})
    date = fields.DateTime('Date', states={'invisible': True})
    next_dose_date = fields.DateTime('Next Dose', states={'invisible': True})

    # --------------------------------------------------------
    # Allow approximate dates for recording of historical
    # vaccinations per patient testimony.
    # --------------------------------------------------------
    cdate_month = fields.Selection([
        ('', ''),
        ('01', 'Jan'),
        ('02', 'Feb'),
        ('03', 'Mar'),
        ('04', 'Apr'),
        ('05', 'May'),
        ('06', 'Jun'),
        ('07', 'Jul'),
        ('08', 'Aug'),
        ('09', 'Sep'),
        ('10', 'Oct'),
        ('11', 'Nov'),
        ('12', 'Dec'),
        ], 'Approximate Month', help="Approximate month of the vaccination",
        sort=False)
    cdate_year = fields.Integer('Approximate Year (YYYY)',
        help="Year of the vaccination")

    # --------------------------------------------------------
    # But also allow an exact date if known or vaccination is
    # being administered.
    # --------------------------------------------------------
    cdate = fields.Date('Date',
        states={
            'invisible': Or(Bool(Eval('cdate_year')), And(Bool(Eval('cdate_month')),
                Bool(Eval('cdate_year'))))
        })
    next_dose = fields.Date('Next Dose')

    # --------------------------------------------------------
    # Display date for tree view that shows appropriate date
    # no matter if cdate or cdate_year or cdate_month and 
    # cdate_year chosen.
    # --------------------------------------------------------
    display_date = fields.Function(fields.Char('Date'), 'get_display_date')

    # --------------------------------------------------------
    # Choose either cdate or the cdate_month and/or cdate_year
    # fields to create an appropriate display.
    # --------------------------------------------------------
    @staticmethod
    def get_display_date(ids, name):
        result = {}
        for vacc in ids:
            if name == 'display_date':
                if vacc.cdate_year is not None and (vacc.cdate_month is None or
                        len(vacc.cdate_month) == 0):
                    result[vacc.id] = "{0}".format(vacc.cdate_year)
                elif vacc.cdate_year != None and vacc.cdate_month != None and vacc.cdate_month != '':
                    result[vacc.id] = "{0} {1}".format(month_num_to_abbrev(vacc.cdate_month), vacc.cdate_year)
                else:
                    result[vacc.id] = "{0}".format(vacc.cdate)

        return result

    # --------------------------------------------------------
    # Revise validation to not require the next_dose_date field.
    # --------------------------------------------------------
    @staticmethod
    def validate_next_dose_date (ids):
        for vaccine_data in ids:
            if vaccine_data.next_dose_date is None:
                return True
            if (vaccine_data.next_dose_date < vaccine_data.date):
                return False
            else:
                return True

    @staticmethod
    def default_cdate():
        return datetime.datetime.now()

    @staticmethod
    def default_cdate_month():
        return ''

    @staticmethod
    def default_cdate_year():
        return None



class MmcPatientMedication(ModelSQL, ModelView):
    'Patient Medication'
    __name__ = 'gnuhealth.patient.medication'

    # --------------------------------------------------------
    # Change the field label.
    # --------------------------------------------------------
    doctor = fields.Many2One('gnuhealth.physician', 'Name',
        help='Name of person who prescribed the medicament')



class MmcMedicationTemplate(ModelSQL, ModelView):
    'Template for medication'
    __name__ = 'gnuhealth.medication.template'

    # --------------------------------------------------------
    # Change the field label.
    # --------------------------------------------------------
    medicament = fields.Many2One('gnuhealth.medicament', 'Name of Med',
        required=True, help='Prescribed Medicine')



class MmcPatientPregnancy(ModelSQL, ModelView):
    'Patient Pregnancy'
    __name__ = 'gnuhealth.patient.pregnancy'

    # --------------------------------------------------------
    # Change the field labels.
    # --------------------------------------------------------
    pdd = fields.Function (fields.Date('Due Date'), 'get_pregnancy_data')
    perinatal = fields.One2Many('gnuhealth.perinatal', 'name', 'Labor')
    puerperium_monitor = fields.One2Many('gnuhealth.puerperium.monitor',
        'name', 'Postpartum')
    pregnancy_end_date = fields.DateTime ('Date/time of birth',
        states={
            'invisible': Bool(Eval('current_pregnancy')),
            'required': Not(Bool(Eval('current_pregnancy'))),
            })

    # --------------------------------------------------------
    # Add an alternative due date field.
    # --------------------------------------------------------
    apdd = fields.Date('Alt Due Date',
        help="Enter the alternative pregnancy due date if there is one")

    # --------------------------------------------------------
    # Add partner information for this pregnancy.
    # --------------------------------------------------------
    partner_first_name = fields.Char('Partner first name',
        help="The partner or husband's first name")
    partner_last_name = fields.Char('Partner last name',
        help="The partner or husband's last name")
    partner_age = fields.Integer('Partner age',
        help="The age in years of the partner")
    partner_employment = fields.Char('Partner work',
        help="The work of the partner")
    partner_education = fields.Char('Partner education',
        help="The amount of education that the partner has completed")
    partner_income = fields.Integer('Partner income',
        help="The amount of pesos per month the partner earns")

    patient_income = fields.Integer('Patient income',
        help="The amount of pesos per month the patient earns")

    # --------------------------------------------------------
    # Add fields for the immediate postpartum stage. These are
    # summary fields, ie. they are summarized from the charts.
    # --------------------------------------------------------
    pp_immed_cr_high = fields.Integer('High CR')
    pp_immed_cr_low = fields.Integer('Low CR')
    pp_immed_fundus_desc = fields.Char('Fundus Desc', size=30, help="Fundus description")
    pp_immed_ebl = fields.Integer('EBL (ml)', help="Estimated blood loss (ml)")
    pp_immed_comments = fields.Char('Comments', size=100, help="Comments")

    # --------------------------------------------------------
    # Add two new sections for postpartum: continuing and ongoing.
    # --------------------------------------------------------
    postpartum_continued = fields.One2Many(
            'gnuhealth.postpartum.continued.monitor',
            'name', 'Postpartum Continued Monitor')
    postpartum_ongoing = fields.One2Many(
            'gnuhealth.postpartum.ongoing.monitor',
            'name', 'Postpartum Ongoing Monitor')

    # --------------------------------------------------------
    # We don't use this field, and it is always one because
    # by law the lay-in clinic cannot handle multiple births.
    # --------------------------------------------------------
    @staticmethod
    def default_fetuses():
        return 1



class MmcPrenatalEvaluation(ModelSQL, ModelView):
    'Prenatal and Antenatal Evaluations'
    __name__ = 'gnuhealth.patient.prenatal.evaluation'

    @staticmethod
    def get_patient_evaluation_data(ids, name):
        result = {}

        for evaluation_data in ids:

            if name == 'gestational_weeks':
                gestational_age = datetime.datetime.date(evaluation_data.evaluation_date) - evaluation_data.name.lmp

                result[evaluation_data.id] = (gestational_age.days)/7

            if name == 'gestational_days':
                gestational_age = datetime.datetime.date(evaluation_data.evaluation_date) - evaluation_data.name.lmp

                result[evaluation_data.id] = gestational_age.days

            if name == 'gestational_age':
                gestational_age = datetime.datetime.date(evaluation_data.evaluation_date) - evaluation_data.name.lmp

                result[evaluation_data.id] = "{0} {1}/7".format((gestational_age.days)/7, (gestational_age.days)%7)

            if name == 'bp':
                result[evaluation_data.id] = "{0}/{1}".format(evaluation_data.systolic, evaluation_data.diastolic)

            if name == 'eval_date_only':
                result[evaluation_data.id] = datetime.datetime.date(evaluation_data.evaluation_date)

        return result

    # --------------------------------------------------------
    # Change the field labels.
    # --------------------------------------------------------
    evaluation_date = fields.DateTime('Admission', required=True)
    fetus_heart_rate = fields.Integer('FHT', help="Fetus heart rate")
    fundal_height = fields.Integer('FH',
        help="Distance between the symphysis pubis and the uterine fundus " \
        "(S-FD) in cm")

    # --------------------------------------------------------
    # Add additional fields.
    # --------------------------------------------------------
    discharge = fields.DateTime('Discharge', help='Time the patient left')
    weight = fields.Numeric("Weight (kg)", (3,1), help="Mother's weight in kilos")
    systolic = fields.Integer('Systolic Pressure')
    diastolic = fields.Integer('Diastolic Pressure')
    cr = fields.Integer("CR", help="Mother's heart rate")
    rr = fields.Integer("RR", help="Mother's respitory rate")
    temperature = fields.Float('Temp (C)', help='Temperature in celcius of the mother')
    position = fields.Char("Position", help="Baby's position")
    examiner = fields.Char('Examiner', help="Who did the examination?")
    next_appt = fields.Date('Next Scheduled Date', help="Date of next prenatal exam")

    # --------------------------------------------------------
    # Add a gestational_age field. Health_gyneco has two similar
    # fields: gestational_weeks and gestational_days. The former
    # is only granular to the week, the later to the day. MMC
    # staff is used to the GA field being the number of weeks and
    # a fractional part with the denominator the number 7, e.g.
    # 33 2/7. Our gestational_age field will attempt to get close
    # to that.
    # --------------------------------------------------------
    gestational_age = fields.Function(fields.Char('GA'),
        'get_patient_evaluation_data')

    # --------------------------------------------------------
    # Add a convenience function that displays the blood pressure
    # as one field instead of two. Useful for the tree view.
    # --------------------------------------------------------
    bp = fields.Function(fields.Char('B/P'), 'get_patient_evaluation_data')

    # --------------------------------------------------------
    # Add a display field for the tree view that only shows the
    # admission date and not the time.
    # --------------------------------------------------------
    eval_date_only = fields.Function(fields.Date('Date'), 'get_patient_evaluation_data')




class MmcPerinatal(ModelSQL, ModelView):
    'Perinatal Information'
    __name__ = 'gnuhealth.perinatal'

    @staticmethod
    def get_perinatal_information(ids, name):
        result = {}

        for perinatal_data in ids:
            if name == 'gestational_weeks':
                gestational_age = datetime.datetime.date(perinatal_data.admission_date) - perinatal_data.name.lmp
                result[perinatal_data.id] = (gestational_age.days)/7

        return result

    # --------------------------------------------------------
    # Change selection list.
    # --------------------------------------------------------
    start_labor_mode = fields.Selection([
        ('nsd', 'NSD'),
        ('o', 'Other'),
        ], 'Delivery mode', sort=False)


    # --------------------------------------------------------
    # Placenta delivery fields.
    # --------------------------------------------------------
    placenta_datetime = fields.DateTime('Placenta delivery')
    placenta_expulsion = fields.Selection([
        ('s', 'Schult'),
        ('d', 'Duncan'),
        ], 'Placenta expulsion', sort=False)
    placenta_delivery = fields.Selection([
        ('s', 'Spontaneous'),
        ('cct', 'CCT'),
        ('ma', 'Manual Assist'),
        ('mr', 'Manual Removal'),
        ], 'Placenta delivery type', sort=False)
    placenta_duration = fields.Integer('Duration (min)',
        help="Duration of the placenta delivery in minutes")
    ebl = fields.Integer('EBL (ml)', help="Estimated blood loss (ml)")

    # --------------------------------------------------------
    # Additional intake fields.
    # --------------------------------------------------------
    begin_labor_intake = fields.DateTime('Labor start')
    pos_intake = fields.Char('POS', size=10)
    fundal_height_intake = fields.Integer('Fundal Height')
    systolic_intake = fields.Integer('Systolic Pressure')
    diastolic_intake = fields.Integer('Diastolic Pressure')
    cr_intake = fields.Integer("CR", help="Mother's heart rate")
    fetus_cr_intake = fields.Integer("FHT", help="Fetus heart rate")
    temperature_intake = fields.Float('Temp (C)', help='Temperature in celcius of the mother')
    examiner_intake = fields.Char('Examiner', required=True)




class MmcPerinatalMonitor(ModelSQL, ModelView):
    'Perinatal Monitor'
    __name__ = 'gnuhealth.perinatal.monitor'

    # --------------------------------------------------------
    # Rename the labels of these fields.
    # --------------------------------------------------------
    frequency = fields.Integer('CR')
    f_frequency = fields.Integer('FHT')

    # --------------------------------------------------------
    # Add a new value.
    # --------------------------------------------------------
    fetus_position = fields.Selection([
        ('c', 'Cephalic'),
        ('o', 'Occiput / Cephalic Posterior'),
        ('fb', 'Frank Breech'),
        ('cb', 'Complete Breech'),
        ('t', 'Transverse Lie'),
        ('t', 'Footling Breech'),
        ], 'Fetus Position', sort=False)

    # --------------------------------------------------------
    # Hide these fields.
    # --------------------------------------------------------
    contractions = fields.Integer('Contractions', states={'invisible': True})

    # --------------------------------------------------------
    # Add these fields.
    # --------------------------------------------------------
    contractionsStr = fields.Char('Contractions', size=12)

    # --------------------------------------------------------
    # Default field values.
    # --------------------------------------------------------
    @staticmethod
    def default_fetus_position():
        return 'c'



class MmcPuerperiumMonitor(ModelSQL, ModelView):
    'Puerperium Monitor'
    __name__ = 'gnuhealth.puerperium.monitor'

    # --------------------------------------------------------
    # Change the labels of these fields.
    # --------------------------------------------------------
    temperature = fields.Float('Temp (C)', help='Temperature in celcius of the mother')
    frequency = fields.Integer('CR')

    # --------------------------------------------------------
    # Add additional fields.
    # --------------------------------------------------------
    ebl = fields.Integer('EBL (ml)', help="Estimated blood loss (ml)")
    examiner = fields.Char('Examiner', required=True)

    # --------------------------------------------------------
    # Add a convenience function that displays the blood pressure
    # as one field instead of two. Useful for the tree view.
    # --------------------------------------------------------
    bp = fields.Function(fields.Char('B/P'), 'get_patient_evaluation_data')

    # --------------------------------------------------------
    # Add a display field for the tree view that only shows the
    # admission date and not the time.
    # --------------------------------------------------------
    eval_date_only = fields.Function(fields.Date('Date'), 'get_patient_evaluation_data')

    @staticmethod
    def get_patient_evaluation_data(ids, name):
        result = {}

        for evaluation_data in ids:
            if name == 'bp':
                result[evaluation_data.id] = "{0}/{1}".format(evaluation_data.systolic, evaluation_data.diastolic)

            if name == 'eval_date_only':
                result[evaluation_data.id] = datetime.datetime.date(evaluation_data.date)

        return result



class Address(ModelSQL, ModelView):
    "Address"
    __name__ = 'party.address'

    # --------------------------------------------------------
    # Change labels, adjust help, etc.
    # --------------------------------------------------------
    name = fields.Char('Addr Name', help="Example: Home, mother's house, prior home, etc.",
            states={'readonly': ~Eval('active'),}, depends=['active'])
    street = fields.Char('Address',
            states={'readonly': ~Eval('active'),}, depends=['active'])

    # --------------------------------------------------------
    # Add new fields.
    # --------------------------------------------------------
    barangay = fields.Char('Barangay', help="The patient's barangay")
    is_agdao = fields.Boolean('Is from Agdao?',
        help="Check if the patient is from Agdao")

    @staticmethod
    def default_city():
        # TODO: do this right.
        return 'Davao City'



class MmcPostpartumContinuedMonitor(ModelSQL, ModelView):
    'Postpartum Continued Monitor'
    __name__ = 'gnuhealth.postpartum.continued.monitor'

    name = fields.Many2One('gnuhealth.patient.pregnancy', 'Patient Pregnancy')
    date_time = fields.DateTime('Date/Time', required=True)
    initials = fields.Char('Initials', size=10, help="Who did the examination?")

    # --------------------------------------------------------
    # Mother's fields.
    # --------------------------------------------------------
    systolic = fields.Integer('Systolic Pressure', help="Mother's systolic")
    diastolic = fields.Integer('Diastolic Pressure', help="Mother's diastolic")
    mother_cr = fields.Integer("CR", help="Mother's heart rate")
    mother_temp = fields.Float('Temp (C)', help='Temperature in celcius of the mother')
    fundus_desc = fields.Char('Fundus Desc', size=30, help="Fundus description")
    ebl = fields.Integer('EBL (ml)', help="Estimated blood loss (ml)")

    # --------------------------------------------------------
    # Baby's fields.
    # --------------------------------------------------------
    bfed = fields.Boolean('BFed', help="Breast Fed");
    baby_temp = fields.Float('Baby Temp (C)', help='Temperature in celcius of the baby')
    baby_rr = fields.Integer("Baby RR", help="Baby's respitory rate")
    baby_cr = fields.Integer("Baby CR", help="Baby's heart rate")
    comments = fields.Char('Comments', size=100, help="Comments")

    # --------------------------------------------------------
    # Add a convenience function that displays the blood pressure
    # as one field instead of two. Useful for the tree view.
    # --------------------------------------------------------
    bp = fields.Function(fields.Char('B/P'), 'get_patient_evaluation_data')

    @staticmethod
    def get_patient_evaluation_data(ids, name):
        result = {}
        for evaluation_data in ids:
            if name == 'bp':
                if evaluation_data.systolic == None or evaluation_data.diastolic == None:
                    result[evaluation_data.id] = ''
                else:
                    result[evaluation_data.id] = "{0}/{1}".format(evaluation_data.systolic, evaluation_data.diastolic)
        return result



class MmcPostpartumOngoingMonitor(ModelSQL, ModelView):
    'Postpartum Ongoing Monitor'
    __name__ = 'gnuhealth.postpartum.ongoing.monitor'

    name = fields.Many2One('gnuhealth.patient.pregnancy', 'Patient Pregnancy')

    # --------------------------------------------------------
    # Examination fields.
    # --------------------------------------------------------
    date_time = fields.DateTime('Date/Time', required=True)
    initials = fields.Char('Initials', size=10, required=True,
            help="Who did the examination?")

    # --------------------------------------------------------
    # Baby fields.
    # --------------------------------------------------------
    b_weight = fields.Integer('Weight', help="Weight in grams")
    b_temp = fields.Float('Temp (C)', help='Temperature in celcius of the baby')
    b_cr = fields.Integer("Baby CR", help="Baby's heart rate")
    b_rr = fields.Integer("Baby RR", help="Baby's respitory rate")
    b_lungs = fields.Char('Lungs', size=70)
    b_skin = fields.Char('Color/Skin', size=70)
    b_cord = fields.Char('Cord', size=70)
    b_urine_last_24 = fields.Char('Urine last 24 hours', size=70)
    b_stool_last_24 = fields.Char('Stool last 24 hours', size=70)
    b_ss_infection = fields.Char('SS Infection', size=70)
    b_feeding = fields.Char('Feeding', size=70)
    b_nbs = fields.DateTime('NBS')
    b_bcg = fields.Char('BCG', size=70)
    b_other = fields.Char('Other', size=70)

    # --------------------------------------------------------
    # Mother fields.
    # --------------------------------------------------------
    m_temp = fields.Float('Temp (C)', help='Temperature in celcius of the mother')
    m_systolic = fields.Integer('Systolic Pressure', help="Mother's systolic")
    m_diastolic = fields.Integer('Diastolic Pressure', help="Mother's diastolic")
    m_cr = fields.Integer("CR", help="Mother's heart rate")
    m_breasts = fields.Char('Breasts', size=70)
    m_fundus = fields.Char('Fundus', size=70)
    m_perineum = fields.Char('Perineum', size=70)
    m_lochia = fields.Char('Lochia', size=70)
    m_urine = fields.Char('Urine', size=70)
    m_stool = fields.Char('Stool', size=70)
    m_ss_infection = fields.Char('SS Infection', size=70)
    m_other = fields.Char('Other', size=70)
    m_next_visit = fields.DateTime('Next Scheduled Visit')



