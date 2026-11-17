{{/*
Common helpers for the ai-coach-mastery chart.
*/}}

{{- define "acm.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "acm.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "acm.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "acm.labels" -}}
app.kubernetes.io/name: {{ include "acm.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/* Resolve a fully qualified image reference, honoring global.imageRegistry */}}
{{- define "acm.image" -}}
{{- $registry := .root.Values.global.imageRegistry -}}
{{- if $registry -}}
{{ printf "%s/%s:%s" $registry .svc.image .svc.tag }}
{{- else -}}
{{ printf "%s:%s" .svc.image .svc.tag }}
{{- end -}}
{{- end -}}
