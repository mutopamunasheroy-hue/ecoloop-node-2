# ============================================================
# ECOLOOP NODE — COMMUNITY HUB
# WhatsApp-inspired Chats | Chat Rooms | Updates
# Powered by Next Gen Impact Hub (NGIH)
# ============================================================

import streamlit as st
import uuid
import mimetypes
from datetime import datetime, timedelta, timezone
from urllib.parse import quote


BUCKET = "community-media"
IMAGE_LIMIT = 8 * 1024 * 1024
VIDEO_LIMIT = 35 * 1024 * 1024


# ============================================================
# GENERAL HELPERS
# ============================================================

def eco_now():
    return datetime.now(timezone.utc).isoformat()


def eco_safe(value, default=""):
    return value if value is not None else default


def eco_rows(response):
    try:
        return response.data or []
    except Exception:
        return []


def eco_select(table, filters=None, columns="*",
               order=None, limit=None):
    try:
        query = st.session_state.eco_supabase.table(
            table
        ).select(columns)

        for method, column, value in filters or []:
            query = getattr(query, method)(column, value)

        if order:
            query = query.order(
                order[0],
                desc=order[1]
            )

        if limit:
            query = query.limit(limit)

        return eco_rows(query.execute())

    except Exception:
        return []


def eco_insert(table, data):
    try:
        return st.session_state.eco_supabase.table(
            table
        ).insert(data).execute()
    except Exception as e:
        st.error(f"Could not save information: {e}")
        return None


def eco_update(table, data, filters):
    try:
        query = st.session_state.eco_supabase.table(
            table
        ).update(data)

        for column, value in filters:
            query = query.eq(column, value)

        return query.execute()

    except Exception as e:
        st.error(f"Could not update: {e}")
        return None


def eco_delete(table, filters):
    try:
        query = st.session_state.eco_supabase.table(
            table
        ).delete()

        for column, value in filters:
            query = query.eq(column, value)

        return query.execute()

    except Exception as e:
        st.error(f"Could not delete: {e}")
        return None


def eco_upload(file, folder="uploads"):
    if not file:
        return None

    try:
        extension = file.name.split(".")[-1]
        filename = (
            f"{folder}/{uuid.uuid4().hex}.{extension}"
        )

        st.session_state.eco_supabase.storage.from_(
            BUCKET
        ).upload(
            filename,
            file.getvalue(),
            {
                "content-type": file.type,
                "upsert": "false"
            }
        )

        result = st.session_state.eco_supabase.storage.from_(
            BUCKET
        ).get_public_url(filename)

        return result

    except Exception as e:
        st.error(f"Upload failed: {e}")
        return None


def eco_profile(user_id):
    rows = eco_select(
        "member_profiles",
        [("eq", "user_id", user_id)],
        limit=1
    )
    return rows[0] if rows else {}


def eco_avatar(profile, size=48):
    profile = profile or {}
    url = profile.get("avatar_url")
    name = profile.get("display_name") or "Member"

    if url:
        st.markdown(
            f"""
            <img src="{url}"
            style="
                width:{size}px;
                height:{size}px;
                border-radius:50%;
                object-fit:cover;
                border:2px solid #25D366;
            ">
            """,
            unsafe_allow_html=True
        )
    else:
        initials = "".join(
            word[0] for word in name.split()[:2]
        ).upper()

        st.markdown(
            f"""
            <div style="
                width:{size}px;
                height:{size}px;
                border-radius:50%;
                background:#128C7E;
                color:white;
                display:flex;
                align-items:center;
                justify-content:center;
                font-weight:bold;
                font-size:18px;
            ">{initials}</div>
            """,
            unsafe_allow_html=True
        )


def eco_profile_name(profile):
    return (
        profile.get("display_name")
        or profile.get("username")
        or "EcoLoop Member"
    )


# ============================================================
# DESIGN
# ============================================================

