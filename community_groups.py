# ============================================================
# ECOLOOP NODE — COMMUNITY HUB
# CHATS | CHAT ROOMS | UPDATES
# Powered by Next Gen Impact Hub (NGIH)
# ============================================================

import streamlit as st
import uuid
from datetime import datetime, timedelta, timezone


BUCKET = "community-media"
IMAGE_LIMIT = 8 * 1024 * 1024
VIDEO_LIMIT = 35 * 1024 * 1024


# ============================================================
# SESSION AND DATABASE HELPERS
# ============================================================

def eco_now():
    return datetime.now(timezone.utc).isoformat()


def eco_db(supabase):
    return supabase


def eco_select(
    supabase,
    table,
    filters=None,
    order=None,
    limit=None
):
    try:
        query = supabase.table(table).select("*")

        for method, column, value in filters or []:
            query = getattr(query, method)(column, value)

        if order:
            query = query.order(
                order[0],
                desc=order[1]
            )

        if limit:
            query = query.limit(limit)

        response = query.execute()
        return response.data or []

    except Exception:
        return []


def eco_insert(supabase, table, data):
    try:
        return supabase.table(table).insert(data).execute()
    except Exception as error:
        st.error(f"Could not save: {error}")
        return None


def eco_update(supabase, table, data, filters):
    try:
        query = supabase.table(table).update(data)

        for column, value in filters:
            query = query.eq(column, value)

        return query.execute()

    except Exception as error:
        st.error(f"Could not update: {error}")
        return None


def eco_upload(supabase, uploaded_file, folder):
    if not uploaded_file:
        return None

    try:
        extension = uploaded_file.name.split(".")[-1]
        filename = f"{folder}/{uuid.uuid4().hex}.{extension}"

        supabase.storage.from_(BUCKET).upload(
            filename,
            uploaded_file.getvalue(),
            {
                "content-type": uploaded_file.type,
                "upsert": "false"
            }
        )

        return supabase.storage.from_(
            BUCKET
        ).get_public_url(filename)

    except Exception as error:
        st.error(f"Upload failed: {error}")
        return None


# ============================================================
# PROFILE HELPERS
# ============================================================

def eco_profile(supabase, user_id):
    if not user_id:
        return {}

    profiles = eco_select(
        supabase,
        "member_profiles",
        [("eq", "user_id", user_id)],
        limit=1
    )

    return profiles[0] if profiles else {}


def eco_name(profile):
    return (
        profile.get("display_name")
        or profile.get("username")
        or "EcoLoop Member"
    )


def eco_avatar(profile, width=55):
    profile = profile or {}
    avatar = profile.get("avatar_url")

    if avatar:
        st.image(avatar, width=width)
    else:
        name = eco_name(profile)
        initials = "".join(
            word[0] for word in name.split()[:2]
        ).upper()

        st.markdown(f"**{initials or '👤'}**")


def eco_profile_details(profile):
    if not profile:
        st.info("Profile unavailable.")
        return

    eco_avatar(profile, 110)

    st.subheader(eco_name(profile))

    if profile.get("username"):
        st.caption(f"@{profile['username']}")

    if profile.get("bio"):
        st.write(profile["bio"])

    if profile.get("location"):
        st.write(f"📍 {profile['location']}")

    if profile.get("country_of_origin"):
        st.write(
            f"Country: {profile['country_of_origin']}"
        )

    if profile.get("interests"):
        st.write("**Interests**")
        st.write(profile["interests"])

    for field, label in [
        ("instagram", "Instagram"),
        ("facebook", "Facebook"),
        ("linkedin", "LinkedIn"),
        ("website", "Website")
    ]:
        if profile.get(field):
            st.write(f"**{label}:** {profile[field]}")


# ============================================================
# NAVIGATION STATE
# ============================================================

