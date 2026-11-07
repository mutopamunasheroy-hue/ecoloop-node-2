# ============================================================
# ECOLOOP NODE — COMMUNITY HUB 2.0
# Powered by Next Gen Impact Hub (NGIH)
# WhatsApp-inspired Community Experience
# ============================================================

import streamlit as st
import uuid
import mimetypes
from datetime import datetime, timezone, timedelta
from urllib.parse import quote


# ============================================================
# CONFIGURATION
# ============================================================

MAX_UPLOAD_MB = 15
STORY_HOURS = 24

GREEN = "#25D366"
DARK_GREEN = "#075E54"


# ============================================================
# DATABASE HELPERS
# ============================================================

def _data(response):
    return getattr(response, "data", None) or []


def _safe_query(query):
    try:
        return _data(query.execute())
    except Exception:
        return []


def _profile(supabase, user_id):
    if not user_id:
        return {}

    rows = _safe_query(
        supabase.table("member_profiles")
        .select("*")
        .eq("user_id", user_id)
        .limit(1)
    )

    return rows[0] if rows else {}


def _name(profile, fallback="Member"):
    return (
        profile.get("display_name")
        or profile.get("username")
        or fallback
    )


def _get_profiles(supabase, user_ids):
    result = {}

    for uid in set(user_ids):
        if not uid:
            continue

        profile = _profile(supabase, uid)
        result[uid] = profile

    return result


def _get_conversation(supabase, user_id, other_id):
    first, second = sorted([str(user_id), str(other_id)])

    rows = _safe_query(
        supabase.table("direct_conversations")
        .select("*")
        .eq("user_one_id", first)
        .eq("user_two_id", second)
        .limit(1)
    )

    if rows:
        return rows[0]

    try:
        response = (
            supabase.table("direct_conversations")
            .insert({
                "user_one_id": first,
                "user_two_id": second
            })
            .execute()
        )

        created = _data(response)
        return created[0] if created else None

    except Exception:
        rows = _safe_query(
            supabase.table("direct_conversations")
            .select("*")
            .eq("user_one_id", first)
            .eq("user_two_id", second)
            .limit(1)
        )

        return rows[0] if rows else None


def _upload(supabase, user_id, uploaded, folder):
    if uploaded is None:
        return None

    try:
        extension = uploaded.name.split(".")[-1]
        filename = f"{uuid.uuid4().hex}.{extension}"
        path = f"{folder}/{user_id}/{filename}"

        bucket = supabase.storage.from_("community-media")

        bucket.upload(
            path,
            uploaded.getvalue(),
            {
                "content-type": (
                    uploaded.type
                    or mimetypes.guess_type(uploaded.name)[0]
                    or "application/octet-stream"
                ),
                "upsert": "true"
            }
        )

        return path

    except Exception as exc:
        st.error(f"Upload failed: {exc}")
        return None


def _media_url(supabase, path):
    if not path:
        return None

    try:
        result = supabase.storage.from_(
            "community-media"
        ).create_signed_url(path, 3600)

        return result.get("signedURL") or result.get("signedUrl")

    except Exception:
        try:
            result = supabase.storage.from_(
                "community-media"
            ).get_public_url(path)

            return result

        except Exception:
            return None


def _time(value):
    if not value:
        return ""

    try:
        dt = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        return dt.astimezone().strftime("%H:%M")

    except Exception:
        return ""


# ============================================================
# SESSION STATE
# ============================================================

