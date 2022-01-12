from __future__ import unicode_literals
import logging
from django.db import models
from django.contrib.gis.db import models
from django.contrib.postgres.fields.jsonb import JSONField
from django.db.models import Max
from multiselectfield import MultiSelectField
from django.utils.encoding import python_2_unicode_compatible
from ledger.accounts.models import EmailUser, RevisionedMixin
from ledger.licence.models import LicenceType
from wildlifecompliance.components.main.models import (
        CommunicationsLogEntry,
        UserAction, 
        Document
        )
from wildlifecompliance.components.main.related_item import can_close_record
from wildlifecompliance.components.users.models import RegionDistrict, CompliancePermissionGroup

logger = logging.getLogger(__name__)

def update_compliance_doc_filename(instance, filename):
    #return 'wildlifecompliance/compliance/{}/documents/{}'.format(
        #instance.call_email.id, filename)
    pass

def update_call_email_doc_filename(instance, filename):
    # return 'wildlifecompliance/compliance/{}/documents/{}'.format(
      #  instance.call_email.id, filename)
    pass

def update_compliance_comms_log_filename(instance, filename):
    #return 'wildlifecompliance/compliance/{}/communications/{}/{}'.format(
        #instance.log_entry.call_email.id, instance.id, filename)
    pass

def update_call_email_comms_log_filename(instance, filename):
    #return 'wildlifecompliance/compliance/{}/communications/{}/{}'.format(
     #   instance.log_entry.call_email.id, instance.id, filename)
    pass

def update_compliance_workflow_log_filename(instance, filename):
    #return 'wildlifecompliance/compliance/{}/workflow/{}/{}'.format(
        #instance.workflow.call_email.id, instance.id, filename)
    pass


class Classification(models.Model):
    CLASSIFICATION_COMPLAINT = 'complaint'
    CLASSIFICATION_ENQUIRY = 'enquiry'
    CLASSIFICATION_INCIDENT = 'incident'

    NAME_CHOICES = (
        (CLASSIFICATION_COMPLAINT, 'Complaint'),
        (CLASSIFICATION_ENQUIRY, 'Enquiry'),
        (CLASSIFICATION_INCIDENT, 'Incident'),
    )

    name = models.CharField(
        max_length=30,
        choices=NAME_CHOICES,
        default=CLASSIFICATION_COMPLAINT,
        unique=True
    )

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_Classification'
        verbose_name_plural = 'CM_Classifications'

    def __str__(self):
        return self.get_name_display()

class CallType(models.Model):
    CALL_TYPE_GENERAL_ENQUIRY = 'general_enquiry'
    CALL_TYPE_ILLEGAL_ACTIVITY = 'illegal_activity'
    CALL_TYPE_AMPHIBIAN = 'amphibian'
    CALL_TYPE_MAMMAL = 'mammal'
    CALL_TYPE_BIRD = 'bird'
    CALL_TYPE_NON_NATIVE_SPECIES = 'non_native_species'
    CALL_TYPE_REPTILE = 'reptile'
    CALL_TYPE_OTHER = 'other'

    NAME_CHOICES = (
        (CALL_TYPE_GENERAL_ENQUIRY, 'General Enquiry'),
        (CALL_TYPE_ILLEGAL_ACTIVITY, 'Illegal Activity'),
        (CALL_TYPE_AMPHIBIAN, 'Ambhibian - e.g. frog, cane toad'),
        (CALL_TYPE_MAMMAL, 'Mammal'),
        (CALL_TYPE_BIRD, 'Bird'),
        (CALL_TYPE_NON_NATIVE_SPECIES, 'Non native species - e.g. pigeon, fox, cattle, peacock'),
        (CALL_TYPE_REPTILE, 'Reptile - e.g. snake, turtles, lizard'),
        (CALL_TYPE_OTHER, 'Other - e.g. spider, bees, fish'),
    )

    name = models.CharField(
        max_length=50,
        choices=NAME_CHOICES,
        default=CALL_TYPE_AMPHIBIAN,
        unique=True,
    )

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_CallType'
        verbose_name_plural = 'CM_CallTypes'

    def __str__(self):
        return self.get_name_display()

