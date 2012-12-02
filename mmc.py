from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, Not, Bool

#class MmcPatient(ModelSQL, ModelView):
	#'Adapt the gnuhealth.patient to our needs'
	#_name = 'gnuhealth.patient'
	#_description = __doc__

#MMC()

class MmcPatientData(ModelSQL, ModelView):
    'Patient related information'
    _name = 'gnuhealth.patient'
    _description = __doc__

    # Hide these fields
    ethnic_group = fields.Many2One('gnuhealth.ethnicity', 'x',
            states={'invisible': True})
    family = fields.Many2One('gnuhealth.family', 'x',
            states={'invisible': True})
    primary_care_doctor = fields.Many2One('gnuhealth.physician', 'x',
            states={'invisible': True})
    current_insurance = fields.Many2One('gnuhealth.insurance', 'x',
            states={'invisible': True})

    # Expand the selection list of these fields.
    marital_status = fields.Selection([
        ('l', 'Live-in'),
        ('s', 'Single'),
        ('m', 'Married'),
        ('w', 'Widowed'),
        ('d', 'Divorced'),
        ('x', 'Separated'),
        ], 'Marital Status', sort=False)


    # Add Phil Health related fields.
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

    # Add new screening related fields.
    gram_stain = fields.Boolean('Gram Stain',
        help="Check if gram stain was done")
    breast_self_exam_taught = fields.Boolean('Taught breast self exam',
        help="Check if patient has been taught how to do breast self exams")


    # Department of Health required id.
   #doh_id = fields.Char(
           #'DOH Id',
           #help="Dept of Health id",
           #required=True)

   ## Insure unique DOH Ids are used.
   #def validate_doh_id(self, ids):


    # Set a reasonable default sex for a maternity clinic.
    def default_sex(self):
        return 'f'

    # 99.4% of all people in the Philippines are RH positive. Oftentimes
    # blood tests do not even test for this.
    def default_rh(self):
        return '+'


MmcPatientData()

class MmcVaccination(ModelSQL, ModelView):
    'Patient Vaccination information'
    _name = 'gnuhealth.vaccination'
    _description = __doc__

    # Was the vaccine administered by MMC?
    vaccine_by_mmc = fields.Boolean('Administered by MMC',
        help="Check if this vaccine was administered by Mercy Maternity Clinic")

    # Hide these unnecessary fields
    vaccine_expiration_date = fields.Date('x', states={'invisible': True})
    vaccine_lot = fields.Char('x', states={'invisible': True})
    institution = fields.Many2One('party.party', 'x', states={'invisible': True})


    # Revise validation to not require the next_dose_date field.
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

    # Change the field label.
    doctor = fields.Many2One('gnuhealth.physician', 'Name',
        help='Name of person who prescribed the medicament')

MmcPatientMedication()


class MmcMedicationTemplate(ModelSQL, ModelView):
    'Template for medication'
    _name = 'gnuhealth.medication.template'
    _description = __doc__

    # Change the field label.
    medicament = fields.Many2One('gnuhealth.medicament', 'Name of Med',
        required=True, help='Prescribed Medicine')



MmcMedicationTemplate()


