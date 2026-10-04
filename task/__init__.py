from otree.api import *


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'task'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    TOTAL_POINTS_TO_ALLOCATE = 100
    TASK_SECONDS = 60
    NUM_PROBLEMS = 20

    # Belief question: "if we picked N_COMPARISON people at random from the
    # room, how many of them do you think scored lower than you?"
    N_COMPARISON = 10


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    score = models.IntegerField(initial=0)
    guessed_score = models.IntegerField(
        label="How many do you think you got correct?",
        min=0,
        max=C.NUM_PROBLEMS,
    )
    guessed_rank = models.IntegerField(
        label="Out of these 10 participants, how many do you believe scored lower than you on the task?",
        min=0,
        max=C.N_COMPARISON,
    )


# PAGES

class TitlePage(Page):
    pass

class FirstInstructions(Page):
    pass


class StartTaskWaitPage(WaitPage):
    """Holds everyone here so the whole session begins the timed task together."""
    wait_for_all_groups = True
    title_text = 'Please wait'
    body_text = 'Waiting for all participants to be ready. The task will start shortly for everyone at the same time.'


class Task(Page):
    form_model = 'player'
    form_fields = ['score']
    timeout_seconds = C.TASK_SECONDS
    timer_text = 'Time remaining:'

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            task_seconds=C.TASK_SECONDS,
            num_problems=C.NUM_PROBLEMS,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if player.field_maybe_none('score') is None:
            player.score = 0
        player.participant.vars['task_score'] = player.score


class TaskResultsWaitPage(WaitPage):
    """Waits for everyone to finish the task, then computes the session top score."""
    wait_for_all_groups = True
    title_text = 'Please wait'
    body_text = 'Waiting for all participants to finish the task.'

    @staticmethod
    def after_all_players_arrive(subsession: Subsession):
        top_score = max(p.score for p in subsession.get_players())
        for p in subsession.get_players():
            p.participant.vars['top_score_in_session'] = top_score


class GuessScore(Page):
    form_model = 'player'
    form_fields = ['guessed_score']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            num_problems=C.NUM_PROBLEMS,
            n_comparison=C.N_COMPARISON,
        )

    @staticmethod
    def error_message(player: Player, values):
        guess = values.get('guessed_score')

        if guess is None:
            return 'Please enter your guess for how many problems you got correct.'
        if guess < 0 or guess > C.NUM_PROBLEMS:
            return f'Please enter a number between 0 and {C.NUM_PROBLEMS}.'

    @staticmethod
    def before_next_page(player, timeout_happened):
        player.participant.guessed_score = player.guessed_score

class GuessRank(Page):
    form_model = 'player'
    form_fields = ['guessed_rank']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            num_problems=C.NUM_PROBLEMS,
            n_comparison=C.N_COMPARISON,
        )

    @staticmethod
    def error_message(player: Player, values):
        rank_guess = values.get('guessed_rank')

        if rank_guess is None:
            return 'Please enter your guess for how many of the 10 people scored lower than you.'
        if rank_guess < 0 or rank_guess > C.N_COMPARISON:
            return f'Please enter a number between 0 and {C.N_COMPARISON}.'


page_sequence = [
    TitlePage,
    FirstInstructions,
    StartTaskWaitPage,
    Task,
    TaskResultsWaitPage,
    GuessScore,
    GuessRank,
]