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
ApiKeyCreateResponseTool = Literal["DASHBOARD", "CLI", "TERRAFORM", "MCP", "API"]
ApiKeyDtoTool = Literal["DASHBOARD", "CLI", "TERRAFORM", "MCP", "API"]
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
    "PAUSE",
    "RESUME",
    "DELETE",
    "ADD_TAG",
    "REMOVE_TAG",
    "UPDATE_SCHEDULE",
    "RUN",
    "MUTE",
    "UNMUTE",
    "ACKNOWLEDGE",
]
CaptureCompareDtoBaselineKind = Literal["last_pass_this_step_this_region"]
CapturePolicyNetwork = Literal["always", "on_failure", "off"]
CapturePolicyScreenshots = Literal["always", "on_failure", "off"]
CapturePolicyTrace = Literal["always", "on_failure", "off"]
CapturePolicyVideo = Literal["always", "on_failure", "off"]
ChangeRoleRequestOrgRole = Literal["OWNER", "ADMIN", "MEMBER"]
ChangeStatusRequestStatus = Literal[
    "INVITED", "ACTIVE", "SUSPENDED", "LEFT", "REMOVED", "DECLINED"
]
CodeCheckType = Literal["code"]
ConfirmationPolicyType = Literal["multi_region"]
CreateAlertChannelRequestManagedBy = Literal[
    "DASHBOARD", "CLI", "TERRAFORM", "MCP", "API"
]
CreateApiKeyRequestTool = Literal["DASHBOARD", "CLI", "TERRAFORM", "MCP", "API"]
CreateAssertionRequestSeverity = Literal["fail", "warn"]
CreateEmailDomainRequestKind = Literal["assigned", "custom"]
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
CreateWebhookInboxRequestStatus = Literal["active", "disabled"]
DatadogChannelConfigChannelType = Literal["datadog"]
DayIncidentImpact = Literal["NONE", "MINOR", "MAJOR", "CRITICAL"]
DayIncidentStatus = Literal["INVESTIGATING", "IDENTIFIED", "MONITORING", "RESOLVED"]
DemoBookingDtoState = Literal[
    "RECEIVED",
    "CREATING",
    "RECONCILING",
    "CONFIRMED",
    "SLOT_UNAVAILABLE",
    "PROVIDER_UNAVAILABLE",
    "NEEDS_FOLLOW_UP",
    "CANCELED",
]
DeviceTokenDtoStatus = Literal[
    "authorization_pending", "slow_down", "expired", "denied", "complete"
]
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
EmailDomainDtoKind = Literal["assigned", "custom"]
EmailDomainDtoStatus = Literal[
    "active", "disabled", "pending_dns", "verification_failed"
]
EntitlementResponseTier = Literal[
    "FREE", "STARTER", "PRO", "TEAM", "BUSINESS", "ENTERPRISE"
]
ErrorResponseReason = Literal["scope", "role"]
EvidencePurgedMetadataKind = Literal["evidence_purged"]
FindingCode = Literal[
    "MONITOR_CONFIG_TYPE_MISMATCH",
    "MONITOR_FREQUENCY_BELOW_PLAN_MIN",
    "MONITOR_LIMIT_REACHED",
    "MONITOR_AUTH_TYPE_UNSUPPORTED",
    "MONITOR_HEARTBEAT_REGIONS_NOT_SUPPORTED",
    "MONITOR_HEARTBEAT_INTERVAL_TOO_SHORT",
    "MONITOR_HEARTBEAT_GRACE_TOO_SHORT",
    "MONITOR_HEARTBEAT_GRACE_EXCEEDS_INTERVAL",
    "MONITOR_HTTP_HEADERS_TOO_MANY",
    "MONITOR_HTTP_HEADER_RESERVED",
    "MONITOR_HTTP_BODY_METHOD_INVALID",
    "MONITOR_HTTP_BODY_TOO_LARGE",
    "MONITOR_ASSERTION_TYPE_NOT_ALLOWED",
    "MONITOR_ALERT_CHANNEL_NOT_FOUND",
    "MONITOR_TAGS_ADD_INVALID",
    "MONITOR_TAGS_REMOVE_INVALID",
    "MONITOR_TOKEN_ROTATION_HEARTBEAT_ONLY",
    "MONITOR_CODE_CHECK_NOT_AVAILABLE",
    "MONITOR_CODE_CHECK_LIMIT_REACHED",
    "MONITOR_CODE_CHECK_REGION_UNAVAILABLE",
    "MONITOR_CODE_CHECK_TEST_UNAVAILABLE",
    "MONITOR_TEST_BUNDLE_UNAVAILABLE",
    "MONITOR_BROWSER_CHECKS_DISABLED",
    "MONITOR_ENVIRONMENT_REQUIRED",
    "MONITOR_ENVIRONMENT_CLEAR_FORBIDDEN",
    "MONITOR_PACKAGE_XOR_DEFINITION",
    "MONITOR_PACKAGE_DIGEST_INVALID",
    "MONITOR_PACKAGE_NOT_SUPPORTED",
    "MONITOR_PACKAGE_PATH_INVALID",
    "MONITOR_PACKAGE_CONCURRENT",
    "MONITOR_DEFINITION_HAS_NO_REVISION",
    "MONITOR_DEFINITION_IN_USE",
    "MONITOR_STATUS_NOT_WRITABLE",
    "MONITOR_PAUSED",
    "MONITOR_OVERLAY_EXPIRES_IN_PAST",
    "MONITOR_QUARANTINE_FIELDS_REQUIRED",
    "MONITOR_MANAGED_BY_TAKEOVER_REQUIRED",
    "MONITOR_HISTORY_PARAM_INVALID",
    "MONITOR_TAKEOVER_FIELD_UNKNOWN",
    "MONITOR_CAPTURE_POLICY_INVALID",
    "MONITOR_RUN_PARALLEL_CODE_ONLY",
    "REVISION_PACKAGE_BYTES_UNAVAILABLE",
    "MONITOR_CODE_TYPE_REQUIRED",
    "MONITOR_DEFINITION_REQUIRED",
    "REVISION_NOT_ON_DEFINITION",
    "REVISION_DIFF_CROSS_DEFINITION",
    "DEFINITION_HEAD_INCOMPLETE",
    "MONITOR_ASSERTION_NOT_SUPPORTED_FOR_TYPE",
    "MONITOR_AUTH_ALREADY_EXISTS",
    "MONITOR_AUTH_NOT_SUPPORTED_FOR_TYPE",
    "MONITOR_AUTH_VAULT_FOREIGN_ORG",
    "ALERT_CHANNEL_DISABLED",
    "ALERT_CHANNEL_PLAN_REQUIRED",
    "ALERT_CHANNEL_TYPE_IMMUTABLE",
    "ALERT_CHANNEL_CONFIG_INVALID",
    "ALERT_CHANNEL_SLACK_WEBHOOK_INVALID",
    "ALERT_CHANNEL_DISCORD_WEBHOOK_INVALID",
    "ALERT_CHANNEL_TEAMS_WEBHOOK_INVALID",
    "ALERT_CHANNEL_TEAMS_WEBHOOK_CLASSIC_RETIRED",
    "ALERT_CHANNEL_TEAMS_WEBHOOK_HOST",
    "ALERT_CHANNEL_WEBHOOK_URL_INVALID",
    "ALERT_CHANNEL_WEBHOOK_HEADER_RESERVED",
    "ALERT_CHANNEL_OPSGENIE_REGION_INVALID",
    "ALERT_CHANNEL_PAGERDUTY_SEVERITY_INVALID",
    "ALERT_CHANNEL_GOOGLE_CHAT_WEBHOOK_INVALID",
    "ALERT_CHANNEL_PHONE_NUMBER_INVALID",
    "ALERT_CHANNEL_PHONE_NUMBER_UNVERIFIED",
    "ALERT_CHANNEL_PHONE_NUMBERS_COUNT_INVALID",
    "ALERT_CHANNEL_PHONE_NUMBER_REQUIRED",
    "ALERT_CHANNEL_VERIFIED_PHONE_NOT_FOUND",
    "ALERT_CHANNEL_PHONE_DESTINATION_MISMATCH",
    "ALERT_CHANNEL_VOICE_LANGUAGE_INVALID",
    "NOTIFICATION_POLICY_RULE_TYPE_REQUIRED",
    "NOTIFICATION_POLICY_RULE_TYPE_INVALID",
    "NOTIFICATION_POLICY_RULE_VALUE_REQUIRED",
    "NOTIFICATION_POLICY_RULE_VALUE_INVALID",
    "NOTIFICATION_POLICY_RULE_VALUES_REQUIRED",
    "NOTIFICATION_POLICY_RULE_MONITOR_IDS_REQUIRED",
    "NOTIFICATION_POLICY_RULE_REGIONS_REQUIRED",
    "NOTIFICATION_POLICY_RULE_INCIDENT_STATUS_REQUIRED",
    "NOTIFICATION_POLICY_RULE_INCIDENT_STATUS_INVALID",
    "NOTIFICATION_POLICY_RULE_INCIDENT_STATUS_CONFLICT",
    "NOTIFICATION_POLICY_ESCALATION_REQUIRED",
    "NOTIFICATION_POLICY_STEPS_REQUIRED",
    "NOTIFICATION_POLICY_ON_RESOLVE_INVALID",
    "NOTIFICATION_POLICY_ON_REOPEN_INVALID",
    "NOTIFICATION_POLICY_STEP_CHANNELS_EMPTY",
    "NOTIFICATION_POLICY_STEP_DELAY_NEGATIVE",
    "NOTIFICATION_POLICY_STEP_DELAY_TOO_LARGE",
    "NOTIFICATION_POLICY_STEP_REPEAT_INVALID",
    "NOTIFICATION_POLICY_STEP_REPEAT_TOO_LARGE",
    "NOTIFICATION_POLICY_STEPS_TOO_MANY",
    "NOTIFICATION_POLICY_STEP_CHANNEL_NOT_FOUND",
    "NOTIFICATION_POLICY_DELETE_BLOCKED",
    "MONITOR_POLICY_TRIGGER_RULES_EMPTY",
    "MONITOR_POLICY_RULE_TYPE_REQUIRED",
    "MONITOR_POLICY_RULE_SEVERITY_REQUIRED",
    "MONITOR_POLICY_CONFIRMATION_REQUIRED",
    "MONITOR_POLICY_CONFIRMATION_TYPE_REQUIRED",
    "MONITOR_POLICY_CONFIRMATION_REGIONS_TOO_FEW",
    "MONITOR_POLICY_CONFIRMATION_WAIT_TOO_SHORT",
    "MONITOR_POLICY_CONFIRMATION_WAIT_BELOW_INVARIANT",
    "MONITOR_POLICY_RECOVERY_REQUIRED",
    "MONITOR_POLICY_RECOVERY_SUCCESSES_TOO_FEW",
    "MONITOR_POLICY_RECOVERY_REGIONS_TOO_FEW",
    "MONITOR_POLICY_RECOVERY_COOLDOWN_OUT_OF_RANGE",
    "MONITOR_POLICY_FIELD_REQUIRED",
    "MONITOR_POLICY_FIELD_NOT_POSITIVE",
    "MONITOR_POLICY_FIELD_OUT_OF_RANGE",
    "URL_INVALID",
    "URL_SCHEME_UNSUPPORTED",
    "URL_HOST_REQUIRED",
    "URL_HOST_PRIVATE",
    "RESOURCE_GROUP_LIMIT_REACHED",
    "RESOURCE_GROUP_MEMBER_LIMIT_REACHED",
    "RESOURCE_GROUP_MEMBER_ALREADY_PRESENT",
    "RESOURCE_GROUP_MEMBER_TYPE_INVALID",
    "RESOURCE_GROUP_THRESHOLD_VALUE_REQUIRED",
    "RESOURCE_GROUP_THRESHOLD_TYPE_REQUIRED",
    "RESOURCE_GROUP_THRESHOLD_OUT_OF_RANGE",
    "RESOURCE_GROUP_SLUG_GENERATION_FAILED",
    "STATUS_PAGE_LIMIT_REACHED",
    "STATUS_PAGE_SLUG_TAKEN",
    "STATUS_PAGE_SLUG_REQUIRED",
    "STATUS_PAGE_SLUG_RESERVED",
    "STATUS_PAGE_VISIBILITY_UNSUPPORTED",
    "STATUS_PAGE_FEATURE_PLAN_REQUIRED",
    "STATUS_PAGE_HOSTNAME_FIRST_PARTY_RESERVED",
    "STATUS_PAGE_HOSTNAME_TLD_RESERVED",
    "STATUS_PAGE_HOSTNAME_TAKEN",
    "STATUS_PAGE_DOMAIN_NOT_VERIFIED",
    "STATUS_PAGE_COMPONENT_GROUP_NOT_FOUND",
    "STATUS_PAGE_COMPONENT_MONITOR_REQUIRED",
    "STATUS_PAGE_COMPONENT_GROUP_REQUIRED",
    "STATUS_PAGE_COMPONENT_STATIC_REFS_INVALID",
    "STATUS_PAGE_COMPONENT_SUBSCRIPTION_REQUIRED",
    "STATUS_PAGE_COMPONENT_SUBSCRIPTION_NOT_FOUND",
    "STATUS_PAGE_COMPONENT_DEPENDENCY_REFS_INVALID",
    "STATUS_PAGE_COMPONENT_SUBSCRIPTION_REFS_INVALID",
    "STATUS_PAGE_NOTIFICATION_DELIVERY_RETRY_NOT_FAILED",
    "STATUS_PAGE_NOTIFICATION_DELIVERY_RETRY_TERMINAL",
    "STATUS_PAGE_MEASURED_UPTIME_MONITOR_ONLY",
    "STATUS_PAGE_COMPONENT_OVERRIDE_EXPIRES_AT_IN_PAST",
    "STATUS_PAGE_COMPONENT_OVERRIDE_EXPIRES_AT_EXCEEDS_MAX",
    "STATUS_PAGE_SUBSCRIBER_DESTINATION_REQUIRED",
    "STATUS_PAGE_SUBSCRIBER_DESTINATION_INVALID",
    "STATUS_PAGE_SUBSCRIBER_COMPONENT_NOT_FOUND",
    "SP_INCIDENT_PUBLISH_RESOLVED",
    "SP_INCIDENT_DISMISS_PUBLISHED",
    "SP_INCIDENT_SCHEDULED_FOR_REQUIRED",
    "SP_INCIDENT_SCHEDULED_UNTIL_BEFORE_FOR",
    "SP_INCIDENT_AUTO_RESOLVE_REQUIRES_UNTIL",
    "SP_INCIDENT_COMPONENT_FOREIGN",
    "SP_INCIDENT_MONITORING_INCIDENT_NOT_FOUND",
    "SUBSCRIPTION_PRICE_INACTIVE",
    "SUBSCRIPTION_PRICE_UNAVAILABLE",
    "SUBSCRIPTION_ALREADY_ACTIVE",
    "SUBSCRIPTION_NOT_ACTIVE",
    "SUBSCRIPTION_NO_SCHEDULED_CHANGE",
    "SUBSCRIPTION_CHANGE_PENDING",
    "SUBSCRIPTION_CANCELING",
    "SUBSCRIPTION_CADENCE_UNAVAILABLE",
    "SUBSCRIPTION_PRICES_INVALID",
    "BILLING_OVERAGE_CAP_INVALID",
    "BILLING_OVERAGE_NOT_ACTIVE",
    "SERVICE_SUBSCRIPTION_FREE_TIER_LIMIT",
    "SERVICE_SUBSCRIPTION_SERVICE_UNAVAILABLE",
    "ACTOR_BAD_REQUEST",
    "ORGANIZATION_ID_REQUIRED",
    "WORKSPACE_REQUIRED",
    "WORKSPACE_INTERNAL_ACTOR_NO_WORKSPACE",
    "WORKSPACE_NOT_FOUND_ON_ORG",
    "ENVIRONMENT_LIMIT_REACHED",
    "ENVIRONMENT_SLUG_TAKEN",
    "ENVIRONMENT_DELETE_BLOCKED",
    "INBOUND_INBOX_NAME_BLANK",
    "INBOUND_HTTP_RESPONSE_DELAY_INVALID",
    "INBOUND_HTTP_RESPONSE_STATUS_INVALID",
    "INBOUND_HTTP_RESPONSE_BODY_TOO_LARGE",
    "INBOUND_HTTP_RESPONSE_BODY_INVALID",
    "INBOUND_HTTP_RESPONSE_CONTENT_TYPE_INVALID",
    "INBOUND_HTTP_RESPONSE_HEADERS_INVALID",
    "INBOUND_EVENTS_CURSOR_INVALID",
    "INBOUND_EVENTS_LIMIT_OUT_OF_RANGE",
    "INBOUND_DOMAIN_CUSTOM_NAME_REQUIRED",
    "INBOUND_DOMAIN_IN_ASSIGNED_ZONE",
    "INBOUND_DOMAIN_NAME_TAKEN",
    "INBOUND_DOMAIN_KIND_INVALID",
    "INBOUND_DOMAIN_STATUS_INVALID",
    "INBOUND_DOMAIN_NAME_INVALID",
    "INBOUND_INJECT_TO_BLANK",
    "INBOUND_INJECT_FROM_BLANK",
    "INBOUND_INJECT_DOMAIN_DISABLED",
    "INBOUND_INJECT_TO_INVALID",
    "INBOUND_INJECT_FROM_INVALID",
    "INBOUND_INJECT_HEADER_INVALID",
    "INBOUND_WAIT_TO_REQUIRED",
    "INBOUND_WAIT_TO_INVALID",
    "INBOUND_WAIT_DOMAIN_REQUIRED",
    "INBOUND_WEBHOOK_INBOX_LIMIT_REACHED",
    "INBOUND_EMAIL_DOMAIN_LIMIT_REACHED",
    "INBOUND_CUSTOM_MX_PLAN_REQUIRED",
    "INBOUND_RETENTION_ABOVE_PLAN",
    "INBOUND_EVENTS_MONTHLY_LIMIT_REACHED",
    "INBOUND_ACTIVITY_INBOX_IDS_REQUIRED",
    "INBOUND_ACTIVITY_INBOX_IDS_TOO_MANY",
    "INBOUND_ACTIVITY_DOMAIN_IDS_REQUIRED",
    "INBOUND_ACTIVITY_DOMAIN_IDS_TOO_MANY",
    "TAG_NAME_TAKEN",
    "SAVED_VIEW_TABLE_UNKNOWN",
    "SAVED_VIEW_LIMIT_REACHED",
    "SAVED_VIEW_FILTERS_TOO_LARGE",
    "SECRET_KEY_TAKEN",
    "SECRET_ENVIRONMENT_VALUE_BLANK",
    "SECRET_REQUEST_ENVIRONMENT_QUERY",
    "SECRET_REQUEST_HEAD_REQUIRED",
    "SECRET_REQUEST_REMAP_SECRET_ID",
    "SESSION_SETUP_FILE_BLANK",
    "SESSION_HEAD_REQUIRED",
    "RUN_NO_HEAD",
    "RUN_KEYS_MISSING",
    "SYNTHETICS_USAGE_CAPPED",
    "RUN_LIST_PARAM_INVALID",
    "ARTIFACT_BYTES_TOO_LARGE",
    "SUPERVISOR_TOKEN_INVALID",
    "LEASE_COMPLETION_CONFLICT",
    "LEASE_FENCE_REJECTED",
    "CAPACITY_TARGET_INVALID",
    "ADMISSIONS_NOT_HELD",
    "RUNTIME_UNKNOWN",
    "RUNTIME_RETIRED",
    "RUNTIME_NOT_AVAILABLE",
    "RUNTIME_UNAVAILABLE",
    "RUNTIME_EOL",
    "RUNTIME_AMBIGUOUS",
    "RUNTIME_DIGEST_IMMUTABLE",
    "RUNTIME_DIGEST_INVALID",
    "API_KEY_LIMIT_REACHED",
    "API_KEY_REVOKED",
    "AUDIT_EXPORT_LIMIT_EXCEEDED",
    "AUTH_FIELD_BLANK",
    "AUTH_EMAIL_INVALID",
    "AUTH_EMAIL_TAKEN",
    "EMAIL_ALREADY_VERIFIED",
    "ORG_EMAIL_TAKEN",
    "ONBOARDING_STAGE_BACKWARD",
    "INVITE_USER_ALREADY_MEMBER",
    "INVITE_ALREADY_ACCEPTED",
    "INVITE_REVOKED",
    "INVITE_EXPIRED",
    "INVITE_EMAIL_MISMATCH",
    "MEMBER_LIMIT_REACHED",
    "MAINTENANCE_WINDOW_END_BEFORE_START",
    "FORENSICS_HASH_BLANK",
    "FORENSICS_HASH_INVALID",
    "CHECK_RESULTS_LIMIT_OUT_OF_RANGE",
    "CHECK_RESULTS_WINDOW_INVALID",
    "CHECK_RESULTS_CURSOR_INVALID",
    "CHECK_RESULTS_REGION_INVALID",
    "STATUS_DATA_STATUS_INVALID",
    "STATUS_DATA_PERIOD_INVALID",
    "STATUS_DATA_GRANULARITY_INVALID",
    "STATUS_DATA_GRANULARITY_PERIOD_MISMATCH",
    "STATUS_DATA_PERIOD_UNKNOWN",
    "STATUS_DATA_FROM_REQUIRED_WITH_TO",
    "STATUS_DATA_TO_IN_FUTURE",
    "STATUS_DATA_FROM_AFTER_TO",
    "STATUS_DATA_WINDOW_TOO_WIDE",
    "STATUS_DATA_TYPES_INVALID",
    "STATUS_DATA_CURSOR_INVALID",
    "STATUS_DATA_LIMIT_OUT_OF_RANGE",
    "STATUS_DATA_COMPONENT_IDS_TOO_MANY",
    "INCIDENT_ACTIVE_EXISTS",
    "INCIDENT_TRANSITION_INVALID",
    "INCIDENT_SERVICE_NOT_FOUND",
    "INCIDENT_SERVICE_INCIDENT_NOT_FOUND",
    "INCIDENT_SERVICE_MISMATCH",
    "INCIDENT_EVENTS_CURSOR_INVALID",
    "INCIDENT_EVENTS_LIMIT_OUT_OF_RANGE",
    "NOTIFICATION_DISPATCH_INVALID_STATE",
    "NOTIFICATION_POLICY_DISPATCHES_LIMIT_OUT_OF_RANGE",
    "NOTIFICATION_POLICY_DISPATCHES_WINDOW_INVALID",
    "NOTIFICATION_POLICY_DISPATCHES_CURSOR_INVALID",
    "WEBHOOK_LIMIT_REACHED",
    "WEBHOOK_URL_BLANK",
    "WEBHOOK_EVENT_TYPES_INVALID",
    "WEBHOOK_EVENT_TYPE_INVALID",
    "ALERT_DELIVERY_RETRY_NOT_FAILED",
    "ADMIN_BACKFILL_TYPE_UNKNOWN",
    "ADMIN_PUBLISH_BLOCKED",
    "ADMIN_ADAPTER_TYPE_UNKNOWN",
    "ADMIN_SEO_METADATA_INVALID",
    "ADMIN_RELATED_SERVICES_TOO_MANY",
    "ADMIN_RELATED_SERVICE_SELF",
    "ADMIN_PROBE_NO_OFFICIAL_URL",
    "ADMIN_PROBE_URL_MALFORMED",
    "ADMIN_LIFECYCLE_TRANSITION_INVALID",
    "CLOUDFLARE_REQUEST_FAILED",
    "CLOUDFLARE_API_ERROR",
    "FIELD_REQUIRED",
    "FIELD_TOO_SMALL",
    "FIELD_TOO_LARGE",
    "FIELD_OUT_OF_RANGE",
    "FIELD_PATTERN_MISMATCH",
    "FIELD_INVALID_EMAIL",
    "FIELD_INVALID_URL",
    "FIELD_INVALID_FORMAT",
    "FIELD_INVARIANT_VIOLATED",
    "FIELD_VALIDATION_FAILED",
    "REQUEST_BODY_REQUIRED",
    "REQUEST_BODY_MALFORMED",
    "REQUEST_BODY_TYPE_MISMATCH",
    "REQUEST_PARAMETER_REQUIRED",
    "REQUEST_MEDIA_TYPE_UNSUPPORTED",
    "CARRIER_CREDITS_EXHAUSTED",
    "SYNTHETICS_USAGE_RESERVED",
    "TESTING_QUOTA_EXHAUSTED",
    "RATE_LIMITED",
    "NOTIFY_RATE",
    "SCOPE_REQUIRED",
    "RUN_TOKEN_ADDRESS_FORBIDDEN",
    "MONITOR_OWNED_BY_OTHER",
    "DEPLOY_LOCKED",
    "LIVE_REVISION_CHANGED",
    "CONFIRMATION_REQUIRED",
    "UPDATE_REQUIRED",
    "CLAIMED",
    "REVISION_ROLLED_BACK",
    "REVISION_NEVER_LIVE",
    "ROLLBACK_INCIDENT_REQUIRED",
    "REVISION_UNTESTED",
    "REVISION_DISCARDED",
    "REVISION_IS_LIVE",
    "DRAFT_LIMIT",
    "NO_TOKEN",
    "CLIENT_TOO_OLD",
    "MAX_RUNS_EXCEEDED",
    "IMPORT_NOT_IN_BUNDLE",
    "USE_PROBE",
    "IDEMPOTENCY_KEY_REUSED",
    "IDEMPOTENCY_KEY_IN_PROGRESS",
    "IDEMPOTENCY_KEY_ORPHANED",
    "TRIGGER_UNSUPPORTED_TYPE",
    "ENVIRONMENT_NOT_FOUND",
    "EVIDENCE_EXPIRED",
    "RUN_EXPIRED",
    "BUNDLE_TOO_LARGE",
    "BUNDLE_NOT_FOUND",
    "IMPORT_NOT_IN_RUNTIME",
    "SECRET_LITERAL",
    "FIELD_UNKNOWN",
    "API_KEY_EXPIRED",
    "DEVICE_AUTHORIZATION_NOT_FOUND",
    "DEVICE_AUTHORIZATION_EXPIRED",
    "DEVICE_WORKSPACE_ORG_MISMATCH",
]
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
InboundOtpCodeSource = Literal["text", "html"]
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
LinkedIncidentDtoStatus = Literal["WATCHING", "TRIGGERED", "CONFIRMED", "RESOLVED"]
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
MonitorDtoBindingReadiness = Literal["ready", "blocked", "not_applicable"]
MonitorDtoCurrentStatus = Literal["up", "degraded", "down", "paused", "unknown"]
MonitorDtoDisplayHealth = Literal[
    "healthy",
    "down",
    "degraded",
    "recovering",
    "infra",
    "flaky",
    "blocked",
    "capped",
    "paused",
    "never_run",
    "confirming",
]
MonitorDtoFlakySeverity = Literal["low", "medium", "high"]
MonitorDtoLastCheckOutcome = Literal["passed", "degraded", "failed"]
MonitorDtoManagedBy = Literal["DASHBOARD", "CLI", "TERRAFORM", "MCP", "API"]
MonitorDtoType = Literal[
    "HTTP", "DNS", "MCP_SERVER", "TCP", "ICMP", "HEARTBEAT", "BROWSER", "MULTI_STEP_API"
]
MonitorFacetDtoField = Literal[
    "type", "environment", "region", "tag", "owner", "project"
]
MonitorFacetValueDtoOwner = Literal["DASHBOARD", "CLI", "TERRAFORM", "MCP", "API"]
MonitorFacetValueDtoWorstState = Literal[
    "healthy",
    "down",
    "degraded",
    "recovering",
    "infra",
    "flaky",
    "blocked",
    "capped",
    "paused",
    "never_run",
    "confirming",
]
MonitorHistoryTickDtoOutcome = Literal["passed", "degraded", "failed"]
MonitorListGroupDtoKey = Literal[
    "failing", "not_running", "flaky", "passing", "running", "paused"
]
MonitorOwnerDtoType = Literal["DASHBOARD", "CLI", "TERRAFORM", "MCP", "API"]
MonitorOwnershipMetadataFromOwner = Literal[
    "DASHBOARD", "CLI", "TERRAFORM", "MCP", "API"
]
MonitorOwnershipMetadataKind = Literal["monitor_ownership"]
MonitorOwnershipMetadataToOwner = Literal["DASHBOARD", "CLI", "TERRAFORM", "MCP", "API"]
MonitorRegionHealthDtoVerdict = Literal["up", "degraded", "down", "paused", "unknown"]
MonitorRegionalHealthDtoRegionalDisplayHealth = Literal[
    "healthy",
    "down",
    "degraded",
    "recovering",
    "infra",
    "flaky",
    "blocked",
    "capped",
    "paused",
    "never_run",
    "confirming",
]
MonitorSessionDtoLifecycle = Literal["active", "expired", "failed", "revoked"]
MonitorSessionDtoReusePolicy = Literal["reuse", "every_run", "on_failure"]
MonitorTestRequestType = Literal[
    "HTTP", "DNS", "MCP_SERVER", "TCP", "ICMP", "HEARTBEAT", "BROWSER", "MULTI_STEP_API"
]
MonitorValidationFindingDtoSeverity = Literal["ERROR", "WARNING"]
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
PickerItemOutcome = Literal[
    "passed",
    "failed",
    "execution_error",
    "timed_out",
    "passed_on_retry",
    "cancelled",
    "inconclusive",
]
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
RevisionDiffHunkDtoChange = Literal["added", "removed", "changed"]
RevisionDtoCreatedByKind = Literal["dashboard", "git", "terraform", "api", "mcp"]
RevisionDtoState = Literal[
    "draft", "tested_passed", "tested_failed", "live", "previous", "discarded"
]
RevisionDtoTestOutcome = Literal["passed", "failed"]
RootlyChannelConfigChannelType = Literal["rootly"]
RowVerdict = Literal["unchanged", "much_slower", "now_failing", "not_reached"]
RunArtifactDtoCaptureReason = Literal["on_failure", "named_step", "customer"]
RunArtifactDtoKind = Literal[
    "screenshot", "video", "trace", "har", "console", "runner_log"
]
RunArtifactDtoLifecycle = Literal[
    "available",
    "processing",
    "failed",
    "not_captured",
    "suppressed",
    "never_reached",
    "expired",
    "no_browser",
]
RunAttemptDtoOutcome = Literal[
    "passed",
    "failed",
    "execution_error",
    "timed_out",
    "passed_on_retry",
    "cancelled",
    "inconclusive",
]
RunCaseDtoStatus = Literal[
    "pending", "running", "passed", "failed", "timed_out", "skipped", "interrupted"
]
RunDiffDtoBaselineKind = Literal[
    "last_pass_same_revision_region",
    "last_pass_any_revision",
    "attempts_in_run",
    "none",
    "selected_run",
]
RunDtoCause = Literal[
    "platform",
    "runtime_unavailable",
    "testing_quota_exhausted",
    "no_seat",
    "lease_lost",
    "target_unreachable",
]
RunDtoMonitorType = Literal[
    "HTTP", "DNS", "MCP_SERVER", "TCP", "ICMP", "HEARTBEAT", "BROWSER", "MULTI_STEP_API"
]
RunDtoOutcome = Literal[
    "passed",
    "failed",
    "execution_error",
    "timed_out",
    "passed_on_retry",
    "cancelled",
    "inconclusive",
]
RunDtoPhase = Literal[
    "created", "queued", "starting", "running", "finalizing", "finished"
]
RunDtoSource = Literal[
    "schedule",
    "run_now",
    "ci",
    "fast_retry",
    "remote_validation",
    "deployment_validation",
    "session_renew",
]
RunEventDtoType = Literal[
    "phase",
    "headline",
    "case_started",
    "case_finished",
    "step_started",
    "step_finished",
    "artifact_ready",
    "artifact_lifecycle",
    "finished",
    "stream_gap",
]
RunEvidenceDtoKind = Literal["screenshot", "trace", "video", "network"]
RunEvidenceDtoState = Literal["present", "bad", "processing", "expired"]
RunExecutionDtoMonitorType = Literal[
    "HTTP", "DNS", "MCP_SERVER", "TCP", "ICMP", "HEARTBEAT", "BROWSER", "MULTI_STEP_API"
]
RunFailureDtoKind = Literal[
    "assertion",
    "timeout",
    "navigation",
    "network",
    "target_blocked",
    "script_error",
    "wait_timeout",
    "setup",
]
RunStepDtoCategory = Literal["named", "assertion", "browser_action"]
RunStepDtoStatus = Literal[
    "pending",
    "running",
    "passed",
    "slow",
    "failed",
    "skipped",
    "suppressed",
    "never_reached",
    "timed_out",
]
RuntimeProfileDtoStatus = Literal["baking", "available", "deprecated", "retired"]
SecretRequestDtoFulfilledBy = Literal["env", "secret"]
SecretRequestDtoReadiness = Literal["resolved", "missing"]
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
TraceEntryPointId = Literal[
    "failing_action", "failing_step", "first_failed_request", "case_start"
]
TransferMonitorRequestTo = Literal["DASHBOARD", "CLI", "TERRAFORM", "MCP", "API"]
TriggerRuleAggregationType = Literal["all_exceed", "average", "p95", "max"]
TriggerRuleScope = Literal["per_region", "any_region"]
TriggerRuleSeverity = Literal["down", "degraded"]
TriggerRuleType = Literal["consecutive_failures", "failures_in_window", "response_time"]
TriggerRunRefPhase = Literal[
    "created", "queued", "starting", "running", "finalizing", "finished"
]
UpdateAlertChannelRequestManagedBy = Literal[
    "DASHBOARD", "CLI", "TERRAFORM", "MCP", "API"
]
UpdateAssertionRequestSeverity = Literal["fail", "warn"]
UpdateDatadogChannelConfigChannelType = Literal["datadog"]
UpdateDiscordChannelConfigChannelType = Literal["discord"]
UpdateEmailChannelConfigChannelType = Literal["email"]
UpdateEmailDomainRequestStatus = Literal[
    "active", "disabled", "pending_dns", "verification_failed"
]
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
UpdateWebhookInboxRequestStatus = Literal["active", "disabled"]
UpdateZapierChannelConfigChannelType = Literal["zapier"]
UpsertMonitorSessionRequestReusePolicy = Literal["reuse", "every_run", "on_failure"]
UserDtoOnboardingStage = Literal[
    "WELCOME", "FIRST_MONITOR", "SETUP_COMPLETE", "COMPLETED"
]
UserDtoUserRole = Literal["SUPERADMIN", "ADMIN", "USER"]
WebhookChannelConfigChannelType = Literal["webhook"]
WebhookInboxDtoStatus = Literal["active", "disabled"]
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
    "ApiKeyCreateResponseTool",
    "ApiKeyDtoTool",
    "AssertionResultDtoSeverity",
    "AssertionTestResultDtoAssertionType",
    "AssertionTestResultDtoSeverity",
    "BasicAuthConfigType",
    "BearerAuthConfigType",
    "BodyContainsAssertionType",
    "BulkMonitorActionRequestAction",
    "CaptureCompareDtoBaselineKind",
    "CapturePolicyNetwork",
    "CapturePolicyScreenshots",
    "CapturePolicyTrace",
    "CapturePolicyVideo",
    "ChangeRoleRequestOrgRole",
    "ChangeStatusRequestStatus",
    "CodeCheckType",
    "ConfirmationPolicyType",
    "CreateAlertChannelRequestManagedBy",
    "CreateApiKeyRequestTool",
    "CreateAssertionRequestSeverity",
    "CreateEmailDomainRequestKind",
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
    "CreateWebhookInboxRequestStatus",
    "DatadogChannelConfigChannelType",
    "DayIncidentImpact",
    "DayIncidentStatus",
    "DemoBookingDtoState",
    "DeviceTokenDtoStatus",
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
    "EmailDomainDtoKind",
    "EmailDomainDtoStatus",
    "EntitlementResponseTier",
    "ErrorResponseReason",
    "EvidencePurgedMetadataKind",
    "FindingCode",
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
    "InboundOtpCodeSource",
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
    "LinkedIncidentDtoStatus",
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
    "MonitorDtoBindingReadiness",
    "MonitorDtoCurrentStatus",
    "MonitorDtoDisplayHealth",
    "MonitorDtoFlakySeverity",
    "MonitorDtoLastCheckOutcome",
    "MonitorDtoManagedBy",
    "MonitorDtoType",
    "MonitorFacetDtoField",
    "MonitorFacetValueDtoOwner",
    "MonitorFacetValueDtoWorstState",
    "MonitorHistoryTickDtoOutcome",
    "MonitorListGroupDtoKey",
    "MonitorOwnerDtoType",
    "MonitorOwnershipMetadataFromOwner",
    "MonitorOwnershipMetadataKind",
    "MonitorOwnershipMetadataToOwner",
    "MonitorRegionHealthDtoVerdict",
    "MonitorRegionalHealthDtoRegionalDisplayHealth",
    "MonitorSessionDtoLifecycle",
    "MonitorSessionDtoReusePolicy",
    "MonitorTestRequestType",
    "MonitorValidationFindingDtoSeverity",
    "MonitorVersionDtoChangedVia",
    "NotificationDispatchDtoCompletionReason",
    "NotificationDispatchDtoStatus",
    "OpsGenieChannelConfigChannelType",
    "OrgIncidentAnnotationDtoSeverity",
    "OrgIncidentAnnotationDtoStatus",
    "PagerDutyChannelConfigChannelType",
    "PhoneCallChannelConfigChannelType",
    "PickerItemOutcome",
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
    "RevisionDiffHunkDtoChange",
    "RevisionDtoCreatedByKind",
    "RevisionDtoState",
    "RevisionDtoTestOutcome",
    "RootlyChannelConfigChannelType",
    "RowVerdict",
    "RunArtifactDtoCaptureReason",
    "RunArtifactDtoKind",
    "RunArtifactDtoLifecycle",
    "RunAttemptDtoOutcome",
    "RunCaseDtoStatus",
    "RunDiffDtoBaselineKind",
    "RunDtoCause",
    "RunDtoMonitorType",
    "RunDtoOutcome",
    "RunDtoPhase",
    "RunDtoSource",
    "RunEventDtoType",
    "RunEvidenceDtoKind",
    "RunEvidenceDtoState",
    "RunExecutionDtoMonitorType",
    "RunFailureDtoKind",
    "RunStepDtoCategory",
    "RunStepDtoStatus",
    "RuntimeProfileDtoStatus",
    "SecretRequestDtoFulfilledBy",
    "SecretRequestDtoReadiness",
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
    "TraceEntryPointId",
    "TransferMonitorRequestTo",
    "TriggerRuleAggregationType",
    "TriggerRuleScope",
    "TriggerRuleSeverity",
    "TriggerRuleType",
    "TriggerRunRefPhase",
    "UpdateAlertChannelRequestManagedBy",
    "UpdateAssertionRequestSeverity",
    "UpdateDatadogChannelConfigChannelType",
    "UpdateDiscordChannelConfigChannelType",
    "UpdateEmailChannelConfigChannelType",
    "UpdateEmailDomainRequestStatus",
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
    "UpdateWebhookInboxRequestStatus",
    "UpdateZapierChannelConfigChannelType",
    "UpsertMonitorSessionRequestReusePolicy",
    "UserDtoOnboardingStage",
    "UserDtoUserRole",
    "WebhookChannelConfigChannelType",
    "WebhookInboxDtoStatus",
    "ZapierChannelConfigChannelType",
]
