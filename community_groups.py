# ============================================================
# ECOLOOP NODE — COMMUNITY HUB
# WhatsApp-style replacement module
# Powered by Next Gen Impact Hub (NGIH)
# ============================================================
#
# Layout like WhatsApp Web:
#   Left  : Chats / Groups / Updates / Discover + search + list
#   Right : Open conversation with bubbles, header, composer
#   Mobile: Shows list first, then chat full screen with back button
#
# Integration:
#   render_community_groups_page(supabase, user_id)
# ============================================================

import mimetypes
import os
import re
import uuid
from datetime import datetime, timedelta, timezone

import streamlit as st

BUCKET = "community-media"
MAX_IMAGE_MB = 8
MAX_VIDEO_MB = 35
MAIN_NAV_KEY = "eco_community_navigation_v3"
WA_GREEN = "#075E54"
WA_GREEN_LIGHT = "#128C7E"
WA_BG = "#ECE5DD"
WA_BUBBLE_ME = "#DCF8C6"
WA_BUBBLE_OTHER = "#FFFFFF"

# ------------------------------
# Helpers
# ------------------------------

def eco_now():
    return datetime.now(timezone.utc)

def eco_iso(value=None):
    value = value or eco_now()
    if isinstance(value, str):
        return value
    return value.isoformat()

def eco_escape(value):
    return str(value or "")

def eco_safe_text(value, default=""):
    text = str(value or "").strip()
    return text if text else default

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
        "eco_sidebar_search": "",
        "eco_mobile_show_chat": False,
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
        if method == "is_":
            query = query.is_(column, None if value in ("null", None) else value)
        else:
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
        rows = eco_select(supabase, "member_profiles", "*", [("eq", "user_id", user_id)], limit=1)
        return rows[0] if rows else {}
    except Exception:
        return {}

def eco_display_name(profile, fallback="EcoLoop member"):
    return eco_safe_text((profile or {}).get("display_name") or (profile or {}).get("username"), fallback)

def eco_initials(name):
    words = [w for w in str(name or "E").strip().split() if w]
    if not words:
        return "E"
    return "".join(w[0].upper() for w in words[:2])

def eco_storage_url(supabase, path, expires=3600):
    if not path:
        return ""
    if str(path).startswith("http"):
        return str(path)
    try:
        result = supabase.storage.from_(BUCKET).create_signed_url(path, expires)
        if hasattr(result, "signed_url"):
            return result.signed_url or ""
        if isinstance(result, dict):
            return result.get("signedURL") or result.get("signedUrl") or ""
        if isinstance(result, str):
            return result
        return ""
    except Exception:
        return ""

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
    supabase.storage.from_(BUCKET).upload(path, uploaded.getvalue(), {"content-type": content_type, "upsert": "false"})
    return path

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
    now = eco_now()
    try:
        local = dt.astimezone()
        if local.date() == now.astimezone().date():
            return local.strftime("%H:%M")
        if (now.astimezone().date() - local.date()).days == 1:
            return "Yesterday"
        return local.strftime("%d/%m/%Y")
    except Exception:
        return str(value)[:16]

def eco_time_short(value):
    dt = _parse_dt(value)
    if not dt:
        return ""
    try:
        return dt.astimezone().strftime("%H:%M")
    except Exception:
        return ""

# ------------------------------
# WhatsApp Styles
# ------------------------------

