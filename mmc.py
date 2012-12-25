# -------------------------------------------------------------------------------
# mmc.py
#
# Customization of GnuHealth for the needs of Mercy Maternity Clinic, Inc.
# -------------------------------------------------------------------------------
from trytond.model import ModelView, ModelSingleton, ModelSQL, fields
from trytond.pyson import Eval, Not, Bool
from trytond.pool import Pool

import datetime
import logging

mmcLog = logging.getLogger('mmc')

class MmcSequences(ModelSingleton, ModelSQL, ModelView):
    "Sequences for MMC"

    _description = __doc__
    _name = "mmc.sequences"

    doh_sequence = fields.Property(fields.Many2One('ir.sequence',
        'DOH Sequence', domain=[('code', '=', 'mmc.doh')],
        required=True))

MmcSequences()


class MmcPatientData(ModelSQL, ModelView):
    'Patient related information'
    _name = 'gnuhealth.patient'
    _description = __doc__

    # --------------------------------------------------------
    # Hide these fields
    # --------------------------------------------------------
    ethnic_group = fields.Many2One('gnuhealth.ethnicity', 'x',
            states={'invisible': True})

    family = fields.Many2One('gnuhealth.family', 'x',
            states={'invisible': True})

    primary_care_doctor = fields.Many2One('gnuhealth.physician', 'x',
            states={'invisible': True})

    current_insurance = fields.Many2One('gnuhealth.insurance', 'x',
            states={'invisible': True})


    # --------------------------------------------------------
    # Expand the selection list of these fields.
    # --------------------------------------------------------
    marital_status = fields.Selection([
        ('l', 'Live-in'),
        ('s', 'Single'),
        ('m', 'Married'),
        ('w', 'Widowed'),
        ('d', 'Divorced'),
        ('x', 'Separated'),
        ], 'Marital Status', sort=False)


    # --------------------------------------------------------
    # Change the label on these fields.
    # --------------------------------------------------------
    diseases = fields.One2Many('gnuhealth.patient.disease', 'name', 'Condition')


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
    # Department of Health required id.
    # --------------------------------------------------------
    doh_id = fields.Char('DOH ID',
        size=8,
        help="Dept of Health id", required=False,
        on_change=['doh_id'])

    # --------------------------------------------------------
    # Format DOH ID # in the customary fashion after the user
    # types it in. User can type with hyphens or not. But don't
    # change anything unless the field seems correct.
    # --------------------------------------------------------
    def on_change_doh_id(self, vals):
        origFld = vals.get('doh_id')
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
    def on_change_phil_health_id(self, vals):
        origFld = vals.get('phil_health_id')
        phic = origFld.replace('-', '')
        val = origFld
        if ((len(phic) == 12) and (phic.isdigit())):
            val = "{0}-{1}-{2}".format(phic[:2], phic[2:11], phic[-1])
        return {'phil_health_id': val}

    # --------------------------------------------------------
    # Validate the DOH ID.
    # --------------------------------------------------------
    def validate_doh_id(self, ids):
        for patientData in self.browse(ids):
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
    def validate_phil_health_id(self, ids):
        for patientData in self.browse(ids):
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
    def default_sex(self):
        return 'f'


    # --------------------------------------------------------
    # 99.4% of all people in the Philippines are RH positive.
    # Oftentimes blood tests do not even test for this.
    # --------------------------------------------------------
    def default_rh(self):
        return '+'

    # --------------------------------------------------------
    # Add our validations to the class.
    # --------------------------------------------------------
    def __init__(self):
        super(MmcPatientData, self).__init__()
        self._sql_constraints = [
            ('name_uniq', 'UNIQUE(name)', 'The Patient already exists !'),
        ]
        self._constraints += [
            ('validate_phil_health_id', 'phil_health_id_format'),
            ('validate_doh_id', 'validate_doh_id_format'),
        ]
        self._error_messages.update({
            'phil_health_id_format': 'PHIC# must be 12 numbers',
            'validate_doh_id_format': 'Department of Health ID must be 6 numbers'
        })

    # --------------------------------------------------------
    # Create a Department of Health id automatically, but it
    # can be overridden by the user, if desired, to another
    # number or a blank value.
    # --------------------------------------------------------
    def create(self, values):
        if not values.get('doh_id'):
            values = values.copy()
            sequence_obj = Pool().get('ir.sequence')
            config_obj = Pool().get('mmc.sequences')
            config = config_obj.browse(1)
            # --------------------------------------------------------
            # The sequence is prefixed with the current 4 digit year
            # but we need only a two digit year and we like it formatted
            # a certain way.
            # --------------------------------------------------------
            seq = sequence_obj.get_id(config.doh_sequence.id)[2:]
            values['doh_id'] = "{0}-{1}-{2}".format(seq[:2], seq[2:4], seq[4:6])

        return super(MmcPatientData, self).create(values)


