import ssl
import logging
from vibora.tests import TestSuite
from vibora import client


class TestSSLErrors(TestSuite):
    def setUp(self):
        # Python always warns about SSL errors but since where are forcing them to occur
        # there is no reason to fill the testing console with these messages.
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    async def test_expired_ssl__expects_exception(self):
        try:
            await client.get("https://expired.badssl.com/")
            self.fail("Client trusted in an expired SSL certificate.")
        except ssl.SSLError:
            pass

    async def test_expired_ssl__expects_ignored(self):
        try:
            await client.get("https://expired.badssl.com/", ssl=False)
        except ssl.SSLError:
            self.fail(
                "Client raised an exception for an expired SSL certificate " "even when explicitly told to not do so."
            )

    async def test_wrong_host_ssl__expects_exception(self):
        try:
            await client.get("https://wrong.host.badssl.com/")
            self.fail("Client trusted in an SSL certificate with an invalid hostname.")
        except (ssl.CertificateError, ssl.SSLError):
            pass

    async def test_wrong_host_ssl__expects_ignored(self):
        try:
            await client.get("https://wrong.host.badssl.com/", ssl=False)
        except ssl.CertificateError:
            self.fail("Failed to ignore SSL verification.")

    async def test_self_signed_certificate__expects_exception(self):
        try:
            await client.get("https://self-signed.badssl.com/")
            self.fail("Client trusted in an self signed certificate.")
        except ssl.SSLError:
            pass

    async def test_self_signed_certificate__expects_ignored(self):
        try:
            await client.get("https://self-signed.badssl.com/", ssl=False)
        except ssl.SSLError:
            self.fail("Failed to ignore SSL verification.")

    async def test_untrusted_root_certificate__expects_exception(self):
        try:
            await client.get("https://untrusted-root.badssl.com/")
            self.fail("Client trusted in an untrusted root certificate.")
        except ssl.SSLError:
            pass

    async def test_untrusted_root_certificate__expects_ignored(self):
        try:
            await client.get("https://untrusted-root.badssl.com/", ssl=False)
        except ssl.SSLError:
            self.fail("Failed to ignore SSL verification.")

    async def test_trusted_certificate__expects_allowed(self):
        try:
            await client.get("https://google.com/")
        except ssl.SSLError:
            self.fail("Failed to validate Google certificate.")

    # Pending OCSP/CRL SSL implementation.
    # def test_revoked_certificate__expects_exception(self):
    #     try:
    #         http.get('https://revoked.badssl.com/')
    #         self.fail('Client trusted in a revoked certificate.')
    #     except ssl.SSLError:
    #         pass

    # Pending OCSP/CRL SSL implementation.
    # def test_revoked_certificate__expects_ignored(self):
    #     try:
    #         http.get('https://revoked.badssl.com/', verify=False)
    #     except ssl.SSLError:
    #         self.fail('Client failed to ignore a revoked certificate.')