class WildcareSpeciesType(models.Model):
    WILDCARE_SPECIES_TYPE_CANETOAD = 'cane_toad'
    WILDCARE_SPECIES_TYPE_FROG = 'frog'
    WILDCARE_SPECIES_TYPE_BUTCHERBIRD = 'butcherbird'
    WILDCARE_SPECIES_TYPE_COCKATOO = 'cockatoo'
    WILDCARE_SPECIES_TYPE_COOT = 'coot'
    WILDCARE_SPECIES_TYPE_CORMORANT = 'cormorant'
    WILDCARE_SPECIES_TYPE_DUCK = 'duck'
    WILDCARE_SPECIES_TYPE_EAGLE_FALCON_HAWK = 'eagle_falcon_hawk'
    WILDCARE_SPECIES_TYPE_EMU = 'emu'
    WILDCARE_SPECIES_TYPE_FINCH = 'finch'
    WILDCARE_SPECIES_TYPE_GOOSE = 'goose'
    WILDCARE_SPECIES_TYPE_HERON = 'heron'
    WILDCARE_SPECIES_TYPE_HONEYEATER = 'honeyeater'
    WILDCARE_SPECIES_TYPE_IBIS = 'ibis'
    WILDCARE_SPECIES_TYPE_KINGFISHER = 'kingfisher'
    WILDCARE_SPECIES_TYPE_MAGPIE = 'magpie'
    WILDCARE_SPECIES_TYPE_MAGPIE_LARK = 'magpie_lark'
    WILDCARE_SPECIES_TYPE_OWL = 'owl'
    WILDCARE_SPECIES_TYPE_PARROT = 'parrot'
    WILDCARE_SPECIES_TYPE_PEACOCK = 'peacock'
    WILDCARE_SPECIES_TYPE_PENGUIN = 'penguin'
    WILDCARE_SPECIES_TYPE_QUAIL = 'quail'
    WILDCARE_SPECIES_TYPE_RAINBOW_BEE_EATER = 'rainbow_bee_eater'
    WILDCARE_SPECIES_TYPE_RAINBOW_LORIKEET = 'rainbow_lorikeet'
    WILDCARE_SPECIES_TYPE_RAVEN = 'raven'
    WILDCARE_SPECIES_TYPE_ALBATROSS = 'albatross'
    WILDCARE_SPECIES_TYPE_GULL = 'gull'
    WILDCARE_SPECIES_TYPE_PELICAN = 'pelican'
    WILDCARE_SPECIES_TYPE_SHEARWATER = 'shearwater'
    WILDCARE_SPECIES_TYPE_TERN = 'tern'
    WILDCARE_SPECIES_TYPE_SWALLOW = 'swallow'
    WILDCARE_SPECIES_TYPE_SWAN = 'swan'
    WILDCARE_SPECIES_TYPE_TAWNY_FROGMOUTH = 'tawny_frogmouth'
    WILDCARE_SPECIES_TYPE_WILLY_WAGTAIL = 'willy_wagtail'
    WILDCARE_SPECIES_TYPE_BAT = 'bat'
    WILDCARE_SPECIES_TYPE_DINGO = 'dingo'
    WILDCARE_SPECIES_TYPE_DOLPHIN = 'dolphin'
    WILDCARE_SPECIES_TYPE_ECHIDNA = 'echidna'
    WILDCARE_SPECIES_TYPE_FERRET = 'ferret'
    WILDCARE_SPECIES_TYPE_KANGAROO = 'kangaroo'
    WILDCARE_SPECIES_TYPE_POSSUM = 'possum'
    WILDCARE_SPECIES_TYPE_QUENDA_OR_BANDICOOT = 'quenda_or_bandicoot'
    WILDCARE_SPECIES_TYPE_QUOKKA = 'quokka'
    WILDCARE_SPECIES_TYPE_SEAL_AND_SEALION = 'seal_and_sealion'
    WILDCARE_SPECIES_TYPE_WHALE = 'whale'
    WILDCARE_SPECIES_TYPE_WOMBAT = 'wombat'
    WILDCARE_SPECIES_TYPE_LIZARD = 'lizard'
    WILDCARE_SPECIES_TYPE_SNAKE = 'snake'
    WILDCARE_SPECIES_TYPE_TURTLE = 'turtle'
    WILDCARE_SPECIES_TYPE_CAT = 'cat'
    WILDCARE_SPECIES_TYPE_DOG = 'dog'
    WILDCARE_SPECIES_TYPE_FOX = 'fox'
    WILDCARE_SPECIES_TYPE_RABBIT = 'rabbit'
    WILDCARE_SPECIES_TYPE_RODENT = 'rodent'
    WILDCARE_SPECIES_TYPE_CHICKEN = 'chicken'
    WILDCARE_SPECIES_TYPE_DUCK_DOMESTIC = 'duck_domestic'
    WILDCARE_SPECIES_TYPE_INDIAN_RINGNECK_PARAKEET = 'indian_ringneck_parakeet'
    WILDCARE_SPECIES_TYPE_PIGEON_OR_DOVE_ = 'pigeon_or_dove'
    WILDCARE_SPECIES_TYPE_FISH = 'fish'
    WILDCARE_SPECIES_TYPE_SHARK = 'shark'
    WILDCARE_SPECIES_TYPE_CATERPILLAR = 'caterpillar'
    WILDCARE_SPECIES_TYPE_BEES_AND_WASPS = 'bees_and_wasps'
    WILDCARE_SPECIES_TYPE_CRAB = 'crab'
    WILDCARE_SPECIES_TYPE_SPIDER = 'spider'
    WILDCARE_SPECIES_TYPE_OTHER = 'other'


    WILDCARE_SPECIES_TYPE_CHOICES = (
        (WILDCARE_SPECIES_TYPE_CANETOAD, 'Cane Toad'),
        (WILDCARE_SPECIES_TYPE_FROG, 'Frog'),
        (WILDCARE_SPECIES_TYPE_BUTCHERBIRD, 'Butcherbird'),
        (WILDCARE_SPECIES_TYPE_COCKATOO, 'Cockatoo'),
        (WILDCARE_SPECIES_TYPE_COOT, 'Coot'),
        (WILDCARE_SPECIES_TYPE_CORMORANT, 'Cormorant'),
        (WILDCARE_SPECIES_TYPE_DUCK, 'Duck'),
        (WILDCARE_SPECIES_TYPE_EAGLE_FALCON_HAWK, 'Eagle, Falcon, Hawk'),
        (WILDCARE_SPECIES_TYPE_EMU, 'Emu'),
        (WILDCARE_SPECIES_TYPE_GOOSE, 'Goose'),
        (WILDCARE_SPECIES_TYPE_HERON, 'Heron'),
        (WILDCARE_SPECIES_TYPE_HONEYEATER, 'Honeyeater'),
        (WILDCARE_SPECIES_TYPE_IBIS, 'Ibis'),
        (WILDCARE_SPECIES_TYPE_KINGFISHER, 'Kingfisher'),
        (WILDCARE_SPECIES_TYPE_MAGPIE, 'Magpie'),
        (WILDCARE_SPECIES_TYPE_MAGPIE_LARK, 'Magpie-Lark'),
        (WILDCARE_SPECIES_TYPE_OWL, 'Owl'),
        (WILDCARE_SPECIES_TYPE_PARROT, 'Parrot'),
        (WILDCARE_SPECIES_TYPE_PEACOCK, 'Peacock'),
        (WILDCARE_SPECIES_TYPE_PENGUIN, 'Penguin'),
        (WILDCARE_SPECIES_TYPE_QUAIL, 'Quail'),
        (WILDCARE_SPECIES_TYPE_RAINBOW_BEE_EATER, 'Rainbow Bee-Eater'),
        (WILDCARE_SPECIES_TYPE_RAINBOW_LORIKEET, 'Rainbow Lorikeet'),
        (WILDCARE_SPECIES_TYPE_RAVEN, 'Raven'),
        (WILDCARE_SPECIES_TYPE_ALBATROSS, 'Albatross'),
        (WILDCARE_SPECIES_TYPE_GULL, 'Gull'),
        (WILDCARE_SPECIES_TYPE_PELICAN, 'Pelican'),
        (WILDCARE_SPECIES_TYPE_SHEARWATER, 'Shearwater'),
        (WILDCARE_SPECIES_TYPE_TERN, 'Tern'),
        (WILDCARE_SPECIES_TYPE_SWALLOW, 'Swallow'),
        (WILDCARE_SPECIES_TYPE_SWAN, 'Swan'),
        (WILDCARE_SPECIES_TYPE_TAWNY_FROGMOUTH, 'Tawny Frogmouth'),
        (WILDCARE_SPECIES_TYPE_WILLY_WAGTAIL, 'Willy Wagtail'),
        (WILDCARE_SPECIES_TYPE_BAT, 'Bat'),
        (WILDCARE_SPECIES_TYPE_DINGO, 'Dingo'),
        (WILDCARE_SPECIES_TYPE_DOLPHIN, 'Dolphin'),
        (WILDCARE_SPECIES_TYPE_ECHIDNA, 'Echidna'),
        (WILDCARE_SPECIES_TYPE_FERRET, 'Ferret'),
        (WILDCARE_SPECIES_TYPE_KANGAROO, 'Kangaroo'),
        (WILDCARE_SPECIES_TYPE_POSSUM, 'Possum'),
        (WILDCARE_SPECIES_TYPE_QUENDA_OR_BANDICOOT, 'Quenda or Bandicoot'),
        (WILDCARE_SPECIES_TYPE_QUOKKA, 'Quokka'),
        (WILDCARE_SPECIES_TYPE_SEAL_AND_SEALION, 'Seal and Sea Lion'),
        (WILDCARE_SPECIES_TYPE_WHALE, 'Whale'),
        (WILDCARE_SPECIES_TYPE_WOMBAT, 'Wombat'),
        (WILDCARE_SPECIES_TYPE_LIZARD, 'Lizard'),
        (WILDCARE_SPECIES_TYPE_SNAKE, 'Snake'),
        (WILDCARE_SPECIES_TYPE_TURTLE, 'Turtle'),
        (WILDCARE_SPECIES_TYPE_CAT, 'Cat'),
        (WILDCARE_SPECIES_TYPE_DOG, 'Dog'),
        (WILDCARE_SPECIES_TYPE_FOX, 'Fox'),
        (WILDCARE_SPECIES_TYPE_RABBIT, 'Rabbit'),
        (WILDCARE_SPECIES_TYPE_RODENT, 'Rodent - Rat, mouse'),
        (WILDCARE_SPECIES_TYPE_CHICKEN, 'Chicken'),
        (WILDCARE_SPECIES_TYPE_DUCK_DOMESTIC, 'Duck - domestic'),
        (WILDCARE_SPECIES_TYPE_INDIAN_RINGNECK_PARAKEET,'Indian Ringneck Parakeet'),
        (WILDCARE_SPECIES_TYPE_PIGEON_OR_DOVE_,'Pigeon or Dove'),
        (WILDCARE_SPECIES_TYPE_FISH,'Fish'),
        (WILDCARE_SPECIES_TYPE_SHARK,'Shark'),
        (WILDCARE_SPECIES_TYPE_CATERPILLAR,'Caterpillar'),
        (WILDCARE_SPECIES_TYPE_BEES_AND_WASPS,'Bees And Wasps'),
        (WILDCARE_SPECIES_TYPE_CRAB,'Crab'),
        (WILDCARE_SPECIES_TYPE_SPIDER,'Spider'),
        (WILDCARE_SPECIES_TYPE_OTHER, 'Other'),
    )

    call_type=models.ForeignKey(CallType, on_delete=models.CASCADE , related_name='wildcare_species_types', blank=True, null=True)
    species_name = models.CharField(
        max_length=100,
        choices=WILDCARE_SPECIES_TYPE_CHOICES,
        unique=True,
    )

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_WildcareSpeciesType'
        verbose_name_plural = 'CM_WildcareSpeciesTypes'
        ordering = ['species_name']
        #unique_together = ['species_name','call_type']

    def __str__(self):
        return self.get_species_name_display()
        
