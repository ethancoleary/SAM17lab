from otree.api import *
import random


doc = """
Loss Aversion (LA) Survey app -- LOSS framing only.

Participants first complete a 1-minute task elsewhere in the session
(the score x_i is read from participant.vars['task_score'], but is
never shown to the participant directly). The full pot at stake is
G = SCORE_MULTIPLIER * x_i (in NOK).

Let:
    G = the full pot (SCORE_MULTIPLIER * score)
    s = SAFE_SHORTFALL_RATE * G   (a small, certain shortfall from G)
    L = BIG_SHORTFALL_RATE * G    (a larger, uncertain shortfall from G)
    p = BIG_SHORTFALL_PROB         (probability of the larger shortfall)

Provisional payment shown = G.
    Option A (safe):  a certain tax of s      -> final payment G - s
    Option B (risky): (1-p) chance of a tax of 0   -> final payment G
                       p chance of a tax of L       -> final payment G - L

Stress treatment: this app's own 'stress' condition is the OPPOSITE of
whatever the participant got in the present_bias app. If
participant.vars['pb_stress'] == 1 (they were stressed there), they get
the relaxed condition here (no timer). If pb_stress == 0 (or unset),
they get the stressed condition here (a short countdown on the Choice
page, after which a random choice is submitted automatically).

After the Choice page, participants see a SnakeWait page: framed as a
mandatory wait for other participants to catch up, with a playable
Snake game to occupy the time. It auto-advances to the next page after
SNAKE_WAIT_SECONDS via oTree's built-in timeout_seconds mechanism.

Choice2 is a second, independent decision (same option structure, its
own model field 'choice2') asked after the wait page.
"""


class C(BaseConstants):
    NAME_IN_URL = 'loss_aversion'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    # Task score fallback if no prior task app has run (e.g. for testing)
    FALLBACK_TASK_SCORE = 40

    # Full pot G = SCORE_MULTIPLIER * score, in NOK
    SCORE_MULTIPLIER = 20

    SAFE_SHORTFALL_RATE = 0.05   # s = 5% of G  (Option A's certain shortfall)
    BIG_SHORTFALL_RATE = 0.25    # L = 25% of G (Option B's possible shortfall)
    BIG_SHORTFALL_PROB = 0.20    # p = 20% chance of the big shortfall in Option B

    STRESS_TIMEOUT_SECONDS = 7

    SNAKE_WAIT_SECONDS = 60


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):

    task_score = models.IntegerField()

    choice = models.StringField(
        choices=[['A', 'Option A (safe)'], ['B', 'Option B (risky)']],
        label="Which option do you choose?",
        widget=widgets.RadioSelect,
        blank=True,
    )

    choice2 = models.StringField(
        choices=[['A', 'Option A (safe)'], ['B', 'Option B (risky)']],
        label="Which option do you choose?",
        widget=widgets.RadioSelect,
        blank=True,
    )
    loss_first = models.IntegerField()

    # Realized risky-option outcome, only relevant if choice == 'B'
    risky_draw_big_shortfall = models.BooleanField(initial=False)

    reference_payment = models.FloatField()   # the anchor shown on screen (G)
    bonus_or_tax_amount = models.FloatField()  # signed adjustment relative to the anchor
    final_payment = models.FloatField()        # always equals G-s, G, or G-L

    confident_in_choice = models.IntegerField(
        label="How confident are you in this choice?",
        choices=[[1, 'Not at all confident'], [2, 'Slightly confident'],
                 [3, 'Moderately confident'], [4, 'Very confident'],
                 [5, 'Extremely confident']],
        widget=widgets.RadioSelectHorizontal,
    )

    # True if choice was assigned randomly because the countdown ran out,
    # False if the participant actively picked and submitted it.
    choice_forced = models.BooleanField(initial=False)

    # Same, but for choice2.
    choice2_forced = models.BooleanField(initial=False)


def get_task_score(player: Player):
    stored = player.participant.vars.get('task_score')
    if stored is None:
        stored = C.FALLBACK_TASK_SCORE
        player.participant.vars['task_score'] = stored
    return stored


def get_pot(player: Player):
    """The full pot G, in NOK, based on the (hidden) task score."""
    return C.SCORE_MULTIPLIER * get_task_score(player)


def is_stressed(player: Player):
    """
    This app's stress condition is the OPPOSITE of whatever the
    participant got in present_bias. pb_stress is read from
    participant.vars (the only mechanism that actually persists across
    page loads/requests in oTree -- a plain attribute assignment like
    participant.pb_stress = 1 does NOT persist).

    pb_stress == 1  -> stressed there  -> NOT stressed here (False)
    pb_stress == 0  -> not stressed there -> stressed here (True)
    pb_stress unset -> treated as 0 -> stressed here (True)
    """
    pb_stress = player.participant.vars.get('pb_stress', 0)
    return pb_stress != 1


