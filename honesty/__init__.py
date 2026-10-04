from otree.api import *
import random


class C(BaseConstants):
    NAME_IN_URL = 'honesty'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    PAYMENT_PER_POINT = 30


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    die_roll = models.IntegerField()

    report = models.IntegerField(
        min=1,
        max=6,
        label='What number did you roll?',
    )


def creating_session(subsession: Subsession):
    for player in subsession.get_players():
        player.die_roll = random.randint(1, 6)


# PAGES

class TitlePage(Page):
    pass
class Instructions(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            payment_per_point=C.PAYMENT_PER_POINT,
        )


class Report(Page):
    form_model = 'player'
    form_fields = ['report']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            die_roll=player.die_roll,
            payment_per_point=C.PAYMENT_PER_POINT,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.payoff = C.PAYMENT_PER_POINT * player.report
        player.die_roll = 0
        player.participant.vars['honesty_report'] = player.report
        player.participant.vars['honesty_payoff'] = player.payoff


page_sequence = [TitlePage, Instructions, Report]