class WildcareSpeciesSubType(models.Model):
    WILDCARE_SPECIES_SUB_TYPE_CORELLA = 'corella'
    WILDCARE_SPECIES_SUB_TYPE_RED_TAILED_BLACK = 'red_tailed_black'
    WILDCARE_SPECIES_SUB_TYPE_WHITE_TAILED_BLACK = 'white_tailed_black'
    WILDCARE_SPECIES_SUB_TYPE_SWAMPHEN = 'swamphen'
    WILDCARE_SPECIES_SUB_TYPE_DARTER = 'darter'
    WILDCARE_SPECIES_SUB_TYPE_GOSHAWK = 'goshawk'
    WILDCARE_SPECIES_SUB_TYPE_KESTREL = 'kestrel'
    WILDCARE_SPECIES_SUB_TYPE_OSPREY = 'osprey'
    WILDCARE_SPECIES_SUB_TYPE_PEREGRINE = 'peregrine'
    WILDCARE_SPECIES_SUB_TYPE_WEDGE_TAILED = 'wedge_tailed'
    WILDCARE_SPECIES_SUB_TYPE_WHITE_BELLIED_SEA = 'white_bellied_sea'
    WILDCARE_SPECIES_SUB_TYPE_EGRET = 'egret'
    WILDCARE_SPECIES_SUB_TYPE_NANKEEN_NIGHT = 'nankeen_night'
    WILDCARE_SPECIES_SUB_TYPE_NEW_HOLLAND = 'new_holland'
    WILDCARE_SPECIES_SUB_TYPE_WATTLEBIRD = 'wattlebird'
    WILDCARE_SPECIES_SUB_TYPE_BLUE_WINGED_KOOKABURRA = 'blue_winged_kookaburra'
    WILDCARE_SPECIES_SUB_TYPE_LAUGHING_KOOKABURRA = 'laughing_kookaburra'
    WILDCARE_SPECIES_SUB_TYPE_SACRED = 'sacred'
    WILDCARE_SPECIES_SUB_TYPE_BARN = 'barn'
    WILDCARE_SPECIES_SUB_TYPE_BOOKBOOK = 'bookbook'
    WILDCARE_SPECIES_SUB_TYPE_AUSTRALIAN_RINGNECK = "28_australian_ringneck"
    WILDCARE_SPECIES_SUB_TYPE_COCKATIEL = 'cockatiel'
    WILDCARE_SPECIES_SUB_TYPE_GALAH = 'galah_pink_and_grey'
    WILDCARE_SPECIES_SUB_TYPE_ROSELLA = 'rosella'
    WILDCARE_SPECIES_SUB_TYPE_LITTLE = 'little'
    WILDCARE_SPECIES_SUB_TYPE_WELCOME = 'welcome'
    WILDCARE_SPECIES_SUB_TYPE_TAMMAR_WALLABY = 'tammar_wallaby'
    WILDCARE_SPECIES_SUB_TYPE_WESTERN_BRUSH_WALLABY = 'western_brush_wallaby'
    WILDCARE_SPECIES_SUB_TYPE_WESTERN_GREY = 'western_grey'
    WILDCARE_SPECIES_SUB_TYPE_BRUSHTAIL = 'brushtail'
    WILDCARE_SPECIES_SUB_TYPE_PYGMY = 'pygmy'
    WILDCARE_SPECIES_SUB_TYPE_RINGTAIL = 'ringtail'
    WILDCARE_SPECIES_SUB_TYPE_BLUE_TONGUE_BOBTAIL = 'blue_tongue_bobtail'
    WILDCARE_SPECIES_SUB_TYPE_GOANNA = 'goanna'
    WILDCARE_SPECIES_SUB_TYPE_MONITOR = 'monitor'
    WILDCARE_SPECIES_SUB_TYPE_SKINK = 'skink'
    WILDCARE_SPECIES_SUB_TYPE_DUGITE = 'dugite'
    WILDCARE_SPECIES_SUB_TYPE_PYTHON = 'python'
    WILDCARE_SPECIES_SUB_TYPE_TIGER = 'tiger'
    WILDCARE_SPECIES_SUB_TYPE_LONG_NECKED_OBLANGA = 'long_necked_oblanga'
    WILDCARE_SPECIES_SUB_TYPE_MARINE = 'marine'
    WILDCARE_SPECIES_SUB_TYPE_WESTERN_SWAMP = 'western_swamp'


    WILDCARE_SPECIES_SUB_TYPE_CHOICES = (
        (WILDCARE_SPECIES_SUB_TYPE_CORELLA, 'Corella'),
        (WILDCARE_SPECIES_SUB_TYPE_RED_TAILED_BLACK, 'Red-tailed Black'),
        (WILDCARE_SPECIES_SUB_TYPE_WHITE_TAILED_BLACK, 'White-tailed Black'),
        (WILDCARE_SPECIES_SUB_TYPE_SWAMPHEN, 'Swamphen'),
        (WILDCARE_SPECIES_SUB_TYPE_DARTER, 'Darter'),
        (WILDCARE_SPECIES_SUB_TYPE_GOSHAWK, 'Goshawk'),
        (WILDCARE_SPECIES_SUB_TYPE_OSPREY, 'Osprey'),
        (WILDCARE_SPECIES_SUB_TYPE_KESTREL, 'Kestrel'),
        (WILDCARE_SPECIES_SUB_TYPE_PEREGRINE, 'Peregrine'),
        (WILDCARE_SPECIES_SUB_TYPE_WEDGE_TAILED, 'Wedge-tailed'),
        (WILDCARE_SPECIES_SUB_TYPE_WHITE_BELLIED_SEA, 'White-bellied Sea'),
        (WILDCARE_SPECIES_SUB_TYPE_EGRET, 'Egret'),
        (WILDCARE_SPECIES_SUB_TYPE_NANKEEN_NIGHT, 'Nankeen Night'),
        (WILDCARE_SPECIES_SUB_TYPE_NEW_HOLLAND, 'New Holland'),
        (WILDCARE_SPECIES_SUB_TYPE_WATTLEBIRD, 'Wattlebird'),
        (WILDCARE_SPECIES_SUB_TYPE_BLUE_WINGED_KOOKABURRA, 'Blue-winged Kookaburra'),
        (WILDCARE_SPECIES_SUB_TYPE_LAUGHING_KOOKABURRA, 'Laughing Kookaburra'),
        (WILDCARE_SPECIES_SUB_TYPE_SACRED, 'Sacred'),
        (WILDCARE_SPECIES_SUB_TYPE_BARN, 'Barn'),
        (WILDCARE_SPECIES_SUB_TYPE_BOOKBOOK, 'Bookbook'),
        (WILDCARE_SPECIES_SUB_TYPE_AUSTRALIAN_RINGNECK, '28 - Australian Ringneck'),
        (WILDCARE_SPECIES_SUB_TYPE_COCKATIEL, 'Cockatiel'),
        (WILDCARE_SPECIES_SUB_TYPE_GALAH, 'Galah - Pink and Grey'),
        (WILDCARE_SPECIES_SUB_TYPE_ROSELLA, 'Rosella'),
        (WILDCARE_SPECIES_SUB_TYPE_LITTLE, 'Little'),
        (WILDCARE_SPECIES_SUB_TYPE_WELCOME, 'Welcome'),
        (WILDCARE_SPECIES_SUB_TYPE_TAMMAR_WALLABY, 'Tammar-Wallaby'),
        (WILDCARE_SPECIES_SUB_TYPE_WESTERN_BRUSH_WALLABY, 'Western Brush Wallaby'),
        (WILDCARE_SPECIES_SUB_TYPE_WESTERN_GREY, 'Western Grey'),
        (WILDCARE_SPECIES_SUB_TYPE_BRUSHTAIL, 'Brushtail'),
        (WILDCARE_SPECIES_SUB_TYPE_PYGMY, 'Pygmy'),
        (WILDCARE_SPECIES_SUB_TYPE_RINGTAIL, 'Ringtail'),
        (WILDCARE_SPECIES_SUB_TYPE_BLUE_TONGUE_BOBTAIL, 'Blue Tongue, Bobtail'),
        (WILDCARE_SPECIES_SUB_TYPE_GOANNA, 'Goanna'),
        (WILDCARE_SPECIES_SUB_TYPE_MONITOR, 'Monitor'),
        (WILDCARE_SPECIES_SUB_TYPE_SKINK, 'Skink'),
        (WILDCARE_SPECIES_SUB_TYPE_DUGITE, 'Dugite'),
        (WILDCARE_SPECIES_SUB_TYPE_PYTHON, 'Python'),
        (WILDCARE_SPECIES_SUB_TYPE_TIGER, 'Tiger'),
        (WILDCARE_SPECIES_SUB_TYPE_LONG_NECKED_OBLANGA, 'Long-necked (oblanga)'),
        (WILDCARE_SPECIES_SUB_TYPE_MARINE, 'Marine'),
        (WILDCARE_SPECIES_SUB_TYPE_WESTERN_SWAMP, 'Western Swamp'),
    )

    wildcare_species_type=models.ForeignKey(WildcareSpeciesType, on_delete=models.CASCADE , related_name='wildcare_species_sub_types')
    species_sub_name = models.CharField(
        max_length=100,
        choices=WILDCARE_SPECIES_SUB_TYPE_CHOICES,
        unique=True,
    )

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_WildcareSpeciesSubType'
        verbose_name_plural = 'CM_WildcareSpeciesSubTypes'
        ordering = ['species_sub_name']
        #unique_together = ['species_sub_name','wildcare_species_type']

    def __str__(self):
        return self.get_species_sub_name_display()


