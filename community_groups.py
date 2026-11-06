import streamlit as st
import uuid
import mimetypes
from datetime import datetime, timezone
from urllib.parse import quote

BUCKET = "community-media"
MAX_FILE_SIZE = 100 * 1024 * 1024
ADMIN_ROLES = ("admin", "group_admin", "owner", "moderator")

REACTIONS = ["👍", "❤️", "😂", "😮", "😢", "🔥", "👏"]


# =========================================================
# GENERAL HELPERS
# =========================================================

def rows(response):
    return response.data if response and response.data else []


def safe_text(value, default=""):
    return str(value or default).strip()


def show_error(error, title="Something went wrong"):
    st.error(f"{title}: {error}")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def get_user_id():
    return st.session_state.get("ecoloop_user_id")


def set_page(page):
    st.session_state["ecoloop_community_page"] = page


def get_profiles(supabase, user_ids):
    ids = list(set(str(x) for x in user_ids if x))

    if not ids:
        return {}

    try:
        result = supabase.table(
            "member_profiles"
        ).select("*").in_(
            "user_id", ids
        ).execute()

        return {
            str(p["user_id"]): p
            for p in rows(result)
        }

    except Exception:
        return {}


def profile_name(profile):
    if not profile:
        return "EcoLoop Member"

    return (
        profile.get("display_name")
        or profile.get("username")
        or "EcoLoop Member"
    )


def format_time(value):
    if not value:
        return ""

    try:
        dt = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        dt = dt.astimezone(timezone.utc)
        current = datetime.now(timezone.utc)

        if dt.date() == current.date():
            return dt.strftime("%H:%M")

        if dt.year == current.year:
            return dt.strftime("%d %b")

        return dt.strftime("%d %b %Y")

    except Exception:
        return ""


def format_full_time(value):
    if not value:
        return ""

    try:
        dt = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
        return dt.astimezone().strftime("%d %b %Y · %H:%M")
    except Exception:
        return ""


def safe_query_table(supabase, table, columns="*"):
    try:
        result = supabase.table(table).select(columns).execute()
        return rows(result)
    except Exception:
        return []


def get_group(supabase, group_id):
    try:
        result = supabase.table(
            "community_groups"
        ).select("*").eq(
            "id", group_id
        ).limit(1).execute()

        found = rows(result)
        return found[0] if found else None

    except Exception:
        return None


def get_community(supabase, community_id):
    try:
        result = supabase.table(
            "communities"
        ).select("*").eq(
            "id", community_id
        ).limit(1).execute()

        found = rows(result)
        return found[0] if found else None

    except Exception:
        return None


# =========================================================
# STORAGE
# =========================================================

def upload_media(supabase, uploaded_file, folder):
    if not uploaded_file:
        return None

    if uploaded_file.size > MAX_FILE_SIZE:
        st.error("Maximum file size is 100 MB.")
        return None

    filename = uploaded_file.name.replace(" ", "_")
    path = f"{folder}/{uuid.uuid4().hex}_{filename}"

    try:
        supabase.storage.from_(BUCKET).upload(
            path,
            uploaded_file.getvalue(),
            {
                "content-type": (
                    uploaded_file.type
                    or mimetypes.guess_type(filename)[0]
                    or "application/octet-stream"
                ),
                "upsert": "true"
            }
        )

        return path

    except Exception as e:
        show_error(e, "File upload failed")
        return None


def media_url(supabase, path):
    if not path:
        return None

    if str(path).startswith("http"):
        return path

    try:
        result = supabase.storage.from_(
            BUCKET
        ).create_signed_url(path, 3600)

        return (
            result.get("signedURL")
            or result.get("signedUrl")
        )

    except Exception:
        return None


def display_attachment(supabase, path, name, file_type):
    if not path:
        return

    url = media_url(supabase, path)

    if not url:
        st.caption("Attachment unavailable.")
        return

    name = name or "Attachment"
    file_type = file_type or ""

    if file_type.startswith("image/"):
        st.image(url, use_container_width=True)

    elif file_type.startswith("video/"):
        st.video(url)

    elif file_type.startswith("audio/"):
        st.audio(url)

    else:
        st.markdown(f"[📎 {name}]({url})")


# =========================================================
# PROFILE SYSTEM
# =========================================================

def get_profile(supabase, user_id):
    try:
        result = supabase.table(
            "member_profiles"
        ).select("*").eq(
            "user_id", user_id
        ).limit(1).execute()

        found = rows(result)
        return found[0] if found else {}

    except Exception:
        return {}


def profile_picture(supabase, profile):
    if not profile:
        return None

    return media_url(
        supabase,
        profile.get("avatar_url")
    )


def profile_editor(supabase, user_id):
    st.subheader("My profile")

    profile = get_profile(supabase, user_id)
    picture = profile_picture(supabase, profile)

    if picture:
        st.image(picture, width=110)

    with st.form("ecoloop_community_profile"):
        display_name = st.text_input(
            "Display name",
            value=profile.get("display_name", "")
        )

        username = st.text_input(
            "Username",
            value=profile.get("username", "")
        )

        bio = st.text_area(
            "About me",
            value=profile.get("bio", "")
        )

        location = st.text_input(
            "Location",
            value=profile.get("location", "")
        )

        interests = st.text_input(
            "Interests",
            value=profile.get("interests", "")
        )

        avatar_url = st.text_input(
            "Profile picture URL",
            value=profile.get("avatar_url", "")
        )

        submitted = st.form_submit_button(
            "Save profile",
            use_container_width=True
        )

        if submitted:
            try:
                supabase.table(
                    "member_profiles"
                ).upsert({
                    "user_id": user_id,
                    "display_name": display_name.strip(),
                    "username": username.strip(),
                    "bio": bio.strip(),
                    "location": location.strip(),
                    "interests": interests.strip(),
                    "avatar_url": avatar_url.strip(),
                    "updated_at": now_iso()
                }, on_conflict="user_id").execute()

                st.success("Profile updated.")
                st.rerun()

            except Exception as e:
                show_error(e, "Could not update profile")


def member_profile_card(supabase, user_id):
    profile = get_profile(supabase, user_id)
    picture = profile_picture(supabase, profile)

    with st.container(border=True):
        col1, col2 = st.columns([1, 4])

        with col1:
            if picture:
                st.image(picture, width=75)
            else:
                st.markdown("## 👤")

        with col2:
            st.markdown(f"**{profile_name(profile)}**")

            if profile.get("username"):
                st.caption("@" + profile["username"])

            if profile.get("location"):
                st.caption("📍 " + profile["location"])

            if profile.get("bio"):
                st.write(profile["bio"])


# =========================================================
# GROUP MEMBERSHIP AND ADMINISTRATION
# =========================================================

