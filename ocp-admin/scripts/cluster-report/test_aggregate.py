#!/usr/bin/env python3

import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import aggregate


class TestParseCpu(unittest.TestCase):
    def test_whole_cores(self):
        self.assertEqual(aggregate.parse_cpu("4"), 4.0)

    def test_millicores(self):
        self.assertEqual(aggregate.parse_cpu("500m"), 0.5)

    def test_millicores_whole(self):
        self.assertEqual(aggregate.parse_cpu("4000m"), 4.0)

    def test_nanocores(self):
        self.assertAlmostEqual(aggregate.parse_cpu("1000000000n"), 1.0)

    def test_microcores(self):
        self.assertAlmostEqual(aggregate.parse_cpu("1000000u"), 1.0)

    def test_none(self):
        self.assertEqual(aggregate.parse_cpu(None), 0.0)

    def test_integer(self):
        self.assertEqual(aggregate.parse_cpu(8), 8.0)

    def test_fractional(self):
        self.assertEqual(aggregate.parse_cpu("0.5"), 0.5)


class TestParseMemory(unittest.TestCase):
    def test_gibibytes(self):
        self.assertEqual(aggregate.parse_memory("16Gi"), 16.0)

    def test_mebibytes(self):
        self.assertEqual(aggregate.parse_memory("16384Mi"), 16.0)

    def test_kibibytes(self):
        self.assertAlmostEqual(aggregate.parse_memory("16777216Ki"), 16.0)

    def test_raw_bytes(self):
        self.assertAlmostEqual(aggregate.parse_memory("17179869184"), 16.0, places=0)

    def test_tebibytes(self):
        self.assertEqual(aggregate.parse_memory("1Ti"), 1024.0)

    def test_decimal_gigabytes(self):
        val = aggregate.parse_memory("16G")
        self.assertAlmostEqual(val, 16000000000 / (1024 ** 3), places=1)

    def test_none(self):
        self.assertEqual(aggregate.parse_memory(None), 0.0)


class TestDetectNodeRole(unittest.TestCase):
    def test_worker(self):
        labels = {"node-role.kubernetes.io/worker": ""}
        self.assertEqual(aggregate.detect_node_role(labels), "worker")

    def test_control_plane(self):
        labels = {"node-role.kubernetes.io/control-plane": ""}
        self.assertEqual(aggregate.detect_node_role(labels), "control-plane")

    def test_master(self):
        labels = {"node-role.kubernetes.io/master": ""}
        self.assertEqual(aggregate.detect_node_role(labels), "master")

    def test_infra(self):
        labels = {"node-role.kubernetes.io/infra": ""}
        self.assertEqual(aggregate.detect_node_role(labels), "infra")

    def test_multiple_roles_prefers_control_plane(self):
        labels = {
            "node-role.kubernetes.io/worker": "",
            "node-role.kubernetes.io/control-plane": "",
        }
        self.assertEqual(aggregate.detect_node_role(labels), "control-plane")

    def test_no_role_labels(self):
        labels = {"kubernetes.io/hostname": "node-1"}
        self.assertEqual(aggregate.detect_node_role(labels), "worker")

    def test_empty_labels(self):
        self.assertEqual(aggregate.detect_node_role({}), "worker")

    def test_none_labels(self):
        self.assertEqual(aggregate.detect_node_role(None), "worker")


class TestDetectGpus(unittest.TestCase):
    def test_nvidia_gpu(self):
        alloc = {"cpu": "8", "memory": "32Gi", "nvidia.com/gpu": "2"}
        count, gpu_type = aggregate.detect_gpus(alloc)
        self.assertEqual(count, 2)
        self.assertEqual(gpu_type, "nvidia.com/gpu")

    def test_amd_gpu(self):
        alloc = {"amd.com/gpu": "4"}
        count, gpu_type = aggregate.detect_gpus(alloc)
        self.assertEqual(count, 4)
        self.assertEqual(gpu_type, "amd.com/gpu")

    def test_intel_gpu(self):
        alloc = {"intel.com/gpu": "1"}
        count, gpu_type = aggregate.detect_gpus(alloc)
        self.assertEqual(count, 1)
        self.assertEqual(gpu_type, "intel.com/gpu")

    def test_no_gpus(self):
        alloc = {"cpu": "8", "memory": "32Gi"}
        count, gpu_type = aggregate.detect_gpus(alloc)
        self.assertEqual(count, 0)
        self.assertEqual(gpu_type, "")

    def test_zero_gpus(self):
        alloc = {"nvidia.com/gpu": "0"}
        count, gpu_type = aggregate.detect_gpus(alloc)
        self.assertEqual(count, 0)
        self.assertEqual(gpu_type, "")

    def test_none_allocatable(self):
        count, gpu_type = aggregate.detect_gpus(None)
        self.assertEqual(count, 0)
        self.assertEqual(gpu_type, "")


