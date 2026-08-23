"""Auto-generated enum literal aliases (uniform request + response).

DO NOT EDIT — regenerated on every ``typegen.sh`` run from the
*un-relaxed* OpenAPI spec. See ``scripts/emit_response_enums.py``
and ``mini/runbooks/api-contract.md`` § 3 for the design.

Each alias is a ``typing.Literal[...]`` of the wire-format values
the API currently accepts (request-side) or emits (response-side)
for the named ``<SchemaName><Property>`` field. Naming is
stable: it does not depend on ``datamodel-codegen``'s suffixed
names (``Status1``, ``Type5``…) which shift on every spec change.

Response-DTO fields decode to plain ``str`` in ``_generated.py``
(Postel-tolerant on receive). Request-DTO fields keep strict
validation through the corresponding ``StrEnum`` in
``_generated.py`` (strict on send). These aliases give SDK
callers a single canonical name they can annotate against in
either direction.
"""

from __future__ import annotations

from typing import Literal

AddIncidentUpdateRequestNewStatus = Literal[
    "WATCHING", "TRIGGERED", "CONFIRMED", "RESOLVED"
]
AdminAddSubscriberRequestChannel = Literal["EMAIL", "SMS", "WEBHOOK"]
AffectedComponentStatus = Literal[
    "OPERATIONAL",
    "DEGRADED_PERFORMANCE",
    "PARTIAL_OUTAGE",
    "MAJOR_OUTAGE",
    "UNDER_MAINTENANCE",
]
AlertChannelDtoChannelType = Literal[
    "email",
    "webhook",
    "slack",
    "pagerduty",
    "opsgenie",
    "teams",
    "discord",
    "telegram",
    "google_chat",
    "pushover",
    "mattermost",
    "splunk_oncall",
    "pushbullet",
    "linear",
    "incident_io",
    "rootly",
    "zapier",
    "datadog",
    "jira",
    "gitlab",
    "sms",
    "phone_call",
]
AlertChannelDtoManagedBy = Literal["DASHBOARD", "CLI", "TERRAFORM", "MCP", "API"]
AlertDeliveryDtoEventType = Literal[
    "INCIDENT_CREATED", "INCIDENT_RESOLVED", "INCIDENT_REOPENED"
]
AlertDeliveryDtoStatus = Literal[
    "PENDING",
    "DELIVERED",
    "RETRY_PENDING",
    "FAILED",
    "CANCELLED",
    "SKIPPED_NO_CREDIT",
    "SKIPPED_UNVERIFIED",
    "SKIPPED_OPTED_OUT",
    "SKIPPED_RATE_LIMITED",
]
ApiKeyAuthConfigType = Literal["api_key"]
AssertionResultDtoSeverity = Literal["fail", "warn"]
AssertionTestResultDtoAssertionType = Literal[
    "status_code",
    "response_time",
    "body_contains",
    "json_path",
    "header_value",
    "regex_body",
    "dns_resolves",
    "dns_response_time",
    "dns_expected_ips",
    "dns_expected_cname",
    "dns_record_contains",
    "dns_record_equals",
    "dns_txt_contains",
    "dns_min_answers",
    "dns_max_answers",
    "dns_response_time_warn",
    "dns_ttl_low",
    "dns_ttl_high",
    "mcp_connects",
    "mcp_response_time",
    "mcp_has_capability",
    "mcp_tool_available",
    "mcp_min_tools",
    "mcp_protocol_version",
    "mcp_response_time_warn",
    "mcp_tool_count_changed",
    "ssl_expiry",
    "response_size",
    "redirect_count",
    "redirect_target",
    "response_time_warn",
    "tcp_connects",
    "tcp_response_time",
    "tcp_response_time_warn",
    "icmp_reachable",
    "icmp_response_time",
    "icmp_response_time_warn",
    "icmp_packet_loss",
    "heartbeat_received",
    "heartbeat_max_interval",
    "heartbeat_interval_drift",
    "heartbeat_payload_contains",
]
AssertionTestResultDtoSeverity = Literal["fail", "warn"]
BasicAuthConfigType = Literal["basic"]
BearerAuthConfigType = Literal["bearer"]
BodyContainsAssertionType = Literal["body_contains"]
BulkMonitorActionRequestAction = Literal[
    "PAUSE", "RESUME", "DELETE", "ADD_TAG", "REMOVE_TAG"
]
ChangeRoleRequestOrgRole = Literal["OWNER", "ADMIN", "MEMBER"]
ChangeStatusRequestStatus = Literal[
    "INVITED", "ACTIVE", "SUSPENDED", "LEFT", "REMOVED", "DECLINED"
]
CodeCheckType = Literal["code"]
ConfirmationPolicyType = Literal["multi_region"]
CreateAlertChannelRequestManagedBy = Literal[
    "DASHBOARD", "CLI", "TERRAFORM", "MCP", "API"
]
CreateAssertionRequestSeverity = Literal["fail", "warn"]
CreateInviteRequestRoleOffered = Literal["OWNER", "ADMIN", "MEMBER"]
CreateManualIncidentRequestSeverity = Literal["DOWN", "DEGRADED", "MAINTENANCE"]
CreateMonitorRequestManagedBy = Literal["DASHBOARD", "CLI", "TERRAFORM", "MCP", "API"]
CreateMonitorRequestType = Literal[
    "HTTP", "DNS", "MCP_SERVER", "TCP", "ICMP", "HEARTBEAT", "BROWSER", "MULTI_STEP_API"
]
CreateResourceGroupRequestHealthThresholdType = Literal["COUNT", "PERCENTAGE"]
CreateResourceGroupRequestManagedBy = Literal[
    "DASHBOARD", "CLI", "TERRAFORM", "MCP", "API"
]
CreateStatusPageComponentRequestType = Literal[
    "MONITOR", "GROUP", "STATIC", "DEPENDENCY"
]
CreateStatusPageIncidentRequestImpact = Literal["NONE", "MINOR", "MAJOR", "CRITICAL"]
CreateStatusPageIncidentRequestStatus = Literal[
    "INVESTIGATING", "IDENTIFIED", "MONITORING", "RESOLVED"
]
CreateStatusPageIncidentUpdateRequestStatus = Literal[
    "INVESTIGATING", "IDENTIFIED", "MONITORING", "RESOLVED"
]
CreateStatusPageMaintenanceRequestImpact = Literal["NONE", "MINOR", "MAJOR", "CRITICAL"]
CreateStatusPageMaintenanceRequestStatus = Literal[
    "INVESTIGATING", "IDENTIFIED", "MONITORING", "RESOLVED"
]
CreateStatusPageRequestIncidentMode = Literal["MANUAL", "REVIEW", "AUTOMATIC"]
CreateStatusPageRequestManagedBy = Literal[
    "DASHBOARD", "CLI", "TERRAFORM", "MCP", "API"
]
CreateStatusPageRequestVisibility = Literal["PUBLIC", "PASSWORD", "IP_RESTRICTED"]
CreateWebhookEndpointRequestSubscribedEventsItem = Literal[
    "monitor.created",
    "monitor.updated",
    "monitor.deleted",
    "incident.created",
    "incident.resolved",
    "incident.reopened",
    "service.status_changed",
    "service.component_changed",
    "service.incident_created",
    "service.incident_updated",
    "service.incident_resolved",
]
DatadogChannelConfigChannelType = Literal["datadog"]
DayIncidentImpact = Literal["NONE", "MINOR", "MAJOR", "CRITICAL"]
DayIncidentStatus = Literal["INVESTIGATING", "IDENTIFIED", "MONITORING", "RESOLVED"]
DiscordChannelConfigChannelType = Literal["discord"]
DnsCheckType = Literal["dns"]
DnsExpectedCnameAssertionType = Literal["dns_expected_cname"]
DnsExpectedIpsAssertionType = Literal["dns_expected_ips"]
DnsMaxAnswersAssertionType = Literal["dns_max_answers"]
DnsMinAnswersAssertionType = Literal["dns_min_answers"]
DnsMonitorConfigRecordTypesItem = Literal[
    "A", "AAAA", "CNAME", "MX", "NS", "TXT", "SRV", "SOA", "CAA", "PTR"
]
DnsRecordContainsAssertionType = Literal["dns_record_contains"]
DnsRecordEqualsAssertionType = Literal["dns_record_equals"]
DnsResolvesAssertionType = Literal["dns_resolves"]
DnsResponseTimeAssertionType = Literal["dns_response_time"]
DnsResponseTimeWarnAssertionType = Literal["dns_response_time_warn"]
DnsTtlHighAssertionType = Literal["dns_ttl_high"]
DnsTtlLowAssertionType = Literal["dns_ttl_low"]
DnsTxtContainsAssertionType = Literal["dns_txt_contains"]
EmailChannelConfigChannelType = Literal["email"]
GitLabChannelConfigChannelType = Literal["gitlab"]
GoogleChatChannelConfigChannelType = Literal["google_chat"]
HeaderAuthConfigType = Literal["header"]
HeaderValueAssertionOperator = Literal[
    "equals", "contains", "less_than", "greater_than", "matches", "range"
]
HeaderValueAssertionType = Literal["header_value"]
HeartbeatIntervalDriftAssertionType = Literal["heartbeat_interval_drift"]
HeartbeatMaxIntervalAssertionType = Literal["heartbeat_max_interval"]
HeartbeatPayloadContainsAssertionType = Literal["heartbeat_payload_contains"]
HeartbeatReceivedAssertionType = Literal["heartbeat_received"]
HttpCheckType = Literal["http"]
HttpMonitorConfigMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"]
IcmpCheckType = Literal["icmp"]
IcmpPacketLossAssertionType = Literal["icmp_packet_loss"]
IcmpReachableAssertionType = Literal["icmp_reachable"]
IcmpResponseTimeAssertionType = Literal["icmp_response_time"]
IcmpResponseTimeWarnAssertionType = Literal["icmp_response_time_warn"]
IncidentActivityEventDtoKind = Literal[
    "update", "dispatch", "delivery", "forensic_transition", "status_page_update"
]
IncidentDtoResolutionReason = Literal["MANUAL", "AUTO_RECOVERED", "AUTO_RESOLVED"]
IncidentDtoSeverity = Literal["DOWN", "DEGRADED", "MAINTENANCE"]
IncidentDtoSource = Literal[
    "AUTOMATIC", "MANUAL", "MONITORS", "STATUS_DATA", "RESOURCE_GROUP"
]
IncidentDtoStatus = Literal["WATCHING", "TRIGGERED", "CONFIRMED", "RESOLVED"]
IncidentFilterParamsSeverity = Literal["DOWN", "DEGRADED", "MAINTENANCE"]
IncidentFilterParamsSource = Literal[
    "AUTOMATIC", "MANUAL", "MONITORS", "STATUS_DATA", "RESOURCE_GROUP"
]
IncidentFilterParamsStatus = Literal["WATCHING", "TRIGGERED", "CONFIRMED", "RESOLVED"]
IncidentIoChannelConfigChannelType = Literal["incident_io"]
IncidentTriggerDtoSource = Literal["forensics", "checks", "none"]
IncidentUpdateDtoCreatedBy = Literal["SYSTEM", "USER"]
IncidentUpdateDtoNewStatus = Literal["WATCHING", "TRIGGERED", "CONFIRMED", "RESOLVED"]
IncidentUpdateDtoOldStatus = Literal["WATCHING", "TRIGGERED", "CONFIRMED", "RESOLVED"]
IntegrationDtoTierAvailability = Literal[
    "FREE", "STARTER", "PRO", "TEAM", "BUSINESS", "ENTERPRISE"
]
InviteDtoRoleOffered = Literal["OWNER", "ADMIN", "MEMBER"]
JiraChannelConfigChannelType = Literal["jira"]
JsonPathAssertionOperator = Literal[
    "equals", "contains", "less_than", "greater_than", "matches", "range"
]
JsonPathAssertionType = Literal["json_path"]
LinearChannelConfigChannelType = Literal["linear"]
LinkedStatusPageIncidentDtoConnectionMode = Literal["AUTO", "MANUAL"]
LinkedStatusPageIncidentDtoImpact = Literal["NONE", "MINOR", "MAJOR", "CRITICAL"]
LinkedStatusPageIncidentDtoPageIncidentMode = Literal["MANUAL", "REVIEW", "AUTOMATIC"]
LinkedStatusPageIncidentDtoStatus = Literal[
    "INVESTIGATING", "IDENTIFIED", "MONITORING", "RESOLVED"
]
MatchRuleType = Literal[
    "severity_gte",
    "monitor_id_in",
    "region_in",
    "incident_status",
    "monitor_type_in",
    "service_id_in",
    "resource_group_id_in",
    "component_name_in",
    "monitor_tag_in",
]
MattermostChannelConfigChannelType = Literal["mattermost"]
McpConnectsAssertionType = Literal["mcp_connects"]
McpHasCapabilityAssertionType = Literal["mcp_has_capability"]
McpMinToolsAssertionType = Literal["mcp_min_tools"]
McpProtocolVersionAssertionType = Literal["mcp_protocol_version"]
McpResponseTimeAssertionType = Literal["mcp_response_time"]
McpResponseTimeWarnAssertionType = Literal["mcp_response_time_warn"]
McpServerCheckType = Literal["mcp_server"]
McpToolAvailableAssertionType = Literal["mcp_tool_available"]
McpToolCountChangedAssertionType = Literal["mcp_tool_count_changed"]
MemberDtoOrgRole = Literal["OWNER", "ADMIN", "MEMBER"]
MemberDtoStatus = Literal[
    "INVITED", "ACTIVE", "SUSPENDED", "LEFT", "REMOVED", "DECLINED"
]
MemberRoleChangedMetadataKind = Literal["member_role_changed"]
MemberRoleChangedMetadataNewRole = Literal["OWNER", "ADMIN", "MEMBER"]
MemberRoleChangedMetadataOldRole = Literal["OWNER", "ADMIN", "MEMBER"]
MonitorAssertionDtoAssertionType = Literal[
    "status_code",
    "response_time",
    "body_contains",
    "json_path",
    "header_value",
    "regex_body",
    "dns_resolves",
    "dns_response_time",
    "dns_expected_ips",
    "dns_expected_cname",
    "dns_record_contains",
    "dns_record_equals",
    "dns_txt_contains",
    "dns_min_answers",
    "dns_max_answers",
    "dns_response_time_warn",
    "dns_ttl_low",
    "dns_ttl_high",
    "mcp_connects",
    "mcp_response_time",
    "mcp_has_capability",
    "mcp_tool_available",
    "mcp_min_tools",
    "mcp_protocol_version",
    "mcp_response_time_warn",
    "mcp_tool_count_changed",
    "ssl_expiry",
    "response_size",
    "redirect_count",
    "redirect_target",
    "response_time_warn",
    "tcp_connects",
    "tcp_response_time",
    "tcp_response_time_warn",
    "icmp_reachable",
    "icmp_response_time",
    "icmp_response_time_warn",
    "icmp_packet_loss",
    "heartbeat_received",
    "heartbeat_max_interval",
    "heartbeat_interval_drift",
    "heartbeat_payload_contains",
]
MonitorAssertionDtoSeverity = Literal["fail", "warn"]
MonitorAuthDtoAuthType = Literal["bearer", "basic", "header", "api_key"]
MonitorDtoCurrentStatus = Literal["up", "degraded", "down", "paused", "unknown"]
MonitorDtoManagedBy = Literal["DASHBOARD", "CLI", "TERRAFORM", "MCP", "API"]
MonitorDtoType = Literal[
    "HTTP", "DNS", "MCP_SERVER", "TCP", "ICMP", "HEARTBEAT", "BROWSER", "MULTI_STEP_API"
]
MonitorTestRequestType = Literal[
    "HTTP", "DNS", "MCP_SERVER", "TCP", "ICMP", "HEARTBEAT", "BROWSER", "MULTI_STEP_API"
]
MonitorVersionDtoChangedVia = Literal["API", "DASHBOARD", "CLI", "TERRAFORM"]
NotificationDispatchDtoCompletionReason = Literal["EXHAUSTED", "RESOLVED", "NO_STEPS"]
NotificationDispatchDtoStatus = Literal[
    "PENDING", "DISPATCHING", "DELIVERED", "ESCALATING", "ACKNOWLEDGED", "COMPLETED"
]
OpsGenieChannelConfigChannelType = Literal["opsgenie"]
OrgIncidentAnnotationDtoSeverity = Literal["DOWN", "DEGRADED", "MAINTENANCE"]
OrgIncidentAnnotationDtoStatus = Literal[
    "WATCHING", "TRIGGERED", "CONFIRMED", "RESOLVED"
]
PagerDutyChannelConfigChannelType = Literal["pagerduty"]
PhoneCallChannelConfigChannelType = Literal["phone_call"]
PlanInfoTier = Literal["FREE", "STARTER", "PRO", "TEAM", "BUSINESS", "ENTERPRISE"]
PublishStatusPageIncidentRequestImpact = Literal["NONE", "MINOR", "MAJOR", "CRITICAL"]
PublishStatusPageIncidentRequestStatus = Literal[
    "INVESTIGATING", "IDENTIFIED", "MONITORING", "RESOLVED"
]
PushbulletChannelConfigChannelType = Literal["pushbullet"]
PushoverChannelConfigChannelType = Literal["pushover"]
RedirectCountAssertionType = Literal["redirect_count"]
RedirectTargetAssertionOperator = Literal[
    "equals", "contains", "less_than", "greater_than", "matches", "range"
]
RedirectTargetAssertionType = Literal["redirect_target"]
RegexBodyAssertionType = Literal["regex_body"]
ResourceGroupDtoHealthThresholdType = Literal["COUNT", "PERCENTAGE"]
ResourceGroupDtoManagedBy = Literal["DASHBOARD", "CLI", "TERRAFORM", "MCP", "API"]
ResourceGroupHealthDtoStatus = Literal["operational", "maintenance", "degraded", "down"]
ResourceGroupHealthDtoThresholdStatus = Literal["healthy", "degraded", "down"]
ResourceGroupMemberDtoStatus = Literal["operational", "maintenance", "degraded", "down"]
ResponseSizeAssertionType = Literal["response_size"]
ResponseTimeAssertionType = Literal["response_time"]
ResponseTimeWarnAssertionType = Literal["response_time_warn"]
ResultSummaryDtoCurrentStatus = Literal["up", "degraded", "down", "paused", "unknown"]
RootlyChannelConfigChannelType = Literal["rootly"]
ServiceCatalogDtoLifecycleStatus = Literal[
    "ACTIVE", "DEGRADED", "DEPRECATED", "RETIRED"
]
ServiceDetailDtoLifecycleStatus = Literal["ACTIVE", "DEGRADED", "DEPRECATED", "RETIRED"]
ServiceSubscriptionDtoAlertSensitivity = Literal[
    "ALL", "AWARENESS", "INCIDENTS_ONLY", "MAJOR_ONLY"
]
SetStatusPageComponentOverrideRequestStatus = Literal[
    "OPERATIONAL",
    "DEGRADED_PERFORMANCE",
    "PARTIAL_OUTAGE",
    "MAJOR_OUTAGE",
    "UNDER_MAINTENANCE",
]
SkippedDispatchStatus = Literal[
    "PENDING", "DISPATCHING", "DELIVERED", "ESCALATING", "ACKNOWLEDGED", "COMPLETED"
]
SlackChannelConfigChannelType = Literal["slack"]
SmsChannelConfigChannelType = Literal["sms"]
SplunkOnCallChannelConfigChannelType = Literal["splunk_oncall"]
SslExpiryAssertionType = Literal["ssl_expiry"]
StateTransitionDetailsSource = Literal["pipeline", "public-api"]
StatusCodeAssertionOperator = Literal[
    "equals", "contains", "less_than", "greater_than", "matches", "range"
]
StatusCodeAssertionType = Literal["status_code"]
StatusEventDtoType = Literal[
    "incident.opened",
    "incident.update",
    "incident.resolved",
    "maintenance.scheduled",
    "maintenance.started",
    "maintenance.completed",
    "component.transition",
]
StatusPageComponentDtoCurrentStatus = Literal[
    "OPERATIONAL",
    "DEGRADED_PERFORMANCE",
    "PARTIAL_OUTAGE",
    "MAJOR_OUTAGE",
    "UNDER_MAINTENANCE",
]
StatusPageComponentDtoOverrideStatus = Literal[
    "OPERATIONAL",
    "DEGRADED_PERFORMANCE",
    "PARTIAL_OUTAGE",
    "MAJOR_OUTAGE",
    "UNDER_MAINTENANCE",
]
StatusPageComponentDtoType = Literal["MONITOR", "GROUP", "STATIC", "DEPENDENCY"]
StatusPageCustomDomainDtoStatus = Literal[
    "PENDING_VERIFICATION",
    "VERIFICATION_FAILED",
    "VERIFIED",
    "SSL_PENDING",
    "ACTIVE",
    "FAILED",
    "REMOVED",
]
StatusPageCustomDomainDtoVerificationMethod = Literal["CNAME", "TXT"]
StatusPageDtoIncidentMode = Literal["MANUAL", "REVIEW", "AUTOMATIC"]
StatusPageDtoManagedBy = Literal["DASHBOARD", "CLI", "TERRAFORM", "MCP", "API"]
StatusPageDtoOverallStatus = Literal[
    "OPERATIONAL",
    "DEGRADED_PERFORMANCE",
    "PARTIAL_OUTAGE",
    "MAJOR_OUTAGE",
    "UNDER_MAINTENANCE",
]
StatusPageDtoVisibility = Literal["PUBLIC", "PASSWORD", "IP_RESTRICTED"]
StatusPageIncidentComponentDtoComponentStatus = Literal[
    "OPERATIONAL",
    "DEGRADED_PERFORMANCE",
    "PARTIAL_OUTAGE",
    "MAJOR_OUTAGE",
    "UNDER_MAINTENANCE",
]
StatusPageIncidentDtoImpact = Literal["NONE", "MINOR", "MAJOR", "CRITICAL"]
StatusPageIncidentDtoStatus = Literal[
    "INVESTIGATING", "IDENTIFIED", "MONITORING", "RESOLVED"
]
StatusPageIncidentUpdateDtoCreatedBy = Literal["USER", "SYSTEM"]
StatusPageIncidentUpdateDtoStatus = Literal[
    "INVESTIGATING", "IDENTIFIED", "MONITORING", "RESOLVED"
]
StatusPageMeasuredComponentUptimeDtoSource = Literal["incident_window", "measured"]
StatusPageNotificationDeliveryDtoEventType = Literal[
    "SUBSCRIPTION_CONFIRMATION",
    "INCIDENT_CREATED",
    "INCIDENT_UPDATED",
    "INCIDENT_RESOLVED",
]
StatusPageNotificationDeliveryDtoStatus = Literal[
    "PENDING",
    "DELIVERED",
    "RETRY_PENDING",
    "FAILED",
    "CANCELLED",
    "SKIPPED_NO_CREDIT",
    "SKIPPED_UNVERIFIED",
    "SKIPPED_OPTED_OUT",
    "SKIPPED_RATE_LIMITED",
]
StatusPageOpenIncidentSummaryDtoStatus = Literal[
    "INVESTIGATING", "IDENTIFIED", "MONITORING", "RESOLVED"
]
StatusPageSubscriberDtoChannel = Literal["EMAIL", "SMS", "WEBHOOK"]
TcpCheckType = Literal["tcp"]
TcpConnectsAssertionType = Literal["tcp_connects"]
TcpResponseTimeAssertionType = Literal["tcp_response_time"]
TcpResponseTimeWarnAssertionType = Literal["tcp_response_time_warn"]
TeamsChannelConfigChannelType = Literal["teams"]
TelegramChannelConfigChannelType = Literal["telegram"]
TriggerRuleAggregationType = Literal["all_exceed", "average", "p95", "max"]
TriggerRuleScope = Literal["per_region", "any_region"]
TriggerRuleSeverity = Literal["down", "degraded"]
TriggerRuleType = Literal["consecutive_failures", "failures_in_window", "response_time"]
UpdateAlertChannelRequestManagedBy = Literal[
    "DASHBOARD", "CLI", "TERRAFORM", "MCP", "API"
]
UpdateAssertionRequestSeverity = Literal["fail", "warn"]
UpdateDatadogChannelConfigChannelType = Literal["datadog"]
UpdateDiscordChannelConfigChannelType = Literal["discord"]
UpdateEmailChannelConfigChannelType = Literal["email"]
UpdateGitLabChannelConfigChannelType = Literal["gitlab"]
UpdateGoogleChatChannelConfigChannelType = Literal["google_chat"]
UpdateIncidentIoChannelConfigChannelType = Literal["incident_io"]
UpdateIncidentRequestSeverity = Literal["DOWN", "DEGRADED", "MAINTENANCE"]
UpdateJiraChannelConfigChannelType = Literal["jira"]
UpdateLinearChannelConfigChannelType = Literal["linear"]
UpdateMattermostChannelConfigChannelType = Literal["mattermost"]
UpdateMonitorRequestManagedBy = Literal["DASHBOARD", "CLI", "TERRAFORM", "MCP", "API"]
UpdateOpsGenieChannelConfigChannelType = Literal["opsgenie"]
UpdatePagerDutyChannelConfigChannelType = Literal["pagerduty"]
UpdatePhoneCallChannelConfigChannelType = Literal["phone_call"]
UpdatePushbulletChannelConfigChannelType = Literal["pushbullet"]
UpdatePushoverChannelConfigChannelType = Literal["pushover"]
UpdateResourceGroupRequestHealthThresholdType = Literal["COUNT", "PERCENTAGE"]
UpdateResourceGroupRequestManagedBy = Literal[
    "DASHBOARD", "CLI", "TERRAFORM", "MCP", "API"
]
UpdateRootlyChannelConfigChannelType = Literal["rootly"]
UpdateSlackChannelConfigChannelType = Literal["slack"]
UpdateSmsChannelConfigChannelType = Literal["sms"]
UpdateSplunkOnCallChannelConfigChannelType = Literal["splunk_oncall"]
UpdateStatusPageIncidentRequestImpact = Literal["NONE", "MINOR", "MAJOR", "CRITICAL"]
UpdateStatusPageIncidentRequestStatus = Literal[
    "INVESTIGATING", "IDENTIFIED", "MONITORING", "RESOLVED"
]
UpdateStatusPageIncidentUpdateRequestStatus = Literal[
    "INVESTIGATING", "IDENTIFIED", "MONITORING", "RESOLVED"
]
UpdateStatusPageRequestIncidentMode = Literal["MANUAL", "REVIEW", "AUTOMATIC"]
UpdateStatusPageRequestManagedBy = Literal[
    "DASHBOARD", "CLI", "TERRAFORM", "MCP", "API"
]
UpdateStatusPageRequestVisibility = Literal["PUBLIC", "PASSWORD", "IP_RESTRICTED"]
UpdateTeamsChannelConfigChannelType = Literal["teams"]
UpdateTelegramChannelConfigChannelType = Literal["telegram"]
UpdateWebhookChannelConfigChannelType = Literal["webhook"]
UpdateWebhookEndpointRequestSubscribedEventsItem = Literal[
    "monitor.created",
    "monitor.updated",
    "monitor.deleted",
    "incident.created",
    "incident.resolved",
    "incident.reopened",
    "service.status_changed",
    "service.component_changed",
    "service.incident_created",
    "service.incident_updated",
    "service.incident_resolved",
]
UpdateZapierChannelConfigChannelType = Literal["zapier"]
WebhookChannelConfigChannelType = Literal["webhook"]
ZapierChannelConfigChannelType = Literal["zapier"]