def is_member(supabase, group_id, user_id):
    group = get_group(supabase, group_id)

    if group and str(group.get("created_by")) == str(user_id):
        return True

    try:
        result = supabase.table(
            "group_memberships"
        ).select("id").eq(
            "group_id", group_id
        ).eq(
            "user_id", user_id
        ).eq(
            "status", "approved"
        ).limit(1).execute()

        return bool(rows(result))

    except Exception:
        return False


def is_admin(supabase, group_id, user_id):
    group = get_group(supabase, group_id)

    if group and str(group.get("created_by")) == str(user_id):
        return True

    try:
        result = supabase.table(
            "group_memberships"
        ).select("membership_role").eq(
            "group_id", group_id
        ).eq(
            "user_id", user_id
        ).eq(
            "status", "approved"
        ).limit(1).execute()

        found = rows(result)

        if found:
            return safe_text(
                found[0].get("membership_role")
            ).lower() in ADMIN_ROLES

    except Exception:
        pass

    return False


def get_memberships(supabase, group_id):
    try:
        result = supabase.table(
            "group_memberships"
        ).select("*").eq(
            "group_id", group_id
        ).order("joined_at").execute()

        return rows(result)

    except Exception:
        return []


def get_approved_members(supabase, group_id):
    return [
        m for m in get_memberships(supabase, group_id)
        if m.get("status") == "approved"
    ]


def request_to_join(supabase, group_id, user_id):
    try:
        existing = supabase.table(
            "group_memberships"
        ).select("id,status").eq(
            "group_id", group_id
        ).eq(
            "user_id", user_id
        ).limit(1).execute()

        found = rows(existing)

        if found:
            status = found[0].get("status")

            if status == "approved":
                st.info("You are already a member.")
            elif status == "pending":
                st.info("Your request is awaiting approval.")
            else:
                st.info("A membership record already exists.")

            return

        supabase.table(
            "group_memberships"
        ).insert({
            "group_id": group_id,
            "user_id": user_id,
            "membership_role": "member",
            "status": "pending"
        }).execute()

        st.success("Your request has been submitted.")
        st.rerun()

    except Exception as e:
        show_error(e, "Could not request membership")


# =========================================================
# COMMUNITIES
# =========================================================

def load_communities(supabase):
    try:
        result = supabase.table(
            "communities"
        ).select("*").order(
            "created_at", desc=True
        ).execute()

        return rows(result)

    except Exception as e:
        show_error(e, "Could not load communities")
        return []


def create_community(supabase, user_id):
    with st.expander("＋ Create a community"):
        with st.form("create_ecoloop_community"):
            name = st.text_input("Community name")
            description = st.text_area("Description")
            location = st.text_input("Location")

            submitted = st.form_submit_button(
                "Create community",
                use_container_width=True
            )

            if submitted:
                if not name.strip():
                    st.warning("Enter a community name.")
                    return

                try:
                    supabase.table(
                        "communities"
                    ).insert({
                        "name": name.strip(),
                        "description": description.strip(),
                        "location": location.strip(),
                        "created_by": user_id
                    }).execute()

                    st.success("Community created.")
                    st.rerun()

                except Exception as e:
                    show_error(e, "Community creation failed")


def create_group(supabase, user_id):
    communities = load_communities(supabase)

    options = {"No community": None}

    for community in communities:
        options[community["name"]] = community["id"]

    with st.expander("＋ Create a group"):
        with st.form("ecoloop_create_group"):
            name = st.text_input("Group name")
            description = st.text_area("Group description")
            location = st.text_input("Location")

            selected = st.selectbox(
                "Community",
                list(options.keys())
            )

            image = st.file_uploader(
                "Group picture",
                type=["png", "jpg", "jpeg"]
            )

            submitted = st.form_submit_button(
                "Create group",
                use_container_width=True
            )

            if submitted:
                if not name.strip():
                    st.warning("Enter a group name.")
                    return

                data = {
                    "name": name.strip(),
                    "description": description.strip(),
                    "location": location.strip(),
                    "created_by": user_id
                }

                if options[selected]:
                    data["community_id"] = options[selected]

                try:
                    result = supabase.table(
                        "community_groups"
                    ).insert(data).execute()

                    created = rows(result)

                    if not created:
                        st.error("Could not retrieve the new group.")
                        return

                    group_id = created[0]["id"]

                    if image:
                        path = upload_media(
                            supabase,
                            image,
                            f"{group_id}/{user_id}"
                        )

                        if path:
                            supabase.table(
                                "community_groups"
                            ).update({
                                "image_url": path
                            }).eq("id", group_id).execute()

                    try:
                        supabase.table(
                            "group_memberships"
                        ).insert({
                            "group_id": group_id,
                            "user_id": user_id,
                            "membership_role": "admin",
                            "status": "approved"
                        }).execute()
                    except Exception:
                        pass

                    st.session_state["ecoloop_open_group_id"] = str(group_id)
                    st.success("Group created.")
                    st.rerun()

                except Exception as e:
                    show_error(e, "Group creation failed")


def load_groups(supabase):
    try:
        result = supabase.table(
            "community_groups"
        ).select("*").order(
            "created_at", desc=True
        ).execute()

        return rows(result)

    except Exception:
        return []


def get_my_groups(supabase, user_id):
    return [
        group for group in load_groups(supabase)
        if is_member(supabase, group["id"], user_id)
    ]


def get_community_groups(supabase, community_id):
    try:
        result = supabase.table(
            "community_groups"
        ).select("*").eq(
            "community_id", community_id
        ).order("created_at", desc=True).execute()

        return rows(result)

    except Exception:
        return []


# =========================================================
# GROUP MESSAGES
# =========================================================

def get_messages(supabase, group_id, limit=200):
    try:
        result = supabase.table(
            "group_messages"
        ).select("*").eq(
            "group_id", group_id
        ).order(
            "created_at", desc=True
        ).limit(limit).execute()

        return list(reversed(rows(result)))

    except Exception as e:
        show_error(e, "Could not load group messages")
        return []


def get_latest_message(supabase, group_id):
    try:
        result = supabase.table(
            "group_messages"
        ).select("*").eq(
            "group_id", group_id
        ).order(
            "created_at", desc=True
        ).limit(1).execute()

        found = rows(result)
        return found[0] if found else None

    except Exception:
        return None


def message_preview(message):
    if not message:
        return "No messages yet"

    text = safe_text(message.get("message_text"))

    if message.get("attachment_name"):
        text = (
            text + " · 📎 " + message["attachment_name"]
            if text else "📎 " + message["attachment_name"]
        )

    if not text:
        text = "Sent an attachment"

    return text[:65] + ("..." if len(text) > 65 else "")


