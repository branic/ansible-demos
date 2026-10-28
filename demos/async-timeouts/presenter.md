# Presenter runbook

Use approximately **15 minutes of demonstration** within the 45-minute teaching
content target. The remaining teaching time covers motivation, YAML explanation,
reusable-role design, takeaways, and discussion. This runbook does not replace a
full rehearsal against the presentation.

## Before recording

- Review the [completed AAP validation](aap/README.md#completed-lab-validation)
  and synchronize the demonstrated revision. Repeat acceptance checks when
  changing code, platform, or EE. Run the CLI harness and strict lint.
- Keep inventory defaults and fixed template policies. Confirm type Run, blank
  limits/tags, one slice, and no surveys or privilege escalation.
- [Deploy the HTTP container](service/README.md#deploy) before the meeting and
  check `/healthz`. AAP uses its ClusterIP URL; CLI requests use the Route URL.
  Keep service setup and cleanup outside the teaching sequence.
- Open each playbook and the role's collection task file in an editor with
  readable YAML. Open the named templates and workflow in AAP.
- Keep a completed validated run available for reference if AAP startup is slow.
  Clearly identify it as a previous run if shown.

## Demonstration sequence

| Time | Action | Explain or show |
| --- | --- | --- |
| 0:00–2:00 | Run `demo_demonstrate_uri_timeout` | Two requests to the prepared HTTP service: socket timeout, expected rescue, then success with a longer timeout |
| 2:00–4:00 | Run `demo_demonstrate_positive_poll` | `async` sets execution allowance; positive `poll` collects at the launch task; only demo1 continues |
| 4:00–6:00 | Run `demo_demonstrate_separate_poll` | All hosts reach `BEFORE COLLECTION`; the registered job ID connects launch to explicit polling |
| 6:00–8:00 | Show `demonstrate-role.yml` and `async_result/tasks/collect.yml` | The repeated polling and error processing now live behind one small role interface |
| 8:00–10:30 | Run `demo_collect_async_fail_host` | demo1 succeeds; demo2 times out without a command rc; demo3 returns rc 7 and stderr; job Failed |
| 10:30–13:30 | Run `demo_workflow_async_collect_and_exclude` | Same outcomes; rescued failures; artifact with demo2/demo3; Successful jobs; downstream action only on demo1 |
| 13:30–15:00 | Open reference role and recap observations | Refer to the earlier workflow pattern; point to `collect_async_status` for broader capabilities |

Use launch/startup time for explanation. Timing targets are a rehearsal budget,
and interactive questions can expand this segment. Validated AAP jobs took
approximately 9.7 seconds for URI, 20 seconds for each mixed async example, and
24 seconds for the complete workflow, excluding queue time.

## Observations to emphasize

- A command returning an async job ID has launched; it has not yet succeeded.
- A socket timeout, async execution limit, and exhausted status polling are
  different boundaries. A polling limit does not cancel a command.
- Retry messages can be normal while a job is unfinished. Final results and
  recap counts determine the outcome.
- The default linear strategy can keep demo1 waiting while demo2 is polled.
  Host-specific failure handling lets healthy hosts continue after collection.
- `fail_host` stops affected hosts and fails the job. `collect_and_exclude`
  rescues, records, and ends affected hosts without leaving native failures.
- The failed-host list is an output artifact. Reference its established workflow
  handoff briefly; concentrate on collecting and processing async results.
- These are separate Ansible host identities inside one EE, not three machines.
- In the validated EE, raw `finished` values are 0/1 and summary return codes
  appear as strings. The timeout has no command return code. Use these observed
  results when choosing illustrative YAML and output screenshots.

## After lab validation

Align illustrative slide excerpts with the exact validated playbooks and role
inputs. Use controller output from the recorded EE version for expected messages,
timeout behavior, and recaps. Rehearse the complete teaching and demo sequence
against the 45-minute target; adjust spoken explanation before shortening the
technical examples or changing their behavior.