class TestParseTabular(unittest.TestCase):
    def test_basic_table(self):
        text = "NAME      STATUS\nnode-1    Ready\nnode-2    NotReady"
        result = aggregate.parse_tabular(text)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["NAME"], "node-1")
        self.assertEqual(result[0]["STATUS"], "Ready")
        self.assertEqual(result[1]["NAME"], "node-2")
        self.assertEqual(result[1]["STATUS"], "NotReady")

    def test_multiword_header(self):
        text = "NAME      DISPLAY NAME   STATUS\nproj-1    My Project     Active"
        result = aggregate.parse_tabular(text)
        self.assertEqual(len(result), 1)
        self.assertIn("DISPLAY NAME", result[0])
        self.assertEqual(result[0]["DISPLAY NAME"], "My Project")

    def test_empty_input(self):
        self.assertEqual(aggregate.parse_tabular(""), [])
        self.assertEqual(aggregate.parse_tabular(None), [])

    def test_header_only(self):
        self.assertEqual(aggregate.parse_tabular("NAME   STATUS"), [])

    def test_short_data_line(self):
        text = "NAME      STATUS   LABELS\nnode-1    Ready"
        result = aggregate.parse_tabular(text)
        self.assertEqual(result[0]["NAME"], "node-1")
        self.assertEqual(result[0]["STATUS"], "Ready")
        self.assertEqual(result[0]["LABELS"], "")

    def test_varying_column_widths(self):
        text = "NAME          STATUS   AGE\nshort         OK       1d\nvery-long     Fail     30d"
        result = aggregate.parse_tabular(text)
        self.assertEqual(result[0]["NAME"], "short")
        self.assertEqual(result[1]["NAME"], "very-long")
        self.assertEqual(result[0]["STATUS"], "OK")
        self.assertEqual(result[1]["STATUS"], "Fail")

    def test_blank_lines_skipped(self):
        text = "NAME   STATUS\n\nnode-1   Ready\n\n"
        result = aggregate.parse_tabular(text)
        self.assertEqual(len(result), 1)

    def test_real_mcp_pod_header(self):
        text = (
            "NAMESPACE          APIVERSION   KIND   NAME                    "
            "READY   STATUS             RESTARTS   AGE\n"
            "openshift-dns      v1           Pod    dns-default-abc12       "
            "1/1     Running            0          5d\n"
            "aistor             v1           Pod    webhook-69496784f7      "
            "0/1     ErrImagePull       0          4d"
        )
        result = aggregate.parse_tabular(text)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["NAMESPACE"], "openshift-dns")
        self.assertEqual(result[0]["STATUS"], "Running")
        self.assertEqual(result[1]["STATUS"], "ErrImagePull")


class TestParseLabelsString(unittest.TestCase):
    def test_basic_labels(self):
        result = aggregate.parse_labels_string(
            "node-role.kubernetes.io/worker=,kubernetes.io/hostname=node-1"
        )
        self.assertEqual(result["node-role.kubernetes.io/worker"], "")
        self.assertEqual(result["kubernetes.io/hostname"], "node-1")

    def test_empty_string(self):
        self.assertEqual(aggregate.parse_labels_string(""), {})

    def test_none(self):
        self.assertEqual(aggregate.parse_labels_string(None), {})

    def test_label_with_value(self):
        result = aggregate.parse_labels_string("beta.kubernetes.io/arch=amd64")
        self.assertEqual(result["beta.kubernetes.io/arch"], "amd64")

    def test_none_literal(self):
        self.assertEqual(aggregate.parse_labels_string("<none>"), {})


