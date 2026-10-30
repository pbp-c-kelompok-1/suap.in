import unittest
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from scanner.models import FoodLog
from story.models import FriendChallenge

from .duels import accept_url, decline_duel, has_lifecycle
from .models import ChallengeProfile
from .ranking import friend_user_ids
from .services import build_challenge_data


needs_story = unittest.skipUnless(
    has_lifecycle(), 'butuh app story dari master (terima, skor, dan hasil tantangan)'
)


def accept_challenge(user, pk):
    from story.challenge_services import accept_challenge as accept
    return accept(user, pk)


def make_user(name):
    return User.objects.create_user(name, password='x12345678')


def log(user, when, grams):
    entry = FoodLog.objects.create(user=user, custom_name='x', co2_grams=grams)
    FoodLog.objects.filter(pk=entry.pk).update(scanned_at=when)


def notifs(user):
    return build_challenge_data(user)['notifs']


def duel_notifs(user):
    return [n for n in notifs(user) if n['id'].startswith('challenge-')]


class PendingChallengeNotificationTests(TestCase):
    def setUp(self):
        self.a, self.b = make_user('andi'), make_user('budi')
        self.ch = FriendChallenge.objects.create(challenger=self.a, opponent=self.b)

    def test_opponent_gets_decline_action_and_accept_when_story_supports_it(self):
        n = duel_notifs(self.b)[0]
        self.assertEqual(n['id'], f'challenge-{self.ch.pk}')
        self.assertIn('andi menantangmu!', n['t'])
        self.assertIn('Adu emisi CO\u2082 terendah selama 7 hari.', n['p'])
        decline = n['actions'][-1]
        self.assertEqual(decline['id'], 'decline')
        self.assertEqual(decline['url'], reverse('challenge:challenge_decline', args=[self.ch.pk]))
        if accept_url(self.ch.pk):                       # story master sudah digabung
            self.assertEqual([a['id'] for a in n['actions']], ['accept', 'decline'])
            self.assertEqual(n['actions'][0]['url'], reverse('story:challenge_accept', args=[self.ch.pk]))
            self.assertIn('Terima atau tolak', n['p'])
        else:                                            # story lama: hanya Tolak, tidak error
            self.assertEqual([a['id'] for a in n['actions']], ['decline'])
            self.assertIn('menolaknya', n['p'])

    def test_challenger_gets_no_notification_while_pending(self):
        self.assertEqual(duel_notifs(self.a), [])

    def test_display_name_is_used_for_challenger(self):
        ChallengeProfile.objects.create(user=self.a, display_name='Andi Hijau')
        self.assertIn('Andi Hijau menantangmu!', duel_notifs(self.b)[0]['t'])

    def test_ordinary_notifications_have_no_actions(self):
        self.assertTrue(all(n['actions'] == [] for n in notifs(self.b) if not n['id'].startswith('challenge-')))

    def test_pending_notification_disappears_after_decline(self):
        self.assertEqual(len(duel_notifs(self.b)), 1)
        decline_duel(self.b, self.ch.pk)
        self.assertEqual(duel_notifs(self.b), [])

    @needs_story
    def test_pending_notification_disappears_after_accept(self):
        accept_challenge(self.b, self.ch.pk)
        self.assertEqual(duel_notifs(self.b), [])


class DeclinedNotificationTests(TestCase):
    def setUp(self):
        self.a, self.b = make_user('andi'), make_user('budi')

    def test_challenger_is_told_when_declined(self):
        ch = FriendChallenge.objects.create(challenger=self.a, opponent=self.b)
        decline_duel(self.b, ch.pk)
        titles = [n['t'] for n in duel_notifs(self.a)]
        self.assertEqual(titles, ['budi menolak tantanganmu'])