class Referrer(models.Model):
    name = models.CharField(max_length=50, blank=True)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_Referrer'
        verbose_name_plural = 'CM_Referrers'

    def __str__(self):
        return self.name


class ReportType(models.Model):

    report_type = models.CharField(max_length=50)
    schema = JSONField(null=True)
    version = models.SmallIntegerField(default=1, blank=False, null=False)
    description = models.CharField(max_length=255, blank=True, null=True)
    replaced_by = models.ForeignKey(
        'self', on_delete=models.PROTECT, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    #advice_url = models.CharField(max_length=255, blank=True, null=True, help_text="Should start with http://")
    advice_url = models.URLField(max_length=255, blank=True, null=True)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_CallEmailReportType'
        verbose_name_plural = 'CM_CallEmailReportTypes'
        unique_together = ('report_type', 'version')

    def __str__(self):
        return '{0}, v.{1}'.format(self.report_type, self.version)

    def referred_to(self):
        if self.referrer:
            return self.referrer.name


class Location(models.Model):

    STATE_CHOICES = (
        ('WA', 'Western Australia'),
        ('VIC', 'Victoria'),
        ('QLD', 'Queensland'),
        ('NSW', 'New South Wales'),
        ('TAS', 'Tasmania'),
        ('NT', 'Northern Territory'),
        ('ACT', 'Australian Capital Territory')
    )

    wkb_geometry = models.PointField(srid=4326, blank=True, null=True)
    street = models.CharField(max_length=100, blank=True, null=True)
    town_suburb = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(
        max_length=50, choices=STATE_CHOICES, blank=True, null=True, default='WA')
    postcode = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True, default='Australia')
    objects = models.GeoManager()
    details = models.TextField(blank=True)
    ben_number = models.CharField(max_length=100, blank=True, null=True)

    @property
    def call_email_id(self):
        if self.call_location.count() > 0:
            return self.call_location.first().id;

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_Location'
        verbose_name_plural = 'CM_Locations'

    def __str__(self):
        if self.country or self.state or self.town_suburb:
            return '{}, {}, {}, {}'.format(self.street, self.town_suburb, self.state, self.country)
        else:
            return self.details