def _init_state():
    defaults = {
        "community_tab": "Chats",
        "community_view": "home",
        "community_chat_type": "direct",
        "community_active_chat": None,
        "community_active_group": None,
        "community_active_channel": None,
        "community_reply": None,
        "community_editing": None,
        "community_profile": None,
        "community_search": "",
        "community_message_input": "",
        "community_show_people": False,
        "community_story_view": None,
        "community_story_caption": "",
        "community_notice": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ============================================================
# VISUAL DESIGN
# ============================================================

def _styles():
    st.markdown("""
    <style>

    .eco-header {
        background: linear-gradient(120deg,#075E54,#128C7E);
        padding: 22px;
        border-radius: 18px;
        color: white;
        margin-bottom: 15px;
    }

    .eco-header h2 {
        color: white !important;
        margin: 0;
    }

    .eco-header p {
        color: #e1fff2;
        margin: 5px 0 0 0;
    }

    .eco-card {
        background: var(--secondary-background-color);
        border: 1px solid rgba(128,128,128,.2);
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
    }

    .eco-bubble {
        padding: 11px 14px;
        border-radius: 15px;
        margin: 7px 0;
        max-width: 85%;
        overflow-wrap: anywhere;
        font-size: 14px;
    }

    .eco-mine {
        background: #DCF8C6;
        color: #172b18;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }

    .eco-theirs {
        background: var(--secondary-background-color);
        border: 1px solid rgba(128,128,128,.2);
        margin-right: auto;
        border-bottom-left-radius: 4px;
    }

    .eco-meta {
        font-size: 10px;
        opacity: .65;
        text-align: right;
        margin-top: 5px;
    }

    .eco-section {
        font-weight: 700;
        font-size: 18px;
        margin: 15px 0 10px 0;
    }

    .eco-avatar {
        width: 45px;
        height: 45px;
        border-radius: 50%;
        object-fit: cover;
    }

    .eco-unread {
        background: #25D366;
        color: white;
        padding: 3px 8px;
        border-radius: 20px;
        font-size: 11px;
    }

    div.stButton > button {
        border-radius: 12px;
    }

    </style>
    """, unsafe_allow_html=True)


def _header():
    st.markdown("""
    <div class="eco-header">
        <h2>🌍 EcoLoop Community</h2>
        <p>Connect. Share. Collaborate. Create impact.</p>
    </div>
    """, unsafe_allow_html=True)


def _avatar(profile):
    url = profile.get("avatar_url")

    if url:
        return f'<img class="eco-avatar" src="{url}"/>'

    return "👤"


# ============================================================
# NAVIGATION
# ============================================================

def _navigation():
    tabs = ["Chats", "Updates", "Communities", "Channels"]

    current = st.session_state.community_tab

    cols = st.columns(4)

    for i, tab in enumerate(tabs):
        with cols[i]:
            if st.button(
                tab,
                key=f"eco_nav_{tab}",
                use_container_width=True,
                type="primary" if current == tab else "secondary"
            ):
                st.session_state.community_tab = tab
                st.session_state.community_view = "home"
                st.rerun()


# ============================================================
# PEOPLE DIRECTORY
# ============================================================

def _people_directory(supabase, user_id):
    st.markdown("### 👥 Discover Members")

    search = st.text_input(
        "Search members",
        key="eco_people_search",
        placeholder="Search by username or name..."
    )

    try:
        response = (
            supabase.table("member_profiles")
            .select("*")
            .limit(100)
            .execute()
        )

        people = _data(response)

    except Exception as exc:
        st.error(f"Could not load members: {exc}")
        return

    for person in people:
        uid = person.get("user_id")

        if uid == user_id:
            continue

        name = _name(person)
        username = person.get("username", "")

        if search:
            term = search.lower()

            if (
                term not in name.lower()
                and term not in username.lower()
            ):
                continue

        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 3, 2])

            with c1:
                url = person.get("avatar_url")

                if url:
                    st.image(url, width=45)
                else:
                    st.write("👤")

            with c2:
                st.write(f"**{name}**")
                st.caption(f"@{username}" if username else "EcoLoop member")

            with c3:
                if st.button(
                    "Message",
                    key=f"person_msg_{uid}"
                ):
                    conversation = _get_conversation(
                        supabase, user_id, uid
                    )

                    if conversation:
                        st.session_state.community_active_chat = (
                            conversation["id"]
                        )
                        st.session_state.community_chat_type = "direct"
                        st.session_state.community_profile = uid
                        st.session_state.community_view = "chat"
                        st.rerun()


# ============================================================
# CHATS HOME
# ============================================================

