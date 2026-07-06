from llp_recast.recast_math import (
    decay_probability_between,
    event_probability_at_least_one,
    event_probability_two,
)

R_MIN, R_MAX = 4.0, 300.0


def test_p_decay_bounded():
    for lab_len in (0.001, 1.0, 4.0, 100.0, 300.0, 1e6):
        p = decay_probability_between(R_MIN, R_MAX, lab_len)
        assert 0.0 <= p <= 1.0


def test_p_decay_peaks_at_detector_scale_not_at_extremes():
    lab_lengths = [0.001, 0.1, 1.0, 10.0, 50.0, 100.0, 300.0, 1000.0, 1e5, 1e8]
    probs = [decay_probability_between(R_MIN, R_MAX, l) for l in lab_lengths]
    peak_len = lab_lengths[probs.index(max(probs))]
    assert 1.0 <= peak_len <= 1000.0
    assert probs[0] < max(probs)
    assert probs[-1] < max(probs)


def test_event_probability_at_least_one_matches_two_llp_formula():
    p = 0.3
    assert event_probability_at_least_one(p, 2) == 1.0 - (1.0 - p) ** 2


def test_event_probability_two():
    assert event_probability_two(0.3) == 0.3 * 0.3
    assert event_probability_two(1.5) == 1.0  # clamped
