import base64
import hashlib
import os
import unittest
from unittest.mock import patch

from knowb_org_index.oauth import GoogleOAuth, OAuthError, _pkce_pair


class OAuthTests(unittest.TestCase):
    def test_pkce_challenge_uses_unpadded_sha256(self):
        verifier, challenge = _pkce_pair()
        expected = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()
        ).decode("ascii").rstrip("=")
        self.assertGreaterEqual(len(verifier), 43)
        self.assertLessEqual(len(verifier), 128)
        self.assertEqual(challenge, expected)
        self.assertNotIn("=", challenge)

    def test_client_id_is_required_before_authorization(self):
        with patch.dict(
            os.environ,
            {
                "KNOWB_GOOGLE_OAUTH_CLIENT_ID": "",
                "KNOWB_GOOGLE_OAUTH_CLIENT_FILE": "",
            },
            clear=False,
        ):
            with self.assertRaises(OAuthError):
                GoogleOAuth()


if __name__ == "__main__":
    unittest.main()