def get_group_last_read(supabase, group_id, user_id):
    try:
        result = supabase.table(
            "group_read_status"
        ).select("last_read_at").eq(
            "group_id", group_id
        ).eq(
            "user_id", user_id
        ).limit(1).execute()

        found = rows(result)

        if found:
            return found[0].get("last_read_at")

    except Exception:
        pass

    return None


def mark_group_read(supabase, group_id, user_id):
    try:
        supabase.table(
            "group_read_status"
        ).upsert({
            "group_id": group_id,
            "user_id": user_id,
            "last_read_at": now_iso()
        }, on_conflict="group_id,user_id").execute()

    except Exception:
        st.session_state[
            f"ecoloop_last_read_{group_id}_{user_id}"
        ] = now_iso()


def get_group_unread(supabase, group_id, user_id):
    last_read = get_group_last_read(
        supabase, group_id, user_id
    )

    if not last_read:
        last_read = st.session_state.get(
            f"ecoloop_last_read_{group_id}_{user_id}"
        )

    if not last_read:
        return 0

    try:
        result = supabase.table(
            "group_messages"
        ).select("id,sender_id").eq(
            "group_id", group_id
        ).gt(
            "created_at", last_read
        ).execute()

        return sum(
            1 for m in rows(result)
            if str(m.get("sender_id")) != str(user_id)
        )

    except Exception:
        return 0


def send_group_message(
    supabase,
    group_id,
    user_id,
    message_text,
    uploaded_file=None,
    reply_to_id=None,
    forwarded_from=None
):
    message_text = safe_text(message_text)

    if not message_text and not uploaded_file:
        st.warning("Write a message or attach a file.")
        return False

    data = {
        "group_id": group_id,
        "sender_id": user_id,
        "message_text": message_text
    }

    if reply_to_id:
        data["reply_to_id"] = reply_to_id

    if forwarded_from:
        data["forwarded_from"] = forwarded_from

    if uploaded_file:
        path = upload_media(
            supabase,
            uploaded_file,
            f"{group_id}/{user_id}"
        )

        if not path:
            return False

        data.update({
            "attachment_path": path,
            "attachment_name": uploaded_file.name,
            "attachment_type": (
                uploaded_file.type
                or mimetypes.guess_type(uploaded_file.name)[0]
                or "application/octet-stream"
            )
        })

    try:
        supabase.table(
            "group_messages"
        ).insert(data).execute()

        mark_group_read(supabase, group_id, user_id)
        return True

    except Exception as e:
        if reply_to_id or forwarded_from:
            st.warning(
                "This message option needs its database field. "
                "We'll add that in the final SQL setup."
            )
        else:
            show_error(e, "Message could not be sent")

        return False


# =========================================================
# MESSAGE REACTIONS
# =========================================================

def get_group_reactions(supabase, message_id):
    try:
        result = supabase.table(
            "group_message_reactions"
        ).select("*").eq(
            "message_id", message_id
        ).execute()

        return rows(result)

    except Exception:
        return []


def reaction_controls(supabase, message_id, user_id):
    reactions = get_group_reactions(supabase, message_id)

    if reactions:
        summary = {}

        for item in reactions:
            emoji = item.get("reaction", "")
            summary[emoji] = summary.get(emoji, 0) + 1

        st.caption(
            "   ".join(
                f"{emoji} {count}"
                for emoji, count in summary.items()
            )
        )

    with st.popover("React"):
        selected = st.selectbox(
            "Choose a reaction",
            REACTIONS,
            key=f"reaction_select_{message_id}"
        )

        if st.button(
            "Send reaction",
            key=f"reaction_send_{message_id}"
        ):
            try:
                supabase.table(
                    "group_message_reactions"
                ).upsert({
                    "message_id": message_id,
                    "user_id": user_id,
                    "reaction": selected
                }).execute()

                st.rerun()

            except Exception:
                st.info(
                    "Reactions will become available after "
                    "the Community database update."
                )


# =========================================================
# GROUP MESSAGE DISPLAY
# =========================================================

def display_group_messages(supabase, messages, user_id):
    sender_ids = [
        m.get("sender_id")
        for m in messages
        if m.get("sender_id")
    ]

    profiles = get_profiles(supabase, sender_ids)

    for message in messages:
        sender_id = str(message.get("sender_id", ""))
        profile = profiles.get(sender_id)
        mine = sender_id == str(user_id)

        with st.container(border=True):
            if mine:
                st.caption("**You** · " + format_time(message.get("created_at")))
            else:
                st.caption(
                    f"**{profile_name(profile)}** · "
                    f"{format_time(message.get('created_at'))}"
                )

            if message.get("forwarded_from"):
                st.caption("↪ Forwarded")

            if message.get("reply_to_id"):
                st.caption("↩ Reply to an earlier message")

            if message.get("deleted_at"):
                st.caption("This message was deleted.")
            elif message.get("message_text"):
                st.write(message["message_text"])

            display_attachment(
                supabase,
                message.get("attachment_path"),
                message.get("attachment_name"),
                message.get("attachment_type")
            )

            if message.get("is_pinned"):
                st.caption("📌 Pinned message")

            reaction_controls(
                supabase,
                message.get("id"),
                user_id
            )

            with st.expander("Message options"):
                if st.button(
                    "↩ Reply to this message",
                    key=f"reply_{message['id']}"
                ):
                    st.session_state[
                        f"reply_to_{message.get('group_id')}"
                    ] = message["id"]
                    st.rerun()

                if st.button(
                    "↪ Forward this message",
                    key=f"forward_{message['id']}"
                ):
                    st.session_state[
                        "ecoloop_forward_message"
                    ] = message
                    st.rerun()

                if mine:
                    if st.button(
                        "Delete message",
                        key=f"delete_message_{message['id']}"
                    ):
                        try:
                            supabase.table(
                                "group_messages"
                            ).update({
                                "deleted_at": now_iso(),
                                "message_text": "Message deleted"
                            }).eq(
                                "id", message["id"]
                            ).eq(
                                "sender_id", user_id
                            ).execute()

                            st.rerun()

                        except Exception:
                            st.info(
                                "Message deletion needs the "
                                "database update."
                            )

                if is_admin(
                    supabase,
                    message.get("group_id"),
                    user_id
                ):
                    if st.button(
                        "Pin message",
                        key=f"pin_{message['id']}"
                    ):
                        try:
                            supabase.table(
                                "group_messages"
                            ).update({
                                "is_pinned": True,
                                "pinned_by": user_id,
                                "pinned_at": now_iso()
                            }).eq(
                                "id", message["id"]
                            ).execute()

                            st.rerun()

                        except Exception as e:
                            show_error(e, "Could not pin message")