def _chats_home(supabase, user_id):
    c1, c2 = st.columns([3, 1])

    with c1:
        st.markdown("### 💬 Your conversations")

    with c2:
        if st.button("＋ New chat", use_container_width=True):
            st.session_state.community_show_people = True
            st.rerun()

    if st.session_state.community_show_people:
        _people_directory(supabase, user_id)

        if st.button("← Back to chats"):
            st.session_state.community_show_people = False
            st.rerun()

        return

    search = st.text_input(
        "Search conversations",
        key="eco_chat_search",
        placeholder="Search people..."
    )

    # Private conversations
    conversations = _safe_query(
        supabase.table("direct_conversations")
        .select("*")
        .or_(
            f"user_one_id.eq.{user_id},"
            f"user_two_id.eq.{user_id}"
        )
        .order("created_at", desc=True)
    )

    if not conversations:
        st.info(
            "Your conversations will appear here. "
            "Start a new conversation with an EcoLoop member."
        )
        return

    for conversation in conversations:
        other_id = (
            conversation["user_two_id"]
            if conversation["user_one_id"] == user_id
            else conversation["user_one_id"]
        )

        profile = _profile(supabase, other_id)
        name = _name(profile)

        if search and search.lower() not in name.lower():
            continue

        messages = _safe_query(
            supabase.table("direct_messages")
            .select("*")
            .eq("conversation_id", conversation["id"])
            .order("created_at", desc=True)
            .limit(1)
        )

        preview = ""

        if messages:
            preview = (
                messages[0].get("message_text")
                or "📎 Attachment"
            )

            if messages[0].get("deleted_at"):
                preview = "This message was deleted"

        with st.container(border=True):
            a, b = st.columns([1, 5])

            with a:
                avatar = profile.get("avatar_url")

                if avatar:
                    st.image(avatar, width=48)
                else:
                    st.write("👤")

            with b:
                st.write(f"**{name}**")
                st.caption(preview[:65] or "Start chatting")

                if st.button(
                    "Open conversation",
                    key=f"open_dm_{conversation['id']}",
                    use_container_width=True
                ):
                    st.session_state.community_active_chat = (
                        conversation["id"]
                    )
                    st.session_state.community_profile = other_id
                    st.session_state.community_chat_type = "direct"
                    st.session_state.community_view = "chat"
                    st.rerun()

    # Group conversations
    st.markdown("### 👥 Group conversations")

    memberships = _safe_query(
        supabase.table("group_memberships")
        .select("group_id")
        .eq("user_id", user_id)
        .eq("status", "active")
    )

    for membership in memberships:
        groups = _safe_query(
            supabase.table("community_groups")
            .select("*")
            .eq("id", membership["group_id"])
            .limit(1)
        )

        if not groups:
            continue

        group = groups[0]

        with st.container(border=True):
            st.write(f"🌿 **{group['name']}**")
            st.caption(group.get("description", ""))

            if st.button(
                "Open group chat",
                key=f"chat_group_{group['id']}",
                use_container_width=True
            ):
                st.session_state.community_active_group = group["id"]
                st.session_state.community_chat_type = "group"
                st.session_state.community_view = "group_chat"
                st.rerun()


# ============================================================
# MESSAGE ACTIONS
# ============================================================

def _message_table(chat_type):
    if chat_type == "direct":
        return "direct_messages"

    if chat_type == "group":
        return "group_messages"

    return "channel_messages"


def _message_parent(chat_type, chat_id):
    if chat_type == "direct":
        return {"conversation_id": chat_id}

    if chat_type == "group":
        return {"group_id": chat_id}

    return {"channel_id": chat_id}


