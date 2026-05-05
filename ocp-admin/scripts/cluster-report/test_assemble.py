#!/usr/bin/env python3

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import assemble


class TestUnwrapPersistedOutput(unittest.TestCase):

    def test_single_text_entry(self):
        raw = json.dumps([{"type": "text", "text": "NAME  STATUS\nnode-1  Ready"}])
        result = assemble.unwrap_persisted_output(raw)
        self.assertEqual(result, "NAME  STATUS\nnode-1  Ready")

    def test_multiple_text_entries(self):
        raw = json.dumps([
            {"type": "text", "text": "part1"},
            {"type": "text", "text": "part2"},
        ])
        result = assemble.unwrap_persisted_output(raw)
        self.assertEqual(result, "part1\npart2")

    def test_non_envelope_json_array(self):
        data = [{"name": "proj-1"}, {"name": "proj-2"}]
        raw = json.dumps(data)
        result = assemble.unwrap_persisted_output(raw)
        self.assertEqual(result, data)

    def test_envelope_with_no_text_type(self):
        raw = json.dumps([{"type": "image", "data": "base64..."}])
        result = assemble.unwrap_persisted_output(raw)
        self.assertIsNone(result)

    def test_mixed_types_in_envelope(self):
        raw = json.dumps([
            {"type": "text", "text": "hello"},
            {"type": "image", "data": "..."},
            {"type": "text", "text": "world"},
        ])
        result = assemble.unwrap_persisted_output(raw)
        self.assertEqual(result, "hello\nworld")

    def test_empty_list(self):
        raw = "[]"
        result = assemble.unwrap_persisted_output(raw)
        self.assertEqual(result, [])

    def test_string_value(self):
        raw = json.dumps("just a string")
        result = assemble.unwrap_persisted_output(raw)
        self.assertEqual(result, "just a string")

    def test_dict_value(self):
        data = {"key": "value"}
        raw = json.dumps(data)
        result = assemble.unwrap_persisted_output(raw)
        self.assertEqual(result, data)

    def test_non_json_returns_raw_string(self):
        raw = "not valid json{{{"
        result = assemble.unwrap_persisted_output(raw)
        self.assertEqual(result, raw)

    def test_plain_text_tabular_passthrough(self):
        raw = (
            "NAMESPACE   APIVERSION   KIND   NAME    READY   STATUS\n"
            "default     v1           Pod    web-1   1/1     Running\n"
            "default     v1           Pod    web-2   0/1     Pending\n"
        )
        result = assemble.unwrap_persisted_output(raw)
        self.assertEqual(result, raw)

    def test_plain_text_oc_format_passthrough(self):
        raw = "NAME      STATUS   ROLES    AGE\nnode-1    Ready    worker   5d\n"
        result = assemble.unwrap_persisted_output(raw)
        self.assertEqual(result, raw)

    def test_large_text_content(self):
        big_text = "LINE\n" * 10000
        raw = json.dumps([{"type": "text", "text": big_text}])
        result = assemble.unwrap_persisted_output(raw)
        self.assertEqual(result, big_text)


