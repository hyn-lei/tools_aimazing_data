"""Offline regression tests for bounded GitHub synchronization."""

import importlib.util
import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock, patch

import requests

from app.providers import github_data


class SlowHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Eventually respond even if the client forgets its timeout, so a
        # regression fails without leaving the test itself stuck forever.
        body = json.dumps({"name": "example"}).encode()
        try:
            if self.path != "/slow-body":
                threading.Event().wait(0.2)
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.flush()
            if self.path == "/slow-body":
                threading.Event().wait(0.2)
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def log_message(self, *args):
        pass


class GitHubTimeoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), SlowHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}/repo"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_api_request_times_out_when_server_stalls(self):
        with patch.object(github_data, "GITHUB_REQUEST_TIMEOUT", (0.05, 0.05), create=True):
            with self.assertRaises(requests.exceptions.Timeout):
                github_data.GitHubData("owner/repo").get_data(self.url)

    def test_raw_readme_request_times_out_when_server_stalls(self):
        with patch.object(github_data, "GITHUB_REQUEST_TIMEOUT", (0.05, 0.05), create=True):
            with self.assertRaises(requests.exceptions.Timeout):
                github_data.get_raw_content(self.url)

    def test_api_request_stops_when_200_response_body_stalls(self):
        url = f"http://127.0.0.1:{self.server.server_port}/slow-body"
        with patch.object(github_data, "GITHUB_REQUEST_TIMEOUT", (0.05, 0.05), create=True):
            # Requests wraps a timeout while consuming a body in ConnectionError.
            with self.assertRaises(requests.exceptions.RequestException):
                github_data.GitHubData("owner/repo").get_data(url)


class GitHubRetrieverTests(unittest.TestCase):
    def setUp(self):
        self.github = Mock()
        self.github.summary_data.return_value = {
            "name": "repo", "full_name": "owner/repo",
            "owner": {"avatar_url": "avatar", "login": "owner"},
            "pushed_at": "2026-10-25T12:00:00Z",
        }
        self.github.activity_data.return_value = [{"timestamp": "2026-10-26T12:00:00Z"}]
        self.github.release_data.return_value = []
        self.github.read_me.return_value = "# README"
        self.factory = patch.object(github_data, "GitHubData", return_value=self.github)
        self.factory.start()
        self.addCleanup(self.factory.stop)

    def test_metadata_refresh_does_not_download_readme(self):
        self.github.read_me.side_effect = AssertionError("metadata refresh fetched README")
        data = github_data.git_hub_retriever("https://github.com/owner/repo", include_readme=False)
        self.assertEqual(len(data), 14)
        self.assertIsNone(data[5])
        self.assertEqual(data[12], "2026-10-26T12:00:00Z")

    def test_import_still_downloads_readme_by_default(self):
        data = github_data.git_hub_retriever("https://github.com/owner/repo")
        self.assertEqual(data[5], "# README")

    def test_missing_activity_uses_repository_push_time(self):
        for activity in (None, [], [{}]):
            with self.subTest(activity=activity):
                self.github.activity_data.return_value = activity
                data = github_data.git_hub_retriever("https://github.com/owner/repo")
                self.assertEqual(data[12], "2026-10-25T12:00:00Z")


class PullDataTests(unittest.TestCase):
    def setUp(self):
        # DataCard imports optional AI SDKs and database configuration. Replace
        # only that external boundary; execute the real job and retriever.
        self.data_card = Mock()
        model_module = ModuleType("app.models.data_card")
        model_module.DataCard = self.data_card
        path = Path(__file__).resolve().parents[1] / "app/jobs/pull_data_from_github.py"
        spec = importlib.util.spec_from_file_location("github_sync_job_under_test", path)
        self.job = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"app.models.data_card": model_module}):
            spec.loader.exec_module(self.job)

    def test_scheduled_refresh_updates_card_without_readme_requests(self):
        self.data_card.list_all.return_value = [{"id": 1, "url": "https://github.com/owner/repo"}]

        def github_response(url, **kwargs):
            response = Mock(status_code=200)
            if url.endswith("/activity"):
                response.json.return_value = [{"timestamp": "2026-10-26T12:00:00Z"}]
            elif url.endswith("/releases"):
                response.json.return_value = []
            elif url == "https://api.github.com/repos/owner/repo":
                response.json.return_value = {
                    "name": "repo", "full_name": "owner/repo",
                    "owner": {"avatar_url": "avatar", "login": "owner"},
                    "stargazers_count": 42,
                }
            else:
                self.fail(f"Scheduled refresh made unnecessary request: {url}")
            return response

        with patch.object(github_data.requests, "get", side_effect=github_response), patch.object(self.job.time, "sleep"):
            self.job.pull_data_from_github()
        self.data_card.update_or_create.assert_called_once()
        url, data, summarize = self.data_card.update_or_create.call_args.args
        self.assertEqual(url, "https://github.com/owner/repo")
        self.assertEqual(data[7], 42)
        self.assertIsNone(data[5])
        self.assertFalse(summarize)

    def test_timeout_on_one_card_does_not_prevent_next_update(self):
        self.data_card.list_all.return_value = [
            {"id": 1, "url": "https://github.com/owner/slow"},
            {"id": 2, "url": "https://github.com/owner/repo"},
        ]
        data = ("repo", "owner/repo", "avatar", "owner", "summary", None,
                [], 42, 1, 2, "homepage", "MIT", "2026-10-26", "v1")
        for error in (requests.Timeout("stalled"), requests.ConnectionError("body stalled")):
            with self.subTest(error=error):
                self.data_card.update_or_create.reset_mock()
                with patch.object(self.job, "git_hub_retriever", side_effect=[error, data]):
                    with patch.object(self.job.time, "sleep"), self.assertLogs(level="ERROR"):
                        self.job.pull_data_from_github()
                self.data_card.update_or_create.assert_called_once_with("https://github.com/owner/repo", data, False)


if __name__ == "__main__":
    unittest.main()