__all__ = [
    "AddIncidentUpdateRequestNewStatus",
    "AdminAddSubscriberRequestChannel",
    "AffectedComponentStatus",
    "AlertChannelDtoChannelType",
    "AlertChannelDtoManagedBy",
    "AlertDeliveryDtoEventType",
    "AlertDeliveryDtoStatus",
    "ApiKeyAuthConfigType",
    "AssertionResultDtoSeverity",
    "AssertionTestResultDtoAssertionType",
    "AssertionTestResultDtoSeverity",
    "BasicAuthConfigType",
    "BearerAuthConfigType",
    "BodyContainsAssertionType",
    "BulkMonitorActionRequestAction",
    "ChangeRoleRequestOrgRole",
    "ChangeStatusRequestStatus",
    "CodeCheckType",
    "ConfirmationPolicyType",
    "CreateAlertChannelRequestManagedBy",
    "CreateAssertionRequestSeverity",
    "CreateInviteRequestRoleOffered",
    "CreateManualIncidentRequestSeverity",
    "CreateMonitorRequestManagedBy",
    "CreateMonitorRequestType",
    "CreateResourceGroupRequestHealthThresholdType",
    "CreateResourceGroupRequestManagedBy",
    "CreateStatusPageComponentRequestType",
    "CreateStatusPageIncidentRequestImpact",
    "CreateStatusPageIncidentRequestStatus",
    "CreateStatusPageIncidentUpdateRequestStatus",
    "CreateStatusPageMaintenanceRequestImpact",
    "CreateStatusPageMaintenanceRequestStatus",
    "CreateStatusPageRequestIncidentMode",
    "CreateStatusPageRequestManagedBy",
    "CreateStatusPageRequestVisibility",
    "CreateWebhookEndpointRequestSubscribedEventsItem",
    "DatadogChannelConfigChannelType",
    "DayIncidentImpact",
    "DayIncidentStatus",
    "DiscordChannelConfigChannelType",
    "DnsCheckType",
    "DnsExpectedCnameAssertionType",
    "DnsExpectedIpsAssertionType",
    "DnsMaxAnswersAssertionType",
    "DnsMinAnswersAssertionType",
    "DnsMonitorConfigRecordTypesItem",
    "DnsRecordContainsAssertionType",
    "DnsRecordEqualsAssertionType",
    "DnsResolvesAssertionType",
    "DnsResponseTimeAssertionType",
    "DnsResponseTimeWarnAssertionType",
    "DnsTtlHighAssertionType",
    "DnsTtlLowAssertionType",
    "DnsTxtContainsAssertionType",
    "EmailChannelConfigChannelType",
    "GitLabChannelConfigChannelType",
    "GoogleChatChannelConfigChannelType",
    "HeaderAuthConfigType",
    "HeaderValueAssertionOperator",
    "HeaderValueAssertionType",
    "HeartbeatIntervalDriftAssertionType",
    "HeartbeatMaxIntervalAssertionType",
    "HeartbeatPayloadContainsAssertionType",
    "HeartbeatReceivedAssertionType",
    "HttpCheckType",
    "HttpMonitorConfigMethod",
    "IcmpCheckType",
    "IcmpPacketLossAssertionType",
    "IcmpReachableAssertionType",
    "IcmpResponseTimeAssertionType",
    "IcmpResponseTimeWarnAssertionType",
    "IncidentActivityEventDtoKind",
    "IncidentDtoResolutionReason",
    "IncidentDtoSeverity",
    "IncidentDtoSource",
    "IncidentDtoStatus",
    "IncidentFilterParamsSeverity",
    "IncidentFilterParamsSource",
    "IncidentFilterParamsStatus",
    "IncidentIoChannelConfigChannelType",
    "IncidentTriggerDtoSource",
    "IncidentUpdateDtoCreatedBy",
    "IncidentUpdateDtoNewStatus",
    "IncidentUpdateDtoOldStatus",
    "IntegrationDtoTierAvailability",
    "InviteDtoRoleOffered",
    "JiraChannelConfigChannelType",
    "JsonPathAssertionOperator",
    "JsonPathAssertionType",
    "LinearChannelConfigChannelType",
    "LinkedStatusPageIncidentDtoConnectionMode",
    "LinkedStatusPageIncidentDtoImpact",
    "LinkedStatusPageIncidentDtoPageIncidentMode",
    "LinkedStatusPageIncidentDtoStatus",
    "MatchRuleType",
    "MattermostChannelConfigChannelType",
    "McpConnectsAssertionType",
    "McpHasCapabilityAssertionType",
    "McpMinToolsAssertionType",
    "McpProtocolVersionAssertionType",
    "McpResponseTimeAssertionType",
    "McpResponseTimeWarnAssertionType",
    "McpServerCheckType",
    "McpToolAvailableAssertionType",
    "McpToolCountChangedAssertionType",
    "MemberDtoOrgRole",
    "MemberDtoStatus",
    "MemberRoleChangedMetadataKind",
    "MemberRoleChangedMetadataNewRole",
    "MemberRoleChangedMetadataOldRole",
    "MonitorAssertionDtoAssertionType",
    "MonitorAssertionDtoSeverity",
    "MonitorAuthDtoAuthType",
    "MonitorDtoCurrentStatus",
    "MonitorDtoManagedBy",
    "MonitorDtoType",
    "MonitorTestRequestType",
    "MonitorVersionDtoChangedVia",
    "NotificationDispatchDtoCompletionReason",
    "NotificationDispatchDtoStatus",
    "OpsGenieChannelConfigChannelType",
    "OrgIncidentAnnotationDtoSeverity",
    "OrgIncidentAnnotationDtoStatus",
    "PagerDutyChannelConfigChannelType",
    "PhoneCallChannelConfigChannelType",
    "PlanInfoTier",
    "PublishStatusPageIncidentRequestImpact",
    "PublishStatusPageIncidentRequestStatus",
    "PushbulletChannelConfigChannelType",
    "PushoverChannelConfigChannelType",
    "RedirectCountAssertionType",
    "RedirectTargetAssertionOperator",
    "RedirectTargetAssertionType",
    "RegexBodyAssertionType",
    "ResourceGroupDtoHealthThresholdType",
    "ResourceGroupDtoManagedBy",
    "ResourceGroupHealthDtoStatus",
    "ResourceGroupHealthDtoThresholdStatus",
    "ResourceGroupMemberDtoStatus",
    "ResponseSizeAssertionType",
    "ResponseTimeAssertionType",
    "ResponseTimeWarnAssertionType",
    "ResultSummaryDtoCurrentStatus",
    "RootlyChannelConfigChannelType",
    "ServiceCatalogDtoLifecycleStatus",
    "ServiceDetailDtoLifecycleStatus",
    "ServiceSubscriptionDtoAlertSensitivity",
    "SetStatusPageComponentOverrideRequestStatus",
    "SkippedDispatchStatus",
    "SlackChannelConfigChannelType",
    "SmsChannelConfigChannelType",
    "SplunkOnCallChannelConfigChannelType",
    "SslExpiryAssertionType",
    "StateTransitionDetailsSource",
    "StatusCodeAssertionOperator",
    "StatusCodeAssertionType",
    "StatusEventDtoType",
    "StatusPageComponentDtoCurrentStatus",
    "StatusPageComponentDtoOverrideStatus",
    "StatusPageComponentDtoType",
    "StatusPageCustomDomainDtoStatus",
    "StatusPageCustomDomainDtoVerificationMethod",
    "StatusPageDtoIncidentMode",
    "StatusPageDtoManagedBy",
    "StatusPageDtoOverallStatus",
    "StatusPageDtoVisibility",
    "StatusPageIncidentComponentDtoComponentStatus",
    "StatusPageIncidentDtoImpact",
    "StatusPageIncidentDtoStatus",
    "StatusPageIncidentUpdateDtoCreatedBy",
    "StatusPageIncidentUpdateDtoStatus",
    "StatusPageMeasuredComponentUptimeDtoSource",
    "StatusPageNotificationDeliveryDtoEventType",
    "StatusPageNotificationDeliveryDtoStatus",
    "StatusPageOpenIncidentSummaryDtoStatus",
    "StatusPageSubscriberDtoChannel",
    "TcpCheckType",
    "TcpConnectsAssertionType",
    "TcpResponseTimeAssertionType",
    "TcpResponseTimeWarnAssertionType",
    "TeamsChannelConfigChannelType",
    "TelegramChannelConfigChannelType",
    "TriggerRuleAggregationType",
    "TriggerRuleScope",
    "TriggerRuleSeverity",
    "TriggerRuleType",
    "UpdateAlertChannelRequestManagedBy",
    "UpdateAssertionRequestSeverity",
    "UpdateDatadogChannelConfigChannelType",
    "UpdateDiscordChannelConfigChannelType",
    "UpdateEmailChannelConfigChannelType",
    "UpdateGitLabChannelConfigChannelType",
    "UpdateGoogleChatChannelConfigChannelType",
    "UpdateIncidentIoChannelConfigChannelType",
    "UpdateIncidentRequestSeverity",
    "UpdateJiraChannelConfigChannelType",
    "UpdateLinearChannelConfigChannelType",
    "UpdateMattermostChannelConfigChannelType",
    "UpdateMonitorRequestManagedBy",
    "UpdateOpsGenieChannelConfigChannelType",
    "UpdatePagerDutyChannelConfigChannelType",
    "UpdatePhoneCallChannelConfigChannelType",
    "UpdatePushbulletChannelConfigChannelType",
    "UpdatePushoverChannelConfigChannelType",
    "UpdateResourceGroupRequestHealthThresholdType",
    "UpdateResourceGroupRequestManagedBy",
    "UpdateRootlyChannelConfigChannelType",
    "UpdateSlackChannelConfigChannelType",
    "UpdateSmsChannelConfigChannelType",
    "UpdateSplunkOnCallChannelConfigChannelType",
    "UpdateStatusPageIncidentRequestImpact",
    "UpdateStatusPageIncidentRequestStatus",
    "UpdateStatusPageIncidentUpdateRequestStatus",
    "UpdateStatusPageRequestIncidentMode",
    "UpdateStatusPageRequestManagedBy",
    "UpdateStatusPageRequestVisibility",
    "UpdateTeamsChannelConfigChannelType",
    "UpdateTelegramChannelConfigChannelType",
    "UpdateWebhookChannelConfigChannelType",
    "UpdateWebhookEndpointRequestSubscribedEventsItem",
    "UpdateZapierChannelConfigChannelType",
    "WebhookChannelConfigChannelType",
    "ZapierChannelConfigChannelType",
]