def get_la_timeout(player: Player):
    """Returns the timeout in seconds for this player on the Choice page,
    or None if the stress treatment does not apply to them (no timer)."""
    return C.STRESS_TIMEOUT_SECONDS if is_stressed(player) else None


def compute_outcome(player: Player):
    x_i = get_task_score(player)
    player.task_score = x_i

    G = get_pot(player)
    s = C.SAFE_SHORTFALL_RATE * G
    L = C.BIG_SHORTFALL_RATE * G
    p = C.BIG_SHORTFALL_PROB

    reference = G  # high anchor shown as "provisional payment"
    if player.choice == 'A':
        tax = s
        final = reference - tax
    else:
        draw_big = random.random() < p
        player.risky_draw_big_shortfall = draw_big
        tax = L if draw_big else 0.0
        final = reference - tax
    player.reference_payment = reference
    player.bonus_or_tax_amount = -tax
    player.final_payment = final


# ---------------------------------------------------------------------------
# PAGES
# ---------------------------------------------------------------------------

class TitlePage(Page):
    pass


class Instructions(Page):

    @staticmethod
    def before_next_page(player, timeout_happened):
        player.loss_first = random.randint(0,1)


class Choice(Page):
    form_model = 'player'
    form_fields = ['choice']

    @staticmethod
    def is_displayed(player):
        return player.loss_first == 1

    @staticmethod
    def get_timeout_seconds(player: Player):
        return get_la_timeout(player)

    @staticmethod
    def vars_for_template(player: Player):
        G = get_pot(player)
        s = C.SAFE_SHORTFALL_RATE * G
        L = C.BIG_SHORTFALL_RATE * G
        p_pct = int(C.BIG_SHORTFALL_PROB * 100)
        q_pct = 100 - p_pct

        reference = round(G, 2)
        option_a_amount = round(s, 2)      # certain tax
        option_b_high = round(L, 2)        # tax if big shortfall drawn
        option_b_low = 0                   # tax if not drawn
        option_b_high_prob_pct = p_pct     # chance of the big tax
        option_b_low_prob_pct = q_pct      # chance of no tax

        return dict(
            reference=reference,
            option_a_amount=option_a_amount,
            option_b_high=option_b_high,
            option_b_low=option_b_low,
            option_b_high_prob_pct=option_b_high_prob_pct,
            option_b_low_prob_pct=option_b_low_prob_pct,
            is_stressed=is_stressed(player),
            stress_timeout=C.STRESS_TIMEOUT_SECONDS,
        )

    @staticmethod
    def error_message(player: Player, values):
        # Non-stressed participants have unlimited time and must pick an
        # option. Stressed participants may legitimately submit blank
        # (their countdown ran out) -- before_next_page fills in a random
        # choice for them, so do not reject a blank submission from them.
        if not is_stressed(player) and not values.get('choice'):
            return 'Please select an option before continuing.'

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if player.field_maybe_none('choice') is None:
            player.choice = random.choice(['A', 'B'])
            player.choice_forced = True
        else:
            player.choice_forced = False

class Choice2(Page):
    form_model = 'player'
    form_fields = ['choice2']

    @staticmethod
    def get_timeout_seconds(player: Player):
        return 1-get_la_timeout(player)

    @staticmethod
    def vars_for_template(player: Player):
        G = get_pot(player)
        s = C.SAFE_SHORTFALL_RATE * G
        L = C.BIG_SHORTFALL_RATE * G
        p_pct = int(C.BIG_SHORTFALL_PROB * 100)
        q_pct = 100 - p_pct

        reference = round(G, 2)
        option_a_amount = round(s, 2)      # certain tax
        option_b_high = round(L, 2)        # tax if big shortfall drawn
        option_b_low = 0                   # tax if not drawn
        option_b_high_prob_pct = p_pct     # chance of the big tax
        option_b_low_prob_pct = q_pct      # chance of no tax

        return dict(
            reference=reference,
            option_a_amount=option_a_amount,
            option_b_high=option_b_high,
            option_b_low=option_b_low,
            option_b_high_prob_pct=option_b_high_prob_pct,
            option_b_low_prob_pct=option_b_low_prob_pct,
            is_stressed=is_stressed(player),
            stress_timeout=C.STRESS_TIMEOUT_SECONDS,
        )

    @staticmethod
    def error_message(player: Player, values):
        # Non-stressed participants have unlimited time and must pick an
        # option. Stressed participants may legitimately submit blank
        # (their countdown ran out) -- before_next_page fills in a random
        # choice for them, so do not reject a blank submission from them.
        if not is_stressed(player) and not values.get('choice2'):
            return 'Please select an option before continuing.'

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if player.field_maybe_none('choice2') is None:
            player.choice2 = random.choice(['A', 'B'])
            player.choice2_forced = True
        else:
            player.choice2_forced = False