@needs_story
class ChallengeOutcomeNotificationTests(TestCase):
    def setUp(self):
        self.a, self.b = make_user('andi'), make_user('budi')
        self.now = timezone.now()

    def test_challenger_is_told_when_accepted(self):
        ch = FriendChallenge.objects.create(challenger=self.a, opponent=self.b)
        accept_challenge(self.b, ch.pk)
        titles = [n['t'] for n in duel_notifs(self.a)]
        self.assertEqual(titles, ['budi menerima tantanganmu!'])
        self.assertEqual(duel_notifs(self.b), [])          # penerima tidak perlu kabar ini

    def _finished_duel(self, metric='lowest_co2', a_grams=300, b_grams=900):
        start = self.now - timedelta(days=8)
        ch = FriendChallenge.objects.create(
            challenger=self.a, opponent=self.b, metric=metric, status='active',
            duration_days=7, started_at=start, ends_at=self.now - timedelta(days=1),
        )
        log(self.a, start + timedelta(hours=2), a_grams)
        log(self.b, start + timedelta(hours=3), b_grams)
        return ch

    def test_result_appears_without_pressing_refresh_and_names_winner(self):
        ch = self._finished_duel()
        self.assertEqual(ch.status, 'active')                      # belum difinalkan
        mine = [n for n in duel_notifs(self.a) if n['id'] == f'challenge-result-{ch.pk}'][0]
        self.assertEqual(mine['t'], 'Kamu menang melawan budi!')
        self.assertIn('Kamu 300 g CO\u2082 vs budi 900 g CO\u2082.', mine['p'])
        ch.refresh_from_db()
        self.assertEqual((ch.status, ch.winner_id), ('finished', self.a.pk))

    def test_loser_gets_encouragement(self):
        ch = self._finished_duel()
        theirs = [n for n in duel_notifs(self.b) if n['id'] == f'challenge-result-{ch.pk}'][0]
        self.assertEqual(theirs['t'], 'andi memenangkan tantangan')
        self.assertIn('Jangan menyerah', theirs['p'])
        self.assertIn('Kamu 900 g CO\u2082 vs andi 300 g CO\u2082.', theirs['p'])

    def test_draw_message(self):
        ch = self._finished_duel(a_grams=500, b_grams=500)
        n = [n for n in duel_notifs(self.a) if n['id'] == f'challenge-result-{ch.pk}'][0]
        self.assertEqual(n['t'], 'Tantangan melawan budi berakhir seri')

    def test_most_scans_uses_scan_counts_in_text(self):
        ch = self._finished_duel('most_scans')
        n = [n for n in duel_notifs(self.a) if n['id'] == f'challenge-result-{ch.pk}'][0]
        self.assertIn('Kamu 1 scan vs budi 1 scan.', n['p'])
        self.assertEqual(n['t'], 'Tantangan melawan budi berakhir seri')

    def test_old_results_do_not_create_new_notifications(self):
        ch = self._finished_duel()
        FriendChallenge.objects.filter(pk=ch.pk).update(
            status='finished', winner=self.a, started_at=self.now - timedelta(days=50),
            finished_at=self.now - timedelta(days=40),
            result_snapshot={'challenger': {'count': 1, 'co2': 300}, 'opponent': {'count': 1, 'co2': 900}},
        )
        self.assertEqual(duel_notifs(self.a), [])

    def test_stranger_sees_nothing_about_other_peoples_challenges(self):
        self._finished_duel()
        self.assertEqual(duel_notifs(make_user('orang_asing')), [])

    def test_notification_text_is_stable_across_reloads(self):
        ch = self._finished_duel()
        first = duel_notifs(self.a)
        self.assertEqual(duel_notifs(self.a), first)
        self.assertEqual(len([n for n in first if n['id'] == f'challenge-result-{ch.pk}']), 1)


class FriendDefinitionTests(TestCase):
    def setUp(self):
        self.me, self.other = make_user('me'), make_user('other')

    def duel(self, status, challenger=None, opponent=None):
        return FriendChallenge.objects.create(
            challenger=challenger or self.other, opponent=opponent or self.me, status=status)

    def test_pending_and_declined_challenges_do_not_make_friends(self):
        self.duel('pending')
        declined = self.duel('pending')
        decline_duel(self.me, declined.pk)                 # ditolak -> dihapus
        self.assertEqual(friend_user_ids(self.me), set())
        self.assertEqual(friend_user_ids(self.other), set())

    def test_accepted_challenge_connects_both_sides(self):
        self.duel('active')
        self.assertEqual(friend_user_ids(self.me), {self.other.pk})
        self.assertEqual(friend_user_ids(self.other), {self.me.pk})

    def test_finished_challenge_still_counts(self):
        self.duel('finished', challenger=self.me, opponent=self.other)
        self.assertEqual(friend_user_ids(self.me), {self.other.pk})