def eco_inject_whatsapp_styles():
    st.markdown(
        """
        <style>
        .block-container { padding-top: 0rem !important; padding-bottom: 0rem !important; padding-left: 0rem !important; padding-right: 0rem !important; max-width: 100% !important; }
        header[data-testid="stHeader"] { display: none; }
        [data-testid="stSidebar"] { display: none; }
        .wa-topbar { background: #075E54; color: white; padding: 12px 16px; display: flex; align-items: center; justify-content: space-between; }
        .wa-topbar b { font-size: 19px; }
        .wa-topbar span { font-size: 12px; opacity: 0.9; }
        .wa-sidebar { background: white; border-right: 1px solid #e0e0e0; height: 100%; }
        .wa-chat-bg { background: #ECE5DD; background-image: radial-gradient(#d5d0c8 0.6px, transparent 0.6px); background-size: 18px 18px; min-height: 72vh; padding: 12px 10px 90px 10px; }
        .wa-bubble-me { background: #DCF8C6; border-radius: 10px 10px 0px 10px; padding: 8px 10px; margin: 4px 0 4px auto; max-width: 78%; width: fit-content; box-shadow: 0 1px 1px rgba(0,0,0,0.08); font-size: 14.5px; line-height: 1.4; }
        .wa-bubble-other { background: white; border-radius: 10px 10px 10px 0px; padding: 8px 10px; margin: 4px auto 4px 0; max-width: 78%; width: fit-content; box-shadow: 0 1px 1px rgba(0,0,0,0.08); font-size: 14.5px; line-height: 1.4; }
        .wa-meta { font-size: 11px; color: #667781; text-align: right; margin-top: 2px; }
        .wa-sender { font-size: 12px; font-weight: 700; color: #128C7E; margin-bottom: 2px; }
        .wa-chat-row { padding: 10px 12px; border-bottom: 1px solid #f0f2f5; cursor: pointer; }
        .wa-chat-row:hover { background: #f0f2f5; }
        .wa-chat-row.active { background: #f0f2f5; }
        .wa-avatar { width: 44px; height: 44px; border-radius: 50%; background: #DFE5E7; display: flex; align-items: center; justify-content: center; font-weight: 700; color: #54656F; font-size: 16px; flex-shrink: 0; }
        .wa-unread { background: #25D366; color: white; font-size: 11px; font-weight: 700; min-width: 20px; height: 20px; border-radius: 20px; display: flex; align-items: center; justify-content: center; padding: 0 6px; }
        .wa-header { background: #F0F2F5; padding: 10px 12px; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid #e0e0e0; }
        .wa-empty { height: 72vh; display: flex; flex-direction: column; align-items: center; justify-content: center; background: #F8F9FA; color: #667781; text-align: center; padding: 30px; }
        div[data-testid="stChatMessage"] { background: transparent !important; border: none !important; padding: 0 !important; }
        div[data-testid="stChatMessageAvatar"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def eco_avatar_html(profile, size=44):
    name = eco_display_name(profile)
    url = profile.get("avatar_url") if profile else None
    if url and str(url).startswith("http"):
        return f'<img src="{url}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;" />'
    return f'<div class="wa-avatar" style="width:{size}px;height:{size}px;">{eco_initials(name)}</div>'

def eco_bubble_html(text, time_label, is_me, sender_name="", edited=False):
    safe = str(text or "").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
    tick = " ✓✓" if is_me else ""
    edit = " · edited" if edited else ""
    sender = f'<div class="wa-sender">{sender_name}</div>' if (not is_me and sender_name) else ""
    cls = "wa-bubble-me" if is_me else "wa-bubble-other"
    return f'<div class="{cls}">{sender}<div>{safe}</div><div class="wa-meta">{time_label}{edit}{tick}</div></div>'

# ------------------------------
# Profiles
# ------------------------------

def save_member_profile(supabase, user_id, values):
    payload = {"user_id": user_id}
    allowed = ("display_name", "username", "bio", "location", "interests", "country_of_origin", "instagram_handle", "facebook_handle", "tiktok_handle", "linkedin_handle", "avatar_url")
    for key in allowed:
        if key in values:
            payload[key] = values[key]
    return supabase.table("member_profiles").upsert(payload, on_conflict="user_id").execute()

def render_profile_editor(supabase, user_id):
    profile = eco_profile(supabase, user_id)
    st.markdown('<div class="wa-topbar"><b>My Profile</b><span>ECOLOOP</span></div>', unsafe_allow_html=True)
    if st.button("‹ Back to chats"):
        st.session_state.eco_chat_view = "Inbox"
        st.rerun()
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
    if avatar_file and st.button("Upload profile picture", key="eco_profile_avatar_save"):
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
                save_member_profile(supabase, user_id, {"display_name": display_name.strip(), "username": username, "bio": bio.strip(), "location": location.strip(), "country_of_origin": country.strip(), "interests": interests.strip(), "instagram_handle": instagram.strip(), "facebook_handle": facebook.strip(), "tiktok_handle": tiktok.strip(), "linkedin_handle": linkedin.strip()})
                st.success("Profile saved.")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not save profile. The username may already be taken. Details: {exc}")

def get_member_directory(supabase, search_text=""):
    q = (search_text or "").strip().lower().lstrip("@").strip()
    try:
        if not q:
            return eco_select(supabase, "member_profiles", "*", order=("display_name", False), limit=150)
        found = {}
        for column in ("username", "display_name", "location"):
            try:
                rows = eco_result_data(supabase.table("member_profiles").select("*").ilike(column, f"%{q}%").limit(100).execute())
                for row in rows:
                    uid = str(row.get("user_id") or row.get("id") or "")
                    if uid:
                        found[uid] = row
            except Exception:
                continue
        return sorted(found.values(), key=lambda r: (str(r.get("username") or "").lower(), str(r.get("display_name") or "").lower()))
    except Exception:
        return []

def render_people_directory(supabase, user_id):
    st.markdown('<div class="wa-topbar"><b>New Chat</b><span>Find people</span></div>', unsafe_allow_html=True)
    if st.button("‹ Back"):
        st.session_state.eco_chat_view = "Inbox"
        st.rerun()
    query = st.text_input("Search people", key="eco_people_search_input", placeholder="Search username or name…")
    profiles = [p for p in get_member_directory(supabase, query) if p.get("user_id") != user_id]
    if not profiles:
        st.info("No members found yet. Try another username.")
        return
    for index, profile in enumerate(profiles):
        render_member_card(supabase, profile, user_id, f"directory_{index}")

def render_member_card(supabase, profile, current_user_id, key_suffix):
    uid = profile.get("user_id")
    name = eco_display_name(profile)
    username = eco_safe_text(profile.get("username"), "member")
    with st.container(border=True):
        c1, c2 = st.columns([1, 4])
        with c1:
            st.markdown(eco_avatar_html(profile), unsafe_allow_html=True)
        with c2:
            st.markdown(f"**{name}**")
            st.caption(f"@{username}")
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
                        st.session_state.eco_mobile_show_chat = True
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not open chat: {exc}")

def render_public_profile(supabase, user_id, current_user_id):
    profile = eco_profile(supabase, user_id)
    if not profile:
        st.warning("This profile is not available.")
        return
    if st.button("‹ Back"):
        st.session_state.eco_chat_view = "Discover People"
        st.rerun()
    st.markdown(eco_avatar_html(profile, 76), unsafe_allow_html=True)
    st.subheader(eco_display_name(profile))
    st.caption("@" + eco_safe_text(profile.get("username"), "member"))
    if profile.get("location"):
        st.caption("📍 " + str(profile["location"]))
    if profile.get("bio"):
        st.write(profile["bio"])
    if profile.get("interests"):
        st.caption("Interests: " + str(profile["interests"]))
    socials = [("Instagram", "instagram_handle"), ("Facebook", "facebook_handle"), ("TikTok", "tiktok_handle"), ("LinkedIn", "linkedin_handle")]
    present = [f"**{label}:** @{profile[key].lstrip('@')}" for label, key in socials if profile.get(key)]
    if present:
        st.markdown(" · ".join(present))
    if user_id != current_user_id and st.button("Message", key=f"eco_public_profile_message_{user_id}", use_container_width=True):
        try:
            conv = get_or_create_direct_conversation(supabase, current_user_id, user_id)
            st.session_state.eco_active_conversation = conv
            st.session_state.eco_chat_view = "Conversation"
            st.rerun()
        except Exception as exc:
            st.error(f"Could not start conversation: {exc}")

# ------------------------------
# Direct Messages
# ------------------------------

def get_or_create_direct_conversation(supabase, user_a, user_b):
    first, second = sorted([str(user_a), str(user_b)])
    rows = eco_select(supabase, "direct_conversations", "*", [("eq", "user_one_id", first), ("eq", "user_two_id", second)], limit=1)
    if rows:
        return rows[0]["id"]
    result = supabase.table("direct_conversations").insert({"user_one_id": first, "user_two_id": second}).execute()
    rows = eco_result_data(result)
    if rows:
        return rows[0]["id"]
    rows = eco_select(supabase, "direct_conversations", "*", [("eq", "user_one_id", first), ("eq", "user_two_id", second)], limit=1)
    if not rows:
        raise RuntimeError("Conversation could not be created.")
    return rows[0]["id"]

def get_direct_conversations(supabase, user_id):
    try:
        rows_a = eco_select(supabase, "direct_conversations", "*", [("eq", "user_one_id", user_id)], order=("created_at", True), limit=150)
        rows_b = eco_select(supabase, "direct_conversations", "*", [("eq", "user_two_id", user_id)], order=("created_at", True), limit=150)
        unique = {str(row["id"]): row for row in rows_a + rows_b if row.get("id")}
        return list(unique.values())
    except Exception:
        return []

def get_direct_messages(supabase, conversation_id, limit=100):
    try:
        return eco_select(supabase, "direct_messages", "*", [("eq", "conversation_id", conversation_id), ("is_", "deleted_at", "null")], order=("created_at", False), limit=limit)
    except Exception:
        return []

def get_latest_direct_message(supabase, conversation_id):
    try:
        rows = eco_select(supabase, "direct_messages", "*", [("eq", "conversation_id", conversation_id), ("is_", "deleted_at", "null")], order=("created_at", True), limit=1)
        return rows[0] if rows else {}
    except Exception:
        return {}

def send_direct_message(supabase, conversation_id, sender_id, message_text, attachment_path="", attachment_name="", attachment_type=""):
    payload = {"conversation_id": conversation_id, "sender_id": sender_id, "message_text": (message_text or "").strip(), "attachment_path": attachment_path or None, "attachment_name": attachment_name or None, "attachment_type": attachment_type or None}
    if not payload["message_text"] and not attachment_path:
        return False
    supabase.table("direct_messages").insert(payload).execute()
    return True

def mark_direct_conversation_read(supabase, conversation_id, user_id):
    try:
        supabase.table("direct_conversation_reads").upsert({"conversation_id": conversation_id, "user_id": user_id, "last_read_at": eco_iso()}, on_conflict="conversation_id,user_id").execute()
        return True
    except Exception:
        return False

def get_read_timestamp(supabase, conversation_id, user_id):
    try:
        rows = eco_select(supabase, "direct_conversation_reads", "last_read_at", [("eq", "conversation_id", conversation_id), ("eq", "user_id", user_id)], limit=1)
        return rows[0].get("last_read_at") if rows else None
    except Exception:
        return None

def get_other_conversation_user(conversation, current_user_id):
    return conversation.get("user_two_id") if str(conversation.get("user_one_id")) == str(current_user_id) else conversation.get("user_one_id")

def eco_soft_delete_message(supabase, table, message_id, sender_id):
    return supabase.table(table).update({"deleted_at": eco_iso()}).eq("id", message_id).eq("sender_id", sender_id).execute()

def eco_edit_message(supabase, table, message_id, sender_id, new_text):
    new_text = (new_text or "").strip()
    if not new_text:
        raise ValueError("A message cannot be empty.")
    return supabase.table(table).update({"message_text": new_text, "edited_at": eco_iso()}).eq("id", message_id).eq("sender_id", sender_id).execute()

def render_whatsapp_bubble(message, current_user_id, supabase=None, sender_name=""):
    if message.get("deleted_at"):
        return
    sent = str(message.get("sender_id")) == str(current_user_id)
    attachment = message.get("attachment_path")
    body = str(message.get("message_text") or "").strip()
    time_label = eco_time_short(message.get("created_at"))
    if attachment and supabase:
        url = eco_storage_url(supabase, attachment)
        kind = str(message.get("attachment_type") or "")
        if url and kind.startswith("image"):
            st.image(url, use_container_width=True)
        elif url and kind.startswith("video"):
            st.video(url)
        elif url:
            st.link_button(message.get("attachment_name") or "Open attachment", url)
    if body:
        st.markdown(eco_bubble_html(body, time_label, sent, sender_name, bool(message.get("edited_at"))), unsafe_allow_html=True)
    if sent and message.get("id"):
        with st.expander("···", expanded=False):
            edited = st.text_input("Edit message", value=body, key=f"eco_dm_edit_text_{message['id']}")
            a, b = st.columns(2)
            with a:
                if st.button("Save", key=f"eco_dm_edit_{message['id']}", use_container_width=True):
                    try:
                        eco_edit_message(supabase, "direct_messages", message["id"], current_user_id, edited)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not edit: {exc}")
            with b:
                if st.button("Delete", key=f"eco_dm_delete_{message['id']}", use_container_width=True):
                    try:
                        eco_soft_delete_message(supabase, "direct_messages", message["id"], current_user_id)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not delete: {exc}")

def render_direct_conversation(supabase, user_id):
    conversation_id = st.session_state.eco_active_conversation
    if not conversation_id:
        st.session_state.eco_chat_view = "Inbox"
        st.rerun()
        return
    conversations = get_direct_conversations(supabase, user_id)
    conversation = next((c for c in conversations if str(c.get("id")) == str(conversation_id)), None)
    if not conversation:
        st.error("This conversation is no longer available.")
        if st.button("‹ Back to chats"):
            st.session_state.eco_active_conversation = None
            st.session_state.eco_chat_view = "Inbox"
            st.rerun()
        return
    other_id = get_other_conversation_user(conversation, user_id)
    other = eco_profile(supabase, other_id) if other_id else {}
    name = eco_display_name(other)

    # Header like WhatsApp
    h1, h2, h3 = st.columns([0.6, 1, 5])
    with h1:
        if st.button("‹", key="eco_dm_back"):
            st.session_state.eco_active_conversation = None
            st.session_state.eco_chat_view = "Inbox"
            st.session_state.eco_mobile_show_chat = False
            st.rerun()
    with h2:
        st.markdown(eco_avatar_html(other, 40), unsafe_allow_html=True)
    with h3:
        st.markdown(f"**{name}**")
        st.caption("@" + eco_safe_text(other.get("username"), "member") + " · Online")

    mark_direct_conversation_read(supabase, conversation_id, user_id)
    messages = get_direct_messages(supabase, conversation_id)

    st.markdown('<div class="wa-chat-bg">', unsafe_allow_html=True)
    if not messages:
        st.markdown('<div class="wa-empty"><div style="font-size:48px;">💬</div><b>Say hi to ' + name + '</b><p>This is the beginning of your conversation.</p></div>', unsafe_allow_html=True)
    for message in messages:
        render_whatsapp_bubble(message, user_id, supabase)
    st.markdown('</div>', unsafe_allow_html=True)

    # Composer pinned at bottom like WhatsApp
    attachment = st.file_uploader("Attach", type=["jpg", "jpeg", "png", "webp", "mp4", "mov", "pdf"], key=f"eco_dm_attach_{conversation_id}", label_visibility="collapsed")
    typed = st.chat_input("Type a message…", key=f"eco_dm_composer_{conversation_id}")
    send_attach = False
    if attachment is not None:
        send_attach = st.button("Send attachment ➤", key=f"eco_dm_send_attachment_{conversation_id}", use_container_width=True)
    if typed is not None or send_attach:
        try:
            path = ""
            selected = attachment if send_attach else None
            if selected:
                path = eco_upload(supabase, selected, "direct-messages", user_id, allow_video=True, allow_documents=True)
            if typed or path:
                send_direct_message(supabase, conversation_id, user_id, typed or "", path, selected.name if selected else "", selected.type if selected else "")
            st.rerun()
        except Exception as exc:
            st.error(f"Message could not be sent: {exc}")

def render_chats_section(supabase, user_id):
    view = st.session_state.get("eco_chat_view", "Inbox")
    if view == "Conversation":
        render_direct_conversation(supabase, user_id)
        return
    if view == "Profile":
        render_public_profile(supabase, st.session_state.get("eco_profile_view_user"), user_id)
        return
    if view == "Discover People":
        render_people_directory(supabase, user_id)
        return
    if view == "My Profile":
        render_profile_editor(supabase, user_id)
        return
    # Inbox is rendered in sidebar layout by main page, fallback here
    render_whatsapp_inbox(supabase, user_id)

def render_whatsapp_inbox(supabase, user_id):
    # Sidebar list
    search = st.text_input("Search or start new chat", key="eco_sidebar_search_input", placeholder="Search chats…", label_visibility="collapsed")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("＋ New chat", key="eco_new_chat_button", use_container_width=True):
            st.session_state.eco_chat_view = "Discover People"
            st.rerun()
    with c2:
        if st.button("My profile", key="eco_my_profile_button", use_container_width=True):
            st.session_state.eco_chat_view = "My Profile"
            st.rerun()
    st.divider()
    conversations = get_direct_conversations(supabase, user_id)
    # Enrich with latest message + unread, then sort by latest
    enriched = []
    for conv in conversations:
        other_id = get_other_conversation_user(conv, user_id)
        profile = eco_profile(supabase, other_id)
        latest = get_latest_direct_message(supabase, conv.get("id"))
        read_at = get_read_timestamp(supabase, conv.get("id"), user_id)
        unread = 0
        if read_at and latest and str(latest.get("sender_id")) != str(user_id):
            read_dt = _parse_dt(read_at)
            msg_dt = _parse_dt(latest.get("created_at"))
            if read_dt and msg_dt and msg_dt > read_dt:
                unread = 1
        # If search, filter
        q = (search or "").strip().lower()
        if q and q not in eco_display_name(profile).lower() and q not in str(profile.get("username", "")).lower():
            continue
        enriched.append((latest.get("created_at") or conv.get("created_at") or "", conv, profile, latest, unread))
    enriched.sort(key=lambda x: x[0] or "", reverse=True)
    if not enriched:
        st.info("No chats yet. Tap + New chat to start one.")
        return
    for _, conv, profile, latest, unread in enriched:
        name = eco_display_name(profile)
        preview = eco_safe_text(latest.get("message_text"), "📎 Attachment" if latest.get("attachment_path") else "No messages yet")
        if str(latest.get("sender_id")) == str(user_id):
            preview = "✓✓ You: " + preview
        time_label = eco_time_label(latest.get("created_at") or conv.get("created_at"))
        is_active = str(st.session_state.get("eco_active_conversation")) == str(conv.get("id"))
        with st.container(border=True):
            col_a, col_b, col_c = st.columns([0.9, 3.5, 1])
            with col_a:
                st.markdown(eco_avatar_html(profile, 44), unsafe_allow_html=True)
            with col_b:
                st.markdown(f"**{name}**")
                st.caption(preview[:60])
                st.caption("@" + eco_safe_text(profile.get("username"), "member"))
            with col_c:
                st.caption(time_label)
                if unread:
                    st.markdown(f'<div class="wa-unread">{unread}</div>', unsafe_allow_html=True)
                if st.button("Open", key=f"eco_inbox_open_{conv.get('id')}", use_container_width=True):
                    st.session_state.eco_active_conversation = conv.get("id")
                    st.session_state.eco_chat_view = "Conversation"
                    st.session_state.eco_mobile_show_chat = True
                    st.rerun()

# ------------------------------
# Groups
# ------------------------------

def get_chatrooms(supabase, search_text=""):
    try:
        rows = eco_select(supabase, "community_groups", "*", order=("created_at", True), limit=150)
        q = (search_text or "").strip().lower()
        if q:
            rows = [r for r in rows if q in str(r.get("name", "")).lower() or q in str(r.get("description", "")).lower() or q in str(r.get("location", "")).lower()]
        return rows
    except Exception:
        return []

def get_my_chatrooms(supabase, user_id):
    try:
        memberships = eco_select(supabase, "group_memberships", "*", [("eq", "user_id", user_id), ("eq", "status", "approved")], limit=200)
        ids = {str(m.get("group_id")) for m in memberships}
        return [g for g in get_chatrooms(supabase) if str(g.get("id")) in ids]
    except Exception:
        return []

def create_chatroom(supabase, user_id, name, description, image_url="", location=""):
    payload = {"name": name.strip(), "description": description.strip(), "created_by": user_id, "image_url": image_url or None, "location": location.strip() or None}
    result = supabase.table("community_groups").insert(payload).execute()
    rows = eco_result_data(result)
    group_id = rows[0].get("id") if rows else None
    if not group_id:
        matches = eco_select(supabase, "community_groups", "*", [("eq", "created_by", user_id), ("eq", "name", name.strip())], order=("created_at", True), limit=1)
        group_id = matches[0].get("id") if matches else None
    if group_id:
        try:
            supabase.table("group_memberships").upsert({"group_id": group_id, "user_id": user_id, "membership_role": "admin", "status": "approved"}, on_conflict="group_id,user_id").execute()
        except Exception:
            pass
    return group_id

def request_chatroom_join(supabase, group_id, user_id):
    return supabase.table("group_memberships").upsert({"group_id": group_id, "user_id": user_id, "membership_role": "member", "status": "pending"}, on_conflict="group_id,user_id").execute()

def leave_chatroom(supabase, group_id, user_id):
    return supabase.table("group_memberships").delete().eq("group_id", group_id).eq("user_id", user_id).execute()

def is_chatroom_member(supabase, group, user_id):
    try:
        rows = eco_select(supabase, "group_memberships", "*", [("eq", "group_id", group.get("id")), ("eq", "user_id", user_id), ("eq", "status", "approved")], limit=1)
        return bool(rows)
    except Exception:
        return str(group.get("created_by")) == str(user_id)

def get_group_membership(supabase, group_id, user_id):
    try:
        rows = eco_select(supabase, "group_memberships", "*", [("eq", "group_id", group_id), ("eq", "user_id", user_id)], limit=1)
        return rows[0] if rows else {}
    except Exception:
        return {}

def get_chatroom_messages(supabase, group_id, limit=100):
    try:
        return eco_select(supabase, "group_messages", "*", [("eq", "group_id", group_id), ("is_", "deleted_at", "null")], order=("created_at", False), limit=limit)
    except Exception:
        return []

def send_chatroom_message(supabase, group_id, sender_id, message_text, attachments=None):
    payload = {"group_id": group_id, "sender_id": sender_id, "message_text": (message_text or "").strip()}
    if attachments:
        payload["attachments"] = attachments
    if not payload["message_text"] and not attachments:
        return False
    supabase.table("group_messages").insert(payload).execute()
    return True

def manage_group_join_requests(supabase, group_id, action, target_user_id):
    status = "approved" if action == "approve" else "rejected"
    return supabase.table("group_memberships").update({"status": status}).eq("group_id", group_id).eq("user_id", target_user_id).execute()

def render_chatroom_chat(supabase, group, user_id):
    group_id = group.get("id")
    if not is_chatroom_member(supabase, group, user_id):
        st.warning("You need approved membership to view this group chat.")
        if st.button("‹ Back to groups"):
            st.session_state.eco_active_chatroom = None
            st.rerun()
        return
    h1, h2 = st.columns([0.6, 5])
    with h1:
        if st.button("‹", key=f"eco_room_back_{group_id}"):
            st.session_state.eco_active_chatroom = None
            st.rerun()
    with h2:
        st.markdown(f"**{group.get('name', 'Community group')}**")
        st.caption(eco_safe_text(group.get("description"), "Community conversation"))
    st.markdown('<div class="wa-chat-bg">', unsafe_allow_html=True)
    messages = get_chatroom_messages(supabase, group_id)
    for message in messages:
        if message.get("deleted_at"):
            continue
        sender = eco_profile(supabase, message.get("sender_id"))
        sent = str(message.get("sender_id")) == str(user_id)
        name = "You" if sent else eco_display_name(sender)
        attachments = message.get("attachments") or []
        if isinstance(attachments, dict):
            attachments = [attachments]
        for item in attachments:
            if not isinstance(item, dict):
                continue
            media_url = eco_storage_url(supabase, item.get("path") or item.get("url"))
            media_type = str(item.get("type") or "")
            if media_url and media_type.startswith("image"):
                st.image(media_url, use_container_width=True)
            elif media_url and media_type.startswith("video"):
                st.video(media_url)
            elif media_url:
                st.link_button(item.get("name") or "Open attachment", media_url)
        body = str(message.get("message_text") or "")
        if body:
            st.markdown(eco_bubble_html(body, eco_time_short(message.get("created_at")), sent, "" if sent else name, bool(message.get("edited_at"))), unsafe_allow_html=True)
        if sent and message.get("id"):
            with st.expander("···"):
                edited = st.text_input("Edit message", value=body, key=f"eco_group_edit_text_{message['id']}")
                a, b = st.columns(2)
                with a:
                    if st.button("Save", key=f"eco_group_edit_{message['id']}", use_container_width=True):
                        try:
                            eco_edit_message(supabase, "group_messages", message["id"], user_id, edited)
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Could not edit: {exc}")
                with b:
                    if st.button("Delete", key=f"eco_group_delete_{message['id']}", use_container_width=True):
                        try:
                            eco_soft_delete_message(supabase, "group_messages", message["id"], user_id)
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Could not delete: {exc}")
    st.markdown('</div>', unsafe_allow_html=True)
    attachment = st.file_uploader("Attach", type=["jpg", "jpeg", "png", "webp", "mp4", "mov", "pdf"], key=f"eco_group_attach_{group_id}", label_visibility="collapsed")
    typed = st.chat_input(f"Message {group.get('name', 'the group')}…", key=f"eco_group_composer_{group_id}")
    send_attach = False
    if attachment is not None:
        send_attach = st.button("Send attachment ➤", key=f"eco_group_send_attachment_{group_id}", use_container_width=True)
    if typed is not None or send_attach:
        try:
            items = []
            selected = attachment if send_attach else None
            if selected:
                path = eco_upload(supabase, selected, "groups", user_id, allow_video=True, allow_documents=True)
                items.append({"path": path, "name": selected.name, "type": selected.type or ""})
            if typed or items:
                send_chatroom_message(supabase, group_id, user_id, typed or "", items)
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
        else:
            st.markdown(f'<div class="wa-avatar">{eco_initials(group.get("name", "G"))}</div>', unsafe_allow_html=True)
        st.markdown(f"**{group.get('name', 'Community group')}**")
        if group.get("location"):
            st.caption("📍 " + str(group["location"]))
        st.write(str(group.get("description") or "A space for people to connect and take action.")[:220])
        if approved:
            st.caption("🟢 Member" if not is_owner else "⭐ Group admin")
            if st.button("Open group chat", key=f"eco_group_open_{view_name}_{group_id}_{index}", use_container_width=True):
                st.session_state.eco_active_chatroom = group_id
                st.rerun()
            if not is_owner and st.button("Leave group", key=f"eco_group_leave_{view_name}_{group_id}_{index}"):
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
                    st.error(f"Could not request membership: {exc}")
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
            if st.button("Back to groups"):
                st.session_state.eco_active_chatroom = None
                st.rerun()
        return
    st.markdown('<div class="wa-topbar"><b>Groups</b><span>Community</span></div>', unsafe_allow_html=True)
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
        for group in groups:
            if str(group.get("created_by")) != str(user_id):
                continue
            with st.expander(f"Manage requests · {group.get('name', 'Group')}"):
                try:
                    pending = eco_select(supabase, "group_memberships", "*", [("eq", "group_id", group.get("id")), ("eq", "status", "pending")], limit=100)
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
    return supabase.table("stories").insert({"user_id": user_id, "caption": (caption or "").strip(), "media_url": media_path, "media_type": media_type, "created_at": now.isoformat(), "expires_at": expires.isoformat()}).execute()

def get_active_stories(supabase):
    try:
        return eco_select(supabase, "stories", "*", [("gt", "expires_at", eco_iso())], order=("created_at", True), limit=150)
    except Exception:
        return []

def render_story_card(supabase, story, current_user_id, index):
    profile = eco_profile(supabase, story.get("user_id"))
    name = "Your update" if str(story.get("user_id")) == str(current_user_id) else eco_display_name(profile)
    with st.container(border=True):
        c1, c2 = st.columns([1, 4])
        with c1:
            st.markdown(eco_avatar_html(profile, 44), unsafe_allow_html=True)
        with c2:
            st.markdown(f"**{name}**")
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
    st.markdown('<div class="wa-topbar"><b>Updates</b><span>24 hours</span></div>', unsafe_allow_html=True)
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
# Discover
# ------------------------------

def render_community_discover(supabase, user_id):
    st.markdown('<div class="wa-topbar"><b>Discover</b><span>People & Groups</span></div>', unsafe_allow_html=True)
    query = st.text_input("Search people or groups", key="eco_discover_search_input", placeholder="Search names, usernames, groups or locations…")
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
# Main Entry - WhatsApp Layout
# ------------------------------

def render_community_groups_page(supabase, user_id):
    eco_init_state()
    eco_inject_whatsapp_styles()
    private_chat_open = st.session_state.get("eco_chat_view") == "Conversation"
    chatroom_open = bool(st.session_state.get("eco_active_chatroom"))
    st.session_state["eco_hide_app_footer"] = bool(private_chat_open or chatroom_open)

    # Focused chat = full screen, no sidebar
    if private_chat_open:
        try:
            render_direct_conversation(supabase, user_id)
        except Exception as exc:
            st.error("The private conversation could not load.")
            st.caption(f"Technical detail: {exc}")
        return
    if chatroom_open:
        try:
            render_chatrooms_page(supabase, user_id)
        except Exception as exc:
            st.error("The chatroom could not load.")
            st.caption(f"Technical detail: {exc}")
        return

    # Top bar like WhatsApp
    me = eco_profile(supabase, user_id)
    st.markdown(
        f'<div class="wa-topbar"><div style="display:flex;align-items:center;gap:10px;">{eco_avatar_html(me, 38)}<div><b>Community Hub</b><br><span>Next Gen Impact Hub · {eco_display_name(me)}</span></div></div><span>Connect · Collaborate · Create impact</span></div>',
        unsafe_allow_html=True,
    )

    # Top nav like WhatsApp tabs
    options = ["💬 Chats", "👥 Groups", "🟢 Updates", "🔎 Discover"]
    labels = {"💬 Chats": "Chats", "👥 Groups": "Groups", "🟢 Updates": "Updates", "🔎 Discover": "Discover"}
    current = st.session_state.get("eco_community_section", "Chats")
    current_option = next((k for k, v in labels.items() if v == current), options[0])
    selected = st.radio("Community navigation", options, horizontal=True, key=MAIN_NAV_KEY, index=options.index(current_option), label_visibility="collapsed")
    section = labels[selected]
    st.session_state.eco_community_section = section

    try:
        if section == "Chats":
            # WhatsApp split: left list, right preview
            left, right = st.columns([1, 1.2])
            with left:
                render_whatsapp_inbox(supabase, user_id)
            with right:
                st.markdown('<div class="wa-empty"><div style="font-size:64px;">💬</div><h3>EcoLoop Web</h3><p>Select a chat to start messaging.<br>Your messages are private to your community.</p><p style="font-size:12px;color:#8696A0;">Powered by Next Gen Impact Hub (NGIH)</p></div>', unsafe_allow_html=True)
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