# =========================================================
# GROUP CHAT COMPOSER
# =========================================================

def group_chat_composer(supabase, group_id, user_id):
    reply_key = f"reply_to_{group_id}"
    reply_id = st.session_state.get(reply_key)

    if reply_id:
        st.info("↩ Replying to a message")

        if st.button("Cancel reply", key=f"cancel_reply_{group_id}"):
            st.session_state[reply_key] = None
            st.rerun()

    with st.form(
        f"group_chat_form_{group_id}",
        clear_on_submit=True
    ):
        message_text = st.text_area(
            "Message",
            placeholder="Type a message...",
            label_visibility="collapsed"
        )

        uploaded_file = st.file_uploader(
            "Attach photo, video, audio or document",
            key=f"group_upload_{group_id}"
        )

        submitted = st.form_submit_button(
            "Send ➤",
            use_container_width=True
        )

        if submitted:
            success = send_group_message(
                supabase,
                group_id,
                user_id,
                message_text,
                uploaded_file,
                reply_to_id=reply_id
            )

            if success:
                st.session_state[reply_key] = None
                st.rerun()


def chat_area(supabase, group_id, user_id):
    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("Messages")

    with col2:
        if st.button("↻ Refresh", key=f"refresh_group_{group_id}"):
            st.rerun()

    messages = get_messages(supabase, group_id)

    if messages:
        display_group_messages(
            supabase,
            messages,
            user_id
        )
    else:
        st.info("No messages yet. Start the conversation!")

    st.divider()

    group_chat_composer(
        supabase,
        group_id,
        user_id
    )


# =========================================================
# GROUP MEMBERS PAGE
# =========================================================

def group_members(supabase, group_id, user_id):
    st.subheader("Group members")

    admin = is_admin(supabase, group_id, user_id)
    memberships = get_memberships(supabase, group_id)

    profiles = get_profiles(
        supabase,
        [m.get("user_id") for m in memberships]
    )

    approved = [
        m for m in memberships
        if m.get("status") == "approved"
    ]

    pending = [
        m for m in memberships
        if m.get("status") == "pending"
    ]

    st.caption(
        f"{len(approved)} members · {len(pending)} pending requests"
    )

    if admin and pending:
        st.markdown("### Membership requests")

        for member in pending:
            profile = profiles.get(str(member.get("user_id")))

            with st.container(border=True):
                st.write(f"**{profile_name(profile)}**")

                left, right = st.columns(2)

                with left:
                    if st.button(
                        "Approve",
                        key=f"approve_{member['id']}"
                    ):
                        try:
                            supabase.table(
                                "group_memberships"
                            ).update({
                                "status": "approved"
                            }).eq(
                                "id", member["id"]
                            ).execute()

                            st.success("Member approved.")
                            st.rerun()

                        except Exception as e:
                            show_error(e, "Approval failed")

                with right:
                    if st.button(
                        "Reject",
                        key=f"reject_{member['id']}"
                    ):
                        try:
                            supabase.table(
                                "group_memberships"
                            ).delete().eq(
                                "id", member["id"]
                            ).execute()

                            st.rerun()

                        except Exception as e:
                            show_error(e, "Rejection failed")

    st.markdown("### Members")

    group = get_group(supabase, group_id)
    owner_id = str(group.get("created_by")) if group else ""

    for member in approved:
        member_id = str(member.get("user_id"))
        profile = profiles.get(member_id)
        role = member.get("membership_role", "member")

        with st.container(border=True):
            col1, col2 = st.columns([1, 4])

            with col1:
                picture = profile_picture(supabase, profile)

                if picture:
                    st.image(picture, width=55)
                else:
                    st.markdown("## 👤")

            with col2:
                st.write(f"**{profile_name(profile)}**")
                st.caption(role.title())

            if admin and member_id != owner_id and member_id != str(user_id):
                if role not in ADMIN_ROLES:
                    if st.button(
                        "Make admin",
                        key=f"promote_{member['id']}"
                    ):
                        try:
                            supabase.table(
                                "group_memberships"
                            ).update({
                                "membership_role": "admin"
                            }).eq(
                                "id", member["id"]
                            ).execute()

                            st.rerun()

                        except Exception as e:
                            show_error(e, "Could not promote member")

                if st.button(
                    "Remove member",
                    key=f"remove_{member['id']}"
                ):
                    try:
                        supabase.table(
                            "group_memberships"
                        ).delete().eq(
                            "id", member["id"]
                        ).execute()

                        st.rerun()

                    except Exception as e:
                        show_error(e, "Could not remove member")

    if admin:
        st.divider()
        st.markdown("### Add a member")

        with st.form(f"add_member_{group_id}"):
            new_user_id = st.text_input("Member's EcoLoop user ID")

            submitted = st.form_submit_button("Add member")

            if submitted:
                try:
                    supabase.table(
                        "group_memberships"
                    ).insert({
                        "group_id": group_id,
                        "user_id": new_user_id.strip(),
                        "membership_role": "member",
                        "status": "approved"
                    }).execute()

                    st.success("Member added.")
                    st.rerun()

                except Exception as e:
                    show_error(e, "Could not add member")


# =========================================================
# GROUP INFORMATION
# =========================================================

def group_profile(supabase, group, user_id):
    group_id = group["id"]
    admin = is_admin(supabase, group_id, user_id)

    st.subheader("Group information")

    picture = media_url(supabase, group.get("image_url"))

    if picture:
        st.image(picture, width=150)
    else:
        st.markdown("## 👥")

    st.markdown(f"### {group.get('name', 'Group')}")
    st.write(group.get("description") or "No description.")

    if group.get("location"):
        st.caption("📍 " + group["location"])

    st.caption(
        f"👥 {len(get_approved_members(supabase, group_id))} members"
    )

    if not admin:
        return

    st.divider()
    st.markdown("### Edit group")

    with st.form(f"edit_group_{group_id}"):
        name = st.text_input(
            "Group name",
            value=group.get("name", "")
        )

        description = st.text_area(
            "Description",
            value=group.get("description", "")
        )

        location = st.text_input(
            "Location",
            value=group.get("location", "")
        )

        image = st.file_uploader(
            "New group picture",
            type=["png", "jpg", "jpeg"],
            key=f"edit_group_picture_{group_id}"
        )

        submitted = st.form_submit_button("Save changes")

        if submitted:
            data = {
                "name": name.strip(),
                "description": description.strip(),
                "location": location.strip()
            }

            if image:
                path = upload_media(
                    supabase,
                    image,
                    f"{group_id}/{user_id}"
                )

                if not path:
                    return

                data["image_url"] = path

            try:
                supabase.table(
                    "community_groups"
                ).update(data).eq(
                    "id", group_id
                ).execute()

                st.success("Group updated.")
                st.rerun()

            except Exception as e:
                show_error(e, "Could not update group")


