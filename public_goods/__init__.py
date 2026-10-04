from otree.api import *


class C(BaseConstants):
    NAME_IN_URL = 'public_goods'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    ENDOWMENT = 100
    MULTIPLIER = 1.5


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    total_contribution = models.CurrencyField()
    individual_return = models.CurrencyField()


class Player(BasePlayer):
    contribution = models.CurrencyField(
        min=0,
        max=C.ENDOWMENT,
        label='How much do you want to contribute to the project?',
    )


def creating_session(subsession: Subsession):
    group_size = subsession.session.config.get('group_size', 1)
    players = subsession.get_players()
    matrix = [
        players[i:i + group_size]
        for i in range(0, len(players), group_size)
    ]
    subsession.set_group_matrix(matrix)


def set_payoffs(group: Group):
    players = group.get_players()
    n = len(players)
    group.total_contribution = sum(p.contribution for p in players)
    group.individual_return = C.MULTIPLIER * group.total_contribution / n

    for p in players:
        p.payoff = C.ENDOWMENT - p.contribution + group.individual_return
        participant = p.participant
        participant.vars['pg_contribution'] = p.contribution
        participant.vars['pg_payoff'] = p.payoff


# PAGES

class TitlePage(Page):
    pass
class Instructions(Page):
    @staticmethod
    def vars_for_template(player: Player):
        group_size = len(player.group.get_players())
        return dict(
            endowment=C.ENDOWMENT,
            multiplier=C.MULTIPLIER,
            group_size=group_size,
            others_count=group_size - 1,
            mpcr=round(C.MULTIPLIER / group_size, 2),
        )


class Contribute(Page):
    form_model = 'player'
    form_fields = ['contribution']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            endowment=C.ENDOWMENT,
            multiplier=C.MULTIPLIER,
            group_size=4,
        )

class WaitForGroup(WaitPage):
    after_all_players_arrive = set_payoffs




page_sequence = [TitlePage, Instructions, Contribute,
                 #WaitForGroup
                ]
