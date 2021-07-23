# Opta Agent

[![Artifact Hub](https://img.shields.io/endpoint?url=https://artifacthub.io/badge/repository/opta-agent)](https://artifacthub.io/packages/search?repo=opta-agent) ![Version: 0.1.0](https://img.shields.io/badge/Version-0.1.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 0.1.0](https://img.shields.io/badge/AppVersion-0.1.0-informational?style=flat-square)

## Requirements

Kubernetes: `>= 1.18.0 < 1.22.0`

## Maintainers

| Name | Email | Url |
| ---- | ------ | --- |
| Runx | info@runx.dev |  |

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| optaAgent.containerResourceLimits.cpu | string | `"200m"` |  |
| optaAgent.containerResourceLimits.memory | string | `"256Mi"` |  |
| optaAgent.containerResourceRequests.cpu | string | `"100m"` |  |
| optaAgent.containerResourceRequests.memory | string | `"128Mi"` |  |
| optaAgent.image | string | `"runx1/opta-agent:latest"` |  |
| optaAgent.namespace | string | `"opta-agent"` |  |
| optaAgent.token | string | `"nil"` |  |