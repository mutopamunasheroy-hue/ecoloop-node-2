
import streamlit as st
import uuid
import html
from datetime import datetime, timedelta, timezone


# ============================================================
# ECOLOOP NODE — COMMUNITY HUB
# Embedded page module. Uses the main app's Supabase client.
# ============================================================

BUCKET = "community-media"

SECTIONS = ["Chats", "Chat Rooms", "Updates", "Discover", "Profile"]


# ------------------------------------------------------------
# GENERAL HELPERS
# ------------------------------------------------------------

def _now():
    return datetime.now(timezone.utc).isoformat()


def _uid():
    return st.session_state.get("eco_community_uid")


def _client():
    return st.session_state.get("eco_community_supabase")


def _run(query):
    try:
        return query.execute().data or []
    except Exception as exc:
        st.error(f"Community Hub error: {exc}")
        return []


def _one(query):
    rows = _run(query)
    return rows[0] if rows else None


def _profile(user_id):
    if not user_id:
        return None
    return _one(
        _client().table("profiles")
        .select("*")
        .eq("id", user_id)
        .limit(1)
    )


def _name(profile):
    if not profile:
        return "EcoLoop member"
    return (
        profile.get("display_name")
        or profile.get("username")
        or "EcoLoop member"
    )


def _avatar(profile):
    if not profile:
        return "🌱"
    return profile.get("avatar_url") or "🌱"


def _time_label(value):
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%H:%M")
    except Exception:
        return ""


def _safe(value):
    return html.escape(str(value or ""))


def _notify_error(label, exc):
    st.error(f"{label}: {exc}")


# ------------------------------------------------------------
# PRESENCE
# ------------------------------------------------------------

def _update_presence(online=True):
    uid = _uid()
    if not uid:
        return

    try:
        _client().table("profiles").update({
            "is_online": online,
            "last_seen": _now()
        }).eq("id", uid).execute()
    except Exception:
        pass


# ------------------------------------------------------------
# STORAGE
# ------------------------------------------------------------

def _upload_file(uploaded_file, folder):
    if not uploaded_file:
        return None

    uid = _uid()
    extension = uploaded_file.name.rsplit(".", 1)[-1].lower()
    safe_extension = "".join(
        char for char in extension if char.isalnum()
    )[:8] or "bin"

    path = f"{folder}/{uid}/{uuid.uuid4().hex}.{safe_extension}"

    try:
        _client().storage.from_(BUCKET).upload(
            path,
            uploaded_file.getvalue(),
            {
                "content-type": uploaded_file.type
                or "application/octet-stream",
                "upsert": "false"
            }
        )

        result = _client().storage.from_(BUCKET).create_signed_url(
            path, 60 * 60 * 24 * 7
        )

        if isinstance(result, dict):
            return (
                result.get("signedURL")
                or result.get("signedUrl")
                or result.get("signed_url")
            )

        return None

    except Exception as exc:
        _notify_error("File upload failed", exc)
        return None


# ------------------------------------------------------------
# PROFILE LOOKUPS
# ------------------------------------------------------------

def _profiles_by_ids(user_ids):
    ids = list(set(uid for uid in user_ids if uid))
    if not ids:
        return {}

    rows = _run(
        _client().table("profiles")
        .select("*")
        .in_("id", ids)
    )

    return {row["id"]: row for row in rows if row.get("id")}


# ------------------------------------------------------------
# DIRECT MESSAGES
# ------------------------------------------------------------

def _get_or_create_chat(other_user_id):
    uid = _uid()

    existing = _one(
        _client().table("direct_chats")
        .select("*")
        .or_(
            f"and(user1.eq.{uid},user2.eq.{other_user_id}),"
            f"and(user1.eq.{other_user_id},user2.eq.{uid})"
        )
        .limit(1)
    )

    if existing:
        return existing

    try:
        result = _client().table("direct_chats").insert({
            "user1": uid,
            "user2": other_user_id,
            "created_at": _now()
        }).execute()

        return result.data[0] if result.data else None

    except Exception as exc:
        _notify_error("Could not start conversation", exc)
        return None