class SnakeWait(Page):
    """
    Framed to participants as a mandatory wait for other participants in
    the room to catch up. It is deliberately NOT a real oTree WaitPage --
    it does not synchronize with anyone else. timeout_seconds triggers
    oTree's built-in auto-submit after SNAKE_WAIT_SECONDS. The visible
    timer widget is hidden with CSS in the template rather than by
    setting timer_text = None (that is undocumented and risks breaking
    the underlying countdown JS that drives the auto-submit).
    """
    timeout_seconds = C.SNAKE_WAIT_SECONDS

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        pass


class Choice_Second(Page):
    form_model = 'player'
    form_fields = ['choice']

    @staticmethod
    def is_displayed(player):
        return player.loss_first == 1

    @staticmethod
    def get_timeout_seconds(player: Player):
        return 1-get_la_timeout(player)

    @staticmethod
    def vars_for_template(player: Player):
        G = get_pot(player)
        s = C.SAFE_SHORTFALL_RATE * G
        L = C.BIG_SHORTFALL_RATE * G
        p_pct = int(C.BIG_SHORTFALL_PROB * 100)
        q_pct = 100 - p_pct

        reference = round(G, 2)
        option_a_amount = round(s, 2)  # certain tax
        option_b_high = round(L, 2)  # tax if big shortfall drawn
        option_b_low = 0  # tax if not drawn
        option_b_high_prob_pct = p_pct  # chance of the big tax
        option_b_low_prob_pct = q_pct  # chance of no tax

        return dict(
            reference=reference,
            option_a_amount=option_a_amount,
            option_b_high=option_b_high,
            option_b_low=option_b_low,
            option_b_high_prob_pct=option_b_high_prob_pct,
            option_b_low_prob_pct=option_b_low_prob_pct,
            is_stressed=is_stressed(player),
            stress_timeout=C.STRESS_TIMEOUT_SECONDS,
        )

    @staticmethod
    def error_message(player: Player, values):
        # Non-stressed participants have unlimited time and must pick an
        # option. Stressed participants may legitimately submit blank
        # (their countdown ran out) -- before_next_page fills in a random
        # choice for them, so do not reject a blank submission from them.
        if not is_stressed(player) and not values.get('choice'):
            return 'Please select an option before continuing.'

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if player.field_maybe_none('choice') is None:
            player.choice = random.choice(['A', 'B'])
            player.choice_forced = True
        else:
            player.choice_forced = False

class NextQuestion(Page):
    pass

class Choice2_Second(Page):
    form_model = 'player'
    form_fields = ['choice2']

    @staticmethod
    def get_timeout_seconds(player: Player):
        return get_la_timeout(player)

    @staticmethod
    def vars_for_template(player: Player):
        G = get_pot(player)
        s = C.SAFE_SHORTFALL_RATE * G
        L = C.BIG_SHORTFALL_RATE * G
        p_pct = int(C.BIG_SHORTFALL_PROB * 100)
        q_pct = 100 - p_pct

        reference = round(G, 2)
        option_a_amount = round(s, 2)  # certain tax
        option_b_high = round(L, 2)  # tax if big shortfall drawn
        option_b_low = 0  # tax if not drawn
        option_b_high_prob_pct = p_pct  # chance of the big tax
        option_b_low_prob_pct = q_pct  # chance of no tax

        return dict(
            reference=reference,
            option_a_amount=option_a_amount,
            option_b_high=option_b_high,
            option_b_low=option_b_low,
            option_b_high_prob_pct=option_b_high_prob_pct,
            option_b_low_prob_pct=option_b_low_prob_pct,
            is_stressed=is_stressed(player),
            stress_timeout=C.STRESS_TIMEOUT_SECONDS,
        )

    @staticmethod
    def error_message(player: Player, values):
        # Non-stressed participants have unlimited time and must pick an
        # option. Stressed participants may legitimately submit blank
        # (their countdown ran out) -- before_next_page fills in a random
        # choice for them, so do not reject a blank submission from them.
        if not is_stressed(player) and not values.get('choice2'):
            return 'Please select an option before continuing.'

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if player.field_maybe_none('choice2') is None:
            player.choice2 = random.choice(['A', 'B'])
            player.choice2_forced = True
        else:
            player.choice2_forced = False


page_sequence = [TitlePage, Instructions, Choice, Choice2, NextQuestion, Choice_Second, Choice2_Second ]