class TestParsePodsTabular(unittest.TestCase):
    def test_basic_pods(self):
        text = (
            "NAMESPACE          APIVERSION   KIND   NAME            "
            "READY   STATUS             RESTARTS   AGE\n"
            "openshift-mon      v1           Pod    prometheus-0    "
            "1/1     Running            0          5d\n"
            "default            v1           Pod    failing-pod     "
            "0/1     CrashLoopBackOff   15         1d"
        )
        result = aggregate.parse_pods_tabular(text)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["namespace"], "openshift-mon")
        self.assertEqual(result[0]["status"], "Running")
        self.assertEqual(result[1]["namespace"], "default")
        self.assertEqual(result[1]["status"], "CrashLoopBackOff")

    def test_empty_input(self):
        self.assertEqual(aggregate.parse_pods_tabular(""), [])

    def test_various_statuses(self):
        for status in ["Running", "Pending", "Failed", "Succeeded",
                       "ErrImagePull", "ImagePullBackOff", "Completed"]:
            text = f"NAMESPACE   NAME     STATUS\ndefault     pod-x    {status}"
            result = aggregate.parse_pods_tabular(text)
            self.assertEqual(result[0]["status"], status, f"Failed for {status}")


class TestParseNodesListTabular(unittest.TestCase):
    def test_basic_nodes(self):
        text = (
            "APIVERSION   KIND   NAME       STATUS   ROLES    AGE   "
            "VERSION   LABELS\n"
            "v1           Node   worker-0   Ready    worker   30d   "
            "v1.28     node-role.kubernetes.io/worker=,kubernetes.io/hostname=worker-0"
        )
        result = aggregate.parse_nodes_list_tabular(text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["metadata"]["name"], "worker-0")
        self.assertIn("node-role.kubernetes.io/worker",
                       result[0]["metadata"]["labels"])

    def test_role_from_roles_column(self):
        text = (
            "APIVERSION   KIND   NAME       STATUS   ROLES           AGE   "
            "VERSION   LABELS\n"
            "v1           Node   master-0   Ready    control-plane   30d   "
            "v1.28     kubernetes.io/hostname=master-0"
        )
        result = aggregate.parse_nodes_list_tabular(text)
        labels = result[0]["metadata"]["labels"]
        role = aggregate.detect_node_role(labels)
        self.assertEqual(role, "control-plane")

    def test_no_allocatable_data(self):
        text = "APIVERSION   KIND   NAME   STATUS   ROLES    LABELS\nv1           Node   n1     Ready    worker   app=test"
        result = aggregate.parse_nodes_list_tabular(text)
        self.assertEqual(result[0]["status"], {})


class TestParseNodesTopTabular(unittest.TestCase):
    def test_basic_top(self):
        text = (
            "NAME     CPU(cores)   CPU(%)   MEMORY(bytes)   MEMORY(%)\n"
            "node-1   4000m        50%      16Gi            50%\n"
            "node-2   2000m        25%      8Gi             25%"
        )
        result = aggregate.parse_nodes_top_tabular(text)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "node-1")
        self.assertEqual(result[0]["cpu_usage"], "4000m")
        self.assertEqual(result[0]["memory_usage"], "16Gi")
        self.assertEqual(result[1]["name"], "node-2")

    def test_empty(self):
        self.assertEqual(aggregate.parse_nodes_top_tabular(""), [])


class TestParseProjectsTabular(unittest.TestCase):
    def test_basic(self):
        text = (
            "APIVERSION                KIND      NAME         DISPLAY NAME   STATUS   LABELS\n"
            "project.openshift.io/v1   Project   my-project   My Project     Active   app=test\n"
            "project.openshift.io/v1   Project   default                     Active   <none>"
        )
        result = aggregate.parse_projects_tabular(text)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "my-project")
        self.assertEqual(result[1]["name"], "default")

    def test_empty(self):
        self.assertEqual(aggregate.parse_projects_tabular(""), [])


class TestParseNamespacesTabular(unittest.TestCase):
    def test_basic(self):
        text = (
            "APIVERSION   KIND        NAME          STATUS   AGE   LABELS\n"
            "v1           Namespace   kube-system   Active   90d   kubernetes.io/metadata.name=kube-system\n"
            "v1           Namespace   default       Active   90d   kubernetes.io/metadata.name=default"
        )
        result = aggregate.parse_namespaces_tabular(text)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "kube-system")
        self.assertEqual(result[1]["name"], "default")