def _send_message(
    supabase,
    user_id,
    chat_type,
    chat_id,
    message,
    uploaded=None,
    reply_to=None
):
    table = _message_table(chat_type)

    payload = {
        **_message_parent(chat_type, chat_id),
        "sender_id": user_id,
        "message_text": message.strip() if message else None
    }

    if reply_to:
        payload["reply_to_id"] = reply_to

    if uploaded:
        path = _upload(
            supabase,
            user_id,
            uploaded,
            "messages"
        )

        if not path:
            return False

        payload["attachment_path"] = path
        payload["attachment_name"] = uploaded.name
        payload["attachment_type"] = uploaded.type

    try:
        supabase.table(table).insert(payload).execute()

        st.session_state.community_reply = None
        return True

    except Exception as exc:
        st.error(f"Message could not be sent: {exc}")
        return False


def _edit_message(supabase, table, message_id, new_text):
    try:
        supabase.table(table).update({
            "message_text": new_text,
            "edited_at": datetime.now(
                timezone.utc
            ).isoformat()
        }).eq("id", message_id).execute()

        st.session_state.community_editing = None
        st.success("Message updated.")
        return True

    except Exception as exc:
        st.error(f"Could not edit message: {exc}")
        return False


def _delete_message(supabase, table, message_id):
    try:
        supabase.table(table).update({
            "message_text": "This message was deleted",
            "deleted_at": datetime.now(
                timezone.utc
            ).isoformat()
        }).eq("id", message_id).execute()

        st.success("Message deleted.")
        return True

    except Exception as exc:
        st.error(f"Could not delete message: {exc}")
        return False


# ============================================================
# MESSAGE DISPLAY
# ============================================================

