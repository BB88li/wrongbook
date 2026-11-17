"""调度算法的单元测试。

只测纯函数，不碰数据库，跑起来很快：
    cd backend && python -m unittest discover -s tests -v
"""
import unittest
from datetime import date, timedelta

from app.services.sm2 import (
    MAX_EF,
    MAX_INTERVAL,
    MIN_EF,
    initial_ef,
    mastery_of,
    next_interval,
    priority_of,
    schedule,
)

TODAY = date(2026, 11, 17)


class TestNextInterval(unittest.TestCase):
    def test_first_success_is_one_day(self):
        n, days, ef = next_interval(0, 1, 2.5, 5)
        self.assertEqual((n, days), (1, 1))
        self.assertGreater(ef, 2.5)  # q=5 会抬高 EF

    def test_second_success_is_six_days(self):
        n, days, _ = next_interval(1, 1, 2.6, 4)
        self.assertEqual((n, days), (2, 6))

    def test_later_success_multiplies_previous_interval(self):
        n, days, ef = next_interval(2, 6, 2.5, 4)
        self.assertEqual(n, 3)
        self.assertEqual(days, round(6 * ef))

    def test_failure_resets_count_and_interval(self):
        n, days, ef = next_interval(5, 30, 2.6, 0)
        self.assertEqual((n, days), (0, 1))
        self.assertLess(ef, 2.6)  # 失败会扣 EF

    def test_failure_then_success_does_not_jump(self):
        """回归测试：修复前「忘了」之后再答对，会直接跳到 30 天。"""
        n, interval, ef = 0, 1, 2.5
        for _ in range(5):  # 连续成功 5 次
            n, interval, ef = next_interval(n, interval, ef, 5)
        n, interval, ef = next_interval(n, interval, ef, 0)  # 忘了
        self.assertEqual(interval, 1)
        n, interval, ef = next_interval(n, interval, ef, 5)  # 又记得了
        self.assertEqual(n, 1)
        self.assertEqual(interval, 1, "失败后重新开始，不应跳到第 6 档间隔")

    def test_interval_capped(self):
        _, days, _ = next_interval(30, 200, MAX_EF, 5)
        self.assertEqual(days, MAX_INTERVAL)

    def test_ef_bounds(self):
        _, _, ef = next_interval(0, 1, MAX_EF, 5)
        self.assertLessEqual(ef, MAX_EF)
        _, _, ef = next_interval(0, 1, MIN_EF, 0)
        self.assertGreaterEqual(ef, MIN_EF)


class TestSchedule(unittest.TestCase):
    def test_no_exam_date_keeps_sm2_interval(self):
        result = schedule(
            review_count=2,
            interval_days=6,
            ease_factor=2.5,
            lapses=0,
            quality=4,
            error_type="careless",
            today=TODAY,
            exam_date=None,
        )
        self.assertEqual(result.mode, "normal")
        self.assertGreater(result.interval_days, 6)
        self.assertEqual(result.due_date, TODAY + timedelta(days=result.interval_days))

    def test_deadline_caps_interval(self):
        # 距考试 20 天，预留 3 天 -> 间隔最多 17 天
        result = schedule(
            review_count=10,
            interval_days=30,
            ease_factor=2.5,
            lapses=0,
            quality=4,
            error_type="careless",
            today=TODAY,
            exam_date=TODAY + timedelta(days=20),
        )
        self.assertEqual(result.interval_days, 17)
        self.assertEqual(result.mode, "capped")

    def test_exam_mode_forces_daily(self):
        result = schedule(
            review_count=10,
            interval_days=30,
            ease_factor=2.5,
            lapses=0,
            quality=5,
            error_type="concept",
            today=TODAY,
            exam_date=TODAY + timedelta(days=5),
        )
        self.assertEqual(result.interval_days, 1)
        self.assertEqual(result.mode, "exam")

    def test_exam_passed_does_not_constrain(self):
        result = schedule(
            review_count=2,
            interval_days=6,
            ease_factor=2.5,
            lapses=0,
            quality=4,
            error_type="method",
            today=TODAY,
            exam_date=TODAY - timedelta(days=3),
        )
        self.assertEqual(result.mode, "normal")

    def test_failure_increments_lapses(self):
        result = schedule(
            review_count=3,
            interval_days=15,
            ease_factor=2.4,
            lapses=2,
            quality=1,
            error_type="concept",
            today=TODAY,
            exam_date=None,
        )
        self.assertEqual(result.lapses, 3)
        self.assertEqual(result.interval_days, 1)


class TestMetrics(unittest.TestCase):
    def test_initial_ef_by_error_type(self):
        self.assertGreater(initial_ef("careless"), initial_ef("method"))
        self.assertGreater(initial_ef("method"), initial_ef("concept"))

    def test_mastery_range(self):
        self.assertEqual(mastery_of(0, None, 0), 0.0)
        self.assertGreaterEqual(mastery_of(10, 5, 0), 0.0)
        self.assertLessEqual(mastery_of(10, 5, 0), 1.0)
        self.assertGreater(mastery_of(5, 5, 0), mastery_of(1, 3, 2))

    def test_priority_prefers_concept_and_weak(self):
        strong = priority_of("careless", 0.9, 0, 10)
        weak = priority_of("concept", 0.2, 3, 4)
        self.assertGreater(weak, strong)


if __name__ == "__main__":
    unittest.main()
