"""Automation routing preserves real boundaries while ignoring changing labels."""
from dataclasses import replace

from gateway.config import Platform
from gateway.session import SessionSource, build_session_key
from gateway.session_automation import _route_identity


def test_thread_followup_and_renamed_labels_keep_same_route():
    origin = SessionSource(
        platform=Platform.DISCORD, chat_id="channel", chat_type="thread",
        user_id="user", thread_id="thread", scope_id="guild", profile="coding",
        chat_name="old chat", chat_topic="old topic", user_name="old name",
        message_id="first", auto_thread_created=True, auto_thread_initial_name="initial",
    )
    followup = replace(
        origin, chat_name="new chat", chat_topic="new topic", user_name="new name",
        message_id="second", auto_thread_created=False, auto_thread_initial_name=None,
    )
    assert _route_identity(origin) == _route_identity(followup)


def test_prospective_discord_thread_matches_its_real_thread_only():
    initiating = SessionSource(
        platform=Platform.DISCORD, chat_id="channel", chat_type="group", user_id="user",
        scope_id="guild", profile="coding", prospective_thread_id="thread",
    )
    followup = replace(initiating, chat_type="thread", prospective_thread_id=None, thread_id="thread")
    other_thread = replace(followup, thread_id="other-thread")
    assert build_session_key(initiating) == build_session_key(followup)
    assert _route_identity(initiating) == _route_identity(followup)
    assert _route_identity(initiating) != _route_identity(other_thread)
    assert _route_identity(initiating) != _route_identity(replace(followup, prospective_thread_id='other-thread'))
    assert _route_identity(replace(initiating, platform=Platform.TELEGRAM)) != _route_identity(
        replace(followup, platform=Platform.TELEGRAM)
    )
    for field, value in {"chat_id": "other-channel", "user_id": "other-user",
                         "scope_id": "other-guild", "profile": "other-profile"}.items():
        assert _route_identity(initiating) != _route_identity(replace(followup, **{field: value})), field


def test_changed_security_and_routing_fields_do_not_share_route():
    source = SessionSource(
        platform=Platform.DISCORD, chat_id="channel", chat_type="thread",
        user_id="user", thread_id="thread", scope_id="guild", profile="coding",
        parent_chat_id="parent", user_id_alt="alt-user", chat_id_alt="alt-chat",
        prospective_thread_id="prospective",
    )
    for field, value in {
        "platform": Platform.TELEGRAM, "chat_id": "other-channel", "chat_type": "group",
        "user_id": "other-user", "thread_id": "other-thread", "scope_id": "other-guild",
        "profile": "other-profile", "parent_chat_id": "other-parent",
        "user_id_alt": "other-alt-user", "chat_id_alt": "other-alt-chat",
        "prospective_thread_id": "other-prospective",
    }.items():
        assert _route_identity(source) != _route_identity(replace(source, **{field: value})), field