def _direct_chats():
    uid = _uid()

    rows = _run(
        _client().table("direct_chats")
        .select("*")
        .or_(f"user1.eq.{uid},user2.eq.{uid}")
        .order("created_at", desc=True)
    )

    other_ids = []
    for row in rows:
        other_ids.append(
            row.get("user2") if row.get("user1") == uid
            else row.get("user1")
        )

    profiles = _profiles_by_ids(other_ids)

    results = []
    for row in rows:
        other_id = (
            row.get("user2") if row.get("user1") == uid
            else row.get("user1")
        )
        results.append({
            "chat": row,
            "other_id": other_id,
            "profile": profiles.get(other_id)
        })

    return results


def _direct_messages(chat_id):
    return _run(
        _client().table("messages")
        .select("*")
        .eq("chat_id", chat_id)
        .is_("deleted_at", "null")
        .order("created_at")
    )


def _send_direct_message(chat_id, message, attachment=None):
    uid = _uid()

    payload = {
        "chat_id": chat_id,
        "sender_id": uid,
        "message_text": message.strip(),
        "status": "sent",
        "created_at": _now()
    }

    if attachment:
        payload.update(attachment)

    try:
        _client().table("messages").insert(payload).execute()
        st.rerun()
    except Exception as exc:
        _notify_error("Message could not be sent", exc)


def _mark_direct_read(chat_id):
    try:
        _client().table("messages").update({
            "status": "read",
            "read_at": _now()
        }).eq("chat_id", chat_id).neq(
            "sender_id", _uid()
        ).neq("status", "read").execute()
    except Exception:
        pass


# ------------------------------------------------------------
# GROUP CHAT
# ------------------------------------------------------------

def _my_groups():
    uid = _uid()

    memberships = _run(
        _client().table("group_members")
        .select("group_id,role,joined_at")
        .eq("user_id", uid)
    )

    group_ids = [m["group_id"] for m in memberships if m.get("group_id")]
    if not group_ids:
        return []

    groups = _run(
        _client().table("groups")
        .select("*")
        .in_("id", group_ids)
        .order("created_at", desc=True)
    )

    return groups


def _create_group(name, description):
    try:
        result = _client().table("groups").insert({
            "name": name.strip(),
            "description": description.strip(),
            "created_by": _uid(),
            "invite_code": uuid.uuid4().hex[:8].upper(),
            "created_at": _now()
        }).execute()

        if not result.data:
            st.error("The room could not be created.")
            return

        group_id = result.data[0]["id"]

        _client().table("group_members").insert({
            "group_id": group_id,
            "user_id": _uid(),
            "role": "admin",
            "joined_at": _now()
        }).execute()

        st.success("Your chat room has been created.")
        st.rerun()

    except Exception as exc:
        _notify_error("Could not create room", exc)


def _join_group(invite_code):
    code = invite_code.strip().upper()
    if not code:
        return

    group = _one(
        _client().table("groups")
        .select("*")
        .eq("invite_code", code)
        .limit(1)
    )

    if not group:
        st.warning("No room was found with that invite code.")
        return

    already_member = _one(
        _client().table("group_members")
        .select("id")
        .eq("group_id", group["id"])
        .eq("user_id", _uid())
        .limit(1)
    )

    if already_member:
        st.info("You are already a member of this room.")
        return

    try:
        _client().table("group_members").insert({
            "group_id": group["id"],
            "user_id": _uid(),
            "role": "member",
            "joined_at": _now()
        }).execute()

        st.success("You joined the room.")
        st.rerun()

    except Exception as exc:
        _notify_error("Could not join room", exc)


def _group_messages(group_id):
    return _run(
        _client().table("group_messages")
        .select("*")
        .eq("group_id", group_id)
        .is_("deleted_at", "null")
        .order("created_at")
    )