# =========================================================
# INVITATIONS
# =========================================================

def group_invitations(supabase, group_id, user_id):
    st.subheader("Invitations")

    if not is_admin(supabase, group_id, user_id):
        st.info("Only group admins can create invitations.")
        return

    if st.button(
        "＋ Create invitation",
        key=f"create_invite_{group_id}"
    ):
        code = uuid.uuid4().hex[:12].upper()

        try:
            supabase.table(
                "community_invites"
            ).insert({
                "invite_code": code,
                "target_type": "group",
                "target_id": group_id,
                "created_by": user_id,
                "is_active": True,
                "max_uses": 50,
                "uses": 0
            }).execute()

            st.session_state[
                f"invite_code_{group_id}"
            ] = code

            st.rerun()

        except Exception as e:
            show_error(e, "Could not create invitation")

    code = st.session_state.get(
        f"invite_code_{group_id}"
    )

    if code:
        st.success("Invitation created.")
        st.code(code)

        st.caption(
            "Share this code with people who want to join."
        )


def redeem_invitation(supabase, user_id, code=None):
    st.subheader("Join a group")

    if not code:
        code = st.text_input("Invitation code").strip().upper()

    if st.button("Find invitation", use_container_width=True):
        if not code:
            st.warning("Enter an invitation code.")
            return

        try:
            result = supabase.table(
                "community_invites"
            ).select("*").eq(
                "invite_code", code
            ).eq(
                "is_active", True
            ).limit(1).execute()

            found = rows(result)

            if not found:
                st.error("Invitation unavailable.")
                return

            invite = found[0]

            if invite.get("target_type") != "group":
                st.error("This invitation is not for a group.")
                return

            group = get_group(supabase, invite.get("target_id"))

            if not group:
                st.error("Group not found.")
                return

            if is_member(supabase, group["id"], user_id):
                st.success("You are already a member.")
                return

            request_to_join(
                supabase,
                group["id"],
                user_id
            )

        except Exception as e:
            show_error(e, "Could not retrieve invitation")


# =========================================================
# GROUP MEETINGS
# =========================================================

def group_meetings(group_id):
    st.subheader("Group meetings")

    st.write(
        "Create an external video meeting room for your group."
    )

    if st.button(
        "＋ Create meeting room",
        key=f"meeting_{group_id}"
    ):
        room = (
            "EcoLoop-"
            + str(group_id).replace("-", "")[:12]
            + "-"
            + uuid.uuid4().hex[:8]
        )

        st.session_state[
            f"meeting_url_{group_id}"
        ] = "https://meet.jit.si/" + quote(room)

    url = st.session_state.get(
        f"meeting_url_{group_id}"
    )

    if url:
        st.link_button(
            "Join video meeting",
            url,
            use_container_width=True
        )

        st.caption("Video meetings are hosted by Jitsi.")


# =========================================================
# GROUP CHAT WORKSPACE
# =========================================================

def group_workspace(supabase, group_id, user_id):
    group = get_group(supabase, group_id)

    if not group:
        st.error("Group not found.")
        return

    if not is_member(supabase, group_id, user_id):
        st.error("You are not an approved member of this group.")
        return

    picture = media_url(supabase, group.get("image_url"))

    back, image_col, heading = st.columns([1, 1, 5])

    with back:
        if st.button("←", key=f"back_group_{group_id}"):
            st.session_state["ecoloop_open_group_id"] = None
            st.session_state["ecoloop_group_info_open"] = False
            st.rerun()

    with image_col:
        if picture:
            st.image(picture, width=50)
        else:
            st.markdown("## 👥")

    with heading:
        if st.button(
            group.get("name", "Group"),
            key=f"group_title_{group_id}"
        ):
            st.session_state["ecoloop_group_info_open"] = (
                not st.session_state.get("ecoloop_group_info_open", False)
            )
            st.rerun()

        st.caption(
            f"{len(get_approved_members(supabase, group_id))} members"
        )

    if st.session_state.get("ecoloop_group_info_open"):
        tabs = st.tabs([
            "Information",
            "Members",
            "Invitations",
            "Meetings"
        ])

        with tabs[0]:
            group_profile(supabase, group, user_id)

        with tabs[1]:
            group_members(supabase, group_id, user_id)

        with tabs[2]:
            group_invitations(supabase, group_id, user_id)

        with tabs[3]:
            group_meetings(group_id)

    else:
        chat_area(supabase, group_id, user_id)

        if st.button(
            "ⓘ Group information",
            key=f"group_info_button_{group_id}",
            use_container_width=True
        ):
            st.session_state["ecoloop_group_info_open"] = True
            st.rerun()

    mark_group_read(supabase, group_id, user_id)


# =========================================================
# WHATSAPP-STYLE GROUP CONVERSATION LIST
# =========================================================

def my_groups_page(supabase, user_id):
    st.subheader("Chats · Groups")

    groups = get_my_groups(supabase, user_id)

    if not groups:
        st.info("You haven't joined any groups yet.")
        return

    for group in groups:
        group_id = group["id"]
        latest = get_latest_message(supabase, group_id)
        count = get_group_unread(supabase, group_id, user_id)

        profile = None

        if latest and latest.get("sender_id"):
            profile = get_profiles(
                supabase,
                [latest["sender_id"]]
            ).get(str(latest["sender_id"]))

        picture = media_url(
            supabase,
            group.get("image_url")
        )

        with st.container(border=True):
            left, middle, right = st.columns([1, 4, 1])

            with left:
                if picture:
                    st.image(picture, width=60)
                else:
                    st.markdown("## 👥")

            with middle:
                st.markdown(f"**{group.get('name', 'Group')}**")

                if latest:
                    st.caption(
                        f"{profile_name(profile)}: "
                        f"{message_preview(latest)}"
                    )
                else:
                    st.caption("Start the conversation")

            with right:
                if latest:
                    st.caption(format_time(latest.get("created_at")))

                if count:
                    st.success(str(count))

            if st.button(
                "Open conversation",
                key=f"open_group_{group_id}",
                use_container_width=True
            ):
                st.session_state["ecoloop_open_group_id"] = str(group_id)
                st.session_state["ecoloop_group_info_open"] = False
                st.rerun()


# =========================================================
# DISCOVER GROUPS
# =========================================================