class MapLayer(models.Model):
    display_name = models.CharField(max_length=100, blank=True, null=True)
    layer_name = models.CharField(max_length=200, blank=True, null=True)  # layer name defined in geoserver (kmi.dpaw.wa.gov.au)
    availability = models.BooleanField(default=True)  # False to hide from the frontend options

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_MapLayer'
        verbose_name_plural = 'CM_MapLayers'

    def __str__(self):
        return '{0}, {1}'.format(self.display_name, self.layer_name)


class CallEmail(RevisionedMixin):
    STATUS_DRAFT = 'draft'
    STATUS_OPEN = 'open'
    STATUS_OPEN_FOLLOWUP = 'open_followup'
    STATUS_OPEN_INSPECTION = 'open_inspection'
    STATUS_OPEN_CASE = 'open_case'
    STATUS_CLOSED = 'closed'
    STATUS_PENDING_CLOSURE = 'pending_closure'
    STATUS_CHOICES = (
        (STATUS_DRAFT, 'Draft'),
        (STATUS_OPEN, 'Open'),
        (STATUS_OPEN_FOLLOWUP, 'Open (follow-up)'),
        (STATUS_OPEN_INSPECTION, 'Open (Inspection)'),
        (STATUS_OPEN_CASE, 'Open (Case)'),
        (STATUS_CLOSED, 'Closed'),
        (STATUS_PENDING_CLOSURE, 'Pending Closure'),
    )

    ENTANGLED_NO = 'no'
    ENTANGLED_FISHING_LINE = 'fishing_line'
    ENTANGLED_ROPE = 'rope'
    ENTANGLED_STRING = 'string'
    ENTANGLED_WIRE = 'wire'
    ENTANGLED_OTHER = 'other'
    ENTANGLED_CHOICES = (
        (ENTANGLED_NO, 'No'),
        (ENTANGLED_FISHING_LINE, 'Fishing Line'),
        (ENTANGLED_ROPE, 'Rope'),
        (ENTANGLED_STRING, 'String'),
        (ENTANGLED_WIRE, 'Wire'),
        (ENTANGLED_OTHER, 'Other'),
    )

    GENDER_FEMALE = 'female'
    GENDER_MALE = 'male'
    GENDER_UNKNOWN = 'unknown'
    GENDER_CHOICES = (
        (GENDER_FEMALE, 'Female'),
        (GENDER_MALE, 'Male'),
        (GENDER_UNKNOWN, 'Unknown'),
    )

    AGE_BABY = 'baby'
    AGE_ADULT = 'adult'
    AGE_JUVENILE = 'juvenile'
    AGE_CHOICES = (
        (AGE_BABY, 'Baby'),
        (AGE_ADULT, 'Adult'),
        (AGE_JUVENILE, 'Juvenile'),
    )

    BABY_KANGAROO_PINKY = 'pinky'
    BABY_KANGAROO_JOEY = 'joey'
    BABY_KANGAROO_CHOICES = (
        (BABY_KANGAROO_PINKY, 'Pinky'),
        (BABY_KANGAROO_JOEY, 'Joey'),
    )

    status = models.CharField(
        max_length=40,
        choices=STATUS_CHOICES,
        default='draft')
    location = models.ForeignKey(
        Location,
        null=True,
        related_name="call_location"
    )
    classification = models.ForeignKey(
        Classification,
        null=True,
        related_name="call_classification"
    )
    call_type = models.ForeignKey(
        CallType,
        null=True,
        blank=True,
        related_name="call_type"
    )
    wildcare_species_type = models.ForeignKey(
        WildcareSpeciesType,
        null=True,
        blank=True,
        related_name="wildcare_species_type"
    )
    wildcare_species_sub_type = models.ForeignKey(
        WildcareSpeciesSubType,
        null=True,
        blank=True,
        related_name="wildcare_species_sub_type"
    )
    species_name = models.CharField(max_length=50, blank=True, null=True)
    dead = models.NullBooleanField()
    euthanise = models.NullBooleanField()
    number_of_animals = models.CharField(max_length=100, blank=True, null=True)
    brief_nature_of_call = models.TextField(blank=True)
    entangled = MultiSelectField(max_length=40, choices=ENTANGLED_CHOICES, blank=True, null=True)
    entangled_other = models.CharField(max_length=100, blank=True, null=True)
    gender = MultiSelectField(max_length=30, choices=GENDER_CHOICES, blank=True, null=True)
    baby_kangaroo = MultiSelectField(max_length=30, choices=BABY_KANGAROO_CHOICES, blank=True, null=True)
    age = MultiSelectField(max_length=30, choices=AGE_CHOICES, blank=True, null=True)
    lodged_on = models.DateField(auto_now_add=True)
    number = models.CharField(max_length=50, blank=True, null=True)
    caller = models.CharField(max_length=100, blank=True, null=True)
    caller_phone_number = models.CharField(max_length=50, blank=True, null=True)
    assigned_to = models.ForeignKey(
        EmailUser, 
        related_name='callemail_assigned_to',
        null=True
    )
    volunteer = models.ForeignKey(
        EmailUser, 
        related_name='callemail_volunteer',
        null=True
    )
    anonymous_call = models.BooleanField(default=False)
    caller_wishes_to_remain_anonymous = models.BooleanField(default=False)
    occurrence_from_to = models.BooleanField(default=False)
    occurrence_date_from = models.DateField(null=True)
    occurrence_time_from = models.CharField(max_length=20, blank=True, null=True)
    occurrence_time_start = models.TimeField(blank=True, null=True)
    occurrence_date_to = models.DateField(null=True)
    occurrence_time_to = models.CharField(max_length=20, blank=True, null=True)
    occurrence_time_end = models.TimeField(blank=True, null=True)
    date_of_call = models.DateField(null=True)
    time_of_call = models.TimeField(blank=True, null=True)
    report_type = models.ForeignKey(
        ReportType,
        null=True,
        related_name='call_schema',
    )
    referrer = models.ManyToManyField(
        Referrer,
        blank=True,
        # related_name="report_referrer"
    )
    email_user = models.ForeignKey(
        EmailUser,
        null=True,
    )
    advice_given = models.BooleanField(default=False)
    advice_details = models.TextField(blank=True, null=True)
    region = models.ForeignKey(
        RegionDistrict, 
        related_name='callemail_region', 
        null=True
    )
    district = models.ForeignKey(
        RegionDistrict, 
        related_name='callemail_district', 
        null=True
    )
    allocated_group = models.ForeignKey(
        CompliancePermissionGroup,
        related_name='callemail_allocated_group', 
        null=True
    )
    
    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_Call/Email'
        verbose_name_plural = 'CM_Calls/Emails'

    def __str__(self):
        return 'ID: {0}, Status: {1}, Number: {2}, Caller: {3}, Assigned To: {4}' \
            .format(self.id, self.status, self.number, self.caller, self.assigned_to)
    
    # Prefix "C" char to CallEmail number.
    def save(self, *args, **kwargs):
        
        super(CallEmail, self).save(*args,**kwargs)
        if self.number is None:
            new_number_id = 'C{0:06d}'.format(self.pk)
            self.number = new_number_id
            self.save()
        
    @property
    def data(self):
        """ returns a queryset of form data records attached to CallEmail (shortcut to ComplianceFormDataRecord related_name). """
        return self.form_data_records.all()

    @property
    def schema(self):
        
        if self.report_type:
            return self.report_type.schema
    
    #def log_user_action(self, action, request):
     #   return CallEmailUserAction.log_action(self, action, request.user)
    def log_user_action(self, action, request=None):
        if request:
            return CallEmailUserAction.log_action(self, action, request.user)
        else:
            return CallEmailUserAction.log_action(self, action)

    @property
    def get_related_items_identifier(self):
        return self.number

    @property
    def get_related_items_descriptor(self):
        #return '{0}, {1}'.format(self.status, self.caller)
        return self.caller
    # @property
    # def related_items(self):
    #     return get_related_items(self)

    def forward_to_regions(self, request):
        self.status = self.STATUS_OPEN
        self.log_user_action(
            CallEmailUserAction.ACTION_FORWARD_TO_REGIONS.format(self.number), 
            request)
        self.save()

    def forward_to_wildlife_protection_branch(self, request):
        self.status = self.STATUS_OPEN
        self.log_user_action(
            CallEmailUserAction.ACTION_FORWARD_TO_WILDLIFE_PROTECTION_BRANCH.format(self.number), 
            request)
        self.save()

    def allocate_for_follow_up(self, request):
        self.status = self.STATUS_OPEN_FOLLOWUP
        self.log_user_action(
                CallEmailUserAction.ACTION_ALLOCATE_FOR_FOLLOWUP.format(self.number), 
                request)
        self.save()

    def allocate_for_inspection(self, request):
        self.status = self.STATUS_OPEN_INSPECTION
        self.log_user_action(
                CallEmailUserAction.ACTION_ALLOCATE_FOR_INSPECTION.format(self.number), 
                request)
        self.save()

    def allocate_for_case(self, request):
        self.status = self.STATUS_OPEN_CASE
        self.log_user_action(
                CallEmailUserAction.ACTION_ALLOCATE_FOR_CASE.format(self.number),
                request)
        self.save()

    def close(self, request=None):
        close_record, parents = can_close_record(self, request)
        if close_record:
            self.status = self.STATUS_CLOSED
            self.log_user_action(
                    CallEmailUserAction.ACTION_CLOSE.format(self.number), 
                    request)
        else:
            self.status = self.STATUS_PENDING_CLOSURE
            self.log_user_action(
                    CallEmailUserAction.ACTION_PENDING_CLOSURE.format(self.number), 
                    request)
        self.save()
        # Call Email has no parents in pending_closure status

    def add_offence(self, request):
        self.log_user_action(
                CallEmailUserAction.ACTION_OFFENCE.format(self.number), 
                request)
        self.save()

    def add_sanction_outcome(self, request):
        self.log_user_action(
                CallEmailUserAction.ACTION_SANCTION_OUTCOME.format(self.number), 
                request)
        self.save()

    def add_referrers(self, request):
        referrers_selected = request.data.get('referrers_selected').split(",")
        for selection in referrers_selected:
            print(selection)
            try:
                selection_int = int(selection)
            except Exception as e:
                raise e
            referrer = Referrer.objects.get(id=selection_int)
            if referrer:
                self.referrer.add(referrer)
        self.save()

