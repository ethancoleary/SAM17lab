from otree.api import *
import secrets


doc = """
Final Survey app.

Collects individual-level background/psychometric measures:

1. Financial pressure: five self-reported items, each rated on a common
   5-point agreement scale ("This statement describes me: Completely /
   Very well / Somewhat / Very little / Not at all"), shown together on
   one page.
2. Parental education: highest level of education completed by either
   parent/guardian (categorical).
3. Risk aversion: a single self-reported general risk-taking item,
   using the widely used Dohmen et al. (2011) 0-10 scale ("How willing
   are you to take risks, in general?").

At the end, participants are redirected (after 3 seconds) to a separate
Qualtrics form to leave their email address for payment. A random,
single-use token is generated and passed via the URL so that Qualtrics
submissions can be matched to a payment record WITHOUT linking the email
to the participant's actual survey answers stored here. Keep the
token-to-participant mapping (logged separately, e.g. in a private file
you control) isolated from both this app's data export and the Qualtrics
export, and delete it once payments are reconciled.
"""


class C(BaseConstants):
    NAME_IN_URL = 'final_survey'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    FINANCIAL_PRESSURE_MIN = 1
    FINANCIAL_PRESSURE_MAX = 5

    RISK_SCALE_MIN = 0
    RISK_SCALE_MAX = 10
    RISK_SCALE_CHOICES = list(range(RISK_SCALE_MIN, RISK_SCALE_MAX + 1))

    AGREEMENT_CHOICES = [
        [5, 'Completely'],
        [4, 'Very well'],
        [3, 'Somewhat'],
        [2, 'Very little'],
        [1, 'Not at all'],
    ]

    FINANCIAL_ITEMS = [
        ('financial_pressure', 'I feel stressed about my personal finances right now'),
        ('unexpected_cost', 'I could handle a major unexpected expense'),
        ('parents', 'I rely entirely on my parents for day to day financing'),
        ('prices', 'Prices are not something that I typically consider when making everday purchases.'),
        ('worry', 'I am worried that I am going to run out of money before my next income transfer'),
    ]

    PARENTAL_EDUCATION_LABEL = (
        "What is the highest level of education completed by either of your parents or guardians?"
    )
    PARENTAL_EDUCATION_CHOICES = [
        ['primary', 'Primary / lower secondary school'],
        ['upper_secondary', 'Upper secondary school (e.g. high school)'],
        ['vocational', 'Vocational or professional training'],
        ['bachelor', "Bachelor's degree"],
        ['master_or_higher', "Master's degree or higher"],
        ['not_sure', 'Not sure'],
        ['prefer_not_to_say', 'Prefer not to say'],
    ]

    QUALTRICS_EMAIL_FORM_URL = 'https://nhh.eu.qualtrics.com/jfe/form/SV_80QXQHz6NMkt8ge'


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    financial_pressure = models.IntegerField(
        label="How much financial stress do you feel that you are under right now?",
        choices=C.AGREEMENT_CHOICES,
        widget=widgets.RadioSelect,
    )

    unexpected_cost = models.IntegerField(
        label="I could handle a major unexpected expense",
        choices=C.AGREEMENT_CHOICES,
        widget=widgets.RadioSelect,
    )

    parents = models.IntegerField(
        label="I rely entirely on my parents for day to day financing",
        choices=C.AGREEMENT_CHOICES,
        widget=widgets.RadioSelect,
    )

    prices = models.IntegerField(
        label="Prices are not something that I typically consider when making everday purchases.",
        choices=C.AGREEMENT_CHOICES,
        widget=widgets.RadioSelect,
    )

    worry = models.IntegerField(
        label="I am worried that I am going to run out of money before my next income transfer",
        choices=C.AGREEMENT_CHOICES,
        widget=widgets.RadioSelect,
    )

    parental_education = models.StringField(
        label=C.PARENTAL_EDUCATION_LABEL,
        choices=C.PARENTAL_EDUCATION_CHOICES,
        widget=widgets.RadioSelect,
    )

    risk_aversion = models.IntegerField(
        label="How willing are you to take risks, in general?",
        choices=C.RISK_SCALE_CHOICES,
        widget=widgets.RadioSelectHorizontal,
    )


# ---------------------------------------------------------------------------
# PAGES
# ---------------------------------------------------------------------------

class TitlePage(Page):
    pass


class FinancialPressure(Page):
    form_model = 'player'
    form_fields = [name for name, _ in C.FINANCIAL_ITEMS]

    @staticmethod
    def vars_for_template(player: Player):
        items = [
            dict(name=name, label=label, choices=C.AGREEMENT_CHOICES)
            for name, label in C.FINANCIAL_ITEMS
        ]
        return dict(items=items)

    @staticmethod
    def error_message(player: Player, values):
        for name, _ in C.FINANCIAL_ITEMS:
            if not values.get(name):
                return 'Please answer all questions before continuing.'


class ParentalEducation(Page):
    form_model = 'player'
    form_fields = ['parental_education']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            education_label=C.PARENTAL_EDUCATION_LABEL,
            education_choices=C.PARENTAL_EDUCATION_CHOICES,
        )

    @staticmethod
    def error_message(player: Player, values):
        if not values.get('parental_education'):
            return 'Please select an option before continuing.'


class RiskAversion(Page):
    form_model = 'player'
    form_fields = ['risk_aversion']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            scale_min=C.RISK_SCALE_MIN,
            scale_max=C.RISK_SCALE_MAX,
            scale_values=C.RISK_SCALE_CHOICES,
        )

    @staticmethod
    def error_message(player: Player, values):
        if values.get('risk_aversion') is None:
            return 'Please select a value before continuing.'


class Debrief(Page):
    @staticmethod
    def vars_for_template(player: Player):
        # Generate a random, single-use token that is NOT derived from
        # participant.code, so the Qualtrics email form cannot be used to
        # reverse-engineer this participant's identity within this app.
        # This token is stored in participant.vars purely so it appears in
        # this app's own data export (so you can independently log the
        # token <-> participant.code mapping in a SEPARATE, private file
        # if you need to reconcile payments -- never merge that mapping
        # back into the survey-answers export).
        token = secrets.token_urlsafe(9)  # ~12 url-safe characters
        player.participant.vars['email_token'] = token
        redirect_url = f'{C.QUALTRICS_EMAIL_FORM_URL}?token={token}'
        return dict(email_token=token, redirect_url=redirect_url)


page_sequence = [TitlePage, FinancialPressure, ParentalEducation, RiskAversion, Debrief]