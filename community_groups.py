# ============================================================
# ECOLOOP NODE — COMMUNITY HUB
# Clean replacement module
# Powered by Next Gen Impact Hub (NGIH)
# ============================================================
#
# Main navigation:
#   1. Chats   — private conversations, people directory, profile
#   2. Groups  — discover, manage and chat in community groups
#   3. Updates — 24-hour photo/video stories
#   4. Discover — search people and groups
#
# Integration:
#   render_community_groups_page(supabase, user_id)
#
# This module intentionally avoids st.tabs() and appended overrides.
# It uses the existing Supabase tables described in the project.
# Optional read receipts use direct_conversation_reads; if that table
# is not installed, the inbox still works and simply omits unread counts.
# ============================================================

import mimetypes
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import streamlit as st


BUCKET = "community-media"
MAX_IMAGE_MB = 8
MAX_VIDEO_MB = 35
MAIN_NAV_KEY = "eco_community_navigation_v3"


# ------------------------------
# General helpers
# ------------------------------

def eco_now():
    return datetime.now(timezone.utc)


def eco_iso(value=None):
    value = value or eco_now()
    if isinstance(value, str):
        return value
    return value.isoformat()


def eco_escape(value):
    # Plain text only: this module deliberately does not render HTML.
    return str(value or "")


def eco_safe_text(value, default=""):
    text = str(value or "").strip()
    return text if text else default


def eco_notify(message, kind="info"):
    try:
        getattr(st, kind)(message)
    except Exception:
        st.info(message)


