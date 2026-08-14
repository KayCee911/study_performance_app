import io
import unittest

from app import app


class UploadSurveyFeedbackTest(unittest.TestCase):
    def test_upload_survey_returns_feedback_summary(self):
        client = app.test_client()

        csv_content = b'''Username,1. Course 1 code,2. Course 1 Unit (in figures),3. Course 1 difficulty,4. Study time for this course (hours per week),5. Study method for course 1,6. Course 1 Grade
student1,CSC101,3,4,3,Active,A
student1,CSC102,2,2,2,Passive,B
'''

        response = client.post(
            "/upload-survey",
            data={"file": (io.BytesIO(csv_content), "sample.csv")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("feedback", payload)
        self.assertTrue(payload["feedback"]["summary"])
        self.assertGreaterEqual(payload["feedback"]["average_projected_gpa"], 0)


if __name__ == "__main__":
    unittest.main()