class TestClassifyPodStatus(unittest.TestCase):
    def test_running(self):
        pod = {"status": {"phase": "Running", "containerStatuses": []}}
        self.assertEqual(aggregate.classify_pod_status(pod), "Running")

    def test_pending(self):
        pod = {"status": {"phase": "Pending"}}
        self.assertEqual(aggregate.classify_pod_status(pod), "Pending")

    def test_succeeded(self):
        pod = {"status": {"phase": "Succeeded"}}
        self.assertEqual(aggregate.classify_pod_status(pod), "Succeeded")

    def test_failed(self):
        pod = {"status": {"phase": "Failed"}}
        self.assertEqual(aggregate.classify_pod_status(pod), "Failed")

    def test_completed_maps_to_succeeded(self):
        pod = {"status": {"phase": "Completed"}}
        self.assertEqual(aggregate.classify_pod_status(pod), "Succeeded")

    def test_crashloopbackoff_override(self):
        pod = {
            "status": {
                "phase": "Running",
                "containerStatuses": [
                    {"state": {"waiting": {"reason": "CrashLoopBackOff"}}}
                ],
            }
        }
        self.assertEqual(aggregate.classify_pod_status(pod), "CrashLoopBackOff")

    def test_imagepullbackoff_override(self):
        pod = {
            "status": {
                "phase": "Pending",
                "containerStatuses": [
                    {"state": {"waiting": {"reason": "ImagePullBackOff"}}}
                ],
            }
        }
        self.assertEqual(aggregate.classify_pod_status(pod), "ImagePullBackOff")

    def test_errimagepull(self):
        pod = {
            "status": {
                "phase": "Pending",
                "containerStatuses": [
                    {"state": {"waiting": {"reason": "ErrImagePull"}}}
                ],
            }
        }
        self.assertEqual(aggregate.classify_pod_status(pod), "ErrImagePull")

    def test_flat_status_string(self):
        pod = {"name": "my-pod", "namespace": "default", "status": "CrashLoopBackOff"}
        self.assertEqual(aggregate.classify_pod_status(pod), "CrashLoopBackOff")

    def test_unknown_default(self):
        pod = {"status": {}}
        self.assertEqual(aggregate.classify_pod_status(pod), "Unknown")


class TestAggregatePodsByNamespace(unittest.TestCase):
    def test_basic_aggregation(self):
        pods = [
            {"metadata": {"namespace": "ns-a"}, "status": {"phase": "Running"}},
            {"metadata": {"namespace": "ns-a"}, "status": {"phase": "Running"}},
            {"metadata": {"namespace": "ns-b"}, "status": {"phase": "Pending"}},
        ]
        result = aggregate.aggregate_pods_by_namespace(pods)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["namespace"], "ns-a")
        self.assertEqual(result[0]["pods_total"], 2)
        self.assertEqual(result[0]["running"], 2)
        self.assertEqual(result[1]["namespace"], "ns-b")
        self.assertEqual(result[1]["pods_total"], 1)
        self.assertEqual(result[1]["pending"], 1)

    def test_top_10_limit(self):
        pods = []
        for i in range(15):
            for j in range(15 - i):
                pods.append({
                    "metadata": {"namespace": f"ns-{i:02d}"},
                    "status": {"phase": "Running"},
                })
        result = aggregate.aggregate_pods_by_namespace(pods)
        self.assertEqual(len(result), 10)
        self.assertEqual(result[0]["pods_total"], 15)
        self.assertEqual(result[9]["pods_total"], 6)

    def test_empty_pods(self):
        self.assertEqual(aggregate.aggregate_pods_by_namespace([]), [])
        self.assertEqual(aggregate.aggregate_pods_by_namespace(None), [])

    def test_flat_pod_structure(self):
        pods = [
            {"namespace": "ns-a", "status": "Running"},
            {"namespace": "ns-a", "status": "Failed"},
        ]
        result = aggregate.aggregate_pods_by_namespace(pods)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["running"], 1)
        self.assertEqual(result[0]["failed"], 1)