def eco_initialise_state():
    defaults = {
        "eco_section": "Chats",
        "eco_chat_view": "inbox",
        "eco_active_person": None,
        "eco_active_room": None,
        "eco_add_menu": False,
        "eco_add_destination": None,
        "eco_edit_message": None,
        "eco_edit_group_message": None,
        "eco_show_profile": False,
        "eco_story_form": False
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ============================================================
# PRIVATE CONVERSATIONS
# ============================================================

def eco_get_conversation(supabase, user_id, other_id):
    first, second = sorted([user_id, other_id])

    conversations = eco_select(
        supabase,
        "direct_conversations",
        [
            ("eq", "user_one_id", first),
            ("eq", "user_two_id", second)
        ],
        limit=1
    )

    if conversations:
        return conversations[0]

    result = eco_insert(
        supabase,
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

    conversations = eco_select(
        supabase,
        "direct_conversations",
        [
            ("eq", "user_one_id", first),
            ("eq", "user_two_id", second)
        ],
        limit=1
    )

    return conversations[0] if conversations else None


def eco_direct_messages(supabase, conversation_id):
    return eco_select(
        supabase,
        "direct_messages",
        [("eq", "conversation_id", conversation_id)],
        order=("created_at", False),
        limit=300
    )


def eco_send_direct(
    supabase,
    conversation_id,
    sender_id,
    message,
    attachment_url=None,
    attachment_name=None,
    attachment_type=None
):
    return eco_insert(
        supabase,
        "direct_messages",
        {
            "conversation_id": conversation_id,
            "sender_id": sender_id,
            "message_text": message,
            "attachment_path": attachment_url,
            "attachment_name": attachment_name,
            "attachment_type": attachment_type
        }
    )


def eco_delete_direct(supabase, message_id, user_id):
    return eco_update(
        supabase,
        "direct_messages",
        {"deleted_at": eco_now()},
        [
            ("id", message_id),
            ("sender_id", user_id)
        ]
    )


def eco_edit_direct(
    supabase,
    message_id,
    user_id,
    revised
):
    return eco_update(
        supabase,
        "direct_messages",
        {
            "message_text": revised,
            "edited_at": eco_now()
        },
        [
            ("id", message_id),
            ("sender_id", user_id)
        ]
    )


# ============================================================
# MESSAGE DISPLAY
# ============================================================

def eco_show_attachment(message):
    attachment = message.get("attachment_path")
    attachment_type = message.get("attachment_type") or ""

    if not attachment:
        return

    if attachment_type.startswith("image/"):
        st.image(attachment, use_container_width=True)

    elif attachment_type.startswith("video/"):
        st.video(attachment)

    elif attachment_type.startswith("audio/"):
        st.audio(attachment)

    else:
        st.link_button(
            message.get("attachment_name") or "Open attachment",
            attachment
        )


def eco_message_controls(
    supabase,
    message,
    user_id,
    group=False
):
    message_id = message.get("id")

    if not message_id:
        return

    if message.get("sender_id") != user_id:
        return

    if message.get("deleted_at"):
        return

    with st.popover("⋮"):
        if st.button(
            "Edit message",
            key=f"edit_{'g' if group else 'd'}_{message_id}"
        ):
            if group:
                st.session_state.eco_edit_group_message = message_id
            else:
                st.session_state.eco_edit_message = message_id
            st.rerun()

        if st.button(
            "Delete message",
            key=f"delete_{'g' if group else 'd'}_{message_id}"
        ):
            table = (
                "group_messages"
                if group else "direct_messages"
            )

            eco_update(
                supabase,
                table,
                {"deleted_at": eco_now()},
                [
                    ("id", message_id),
                    ("sender_id", user_id)
                ]
            )

            st.rerun()


def eco_render_message(
    supabase,
    message,
    user_id,
    group=False
):
    mine = message.get("sender_id") == user_id
    deleted = bool(message.get("deleted_at"))

    message_id = message.get("id")

    with st.container():
        left, right = st.columns(
            [1, 1],
            vertical_alignment="top"
        )

        if mine:
            with left:
                st.write("")

            with right:
                st.markdown("**You**")

                if deleted:
                    st.caption("This message was deleted.")
                else:
                    st.success(
                        message.get("message_text") or ""
                    )

                    eco_show_attachment(message)

                    if message.get("edited_at"):
                        st.caption("Edited")

                st.caption(
                    (message.get("created_at") or "")[:16]
                )

                eco_message_controls(
                    supabase,
                    message,
                    user_id,
                    group
                )

        else:
            profile = eco_profile(
                supabase,
                message.get("sender_id")
            )

            with left:
                eco_avatar(profile, 34)

                st.caption(eco_name(profile))

                if deleted:
                    st.info("This message was deleted.")
                else:
                    st.info(
                        message.get("message_text") or ""
                    )

                    eco_show_attachment(message)

                    if message.get("edited_at"):
                        st.caption("Edited")

                st.caption(
                    (message.get("created_at") or "")[:16]
                )

            with right:
                st.write("")


# ============================================================
# PRIVATE CHAT COMPOSER
# ============================================================

def eco_direct_composer(
    supabase,
    conversation_id,
    user_id
):
    st.divider()

    attachment = st.file_uploader(
        "📎 Attach a file",
        key=f"direct_attachment_{conversation_id}"
    )

    audio = None

    if hasattr(st, "audio_input"):
        audio = st.audio_input(
            "Record voice message",
            key=f"direct_audio_{conversation_id}"
        )

    message = st.chat_input(
        " ",
        key=f"direct_composer_{conversation_id}"
    )

    if message or attachment or audio:
        uploaded = attachment or audio
        attachment_url = None
        attachment_name = None
        attachment_type = None

        if uploaded:
            limit = (
                VIDEO_LIMIT
                if uploaded.type.startswith("video/")
                else IMAGE_LIMIT
            )

            if uploaded.size > limit:
                st.error("File exceeds the upload limit.")
                return

            attachment_url = eco_upload(
                supabase,
                uploaded,
                "private-messages"
            )

            attachment_name = uploaded.name
            attachment_type = uploaded.type

        eco_send_direct(
            supabase,
            conversation_id,
            user_id,
            message or "",
            attachment_url,
            attachment_name,
            attachment_type
        )

        st.rerun()


# ============================================================
# PRIVATE CHAT SCREEN
# ============================================================

def render_private_chat(supabase, user_id, other_id):
    other = eco_profile(supabase, other_id)

    if not other:
        st.error("Member profile could not be found.")
        return

    conversation = eco_get_conversation(
        supabase,
        user_id,
        other_id
    )

    if not conversation:
        st.error("Unable to open conversation.")
        return

    conversation_id = conversation["id"]

    top_left, top_middle, top_right = st.columns(
        [1, 4, 1]
    )

    with top_left:
        eco_avatar(other, 48)

    with top_middle:
        st.markdown(f"**{eco_name(other)}**")

        if other.get("username"):
            st.caption(f"@{other['username']}")

    with top_right:
        if st.button(
            "Profile",
            key=f"profile_{other_id}"
        ):
            st.session_state.eco_show_profile = (
                not st.session_state.eco_show_profile
            )

    if st.session_state.eco_show_profile:
        with st.container(border=True):
            eco_profile_details(other)

    st.divider()

    messages = eco_direct_messages(
        supabase,
        conversation_id
    )

    for message in messages:
        eco_render_message(
            supabase,
            message,
            user_id
        )

    edit_id = st.session_state.eco_edit_message

    if edit_id:
        editing = next(
            (
                m for m in messages
                if str(m.get("id")) == str(edit_id)
            ),
            None
        )

        if editing:
            with st.form(f"edit_direct_{edit_id}"):
                revised = st.text_area(
                    "Edit your message",
                    value=editing.get("message_text") or ""
                )

                save, cancel = st.columns(2)

                with save:
                    saved = st.form_submit_button("Save")

                with cancel:
                    cancelled = st.form_submit_button("Cancel")

                if saved:
                    if revised.strip():
                        eco_edit_direct(
                            supabase,
                            edit_id,
                            user_id,
                            revised.strip()
                        )

                    st.session_state.eco_edit_message = None
                    st.rerun()

                if cancelled:
                    st.session_state.eco_edit_message = None
                    st.rerun()

    eco_direct_composer(
        supabase,
        conversation_id,
        user_id
    )


# ============================================================
# PRIVATE CHAT INBOX
# ============================================================

def eco_all_private_conversations(supabase, user_id):
    first = eco_select(
        supabase,
        "direct_conversations",
        [("eq", "user_one_id", user_id)],
        order=("created_at", True)
    )

    second = eco_select(
        supabase,
        "direct_conversations",
        [("eq", "user_two_id", user_id)],
        order=("created_at", True)
    )

    unique = {}

    for conversation in first + second:
        unique[conversation.get("id")] = conversation

    return list(unique.values())


def render_private_inbox(supabase, user_id):
    search = st.text_input(
        "Search conversations",
        placeholder="Search people..."
    )

    conversations = eco_all_private_conversations(
        supabase,
        user_id
    )

    if not conversations:
        st.info(
            "Your private conversations will appear here."
        )

    for conversation in conversations:
        other_id = (
            conversation["user_two_id"]
            if conversation["user_one_id"] == user_id
            else conversation["user_one_id"]
        )

        profile = eco_profile(supabase, other_id)

        if not profile:
            continue

        name = eco_name(profile)

        if search and search.lower() not in (
            name + " " + profile.get("username", "")
        ).lower():
            continue

        messages = eco_direct_messages(
            supabase,
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
            c1, c2, c3 = st.columns(
                [1, 4, 1],
                vertical_alignment="center"
            )

            with c1:
                eco_avatar(profile, 48)

            with c2:
                st.markdown(f"**{name}**")
                st.caption(preview[:65])

            with c3:
                if st.button(
                    "Open",
                    key=f"open_private_{conversation['id']}"
                ):
                    st.session_state.eco_active_person = other_id
                    st.session_state.eco_chat_view = "conversation"
                    st.session_state.eco_show_profile = False
                    st.rerun()


# ============================================================
# FIND PEOPLE
# ============================================================

def render_find_people(supabase, user_id):
    st.markdown("### Find people")

    search = st.text_input(
        "Search by name or username",
        placeholder="Enter a name or username..."
    )

    if not search:
        st.caption(
            "Find an EcoLoop member to start a private conversation."
        )
        return

    profiles = eco_select(
        supabase,
        "member_profiles",
        limit=500
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

    if not matches:
        st.info("No matching members found.")
        return

    for profile in matches:
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 4, 2])

            with c1:
                eco_avatar(profile, 48)

            with c2:
                st.markdown(
                    f"**{eco_name(profile)}**"
                )

                st.caption(
                    f"@{profile.get('username', '')}"
                )

            with c3:
                if st.button(
                    "Message",
                    key=f"find_message_{profile['user_id']}"
                ):
                    st.session_state.eco_active_person = (
                        profile["user_id"]
                    )

                    st.session_state.eco_chat_view = (
                        "conversation"
                    )

                    st.session_state.eco_add_destination = None
                    st.session_state.eco_show_profile = False
                    st.rerun()


# ============================================================
# CHATS SECTION
# ============================================================

def render_chats_section(supabase, user_id):
    if st.session_state.eco_chat_view == "conversation":
        if st.button("← Back to Chats"):
            st.session_state.eco_chat_view = "inbox"
            st.session_state.eco_active_person = None
            st.session_state.eco_show_profile = False
            st.rerun()

        other_id = st.session_state.eco_active_person

        if other_id:
            render_private_chat(
                supabase,
                user_id,
                other_id
            )

        return

    st.markdown("### Chats")

    render_private_inbox(
        supabase,
        user_id
    )


# ============================================================
# CHAT ROOM HELPERS
# ============================================================

def eco_room_membership(supabase, group_id, user_id):
    rows = eco_select(
        supabase,
        "group_memberships",
        [
            ("eq", "group_id", group_id),
            ("eq", "user_id", user_id)
        ],
        limit=1
    )

    return rows[0] if rows else None


def eco_room_messages(supabase, group_id):
    return eco_select(
        supabase,
        "group_messages",
        [("eq", "group_id", group_id)],
        order=("created_at", False),
        limit=300
    )


def eco_send_room_message(
    supabase,
    group_id,
    sender_id,
    message
):
    return eco_insert(
        supabase,
        "group_messages",
        {
            "group_id": group_id,
            "sender_id": sender_id,
            "message_text": message
        }
    )


# ============================================================
# CHAT ROOM SCREEN
# ============================================================

def render_room_chat(supabase, user_id, room):
    group_id = room["id"]

    if st.button("← Back to Chat Rooms"):
        st.session_state.eco_active_room = None
        st.session_state.eco_edit_group_message = None
        st.rerun()

    st.markdown(f"### {room.get('name', 'Chat Room')}")

    if room.get("image_url"):
        st.image(room["image_url"], width=90)

    st.caption(
        room.get("description") or "EcoLoop chat room"
    )

    st.divider()

    messages = eco_room_messages(
        supabase,
        group_id
    )

    for message in messages:
        eco_render_message(
            supabase,
            message,
            user_id,
            group=True
        )

    edit_id = st.session_state.eco_edit_group_message

    if edit_id:
        editing = next(
            (
                m for m in messages
                if str(m.get("id")) == str(edit_id)
            ),
            None
        )

        if editing:
            with st.form(f"edit_room_{edit_id}"):
                revised = st.text_area(
                    "Edit your message",
                    value=editing.get("message_text") or ""
                )

                save, cancel = st.columns(2)

                with save:
                    saved = st.form_submit_button("Save")

                with cancel:
                    cancelled = st.form_submit_button("Cancel")

                if saved:
                    if revised.strip():
                        eco_update(
                            supabase,
                            "group_messages",
                            {
                                "message_text": revised.strip(),
                                "edited_at": eco_now()
                            },
                            [
                                ("id", edit_id),
                                ("sender_id", user_id)
                            ]
                        )

                    st.session_state.eco_edit_group_message = None
                    st.rerun()

                if cancelled:
                    st.session_state.eco_edit_group_message = None
                    st.rerun()

    message = st.chat_input(
        " ",
        key=f"room_composer_{group_id}"
    )

    if message and message.strip():
        eco_send_room_message(
            supabase,
            group_id,
            user_id,
            message.strip()
        )
        st.rerun()


# ============================================================
# CREATE CHAT ROOM
# ============================================================

def render_create_room(supabase, user_id):
    with st.expander("＋ Create a chat room"):
        with st.form("eco_create_room_form"):
            name = st.text_input("Room name")

            description = st.text_area(
                "Room description"
            )

            location = st.text_input(
                "Location (optional)"
            )

            image = st.file_uploader(
                "Room picture",
                type=["png", "jpg", "jpeg"]
            )

            submit = st.form_submit_button(
                "Create chat room"
            )

            if submit:
                if not name.strip():
                    st.error("Enter a room name.")
                else:
                    image_url = (
                        eco_upload(
                            supabase,
                            image,
                            "room-covers"
                        )
                        if image else None
                    )

                    result = eco_insert(
                        supabase,
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
                        try:
                            room = result.data[0]

                            eco_insert(
                                supabase,
                                "group_memberships",
                                {
                                    "group_id": room["id"],
                                    "user_id": user_id,
                                    "membership_role": "admin",
                                    "status": "approved"
                                }
                            )

                        except Exception:
                            pass

                        st.success("Chat room created.")
                        st.rerun()


# ============================================================
# CHAT ROOMS SECTION
# ============================================================

def render_chatrooms_page(supabase, user_id):
    active_room = st.session_state.eco_active_room

    if active_room:
        rooms = eco_select(
            supabase,
            "community_groups",
            [("eq", "id", active_room)],
            limit=1
        )

        if rooms:
            render_room_chat(
                supabase,
                user_id,
                rooms[0]
            )
        else:
            st.error("Chat room not found.")

        return

    st.markdown("### Chat Rooms")

    st.caption(
        "Discover communities, join conversations and collaborate."
    )

    render_create_room(
        supabase,
        user_id
    )

    rooms = eco_select(
        supabase,
        "community_groups",
        order=("created_at", True),
        limit=300
    )

    memberships = eco_select(
        supabase,
        "group_memberships",
        [("eq", "user_id", user_id)]
    )

    membership_map = {
        membership["group_id"]: membership
        for membership in memberships
        if membership.get("group_id")
    }

    joined_rooms = []
    discover_rooms = []

    for room in rooms:
        membership = membership_map.get(room["id"])

        if membership and membership.get("status") == "approved":
            joined_rooms.append(room)
        else:
            discover_rooms.append(room)

    st.markdown("#### Your chat rooms")

    if not joined_rooms:
        st.info(
            "Your joined chat rooms will appear here."
        )

    for room in joined_rooms:
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 4, 1])

            with c1:
                if room.get("image_url"):
                    st.image(
                        room["image_url"],
                        width=52
                    )
                else:
                    st.write("👥")

            with c2:
                st.markdown(f"**{room['name']}**")
                st.caption(
                    room.get("description") or ""
                )

            with c3:
                if st.button(
                    "Open",
                    key=f"open_room_{room['id']}"
                ):
                    st.session_state.eco_active_room = room["id"]
                    st.rerun()

    st.divider()
    st.markdown("#### Discover chat rooms")

    if not discover_rooms:
        st.info("No other chat rooms available yet.")

    for room in discover_rooms:
        membership = membership_map.get(room["id"])

        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 4, 2])

            with c1:
                if room.get("image_url"):
                    st.image(
                        room["image_url"],
                        width=52
                    )
                else:
                    st.write("👥")

            with c2:
                st.markdown(f"**{room['name']}**")
                st.caption(
                    room.get("description") or ""
                )

            with c3:
                if membership and membership.get("status") == "pending":
                    st.caption("Pending approval")

                elif st.button(
                    "Join",
                    key=f"join_room_{room['id']}"
                ):
                    eco_insert(
                        supabase,
                        "group_memberships",
                        {
                            "group_id": room["id"],
                            "user_id": user_id,
                            "membership_role": "member",
                            "status": "pending"
                        }
                    )

                    st.success("Join request submitted.")
                    st.rerun()


