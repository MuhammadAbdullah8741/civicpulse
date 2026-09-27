"""Safety checks for the publication/deployment boundary; no Docker or network needed."""
import importlib.util
import os
import subprocess
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


publish = load("publish_images")
deploy = load("deploy_ci")
SHA = "a" * 40
BACKEND = "ghcr.io/example/civicpulse-backend@sha256:" + "b" * 64
FRONTEND = "ghcr.io/example/civicpulse-frontend@sha256:" + "c" * 64
MANIFEST = "containers:\n- image: civicpulse-backend:release-required\n---\ncontainers:\n- image: civicpulse-frontend:release-required\n"


class PublicationTests(unittest.TestCase):
    def test_main_tags_include_sha_and_latest(self):
        self.assertEqual(publish.publication_tags(SHA, "refs/heads/main", ""), [SHA, "latest"])

    def test_rehearsal_does_not_move_latest(self):
        self.assertEqual(publish.publication_tags(SHA, "refs/heads/dev", ""), [SHA])

    def test_release_tags_do_not_move_latest(self):
        self.assertEqual(publish.publication_tags(SHA, "refs/tags/v1.2.3", "v1.2.3"), [SHA, "v1.2.3", "1.2.3"])

    def test_bad_or_mismatched_version_is_rejected(self):
        for tag in ("v01.2.3", "v1", "latest", "v1.2.3;echo unsafe"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                publish.publication_tags(SHA, f"refs/tags/{tag}", tag)
        with self.assertRaises(ValueError):
            publish.publication_tags(SHA, "refs/heads/main", "v1.2.3")

    def test_short_sha_is_rejected(self):
        with self.assertRaises(ValueError):
            publish.publication_tags("abc123", "refs/heads/main", "")

    def test_digest_must_match_published_repository(self):
        self.assertEqual(publish.digest_for("ghcr.io/example/civicpulse-backend", [BACKEND, FRONTEND]), BACKEND)
        with self.assertRaises(ValueError):
            publish.digest_for("ghcr.io/example/civicpulse-backend", [FRONTEND])


class PublishingGateTests(unittest.TestCase):
    def test_scan_failure_prevents_every_push(self):
        calls = []

        def fake_run(*args, **kwargs):
            calls.append(args)
            if args[:2] == ("git", "rev-parse"):
                return SimpleNamespace(stdout=SHA + "\n")
            if "scripts/scan_images.py" in args:
                raise subprocess.CalledProcessError(1, args)
            return SimpleNamespace(stdout="")

        environment = {"GITHUB_ACTIONS": "true", "GITHUB_SHA": SHA,
                       "GITHUB_REPOSITORY": "Example/civicpulse",
                       "GITHUB_REF": "refs/heads/main", "RELEASE_TAG": ""}
        original = Path.cwd()
        with tempfile.TemporaryDirectory() as folder:
            try:
                os.chdir(folder)
                with patch.dict(os.environ, environment), patch.object(publish, "run", side_effect=fake_run):
                    with self.assertRaises(subprocess.CalledProcessError):
                        publish.main()
            finally:
                os.chdir(original)
        self.assertFalse(any(call[:2] == ("docker", "push") for call in calls))
        self.assertEqual(sum(call[:2] == ("docker", "build") for call in calls), 2)

    def test_helpers_reject_local_execution(self):
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "false"}):
            with self.assertRaises(RuntimeError):
                publish.main()
            with self.assertRaises(RuntimeError):
                deploy.main()


class DeploymentTests(unittest.TestCase):
    def test_images_are_replaced_by_digests(self):
        output = deploy.render_images(MANIFEST, BACKEND, FRONTEND)
        self.assertIn(BACKEND, output)
        self.assertIn(FRONTEND, output)
        self.assertNotIn("release-required", output)

    def test_mutable_tag_is_rejected(self):
        with self.assertRaises(ValueError):
            deploy.render_images(MANIFEST, "ghcr.io/example/civicpulse-backend:latest", FRONTEND)

    def test_unknown_manifest_is_rejected(self):
        with self.assertRaises(ValueError):
            deploy.render_images("image: another-application:dev\n", BACKEND, FRONTEND)

    def test_duplicate_backend_is_rejected(self):
        with self.assertRaises(ValueError):
            deploy.render_images(MANIFEST + "image: civicpulse-backend:dev\n", BACKEND, FRONTEND)

    def test_migration_uses_same_backend_digest(self):
        rendered = deploy.render_images("image: civicpulse-backend:dev\n", BACKEND, FRONTEND, migration=True)
        self.assertEqual(rendered, "image: " + BACKEND + "\n")

    def test_user_cluster_cannot_be_selected(self):
        self.assertEqual(deploy.CONTEXT, "k3d-civicpulse-ci")


if __name__ == "__main__":
    unittest.main()