class TestProcessCluster(unittest.TestCase):
    def _make_cluster(self, **overrides):
        base = {
            "context": "test-cluster",
            "server": "https://api.test.example.com:6443",
            "nodes_top": None,
            "nodes_list": None,
            "projects": None,
            "namespaces": None,
            "pods": None,
            "errors": [],
        }
        base.update(overrides)
        return base

    def test_full_data(self):
        cluster = self._make_cluster(
            nodes_top=[
                {"name": "node-1", "cpu_usage": "4000m", "memory_usage": "16Gi"},
            ],
            nodes_list=[
                {
                    "metadata": {
                        "name": "node-1",
                        "labels": {"node-role.kubernetes.io/worker": ""},
                    },
                    "status": {
                        "allocatable": {"cpu": "8", "memory": "32Gi", "nvidia.com/gpu": "2"},
                    },
                }
            ],
            projects=[{"name": f"proj-{i}"} for i in range(5)],
            pods=[
                {"metadata": {"namespace": "default"}, "status": {"phase": "Running"}},
                {"metadata": {"namespace": "default"}, "status": {"phase": "Running"}},
                {"metadata": {"namespace": "kube-system"}, "status": {"phase": "Failed"}},
            ],
        )
        result = aggregate.process_cluster(cluster)

        ov = result["overview"]
        self.assertEqual(ov["node_count"], 1)
        self.assertEqual(ov["cpu_used_cores"], 4.0)
        self.assertEqual(ov["cpu_total_cores"], 8.0)
        self.assertEqual(ov["cpu_percent"], 50)
        self.assertEqual(ov["gpu_total"], 2)
        self.assertEqual(ov["project_count"], 5)
        self.assertEqual(ov["pods_running"], 2)
        self.assertEqual(ov["pods_total"], 3)
        self.assertTrue(ov["metrics_available"])

        self.assertEqual(result["pod_status"]["Running"], 2)
        self.assertEqual(result["pod_status"]["Failed"], 1)
        self.assertEqual(len(result["top_namespaces"]), 2)

    def test_no_metrics_server(self):
        cluster = self._make_cluster(
            nodes_top=None,
            nodes_list=[
                {
                    "metadata": {"name": "node-1", "labels": {}},
                    "status": {"allocatable": {"cpu": "8", "memory": "32Gi"}},
                }
            ],
        )
        result = aggregate.process_cluster(cluster)

        ov = result["overview"]
        self.assertFalse(ov["metrics_available"])
        self.assertIsNone(ov["cpu_used_cores"])
        self.assertIsNone(ov["cpu_percent"])
        self.assertEqual(ov["cpu_total_cores"], 8.0)

    def test_empty_cluster(self):
        cluster = self._make_cluster()
        result = aggregate.process_cluster(cluster)

        ov = result["overview"]
        self.assertEqual(ov["node_count"], 0)
        self.assertEqual(ov["pods_total"], 0)
        self.assertEqual(ov["project_count"], 0)
        self.assertEqual(result["pod_status"], {})
        self.assertEqual(result["top_namespaces"], [])

    def test_namespaces_fallback(self):
        cluster = self._make_cluster(
            projects=None,
            namespaces=[{"name": f"ns-{i}"} for i in range(3)],
        )
        result = aggregate.process_cluster(cluster)
        self.assertEqual(result["overview"]["project_count"], 3)

    def test_tabular_pods_input(self):
        tabular_pods = (
            "NAMESPACE      APIVERSION   KIND   NAME    "
            "READY   STATUS    RESTARTS   AGE\n"
            "default        v1           Pod    pod-1   "
            "1/1     Running   0          1d\n"
            "default        v1           Pod    pod-2   "
            "1/1     Running   0          1d\n"
            "kube-system    v1           Pod    pod-3   "
            "0/1     Failed    5          3d"
        )
        cluster = self._make_cluster(pods=tabular_pods)
        result = aggregate.process_cluster(cluster)
        self.assertEqual(result["overview"]["pods_total"], 3)
        self.assertEqual(result["overview"]["pods_running"], 2)
        self.assertEqual(result["pod_status"]["Running"], 2)
        self.assertEqual(result["pod_status"]["Failed"], 1)
        self.assertEqual(len(result["top_namespaces"]), 2)

    def test_tabular_projects_input(self):
        tabular_projects = (
            "APIVERSION                KIND      NAME       DISPLAY NAME   STATUS   LABELS\n"
            "project.openshift.io/v1   Project   proj-1     Project 1      Active   <none>\n"
            "project.openshift.io/v1   Project   proj-2     Project 2      Active   <none>\n"
            "project.openshift.io/v1   Project   proj-3                    Active   <none>"
        )
        cluster = self._make_cluster(projects=tabular_projects)
        result = aggregate.process_cluster(cluster)
        self.assertEqual(result["overview"]["project_count"], 3)

    def test_mixed_tabular_and_json(self):
        tabular_pods = (
            "NAMESPACE   NAME    STATUS\n"
            "default     pod-1   Running"
        )
        json_nodes = [{
            "metadata": {"name": "n1", "labels": {}},
            "status": {"allocatable": {"cpu": "4", "memory": "16Gi"}},
        }]
        cluster = self._make_cluster(
            pods=tabular_pods, nodes_list=json_nodes,
            projects=[{"name": "proj-1"}])
        result = aggregate.process_cluster(cluster)
        self.assertEqual(result["overview"]["pods_total"], 1)
        self.assertEqual(result["overview"]["node_count"], 1)
        self.assertEqual(result["overview"]["project_count"], 1)

    def test_tabular_nodes_list_known_limitation(self):
        tabular_nodes = (
            "APIVERSION   KIND   NAME       STATUS   ROLES    AGE   "
            "VERSION   LABELS\n"
            "v1           Node   worker-0   Ready    worker   30d   "
            "v1.28     node-role.kubernetes.io/worker="
        )
        cluster = self._make_cluster(nodes_list=tabular_nodes)
        result = aggregate.process_cluster(cluster)
        self.assertEqual(result["overview"]["node_count"], 1)
        self.assertEqual(result["overview"]["cpu_total_cores"], 0.0)
        self.assertEqual(result["overview"]["memory_total_gib"], 0.0)
        self.assertEqual(result["overview"]["gpu_total"], 0)
        self.assertEqual(result["nodes"][0]["role"], "worker")

    def test_tabular_nodes_top_with_json_nodes_list(self):
        tabular_top = (
            "NAME     CPU(cores)   CPU(%)   MEMORY(bytes)   MEMORY(%)\n"
            "node-1   4000m        50%      16Gi            50%"
        )
        json_nodes = [{
            "metadata": {"name": "node-1",
                         "labels": {"node-role.kubernetes.io/worker": ""}},
            "status": {"allocatable": {"cpu": "8", "memory": "32Gi"}},
        }]
        cluster = self._make_cluster(
            nodes_top=tabular_top, nodes_list=json_nodes)
        result = aggregate.process_cluster(cluster)
        self.assertEqual(result["overview"]["cpu_used_cores"], 4.0)
        self.assertEqual(result["overview"]["cpu_total_cores"], 8.0)
        self.assertTrue(result["overview"]["metrics_available"])