class TestResolveFileRef(unittest.TestCase):

    def test_valid_envelope_file(self):
        content = json.dumps([{"type": "text", "text": "pod data here"}])
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            result, error = assemble.resolve_file_ref(path)
            self.assertIsNone(error)
            self.assertEqual(result, "pod data here")
        finally:
            os.unlink(path)

    def test_valid_plain_json_file(self):
        data = [{"name": "ns-1"}, {"name": "ns-2"}]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            result, error = assemble.resolve_file_ref(path)
            self.assertIsNone(error)
            self.assertEqual(result, data)
        finally:
            os.unlink(path)

    def test_missing_file(self):
        result, error = assemble.resolve_file_ref("/tmp/nonexistent-file.json")
        self.assertIsNone(result)
        self.assertIn("not found", error.lower())

    def test_path_outside_allowed_directory(self):
        result, error = assemble.resolve_file_ref("/etc/passwd")
        self.assertIsNone(result)
        self.assertIn("outside allowed directory", error.lower())

    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        try:
            result, error = assemble.resolve_file_ref(path)
            self.assertIsNone(result)
            self.assertIn("Empty", error)
        finally:
            os.unlink(path)

    def test_non_json_file_returns_content(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("not json{{{")
            path = f.name
        try:
            result, error = assemble.resolve_file_ref(path)
            self.assertIsNone(error)
            self.assertEqual(result, "not json{{{")
        finally:
            os.unlink(path)

    def test_plain_text_tabular_file(self):
        text = (
            "NAMESPACE   APIVERSION   KIND   NAME    READY   STATUS    RESTARTS   AGE\n"
            "default     v1           Pod    web-1   1/1     Running   0          1d\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(text)
            path = f.name
        try:
            result, error = assemble.resolve_file_ref(path)
            self.assertIsNone(error)
            self.assertEqual(result, text)
        finally:
            os.unlink(path)

    def test_envelope_with_no_text(self):
        content = json.dumps([{"type": "image", "data": "..."}])
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            result, error = assemble.resolve_file_ref(path)
            self.assertIsNone(result)
            self.assertIn("No text content", error)
        finally:
            os.unlink(path)

    @unittest.skipIf(os.getuid() == 0, "Cannot test permission denied as root")
    def test_permission_denied(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("data")
            path = f.name
        try:
            os.chmod(path, 0o000)
            result, error = assemble.resolve_file_ref(path)
            self.assertIsNone(result)
            self.assertIn("Permission denied", error)
        finally:
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
            os.unlink(path)


class TestResolveCluster(unittest.TestCase):

    def test_all_inline_passthrough(self):
        cluster = {
            "context": "test",
            "server": "https://test:6443",
            "nodes_top": "NAME CPU\nnode1 100m",
            "nodes_list": "NAME STATUS\nnode1 Ready",
            "projects": [{"name": "p1"}],
            "namespaces": None,
            "pods": "NS NAME STATUS\ndefault pod1 Running",
            "errors": [],
        }
        original = json.loads(json.dumps(cluster))
        assemble.resolve_cluster(cluster)
        self.assertEqual(cluster, original)

    def test_file_ref_resolved(self):
        content = json.dumps([{"type": "text", "text": "pod data"}])
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            cluster = {
                "pods": {"$file": path},
                "nodes_top": None,
                "nodes_list": None,
                "projects": None,
                "namespaces": None,
                "errors": [],
            }
            assemble.resolve_cluster(cluster)
            self.assertEqual(cluster["pods"], "pod data")
            self.assertEqual(cluster["errors"], [])
        finally:
            os.unlink(path)

    def test_failed_file_ref_adds_error(self):
        cluster = {
            "pods": {"$file": "/tmp/nonexistent-file.json"},
            "nodes_top": None,
            "nodes_list": None,
            "projects": None,
            "namespaces": None,
            "errors": [],
        }
        assemble.resolve_cluster(cluster)
        self.assertIsNone(cluster["pods"])
        self.assertEqual(len(cluster["errors"]), 1)
        self.assertIn("not found", cluster["errors"][0].lower())

    def test_preserves_existing_errors(self):
        cluster = {
            "pods": {"$file": "/tmp/nonexistent-file.json"},
            "nodes_top": None,
            "nodes_list": None,
            "projects": None,
            "namespaces": None,
            "errors": ["Metrics Server not available"],
        }
        assemble.resolve_cluster(cluster)
        self.assertEqual(len(cluster["errors"]), 2)
        self.assertEqual(cluster["errors"][0], "Metrics Server not available")

    def test_mixed_inline_file_null(self):
        content = json.dumps([{"type": "text", "text": "node data"}])
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            cluster = {
                "nodes_top": None,
                "nodes_list": {"$file": path},
                "projects": [{"name": "p1"}],
                "namespaces": None,
                "pods": "NS NAME STATUS\ndefault pod1 Running",
                "errors": [],
            }
            assemble.resolve_cluster(cluster)
            self.assertIsNone(cluster["nodes_top"])
            self.assertEqual(cluster["nodes_list"], "node data")
            self.assertEqual(cluster["projects"], [{"name": "p1"}])
            self.assertEqual(cluster["pods"], "NS NAME STATUS\ndefault pod1 Running")
        finally:
            os.unlink(path)

    def test_non_data_fields_ignored(self):
        cluster = {
            "context": {"$file": "/should/not/resolve"},
            "nodes_top": None,
            "nodes_list": None,
            "projects": None,
            "namespaces": None,
            "pods": None,
            "errors": [],
        }
        assemble.resolve_cluster(cluster)
        self.assertEqual(cluster["context"], {"$file": "/should/not/resolve"})


class TestFullPipeline(unittest.TestCase):

    SCRIPT = str(Path(__file__).parent / "assemble.py")

    def _run(self, input_data, extra_args=None):
        cmd = [sys.executable, self.SCRIPT]
        if extra_args:
            cmd.extend(extra_args)
        proc = subprocess.run(
            cmd,
            input=json.dumps(input_data),
            capture_output=True, text=True,
        )
        return proc

    def test_inline_passthrough(self):
        manifest = {
            "generated_at": "2026-01-01T00:00:00Z",
            "clusters": {
                "test": {
                    "context": "test",
                    "server": "https://test:6443",
                    "nodes_top": None,
                    "nodes_list": None,
                    "projects": [{"name": "default"}],
                    "namespaces": None,
                    "pods": "NS NAME STATUS\ndefault pod1 Running",
                    "errors": [],
                }
            },
        }
        proc = self._run(manifest)
        self.assertEqual(proc.returncode, 0, f"Failed: {proc.stderr}")
        output = json.loads(proc.stdout)
        cluster = output["clusters"]["test"]
        self.assertEqual(cluster["pods"], "NS NAME STATUS\ndefault pod1 Running")
        self.assertEqual(cluster["projects"], [{"name": "default"}])

    def test_file_ref_resolution(self):
        content = json.dumps([{"type": "text", "text": "resolved content"}])
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            manifest = {
                "generated_at": "2026-01-01T00:00:00Z",
                "clusters": {
                    "test": {
                        "context": "test",
                        "server": "https://test:6443",
                        "nodes_top": None,
                        "nodes_list": None,
                        "projects": None,
                        "namespaces": None,
                        "pods": {"$file": path},
                        "errors": [],
                    }
                },
            }
            proc = self._run(manifest)
            self.assertEqual(proc.returncode, 0, f"Failed: {proc.stderr}")
            output = json.loads(proc.stdout)
            self.assertEqual(output["clusters"]["test"]["pods"], "resolved content")
        finally:
            os.unlink(path)

    def test_aggregate_flag(self):
        manifest = {
            "generated_at": "2026-01-01T00:00:00Z",
            "clusters": {
                "test": {
                    "context": "test",
                    "server": "https://test:6443",
                    "nodes_top": None,
                    "nodes_list": None,
                    "projects": [{"name": "default"}, {"name": "kube-system"}],
                    "namespaces": None,
                    "pods": [
                        {"namespace": "default", "name": "pod1", "status": "Running"},
                        {"namespace": "default", "name": "pod2", "status": "Pending"},
                    ],
                    "errors": [],
                }
            },
        }
        proc = self._run(manifest, extra_args=["--aggregate"])
        self.assertEqual(proc.returncode, 0, f"Failed: {proc.stderr}")
        output = json.loads(proc.stdout)
        self.assertIn("clusters_reported", output)
        self.assertIn("overview", output)
        self.assertEqual(output["clusters_reported"], 1)
        self.assertEqual(output["overview"][0]["project_count"], 2)
        self.assertEqual(output["overview"][0]["pods_total"], 2)
        self.assertEqual(output["overview"][0]["pods_running"], 1)

    def test_malformed_manifest(self):
        proc = subprocess.run(
            [sys.executable, self.SCRIPT],
            input="not valid json{{{",
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 1)
        output = json.loads(proc.stdout)
        self.assertIn("error", output)

    def test_file_ref_error_in_pipeline(self):
        manifest = {
            "generated_at": "2026-01-01T00:00:00Z",
            "clusters": {
                "test": {
                    "context": "test",
                    "server": "https://test:6443",
                    "nodes_top": None,
                    "nodes_list": None,
                    "projects": None,
                    "namespaces": None,
                    "pods": {"$file": "/tmp/nonexistent-file.json"},
                    "errors": [],
                }
            },
        }
        proc = self._run(manifest)
        self.assertEqual(proc.returncode, 0)
        output = json.loads(proc.stdout)
        cluster = output["clusters"]["test"]
        self.assertIsNone(cluster["pods"])
        self.assertTrue(len(cluster["errors"]) > 0)

    def test_end_to_end_with_file_ref_and_aggregate(self):
        pods_text = (
            "NAMESPACE   APIVERSION   KIND   NAME    READY   STATUS    RESTARTS   AGE\n"
            "default     v1           Pod    web-1   1/1     Running   0          1d\n"
            "default     v1           Pod    web-2   1/1     Running   0          1d\n"
            "kube-sys    v1           Pod    dns-1   0/1     Failed    3          2d\n"
        )
        content = json.dumps([{"type": "text", "text": pods_text}])
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            manifest = {
                "generated_at": "2026-01-01T00:00:00Z",
                "clusters": {
                    "prod": {
                        "context": "prod",
                        "server": "https://prod:6443",
                        "nodes_top": None,
                        "nodes_list": None,
                        "projects": [{"name": "default"}, {"name": "kube-sys"}],
                        "namespaces": None,
                        "pods": {"$file": path},
                        "errors": [],
                    }
                },
            }
            proc = self._run(manifest, extra_args=["--aggregate"])
            self.assertEqual(proc.returncode, 0, f"Failed: {proc.stderr}")
            output = json.loads(proc.stdout)
            self.assertEqual(output["clusters_reported"], 1)
            ov = output["overview"][0]
            self.assertEqual(ov["pods_total"], 3)
            self.assertEqual(ov["pods_running"], 2)
            self.assertEqual(ov["project_count"], 2)
        finally:
            os.unlink(path)

    def test_plain_text_file_ref_with_aggregate(self):
        pods_text = (
            "NAMESPACE   APIVERSION   KIND   NAME    READY   STATUS    RESTARTS   AGE\n"
            "default     v1           Pod    web-1   1/1     Running   0          1d\n"
            "default     v1           Pod    web-2   0/1     Pending   0          1h\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(pods_text)
            path = f.name
        try:
            manifest = {
                "generated_at": "2026-01-01T00:00:00Z",
                "clusters": {
                    "prod": {
                        "context": "prod",
                        "server": "https://prod:6443",
                        "nodes_top": None,
                        "nodes_list": None,
                        "projects": [{"name": "default"}],
                        "namespaces": None,
                        "pods": {"$file": path},
                        "errors": [],
                    }
                },
            }
            proc = self._run(manifest, extra_args=["--aggregate"])
            self.assertEqual(proc.returncode, 0, f"Failed: {proc.stderr}")
            output = json.loads(proc.stdout)
            self.assertEqual(output["clusters_reported"], 1)
            ov = output["overview"][0]
            self.assertEqual(ov["pods_total"], 2)
            self.assertEqual(ov["pods_running"], 1)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
