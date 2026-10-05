from otree.api import *
import random


doc = """
Competition Game app (self-contained, single oTree round).

Implements the last two stages of the tournament-entry design from the
group project note (a Niederle & Vesterlund 2007 style design). Stage 1
(piece-rate) lives in a separate 'task' app and is not repeated here.
Since this app now uses NUM_ROUNDS = 1, "Round 2" and "Round 3" are no
longer separate oTree rounds -- they are simply the next page in the
sequence, and both scores (r2score, r3score) live as separate fields
on the same single-round Player object.

Forced tournament (r2score): each individual performs the addition
    task for a score r2score. Grouped into groups of GROUP_SIZE. Earns
    4 * r2score * PIECE_RATE if r2score is the strictly highest score
    in their group, else 0.

Competition entry decision (r3score): each individual chooses whether
    to enter a tournament, enter_tournament in {True, False}, BEFORE
    performing the task again for a score r3score. If entered,
    r3score is compared against the OTHER group members' r2score
    (the forced-tournament score, not a simultaneous score) --
    removing strategic uncertainty about what others are doing right
    now, exactly as in the classic design.
        enter_tournament = True: earn 4 * r3score * PIECE_RATE if
            r3score > max(others' r2score in the group), else 0.
        enter_tournament = False: earn r3score * PIECE_RATE
            (safe piece-rate).

No per-stage results pages are shown anywhere. Everything is revealed
only in FinalResults at the very end.
"""


class C(BaseConstants):
    NAME_IN_URL = 'competition'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    TASK_SECONDS = 60
    NUM_PROBLEMS = 20

    PIECE_RATE = 2          # NOK per correct answer, piece-rate payment
    TOURNAMENT_MULTIPLE = 4  # winner earns TOURNAMENT_MULTIPLE * score * PIECE_RATE


class Subsession(BaseSubsession):
    def creating_session(self):
        self.group_randomly()


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    enter_tournament = models.BooleanField(
        label="Do you want to enter the tournament for this round?",
        choices=[[True, 'Yes, enter the tournament'], [False, 'No, take the piece-rate payment']],
        widget=widgets.RadioSelect,
    )

    r2score = models.IntegerField(initial=0)
    r3score = models.IntegerField(initial=0)







# ---------------------------------------------------------------------------
# PAGES
# ---------------------------------------------------------------------------
# No per-stage results or wait pages are shown to participants. Scores and
# payoffs are still computed and recorded in the background exactly as
# before; they just are not surfaced until FinalResults at the very end.
# With NUM_ROUNDS = 1, no is_displayed guards are needed anywhere -- every
# page below appears exactly once, in the order listed in page_sequence.

class TitlePage(Page):
    pass


class Instructions(Page):
    pass

class Round1Instructions(Page):
    pass


class Round2Instructions(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            piece_rate=C.PIECE_RATE,
            multiple=C.TOURNAMENT_MULTIPLE,
            group_size=C.PLAYERS_PER_GROUP,
        )


class Round2Task(Page):
    form_model = 'player'
    form_fields = ['r2score']
    timeout_seconds = C.TASK_SECONDS
    timer_text = 'Time remaining:'

    @staticmethod
    def vars_for_template(player: Player):
        return dict(task_seconds=C.TASK_SECONDS, num_problems=C.NUM_PROBLEMS, round_label=2)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if player.field_maybe_none('r2score') is None:
            player.r2score = 0

class Round3Instructions(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return dict(piece_rate=C.PIECE_RATE, multiple=C.TOURNAMENT_MULTIPLE)


class Round3EntryDecision(Page):
    form_model = 'player'
    form_fields = ['enter_tournament']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            piece_rate=C.PIECE_RATE,
            multiple=C.TOURNAMENT_MULTIPLE,
        )

    @staticmethod
    def error_message(player: Player, values):
        if values.get('enter_tournament') is None:
            return 'Please choose whether to enter the tournament.'


class Round3Task(Page):
    form_model = 'player'
    form_fields = ['r3score']
    timeout_seconds = C.TASK_SECONDS
    timer_text = 'Time remaining:'

    @staticmethod
    def vars_for_template(player: Player):
        return dict(task_seconds=C.TASK_SECONDS, num_problems=C.NUM_PROBLEMS, round_label=3)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if player.field_maybe_none('r3score') is None:
            player.r3score = 0




page_sequence = [
    TitlePage, Instructions, Round1Instructions,
    Round2Instructions, Round2Task,
    Round3Instructions, Round3EntryDecision, Round3Task,
]