@python_2_unicode_compatible
class ComplianceFormDataRecord(models.Model):

    INSTANCE_ID_SEPARATOR = "__instance-"

    ACTION_TYPE_ASSIGN_VALUE = 'value'
    ACTION_TYPE_ASSIGN_COMMENT = 'comment'

    COMPONENT_TYPE_TEXT = 'text'
    COMPONENT_TYPE_TAB = 'tab'
    COMPONENT_TYPE_SECTION = 'section'
    COMPONENT_TYPE_GROUP = 'group'
    COMPONENT_TYPE_NUMBER = 'number'
    COMPONENT_TYPE_EMAIL = 'email'
    COMPONENT_TYPE_SELECT = 'select'
    COMPONENT_TYPE_MULTI_SELECT = 'multi-select'
    COMPONENT_TYPE_TEXT_AREA = 'text_area'
    COMPONENT_TYPE_TABLE = 'table'
    COMPONENT_TYPE_EXPANDER_TABLE = 'expander_table'
    COMPONENT_TYPE_LABEL = 'label'
    COMPONENT_TYPE_RADIO = 'radiobuttons'
    COMPONENT_TYPE_CHECKBOX = 'checkbox'
    COMPONENT_TYPE_DECLARATION = 'declaration'
    COMPONENT_TYPE_FILE = 'file'
    COMPONENT_TYPE_DATE = 'date'
    COMPONENT_TYPE_CHOICES = (
        (COMPONENT_TYPE_TEXT, 'Text'),
        (COMPONENT_TYPE_TAB, 'Tab'),
        (COMPONENT_TYPE_SECTION, 'Section'),
        (COMPONENT_TYPE_GROUP, 'Group'),
        (COMPONENT_TYPE_NUMBER, 'Number'),
        (COMPONENT_TYPE_EMAIL, 'Email'),
        (COMPONENT_TYPE_SELECT, 'Select'),
        (COMPONENT_TYPE_MULTI_SELECT, 'Multi-Select'),
        (COMPONENT_TYPE_TEXT_AREA, 'Text Area'),
        (COMPONENT_TYPE_TABLE, 'Table'),
        (COMPONENT_TYPE_EXPANDER_TABLE, 'Expander Table'),
        (COMPONENT_TYPE_LABEL, 'Label'),
        (COMPONENT_TYPE_RADIO, 'Radio'),
        (COMPONENT_TYPE_CHECKBOX, 'Checkbox'),
        (COMPONENT_TYPE_DECLARATION, 'Declaration'),
        (COMPONENT_TYPE_FILE, 'File'),
        (COMPONENT_TYPE_DATE, 'Date'),
    )

    call_email = models.ForeignKey(CallEmail, related_name='form_data_records')
    field_name = models.CharField(max_length=512, blank=True, null=True)
    schema_name = models.CharField(max_length=256, blank=True, null=True)
    instance_name = models.CharField(max_length=256, blank=True, null=True)
    component_type = models.CharField(
        max_length=64,
        choices=COMPONENT_TYPE_CHOICES,
        default=COMPONENT_TYPE_TEXT)
    value = JSONField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    deficiency = models.TextField(blank=True, null=True)

    def __str__(self):
        return "CallEmail {id} record {field}: {value}".format(
            id=self.call_email_id,
            field=self.field_name,
            value=self.value[:8]
        )

    class Meta:
        app_label = 'wildlifecompliance'
        unique_together = ('call_email', 'field_name',)

    @staticmethod
    def process_form(request, CallEmail, form_data, action=ACTION_TYPE_ASSIGN_VALUE):
        can_edit_comments = request.user.has_perm(
            'wildlifecompliance.licensing_officer'
        ) or request.user.has_perm(
            'wildlifecompliance.assessor'
        )
        can_edit_deficiencies = request.user.has_perm(
            'wildlifecompliance.licensing_officer'
        )

        if action == ComplianceFormDataRecord.ACTION_TYPE_ASSIGN_COMMENT and\
                not can_edit_comments and not can_edit_deficiencies:
            raise Exception(
                'You are not authorised to perform this action!')
        
        for field_name, field_data in form_data.items():
            schema_name = field_data.get('schema_name', '')
            component_type = field_data.get('component_type', '')
            value = field_data.get('value', '')
            comment = field_data.get('comment_value', '')
            deficiency = field_data.get('deficiency_value', '')
            instance_name = ''

            if ComplianceFormDataRecord.INSTANCE_ID_SEPARATOR in field_name:
                [parsed_schema_name, instance_name] = field_name.split(
                    ComplianceFormDataRecord.INSTANCE_ID_SEPARATOR
                )
                schema_name = schema_name if schema_name else parsed_schema_name

            form_data_record, created = ComplianceFormDataRecord.objects.get_or_create(
                call_email_id=CallEmail.id,
                field_name=field_name
            )
            if created:
                form_data_record.schema_name = schema_name
                form_data_record.instance_name = instance_name
                form_data_record.component_type = component_type
            if action == ComplianceFormDataRecord.ACTION_TYPE_ASSIGN_VALUE:
                form_data_record.value = value
            elif action == ComplianceFormDataRecord.ACTION_TYPE_ASSIGN_COMMENT:
                if can_edit_comments:
                    form_data_record.comment = comment
                if can_edit_deficiencies:
                    form_data_record.deficiency = deficiency
            form_data_record.save()


