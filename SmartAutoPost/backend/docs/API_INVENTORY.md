# API Inventory

Base prefix: `/api/v1`

Generated from the project router source files.

## Ai Caption

| Method | Route | Handler |
|---|---|---|
| POST | `/api/v1/ai/generate-caption` | `generate_caption` |

## Ai Hashtag

| Method | Route | Handler |
|---|---|---|
| POST | `/api/v1/ai/generate-hashtags` | `generate_hashtags` |

## Ai Image Prompt

| Method | Route | Handler |
|---|---|---|
| POST | `/api/v1/ai/generate-image-prompt` | `generate_image_prompt` |

## Ai Seo

| Method | Route | Handler |
|---|---|---|
| POST | `/api/v1/ai/generate-seo` | `generate_seo` |

## Analytics

| Method | Route | Handler |
|---|---|---|
| GET | `/api/v1/analytics/summary` | `get_analytics_summary` |

## Audit Log

| Method | Route | Handler |
|---|---|---|
| POST | `/api/v1/audit-logs/` | `create_audit_log` |
| GET | `/api/v1/audit-logs/` | `list_audit_logs` |
| GET | `/api/v1/audit-logs/{audit_log_id}` | `get_audit_log` |
| DELETE | `/api/v1/audit-logs/{audit_log_id}` | `delete_audit_log` |

## Auth

| Method | Route | Handler |
|---|---|---|
| POST | `/api/v1/auth/register` | `register_user` |
| POST | `/api/v1/auth/login` | `login_user` |
| GET | `/api/v1/auth/me` | `get_my_profile` |
| POST | `/api/v1/auth/refresh` | `refresh_access_token` |
| POST | `/api/v1/auth/logout` | `logout` |
| POST | `/api/v1/auth/verify-email` | `verify_email` |
| POST | `/api/v1/auth/forgot-password` | `forgot_password` |
| POST | `/api/v1/auth/reset-password` | `reset_password` |
| POST | `/api/v1/auth/2fa/enable` | `enable_2fa` |
| POST | `/api/v1/auth/2fa/verify` | `verify_2fa` |
| GET | `/api/v1/auth/reset-password` | `reset_password_page` |

## Brand Kit

| Method | Route | Handler |
|---|---|---|
| POST | `/api/v1/brand-kits` | `create_brand_kit` |
| GET | `/api/v1/brand-kits` | `list_brand_kits` |
| GET | `/api/v1/brand-kits/{brand_kit_id}` | `get_brand_kit` |
| PUT | `/api/v1/brand-kits/{brand_kit_id}` | `update_brand_kit` |
| DELETE | `/api/v1/brand-kits/{brand_kit_id}` | `delete_brand_kit` |

## Calendar

| Method | Route | Handler |
|---|---|---|
| GET | `/api/v1/calendar/` | `get_calendar_posts` |

## Competitor

| Method | Route | Handler |
|---|---|---|
| POST | `/api/v1/competitors` | `create_competitor` |
| GET | `/api/v1/competitors` | `list_competitors` |
| GET | `/api/v1/competitors/{competitor_id}` | `get_competitor` |
| PUT | `/api/v1/competitors/{competitor_id}` | `update_competitor` |
| DELETE | `/api/v1/competitors/{competitor_id}` | `delete_competitor` |

## Competitor Metric

| Method | Route | Handler |
|---|---|---|
| POST | `/api/v1/competitor-metrics` | `create_metric` |
| GET | `/api/v1/competitor-metrics` | `list_metrics` |
| GET | `/api/v1/competitor-metrics/{metric_id}` | `get_metric` |
| PUT | `/api/v1/competitor-metrics/{metric_id}` | `update_metric` |
| DELETE | `/api/v1/competitor-metrics/{metric_id}` | `delete_metric` |

## Coupon