def _send_group_message(group_id, message, attachment=None):
    payload = {
        "group_id": group_id,
        "sender_id": _uid(),
        "message_text": message.strip(),
        "status": "sent",
        "created_at": _now()
    }

    if attachment:
        payload.update(attachment)

    try:
        _client().table("group_messages").insert(payload).execute()
        st.rerun()
    except Exception as exc:
        _notify_error("Group message could not be sent", exc)


def _mark_group_read(group_id):
    try:
        _client().table("group_messages").update({
            "status": "read",
            "read_at": _now()
        }).eq("group_id", group_id).neq(
            "sender_id", _uid()
        ).neq("status", "read").execute()
    except Exception:
        pass


def _group_members(group_id):
    rows = _run(
        _client().table("group_members")
        .select("user_id,role,joined_at")
        .eq("group_id", group_id)
    )

    profiles = _profiles_by_ids([r.get("user_id") for r in rows])

    return [
        {
            **row,
            "profile": profiles.get(row.get("user_id"))
        }
        for row in rows
    ]


# ------------------------------------------------------------
# MESSAGE REACTIONS
# ------------------------------------------------------------

def _get_reactions(message_id, is_group):
    return _run(
        _client().table("message_reactions")
        .select("*")
        .eq("message_id", message_id)
        .eq("is_group", is_group)
    )


def _toggle_reaction(message_id, emoji, is_group):
    uid = _uid()

    existing = _one(
        _client().table("message_reactions")
        .select("*")
        .eq("message_id", message_id)
        .eq("user_id", uid)
        .eq("is_group", is_group)
        .limit(1)
    )

    try:
        if existing and existing.get("emoji") == emoji:
            _client().table("message_reactions").delete().eq(
                "id", existing["id"]
            ).execute()
        elif existing:
            _client().table("message_reactions").update({
                "emoji": emoji
            }).eq("id", existing["id"]).execute()
        else:
            _client().table("message_reactions").insert({
                "message_id": message_id,
                "user_id": uid,
                "emoji": emoji,
                "is_group": is_group
            }).execute()

        st.rerun()

    except Exception as exc:
        _notify_error("Reaction could not be saved", exc)


# ------------------------------------------------------------
# STORIES / UPDATES
# ------------------------------------------------------------

def _recent_stories():
    cutoff = (
        datetime.now(timezone.utc) - timedelta(hours=24)
    ).isoformat()

    rows = _run(
        _client().table("stories")
        .select("*")
        .gte("created_at", cutoff)
        .order("created_at", desc=True)
    )

    profiles = _profiles_by_ids([r.get("user_id") for r in rows])

    return [
        {
            **row,
            "profile": profiles.get(row.get("user_id"))
        }
        for row in rows
    ]


def _post_story(uploaded_file, caption):
    if not uploaded_file:
        st.warning("Choose a photo or video first.")
        return

    media_url = _upload_file(uploaded_file, "stories")
    if not media_url:
        return

    try:
        _client().table("stories").insert({
            "user_id": _uid(),
            "media_path": media_url,
            "caption": caption.strip(),
            "created_at": _now()
        }).execute()

        st.success("Your update has been posted.")
        st.rerun()

    except Exception as exc:
        _notify_error("Could not post update", exc)


# ------------------------------------------------------------
# DISCOVER
# ------------------------------------------------------------

def _search_profiles(search_text):
    term = search_text.strip()
    if not term:
        return []

    try:
        return _run(
            _client().table("profiles")
            .select("*")
            .or_(
                f"username.ilike.%{term}%,"
                f"display_name.ilike.%{term}%"
            )
            .neq("id", _uid())
            .limit(30)
        )
    except Exception as exc:
        _notify_error("Profile search failed", exc)
        return []


# ------------------------------------------------------------
# PROFILE UPDATE
# ------------------------------------------------------------

