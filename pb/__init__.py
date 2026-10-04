from otree.api import *
import random


class C(BaseConstants):
    NAME_IN_URL = 'present_bias'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    SOONER_AMOUNT = 250
    MULTIPLIER = 1.2       # m: multiplier on the later payment
    WEEKS_LAG = 4          # w: gap between the two payment dates in each question
    FRONT_END_DELAY = 24   # d: delay before the "sooner" payment in Q2

    LATER_AMOUNT = round(SOONER_AMOUNT * MULTIPLIER)  # 250m
    STRESS_TIMEOUT_SECONDS = 8


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    choice_now = models.StringField(
        choices=[
            ['A', 'Option A: receive {} NOK today'.format(C.SOONER_AMOUNT)],
            ['B', 'Option B: receive {} NOK in {} weeks'.format(C.LATER_AMOUNT, C.WEEKS_LAG)],
        ],
        widget=widgets.RadioSelect,
        label='',
        blank=True,
    )

    choice_future = models.StringField(
        choices=[
            ['A', 'Option A: receive {} NOK in {} weeks'.format(C.SOONER_AMOUNT, C.FRONT_END_DELAY)],
            ['B', 'Option B: receive {} NOK in {} weeks'.format(
                C.LATER_AMOUNT, C.FRONT_END_DELAY + C.WEEKS_LAG)],
        ],
        widget=widgets.RadioSelect,
        label='',
        blank=True,
    )
    stress = models.IntegerField()

    present_biased = models.BooleanField()

    # True if this player's choice on this page was assigned randomly
    # because time ran out (or the page was submitted with no selection),
    # False if the participant actively picked an option and submitted
    # manually.
    choice_now_forced = models.BooleanField(initial=False)
    choice_future_forced = models.BooleanField(initial=False)


def is_stressed(player: Player):
    """
    IMPORTANT: the stress treatment is assigned in an earlier app via
    participant.vars['pb_stress'] (a plain attribute assignment like
    participant.pb_stress = 1 does NOT persist across page loads/requests
    in oTree -- only participant.vars is saved to the database and
    reloaded on every request). Read it the same way it is written.
    """
    return player.participant.vars.get('pb_stress') == 1


def get_stress_timeout(player: Player):
    """Returns the timeout in seconds for this player on a timed page, or
    None if the stress treatment does not apply to them (no timer at all)."""
    return C.STRESS_TIMEOUT_SECONDS if is_stressed(player) else None


class TitlePage(Page):
    pass


# PAGES
class Instructions(Page):
    @staticmethod
    def vars_for_template(player: Player):
        player.stress = player.participant.vars.get('pb_stress')
        return dict(
            sooner_amount=C.SOONER_AMOUNT,
            later_amount=C.LATER_AMOUNT,
        )


class Q1Now(Page):
    form_model = 'player'
    form_fields = ['choice_now']

    @staticmethod
    def get_timeout_seconds(player: Player):
        return get_stress_timeout(player)

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            sooner_amount=C.SOONER_AMOUNT,
            later_amount=C.LATER_AMOUNT,
            weeks_lag=C.WEEKS_LAG,
            is_stressed=is_stressed(player),
            stress_timeout=C.STRESS_TIMEOUT_SECONDS,
        )

    @staticmethod
    def error_message(player: Player, values):
        # Non-stressed participants have unlimited time and MUST pick an
        # option -- reject a blank submission from them.
        # Stressed participants may legitimately submit blank (their
        # countdown ran out), so a blank submission from them must be
        # ALLOWED THROUGH -- before_next_page below fills in a random
        # choice for them. Do not reject it here.
        if not is_stressed(player) and not values.get('choice_now'):
            return 'Please select an option before continuing.'

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if player.field_maybe_none('choice_now') is None:
            player.choice_now = random.choice(['A', 'B'])
            player.choice_now_forced = True
        else:
            player.choice_now_forced = False

class NextQuestion(Page):
    pass

class Q2Future(Page):
    form_model = 'player'
    form_fields = ['choice_future']

    @staticmethod
    def get_timeout_seconds(player: Player):
        return get_stress_timeout(player)

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            sooner_amount=C.SOONER_AMOUNT,
            later_amount=C.LATER_AMOUNT,
            weeks_lag=C.WEEKS_LAG,
            front_end_delay=C.FRONT_END_DELAY,
            later_date=C.FRONT_END_DELAY + C.WEEKS_LAG,
            is_stressed=is_stressed(player),
            stress_timeout=C.STRESS_TIMEOUT_SECONDS,
        )

    @staticmethod
    def error_message(player: Player, values):
        if not is_stressed(player) and not values.get('choice_future'):
            return 'Please select an option before continuing.'

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if player.field_maybe_none('choice_future') is None:
            player.choice_future = random.choice(['A', 'B'])
            player.choice_future_forced = True
        else:
            player.choice_future_forced = False

        # Present bias: impatient (sooner) when immediate, but patient (later) once both are delayed
        player.present_biased = (
            player.choice_now == 'A' and player.choice_future == 'B'
        )
        participant = player.participant
        participant.vars['pb_choice_now'] = player.choice_now
        participant.vars['pb_choice_future'] = player.choice_future
        participant.vars['pb_present_biased'] = player.present_biased
        participant.vars['pb_choice_now_forced'] = player.choice_now_forced
        participant.vars['pb_choice_future_forced'] = player.choice_future_forced


page_sequence = [TitlePage, Instructions, Q1Now, NextQuestion, Q2Future]