class TestComputeTotals(unittest.TestCase):
    def test_two_clusters(self):
        overview = [
            {
                "node_count": 3, "cpu_used_cores": 10.0, "cpu_total_cores": 24.0,
                "memory_used_gib": 40.0, "memory_total_gib": 96.0,
                "gpu_total": 2, "project_count": 10,
                "pods_running": 50, "pods_total": 60,
            },
            {
                "node_count": 5, "cpu_used_cores": 20.0, "cpu_total_cores": 40.0,
                "memory_used_gib": 60.0, "memory_total_gib": 160.0,
                "gpu_total": 4, "project_count": 20,
                "pods_running": 100, "pods_total": 120,
            },
        ]
        totals = aggregate.compute_totals(overview)
        self.assertEqual(totals["node_count"], 8)
        self.assertEqual(totals["cpu_used_cores"], 30.0)
        self.assertEqual(totals["cpu_total_cores"], 64.0)
        self.assertEqual(totals["cpu_percent"], 47)
        self.assertEqual(totals["memory_used_gib"], 100.0)
        self.assertEqual(totals["memory_total_gib"], 256.0)
        self.assertEqual(totals["memory_percent"], 39)
        self.assertEqual(totals["gpu_total"], 6)
        self.assertEqual(totals["project_count"], 30)
        self.assertEqual(totals["pods_running"], 150)
        self.assertEqual(totals["pods_total"], 180)

    def test_mixed_metrics_availability(self):
        overview = [
            {"node_count": 3, "cpu_used_cores": 10.0, "cpu_total_cores": 24.0,
             "memory_used_gib": 40.0, "memory_total_gib": 96.0,
             "gpu_total": 0, "project_count": 5, "pods_running": 20, "pods_total": 25},
            {"node_count": 2, "cpu_used_cores": None, "cpu_total_cores": 16.0,
             "memory_used_gib": None, "memory_total_gib": 64.0,
             "gpu_total": 0, "project_count": 3, "pods_running": 10, "pods_total": 15},
        ]
        totals = aggregate.compute_totals(overview)
        self.assertEqual(totals["cpu_used_cores"], 10.0)
        self.assertEqual(totals["cpu_total_cores"], 40.0)


