import random

from otree.api import *



class C(BaseConstants):
    NAME_IN_URL = 'intro'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    password = models.StringField()
    group_number = models.IntegerField(
        choices=[1, 2, 3, 4, 5, 6],
        label='What is your group number?',
    )

    age = models.IntegerField(
        min=15,
        max=100,
    )

    nationality = models.IntegerField(
        choices=[
            [1, 'Norwegian'],
            [2, 'Other Nordic'],
            [3, 'Other EU/EEA'],
            [4, 'Non-EU/EEA'],
        ],
        widget=widgets.RadioSelect,
    )

    exchange = models.IntegerField(
        choices=[[1, 'Yes'], [0, 'No']],
        widget=widgets.RadioSelect,
    )

    gender = models.IntegerField(
        choices=[
            [1, 'Male'],
            [2, 'Female'],
            [3, 'Other'],
            [4, 'Prefer not to say'],
        ],

        widget=widgets.RadioSelect,
    )
    pb_stress = models.IntegerField()
    spec_treatment = models.IntegerField()
    comp_treatment = models.IntegerField()
    pgg_treatment = models.IntegerField()
    honesty_treatment = models.IntegerField()

class Password(Page):
    form_model = 'player'
    form_fields = ['password']

    @staticmethod
    def error_message(player, values):
        if values['password'].strip() != '0510':
            return 'Incorrect password. Please try again.'

class Welcome(Page):

    @staticmethod
    def before_next_page(player, timeout_happened):
        player.pb_stress =  random.randint(0, 1)
        player.participant.vars['pb_stress'] = player.pb_stress

        player.spec_treatment = random.randint(1, 3)  # 1 is merit, 2 is luck and 3 is don't know.
        player.participant.vars['spec_treatment'] = player.spec_treatment

        player.comp_treatment = random.randint(0, 1) #0 is baseline and 1 is additional info
        player.participant.vars['comp_treatment'] = player.comp_treatment

        player.pgg_treatment = random.randint(0, 1) #0 is contribute, 1 is give up
        player.participant.vars['pgg_treatment'] = player.pgg_treatment

        player.honesty_treatment = random.randint(0, 1)  # 0 is self, 1 is charity
        player.participant.vars['honesty_treatment'] = player.honesty_treatment



class GroupNumber(Page):
    form_model = 'player'
    form_fields = ['group_number']


class P_Details(Page):
    form_model = 'player'
    form_fields = [
        'age',
        'nationality',
        'exchange',
        'gender',
    ]


page_sequence = [Password,
                Welcome,
                 GroupNumber,
                P_Details
                ]