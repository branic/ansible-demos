# Standalone HTTP service for the URI lesson

Run this service before presenting `demonstrate-uri-timeout.yml`. The teaching
playbook only sends requests; it does not provision or stop the server.

One Python container runs in the dedicated `async-timeouts-demo` OpenShift
project. A ConfigMap supplies the script, a ClusterIP Service provides access
from AAP, and an OpenShift Route provides access from the CLI. No VM, persistent
volume, custom image build, or additional Ansible collection is needed.

## Deploy

Log in with `oc` using an account allowed to create the dedicated project and
its resources. From the repository root:

```bash
oc apply -k demos/async-timeouts/service
oc -n async-timeouts-demo rollout status deployment/async-timeouts-http --timeout=120s
```

The manifests use the public Red Hat UBI Python 3.12 image pinned to an immutable
digest. The script uses only Python's standard library. It runs with OpenShift's
assigned non-root user and a read-only root filesystem. The tested OpenShift
version is 4.22.14; the container's Python version is 3.12.15.

[Kustomize](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/)
generates the ConfigMap from `slow_http_server.py` and adds a content hash to its
name. Reapplying unchanged files is idempotent. Updating the script changes the
referenced ConfigMap name and rolls out a new pod. Older generated ConfigMaps
can remain until the dedicated project is removed.

## Endpoints

| Path | Behavior |
| --- | --- |
| `/slow` | Wait three seconds, then return HTTP 200 and `{"message": "Delayed response completed"}` |
| `/healthz` | Return HTTP 200 immediately; used by readiness and liveness probes |

The server handles requests concurrently, so the deliberately slow request does
not delay health probes. There is no HTTP shutdown endpoint; OpenShift controls
the container lifecycle. SIGTERM stops the server gracefully.

The default inventory URL is:

```text
http://async-timeouts-http.async-timeouts-demo.svc.cluster.local:8080/slow
```

This requires AAP's execution pods to resolve and reach services in that project.
If AAP runs outside this cluster, override `async_timeouts_http_url` with the
Route URL. The service and Route use HTTP for this dummy lab response, so the
timeout lesson needs no certificate configuration.

For CLI execution, obtain the cluster-assigned Route hostname:

```bash
async_timeouts_route=$(oc -n async-timeouts-demo get route async-timeouts-http -o jsonpath='{.spec.host}')
curl --noproxy '*' --fail "http://${async_timeouts_route}/healthz"
ansible-playbook -i demos/async-timeouts/inventory \
  demos/async-timeouts/playbooks/demonstrate-uri-timeout.yml \
  -e "async_timeouts_http_url=http://${async_timeouts_route}/slow"
```

The tested lab Route is
`http://async-timeouts-http-async-timeouts-demo.apps-crc.testing/slow`.
Ansible does not use environment proxies for these lab requests. The first
request must time out; the second must succeed. A wrong, unavailable, or fast
endpoint fails the demonstration rather than passing as the expected timeout.

## Verify and clean up

```bash
oc -n async-timeouts-demo get deployment,pods,service,route
oc -n async-timeouts-demo logs deployment/async-timeouts-http
```

The service stays up across CLI and AAP jobs. Prepare it before recording and
remove it after the presentation:

```bash
oc delete -k demos/async-timeouts/service
```

This removes the dedicated project and all of its contents, including generated
ConfigMaps. Reserve that project for this demo. Cleanup does not remove AAP
templates or the shared AAP project.

The automated CLI harness launches this same script on an ephemeral loopback
port, manages it outside Ansible, and removes it afterward. Run only the URI
and static/check-mode checks with:

```bash
python3 demos/async-timeouts/tests/verify_cli.py --uri-only
```

That verification path does not require OpenShift or access to the deployed
service. It checks repeated timeout/success runs, rejection of a fast endpoint,
and removal of the local test server and temporary directory.
