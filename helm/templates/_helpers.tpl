{{/*
Expand the name of the chart.
*/}}
{{- define "opta-agent.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "opta-agent.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "opta-agent.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "opta-agent.labels" -}}
helm.sh/chart: {{ include "opta-agent.chart" . }}
{{ include "opta-agent.selectorLabels" . }}
{{ include "opta-agent.optaLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "opta-agent.selectorLabels" -}}
app.kubernetes.io/name: {{ include "opta-agent.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "opta-agent.optaLabels" -}}
opta.dev/module-name: {{ .Values.moduleName }}
opta.dev/layer-name: {{ .Values.layerName }}
opta.dev/environment-name: {{ .Values.environmentName }}
{{- end }}

{{/*Namespace name*/}}
{{- define "opta-agent.namespaceName" -}}
{{- .Values.layerName }}
{{- end }}
{{/*Service name*/}}
{{- define "opta-agent.serviceName" -}}
{{- .Values.moduleName }}
{{- end }}

