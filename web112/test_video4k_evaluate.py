import unittest
import video4k_evaluate as ev

class VideoEvidenceTests(unittest.TestCase):
    def test_detects_real_advancing_4k_frames(self):
        samples = [dict(width=3840,height=2160,wall_ms=1000+i*1000,media_time=1+i,
                        total_frames=24+i*24,dropped_frames=2+i) for i in range(4)]
        r = ev.evaluate(samples)
        self.assertTrue(r['verified_4k_frame_progress'])
        self.assertEqual(r['observed_total_frames'], 72)
        self.assertEqual(r['observed_dropped_frames'], 3)
        self.assertEqual(r['observed_displayed_frames'], 69)
        self.assertEqual(r['source_width'], 3840)

    def test_rejects_wrong_resolution_or_stalled_video(self):
        wrong = [dict(width=1920,height=1080,wall_ms=i*1000,media_time=i,total_frames=i*24,dropped_frames=0) for i in range(3)]
        stalled = [dict(width=3840,height=2160,wall_ms=i*1000,media_time=0,total_frames=0,dropped_frames=0) for i in range(3)]
        for samples in (wrong, stalled, []):
            with self.assertRaises(ValueError): ev.evaluate(samples)

    def test_rejects_bad_dropped_frame_counters(self):
        samples = [dict(width=3840,height=2160,wall_ms=i*1000,media_time=i,total_frames=i*24,dropped_frames=i*48) for i in range(3)]
        with self.assertRaises(ValueError): ev.evaluate(samples)

if __name__ == '__main__': unittest.main()