def eco_init_state():
    defaults = {
        "eco_community_section": "Chats",
        "eco_chat_view": "Inbox",
        "eco_active_conversation": None,
        "eco_active_chatroom": None,
        "eco_people_search": "",
        "eco_group_view": "Discover",
        "eco_story_view": "Recent Updates",
        "eco_discover_search": "",
        "eco_profile_view_user": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def eco_result_data(result):
    try:
        return result.data or []
    except Exception:
        return []


def eco_select(supabase, table, columns="*", filters=None, order=None, limit=None):
    query = supabase.table(table).select(columns)
    for method, column, value in (filters or []):
        query = getattr(query, method)(column, value)
    if order:
        column, desc = order
        query = query.order(column, desc=desc)
    if limit:
        query = query.limit(limit)
    return eco_result_data(query.execute())


def eco_profile(supabase, user_id):
    if not user_id:
        return {}
    try:
        rows = eco_select(
            supabase, "member_profiles", "*",
            [("eq", "user_id", user_id)], limit=1
        )
        return rows[0] if rows else {}
    except Exception:
        return {}


def eco_display_name(profile, fallback="EcoLoop member"):
    return eco_safe_text(
        (profile or {}).get("display_name")
        or (profile or {}).get("username"),
        fallback
    )


def eco_initials(name):
    words = [w for w in str(name or "E").strip().split() if w]
    if not words:
        return "E"
    return "".join(w[0].upper() for w in words[:2])


def eco_avatar(profile, size=48):
    profile = profile or {}
    avatar = profile.get("avatar_url")
    if avatar:
        st.image(avatar, width=size)
    else:
        st.subheader(eco_initials(eco_display_name(profile)))


def eco_storage_url(supabase, path, expires=3600):
    if not path:
        return ""
    try:
        result = supabase.storage.from_(BUCKET).create_signed_url(path, expires)
        if isinstance(result, dict):
            return result.get("signedURL") or result.get("signedUrl") or ""
        return ""
    except Exception:
        return path if str(path).startswith("http") else ""


def eco_upload(supabase, uploaded, folder, user_id, allow_video=False, allow_documents=False):
    if not uploaded:
        return ""
    name = os.path.basename(uploaded.name or "upload")
    ext = os.path.splitext(name)[1].lower()
    allowed_images = {".jpg", ".jpeg", ".png", ".webp"}
    allowed_videos = {".mp4", ".mov", ".webm"}
    allowed_documents = {".pdf"}
    allowed = allowed_images | (allowed_videos if allow_video else set()) | (allowed_documents if allow_documents else set())
    if ext not in allowed:
        raise ValueError("Please choose a supported image" + (" or video." if allow_video else "."))
    limit = MAX_VIDEO_MB if ext in allowed_videos else MAX_IMAGE_MB
    if uploaded.size > limit * 1024 * 1024:
        raise ValueError(f"File is too large. Maximum size is {limit} MB.")
    path = f"{folder}/{user_id}/{uuid.uuid4().hex}{ext}"
    content_type = uploaded.type or mimetypes.guess_type(name)[0] or "application/octet-stream"
    supabase.storage.from_(BUCKET).upload(
        path, uploaded.getvalue(),
        {"content-type": content_type, "upsert": "false"}
    )
    return path


def eco_header(title, subtitle=None):
    st.subheader(title)
    if subtitle:
        st.caption(subtitle)


def eco_inject_styles():
    # Native Streamlit components only. No injected HTML or CSS.
    return None


# ------------------------------
# Member profiles and discovery
# ------------------------------

def save_member_profile(supabase, user_id, values):
    payload = {"user_id": user_id}
    allowed = (
        "display_name", "username", "bio", "location", "interests",
        "country_of_origin", "instagram_handle", "facebook_handle",
        "tiktok_handle", "linkedin_handle", "avatar_url"
    )
    for key in allowed:
        if key in values:
            payload[key] = values[key]
    return supabase.table("member_profiles").upsert(
        payload, on_conflict="user_id"
    ).execute()


def render_profile_editor(supabase, user_id):
    profile = eco_profile(supabase, user_id)
    eco_header("My profile", "Your community identity")
    with st.form("eco_profile_edit_form", clear_on_submit=False):
        display_name = st.text_input("Display name", value=profile.get("display_name", ""))
        username = st.text_input("Username", value=profile.get("username", ""), help="Use a unique username without spaces.")
        bio = st.text_area("About me", value=profile.get("bio", ""), max_chars=240)
        location = st.text_input("Location (optional)", value=profile.get("location", ""))
        country = st.text_input("Country of origin (optional)", value=profile.get("country_of_origin", ""))
        interests = st.text_input("Interests (comma separated)", value=profile.get("interests", ""))
        st.caption("Social handles are optional.")
        instagram = st.text_input("Instagram", value=profile.get("instagram_handle", ""))
        facebook = st.text_input("Facebook", value=profile.get("facebook_handle", ""))
        tiktok = st.text_input("TikTok", value=profile.get("tiktok_handle", ""))
        linkedin = st.text_input("LinkedIn", value=profile.get("linkedin_handle", ""))
        submitted = st.form_submit_button("Save profile", use_container_width=True)
    avatar_file = st.file_uploader("Update profile picture", type=["jpg", "jpeg", "png", "webp"], key="eco_profile_avatar_upload")
    if avatar_file:
        if st.button("Upload profile picture", key="eco_profile_avatar_save"):
            try:
                path = eco_upload(supabase, avatar_file, "profiles", user_id)
                save_member_profile(supabase, user_id, {"avatar_url": path})
                st.success("Profile picture updated.")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not upload picture: {exc}")
    if submitted:
        username = re.sub(r"[^a-zA-Z0-9_.]", "", username).lower()
        if len(username) < 3:
            st.error("Choose a username with at least 3 letters or numbers.")
        else:
            try:
                save_member_profile(supabase, user_id, {
                    "display_name": display_name.strip(),
                    "username": username,
                    "bio": bio.strip(),
                    "location": location.strip(),
                    "country_of_origin": country.strip(),
                    "interests": interests.strip(),
                    "instagram_handle": instagram.strip(),
                    "facebook_handle": facebook.strip(),
                    "tiktok_handle": tiktok.strip(),
                    "linkedin_handle": linkedin.strip(),
                })
                st.success("Profile saved.")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not save profile. The username may already be taken. Details: {exc}")


def get_member_directory(supabase, search_text=""):
    """Search the full member_profiles table, including administrator accounts.

    A search is performed by Supabase rather than filtering only the first
    150 downloaded profiles. No role is excluded, so a Super Admin profile
    is discoverable by username just like any other member profile.
    """
    q = (search_text or "").strip().lower().lstrip("@").strip()
    try:
        if not q:
            return eco_select(
                supabase, "member_profiles", "*",
                order=("display_name", False), limit=150
            )

        # Search username first (the primary member lookup), then display
        # name and location. Merge by user_id to avoid duplicate cards.
        found = {}
        for column in ("username", "display_name", "location"):
            try:
                query = (
                    supabase.table("member_profiles")
                    .select("*")
                    .ilike(column, f"%{q}%")
                    .limit(100)
                )
                rows = eco_result_data(query.execute())
                for row in rows:
                    uid = str(row.get("user_id") or row.get("id") or "")
                    if uid:
                        found[uid] = row
            except Exception:
                # A missing optional search column must not prevent
                # username lookup or hide the rest of the directory.
                continue

        return sorted(
            found.values(),
            key=lambda row: (
                str(row.get("username") or "").lower(),
                str(row.get("display_name") or "").lower()
            )
        )
    except Exception:
        return []


def render_member_card(supabase, profile, current_user_id, key_suffix):
    uid = profile.get("user_id")
    name = eco_display_name(profile)
    username = eco_safe_text(profile.get("username"), "member")
    with st.container(border=True):
        left, right = st.columns([1, 4])
        with left:
            eco_avatar(profile, 52)
        with right:
            st.markdown(f"**{eco_escape(name)}**")
            st.caption(f"@{eco_escape(username)}")
            if profile.get("bio"):
                st.write(str(profile["bio"])[:150])
            if profile.get("location"):
                st.caption(f"📍 {profile['location']}")
        if uid and uid != current_user_id:
            a, b = st.columns(2)
            with a:
                if st.button("View profile", key=f"eco_person_profile_{key_suffix}_{uid}", use_container_width=True):
                    st.session_state.eco_profile_view_user = uid
                    st.session_state.eco_chat_view = "Profile"
                    st.rerun()
            with b:
                if st.button("Message", key=f"eco_person_message_{key_suffix}_{uid}", use_container_width=True):
                    try:
                        conv = get_or_create_direct_conversation(supabase, current_user_id, uid)
                        st.session_state.eco_active_conversation = conv
                        st.session_state.eco_chat_view = "Conversation"
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not open chat: {exc}")


def render_people_directory(supabase, user_id):
    eco_header("Discover people", "Find community members by name or username")
    query = st.text_input("Search people", key="eco_people_search_input", placeholder="Search username or name…")
    profiles = [p for p in get_member_directory(supabase, query) if p.get("user_id") != user_id]
    if not profiles:
        st.info("No members found yet. Try another username.")
        return
    for index, profile in enumerate(profiles):
        render_member_card(supabase, profile, user_id, f"directory_{index}")


def render_public_profile(supabase, user_id, current_user_id):
    profile = eco_profile(supabase, user_id)
    if not profile:
        st.warning("This profile is not available.")
        return
    name = eco_display_name(profile)
    col1, col2 = st.columns([1, 3])
    with col1:
        eco_avatar(profile, 76)
    with col2:
        st.subheader(name)
        st.caption("@" + eco_safe_text(profile.get("username"), "member"))
        if profile.get("location"):
            st.caption("📍 " + str(profile["location"]))
    if profile.get("bio"):
        st.write(profile["bio"])
    if profile.get("interests"):
        st.caption("Interests: " + str(profile["interests"]))
    socials = [
        ("Instagram", "instagram_handle"),
        ("Facebook", "facebook_handle"),
        ("TikTok", "tiktok_handle"),
        ("LinkedIn", "linkedin_handle"),
    ]
    present = [f"**{label}:** @{profile[key].lstrip('@')}" for label, key in socials if profile.get(key)]
    if present:
        st.markdown(" · ".join(present))
    if user_id != current_user_id:
        if st.button("Message", key=f"eco_public_profile_message_{user_id}", use_container_width=True):
            try:
                conv = get_or_create_direct_conversation(supabase, current_user_id, user_id)
                st.session_state.eco_active_conversation = conv
                st.session_state.eco_chat_view = "Conversation"
                st.rerun()
            except Exception as exc:
                st.error(f"Could not start conversation: {exc}")


# ------------------------------
# Private direct messages
# ------------------------------

def get_or_create_direct_conversation(supabase, user_a, user_b):
    first, second = sorted([str(user_a), str(user_b)])
    try:
        rows = eco_select(
            supabase, "direct_conversations", "*",
            [("eq", "user_one_id", first), ("eq", "user_two_id", second)],
            limit=1
        )
        if rows:
            return rows[0]["id"]
    except Exception:
        pass
    result = supabase.table("direct_conversations").insert({
        "user_one_id": first,
        "user_two_id": second
    }).execute()
    rows = eco_result_data(result)
    if rows:
        return rows[0]["id"]
    # Some Supabase clients return no inserted representation.
    rows = eco_select(
        supabase, "direct_conversations", "*",
        [("eq", "user_one_id", first), ("eq", "user_two_id", second)],
        limit=1
    )
    if not rows:
        raise RuntimeError("Conversation could not be created.")
    return rows[0]["id"]


def get_direct_conversations(supabase, user_id):
    try:
        rows_a = eco_select(
            supabase, "direct_conversations", "*",
            [("eq", "user_one_id", user_id)],
            order=("created_at", True), limit=150
        )
        rows_b = eco_select(
            supabase, "direct_conversations", "*",
            [("eq", "user_two_id", user_id)],
            order=("created_at", True), limit=150
        )
        unique = {str(row["id"]): row for row in rows_a + rows_b if row.get("id")}
        return list(unique.values())
    except Exception:
        return []


def get_direct_messages(supabase, conversation_id, limit=100):
    try:
        return eco_select(
            supabase, "direct_messages", "*",
            [("eq", "conversation_id", conversation_id), ("is_", "deleted_at", "null")],
            order=("created_at", False), limit=limit
        )
    except Exception:
        try:
            return eco_select(
                supabase, "direct_messages", "*",
                [("eq", "conversation_id", conversation_id)],
                order=("created_at", False), limit=limit
            )
        except Exception:
            return []


def send_direct_message(supabase, conversation_id, sender_id, message_text, attachment_path="", attachment_name="", attachment_type=""):
    payload = {
        "conversation_id": conversation_id,
        "sender_id": sender_id,
        "message_text": (message_text or "").strip(),
        "attachment_path": attachment_path or None,
        "attachment_name": attachment_name or None,
        "attachment_type": attachment_type or None,
    }
    if not payload["message_text"] and not attachment_path:
        return False
    supabase.table("direct_messages").insert(payload).execute()
    return True


def mark_direct_conversation_read(supabase, conversation_id, user_id):
    try:
        supabase.table("direct_conversation_reads").upsert({
            "conversation_id": conversation_id,
            "user_id": user_id,
            "last_read_at": eco_iso()
        }, on_conflict="conversation_id,user_id").execute()
        return True
    except Exception:
        return False


def get_read_timestamp(supabase, conversation_id, user_id):
    try:
        rows = eco_select(
            supabase, "direct_conversation_reads", "last_read_at",
            [("eq", "conversation_id", conversation_id), ("eq", "user_id", user_id)],
            limit=1
        )
        return rows[0].get("last_read_at") if rows else None
    except Exception:
        return None


def get_other_conversation_user(conversation, current_user_id):
    return conversation.get("user_two_id") if str(conversation.get("user_one_id")) == str(current_user_id) else conversation.get("user_one_id")


def _parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def eco_time_label(value):
    dt = _parse_dt(value)
    if not dt:
        return ""
    try:
        return dt.astimezone().strftime("%H:%M")
    except Exception:
        return str(value)[:16]


def eco_soft_delete_message(supabase, table, message_id, sender_id):
    """Soft-delete only the signed-in user's own message."""
    return supabase.table(table).update({"deleted_at": eco_iso()}).eq(
        "id", message_id
    ).eq("sender_id", sender_id).execute()


def eco_edit_message(supabase, table, message_id, sender_id, new_text):
    new_text = (new_text or "").strip()
    if not new_text:
        raise ValueError("A message cannot be empty.")
    return supabase.table(table).update({
        "message_text": new_text,
        "edited_at": eco_iso(),
    }).eq("id", message_id).eq("sender_id", sender_id).execute()


def eco_message_visible(message):
    return not message.get("deleted_at")


def eco_render_bubble(message, current_user_id, supabase=None):
    """Render a private message and controls for its author."""
    if not eco_message_visible(message):
        return
    sent = str(message.get("sender_id")) == str(current_user_id)
    role = "user" if sent else "assistant"
    attachment = message.get("attachment_path")
    message_id = message.get("id")
    with st.chat_message(role):
        if attachment and supabase:
            url = eco_storage_url(supabase, attachment)
            kind = str(message.get("attachment_type") or "")
            if url and kind.startswith("image"):
                st.image(url, use_container_width=True)
            elif url and kind.startswith("video"):
                st.video(url)
            elif url:
                st.link_button(message.get("attachment_name") or "Open attachment", url)
        body = str(message.get("message_text") or "").strip()
        if body:
            st.write(body)
        meta = eco_time_label(message.get("created_at"))
        if message.get("edited_at"):
            meta += " · edited"
        st.caption((meta + ("  ✓✓" if sent else "")).strip())
        if sent and message_id:
            with st.expander("Message options"):
                edited = st.text_input(
                    "Edit message", value=body,
                    key=f"eco_dm_edit_text_{message_id}"
                )
                a, b = st.columns(2)
                with a:
                    if st.button("Save edit", key=f"eco_dm_edit_{message_id}", use_container_width=True):
                        try:
                            eco_edit_message(supabase, "direct_messages", message_id, current_user_id, edited)
                            st.success("Message updated.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Could not edit message: {exc}")
                with b:
                    if st.button("Delete message", key=f"eco_dm_delete_{message_id}", use_container_width=True):
                        try:
                            eco_soft_delete_message(supabase, "direct_messages", message_id, current_user_id)
                            st.success("Message deleted.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Could not delete message: {exc}")


def render_direct_conversation(supabase, user_id):
    """Full-screen private conversation; no Community Hub footer/navigation."""
    conversation_id = st.session_state.eco_active_conversation
    if not conversation_id:
        st.session_state.eco_chat_view = "Inbox"
        st.rerun()
        return

    conversations = get_direct_conversations(supabase, user_id)
    conversation = next(
        (c for c in conversations if str(c.get("id")) == str(conversation_id)),
        None
    )
    if not conversation:
        st.error("This conversation is no longer available.")
        if st.button("‹ Back to chats", key="eco_dm_missing_back"):
            st.session_state.eco_active_conversation = None
            st.session_state.eco_chat_view = "Inbox"
            st.rerun()
        return

    other_id = get_other_conversation_user(conversation, user_id)
    other = eco_profile(supabase, other_id) if other_id else {}
    name = eco_display_name(other)

    # Compact conversation header. Main Community Hub navigation is hidden
    # by the early return in render_community_groups_page().
    back, avatar_col, title_col, menu_col = st.columns([0.55, 0.8, 3.8, 0.6])
    with back:
        if st.button("‹", key="eco_dm_back", help="Back to chats"):
            st.session_state.eco_active_conversation = None
            st.session_state.eco_chat_view = "Inbox"
            st.rerun()
    with avatar_col:
        eco_avatar(other, 40)
    with title_col:
        st.markdown(f"**{eco_escape(name)}**")
        st.caption("@" + eco_safe_text(other.get("username"), "member"))
    with menu_col:
        if st.button("⋮", key="eco_dm_menu", help="Conversation options"):
            st.info("More conversation options will be available here.")

    st.divider()
    mark_direct_conversation_read(supabase, conversation_id, user_id)
    messages = get_direct_messages(supabase, conversation_id)
    if not messages:
        st.info("This is the beginning of your conversation. Send a message to get things started.")
    for message in messages:
        eco_render_bubble(message, user_id, supabase)

    # Attachments sit immediately above the native bottom-pinned composer.
    attachment = st.file_uploader(
        "Attach a photo, video or document",
        type=["jpg", "jpeg", "png", "webp", "mp4", "mov", "pdf"],
        key=f"eco_dm_attach_{conversation_id}",
        label_visibility="collapsed"
    )
    if hasattr(st, "chat_input"):
        typed_message = st.chat_input("Write a message…", key=f"eco_dm_composer_{conversation_id}")
    else:
        typed_message = None
        st.warning("Your Streamlit version does not support the bottom chat composer. Update Streamlit to use it.")

    send_attachment = False
    if attachment is not None:
        send_attachment = st.button("Send attachment", key=f"eco_dm_send_attachment_{conversation_id}")
    if typed_message is not None or send_attachment:
        try:
            path = ""
            selected_file = attachment if send_attachment else None
            if selected_file:
                path = eco_upload(supabase, selected_file, "direct-messages", user_id, allow_video=True, allow_documents=True)
            send_direct_message(
                supabase, conversation_id, user_id, typed_message or "",
                path,
                selected_file.name if selected_file else "",
                selected_file.type if selected_file else ""
            )
            st.rerun()
        except Exception as exc:
            st.error(f"Message could not be sent: {exc}")


def render_chat_inbox(supabase, user_id):
    eco_header("Chats", "Private conversations with your community")
    conversations = get_direct_conversations(supabase, user_id)
    if not conversations:
        st.info("Your inbox is empty. Discover people and start a conversation.")
    for index, conv in enumerate(conversations):
        other_id = get_other_conversation_user(conv, user_id)
        profile = eco_profile(supabase, other_id)
        name = eco_display_name(profile)
        messages = get_direct_messages(supabase, conv.get("id"), limit=1)
        latest = messages[-1] if messages else {}
        preview = eco_safe_text(latest.get("message_text"), "Attachment" if latest.get("attachment_path") else "No messages yet")
        timestamp = eco_time_label(latest.get("created_at") or conv.get("created_at"))
        read_at = get_read_timestamp(supabase, conv.get("id"), user_id)
        unread = 0
        if read_at:
            try:
                all_messages = get_direct_messages(supabase, conv.get("id"), limit=100)
                read_dt = _parse_dt(read_at)
                unread = sum(
                    1 for m in all_messages
                    if str(m.get("sender_id")) != str(user_id)
                    and _parse_dt(m.get("created_at"))
                    and read_dt
                    and _parse_dt(m.get("created_at")) > read_dt
                )
            except Exception:
                unread = 0
        with st.container(border=True):
            left, middle, right = st.columns([0.8, 3.3, 1.0])
            with left:
                eco_avatar(profile, 46)
            with middle:
                st.markdown(f"**{eco_escape(name)}**")
                st.caption(preview[:70])
                st.caption("@" + eco_safe_text(profile.get("username"), "member"))
            with right:
                st.caption(timestamp)
                if unread:
                    st.caption(f"Unread: {unread}")
                if st.button("Open chat", key=f"eco_inbox_open_{index}_{conv.get('id')}", use_container_width=True):
                    st.session_state.eco_active_conversation = conv.get("id")
                    st.session_state.eco_chat_view = "Conversation"
                    st.rerun()
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("＋ New chat", key="eco_new_chat_button", use_container_width=True):
            st.session_state.eco_chat_view = "Discover People"
            st.rerun()
    with c2:
        if st.button("My profile", key="eco_my_profile_button", use_container_width=True):
            st.session_state.eco_chat_view = "My Profile"
            st.rerun()


def render_chats_section(supabase, user_id):
    view = st.session_state.get("eco_chat_view", "Inbox")
    if view == "Conversation":
        render_direct_conversation(supabase, user_id)
        return
    if view == "Profile":
        profile_user = st.session_state.get("eco_profile_view_user")
        if st.button("‹ Back", key="eco_profile_back"):
            st.session_state.eco_chat_view = "Discover People"
            st.rerun()
        render_public_profile(supabase, profile_user, user_id)
        return
    if view == "Discover People":
        if st.button("‹ Back to inbox", key="eco_people_back"):
            st.session_state.eco_chat_view = "Inbox"
            st.rerun()
        render_people_directory(supabase, user_id)
        return
    if view == "My Profile":
        if st.button("‹ Back to inbox", key="eco_myprofile_back"):
            st.session_state.eco_chat_view = "Inbox"
            st.rerun()
        render_profile_editor(supabase, user_id)
        return
    render_chat_inbox(supabase, user_id)


# ------------------------------
# Chatrooms / community groups
# ------------------------------

def get_chatrooms(supabase, search_text=""):
    try:
        rows = eco_select(supabase, "community_groups", "*", order=("created_at", True), limit=150)
        q = (search_text or "").strip().lower()
        if q:
            rows = [
                row for row in rows
                if q in str(row.get("name", "")).lower()
                or q in str(row.get("description", "")).lower()
                or q in str(row.get("location", "")).lower()
            ]
        return rows
    except Exception:
        return []


def get_my_chatrooms(supabase, user_id):
    try:
        memberships = eco_select(
            supabase, "group_memberships", "*",
            [("eq", "user_id", user_id), ("eq", "status", "approved")],
            limit=200
        )
        ids = {str(m.get("group_id")) for m in memberships}
        return [g for g in get_chatrooms(supabase) if str(g.get("id")) in ids]
    except Exception:
        return []


def create_chatroom(supabase, user_id, name, description, image_url="", location=""):
    payload = {
        "name": name.strip(),
        "description": description.strip(),
        "created_by": user_id,
        "image_url": image_url or None,
        "location": location.strip() or None,
    }
    result = supabase.table("community_groups").insert(payload).execute()
    rows = eco_result_data(result)
    if rows:
        group_id = rows[0].get("id")
    else:
        matches = eco_select(
            supabase, "community_groups", "*",
            [("eq", "created_by", user_id), ("eq", "name", name.strip())],
            order=("created_at", True), limit=1
        )
        group_id = matches[0].get("id") if matches else None
    if group_id:
        try:
            supabase.table("group_memberships").upsert({
                "group_id": group_id,
                "user_id": user_id,
                "membership_role": "admin",
                "status": "approved"
            }, on_conflict="group_id,user_id").execute()
        except Exception:
            pass
    return group_id


def request_chatroom_join(supabase, group_id, user_id):
    return supabase.table("group_memberships").upsert({
        "group_id": group_id,
        "user_id": user_id,
        "membership_role": "member",
        "status": "pending"
    }, on_conflict="group_id,user_id").execute()


def leave_chatroom(supabase, group_id, user_id):
    return supabase.table("group_memberships").delete().eq(
        "group_id", group_id
    ).eq("user_id", user_id).execute()


def is_chatroom_member(supabase, group, user_id):
    try:
        rows = eco_select(
            supabase, "group_memberships", "*",
            [("eq", "group_id", group.get("id")), ("eq", "user_id", user_id), ("eq", "status", "approved")],
            limit=1
        )
        return bool(rows)
    except Exception:
        return str(group.get("created_by")) == str(user_id)


def get_group_membership(supabase, group_id, user_id):
    try:
        rows = eco_select(
            supabase, "group_memberships", "*",
            [("eq", "group_id", group_id), ("eq", "user_id", user_id)],
            limit=1
        )
        return rows[0] if rows else {}
    except Exception:
        return {}


def get_chatroom_messages(supabase, group_id, limit=100):
    try:
        return eco_select(
            supabase, "group_messages", "*",
            [("eq", "group_id", group_id), ("is_", "deleted_at", "null")],
            order=("created_at", False), limit=limit
        )
    except Exception:
        return []


def send_chatroom_message(supabase, group_id, sender_id, message_text, attachments=None):
    payload = {
        "group_id": group_id,
        "sender_id": sender_id,
        "message_text": (message_text or "").strip(),
    }
    if attachments:
        payload["attachments"] = attachments
    if not payload["message_text"] and not attachments:
        return False
    supabase.table("group_messages").insert(payload).execute()
    return True


def manage_group_join_requests(supabase, group_id, action, target_user_id):
    status = "approved" if action == "approve" else "rejected"
    return supabase.table("group_memberships").update({
        "status": status
    }).eq("group_id", group_id).eq("user_id", target_user_id).execute()


def render_chatroom_chat(supabase, group, user_id):
    group_id = group.get("id")
    is_member = is_chatroom_member(supabase, group, user_id)
    if not is_member:
        st.warning("You need approved membership to view this group chat.")
        if st.button("‹ Back to groups", key=f"eco_room_back_not_member_{group_id}"):
            st.session_state.eco_active_chatroom = None
            st.rerun()
        return
    top1, top2 = st.columns([1, 5])
    with top1:
        if st.button("‹ Back", key=f"eco_room_back_{group_id}"):
            st.session_state.eco_active_chatroom = None
            st.rerun()
    with top2:
        st.markdown(f"### {eco_escape(group.get('name', 'Community group'))}")
    st.caption(eco_safe_text(group.get("description"), "Community conversation"))
    st.divider()
    messages = get_chatroom_messages(supabase, group_id)
    for message in messages:
        if not eco_message_visible(message):
            continue
        sender = eco_profile(supabase, message.get("sender_id"))
        sent = str(message.get("sender_id")) == str(user_id)
        name = "You" if sent else eco_display_name(sender)
        with st.chat_message("user" if sent else "assistant"):
            if not sent:
                st.caption(name)
            attachments = message.get("attachments") or []
            if isinstance(attachments, dict):
                attachments = [attachments]
            for item in attachments:
                if not isinstance(item, dict):
                    continue
                media_path = item.get("path") or item.get("url")
                media_url = eco_storage_url(supabase, media_path)
                media_type = str(item.get("type") or "")
                if media_url and media_type.startswith("image"):
                    st.image(media_url, use_container_width=True)
                elif media_url and media_type.startswith("video"):
                    st.video(media_url)
                elif media_url:
                    st.link_button(item.get("name") or "Open attachment", media_url)
            st.write(str(message.get("message_text") or ""))
            meta = eco_time_label(message.get("created_at"))
            if message.get("edited_at"):
                meta += " · edited"
            st.caption(meta)
            if sent and message.get("id"):
                with st.expander("Message options"):
                    body = str(message.get("message_text") or "")
                    edited = st.text_input("Edit message", value=body, key=f"eco_group_edit_text_{message['id']}")
                    a, b = st.columns(2)
                    with a:
                        if st.button("Save edit", key=f"eco_group_edit_{message['id']}", use_container_width=True):
                            try:
                                eco_edit_message(supabase, "group_messages", message["id"], user_id, edited)
                                st.success("Message updated.")
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Could not edit message: {exc}")
                    with b:
                        if st.button("Delete message", key=f"eco_group_delete_{message['id']}", use_container_width=True):
                            try:
                                eco_soft_delete_message(supabase, "group_messages", message["id"], user_id)
                                st.success("Message deleted.")
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Could not delete message: {exc}")

    attachment = st.file_uploader(
        "Attach a photo, video or document",
        type=["jpg", "jpeg", "png", "webp", "mp4", "mov", "pdf"],
        key=f"eco_group_attach_{group_id}"
    )
    with st.form(f"eco_group_send_form_{group_id}", clear_on_submit=True):
        text_value = st.text_input("Message", placeholder=f"Message {group.get('name', 'the group')}…", label_visibility="collapsed")
        send = st.form_submit_button("Send", use_container_width=True)
    send_attachment = False
    if attachment is not None:
        send_attachment = st.button("Send attachment", key=f"eco_group_send_attachment_{group_id}")
    if send or send_attachment:
        try:
            attachment_items = []
            selected_file = attachment if send_attachment else None
            if selected_file:
                path = eco_upload(supabase, selected_file, "groups", user_id, allow_video=True, allow_documents=True)
                attachment_items.append({"path": path, "name": selected_file.name, "type": selected_file.type or ""})
            send_chatroom_message(supabase, group_id, user_id, text_value if send else "", attachment_items)
            st.rerun()
        except Exception as exc:
            st.error(f"Message could not be sent: {exc}")


def _render_group_card(supabase, group, user_id, index, view_name):
    group_id = group.get("id")
    membership = get_group_membership(supabase, group_id, user_id)
    status = membership.get("status")
    is_owner = str(group.get("created_by")) == str(user_id)
    approved = status == "approved" or is_owner
    with st.container(border=True):
        image_url = eco_storage_url(supabase, group.get("image_url"))
        if image_url:
            st.image(image_url, use_container_width=True)
        st.markdown(f"**{eco_escape(group.get('name', 'Community group'))}**")
        if group.get("location"):
            st.caption("📍 " + str(group["location"]))
        st.write(str(group.get("description") or "A space for people to connect and take action.")[:220])
        if approved:
            st.caption("🟢 Member" if not is_owner else "⭐ Group admin")
            if st.button("Open group chat", key=f"eco_group_open_{view_name}_{group_id}_{index}", use_container_width=True):
                st.session_state.eco_active_chatroom = group_id
                st.rerun()
            if not is_owner:
                if st.button("Leave group", key=f"eco_group_leave_{view_name}_{group_id}_{index}"):
                    try:
                        leave_chatroom(supabase, group_id, user_id)
                        st.success("You left the group.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not leave group: {exc}")
        elif status == "pending":
            st.info("Your join request is waiting for approval.")
        elif status == "rejected":
            st.caption("Your previous request was not approved.")
            if st.button("Request to join again", key=f"eco_group_rejoin_{view_name}_{group_id}_{index}", use_container_width=True):
                try:
                    request_chatroom_join(supabase, group_id, user_id)
                    st.success("Join request sent.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not send request: {exc}")
        else:
            if st.button("Request to join", key=f"eco_group_join_{view_name}_{group_id}_{index}", use_container_width=True):
                try:
                    request_chatroom_join(supabase, group_id, user_id)
                    st.success("Join request sent to the group admins.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not request membership: {exc}")


def render_chatrooms_page(supabase, user_id):
    if st.session_state.get("eco_active_chatroom"):
        group_id = st.session_state.eco_active_chatroom
        group = next((g for g in get_chatrooms(supabase) if str(g.get("id")) == str(group_id)), None)
        if group:
            render_chatroom_chat(supabase, group, user_id)
        else:
            st.warning("This group could not be found.")
            if st.button("Back to groups", key="eco_missing_group_back"):
                st.session_state.eco_active_chatroom = None
                st.rerun()
        return

    eco_header("Groups", "Join communities, share ideas and work together")
    views = ["Discover", "My Groups", "Create"]
    current = st.session_state.get("eco_group_view", "Discover")
    selected = st.radio("Group sections", views, horizontal=True, key="eco_group_view_radio", label_visibility="collapsed", index=views.index(current) if current in views else 0)
    st.session_state.eco_group_view = selected

    if selected == "Discover":
        search = st.text_input("Search groups", placeholder="Search by group name, topic or location…", key="eco_group_search")
        groups = get_chatrooms(supabase, search)
        if not groups:
            st.info("No groups found. You can create the first community group.")
        for i, group in enumerate(groups):
            _render_group_card(supabase, group, user_id, i, "discover")

    elif selected == "My Groups":
        groups = get_my_chatrooms(supabase, user_id)
        if not groups:
            st.info("You have not joined any groups yet. Explore communities to get started.")
        for i, group in enumerate(groups):
            _render_group_card(supabase, group, user_id, i, "mine")
        # Admin tools for pending requests
        for i, group in enumerate(groups):
            if str(group.get("created_by")) != str(user_id):
                continue
            with st.expander(f"Manage requests · {group.get('name', 'Group')}"):
                try:
                    pending = eco_select(
                        supabase, "group_memberships", "*",
                        [("eq", "group_id", group.get("id")), ("eq", "status", "pending")],
                        limit=100
                    )
                except Exception:
                    pending = []
                if not pending:
                    st.caption("No pending requests.")
                for j, request in enumerate(pending):
                    person = eco_profile(supabase, request.get("user_id"))
                    a, b, c = st.columns([3, 1, 1])
                    with a:
                        st.write(eco_display_name(person))
                        st.caption("@" + eco_safe_text(person.get("username"), "member"))
                    with b:
                        if st.button("Approve", key=f"eco_req_approve_{group.get('id')}_{j}"):
                            try:
                                manage_group_join_requests(supabase, group.get("id"), "approve", request.get("user_id"))
                                st.rerun()
                            except Exception as exc:
                                st.error(str(exc))
                    with c:
                        if st.button("Reject", key=f"eco_req_reject_{group.get('id')}_{j}"):
                            try:
                                manage_group_join_requests(supabase, group.get("id"), "reject", request.get("user_id"))
                                st.rerun()
                            except Exception as exc:
                                st.error(str(exc))

    else:
        with st.form("eco_create_group_form", clear_on_submit=True):
            name = st.text_input("Group name", placeholder="e.g. Bulawayo Climate Action")
            description = st.text_area("What is this group about?", max_chars=500)
            location = st.text_input("Location (optional)")
            image_file = st.file_uploader("Group cover image (optional)", type=["jpg", "jpeg", "png", "webp"], key="eco_group_cover_upload")
            submit = st.form_submit_button("Create community group", use_container_width=True)
        if submit:
            if len(name.strip()) < 3 or len(description.strip()) < 8:
                st.error("Add a group name and a short description.")
            else:
                try:
                    image_path = eco_upload(supabase, image_file, "chatrooms", user_id) if image_file else ""
                    group_id = create_chatroom(supabase, user_id, name, description, image_path, location)
                    if group_id:
                        st.success("Your group has been created.")
                        st.session_state.eco_active_chatroom = group_id
                        st.rerun()
                    else:
                        st.success("Group created. Find it under My Groups.")
                except Exception as exc:
                    st.error(f"Could not create group: {exc}")


# ------------------------------
# Stories / Updates
# ------------------------------

def create_story(supabase, user_id, caption, media_path, media_type):
    now = eco_now()
    expires = now + timedelta(hours=24)
    return supabase.table("stories").insert({
        "user_id": user_id,
        "caption": (caption or "").strip(),
        "media_url": media_path,
        "media_type": media_type,
        "created_at": now.isoformat(),
        "expires_at": expires.isoformat(),
    }).execute()


def get_active_stories(supabase):
    try:
        return eco_select(
            supabase, "stories", "*",
            [("gt", "expires_at", eco_iso())],
            order=("created_at", True), limit=150
        )
    except Exception:
        return []


def render_story_card(supabase, story, current_user_id, index):
    profile = eco_profile(supabase, story.get("user_id"))
    name = "Your update" if str(story.get("user_id")) == str(current_user_id) else eco_display_name(profile)
    with st.container(border=True):
        st.markdown(f"**{eco_escape(name)}**")
        st.caption(eco_time_label(story.get("created_at")))
        url = eco_storage_url(supabase, story.get("media_url"))
        media_type = str(story.get("media_type") or "")
        if url and media_type.startswith("video"):
            st.video(url)
        elif url:
            st.image(url, use_container_width=True)
        if story.get("caption"):
            st.write(story["caption"])


def render_stories_page(supabase, user_id):
    eco_header("Updates", "Share a moment with your community · updates disappear after 24 hours")
    views = ["Recent Updates", "Create Update"]
    current = st.session_state.get("eco_story_view", "Recent Updates")
    selected = st.radio("Update sections", views, horizontal=True, key="eco_story_view_radio", label_visibility="collapsed", index=views.index(current) if current in views else 0)
    st.session_state.eco_story_view = selected
    if selected == "Create Update":
        st.markdown("### Share an update")
        uploaded = st.file_uploader("Choose a photo or short video", type=["jpg", "jpeg", "png", "webp", "mp4", "mov", "webm"], key="eco_story_upload")
        caption = st.text_area("Add a caption (optional)", max_chars=180, key="eco_story_caption")
        if st.button("Publish update", key="eco_story_publish", use_container_width=True):
            if not uploaded:
                st.warning("Choose a photo or video first.")
            else:
                try:
                    path = eco_upload(supabase, uploaded, "stories", user_id, allow_video=True)
                    media_type = uploaded.type or mimetypes.guess_type(uploaded.name)[0] or "image"
                    create_story(supabase, user_id, caption, path, media_type)
                    st.success("Your update is live for 24 hours.")
                    st.session_state.eco_story_view = "Recent Updates"
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not publish update: {exc}")
        return
    stories = get_active_stories(supabase)
    mine = [s for s in stories if str(s.get("user_id")) == str(user_id)]
    others = [s for s in stories if str(s.get("user_id")) != str(user_id)]
    if mine:
        st.markdown("### My status")
        for i, story in enumerate(mine):
            render_story_card(supabase, story, user_id, i)
    if others:
        st.markdown("### Recent updates")
        for i, story in enumerate(others):
            render_story_card(supabase, story, user_id, i)
    if not stories:
        st.info("No updates yet. Be the first to share something with your community.")


# ------------------------------
# Community discovery
# ------------------------------

def render_community_discover(supabase, user_id):
    eco_header("Discover", "Find people and communities across EcoLoop")
    query = st.text_input(
        "Search people or groups", key="eco_discover_search_input",
        placeholder="Search names, usernames, groups or locations…"
    )
    st.markdown("### People")
    people = [p for p in get_member_directory(supabase, query) if str(p.get("user_id")) != str(user_id)]
    if people:
        for index, profile in enumerate(people[:30]):
            render_member_card(supabase, profile, user_id, f"discover_{index}")
    else:
        st.caption("No matching people found.")
    st.divider()
    st.markdown("### Groups")
    groups = get_chatrooms(supabase, query)
    if groups:
        for index, group in enumerate(groups[:30]):
            _render_group_card(supabase, group, user_id, index, "discover_hub")
    else:
        st.caption("No matching groups found.")


# ------------------------------
# Main Community Hub entry point
# ------------------------------

def render_community_groups_page(supabase, user_id):
    """Render the Community Hub; hide the app footer in focused chat screens."""
    eco_init_state()
    eco_inject_styles()

    private_chat_open = st.session_state.get("eco_chat_view") == "Conversation"
    chatroom_open = bool(st.session_state.get("eco_active_chatroom"))

    # streamlit_app.py checks this session flag before rendering its global
    # footer. Keep the flag true for BOTH one-to-one and group conversations.
    # The Chats inbox, Chat Rooms directory and Updates feed keep the footer.
    st.session_state["eco_hide_app_footer"] = bool(
        private_chat_open or chatroom_open
    )

    if private_chat_open:
        try:
            render_direct_conversation(supabase, user_id)
        except Exception as exc:
            st.error("The private conversation could not load.")
            st.caption(f"Technical detail: {exc}")
        return

    # An opened group chat is also a focused, full-screen conversation.
    # Return before the Hub navigation and its own footer are rendered.
    if chatroom_open:
        try:
            render_chatrooms_page(supabase, user_id)
        except Exception as exc:
            st.error("The chatroom could not load.")
            st.caption(f"Technical detail: {exc}")
        return

    st.caption("NEXT GEN IMPACT HUB")
    st.title("Community Hub")
    st.caption("Connect · Collaborate · Create impact")

    options = ["💬 Chats", "👥 Groups", "🟢 Updates", "🔎 Discover"]
    labels = {"💬 Chats": "Chats", "👥 Groups": "Groups", "🟢 Updates": "Updates", "🔎 Discover": "Discover"}
    current = st.session_state.get("eco_community_section", "Chats")
    current_option = next((key for key, value in labels.items() if value == current), options[0])
    selected = st.radio(
        "Community navigation", options, horizontal=True,
        key=MAIN_NAV_KEY, index=options.index(current_option),
        label_visibility="collapsed"
    )
    section = labels[selected]
    st.session_state.eco_community_section = section
    st.divider()

    try:
        if section == "Chats":
            render_chats_section(supabase, user_id)
        elif section == "Groups":
            render_chatrooms_page(supabase, user_id)
        elif section == "Updates":
            render_stories_page(supabase, user_id)
        else:
            render_community_discover(supabase, user_id)
    except Exception as exc:
        st.error("The Community Hub section could not load.")
        st.caption(f"Technical detail: {exc}")

    st.divider()
    st.caption("Powered by Next Gen Impact Hub (NGIH)")