class TestDetectAttentionItems(unittest.TestCase):
    def test_high_cpu(self):
        overview = [{"cluster": "prod", "cpu_percent": 90, "memory_percent": 50,
                      "metrics_available": True, "server": "x"}]
        per_cluster = {"prod": {"nodes": [], "pod_status": {}, "errors": []}}
        items = aggregate.detect_attention_items(overview, per_cluster)
        self.assertTrue(any("CPU usage at 90%" in i for i in items))

    def test_failed_pods(self):
        overview = [{"cluster": "prod", "cpu_percent": 50, "memory_percent": 50,
                      "metrics_available": True, "server": "x"}]
        per_cluster = {"prod": {"nodes": [], "pod_status": {"Failed": 3}, "errors": []}}
        items = aggregate.detect_attention_items(overview, per_cluster)
        self.assertTrue(any("3 pods in Failed" in i for i in items))

    def test_pending_pods(self):
        overview = [{"cluster": "dev", "cpu_percent": 30, "memory_percent": 30,
                      "metrics_available": True, "server": "x"}]
        per_cluster = {"dev": {"nodes": [], "pod_status": {"Pending": 5}, "errors": []}}
        items = aggregate.detect_attention_items(overview, per_cluster)
        self.assertTrue(any("5 pods in Pending" in i for i in items))

    def test_crashloopbackoff(self):
        overview = [{"cluster": "prod", "cpu_percent": None, "memory_percent": None,
                      "metrics_available": False, "server": "x"}]
        per_cluster = {"prod": {"nodes": [], "pod_status": {"CrashLoopBackOff": 2}, "errors": []}}
        items = aggregate.detect_attention_items(overview, per_cluster)
        self.assertTrue(any("CrashLoopBackOff" in i for i in items))
        self.assertTrue(any("Metrics Server" in i for i in items))

    def test_no_issues(self):
        overview = [{"cluster": "prod", "cpu_percent": 30, "memory_percent": 40,
                      "metrics_available": True, "server": "x"}]
        per_cluster = {"prod": {"nodes": [], "pod_status": {"Running": 10}, "errors": []}}
        items = aggregate.detect_attention_items(overview, per_cluster)
        self.assertEqual(items, [])

    def test_node_level_high_usage(self):
        overview = [{"cluster": "prod", "cpu_percent": 50, "memory_percent": 50,
                      "metrics_available": True, "server": "x"}]
        per_cluster = {"prod": {
            "nodes": [{"name": "node-1", "cpu_used": 7.5, "cpu_total": 8.0,
                        "memory_used": 5.0, "memory_total": 32.0}],
            "pod_status": {}, "errors": [],
        }}
        items = aggregate.detect_attention_items(overview, per_cluster)
        self.assertTrue(any("node-1 CPU at 94%" in i for i in items))


