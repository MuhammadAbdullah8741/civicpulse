# ADR 0003: Identify source by Git SHA and deploy published image digests

- Status: Accepted for implementation; live workflow evidence pending the first main run.
- Context: Mutable latest tags cannot identify the source or exact artifact running in a cluster.

## Decision

CD calls the complete ci.yml suite from the same commit through workflow_call.
The build-push job needs that suite to succeed. It builds both images, scans
both local images with the existing Trivy gate, and generates Syft SPDX JSON
SBOMs before any push. Each image receives OCI source and revision labels.

On main, images are published to GHCR under the full commit SHA and latest.
Release tags vMAJOR.MINOR.PATCH must refer to a commit reachable from main;
they trigger the same CI, scan, SBOM and deployment pipeline, adding version
tags. Release notes are published only after that pipeline succeeds.

The build job captures GHCR RepoDigests as job outputs. The deploy job uses
repository@sha256 references for both applications and the migration Job.
It renders the existing production overlay without editing checked-in
manifests. latest is never a deployment input.

## Credentials and scope

GITHUB_TOKEN is supplied by GitHub through its secrets context. Package write
permission exists only where publishing requires it; deployment receives
package read permission. Release-note creation receives contents write.
No personal registry password or Groq key is required for CI. The temporary
cluster gets a random database password, simulated triage and a short-lived
registry pull Secret, then is deleted even on failure. Secrets are passed via
stdin and are excluded from saved manifests and uploaded evidence.

## Consequences

A SHA tag identifies source, while a digest identifies exact image bytes.
Rebuilding the same commit can change bytes when external package repositories
change (including the existing apk upgrade step); therefore a SHA tag alone
is not a bit-for-bit reproducibility guarantee. Digests recorded per workflow
are the deployment authority. SBOMs describe the images built in that run.

The ephemeral cluster proves deployment and Ingress smoke behavior on a clean
runner. It does not host the public application or exercise a persistent
production database. Local scaling experiments remain separate evidence.
Registry tags are not an atomic pair: if one push fails, deployment is blocked,
but an already uploaded image can remain in GHCR. The failed run must not be
reported as a successful delivery.

No Cosign signing or signature-verification bonus is claimed by this ADR.

## Verification and rollback

The delivery-images artifact contains images.json, two SPDX SBOMs and Trivy
reports. delivery-deployment contains rendered production/migration resources,
pod image IDs, events, smoke output and HPA output. Save the successful run URL.

For an immediate operational rollback use rollout undo on the local backend
Deployment after identifying the desired history entry. For an auditable
rollback, render the previous source overlay with its recorded previous image
digests and apply it. Schema compatibility must be considered separately;
rolling back an application image does not undo a database migration.

References:
- https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows
- https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry
- https://github.com/anchore/syft
