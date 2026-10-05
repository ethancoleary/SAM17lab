from os import environ

SESSION_CONFIGS = [
    dict(
        name='econ_psych_lab',
        display_name='Economics and Psychology Lab',
        num_demo_participants=4,
        app_sequence=[
            'intro',
            'pb',
            'honesty',
            'public_goods',
            'task',
            'la',
            'spectator',
            'competition',
            'final_survey'

        ],
        group_size=45,  # default value shown in the admin form
    ),
]

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=0.0,
    participation_fee=0.00,
    doc="",
)

PARTICIPANT_FIELDS = [
    'spectator_final_a',
    'spectator_final_b',
    'spectator_gini',
    'spectator_intervention',
    'pg_contribution',
    'pg_payoff',
    'task_score',
    'pb_stress',
    'spec_treatment',
    'comp_treatment',
    'pgg_treatment',
    'honesty_treatment',
    'top_score_in_session',
    'guessed_score',

]
SESSION_FIELDS = []

LANGUAGE_CODE = 'en'
REAL_WORLD_CURRENCY_CODE = 'NOK'
USE_POINTS = True

ROOMS = []

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """"""

SECRET_KEY = 'nhh-econ-psych-lab-2026-change-me'

INSTALLED_APPS = ['otree']