class TestFullPipeline(unittest.TestCase):

    def test_two_cluster_report(self):
        input_data = {
            "generated_at": "2026-03-03T14:30:00Z",
            "clusters": {
                "prod-us": {
                    "context": "prod-us",
                    "server": "https://api.prod-us.example.com:6443",
                    "nodes_top": [
                        {"name": "node-1", "cpu_usage": "4000m", "memory_usage": "16Gi"},
                        {"name": "node-2", "cpu_usage": "3000m", "memory_usage": "12Gi"},
                    ],
                    "nodes_list": [
                        {
                            "metadata": {"name": "node-1",
                                         "labels": {"node-role.kubernetes.io/worker": ""}},
                            "status": {"allocatable": {"cpu": "8", "memory": "32Gi",
                                                       "nvidia.com/gpu": "2"}},
                        },
                        {
                            "metadata": {"name": "node-2",
                                         "labels": {"node-role.kubernetes.io/worker": ""}},
                            "status": {"allocatable": {"cpu": "8", "memory": "32Gi"}},
                        },
                    ],
                    "projects": [{"name": f"proj-{i}"} for i in range(10)],
                    "pods": [
                        {"metadata": {"namespace": "app"}, "status": {"phase": "Running"}}
                        for _ in range(8)
                    ] + [
                        {"metadata": {"namespace": "app"}, "status": {"phase": "Failed"}}
                        for _ in range(2)
                    ],
                    "errors": [],
                },
                "dev-eu": {
                    "context": "dev-eu",
                    "server": "https://api.dev-eu.example.com:6443",
                    "nodes_top": None,
                    "nodes_list": [
                        {
                            "metadata": {"name": "dev-1",
                                         "labels": {"node-role.kubernetes.io/worker": ""}},
                            "status": {"allocatable": {"cpu": "4", "memory": "16Gi"}},
                        },
                    ],
                    "projects": [{"name": f"ns-{i}"} for i in range(3)],
                    "pods": [
                        {"metadata": {"namespace": "default"}, "status": {"phase": "Running"}}
                        for _ in range(5)
                    ],
                    "errors": [],
                },
            },
        }

        script_path = Path(__file__).parent / "aggregate.py"
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, f"Script failed: {proc.stderr}")

        output = json.loads(proc.stdout)

        self.assertEqual(output["generated_at"], "2026-03-03T14:30:00Z")
        self.assertEqual(output["clusters_reported"], 2)
        self.assertEqual(output["clusters_failed"], 0)
        self.assertEqual(len(output["overview"]), 2)

        prod = next(o for o in output["overview"] if o["cluster"] == "prod-us")
        self.assertEqual(prod["node_count"], 2)
        self.assertEqual(prod["gpu_total"], 2)
        self.assertTrue(prod["metrics_available"])
        self.assertEqual(prod["pods_running"], 8)
        self.assertEqual(prod["pods_total"], 10)

        dev = next(o for o in output["overview"] if o["cluster"] == "dev-eu")
        self.assertFalse(dev["metrics_available"])
        self.assertIsNone(dev["cpu_used_cores"])
        self.assertEqual(dev["node_count"], 1)

        self.assertTrue(any("Failed" in a for a in output["attention"]))

        self.assertEqual(output["totals"]["node_count"], 3)
        self.assertEqual(output["totals"]["gpu_total"], 2)

    def test_malformed_input(self):
        script_path = Path(__file__).parent / "aggregate.py"
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            input="not valid json{{{",
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 1)
        output = json.loads(proc.stdout)
        self.assertIn("error", output)

    def test_empty_clusters(self):
        script_path = Path(__file__).parent / "aggregate.py"
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            input=json.dumps({"clusters": {}}),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 1)
        output = json.loads(proc.stdout)
        self.assertIn("error", output)

    def test_tabular_input_pipeline(self):
        input_data = {
            "generated_at": "2026-03-03T15:00:00Z",
            "clusters": {
                "prod": {
                    "context": "prod",
                    "server": "https://api.prod.example.com:6443",
                    "nodes_top": (
                        "NAME     CPU(cores)   CPU(%)   MEMORY(bytes)   MEMORY(%)\n"
                        "node-1   4000m        50%      16Gi            50%"
                    ),
                    "nodes_list": [
                        {
                            "metadata": {"name": "node-1",
                                         "labels": {"node-role.kubernetes.io/worker": ""}},
                            "status": {"allocatable": {"cpu": "8", "memory": "32Gi"}},
                        }
                    ],
                    "projects": (
                        "APIVERSION                KIND      NAME     DISPLAY NAME   STATUS   LABELS\n"
                        "project.openshift.io/v1   Project   proj-1                  Active   <none>\n"
                        "project.openshift.io/v1   Project   proj-2                  Active   <none>"
                    ),
                    "pods": (
                        "NAMESPACE      NAME    STATUS\n"
                        "default        pod-1   Running\n"
                        "default        pod-2   Running\n"
                        "kube-system    pod-3   Pending"
                    ),
                    "namespaces": None,
                    "errors": [],
                }
            },
        }
        script_path = Path(__file__).parent / "aggregate.py"
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            input=json.dumps(input_data),
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, f"Script failed: {proc.stderr}")
        output = json.loads(proc.stdout)
        self.assertEqual(output["clusters_reported"], 1)
        prod = output["overview"][0]
        self.assertEqual(prod["pods_total"], 3)
        self.assertEqual(prod["pods_running"], 2)
        self.assertEqual(prod["project_count"], 2)
        self.assertEqual(prod["cpu_used_cores"], 4.0)
        self.assertEqual(prod["cpu_total_cores"], 8.0)
        self.assertTrue(prod["metrics_available"])
        self.assertTrue(any("Pending" in a for a in output["attention"]))


if __name__ == "__main__":
    unittest.main()