# ============================================================
# UPDATES — STORIES
# ============================================================

def render_stories_page(supabase, user_id):
    st.markdown("### Updates")

    st.caption(
        "Share moments, activities and community progress."
    )

    if st.button("＋ Add update"):
        st.session_state.eco_story_form = (
            not st.session_state.eco_story_form
        )

    if st.session_state.eco_story_form:
        with st.form("eco_story_form"):
            caption = st.text_area(
                "Write something about your update"
            )

            media = st.file_uploader(
                "Choose photo or video",
                type=[
                    "jpg", "jpeg", "png",
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
                            supabase,
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
                                supabase,
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

                            st.session_state.eco_story_form = False
                            st.success("Update shared.")
                            st.rerun()

    st.divider()

    stories = eco_select(
        supabase,
        "stories",
        order=("created_at", True),
        limit=300
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

    st.markdown("#### Recent updates")

    if not active_stories:
        st.info("No recent updates yet.")

    for story in active_stories:
        profile = eco_profile(
            supabase,
            story.get("user_id")
        )

        with st.container(border=True):
            c1, c2 = st.columns([1, 5])

            with c1:
                eco_avatar(profile, 48)

            with c2:
                st.markdown(
                    f"**{eco_name(profile)}**"
                )

                st.caption(
                    (story.get("created_at") or "")[:16]
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
    st.divider()

    left, right = st.columns(
        [5, 1],
        vertical_alignment="center"
    )

    with right:
        if st.button(
            "＋",
            key="eco_floating_add",
            help="Start a conversation or find a chat room",
            type="primary"
        ):
            st.session_state.eco_add_menu = (
                not st.session_state.eco_add_menu
            )

    if st.session_state.eco_add_menu:
        with st.container(border=True):
            st.markdown("### Start something new")

            c1, c2 = st.columns(2)

            with c1:
                if st.button(
                    "👤 Find people",
                    use_container_width=True
                ):
                    st.session_state.eco_add_destination = "people"
                    st.session_state.eco_add_menu = False
                    st.rerun()

            with c2:
                if st.button(
                    "👥 Find chat rooms",
                    use_container_width=True
                ):
                    st.session_state.eco_add_destination = "rooms"
                    st.session_state.eco_add_menu = False
                    st.rerun()

            if st.button(
                "＋ Create a chat room",
                use_container_width=True
            ):
                st.session_state.eco_add_destination = "create_room"
                st.session_state.eco_add_menu = False
                st.rerun()


# ============================================================
# MAIN COMMUNITY HUB
# ============================================================

def render_community_groups_page(supabase, user_id):

    eco_initialise_state()

    st.markdown("# EcoLoop")
    st.caption(
        "Connect. Communicate. Create impact."
    )

    # Three separate main destinations.
    selected = st.radio(
        "Community navigation",
        ["Chats", "Chat Rooms", "Updates"],
        horizontal=True,
        key="eco_section",
        label_visibility="collapsed"
    )

    st.divider()

    destination = st.session_state.eco_add_destination

    if destination == "people":
        if st.button("← Back"):
            st.session_state.eco_add_destination = None
            st.rerun()

        render_find_people(
            supabase,
            user_id
        )

    elif destination == "rooms":
        if st.button("← Back"):
            st.session_state.eco_add_destination = None
            st.rerun()

        render_chatrooms_page(
            supabase,
            user_id
        )

    elif destination == "create_room":
        if st.button("← Back"):
            st.session_state.eco_add_destination = None
            st.rerun()

        render_create_room(
            supabase,
            user_id
        )

    else:
        if selected == "Chats":
            render_chats_section(
                supabase,
                user_id
            )

        elif selected == "Chat Rooms":
            render_chatrooms_page(
                supabase,
                user_id
            )

        elif selected == "Updates":
            render_stories_page(
                supabase,
                user_id
            )

    render_floating_add()

    st.divider()

    st.caption(
        "Powered by Next Gen Impact Hub (NGIH)"
    )

    st.caption(
        "Designed by Munashe Roy Mutopa — Project Coordinator"
)