def eco_inject_styles():
    st.markdown(
        """
        <style>
        .eco-title {
            font-size:27px;
            font-weight:800;
            color:#128C7E;
            margin-bottom:3px;
        }

        .eco-subtitle {
            color:var(--text-color);
            opacity:.65;
            font-size:13px;
        }

        .eco-card {
            border:1px solid rgba(128,128,128,.2);
            border-radius:17px;
            padding:14px;
            margin-bottom:10px;
            background:var(--secondary-background-color);
        }

        .eco-chat-header {
            padding:13px;
            border-radius:15px;
            background:var(--secondary-background-color);
            margin-bottom:12px;
        }

        .eco-message {
            padding:11px 14px;
            border-radius:17px;
            margin:5px 0;
            max-width:82%;
            overflow-wrap:anywhere;
        }

        .eco-outgoing {
            background:#DCF8C6;
            color:#18351B;
            margin-left:auto;
            border-bottom-right-radius:4px;
        }

        .eco-incoming {
            background:var(--secondary-background-color);
            margin-right:auto;
            border-bottom-left-radius:4px;
        }

        .eco-message-time {
            font-size:10px;
            opacity:.6;
            text-align:right;
            margin-top:5px;
        }

        .eco-floating {
            position:fixed;
            bottom:85px;
            right:22px;
            z-index:999;
            background:#128C7E;
            color:white;
            border-radius:50%;
            width:58px;
            height:58px;
            display:flex;
            align-items:center;
            justify-content:center;
            font-size:30px;
            box-shadow:0 4px 15px rgba(0,0,0,.25);
        }

        div[data-testid="stChatInput"] {
            border-radius:25px;
        }

        button[kind="primary"] {
            background:#128C7E;
            border-color:#128C7E;
        }

        </style>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# PROFILE VIEW
# ============================================================

def render_member_profile(profile):
    if not profile:
        st.info("This profile is not available.")
        return

    name = eco_profile_name(profile)

    st.markdown("### Member profile")

    if profile.get("avatar_url"):
        st.image(
            profile["avatar_url"],
            width=125
        )

    st.subheader(name)

    if profile.get("username"):
        st.caption(f"@{profile['username']}")

    if profile.get("bio"):
        st.write(profile["bio"])

    if profile.get("location"):
        st.caption(f"📍 {profile['location']}")

    if profile.get("interests"):
        st.write("**Interests**")
        st.write(profile["interests"])

    if profile.get("country_of_origin"):
        st.caption(
            f"Country: {profile['country_of_origin']}"
        )

    for field, label in [
        ("instagram", "Instagram"),
        ("facebook", "Facebook"),
        ("linkedin", "LinkedIn"),
        ("website", "Website")
    ]:
        if profile.get(field):
            st.write(f"**{label}:** {profile[field]}")


# ============================================================
# PRIVATE CONVERSATIONS
# ============================================================

def eco_get_conversation(user_id, other_id):
    first, second = sorted([user_id, other_id])

    rows = eco_select(
        "direct_conversations",
        [
            ("eq", "user_one_id", first),
            ("eq", "user_two_id", second)
        ],
        limit=1
    )

    if rows:
        return rows[0]

    result = eco_insert(
        "direct_conversations",
        {
            "user_one_id": first,
            "user_two_id": second
        }
    )

    if result:
        try:
            return result.data[0]
        except Exception:
            pass

    rows = eco_select(
        "direct_conversations",
        [
            ("eq", "user_one_id", first),
            ("eq", "user_two_id", second)
        ],
        limit=1
    )

    return rows[0] if rows else None


def eco_get_direct_messages(conversation_id):
    return eco_select(
        "direct_messages",
        [
            ("eq", "conversation_id", conversation_id)
        ],
        order=("created_at", False),
        limit=200
    )


def eco_send_direct_message(
    conversation_id,
    sender_id,
    message,
    attachment_path=None,
    attachment_name=None,
    attachment_type=None
):
    data = {
        "conversation_id": conversation_id,
        "sender_id": sender_id,
        "message_text": message,
        "attachment_path": attachment_path,
        "attachment_name": attachment_name,
        "attachment_type": attachment_type
    }

    return eco_insert("direct_messages", data)


def eco_render_direct_message(message, user_id):
    mine = message.get("sender_id") == user_id
    deleted = bool(message.get("deleted_at"))

    message_id = message.get("id")

    css = "eco-outgoing" if mine else "eco-incoming"

    content = (
        "This message was deleted."
        if deleted
        else message.get("message_text") or ""
    )

    st.markdown(
        f"""
        <div class="eco-message {css}">
            {content}
            <div class="eco-message-time">
                {message.get("created_at", "")[:16]}
                {" · Edited" if message.get("edited_at") else ""}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if mine and not deleted and message_id:
        with st.expander("Message options"):
            if st.button(
                "✏️ Edit message",
                key=f"edit_dm_{message_id}"
            ):
                st.session_state.editing_message = message_id

            if st.button(
                "🗑️ Delete message",
                key=f"delete_dm_{message_id}"
            ):
                eco_update(
                    "direct_messages",
                    {"deleted_at": eco_now()},
                    [
                        ("id", message_id),
                        ("sender_id", user_id)
                    ]
                )
                st.rerun()

            if st.session_state.get(
                "editing_message"
            ) == message_id:
                with st.form(
                    f"edit_dm_form_{message_id}"
                ):
                    revised = st.text_area(
                        "Edit your message",
                        value=message.get("message_text") or ""
                    )

                    save = st.form_submit_button(
                        "Save changes"
                    )

                    if save and revised.strip():
                        eco_update(
                            "direct_messages",
                            {
                                "message_text": revised.strip(),
                                "edited_at": eco_now()
                            },
                            [
                                ("id", message_id),
                                ("sender_id", user_id)
                            ]
                        )

                        st.session_state.editing_message = None
                        st.rerun()


def render_private_chat(
    supabase,
    user_id,
    other_id
):
    other = eco_profile(other_id)

    if not other:
        st.warning("Member profile could not be found.")
        return

    conversation = eco_get_conversation(
        user_id,
        other_id
    )

    if not conversation:
        st.error("Could not open this conversation.")
        return

    conversation_id = conversation["id"]

    with st.container():
        st.markdown(
            '<div class="eco-chat-header">',
            unsafe_allow_html=True
        )

        col1, col2 = st.columns([1, 4])

        with col1:
            if other.get("avatar_url"):
                st.image(
                    other["avatar_url"],
                    width=55
                )

        with col2:
            st.markdown(
                f"**{eco_profile_name(other)}**"
            )

            st.caption(
                f"@{other.get('username', 'member')}"
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )

        with st.expander("View profile"):
            render_member_profile(other)

    messages = eco_get_direct_messages(
        conversation_id
    )

    st.markdown("---")

    for message in messages:
        eco_render_direct_message(
            message,
            user_id
        )

    st.markdown("---")

    attachment = st.file_uploader(
        "📎 Attach a photo or file",
        key=f"dm_file_{conversation_id}"
    )

    audio = None

    if hasattr(st, "audio_input"):
        audio = st.audio_input(
            "🎙️ Record a voice message",
            key=f"dm_audio_{conversation_id}"
        )

    typed_message = st.chat_input(
        " ",
        key=f"dm_input_{conversation_id}"
    )

    if typed_message or attachment or audio:
        attachment_url = None
        attachment_name = None
        attachment_type = None

        upload_file = attachment or audio

        if upload_file:
            limit = (
                VIDEO_LIMIT
                if "video" in upload_file.type
                else IMAGE_LIMIT
            )

            if upload_file.size > limit:
                st.error("This file is too large.")
                return

            attachment_url = eco_upload(
                upload_file,
                "private-messages"
            )

            attachment_name = upload_file.name
            attachment_type = upload_file.type

        eco_send_direct_message(
            conversation_id,
            user_id,
            typed_message or "",
            attachment_url,
            attachment_name,
            attachment_type
        )

        st.rerun()


# ============================================================
# CHATS — PRIVATE INBOX AND PEOPLE SEARCH
# ============================================================

def render_people_search(user_id):
    st.markdown("### Find people")

    search = st.text_input(
        "Search by name or username",
        placeholder="Search EcoLoop members..."
    )

    if not search:
        st.caption(
            "Search for a member to start a private conversation."
        )
        return

    profiles = eco_select(
        "member_profiles",
        limit=300
    )

    matches = []

    for profile in profiles:
        if profile.get("user_id") == user_id:
            continue

        name = (
            profile.get("display_name") or ""
        ).lower()

        username = (
            profile.get("username") or ""
        ).lower()

        if (
            search.lower() in name
            or search.lower() in username
        ):
            matches.append(profile)

    for profile in matches:
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 4, 2])

            with c1:
                if profile.get("avatar_url"):
                    st.image(
                        profile["avatar_url"],
                        width=48
                    )
                else:
                    st.write("👤")

            with c2:
                st.write(
                    f"**{eco_profile_name(profile)}**"
                )
                st.caption(
                    f"@{profile.get('username', '')}"
                )

            with c3:
                if st.button(
                    "Message",
                    key=f"start_chat_{profile['user_id']}"
                ):
                    st.session_state.active_private_chat = (
                        profile["user_id"]
                    )
                    st.session_state.chat_screen = "conversation"
                    st.rerun()