| Method | Route | Handler |
|---|---|---|
| POST | `/api/v1/coupons/` | `create_coupon` |
| GET | `/api/v1/coupons/` | `list_coupons` |
| POST | `/api/v1/coupons/validate` | `validate_coupon` |
| GET | `/api/v1/coupons/{coupon_id}` | `get_coupon` |
| PUT | `/api/v1/coupons/{coupon_id}` | `update_coupon` |
| DELETE | `/api/v1/coupons/{coupon_id}` | `delete_coupon` |

## Dashboard

| Method | Route | Handler |
|---|---|---|
| GET | `/api/v1/dashboard/summary` | `get_dashboard_summary` |
| GET | `/api/v1/dashboard/recent-posts` | `get_dashboard_recent_posts` |
| GET | `/api/v1/dashboard/activity` | `get_dashboard_activity` |
| GET | `/api/v1/dashboard/charts` | `get_dashboard_charts` |

## Gemini

| Method | Route | Handler |
|---|---|---|
| POST | `/api/v1/ai/gemini-generate` | `gemini_generate` |

## Health

| Method | Route | Handler |
|---|---|---|
| GET | `/api/v1/health` | `health_check` |

## Invoice

| Method | Route | Handler |
|---|---|---|
| POST | `/api/v1/invoices/from-payment/{payment_id}` | `create_invoice_from_payment` |
| GET | `/api/v1/invoices/` | `list_invoices` |
| GET | `/api/v1/invoices/{invoice_id}/download` | `download_invoice_pdf` |
| GET | `/api/v1/invoices/{invoice_id}` | `get_invoice` |

## Media

| Method | Route | Handler |
|---|---|---|
| GET | `/api/v1/media/` | `media_home` |
| POST | `/api/v1/media/upload` | `upload_media` |
| GET | `/api/v1/media/list` | `list_media` |
| DELETE | `/api/v1/media/{media_id}` | `delete_media` |

## Member Role

| Method | Route | Handler |
|---|---|---|
| POST | `/api/v1/member-roles/members/{member_id}/assign/{role_id}` | `assign_role` |
| DELETE | `/api/v1/member-roles/members/{member_id}/remove/{role_id}` | `remove_role` |
| GET | `/api/v1/member-roles/members/{member_id}` | `get_member_roles` |

## Notification

| Method | Route | Handler |
|---|---|---|
| GET | `/api/v1/notifications/` | `get_notifications` |
| GET | `/api/v1/notifications/unread-count` | `get_unread_count` |
| PUT | `/api/v1/notifications/read-all` | `mark_all_notifications_as_read` |
| PUT | `/api/v1/notifications/{notification_id}/read` | `mark_notification_as_read` |
| DELETE | `/api/v1/notifications/{notification_id}` | `delete_notification` |

## Organization

| Method | Route | Handler |
|---|---|---|
| POST | `/api/v1/organizations/` | `create_organization` |
| GET | `/api/v1/organizations/` | `list_my_organizations` |
| GET | `/api/v1/organizations/{organization_id}` | `get_organization_detail` |
| PUT | `/api/v1/organizations/{organization_id}` | `update_organization` |
| DELETE | `/api/v1/organizations/{organization_id}` | `delete_organization` |

## Organization Member

| Method | Route | Handler |
|---|---|---|
| POST | `/api/v1/organizations/{organization_id}/members` | `add_member` |
| GET | `/api/v1/organizations/{organization_id}/members` | `list_members` |
| PUT | `/api/v1/organizations/{organization_id}/members/{member_id}` | `update_member_role` |
| DELETE | `/api/v1/organizations/{organization_id}/members/{member_id}` | `remove_member` |

## Payment

| Method | Route | Handler |
|---|---|---|
| POST | `/api/v1/payments/` | `create_payment` |
| GET | `/api/v1/payments/` | `list_payments` |
| GET | `/api/v1/payments/{payment_id}` | `get_payment` |

## Permission

| Method | Route | Handler |
|---|---|---|
| POST | `/api/v1/permissions/seed` | `seed_permissions` |
| GET | `/api/v1/permissions` | `list_permissions` |
| GET | `/api/v1/permissions/{permission_id}` | `get_permission` |
| POST | `/api/v1/permissions/roles/{role_id}/assign/{permission_id}` | `assign_permission` |
| DELETE | `/api/v1/permissions/roles/{role_id}/remove/{permission_id}` | `remove_permission` |
| GET | `/api/v1/permissions/roles/{role_id}` | `role_permissions` |

