# Standalone HTTP service for the URI lesson

Deploy this service before running `demonstrate-uri-timeout.yml`. The playbook
sends requests and leaves service management to the operator.

One Python container runs in the dedicated `async-timeouts-demo` OpenShift
project. A ConfigMap supplies the script, a ClusterIP Service provides access
from AAP, and an OpenShift Route provides access from the CLI.

## Deploy

Log in with `oc` using an account allowed to create the dedicated project and
its resources. From the repository root:

```bash
oc apply -k demos/async-timeouts/service
oc -n async-timeouts-demo rollout status deployment/async-timeouts-http --timeout=120s
```

## Endpoints

| Path | Behavior |
| --- | --- |
| `/slow` | Wait three seconds, then return HTTP 200 and `{"message": "Delayed response completed"}` |
| `/healthz` | Return HTTP 200 immediately; used by readiness and liveness probes |

The default inventory URL is:

```text
http://async-timeouts-http.async-timeouts-demo.svc.cluster.local:8080/slow
```

This requires AAP's execution pods to resolve and reach services in that project.
If AAP runs outside this cluster, override `async_timeouts_http_url` with the
Route URL. The service and Route use HTTP for the demonstration response.

For CLI execution, obtain the cluster-assigned Route hostname:

```bash
async_timeouts_route=$(oc -n async-timeouts-demo get route async-timeouts-http -o jsonpath='{.spec.host}')
curl --noproxy '*' --fail "http://${async_timeouts_route}/healthz"
ansible-playbook -i demos/async-timeouts/inventory \
  demos/async-timeouts/playbooks/demonstrate-uri-timeout.yml \
  -e "async_timeouts_http_url=http://${async_timeouts_route}/slow"
```

Confirm that the first request reports a socket timeout and the second succeeds.

## Verify and clean up

```bash
oc -n async-timeouts-demo get deployment,pods,service,route
oc -n async-timeouts-demo logs deployment/async-timeouts-http
```

The service stays available across CLI and AAP jobs. Remove it when finished:

```bash
oc delete -k demos/async-timeouts/service
```

This removes the dedicated project and all of its contents, including generated
ConfigMaps. Reserve that project for this demo. Cleanup does not remove AAP
templates or the shared AAP project.