def _display_messages(supabase, user_id, chat_type, chat_id):
    table = _message_table(chat_type)

    messages = _safe_query(
        supabase.table(table)
        .select("*")
        .match(_message_parent(chat_type, chat_id))
        .order("created_at", desc=False)
        .limit(200)
    )

    profiles = _get_profiles(
        supabase,
        [m.get("sender_id") for m in messages]
    )

    for msg in messages:
        sender_id = msg.get("sender_id")
        mine = sender_id == user_id

        profile = profiles.get(sender_id, {})
        sender = _name(profile)

        deleted = bool(msg.get("deleted_at"))
        edited = bool(msg.get("edited_at"))

        text = msg.get("message_text") or ""

        if deleted:
            text = "🚫 This message was deleted"

        if not mine:
            st.caption(sender)

        alignment = "eco-mine" if mine else "eco-theirs"

        safe_text = (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )

        timestamp = _time(msg.get("created_at"))

        st.markdown(
            f"""
            <div class="eco-bubble {alignment}">
                {safe_text}
                <div class="eco-meta">
                    {"Edited · " if edited else ""}
                    {timestamp}
                    {" ✓✓" if mine else ""}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        attachment = msg.get("attachment_path")

        if attachment and not deleted:
            url = _media_url(supabase, attachment)

            if url:
                kind = msg.get("attachment_type", "")

                if kind.startswith("image/"):
                    st.image(url, width=250)

                elif kind.startswith("video/"):
                    st.video(url)

                elif kind.startswith("audio/"):
                    st.audio(url)

                else:
                    st.link_button(
                        f"📎 {msg.get('attachment_name', 'Download attachment')}",
                        url
                    )

        # Message action controls
        if not deleted:
            with st.popover("⋮ Message options"):
                if st.button(
                    "↩ Reply",
                    key=f"reply_{msg['id']}"
                ):
                    st.session_state.community_reply = {
                        "id": msg["id"],
                        "text": text[:100]
                    }
                    st.rerun()

                if st.button(
                    "❤️ React",
                    key=f"react_{msg['id']}"
                ):
                    st.info(
                        "Message reactions require the "
                        "community_reactions database table."
                    )

                if mine:
                    if st.button(
                        "✏️ Edit message",
                        key=f"edit_{msg['id']}"
                    ):
                        st.session_state.community_editing = {
                            "id": msg["id"],
                            "text": text
                        }
                        st.rerun()

                    if st.button(
                        "🗑 Delete message",
                        key=f"delete_{msg['id']}"
                    ):
                        _delete_message(
                            supabase,
                            table,
                            msg["id"]
                        )
                        st.rerun()


# ============================================================
# CHAT COMPOSER
# ============================================================

def _composer(supabase, user_id, chat_type, chat_id):
    editing = st.session_state.community_editing
    reply = st.session_state.community_reply

    if reply:
        st.info(f"↩ Replying to: {reply['text']}")

        if st.button("Cancel reply"):
            st.session_state.community_reply = None
            st.rerun()

    if editing:
        st.warning("Editing your message")

        edited = st.text_area(
            "Edit message",
            value=editing["text"],
            key=f"editing_text_{editing['id']}"
        )

        a, b = st.columns(2)

        with a:
            if st.button("Save changes", use_container_width=True):
                if edited.strip():
                    _edit_message(
                        supabase,
                        _message_table(chat_type),
                        editing["id"],
                        edited.strip()
                    )
                    st.rerun()

        with b:
            if st.button("Cancel", use_container_width=True):
                st.session_state.community_editing = None
                st.rerun()

        return

    with st.form(
        key=f"message_form_{chat_type}_{chat_id}",
        clear_on_submit=True
    ):
        message = st.text_area(
            "Message",
            placeholder="Type a message...",
            height=75
        )

        attachment = st.file_uploader(
            "📎 Attach photo, video, audio or document",
            type=[
                "png", "jpg", "jpeg", "webp",
                "mp4", "mov", "mp3", "wav",
                "pdf", "doc", "docx",
                "txt", "xlsx", "csv"
            ],
            key=f"upload_{chat_type}_{chat_id}"
        )

        send = st.form_submit_button(
            "➤ Send message",
            use_container_width=True
        )

        if send:
            if not message.strip() and not attachment:
                st.warning("Write a message or attach a file.")

            else:
                reply_id = (
                    reply["id"] if reply else None
                )

                success = _send_message(
                    supabase,
                    user_id,
                    chat_type,
                    chat_id,
                    message,
                    attachment,
                    reply_id
                )

                if success:
                    st.rerun()


# ============================================================
# PRIVATE CHAT
# ============================================================

def _private_chat(supabase, user_id):
    chat_id = st.session_state.community_active_chat
    other_id = st.session_state.community_profile

    if not chat_id:
        return

    profile = _profile(supabase, other_id)

    a, b = st.columns([1, 5])

    with a:
        if st.button("← Back"):
            st.session_state.community_view = "home"
            st.rerun()

    with b:
        st.markdown(f"### 💬 {_name(profile)}")
        st.caption(
            f"@{profile.get('username', 'member')}"
        )

    if profile.get("bio"):
        st.caption(profile["bio"])

    c1, c2 = st.columns(2)

    with c1:
        st.button(
            "📞 Voice call",
            key="eco_voice_call",
            use_container_width=True,
            disabled=True
        )

    with c2:
        st.button(
            "📹 Video call",
            key="eco_video_call",
            use_container_width=True,
            disabled=True
        )

    st.divider()

    _display_messages(
        supabase,
        user_id,
        "direct",
        chat_id
    )

    st.divider()

    _composer(
        supabase,
        user_id,
        "direct",
        chat_id
    )


# ============================================================
# GROUP DISCOVERY
# ============================================================

def _groups_home(supabase, user_id):
    st.markdown("### 🌿 Explore Groups")

    a, b = st.columns(2)

    with a:
        st.markdown("**My Groups**")

    with b:
        if st.button("＋ Create group", use_container_width=True):
            st.session_state.community_view = "create_group"
            st.rerun()

    memberships = _safe_query(
        supabase.table("group_memberships")
        .select("group_id")
        .eq("user_id", user_id)
        .eq("status", "active")
    )

    my_ids = [m["group_id"] for m in memberships]

    if my_ids:
        groups = []

        for gid in my_ids:
            found = _safe_query(
                supabase.table("community_groups")
                .select("*")
                .eq("id", gid)
                .limit(1)
            )

            groups.extend(found)

        for group in groups:
            with st.container(border=True):
                st.markdown(f"### 🌱 {group['name']}")
                st.caption(group.get("description", ""))

                if st.button(
                    "Open group",
                    key=f"group_open_{group['id']}",
                    use_container_width=True
                ):
                    st.session_state.community_active_group = group["id"]
                    st.session_state.community_view = "group_chat"
                    st.rerun()

    else:
        st.info("You haven't joined any groups yet.")

    st.divider()
    st.markdown("### 🔎 Discover new groups")

    all_groups = _safe_query(
        supabase.table("community_groups")
        .select("*")
        .order("created_at", desc=True)
        .limit(100)
    )

    for group in all_groups:
        if group["id"] in my_ids:
            continue

        with st.container(border=True):
            st.markdown(f"### 🌍 {group['name']}")
            st.write(group.get("description", ""))
            st.caption(group.get("location", "Community group"))

            if st.button(
                "Join group",
                key=f"join_{group['id']}",
                use_container_width=True
            ):
                try:
                    supabase.table("group_memberships").insert({
                        "group_id": group["id"],
                        "user_id": user_id,
                        "membership_role": "member",
                        "status": "active"
                    }).execute()

                    st.success("You joined the group!")
                    st.rerun()

                except Exception as exc:
                    st.error(f"Could not join group: {exc}")


# ============================================================
# CREATE GROUP
# ============================================================

def _create_group(supabase, user_id):
    st.markdown("### ＋ Create a community group")

    with st.form("eco_create_group"):
        name = st.text_input("Group name")

        description = st.text_area(
            "About this group"
        )

        location = st.text_input(
            "Location (optional)"
        )

        submit = st.form_submit_button(
            "Create group",
            use_container_width=True
        )

        if submit:
            if not name.strip():
                st.error("Please enter a group name.")

            else:
                try:
                    result = supabase.table(
                        "community_groups"
                    ).insert({
                        "name": name.strip(),
                        "description": description,
                        "created_by": user_id,
                        "location": location
                    }).execute()

                    created = _data(result)

                    if created:
                        group_id = created[0]["id"]

                        supabase.table(
                            "group_memberships"
                        ).insert({
                            "group_id": group_id,
                            "user_id": user_id,
                            "membership_role": "admin",
                            "status": "active"
                        }).execute()

                        st.success("Group created!")
                        st.session_state.community_view = "home"
                        st.session_state.community_tab = "Groups"
                        st.rerun()

                except Exception as exc:
                    st.error(f"Could not create group: {exc}")


# ============================================================
# GROUP CHAT
# ============================================================

def _group_chat(supabase, user_id):
    group_id = st.session_state.community_active_group

    if not group_id:
        return

    groups = _safe_query(
        supabase.table("community_groups")
        .select("*")
        .eq("id", group_id)
        .limit(1)
    )

    if not groups:
        st.error("Group not found.")
        return

    group = groups[0]

    if st.button("← Back to groups"):
        st.session_state.community_view = "home"
        st.session_state.community_tab = "Groups"
        st.rerun()

    st.markdown(f"## 🌿 {group['name']}")
    st.caption(group.get("description", ""))

    members = _safe_query(
        supabase.table("group_memberships")
        .select("*")
        .eq("group_id", group_id)
        .eq("status", "active")
    )

    st.caption(f"👥 {len(members)} members")

    st.divider()

    _display_messages(
        supabase,
        user_id,
        "group",
        group_id
    )

    st.divider()

    _composer(
        supabase,
        user_id,
        "group",
        group_id
    )


# ============================================================
# STORIES / UPDATES
# ============================================================

def _updates_home(supabase, user_id):
    st.markdown("### 📸 Community Updates")

    with st.expander("＋ Share an update"):
        with st.form("eco_story_form"):
            caption = st.text_area(
                "What's happening?"
            )

            media = st.file_uploader(
                "Add a photo or video",
                type=["jpg", "jpeg", "png", "webp", "mp4", "mov"]
            )

            submit = st.form_submit_button(
                "Share update"
            )

            if submit:
                media_path = None
                media_type = None

                if media:
                    media_path = _upload(
                        supabase,
                        user_id,
                        media,
                        "stories"
                    )

                    if not media_path:
                        st.error("Story upload failed.")
                        return

                    media_type = media.type

                try:
                    now = datetime.now(timezone.utc)

                    supabase.table("community_stories").insert({
                        "user_id": user_id,
                        "caption": caption,
                        "media_url": media_path,
                        "media_type": media_type,
                        "expires_at": (
                            now + timedelta(hours=STORY_HOURS)
                        ).isoformat()
                    }).execute()

                    st.success("Your update has been shared!")
                    st.rerun()

                except Exception as exc:
                    st.error(f"Could not share update: {exc}")

    st.divider()

    stories = _safe_query(
        supabase.table("community_stories")
        .select("*")
        .gt(
            "expires_at",
            datetime.now(timezone.utc).isoformat()
        )
        .order("created_at", desc=True)
        .limit(100)
    )

    if not stories:
        st.info("No recent updates yet. Be the first to share!")
        return

    profiles = _get_profiles(
        supabase,
        [s.get("user_id") for s in stories]
    )

    for story in stories:
        profile = profiles.get(story["user_id"], {})

        with st.container(border=True):
            st.markdown(
                f"**🟢 {_name(profile)}**"
            )

            st.caption(_time(story.get("created_at")))

            if story.get("media_url"):
                url = _media_url(
                    supabase,
                    story["media_url"]
                )

                if url:
                    if (
                        story.get("media_type", "")
                        .startswith("video/")
                    ):
                        st.video(url)
                    else:
                        st.image(url, use_container_width=True)

            if story.get("caption"):
                st.write(story["caption"])


# ============================================================
# COMMUNITIES
# ============================================================

def _communities_home(supabase, user_id):
    st.markdown("### 🌍 EcoLoop Communities")

    communities = _safe_query(
        supabase.table("communities")
        .select("*")
        .order("created_at", desc=True)
        .limit(100)
    )

    if not communities:
        st.info("Communities will appear here.")
        return

    for community in communities:
        with st.container(border=True):
            if community.get("image_url"):
                st.image(
                    community["image_url"],
                    width=100
                )

            st.markdown(
                f"### 🌱 {community['name']}"
            )

            st.write(
                community.get("description", "")
            )

            st.caption(
                community.get("location", "")
            )

            if st.button(
                "Explore community",
                key=f"community_{community['id']}"
            ):
                st.session_state.community_active_community = (
                    community["id"]
                )
                st.session_state.community_view = "community_detail"
                st.rerun()


def _community_detail(supabase, user_id):
    community_id = st.session_state.get(
        "community_active_community"
    )

    if not community_id:
        return

    if st.button("← Back"):
        st.session_state.community_view = "home"
        st.rerun()

    communities = _safe_query(
        supabase.table("communities")
        .select("*")
        .eq("id", community_id)
        .limit(1)
    )

    if not communities:
        return

    community = communities[0]

    st.markdown(f"## 🌍 {community['name']}")
    st.write(community.get("description", ""))

    st.markdown("### Community groups")

    groups = _safe_query(
        supabase.table("community_groups")
        .select("*")
        .eq("community_id", community_id)
    )

    for group in groups:
        with st.container(border=True):
            st.write(f"**🌱 {group['name']}**")
            st.caption(group.get("description", ""))

            if st.button(
                "Open group",
                key=f"community_group_{group['id']}"
            ):
                st.session_state.community_active_group = group["id"]
                st.session_state.community_view = "group_chat"
                st.rerun()


# ============================================================
# CHANNELS
# ============================================================

def _channels_home(supabase, user_id):
    st.markdown("### 📢 Community Channels")

    channels = _safe_query(
        supabase.table("community_channels")
        .select("*")
        .eq("is_active", True)
        .order("created_at", desc=True)
    )

    if not channels:
        st.info("No active channels available.")
        return

    for channel in channels:
        with st.container(border=True):
            st.markdown(
                f"### 📢 {channel['name']}"
            )

            st.write(channel.get("description", ""))

            if st.button(
                "Open channel",
                key=f"channel_{channel['id']}"
            ):
                st.session_state.community_active_channel = (
                    channel["id"]
                )
                st.session_state.community_view = "channel_chat"
                st.rerun()


def _channel_chat(supabase, user_id):
    channel_id = st.session_state.community_active_channel

    if not channel_id:
        return

    if st.button("← Back to channels"):
        st.session_state.community_view = "home"
        st.session_state.community_tab = "Channels"
        st.rerun()

    channels = _safe_query(
        supabase.table("community_channels")
        .select("*")
        .eq("id", channel_id)
        .limit(1)
    )

    if not channels:
        return

    channel = channels[0]

    st.markdown(f"## 📢 {channel['name']}")
    st.write(channel.get("description", ""))

    _display_messages(
        supabase,
        user_id,
        "channel",
        channel_id
    )

    st.divider()

    # Channel posting restricted to administrators.
    memberships = _safe_query(
        supabase.table("group_memberships")
        .select("membership_role")
        .eq("user_id", user_id)
        .eq("status", "active")
    )

    is_admin = any(
        m.get("membership_role") in ["admin", "moderator"]
        for m in memberships
    )

    if is_admin:
        _composer(
            supabase,
            user_id,
            "channel",
            channel_id
        )
    else:
        st.info("Only authorised administrators can post here.")


# ============================================================
# PROFILE
# ============================================================

def _my_profile(supabase, user_id):
    st.markdown("### 👤 My Community Profile")

    profile = _profile(supabase, user_id)

    if profile.get("avatar_url"):
        st.image(
            profile["avatar_url"],
            width=120
        )

    st.markdown(
        f"## {_name(profile)}"
    )

    if profile.get("username"):
        st.caption(f"@{profile['username']}")

    st.write(
        profile.get("bio", "Add a bio to introduce yourself.")
    )

    if profile.get("location"):
        st.caption(f"📍 {profile['location']}")

    if st.button("Edit profile"):
        st.info(
            "Your main EcoLoop account profile settings "
            "remain managed by the account profile module."
        )


# ============================================================
# MAIN COMMUNITY HUB
# ============================================================

def render_community_groups_page(supabase, user_id):

    _init_state()
    _styles()
    _header()

    if not user_id:
        st.warning("Please sign in to access the Community Hub.")
        return

    view = st.session_state.community_view
    tab = st.session_state.community_tab

    # --------------------------------------------------------
    # OPEN PRIVATE CHAT
    # --------------------------------------------------------

    if view == "chat":
        _private_chat(supabase, user_id)
        return

    # --------------------------------------------------------
    # OPEN GROUP CHAT
    # --------------------------------------------------------

    if view == "group_chat":
        _group_chat(supabase, user_id)
        return

    # --------------------------------------------------------
    # CREATE GROUP
    # --------------------------------------------------------

    if view == "create_group":
        _create_group(supabase, user_id)
        return

    # --------------------------------------------------------
    # COMMUNITY DETAIL
    # --------------------------------------------------------

    if view == "community_detail":
        _community_detail(supabase, user_id)
        return

    # --------------------------------------------------------
    # CHANNEL CHAT
    # --------------------------------------------------------

    if view == "channel_chat":
        _channel_chat(supabase, user_id)
        return

    # --------------------------------------------------------
    # HOME NAVIGATION
    # --------------------------------------------------------

    _navigation()

    if tab == "Chats":
        _chats_home(supabase, user_id)

    elif tab == "Updates":
        _updates_home(supabase, user_id)

    elif tab == "Communities":
        _communities_home(supabase, user_id)

    elif tab == "Channels":
        _channels_home(supabase, user_id)

    # --------------------------------------------------------
    # PROFILE ACCESS
    # --------------------------------------------------------

    st.divider()

    if st.button(
        "👤 My Community Profile",
        use_container_width=True
    ):
        st.session_state.community_view = "profile"
        st.rerun()


# ============================================================
# END OF ECOLOOP NODE COMMUNITY HUB
# ============================================================