class CallEmailDocument(Document):
    call_email = models.ForeignKey('CallEmail', related_name='documents')
    #_file = models.FileField(max_length=255, upload_to=update_call_email_doc_filename)
    _file = models.FileField(max_length=255)
    input_name = models.CharField(max_length=255, blank=True, null=True)
    # after initial submit prevent document from being deleted
    can_delete = models.BooleanField(default=True)
    version_comment = models.CharField(max_length=255, blank=True, null=True)

    def delete(self):
        if self.can_delete:
            return super(CallEmailDocument, self).delete()
        logger.info(
            'Cannot delete existing document object after application has been submitted (including document submitted before\
            application pushback to status Draft): {}'.format(
                self.name)
        )

    class Meta:
        app_label = 'wildlifecompliance'


class CallEmailLogDocument(Document):
    #name = models.CharField(max_length=100, blank=True,
     #       verbose_name='name', help_text='')
    log_entry = models.ForeignKey(
        'CallEmailLogEntry',
        related_name='documents')
    #input_name = models.CharField(max_length=255, blank=True, null=True)
    #version_comment = models.CharField(max_length=255, blank=True, null=True)
    #_file = models.FileField(max_length=255, upload_to=update_call_email_comms_log_filename)
    _file = models.FileField(max_length=255)

    class Meta:
        app_label = 'wildlifecompliance'


