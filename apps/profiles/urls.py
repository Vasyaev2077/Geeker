from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = "profiles"

urlpatterns = [
    path("", views.ProfileDetailView.as_view(), name="detail"),
    path("edit/", views.ProfileUpdateView.as_view(), name="edit"),
    path("settings/", views.ProfileSettingsView.as_view(), name="settings"),
    path("posts/create/", views.ProfilePostCreateView.as_view(), name="post_create"),
    path("posts/<int:pk>/edit/", views.ProfilePostUpdateView.as_view(), name="post_edit"),
    path("posts/<int:pk>/pin/", views.ProfilePostTogglePinView.as_view(), name="post_pin"),
    path("posts/<int:pk>/vote/", views.ProfilePostVoteView.as_view(), name="post_vote"),
    path(
        "posts/<int:pk>/comments/create/",
        views.ProfilePostCommentCreateView.as_view(),
        name="post_comment_create",
    ),
    path(
        "posts/<int:pk>/toggle-comments/",
        views.ProfilePostToggleCommentsView.as_view(),
        name="post_toggle_comments",
    ),
    path("posts/<int:pk>/delete/", views.ProfilePostDeleteView.as_view(), name="post_delete"),
    path(
        "settings/privacy/",
        TemplateView.as_view(
            template_name="profiles/settings_section.html",
            extra_context={"title": "Конфиденциальность"},
        ),
        name="settings_privacy",
    ),
    path(
        "settings/notifications/",
        TemplateView.as_view(
            template_name="profiles/settings_section.html",
            extra_context={"title": "Уведомления и звуки"},
        ),
        name="settings_notifications",
    ),
    path(
        "settings/chat/",
        TemplateView.as_view(
            template_name="profiles/settings_section.html",
            extra_context={"title": "Настройки чатов"},
        ),
        name="settings_chat",
    ),
    path(
        "settings/advanced/",
        TemplateView.as_view(
            template_name="profiles/settings_section.html",
            extra_context={"title": "Продвинутые настройки"},
        ),
        name="settings_advanced",
    ),
    path(
        "settings/audio-video/",
        TemplateView.as_view(
            template_name="profiles/settings_section.html",
            extra_context={"title": "Звук и камера"},
        ),
        name="settings_audio_video",
    ),
]