def discover_groups_page(supabase, user_id):
    st.subheader("Discover groups")

    search = st.text_input(
        "🔎 Search groups",
        placeholder="Group name, topic or location..."
    ).lower()

    communities = load_communities(supabase)

    community_names = ["All communities"] + [
        c.get("name", "Community")
        for c in communities
    ]

    selected = st.selectbox(
        "Community filter",
        community_names
    )

    create_group(supabase, user_id)

    community_lookup = {
        str(c["id"]): c.get("name", "")
        for c in communities
    }

    for group in load_groups(supabase):
        community_name = community_lookup.get(
            str(group.get("community_id")), ""
        )

        searchable = " ".join([
            safe_text(group.get("name")),
            safe_text(group.get("description")),
            safe_text(group.get("location")),
            community_name
        ]).lower()

        if search and search not in searchable:
            continue

        if selected != "All communities" and community_name != selected:
            continue

        group_id = group["id"]
        picture = media_url(supabase, group.get("image_url"))

        with st.container(border=True):
            if picture:
                st.image(picture, width=90)

            st.markdown(f"**{group.get('name', 'Group')}**")
            st.write(group.get("description") or "No description.")

            if community_name:
                st.caption("🌍 " + community_name)

            if group.get("location"):
                st.caption("📍 " + group["location"])

            if is_member(supabase, group_id, user_id):
                if st.button(
                    "Open group",
                    key=f"discover_open_{group_id}"
                ):
                    st.session_state["ecoloop_open_group_id"] = str(group_id)
                    st.rerun()
            else:
                if st.button(
                    "Request to join",
                    key=f"discover_join_{group_id}"
                ):
                    request_to_join(supabase, group_id, user_id)


# =========================================================
# CHANNELS
# =========================================================

def load_channels(supabase, community_id):
    try:
        result = supabase.table(
            "community_channels"
        ).select("*").eq(
            "community_id", community_id
        ).eq(
            "is_active", True
        ).order("created_at", desc=True).execute()

        return rows(result)

    except Exception:
        return []


def get_channel_messages(supabase, channel_id, limit=100):
    try:
        result = supabase.table(
            "channel_messages"
        ).select("*").eq(
            "channel_id", channel_id
        ).order(
            "created_at", desc=True
        ).limit(limit).execute()

        return list(reversed(rows(result)))

    except Exception:
        return []


def channel_last_read(supabase, channel_id, user_id):
    try:
        result = supabase.table(
            "channel_read_status"
        ).select("last_read_at").eq(
            "channel_id", channel_id
        ).eq(
            "user_id", user_id
        ).limit(1).execute()

        found = rows(result)
        return found[0].get("last_read_at") if found else None

    except Exception:
        return None


def mark_channel_read(supabase, channel_id, user_id):
    try:
        supabase.table(
            "channel_read_status"
        ).upsert({
            "channel_id": channel_id,
            "user_id": user_id,
            "last_read_at": now_iso()
        }, on_conflict="channel_id,user_id").execute()

    except Exception:
        pass


def channel_unread_count(supabase, channel_id, user_id):
    last_read = channel_last_read(
        supabase, channel_id, user_id
    )

    if not last_read:
        return 0

    try:
        result = supabase.table(
            "channel_messages"
        ).select("id,sender_id").eq(
            "channel_id", channel_id
        ).gt(
            "created_at", last_read
        ).execute()

        return sum(
            1 for m in rows(result)
            if str(m.get("sender_id")) != str(user_id)
        )

    except Exception:
        return 0


def create_channel(supabase, community, user_id):
    if str(community.get("created_by")) != str(user_id):
        return

    community_id = community["id"]

    with st.expander("＋ Create announcement channel"):
        with st.form(f"create_channel_{community_id}"):
            name = st.text_input("Channel name")
            description = st.text_area("Channel description")

            submitted = st.form_submit_button("Create channel")

            if submitted:
                try:
                    supabase.table(
                        "community_channels"
                    ).insert({
                        "community_id": community_id,
                        "name": name.strip(),
                        "description": description.strip(),
                        "created_by": user_id,
                        "is_active": True
                    }).execute()

                    st.success("Channel created.")
                    st.rerun()

                except Exception as e:
                    show_error(e, "Channel creation failed")


def channel_workspace(supabase, channel, user_id):
    st.subheader("📢 " + channel.get("name", "Channel"))
    st.caption(channel.get("description") or "Community announcements")

    messages = get_channel_messages(
        supabase,
        channel["id"]
    )

    profiles = get_profiles(
        supabase,
        [m.get("sender_id") for m in messages]
    )

    for message in messages:
        profile = profiles.get(str(message.get("sender_id")))

        with st.container(border=True):
            st.caption(
                f"**{profile_name(profile)}** · "
                f"{format_time(message.get('created_at'))}"
            )

            st.write(message.get("message_text", ""))

    if str(channel.get("created_by")) == str(user_id):
        st.divider()

        with st.form(f"channel_post_{channel['id']}"):
            post = st.text_area(
                "Write an announcement",
                placeholder="Share an update with the community..."
            )

            submitted = st.form_submit_button(
                "Publish announcement",
                use_container_width=True
            )

            if submitted:
                if not post.strip():
                    st.warning("Write an announcement.")
                else:
                    try:
                        supabase.table(
                            "channel_messages"
                        ).insert({
                            "channel_id": channel["id"],
                            "sender_id": user_id,
                            "message_text": post.strip()
                        }).execute()

                        st.success("Announcement published.")
                        st.rerun()

                    except Exception as e:
                        show_error(e, "Could not publish announcement")
    else:
        st.caption("Only the channel creator can publish announcements.")

    mark_channel_read(supabase, channel["id"], user_id)


# =========================================================
# COMMUNITIES PAGE
# =========================================================

def communities_page(supabase, user_id):
    st.subheader("Communities")

    communities = load_communities(supabase)

    if not communities:
        st.info("No communities have been created yet.")
        return

    for community in communities:
        community_id = community["id"]

        with st.container(border=True):
            st.markdown(f"### 🌍 {community.get('name', 'Community')}")
            st.write(community.get("description") or "No description.")

            if community.get("location"):
                st.caption("📍 " + community["location"])

            groups = get_community_groups(
                supabase,
                community_id
            )

            channels = load_channels(
                supabase,
                community_id
            )

            st.caption(
                f"👥 {len(groups)} groups · "
                f"📢 {len(channels)} channels"
            )

            create_channel(
                supabase,
                community,
                user_id
            )

            group_tab, channel_tab = st.tabs([
                "Groups",
                "Channels"
            ])

            with group_tab:
                for group in groups:
                    st.write("👥 **" + group.get("name", "Group") + "**")

                    if is_member(supabase, group["id"], user_id):
                        if st.button(
                            "Open group",
                            key=f"community_open_{group['id']}"
                        ):
                            st.session_state["ecoloop_open_group_id"] = str(group["id"])
                            st.rerun()
                    else:
                        if st.button(
                            "Request to join",
                            key=f"community_join_{group['id']}"
                        ):
                            request_to_join(
                                supabase,
                                group["id"],
                                user_id
                            )

            with channel_tab:
                for channel in channels:
                    count = channel_unread_count(
                        supabase,
                        channel["id"],
                        user_id
                    )

                    st.markdown(
                        f"**📢 {channel.get('name', 'Channel')}**"
                    )

                    if channel.get("description"):
                        st.caption(channel["description"])

                    if count:
                        st.success(f"{count} unread announcements")

                    if st.button(
                        "Open channel",
                        key=f"open_channel_{channel['id']}"
                    ):
                        st.session_state[
                            "ecoloop_open_channel_id"
                        ] = str(channel["id"])
                        st.rerun()