class CallEmailLogEntry(CommunicationsLogEntry):
    call_email = models.ForeignKey(CallEmail, related_name='comms_logs')

    class Meta:
        app_label = 'wildlifecompliance'


class CallEmailUserAction(models.Model):
    ACTION_CREATE_CALL_EMAIL = "Create Call/Email {}"
    ACTION_SAVE_CALL_EMAIL_ = "Save Call/Email {}"
    ACTION_FORWARD_TO_REGIONS = "Forward Call/Email {} to regions"
    ACTION_FORWARD_TO_WILDLIFE_PROTECTION_BRANCH = "Forward Call/Email {} to Wildlife Protection Branch"
    ACTION_ALLOCATE_FOR_FOLLOWUP = "Allocate Call/Email {} for follow up"
    ACTION_ALLOCATE_FOR_INSPECTION = "Allocate Call/Email {} for inspection"
    ACTION_ALLOCATE_FOR_LEGAL_CASE = "Allocate Call/Email {} for case"
    ACTION_CLOSE = "Close Call/Email {}"
    ACTION_PENDING_CLOSURE = "Mark Call/Email {} as pending closure"
    ACTION_OFFENCE = "Create linked offence for Call/Email {}"
    ACTION_SANCTION_OUTCOME = "Create Sanction Outcome for Call/Email {}"
    ACTION_PERSON_SEARCH = "Linked person to Call/Email {}"
    # ACTION_ADD_WEAK_LINK = "Create manual link between Call/Email: {} and {}: {}"
    # ACTION_REMOVE_WEAK_LINK = "Remove manual link between Call/Email: {} and {}: {}"
    ACTION_ADD_WEAK_LINK = "Create manual link between {}: {} and {}: {}"
    ACTION_REMOVE_WEAK_LINK = "Remove manual link between {}: {} and {}: {}"

    who = models.ForeignKey(EmailUser, null=True, blank=True)
    when = models.DateTimeField(null=False, blank=False, auto_now_add=True)
    what = models.TextField(blank=False)

    class Meta:
        app_label = 'wildlifecompliance'
        ordering = ('-when',)

    @classmethod
    def log_action(cls, call_email, action, user=None):
        return cls.objects.create(
            call_email=call_email,
            who=user,
            what=str(action)
        )

    call_email = models.ForeignKey(CallEmail, related_name='action_logs')


import reversion
reversion.register(Classification, follow=['call_classification'])
reversion.register(CallType, follow=['wildcare_species_types', 'call_type'])
reversion.register(WildcareSpeciesType, follow=['wildcare_species_sub_types', 'wildcare_species_type'])
reversion.register(WildcareSpeciesSubType, follow=['wildcare_species_sub_type'])
reversion.register(Referrer, follow=['callemail_set'])
reversion.register(ReportType, follow=['reporttype_set', 'call_schema'])
reversion.register(Location, follow=['inspection_location', 'offence_location'])
reversion.register(MapLayer, follow=[])
#reversion.register(CallEmail_referrer, follow=[])
reversion.register(CallEmail, follow=['location', 'form_data_records', 'documents', 'comms_logs', 'action_logs', 'legal_case_call_email', 'inspection_call_email', 'offence_call_eamil'])
reversion.register(ComplianceFormDataRecord, follow=[])
reversion.register(CallEmailDocument, follow=[])
reversion.register(CallEmailLogDocument, follow=[])
reversion.register(CallEmailLogEntry, follow=['documents'])
reversion.register(CallEmailUserAction, follow=[])