def _save_profile(display_name, username, bio, location,
                  interests, instagram, tiktok, avatar_url=None):

    payload = {
        "display_name": display_name.strip(),
        "username": username.strip().lstrip("@"),
        "bio": bio.strip(),
        "location": location.strip(),
        "interests": interests.strip(),
        "instagram": instagram.strip(),
        "tiktok": tiktok.strip()
    }

    if avatar_url:
        payload["avatar_url"] = avatar_url

    try:
        _client().table("profiles").update(payload).eq(
            "id", _uid()
        ).execute()

        st.success("Profile updated.")
        st.rerun()

    except Exception as exc:
        _notify_error("Profile could not be updated", exc)


# ------------------------------------------------------------
# MESSAGE DISPLAY
# ------------------------------------------------------------

def _render_messages(messages, profiles, is_group):
    uid = _uid()

    st.markdown("""
    <style>
    .eco-wa-message {
        padding: 10px 13px;
        border-radius: 14px;
        margin: 7px 0;
        max-width: 82%;
        overflow-wrap: anywhere;
        font-size: 14px;
    }
    .eco-wa-mine {
        background: #d9fdd3;
        color: #173b20;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }
    .eco-wa-theirs {
        background: #ffffff;
        color: #202020;
        margin-right: auto;
        border-bottom-left-radius: 4px;
    }
    .eco-wa-meta {
        font-size: 10px;
        opacity: .65;
        text-align: right;
        margin-top: 5px;
    }
    .eco-wa-sender {
        font-size: 11px;
        font-weight: 700;
        margin-bottom: 4px;
        color: #287b45;
    }
    </style>
    """, unsafe_allow_html=True)

    for message in messages:
        sender_id = message.get("sender_id")
        mine = sender_id == uid
        sender_profile = profiles.get(sender_id, {})
        bubble_class = "eco-wa-mine" if mine else "eco-wa-theirs"

        sender_label = ""
        if is_group and not mine:
            sender_label = (
                f'<div class="eco-wa-sender">'
                f'{_safe(_name(sender_profile))}</div>'
            )

        message_text = _safe(message.get("message_text"))
        timestamp = _time_label(message.get("created_at"))

        attachment_html = ""
        attachment_path = message.get("attachment_path")

        if attachment_path:
            attachment_html = (
                f'<div style="margin-top:6px">'
                f'<a href="{_safe(attachment_path)}" target="_blank">'
                f'Open attachment</a></div>'
            )

        status = ""
        if mine:
            status = " ✓✓" if message.get("status") == "read" else " ✓"

        st.markdown(
            f'<div class="eco-wa-message {bubble_class}">'
            f'{sender_label}'
            f'<div>{message_text}</div>'
            f'{attachment_html}'
            f'<div class="eco-wa-meta">{timestamp}{status}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        message_id = message.get("id")
        if message_id:
            reactions = _get_reactions(message_id, is_group)

            if reactions:
                counts = {}
                for reaction in reactions:
                    emoji = reaction.get("emoji", "👍")
                    counts[emoji] = counts.get(emoji, 0) + 1

                st.caption(
                    "  ".join(
                        f"{emoji} {count}"
                        for emoji, count in counts.items()
                    )
                )

            reaction_cols = st.columns(5)
            for col, emoji in zip(
                reaction_cols, ["❤️", "👍", "😂", "😮", "👏"]
            ):
                with col:
                    if col.button(
                        emoji,
                        key=f"react_{is_group}_{message_id}_{emoji}"
                    ):
                        _toggle_reaction(message_id, emoji, is_group)


def _attachment_payload(uploaded_file, folder="chat"):
    if not uploaded_file:
        return None

    url = _upload_file(uploaded_file, folder)
    if not url:
        return None

    return {
        "attachment_path": url,
        "attachment_type": uploaded_file.type or "file",
        "attachment_name": uploaded_file.name
    }


# ------------------------------------------------------------
# CHAT COMPOSER
# ------------------------------------------------------------

def _composer(chat_id=None, group_id=None):
    prefix = "group" if group_id else "direct"
    target = group_id or chat_id

    with st.form(f"{prefix}_composer_{target}", clear_on_submit=True):
        message = st.text_input(
            "Message",
            placeholder="Type a message...",
            label_visibility="collapsed"
        )

        attachment = st.file_uploader(
            "Attach a file",
            key=f"{prefix}_attachment_{target}",
            label_visibility="collapsed"
        )

        submitted = st.form_submit_button(
            "Send",
            use_container_width=True
        )

    if submitted:
        if not message.strip() and not attachment:
            st.info("Write a message or attach a file.")
            return

        attachment_data = (
            _attachment_payload(attachment)
            if attachment else None
        )

        if attachment and not attachment_data:
            return

        if group_id:
            _send_group_message(
                group_id, message, attachment_data
            )
        else:
            _send_direct_message(
                chat_id, message, attachment_data
            )


# ------------------------------------------------------------
# SECTION: CHATS
# ------------------------------------------------------------

def _chats_page():
    st.subheader("💬 Private Chats")

    if st.session_state.get("eco_open_chat"):
        chat_id = st.session_state.eco_open_chat
        other_id = st.session_state.get("eco_open_chat_user")
        other_profile = _profile(other_id)

        left, right = st.columns([1, 5])
        with left:
            if st.button("← Back"):
                st.session_state.eco_open_chat = None
                st.session_state.eco_open_chat_user = None
                st.rerun()

        with right:
            st.markdown(f"### {_name(other_profile)}")

        if other_profile and other_profile.get("is_online"):
            st.caption("🟢 Online")
        else:
            st.caption("Last seen recently")

        messages = _direct_messages(chat_id)
        _mark_direct_read(chat_id)

        profiles = _profiles_by_ids(
            [m.get("sender_id") for m in messages]
        )
        _render_messages(messages, profiles, False)
        _composer(chat_id=chat_id)
        return

    search = st.text_input(
        "Search conversations",
        placeholder="Search your chats..."
    ).lower()

    conversations = _direct_chats()

    if not conversations:
        st.info("Your private conversations will appear here.")
        st.caption("Visit Discover to find and message other members.")
        return

    for item in conversations:
        profile = item["profile"]
        if not profile:
            continue

        display = _name(profile)
        username = profile.get("username", "")

        if search and search not in display.lower() and search not in username.lower():
            continue

        chat = item["chat"]
        chat_id = chat["id"]

        last_message = _one(
            _client().table("messages")
            .select("message_text,created_at")
            .eq("chat_id", chat_id)
            .is_("deleted_at", "null")
            .order("created_at", desc=True)
            .limit(1)
        )

        col1, col2 = st.columns([1, 5])

        with col1:
            st.markdown(f"## {_safe(_avatar(profile))}")

        with col2:
            label = display
            if profile.get("is_online"):
                label += "  🟢"

            if st.button(
                label,
                key=f"open_direct_{chat_id}",
                use_container_width=True
            ):
                st.session_state.eco_open_chat = chat_id
                st.session_state.eco_open_chat_user = item["other_id"]
                st.rerun()

            if last_message:
                st.caption(
                    (last_message.get("message_text") or "Attachment")[:75]
                )
            else:
                st.caption("Start a conversation")


# ------------------------------------------------------------
# SECTION: CHAT ROOMS
# ------------------------------------------------------------

def _rooms_page():
    st.subheader("👥 Chat Rooms")

    with st.expander("＋ Create a chat room"):
        room_name = st.text_input("Room name", key="eco_new_room_name")
        description = st.text_area(
            "Description", key="eco_new_room_description"
        )

        if st.button("Create room"):
            if room_name.strip():
                _create_group(room_name, description)
            else:
                st.warning("Enter a room name.")

    with st.expander("Join with an invite code"):
        invite_code = st.text_input(
            "Invite code", key="eco_room_invite"
        )
        if st.button("Join room"):
            _join_group(invite_code)

    if st.session_state.get("eco_open_group"):
        group_id = st.session_state.eco_open_group
        group = _one(
            _client().table("groups")
            .select("*")
            .eq("id", group_id)
            .limit(1)
        )

        if not group:
            st.warning("This room is no longer available.")
            st.session_state.eco_open_group = None
            return

        if st.button("← Back to rooms"):
            st.session_state.eco_open_group = None
            st.rerun()

        st.markdown(f"### {group.get('name', 'Chat Room')}")
        st.caption(group.get("description") or "Community conversation")

        with st.expander("Room details and members"):
            st.write("Invite code:", group.get("invite_code", "Unavailable"))

            for member in _group_members(group_id):
                profile = member.get("profile")
                st.write(
                    f"{_avatar(profile)} {_name(profile)} "
                    f"— {member.get('role', 'member')}"
                )

        messages = _group_messages(group_id)
        _mark_group_read(group_id)

        profiles = _profiles_by_ids(
            [m.get("sender_id") for m in messages]
        )

        _render_messages(messages, profiles, True)
        _composer(group_id=group_id)
        return

    groups = _my_groups()

    if not groups:
        st.info("You haven't joined any chat rooms yet.")
        return

    for group in groups:
        col1, col2 = st.columns([1, 5])

        with col1:
            st.markdown("## 👥")

        with col2:
            if st.button(
                group.get("name", "Chat Room"),
                key=f"open_group_{group['id']}",
                use_container_width=True
            ):
                st.session_state.eco_open_group = group["id"]
                st.rerun()

            st.caption(group.get("description") or "Community room")


# ------------------------------------------------------------
# SECTION: UPDATES
# ------------------------------------------------------------

def _updates_page():
    st.subheader("🟢 Updates")

    with st.expander("＋ Share an update", expanded=False):
        story_file = st.file_uploader(
            "Choose a photo or video",
            type=["png", "jpg", "jpeg", "webp", "mp4", "mov"],
            key="eco_story_upload"
        )

        caption = st.text_area(
            "Write a caption",
            key="eco_story_caption"
        )

        if st.button("Post update"):
            _post_story(story_file, caption)

    stories = _recent_stories()

    if not stories:
        st.info("No updates have been shared in the last 24 hours.")
        return

    st.caption("Updates disappear from this feed after 24 hours.")

    for story in stories:
        profile = story.get("profile")
        created = _time_label(story.get("created_at"))

        st.markdown(
            f"**{_safe(_avatar(profile))} "
            f"{_safe(_name(profile))}**  ·  {created}"
        )

        media = story.get("media_path")
        if media:
            media_lower = media.lower().split("?")[0]

            if media_lower.endswith((".mp4", ".mov", ".webm")):
                st.video(media)
            else:
                st.image(media, use_container_width=True)

        if story.get("caption"):
            st.write(story["caption"])

        st.divider()


# ------------------------------------------------------------
# SECTION: DISCOVER
# ------------------------------------------------------------

def _discover_page():
    st.subheader("🔎 Discover Members")

    search = st.text_input(
        "Find people",
        placeholder="Search by name or username..."
    )

    if not search.strip():
        st.info("Search for a member by name or username.")
        return

    results = _search_profiles(search)

    if not results:
        st.info("No matching members found.")
        return

    for profile in results:
        with st.container(border=True):
            left, right = st.columns([1, 4])

            with left:
                st.markdown(f"## {_safe(_avatar(profile))}")

            with right:
                st.markdown(f"**{_safe(_name(profile))}**")
                st.caption(
                    f"@{profile.get('username', '')}"
                )

                if profile.get("location"):
                    st.caption(profile["location"])

                if profile.get("bio"):
                    st.write(profile["bio"])

                if st.button(
                    "Message",
                    key=f"discover_message_{profile['id']}"
                ):
                    chat = _get_or_create_chat(profile["id"])

                    if chat:
                        st.session_state.eco_open_chat = chat["id"]
                        st.session_state.eco_open_chat_user = profile["id"]
                        st.session_state.eco_section = "Chats"
                        st.rerun()


# ------------------------------------------------------------
# SECTION: PROFILE
# ------------------------------------------------------------

def _profile_page():
    st.subheader("👤 My Profile")

    profile = _profile(_uid()) or {}

    st.markdown(f"## {_safe(_avatar(profile))}")
    st.markdown(f"### {_safe(_name(profile))}")
    st.caption(f"@{profile.get('username', '')}")

    with st.expander("Edit my profile", expanded=False):
        display_name = st.text_input(
            "Display name",
            value=profile.get("display_name") or ""
        )

        username = st.text_input(
            "Username",
            value=profile.get("username") or ""
        )

        bio = st.text_area(
            "Bio",
            value=profile.get("bio") or ""
        )

        location = st.text_input(
            "Location",
            value=profile.get("location") or ""
        )

        interests = st.text_input(
            "Interests",
            value=profile.get("interests") or ""
        )

        instagram = st.text_input(
            "Instagram",
            value=profile.get("instagram") or ""
        )

        tiktok = st.text_input(
            "TikTok",
            value=profile.get("tiktok") or ""
        )

        avatar_file = st.file_uploader(
            "Upload profile picture",
            type=["png", "jpg", "jpeg", "webp"],
            key="eco_profile_avatar"
        )

        if st.button("Save profile"):
            avatar_url = None

            if avatar_file:
                avatar_url = _upload_file(avatar_file, "avatars")
                if not avatar_url:
                    return

            _save_profile(
                display_name,
                username,
                bio,
                location,
                interests,
                instagram,
                tiktok,
                avatar_url
            )

    if profile.get("bio"):
        st.write(profile["bio"])

    if profile.get("location"):
        st.caption(f"📍 {profile['location']}")

    if profile.get("interests"):
        st.write("**Interests:**", profile["interests"])

    if profile.get("instagram"):
        st.write("Instagram:", profile["instagram"])

    if profile.get("tiktok"):
        st.write("TikTok:", profile["tiktok"])


# ============================================================
# MAIN RENDER FUNCTION
# ============================================================

def render_community_groups_page(supabase=None, user_id=None):
    """
    Call this function from the main EcoLoop app.

    Example:
        render_community_groups_page(supabase, user_id)

    The module does not create a second login, configure the
    Streamlit page, or run automatically when imported.
    """

    if supabase is None:
        st.error("Community Hub could not access EcoLoop's database connection.")
        return

    if not user_id:
        user_id = (
            st.session_state.get("user_id")
            or st.session_state.get("uid")
        )

    if not user_id:
        st.warning("Please sign in to EcoLoop Node to use Community Hub.")
        return

    st.session_state.eco_community_supabase = supabase
    st.session_state.eco_community_uid = str(user_id)

    _update_presence(True)

    st.markdown("""
    <style>
    .eco-community-heading {
        font-size: 27px;
        font-weight: 800;
        margin-bottom: 2px;
    }
    .eco-community-subtitle {
        opacity: .7;
        font-size: 13px;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="eco-community-heading">♻️ Community Hub</div>'
        '<div class="eco-community-subtitle">'
        'Connect, communicate and grow together.'
        '</div>',
        unsafe_allow_html=True
    )

    if "eco_section" not in st.session_state:
        st.session_state.eco_section = "Chats"

    # Horizontal navigation
    nav_cols = st.columns(5)

    for col, section in zip(nav_cols, SECTIONS):
        with col:
            selected = st.session_state.eco_section == section

            if st.button(
                section,
                key=f"eco_nav_{section}",
                type="primary" if selected else "secondary",
                use_container_width=True
            ):
                st.session_state.eco_section = section
                st.rerun()

    st.divider()

    section = st.session_state.eco_section

    if section == "Chats":
        _chats_page()

    elif section == "Chat Rooms":
        _rooms_page()

    elif section == "Updates":
        _updates_page()

    elif section == "Discover":
        _discover_page()

    elif section == "Profile":
        _profile_page()

    st.divider()

    st.caption(
        "Powered by Next Gen Impact Hub (NGIH) · EcoLoop Node"
    )