def render_private_inbox(user_id):
    conversations = eco_select(
        "direct_conversations",
        [
            ("eq", "user_one_id", user_id)
        ],
        order=("created_at", True)
    )

    other_conversations = eco_select(
        "direct_conversations",
        [
            ("eq", "user_two_id", user_id)
        ],
        order=("created_at", True)
    )

    all_conversations = conversations + other_conversations

    seen = set()
    unique = []

    for conversation in all_conversations:
        cid = conversation.get("id")

        if cid and cid not in seen:
            seen.add(cid)
            unique.append(conversation)

    if not unique:
        st.info(
            "Your private conversations will appear here."
        )
        return

    for conversation in unique:
        other_id = (
            conversation["user_two_id"]
            if conversation["user_one_id"] == user_id
            else conversation["user_one_id"]
        )

        profile = eco_profile(other_id)

        if not profile:
            continue

        messages = eco_get_direct_messages(
            conversation["id"]
        )

        latest = messages[-1] if messages else {}

        preview = (
            "Message deleted"
            if latest.get("deleted_at")
            else latest.get("message_text")
            or "Start a conversation"
        )

        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 5, 1])

            with c1:
                if profile.get("avatar_url"):
                    st.image(
                        profile["avatar_url"],
                        width=52
                    )
                else:
                    st.write("👤")

            with c2:
                st.markdown(
                    f"**{eco_profile_name(profile)}**"
                )
                st.caption(preview[:65])

            with c3:
                if st.button(
                    "Open",
                    key=f"open_dm_{conversation['id']}"
                ):
                    st.session_state.active_private_chat = other_id
                    st.session_state.chat_screen = "conversation"
                    st.rerun()