# =========================================================
# PRIVATE ONE-TO-ONE CHATS
# =========================================================

def ordered_pair(user_a, user_b):
    return sorted([str(user_a), str(user_b)])


def load_direct_conversations(supabase, user_id):
    try:
        first = supabase.table(
            "direct_conversations"
        ).select("*").eq(
            "participant_one", user_id
        ).execute()

        second = supabase.table(
            "direct_conversations"
        ).select("*").eq(
            "participant_two", user_id
        ).execute()

        combined = rows(first) + rows(second)

        unique = {}

        for conversation in combined:
            unique[str(conversation["id"])] = conversation

        return list(unique.values())

    except Exception:
        return []


def get_or_create_direct_conversation(supabase, user_id, other_user_id):
    if str(user_id) == str(other_user_id):
        st.warning("You cannot start a chat with yourself.")
        return None

    one, two = ordered_pair(user_id, other_user_id)

    try:
        result = supabase.table(
            "direct_conversations"
        ).select("*").eq(
            "participant_one", one
        ).eq(
            "participant_two", two
        ).limit(1).execute()

        found = rows(result)

        if found:
            return found[0]

        result = supabase.table(
            "direct_conversations"
        ).insert({
            "participant_one": one,
            "participant_two": two,
            "created_by": user_id
        }).execute()

        created = rows(result)

        return created[0] if created else None

    except Exception as e:
        show_error(
            e,
            "Private chats need the additional database setup."
        )
        return None


def get_direct_messages(supabase, conversation_id, limit=200):
    try:
        result = supabase.table(
            "direct_messages"
        ).select("*").eq(
            "conversation_id", conversation_id
        ).order(
            "created_at", desc=True
        ).limit(limit).execute()

        return list(reversed(rows(result)))

    except Exception:
        return []


def get_direct_unread(supabase, conversation_id, user_id):
    try:
        status = supabase.table(
            "direct_read_status"
        ).select("last_read_at").eq(
            "conversation_id", conversation_id
        ).eq(
            "user_id", user_id
        ).limit(1).execute()

        found = rows(status)
        if not found:
            return 0

        last_read = found[0]["last_read_at"]

        messages = supabase.table(
            "direct_messages"
        ).select("id,sender_id").eq(
            "conversation_id", conversation_id
        ).gt(
            "created_at", last_read
        ).execute()

        return sum(
            1 for m in rows(messages)
            if str(m.get("sender_id")) != str(user_id)
        )

    except Exception:
        return 0


def mark_direct_read(supabase, conversation_id, user_id):
    try:
        supabase.table(
            "direct_read_status"
        ).upsert({
            "conversation_id": conversation_id,
            "user_id": user_id,
            "last_read_at": now_iso()
        }, on_conflict="conversation_id,user_id").execute()

    except Exception:
        pass


def send_direct_message(
    supabase,
    conversation_id,
    user_id,
    message_text,
    uploaded_file=None
):
    message_text = safe_text(message_text)

    if not message_text and not uploaded_file:
        st.warning("Write a message or attach a file.")
        return False

    data = {
        "conversation_id": conversation_id,
        "sender_id": user_id,
        "message_text": message_text
    }

    if uploaded_file:
        path = upload_media(
            supabase,
            uploaded_file,
            f"direct/{conversation_id}/{user_id}"
        )

        if not path:
            return False

        data.update({
            "attachment_path": path,
            "attachment_name": uploaded_file.name,
            "attachment_type": uploaded_file.type
        })

    try:
        supabase.table(
            "direct_messages"
        ).insert(data).execute()

        mark_direct_read(
            supabase,
            conversation_id,
            user_id
        )

        return True

    except Exception as e:
        show_error(e, "Private message could not be sent")
        return False


def direct_chat_workspace(supabase, conversation, user_id):
    conversation_id = conversation["id"]

    one = str(conversation["participant_one"])
    two = str(conversation["participant_two"])

    other_id = two if one == str(user_id) else one

    profile = get_profile(supabase, other_id)
    picture = profile_picture(supabase, profile)

    back, image_col, heading = st.columns([1, 1, 5])

    with back:
        if st.button("←", key=f"direct_back_{conversation_id}"):
            st.session_state["ecoloop_open_direct_id"] = None
            st.rerun()

    with image_col:
        if picture:
            st.image(picture, width=50)
        else:
            st.markdown("## 👤")

    with heading:
        st.markdown(f"**{profile_name(profile)}**")

        if profile.get("username"):
            st.caption("@" + profile["username"])

    st.divider()

    messages = get_direct_messages(
        supabase,
        conversation_id
    )

    profiles = get_profiles(
        supabase,
        [m.get("sender_id") for m in messages]
    )

    for message in messages:
        mine = str(message.get("sender_id")) == str(user_id)
        sender_profile = profiles.get(str(message.get("sender_id")))

        with st.container(border=True):
            st.caption(
                ("You" if mine else profile_name(sender_profile))
                + " · "
                + format_time(message.get("created_at"))
            )

            if message.get("deleted_at"):
                st.caption("Message deleted.")
            else:
                st.write(message.get("message_text") or "")

                display_attachment(
                    supabase,
                    message.get("attachment_path"),
                    message.get("attachment_name"),
                    message.get("attachment_type")
                )

    st.divider()

    with st.form(
        f"direct_form_{conversation_id}",
        clear_on_submit=True
    ):
        text = st.text_area(
            "Message",
            placeholder="Type a private message...",
            label_visibility="collapsed"
        )

        upload = st.file_uploader(
            "Attach media or document",
            key=f"direct_upload_{conversation_id}"
        )

        submitted = st.form_submit_button(
            "Send ➤",
            use_container_width=True
        )

        if submitted:
            if send_direct_message(
                supabase,
                conversation_id,
                user_id,
                text,
                upload
            ):
                st.rerun()

    mark_direct_read(
        supabase,
        conversation_id,
        user_id
    )


