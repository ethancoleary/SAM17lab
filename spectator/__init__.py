from otree.api import *
import random


class C(BaseConstants):
    NAME_IN_URL = 'spectator'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    TOTAL_POINTS_TO_ALLOCATE = 250
    HIGH_PAY = 200
    LOW_PAY = 50


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):

    treatment = models.IntegerField()

    # 1 = initial pay should be assigned by merit (higher task score gets
    # HIGH_PAY); 0 = initial pay should be assigned randomly, regardless
    # of task score. Read from participant.vars['merit_treatment'] the
    # same way 'treatment' is read from participant.spec_treatment.
    merit = models.IntegerField()

    worker_a_id = models.IntegerField()
    worker_b_id = models.IntegerField()
    worker_a_score = models.IntegerField()
    worker_b_score = models.IntegerField()

    # Initial endowments before the spectator intervenes, determined by merit
    worker_a_initial = models.IntegerField()
    worker_b_initial = models.IntegerField()

    final_a = models.IntegerField(
        min=0,
        max=C.TOTAL_POINTS_TO_ALLOCATE,
        label='How many NOK should Worker A receive?',
    )
    final_b = models.IntegerField()
    implemented_gini = models.FloatField()
    intervention = models.BooleanField()


def get_merit(player: Player):
    """
    Ensures player.merit is set, reading it from
    participant.vars['merit_treatment'] (set upstream, e.g. by an earlier
    app in the session) the same way player.treatment is read from
    participant.spec_treatment in TitlePage. Defaults to 0 (random
    initial pay, not merit-based) if no such var has been set -- e.g.
    when testing this app in isolation.
    """
    if player.field_maybe_none('merit') is not None:
        return player.merit

    merit_value = player.participant.vars.get('merit_treatment', 0)
    player.merit = merit_value
    return merit_value


def ensure_role_assignment(player: Player):
    """
    Guarantees worker_a/b ids, scores, and initial pay are set for this
    player, computing them now if they are still missing. This makes the
    app resilient regardless of whether RoleAssignment.before_next_page
    already ran for this player (e.g. if a page was skipped, timed out
    before submitting, or this is being viewed out of the normal flow).
    """
    if player.field_maybe_none('worker_a_score') is not None:
        return  # already assigned

    get_merit(player)

    subsession = player.subsession
    players = subsession.get_players()

    others = [
        p for p in players
        if p.participant.id_in_session != player.participant.id_in_session
    ]

    if len(others) >= 2:
        worker_a, worker_b = random.sample(others, 2)
    elif len(others) == 1:
        worker_a = worker_b = others[0]
    else:
        worker_a = worker_b = player  # solo testing fallback

    player.worker_a_id = worker_a.participant.id_in_session
    player.worker_b_id = worker_b.participant.id_in_session
    player.worker_a_score = worker_a.participant.vars.get('task_score', 0)
    player.worker_b_score = worker_b.participant.vars.get('task_score', 0)

    if player.merit == 1:
        if player.worker_a_score > player.worker_b_score:
            a_high = True
        elif player.worker_a_score < player.worker_b_score:
            a_high = False
        else:
            a_high = random.random() < 0.5
    else:
        a_high = random.random() < 0.5

    if a_high:
        player.worker_a_initial = C.HIGH_PAY
        player.worker_b_initial = C.LOW_PAY
    else:
        player.worker_a_initial = C.LOW_PAY
        player.worker_b_initial = C.HIGH_PAY


# PAGES

class TitlePage(Page):

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.treatment = player.participant.spec_treatment


class SpectatorInstructions(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            total=C.TOTAL_POINTS_TO_ALLOCATE,
            high_pay=C.HIGH_PAY,
            low_pay=C.LOW_PAY,
        )


class RoleAssignment(Page):
    @staticmethod
    def vars_for_template(player: Player):
        ensure_role_assignment(player)
        return dict(
            worker_a_score=player.worker_a_score,
            worker_b_score=player.worker_b_score,
            worker_a_initial=player.worker_a_initial,
            worker_b_initial=player.worker_b_initial,
            total=C.TOTAL_POINTS_TO_ALLOCATE,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        ensure_role_assignment(player)


class Decide(Page):
    form_model = 'player'
    form_fields = ['final_a']

    @staticmethod
    def vars_for_template(player: Player):
        ensure_role_assignment(player)
        return dict(
            worker_a_score=player.worker_a_score,
            worker_b_score=player.worker_b_score,
            worker_a_initial=player.worker_a_initial,
            worker_b_initial=player.worker_b_initial,
            total=C.TOTAL_POINTS_TO_ALLOCATE,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        ensure_role_assignment(player)
        player.final_b = C.TOTAL_POINTS_TO_ALLOCATE - player.final_a
        player.implemented_gini = abs(player.final_a - player.final_b) / (2 * C.TOTAL_POINTS_TO_ALLOCATE)

        player.intervention = (player.final_a != player.worker_a_initial)

        participant = player.participant
        participant.vars['spectator_final_a'] = player.final_a
        participant.vars['spectator_final_b'] = player.final_b
        participant.vars['spectator_gini'] = player.implemented_gini
        participant.vars['spectator_intervention'] = player.intervention


page_sequence = [
    TitlePage,
    SpectatorInstructions,
    RoleAssignment,
    Decide,
]