## Plan

| Method | Route | Handler |
|---|---|---|
| GET | `/api/v1/plans/` | `list_plans` |
| GET | `/api/v1/plans/{plan_id}` | `get_plan` |
| POST | `/api/v1/plans/` | `create_plan` |
| PUT | `/api/v1/plans/{plan_id}` | `update_plan` |
| DELETE | `/api/v1/plans/{plan_id}` | `delete_plan` |

## Post

| Method | Route | Handler |
|---|---|---|
| POST | `/api/v1/posts/` | `create_post` |
| GET | `/api/v1/posts/` | `list_posts` |
| POST | `/api/v1/posts/{post_id}/attach-media` | `attach_media` |
| PUT | `/api/v1/posts/{post_id}/schedule` | `schedule_post` |
| GET | `/api/v1/posts/{post_id}` | `get_post_detail` |
| PUT | `/api/v1/posts/{post_id}` | `update_post` |
| DELETE | `/api/v1/posts/{post_id}` | `delete_post` |

## Post Analytic

| Method | Route | Handler |
|---|---|---|
| POST | `/api/v1/post-analytics` | `create_post_analytic` |
| GET | `/api/v1/post-analytics` | `list_post_analytics` |
| GET | `/api/v1/post-analytics/{analytic_id}` | `get_post_analytic` |
| PUT | `/api/v1/post-analytics/{analytic_id}` | `update_post_analytic` |
| DELETE | `/api/v1/post-analytics/{analytic_id}` | `delete_post_analytic` |

## Post Schedule

| Method | Route | Handler |
|---|---|---|
| POST | `/api/v1/post-schedules/` | `create_schedule` |
| POST | `/api/v1/post-schedules/process` | `process_pending_schedules` |

## Publishing

| Method | Route | Handler |
|---|---|---|
| POST | `/api/v1/publish/{post_id}` | `publish_post` |
| POST | `/api/v1/publish/retry/{post_id}` | `retry_publish` |
| GET | `/api/v1/publish/logs/{post_id}` | `get_publish_logs` |
| GET | `/api/v1/publish/status/{post_id}` | `get_publish_status` |

## Refund

| Method | Route | Handler |
|---|---|---|
| POST | `/api/v1/refunds/` | `create_refund` |
| GET | `/api/v1/refunds/` | `list_refunds` |
| GET | `/api/v1/refunds/{refund_id}` | `get_refund` |

## Role

| Method | Route | Handler |
|---|---|---|
| POST | `/api/v1/roles` | `create_role` |
| GET | `/api/v1/roles` | `list_roles` |
| GET | `/api/v1/roles/{role_id}` | `get_role` |
| PUT | `/api/v1/roles/{role_id}` | `update_role` |
| DELETE | `/api/v1/roles/{role_id}` | `delete_role` |

## Social Account

| Method | Route | Handler |
|---|---|---|
| POST | `/api/v1/social-accounts/` | `connect_social_account` |
| GET | `/api/v1/social-accounts/` | `list_social_accounts` |
| DELETE | `/api/v1/social-accounts/{account_id}` | `delete_social_account` |

## Subscription

| Method | Route | Handler |
|---|---|---|
| POST | `/api/v1/subscriptions/` | `create_subscription` |
| GET | `/api/v1/subscriptions/current` | `get_current_subscription` |
| GET | `/api/v1/subscriptions/history` | `get_subscription_history` |
| DELETE | `/api/v1/subscriptions/current` | `cancel_current_subscription` |

## Usage

| Method | Route | Handler |
|---|---|---|
| GET | `/api/v1/usage/summary` | `get_usage_summary` |
| GET | `/api/v1/usage/{usage_type}` | `get_usage_detail` |
| POST | `/api/v1/usage/{usage_type}/increment` | `increment_usage` |