MmcPatientData()


class MmcPatientDiseaseInfo(ModelSQL, ModelView):
    'Patient Disease History'
    _name = 'gnuhealth.patient.disease'
    _description = __doc__

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


MmcPatientDiseaseInfo()


class MmcVaccination(ModelSQL, ModelView):
    'Patient Vaccination information'
    _name = 'gnuhealth.vaccination'
    _description = __doc__

    # --------------------------------------------------------
    # Was the vaccine administered by MMC?
    # --------------------------------------------------------
    vaccine_by_mmc = fields.Boolean('Administered by MMC',
        help="Check if this vaccine was administered by Mercy Maternity Clinic")


    # --------------------------------------------------------
    # Hide these unnecessary fields
    # --------------------------------------------------------
    vaccine_expiration_date = fields.Date('x', states={'invisible': True})
    vaccine_lot = fields.Char('x', states={'invisible': True})
    institution = fields.Many2One('party.party', 'x', states={'invisible': True})


    # --------------------------------------------------------
    # Revise validation to not require the next_dose_date field.
    # --------------------------------------------------------
    def validate_next_dose_date (self, ids):
        for vaccine_data in self.browse(ids):
            if vaccine_data.next_dose_date is None:
                return True
            if (vaccine_data.next_dose_date < vaccine_data.date):
                return False
            else:
                return True

MmcVaccination()


class MmcPatientMedication(ModelSQL, ModelView):
    'Patient Medication'
    _name = 'gnuhealth.patient.medication'
    _inherits = {'gnuhealth.medication.template': 'template'}
    _description = __doc__

    # --------------------------------------------------------
    # Change the field label.
    # --------------------------------------------------------
    doctor = fields.Many2One('gnuhealth.physician', 'Name',
        help='Name of person who prescribed the medicament')

MmcPatientMedication()


class MmcMedicationTemplate(ModelSQL, ModelView):
    'Template for medication'
    _name = 'gnuhealth.medication.template'
    _description = __doc__

    # --------------------------------------------------------
    # Change the field label.
    # --------------------------------------------------------
    medicament = fields.Many2One('gnuhealth.medicament', 'Name of Med',
        required=True, help='Prescribed Medicine')

MmcMedicationTemplate()


class MmcPatientPregnancy(ModelSQL, ModelView):
    'Patient Pregnancy'
    _name = 'gnuhealth.patient.pregnancy'
    _description = __doc__

    # --------------------------------------------------------
    # Change the field label.
    # --------------------------------------------------------
    pdd = fields.Function (fields.Date('Due Date'), 'get_pregnancy_data')


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



MmcPatientPregnancy()


class MmcPrenatalEvaluation(ModelSQL, ModelView):
    'Prenatal and Antenatal Evaluations'
    _name = 'gnuhealth.patient.prenatal.evaluation'
    _description = __doc__

    def get_patient_evaluation_data(self, ids, name):
        result = {}

        for evaluation_data in self.browse(ids):

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

    # --------------------------------------------------------
    # Add additional fields.
    # --------------------------------------------------------
    discharge = fields.DateTime('Discharge', help='Time the patient left')
    weight = fields.Integer("Weight", help="Mother's weight in kilos")
    systolic = fields.Integer('Systolic Pressure')
    diastolic = fields.Integer('Diastolic Pressure')
    cr = fields.Integer("CR", help="Mother's heart rate")
    rr = fields.Integer("RR", help="Mother's respitory rate")
    temperature = fields.Float('Temp', help='Temperature in celcius of the mother')
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


MmcPrenatalEvaluation()