def render_chats_section(user_id):
    if (
        st.session_state.get("chat_screen")
        == "conversation"
    ):
        if st.button("← Back to Chats"):
            st.session_state.chat_screen = "inbox"
            st.session_state.active_private_chat = None
            st.rerun()

        other_id = st.session_state.get(
            "active_private_chat"
        )

        if other_id:
            render_private_chat(
                st.session_state.eco_supabase,
                user_id,
                other_id
            )

        return

    st.markdown("### Private chats")

    render_private_inbox(user_id)


# ============================================================
# CHAT ROOMS
# ============================================================

def eco_get_room_membership(group_id, user_id):
    rows = eco_select(
        "group_memberships",
        [
            ("eq", "group_id", group_id),
            ("eq", "user_id", user_id)
        ],
        limit=1
    )

    return rows[0] if rows else None


def eco_get_room_messages(group_id):
    return eco_select(
        "group_messages",
        [
            ("eq", "group_id", group_id)
        ],
        order=("created_at", False),
        limit=200
    )


def eco_render_group_message(message, user_id):
    mine = message.get("sender_id") == user_id
    deleted = bool(message.get("deleted_at"))

    css = (
        "eco-outgoing"
        if mine
        else "eco-incoming"
    )

    profile = eco_profile(
        message.get("sender_id")
    )

    sender = eco_profile_name(profile)

    content = (
        "This message was deleted."
        if deleted
        else message.get("message_text") or ""
    )

    st.caption(sender)

    st.markdown(
        f"""
        <div class="eco-message {css}">
            {content}
            <div class="eco-message-time">
                {message.get("created_at", "")[:16]}
                {" · Edited" if message.get("edited_at") else ""}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    message_id = message.get("id")

    if mine and not deleted and message_id:
        with st.expander("Message options"):
            if st.button(
                "✏️ Edit",
                key=f"edit_group_{message_id}"
            ):
                st.session_state.editing_group_message = message_id

            if st.button(
                "🗑️ Delete",
                key=f"delete_group_{message_id}"
            ):
                eco_update(
                    "group_messages",
                    {"deleted_at": eco_now()},
                    [
                        ("id", message_id),
                        ("sender_id", user_id)
                    ]
                )
                st.rerun()

            if st.session_state.get(
                "editing_group_message"
            ) == message_id:
                with st.form(
                    f"edit_group_form_{message_id}"
                ):
                    revised = st.text_area(
                        "Edit message",
                        value=message.get("message_text") or ""
                    )

                    if st.form_submit_button("Save"):
                        eco_update(
                            "group_messages",
                            {
                                "message_text": revised.strip(),
                                "edited_at": eco_now()
                            },
                            [
                                ("id", message_id),
                                ("sender_id", user_id)
                            ]
                        )

                        st.session_state.editing_group_message = None
                        st.rerun()


def eco_send_group_message(
    group_id,
    sender_id,
    message
):
    return eco_insert(
        "group_messages",
        {
            "group_id": group_id,
            "sender_id": sender_id,
            "message_text": message
        }
    )


def render_room_chat(group, user_id):
    group_id = group["id"]

    st.markdown(
        f"### {group.get('name', 'Chat Room')}"
    )

    st.caption(
        group.get("description") or "EcoLoop community chatroom"
    )

    if st.button("← Back to Chat Rooms"):
        st.session_state.active_room = None
        st.rerun()

    messages = eco_get_room_messages(group_id)

    for message in messages:
        eco_render_group_message(
            message,
            user_id
        )

    st.markdown("---")

    typed = st.chat_input(
        " ",
        key=f"group_input_{group_id}"
    )

    if typed and typed.strip():
        eco_send_group_message(
            group_id,
            user_id,
            typed.strip()
        )
        st.rerun()


def render_chatrooms_page(user_id):
    active_room = st.session_state.get(
        "active_room"
    )

    if active_room:
        rooms = eco_select(
            "community_groups",
            [
                ("eq", "id", active_room)
            ],
            limit=1
        )

        if rooms:
            render_room_chat(
                rooms[0],
                user_id
            )
        else:
            st.error("Chat room not found.")

        return

    st.markdown("### Chat Rooms")

    st.caption(
        "Join communities and communicate with other members."
    )

    rooms = eco_select(
        "community_groups",
        order=("created_at", True),
        limit=200
    )

    memberships = eco_select(
        "group_memberships",
        [
            ("eq", "user_id", user_id)
        ]
    )

    membership_map = {
        m["group_id"]: m
        for m in memberships
    }

    st.markdown("#### Your chat rooms")

    joined = [
        room for room in rooms
        if (
            membership_map.get(room["id"])
            and membership_map[room["id"]].get("status")
            == "approved"
        )
    ]

    if not joined:
        st.info(
            "You haven't joined any chat rooms yet."
        )

    for room in joined:
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 4, 2])

            with c1:
                if room.get("image_url"):
                    st.image(
                        room["image_url"],
                        width=55
                    )
                else:
                    st.write("👥")

            with c2:
                st.write(f"**{room['name']}**")
                st.caption(
                    room.get("description") or ""
                )

            with c3:
                if st.button(
                    "Open",
                    key=f"room_open_{room['id']}"
                ):
                    st.session_state.active_room = room["id"]
                    st.rerun()

    st.markdown("---")
    st.markdown("#### Discover chat rooms")

    for room in rooms:
        if room in joined:
            continue

        membership = membership_map.get(
            room["id"]
        )

        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 4, 2])

            with c1:
                if room.get("image_url"):
                    st.image(
                        room["image_url"],
                        width=55
                    )
                else:
                    st.write("👥")

            with c2:
                st.write(f"**{room['name']}**")
                st.caption(
                    room.get("description") or ""
                )

            with c3:
                if membership and membership.get(
                    "status"
                ) == "pending":
                    st.caption("Request pending")

                elif st.button(
                    "Join",
                    key=f"join_room_{room['id']}"
                ):
                    eco_insert(
                        "group_memberships",
                        {
                            "group_id": room["id"],
                            "user_id": user_id,
                            "membership_role": "member",
                            "status": "pending"
                        }
                    )
                    st.success(
                        "Your request has been submitted."
                    )
                    st.rerun()


# ============================================================
# CREATE CHAT ROOM
# ============================================================

def render_create_room(user_id):
    with st.expander("＋ Create a chat room"):
        with st.form("create_eco_room"):
            name = st.text_input("Room name")
            description = st.text_area(
                "What is this room about?"
            )
            location = st.text_input(
                "Location (optional)"
            )

            image = st.file_uploader(
                "Room cover image",
                type=["png", "jpg", "jpeg"]
            )

            submitted = st.form_submit_button(
                "Create room"
            )

            if submitted:
                if not name.strip():
                    st.error("Enter a room name.")
                else:
                    image_url = (
                        eco_upload(image, "room-covers")
                        if image else None
                    )

                    result = eco_insert(
                        "community_groups",
                        {
                            "name": name.strip(),
                            "description": description,
                            "location": location,
                            "image_url": image_url,
                            "created_by": user_id
                        }
                    )

                    if result:
                        st.success("Chat room created.")
                        st.rerun()


# ============================================================
# UPDATES — 24-HOUR STORIES
# ============================================================

def render_stories_page(user_id):
    st.markdown("### Updates")

    st.caption(
        "Share moments with the EcoLoop community."
    )

    if st.button("＋ Add update"):
        st.session_state.adding_story = True

    if st.session_state.get("adding_story"):
        with st.form("eco_story_form"):
            caption = st.text_area(
                "Write a caption (optional)"
            )

            media = st.file_uploader(
                "Choose a photo or video",
                type=[
                    "png", "jpg", "jpeg",
                    "mp4", "mov", "webm"
                ]
            )

            submit = st.form_submit_button(
                "Share update"
            )

            if submit:
                if not media:
                    st.error("Choose a photo or video.")
                else:
                    limit = (
                        VIDEO_LIMIT
                        if media.type.startswith("video/")
                        else IMAGE_LIMIT
                    )

                    if media.size > limit:
                        st.error("File is too large.")
                    else:
                        url = eco_upload(
                            media,
                            "stories"
                        )

                        if url:
                            media_type = (
                                "video"
                                if media.type.startswith("video/")
                                else "image"
                            )

                            eco_insert(
                                "stories",
                                {
                                    "user_id": user_id,
                                    "caption": caption,
                                    "media_url": url,
                                    "media_type": media_type,
                                    "expires_at": (
                                        datetime.now(timezone.utc)
                                        + timedelta(hours=24)
                                    ).isoformat()
                                }
                            )

                            st.session_state.adding_story = False
                            st.success("Update shared.")
                            st.rerun()

    st.markdown("---")
    st.markdown("#### Recent updates")

    stories = eco_select(
        "stories",
        order=("created_at", True),
        limit=200
    )

    now = datetime.now(timezone.utc)

    active_stories = []

    for story in stories:
        try:
            expiry = datetime.fromisoformat(
                story["expires_at"].replace("Z", "+00:00")
            )

            if expiry > now:
                active_stories.append(story)

        except Exception:
            continue

    for story in active_stories:
        profile = eco_profile(
            story.get("user_id")
        )

        with st.container(border=True):
            c1, c2 = st.columns([1, 5])

            with c1:
                if profile.get("avatar_url"):
                    st.image(
                        profile["avatar_url"],
                        width=48
                    )
                else:
                    st.write("👤")

            with c2:
                st.write(
                    f"**{eco_profile_name(profile)}**"
                )
                st.caption(
                    story.get("created_at", "")[:16]
                )

            if story.get("media_type") == "video":
                st.video(story["media_url"])
            else:
                st.image(
                    story["media_url"],
                    use_container_width=True
                )

            if story.get("caption"):
                st.write(story["caption"])


# ============================================================
# FLOATING ADD MENU
# ============================================================

def render_floating_add():
    st.markdown(
        """
        <div class="eco-floating">+</div>
        """,
        unsafe_allow_html=True
    )

    with st.popover("＋", use_container_width=False):
        st.markdown("### Start something")

        if st.button(
            "👤 Find a person",
            use_container_width=True
        ):
            st.session_state.add_action = "people"

        if st.button(
            "👥 Find a chat room",
            use_container_width=True
        ):
            st.session_state.add_action = "rooms"

        if st.button(
            "＋ Create a chat room",
            use_container_width=True
        ):
            st.session_state.add_action = "create_room"


# ============================================================
# MAIN COMMUNITY HUB
# ============================================================

def render_community_groups_page(
    supabase,
    user_id
):
    st.session_state.eco_supabase = supabase

    defaults = {
        "eco_section": "Chats",
        "chat_screen": "inbox",
        "active_private_chat": None,
        "active_room": None,
        "adding_story": False,
        "add_action": None,
        "editing_message": None,
        "editing_group_message": None
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    eco_inject_styles()

    st.markdown(
        '<div class="eco-title">EcoLoop</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Connect. Communicate. Create impact."
    )

    sections = [
        "Chats",
        "Chat Rooms",
        "Updates"
    ]

    selected = st.radio(
        "Community navigation",
        sections,
        horizontal=True,
        key="eco_section",
        label_visibility="collapsed"
    )

    st.markdown("---")

    action = st.session_state.get(
        "add_action"
    )

    if action == "people":
        render_people_search(user_id)

        if st.button("← Back"):
            st.session_state.add_action = None
            st.rerun()

        return

    if action == "rooms":
        render_chatrooms_page(user_id)

        if st.button("← Back to add menu"):
            st.session_state.add_action = None
            st.rerun()

        return

    if action == "create_room":
        render_create_room(user_id)

        if st.button("← Back"):
            st.session_state.add_action = None
            st.rerun()

        return

    if selected == "Chats":
        render_chats_section(user_id)

    elif selected == "Chat Rooms":
        render_create_room(user_id)
        render_chatrooms_page(user_id)

    elif selected == "Updates":
        render_stories_page(user_id)

    render_floating_add()

    st.markdown("---")

    st.markdown(
        """
        <div style="
            text-align:center;
            opacity:.65;
            font-size:12px;
            padding:10px;
        ">
            Powered by <b>Next Gen Impact Hub (NGIH)</b><br>
            Designed by Munashe Roy Mutopa —
            Project Coordinator
        </div>
        """,
        unsafe_allow_html=True
            )