def direct_chats_page(supabase, user_id):
    st.subheader("Private chats")

    with st.expander("＋ Start a new chat", expanded=False):
        with st.form("start_private_chat"):
            other_user_id = st.text_input(
                "Enter the other member's EcoLoop user ID"
            )

            submitted = st.form_submit_button(
                "Start conversation",
                use_container_width=True
            )

            if submitted:
                if not other_user_id.strip():
                    st.warning("Enter a member user ID.")
                else:
                    conversation = get_or_create_direct_conversation(
                        supabase,
                        user_id,
                        other_user_id.strip()
                    )

                    if conversation:
                        st.session_state[
                            "ecoloop_open_direct_id"
                        ] = str(conversation["id"])
                        st.rerun()

    conversations = load_direct_conversations(
        supabase,
        user_id
    )

    if not conversations:
        st.info("Your private conversations will appear here.")
        return

    for conversation in conversations:
        one = str(conversation["participant_one"])
        two = str(conversation["participant_two"])

        other_id = two if one == str(user_id) else one

        profile = get_profile(supabase, other_id)
        picture = profile_picture(supabase, profile)

        messages = get_direct_messages(
            supabase,
            conversation["id"],
            1
        )

        latest = messages[-1] if messages else None

        count = get_direct_unread(
            supabase,
            conversation["id"],
            user_id
        )

        with st.container(border=True):
            left, middle, right = st.columns([1, 4, 1])

            with left:
                if picture:
                    st.image(picture, width=55)
                else:
                    st.markdown("## 👤")

            with middle:
                st.markdown(f"**{profile_name(profile)}**")
                st.caption(
                    message_preview(latest)
                    if latest else "Start a conversation"
                )

            with right:
                if count:
                    st.success(str(count))

            if st.button(
                "Open chat",
                key=f"open_direct_{conversation['id']}",
                use_container_width=True
            ):
                st.session_state[
                    "ecoloop_open_direct_id"
                ] = str(conversation["id"])
                st.rerun()


# =========================================================
# COMMUNITY HOME AND NAVIGATION
# =========================================================

def render_community_groups_page(supabase, user_id):

    if not user_id:
        st.warning("Please sign in to access EcoLoop Community.")
        return

    st.session_state["ecoloop_user_id"] = user_id

    # ---------------------------------------------
    # PRIVATE CHAT OPEN
    # ---------------------------------------------

    direct_id = st.session_state.get(
        "ecoloop_open_direct_id"
    )

    if direct_id:
        conversations = load_direct_conversations(
            supabase,
            user_id
        )

        conversation = next(
            (
                c for c in conversations
                if str(c.get("id")) == str(direct_id)
            ),
            None
        )

        if conversation:
            direct_chat_workspace(
                supabase,
                conversation,
                user_id
            )
        else:
            st.error("Private conversation unavailable.")
            st.session_state["ecoloop_open_direct_id"] = None

        return

    # ---------------------------------------------
    # GROUP CHAT OPEN
    # ---------------------------------------------

    group_id = st.session_state.get(
        "ecoloop_open_group_id"
    )

    if group_id:
        group_workspace(
            supabase,
            group_id,
            user_id
        )
        return

    # ---------------------------------------------
    # CHANNEL OPEN
    # ---------------------------------------------

    channel_id = st.session_state.get(
        "ecoloop_open_channel_id"
    )

    if channel_id:
        channels = safe_query_table(
            supabase,
            "community_channels"
        )

        channel = next(
            (
                c for c in channels
                if str(c.get("id")) == str(channel_id)
            ),
            None
        )

        if channel:
            if st.button("← Back to Community"):
                st.session_state["ecoloop_open_channel_id"] = None
                st.rerun()

            channel_workspace(
                supabase,
                channel,
                user_id
            )
        else:
            st.error("Channel unavailable.")
            st.session_state["ecoloop_open_channel_id"] = None

        return

    # ---------------------------------------------
    # INVITATION LINK
    # ---------------------------------------------

    invite_code = st.query_params.get("invite")

    if invite_code:
        st.title("🔗 EcoLoop invitation")

        redeem_invitation(
            supabase,
            user_id,
            str(invite_code).upper()
        )

        if st.button("Back to Community"):
            st.query_params.clear()
            st.rerun()

        return

    # ---------------------------------------------
    # MAIN COMMUNITY HOME
    # ---------------------------------------------

    st.title("🌍 EcoLoop Community")
    st.caption("Connect · Share · Learn · Take action")

    groups = get_my_groups(supabase, user_id)

    unread_total = sum(
        get_group_unread(supabase, g["id"], user_id)
        for g in groups
    )

    if unread_total:
        st.info(f"💬 {unread_total} unread group messages")

    tabs = st.tabs([
        "💬 Chats",
        "👥 Groups",
        "🌍 Communities",
        "📢 Channels",
        "👤 Profile",
        "🔗 Join"
    ])

    # CHATS
    with tabs[0]:
        chat_type = st.radio(
            "Conversation type",
            ["All chats", "Private chats", "Group chats"],
            horizontal=True,
            key="community_chat_filter"
        )

        if chat_type in ["All chats", "Private chats"]:
            direct_chats_page(
                supabase,
                user_id
            )

        if chat_type in ["All chats", "Group chats"]:
            st.divider()
            my_groups_page(
                supabase,
                user_id
            )

    # GROUPS
    with tabs[1]:
        discover_groups_page(
            supabase,
            user_id
        )

    # COMMUNITIES
    with tabs[2]:
        create_community(
            supabase,
            user_id
        )

        communities_page(
            supabase,
            user_id
        )

    # CHANNELS
    with tabs[3]:
        communities = load_communities(supabase)

        if not communities:
            st.info("Create or join a community to access its channels.")

        for community in communities:
            st.markdown(f"### 🌍 {community.get('name', 'Community')}")

            for channel in load_channels(supabase, community["id"]):
                count = channel_unread_count(
                    supabase,
                    channel["id"],
                    user_id
                )

                with st.container(border=True):
                    st.markdown(
                        f"**📢 {channel.get('name', 'Channel')}**"
                    )

                    st.caption(
                        channel.get("description") or "Announcements"
                    )

                    if count:
                        st.success(f"{count} unread")

                    if st.button(
                        "Open channel",
                        key=f"channel_home_{channel['id']}"
                    ):
                        st.session_state[
                            "ecoloop_open_channel_id"
                        ] = str(channel["id"])
                        st.rerun()

    # PROFILE
    with tabs[4]:
        profile_editor(
            supabase,
            user_id
        )

    # JOIN
    with tabs[5]:
        redeem_invitation(
            supabase,
            user_id
        )
