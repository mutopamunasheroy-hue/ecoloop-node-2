import streamlit as st
import uuid
import mimetypes
from datetime import datetime, timezone, timedelta

BUCKET = "community-media"
MAX_FILE_SIZE = 100 * 1024 * 1024
ADMIN_ROLES = ("admin", "group_admin", "owner", "moderator")
REACTIONS = ["👍", "❤️", "😂", "😮", "😢", "🔥", "👏"]


# ============================================================
# ECOLOOP COMMUNITY — DESIGN
# ============================================================

def community_styles():
    st.markdown("""
    <style>
    .eco-hero {
        padding: 24px 20px;
        border-radius: 20px;
        background: linear-gradient(125deg,#073b35,#087e65,#16a085);
        color: white;
        margin-bottom: 18px;
    }
    .eco-hero h1 {
        color: white;
        font-size: 28px;
        margin-bottom: 5px;
    }
    .eco-hero p {
        color: #d9fff1;
        margin: 0;
    }
    .eco-card {
        padding: 17px;
        border-radius: 17px;
        background: rgba(20,150,110,.09);
        border: 1px solid rgba(30,160,120,.25);
        min-height: 105px;
        margin-bottom: 8px;
    }
    .eco-card-icon {
        font-size: 27px;
        margin-bottom: 7px;
    }
    .eco-card-title {
        font-size: 16px;
        font-weight: 700;
    }
    .eco-card-sub {
        font-size: 12px;
        opacity: .75;
    }
    .eco-section {
        font-size: 19px;
        font-weight: 750;
        margin-top: 18px;
        margin-bottom: 8px;
    }
    .eco-story {
        padding: 12px 8px;
        border-radius: 15px;
        border: 1px solid rgba(20,160,120,.4);
        text-align: center;
        min-height: 88px;
    }
    .eco-avatar {
        font-size: 30px;
    }
    </style>
    """, unsafe_allow_html=True)


# ============================================================
# GENERAL HELPERS
# ============================================================

def rows(response):
    return response.data if response and response.data else []


def safe_text(value, default=""):
    return str(value or default).strip()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def show_error(error, title="Something went wrong"):
    st.error(f"{title}: {error}")


def format_time(value):
    if not value:
        return ""

    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        dt = dt.astimezone()

        if dt.date() == datetime.now().astimezone().date():
            return dt.strftime("%H:%M")

        return dt.strftime("%d %b")

    except Exception:
        return ""


def format_full_time(value):
    if not value:
        return ""

    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.astimezone().strftime("%d %b %Y · %H:%M")
    except Exception:
        return ""


def safe_query_table(supabase, table, columns="*"):
    try:
        return rows(
            supabase.table(table).select(columns).execute()
        )
    except Exception:
        return []


def get_profiles(supabase, user_ids):
    ids = list(set(str(x) for x in user_ids if x))

    if not ids:
        return {}

    try:
        result = supabase.table("member_profiles").select("*").in_(
            "user_id", ids
        ).execute()

        return {
            str(p["user_id"]): p
            for p in rows(result)
        }
    except Exception:
        return {}


def get_profile(supabase, user_id):
    try:
        result = supabase.table("member_profiles").select("*").eq(
            "user_id", user_id
        ).limit(1).execute()

        found = rows(result)
        return found[0] if found else {}
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
        show_error(e, "Upload failed")
        return None


def media_url(supabase, path):
    if not path:
        return None

    if str(path).startswith("http"):
        return path

    try:
        result = supabase.storage.from_(BUCKET).create_signed_url(
            path, 3600
        )
        return result.get("signedURL") or result.get("signedUrl")
    except Exception:
        return None


def display_attachment(supabase, path, name=None, file_type=None):
    if not path:
        return

    url = media_url(supabase, path)

    if not url:
        st.caption("Attachment unavailable.")
        return

    file_type = file_type or ""
    name = name or "Attachment"

    if file_type.startswith("image/"):
        st.image(url, use_container_width=True)
    elif file_type.startswith("video/"):
        st.video(url)
    elif file_type.startswith("audio/"):
        st.audio(url)
    else:
        st.markdown(f"[📎 {name}]({url})")


def get_group(supabase, group_id):
    try:
        found = rows(
            supabase.table("community_groups").select("*").eq(
                "id", group_id
            ).limit(1).execute()
        )
        return found[0] if found else None
    except Exception:
        return None


def get_community(supabase, community_id):
    try:
        found = rows(
            supabase.table("communities").select("*").eq(
                "id", community_id
            ).limit(1).execute()
        )
        return found[0] if found else None
    except Exception:
        return None


# ============================================================
# PROFILE SYSTEM
# ============================================================

def profile_picture(supabase, profile):
    if not profile:
        return None
    return media_url(supabase, profile.get("avatar_url"))


def profile_editor(supabase, user_id):
    st.subheader("My profile")

    profile = get_profile(supabase, user_id)
    picture = profile_picture(supabase, profile)

    if picture:
        st.image(picture, width=115)

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
        avatar = st.file_uploader(
            "Upload profile picture",
            type=["png", "jpg", "jpeg"],
            key="community_profile_avatar"
        )

        avatar_url = st.text_input(
            "Or enter picture URL",
            value=profile.get("avatar_url", "")
        )

        submitted = st.form_submit_button(
            "Save profile",
            use_container_width=True
        )

        if submitted:
            if avatar:
                path = upload_media(
                    supabase, avatar, f"profiles/{user_id}"
                )
                if path:
                    avatar_url = path

            try:
                supabase.table("member_profiles").upsert({
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

# ============================================================
# PART 2 — GROUPS, MEMBERSHIPS AND GROUP MESSAGING
# ============================================================

def get_group_membership(supabase, group_id, user_id):
    try:
        result = (
            supabase.table("group_memberships")
            .select("*")
            .eq("group_id", group_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None
    except Exception:
        return None


def get_group_members(supabase, group_id):
    try:
        result = (
            supabase.table("group_memberships")
            .select("*")
            .eq("group_id", group_id)
            .eq("status", "approved")
            .eq("group_id", group_id)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def is_group_admin(supabase, group_id, user_id):
    membership = get_group_membership(supabase, group_id, user_id)

    if not membership:
        return False

    return (
        membership.get("status") == "approved"
        and membership.get("membership_role") in ["admin", "creator", "owner"]
    )


def load_communities(supabase):
    try:
        result = (
            supabase.table("communities")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def load_groups(supabase, community_id=None):
    try:
        query = (
            supabase.table("community_groups")
            .select("*")
            .order("created_at", desc=True)
        )

        if community_id:
            query = query.eq("community_id", community_id)

        result = query.execute()
        return result.data or []
    except Exception:
        return []


def create_community(supabase, user_id, name, description, location=""):
    try:
        result = (
            supabase.table("communities")
            .insert({
                "name": name.strip(),
                "description": description.strip(),
                "location": location.strip(),
                "created_by": user_id
            })
            .execute()
        )

        return bool(result.data), result.data
    except Exception as error:
        st.error(f"Could not create community: {error}")
        return False, None


def create_group(
    supabase,
    user_id,
    name,
    description,
    community_id=None,
    location=""
):
    try:
        payload = {
            "name": name.strip(),
            "description": description.strip(),
            "created_by": user_id,
            "location": location.strip()
        }

        if community_id:
            payload["community_id"] = community_id

        result = (
            supabase.table("community_groups")
            .insert(payload)
            .execute()
        )

        if not result.data:
            return False, None

        group = result.data[0]

        supabase.table("group_memberships").insert({
            "group_id": group["id"],
            "user_id": user_id,
            "membership_role": "admin",
            "status": "approved"
        }).execute()

        return True, group

    except Exception as error:
        st.error(f"Could not create group: {error}")
        return False, None


def request_group_membership(supabase, group_id, user_id):
    existing = get_group_membership(supabase, group_id, user_id)

    if existing:
        return False, "You already have a membership request or membership."

    try:
        supabase.table("group_memberships").insert({
            "group_id": group_id,
            "user_id": user_id,
            "membership_role": "member",
            "status": "pending"
        }).execute()

        return True, "Your request has been sent."
    except Exception as error:
        return False, str(error)


def approve_group_member(supabase, membership_id):
    try:
        supabase.table("group_memberships").update({
            "status": "approved"
        }).eq("id", membership_id).execute()

        return True
    except Exception as error:
        st.error(f"Could not approve member: {error}")
        return False


def remove_group_member(supabase, membership_id):
    try:
        supabase.table("group_memberships").delete().eq(
            "id", membership_id
        ).execute()

        return True
    except Exception as error:
        st.error(f"Could not remove member: {error}")
        return False


def load_group_messages(supabase, group_id, limit=100):
    try:
        result = (
            supabase.table("group_messages")
            .select("*")
            .eq("group_id", group_id)
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def mark_group_as_read(supabase, group_id, user_id):
    try:
        existing = (
            supabase.table("group_read_status")
            .select("id")
            .eq("group_id", group_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()

        if existing.data:
            supabase.table("group_read_status").update({
                "last_read_at": now
            }).eq("id", existing.data[0]["id"]).execute()
        else:
            supabase.table("group_read_status").insert({
                "group_id": group_id,
                "user_id": user_id,
                "last_read_at": now
            }).execute()

    except Exception:
        pass


def get_group_unread_count(supabase, group_id, user_id):
    try:
        status = (
            supabase.table("group_read_status")
            .select("last_read_at")
            .eq("group_id", group_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        if not status.data:
            return len(load_group_messages(supabase, group_id))

        last_read = status.data[0].get("last_read_at")

        if not last_read:
            return 0

        result = (
            supabase.table("group_messages")
            .select("id", count="exact")
            .eq("group_id", group_id)
            .gt("created_at", last_read)
            .neq("sender_id", user_id)
            .execute()
        )

        return result.count or 0

    except Exception:
        return 0


def send_group_message(
    supabase,
    group_id,
    user_id,
    message_text,
    attachment_path=None,
    attachment_name=None,
    attachment_type=None
):
    try:
        payload = {
            "group_id": group_id,
            "sender_id": user_id,
            "message_text": message_text.strip()
        }

        if attachment_path:
            payload["attachment_path"] = attachment_path
            payload["attachment_name"] = attachment_name
            payload["attachment_type"] = attachment_type

        result = (
            supabase.table("group_messages")
            .insert(payload)
            .execute()
        )

        return bool(result.data)

    except Exception as error:
        st.error(f"Message could not be sent: {error}")
        return False


def add_group_reaction(supabase, message_id, user_id, reaction):
    try:
        supabase.table("group_message_reactions").insert({
            "message_id": message_id,
            "user_id": user_id,
            "reaction": reaction
        }).execute()

        return True

    except Exception:
        return False


def load_group_reactions(supabase, message_id):
    try:
        result = (
            supabase.table("group_message_reactions")
            .select("*")
            .eq("message_id", message_id)
            .execute()
        )

        return result.data or []

    except Exception:
        return []


def render_group_message(supabase, message, user_id):
    sender_id = message.get("sender_id")
    own_message = sender_id == user_id

    profile = get_member_profile(supabase, sender_id)

    sender_name = (
        profile.get("display_name")
        or profile.get("username")
        or "EcoLoop member"
    ) if profile else "EcoLoop member"

    message_text = message.get("message_text") or ""
    created_at = message.get("created_at", "")

    with st.container(border=True):
        header_col, time_col = st.columns([4, 2])

        with header_col:
            if own_message:
                st.caption("You")
            else:
                st.caption(sender_name)

        with time_col:
            st.caption(created_at[:16].replace("T", " ") if created_at else "")

        if message_text:
            st.write(message_text)

        attachment_path = message.get("attachment_path")

        if attachment_path:
            render_community_attachment(
                attachment_path,
                message.get("attachment_name"),
                message.get("attachment_type")
            )

        reactions = load_group_reactions(
            supabase,
            message.get("id")
        )

        if reactions:
            reaction_counts = {}

            for item in reactions:
                emoji = item.get("reaction", "👍")
                reaction_counts[emoji] = reaction_counts.get(emoji, 0) + 1

            st.caption(
                "   ".join(
                    f"{emoji} {count}"
                    for emoji, count in reaction_counts.items()
                )
            )

        reaction_col1, reaction_col2, reaction_col3 = st.columns(3)

        for column, emoji in zip(
            [reaction_col1, reaction_col2, reaction_col3],
            ["👍", "❤️", "😂"]
        ):
            with column:
                if st.button(
                    emoji,
                    key=f"group_reaction_{message.get('id')}_{emoji}"
                ):
                    add_group_reaction(
                        supabase,
                        message.get("id"),
                        user_id,
                        emoji
                    )
                    st.rerun()


def render_group_chat_composer(supabase, group_id, user_id):
    with st.form(
        key=f"group_message_form_{group_id}",
        clear_on_submit=True
    ):
        message = st.text_area(
            "Message",
            placeholder="Write a message...",
            label_visibility="collapsed",
            height=80
        )

        attachment = st.file_uploader(
            "Attach a file",
            key=f"group_attachment_{group_id}"
        )

        submitted = st.form_submit_button(
            "Send message",
            use_container_width=True
        )

        if submitted:
            attachment_path = None
            attachment_name = None
            attachment_type = None

            if attachment:
                uploaded = upload_community_media(
                    supabase,
                    attachment,
                    user_id
                )

                if uploaded:
                    attachment_path = uploaded
                    attachment_name = attachment.name
                    attachment_type = attachment.type

            if message.strip() or attachment_path:
                success = send_group_message(
                    supabase,
                    group_id,
                    user_id,
                    message,
                    attachment_path,
                    attachment_name,
                    attachment_type
                )

                if success:
                    st.rerun()

# ============================================================
# PART 3 — GROUP PROFILES, ADMIN TOOLS AND PRIVATE CHATS
# ============================================================

def render_group_members(supabase, group_id, user_id):
    st.subheader("Group members")

    members = get_group_members(supabase, group_id)

    if not members:
        st.info("No approved members yet.")
        return

    current_user_admin = is_group_admin(
        supabase, group_id, user_id
    )

    for member in members:
        member_id = member.get("user_id")
        profile = get_member_profile(supabase, member_id)

        name = (
            profile.get("display_name")
            or profile.get("username")
            or "EcoLoop member"
        ) if profile else "EcoLoop member"

        role = member.get("membership_role", "member")

        with st.container(border=True):
            col1, col2 = st.columns([4, 1])

            with col1:
                st.write(f"**{name}**")
                st.caption(role.title())

            with col2:
                if current_user_admin and member_id != user_id:
                    if st.button(
                        "Remove",
                        key=f"remove_member_{member.get('id')}"
                    ):
                        if remove_group_member(
                            supabase, member.get("id")
                        ):
                            st.success("Member removed.")
                            st.rerun()


def render_group_admin_requests(supabase, group_id):
    st.subheader("Membership requests")

    try:
        result = (
            supabase.table("group_memberships")
            .select("*")
            .eq("group_id", group_id)
            .eq("status", "pending")
            .execute()
        )

        requests = result.data or []

    except Exception:
        st.warning("Could not load membership requests.")
        return

    if not requests:
        st.caption("There are no pending requests.")
        return

    for request in requests:
        profile = get_member_profile(
            supabase, request.get("user_id")
        )

        name = (
            profile.get("display_name")
            or profile.get("username")
            or "New member"
        ) if profile else "New member"

        with st.container(border=True):
            st.write(f"**{name}**")

            if st.button(
                "Approve request",
                key=f"approve_request_{request.get('id')}",
                use_container_width=True
            ):
                if approve_group_member(
                    supabase, request.get("id")
                ):
                    st.success("Member approved.")
                    st.rerun()


def render_group_profile(supabase, group, user_id):
    group_id = group.get("id")

    st.subheader(group.get("name", "Group"))

    if group.get("image_url"):
        st.image(
            group["image_url"],
            use_container_width=True
        )

    st.write(group.get("description") or "No description added.")

    if group.get("location"):
        st.caption(f"📍 {group['location']}")

    members = get_group_members(supabase, group_id)

    st.caption(f"👥 {len(members)} approved members")

    membership = get_group_membership(
        supabase, group_id, user_id
    )

    if not membership:
        if st.button(
            "Join group",
            key=f"join_group_{group_id}",
            use_container_width=True
        ):
            success, message = request_group_membership(
                supabase, group_id, user_id
            )

            if success:
                st.success(message)
            else:
                st.info(message)

            st.rerun()

        return

    if membership.get("status") == "pending":
        st.info("Your membership request is awaiting approval.")
        return

    if membership.get("status") != "approved":
        st.info("You are not an approved member of this group.")
        return

    st.success("You are a member of this group.")


def render_group_workspace(supabase, group, user_id):
    group_id = group.get("id")

    st.markdown(f"## {group.get('name', 'Group')}")

    description = group.get("description") or ""
    if description:
        st.caption(description)

    tab_chat, tab_members, tab_admin = st.tabs([
        "💬 Chat",
        "👥 Members",
        "⚙️ Manage"
    ])

    with tab_chat:
        mark_group_as_read(supabase, group_id, user_id)

        messages = load_group_messages(supabase, group_id)

        if not messages:
            st.info("No messages yet. Start the conversation.")

        for message in messages:
            render_group_message(
                supabase, message, user_id
            )

        render_group_chat_composer(
            supabase, group_id, user_id
        )

    with tab_members:
        render_group_members(
            supabase, group_id, user_id
        )

    with tab_admin:
        if is_group_admin(supabase, group_id, user_id):
            render_group_admin_requests(
                supabase, group_id
            )
        else:
            st.info("Group management is available to admins.")


# ============================================================
# PRIVATE CONVERSATIONS
# ============================================================

def get_direct_conversation(
    supabase, user_one, user_two
):
    try:
        result = (
            supabase.table("direct_conversations")
            .select("*")
            .or_(
                f"and(participant_one.eq.{user_one},"
                f"participant_two.eq.{user_two}),"
                f"and(participant_one.eq.{user_two},"
                f"participant_two.eq.{user_one})"
            )
            .limit(1)
            .execute()
        )

        return result.data[0] if result.data else None

    except Exception:
        return None


def create_direct_conversation(
    supabase, user_one, user_two
):
    existing = get_direct_conversation(
        supabase, user_one, user_two
    )

    if existing:
        return existing

    try:
        result = (
            supabase.table("direct_conversations")
            .insert({
                "participant_one": user_one,
                "participant_two": user_two,
                "created_by": user_one
            })
            .execute()
        )

        return result.data[0] if result.data else None

    except Exception as error:
        st.error(f"Could not start conversation: {error}")
        return None


def load_direct_messages(
    supabase, conversation_id, limit=100
):
    try:
        result = (
            supabase.table("direct_messages")
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )

        return result.data or []

    except Exception:
        return []


def send_direct_message(
    supabase,
    conversation_id,
    user_id,
    message_text
):
    try:
        result = (
            supabase.table("direct_messages")
            .insert({
                "conversation_id": conversation_id,
                "sender_id": user_id,
                "message_text": message_text.strip()
            })
            .execute()
        )

        return bool(result.data)

    except Exception as error:
        st.error(f"Message could not be sent: {error}")
        return False


def mark_direct_as_read(
    supabase, conversation_id, user_id
):
    try:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()

        existing = (
            supabase.table("direct_read_status")
            .select("id")
            .eq("conversation_id", conversation_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        if existing.data:
            supabase.table("direct_read_status").update({
                "last_read_at": now
            }).eq("id", existing.data[0]["id"]).execute()

        else:
            supabase.table("direct_read_status").insert({
                "conversation_id": conversation_id,
                "user_id": user_id,
                "last_read_at": now
            }).execute()

    except Exception:
        pass


def get_direct_unread_count(
    supabase, conversation_id, user_id
):
    try:
        status = (
            supabase.table("direct_read_status")
            .select("last_read_at")
            .eq("conversation_id", conversation_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        if not status.data:
            messages = load_direct_messages(
                supabase, conversation_id
            )
            return sum(
                1 for message in messages
                if message.get("sender_id") != user_id
            )

        last_read = status.data[0].get("last_read_at")

        if not last_read:
            return 0

        result = (
            supabase.table("direct_messages")
            .select("id", count="exact")
            .eq("conversation_id", conversation_id)
            .gt("created_at", last_read)
            .neq("sender_id", user_id)
            .execute()
        )

        return result.count or 0

    except Exception:
        return 0


def render_direct_message(
    supabase, message, user_id
):
    own_message = message.get("sender_id") == user_id

    profile = get_member_profile(
        supabase, message.get("sender_id")
    )

    sender_name = (
        profile.get("display_name")
        or profile.get("username")
        or "EcoLoop member"
    ) if profile else "EcoLoop member"

    timestamp = message.get("created_at", "")

    with st.container(border=True):
        if own_message:
            st.caption("You")
        else:
            st.caption(sender_name)

        st.write(message.get("message_text") or "")

        if timestamp:
            st.caption(
                timestamp[:16].replace("T", " ")
            )


def render_direct_chat_composer(
    supabase, conversation_id, user_id
):
    with st.form(
        key=f"direct_message_form_{conversation_id}",
        clear_on_submit=True
    ):
        message = st.text_area(
            "Message",
            placeholder="Write a message...",
            label_visibility="collapsed",
            height=75
        )

        submitted = st.form_submit_button(
            "Send",
            use_container_width=True
        )

        if submitted and message.strip():
            if send_direct_message(
                supabase,
                conversation_id,
                user_id,
                message
            ):
                st.rerun()


def render_direct_chat(
    supabase, conversation, user_id, other_user_id
):
    conversation_id = conversation.get("id")

    profile = get_member_profile(
        supabase, other_user_id
    )

    other_name = (
        profile.get("display_name")
        or profile.get("username")
        or "EcoLoop member"
    ) if profile else "EcoLoop member"

    st.markdown(f"### 💬 {other_name}")

    if profile and profile.get("avatar_url"):
        st.image(
            profile["avatar_url"],
            width=75
        )

    mark_direct_as_read(
        supabase, conversation_id, user_id
    )

    messages = load_direct_messages(
        supabase, conversation_id
    )

    if not messages:
        st.info("This conversation is empty. Say hello!")

    for message in messages:
        render_direct_message(
            supabase, message, user_id
        )

    render_direct_chat_composer(
        supabase, conversation_id, user_id
            )

# ============================================================
# PART 4 — COMMUNITY HOME, CHAT LIST, CHANNELS AND STORIES
# ============================================================

def get_other_conversation_user(conversation, user_id):
    if conversation.get("participant_one") == user_id:
        return conversation.get("participant_two")

    return conversation.get("participant_one")


def load_user_conversations(supabase, user_id):
    try:
        result = (
            supabase.table("direct_conversations")
            .select("*")
            .or_(
                f"participant_one.eq.{user_id},"
                f"participant_two.eq.{user_id}"
            )
            .order("created_at", desc=True)
            .execute()
        )

        return result.data or []

    except Exception:
        return []


def get_last_direct_message(supabase, conversation_id):
    try:
        result = (
            supabase.table("direct_messages")
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        return result.data[0] if result.data else None

    except Exception:
        return None


def get_last_group_message(supabase, group_id):
    try:
        result = (
            supabase.table("group_messages")
            .select("*")
            .eq("group_id", group_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        return result.data[0] if result.data else None

    except Exception:
        return None


def format_chat_time(timestamp):
    if not timestamp:
        return ""

    try:
        from datetime import datetime

        value = datetime.fromisoformat(
            timestamp.replace("Z", "+00:00")
        )

        return value.strftime("%H:%M")

    except Exception:
        return timestamp[:10]


def render_direct_chat_list(supabase, user_id):
    conversations = load_user_conversations(
        supabase, user_id
    )

    if not conversations:
        st.info(
            "Your private conversations will appear here. "
            "Find a member and start chatting."
        )
        return

    for conversation in conversations:
        other_id = get_other_conversation_user(
            conversation, user_id
        )

        if not other_id:
            continue

        profile = get_member_profile(
            supabase, other_id
        )

        name = (
            profile.get("display_name")
            or profile.get("username")
            or "EcoLoop member"
        ) if profile else "EcoLoop member"

        last_message = get_last_direct_message(
            supabase, conversation.get("id")
        )

        preview = (
            last_message.get("message_text")
            if last_message else "Start a conversation"
        )

        unread = get_direct_unread_count(
            supabase, conversation.get("id"), user_id
        )

        avatar = (
            profile.get("avatar_url")
            if profile else None
        )

        with st.container(border=True):
            col1, col2, col3 = st.columns([1, 4, 1])

            with col1:
                if avatar:
                    st.image(avatar, width=48)
                else:
                    st.markdown("👤")

            with col2:
                st.markdown(f"**{name}**")
                st.caption(str(preview or "")[:65])

            with col3:
                if unread:
                    st.markdown(f"**{unread}**")

                if st.button(
                    "Open",
                    key=f"open_direct_{conversation.get('id')}"
                ):
                    st.session_state["community_active_chat"] = {
                        "type": "direct",
                        "conversation": conversation,
                        "other_user_id": other_id
                    }
                    st.rerun()


def render_group_chat_list(supabase, user_id):
    try:
        result = (
            supabase.table("group_memberships")
            .select("*")
            .eq("user_id", user_id)
            .eq("status", "approved")
            .execute()
        )

        memberships = result.data or []

    except Exception:
        st.warning("Could not load your groups.")
        return

    if not memberships:
        st.info("Groups you join will appear here.")
        return

    for membership in memberships:
        group_id = membership.get("group_id")

        try:
            group_result = (
                supabase.table("community_groups")
                .select("*")
                .eq("id", group_id)
                .limit(1)
                .execute()
            )

            group = (
                group_result.data[0]
                if group_result.data else None
            )

        except Exception:
            group = None

        if not group:
            continue

        last_message = get_last_group_message(
            supabase, group_id
        )

        preview = (
            last_message.get("message_text")
            if last_message else "No messages yet"
        )

        unread = get_group_unread_count(
            supabase, group_id, user_id
        )

        with st.container(border=True):
            col1, col2, col3 = st.columns([1, 4, 1])

            with col1:
                if group.get("image_url"):
                    st.image(
                        group["image_url"],
                        width=48
                    )
                else:
                    st.markdown("👥")

            with col2:
                st.markdown(
                    f"**{group.get('name', 'Group')}**"
                )
                st.caption(str(preview or "")[:65])

            with col3:
                if unread:
                    st.markdown(f"**{unread}**")

                if st.button(
                    "Open",
                    key=f"open_group_{group_id}"
                ):
                    st.session_state[
                        "community_active_group"
                    ] = group
                    st.rerun()


def render_chats_page(supabase, user_id):
    st.markdown("## 💬 Chats")

    active_chat = st.session_state.get(
        "community_active_chat"
    )

    if active_chat:
        if st.button("← Back to chats"):
            st.session_state.pop(
                "community_active_chat", None
            )
            st.rerun()

        if active_chat.get("type") == "direct":
            render_direct_chat(
                supabase,
                active_chat["conversation"],
                user_id,
                active_chat["other_user_id"]
            )

        return

    direct_tab, group_tab = st.tabs([
        "Private chats",
        "Group chats"
    ])

    with direct_tab:
        render_direct_chat_list(supabase, user_id)

    with group_tab:
        render_group_chat_list(supabase, user_id)


def render_groups_page(supabase, user_id):
    st.markdown("## 👥 Groups")

    active_group = st.session_state.get(
        "community_active_group"
    )

    if active_group:
        if st.button("← Back to groups"):
            st.session_state.pop(
                "community_active_group", None
            )
            st.rerun()

        membership = get_group_membership(
            supabase, active_group.get("id"), user_id
        )

        if membership and membership.get("status") == "approved":
            render_group_workspace(
                supabase, active_group, user_id
            )
        else:
            render_group_profile(
                supabase, active_group, user_id
            )

        return

    create_tab, discover_tab, my_tab = st.tabs([
        "Create group",
        "Discover groups",
        "My groups"
    ])

    with create_tab:
        st.write("Create a space for people with shared interests.")

        with st.form("create_ecoloop_group"):
            name = st.text_input("Group name")
            description = st.text_area("Description")
            location = st.text_input("Location")

            communities = load_communities(supabase)

            community_options = {
                "No community": None
            }

            for community in communities:
                community_options[
                    community.get("name", "Community")
                ] = community.get("id")

            selected_community = st.selectbox(
                "Connect to a community",
                list(community_options.keys())
            )

            submitted = st.form_submit_button(
                "Create group",
                use_container_width=True
            )

            if submitted:
                if not name.strip():
                    st.warning("Enter a group name.")
                else:
                    success, group = create_group(
                        supabase,
                        user_id,
                        name,
                        description,
                        community_options[selected_community],
                        location
                    )

                    if success:
                        st.success("Your group has been created.")
                        st.rerun()

    with discover_tab:
        groups = load_groups(supabase)

        if not groups:
            st.info("No groups have been created yet.")

        for group in groups:
            with st.container(border=True):
                st.markdown(
                    f"**{group.get('name', 'Group')}**"
                )

                st.write(
                    group.get("description")
                    or "No description available."
                )

                if st.button(
                    "View group",
                    key=f"discover_group_{group.get('id')}",
                    use_container_width=True
                ):
                    st.session_state[
                        "community_active_group"
                    ] = group
                    st.rerun()

    with my_tab:
        render_group_chat_list(supabase, user_id)


# ============================================================
# COMMUNITIES
# ============================================================

def render_communities_page(supabase, user_id):
    st.markdown("## 🌍 Communities")

    create_tab, explore_tab = st.tabs([
        "Create community",
        "Explore communities"
    ])

    with create_tab:
        with st.form("create_ecoloop_community"):
            name = st.text_input("Community name")
            description = st.text_area("What is this community about?")
            location = st.text_input("Location")

            submitted = st.form_submit_button(
                "Create community",
                use_container_width=True
            )

            if submitted:
                if not name.strip():
                    st.warning("Enter a community name.")
                else:
                    success, data = create_community(
                        supabase,
                        user_id,
                        name,
                        description,
                        location
                    )

                    if success:
                        st.success("Community created.")
                        st.rerun()

    with explore_tab:
        communities = load_communities(supabase)

        if not communities:
            st.info("No communities available yet.")

        for community in communities:
            with st.container(border=True):
                if community.get("image_url"):
                    st.image(
                        community["image_url"],
                        use_container_width=True
                    )

                st.markdown(
                    f"**{community.get('name', 'Community')}**"
                )

                st.write(
                    community.get("description")
                    or "No description added."
                )

                if community.get("location"):
                    st.caption(
                        f"📍 {community['location']}"
                    )

                community_groups = load_groups(
                    supabase,
                    community.get("id")
                )

                st.caption(
                    f"{len(community_groups)} groups"
                )

                if st.button(
                    "View its groups",
                    key=f"community_groups_{community.get('id')}"
                ):
                    st.session_state[
                        "community_selected_community"
                    ] = community
                    st.rerun()

        selected = st.session_state.get(
            "community_selected_community"
        )

        if selected:
            st.divider()
            st.subheader(
                f"Groups in {selected.get('name')}"
            )

            if st.button("← Back to communities"):
                st.session_state.pop(
                    "community_selected_community", None
                )
                st.rerun()

            for group in load_groups(
                supabase, selected.get("id")
            ):
                with st.container(border=True):
                    st.markdown(
                        f"**{group.get('name', 'Group')}**"
                    )
                    st.write(
                        group.get("description") or ""
                    )

                    if st.button(
                        "Open group",
                        key=f"community_open_group_{group.get('id')}"
                    ):
                        st.session_state[
                            "community_active_group"
                        ] = group
                        st.session_state[
                            "community_page"
                        ] = "Groups"
                        st.rerun()


# ============================================================
# CHANNELS
# ============================================================

def load_community_channels(supabase, community_id=None):
    try:
        query = (
            supabase.table("community_channels")
            .select("*")
            .eq("is_active", True)
            .order("created_at", desc=True)
        )

        if community_id:
            query = query.eq("community_id", community_id)

        result = query.execute()
        return result.data or []

    except Exception:
        return []


def load_channel_messages(supabase, channel_id):
    try:
        result = (
            supabase.table("channel_messages")
            .select("*")
            .eq("channel_id", channel_id)
            .order("created_at", desc=False)
            .limit(100)
            .execute()
        )

        return result.data or []

    except Exception:
        return []


def send_channel_message(
    supabase, channel_id, user_id, message_text
):
    try:
        supabase.table("channel_messages").insert({
            "channel_id": channel_id,
            "sender_id": user_id,
            "message_text": message_text.strip()
        }).execute()

        return True

    except Exception as error:
        st.error(f"Could not publish announcement: {error}")
        return False


def render_channels_page(supabase, user_id):
    st.markdown("## 📢 Channels")
    st.caption(
        "Announcements and updates from EcoLoop communities."
    )

    channels = load_community_channels(supabase)

    if not channels:
        st.info("No channels are available yet.")
        return

    for channel in channels:
        channel_id = channel.get("id")

        with st.expander(
            f"📢 {channel.get('name', 'Channel')}"
        ):
            st.write(
                channel.get("description") or ""
            )

            messages = load_channel_messages(
                supabase, channel_id
            )

            if not messages:
                st.caption("No announcements yet.")

            for message in messages:
                profile = get_member_profile(
                    supabase,
                    message.get("sender_id")
                )

                sender = (
                    profile.get("display_name")
                    or profile.get("username")
                    or "Community admin"
                ) if profile else "Community admin"

                with st.container(border=True):
                    st.caption(sender)
                    st.write(
                        message.get("message_text") or ""
                    )

                    timestamp = message.get("created_at", "")
                    if timestamp:
                        st.caption(
                            timestamp[:16].replace("T", " ")
                        )

            if channel.get("created_by") == user_id:
                with st.form(
                    f"channel_post_{channel_id}",
                    clear_on_submit=True
                ):
                    announcement = st.text_area(
                        "Publish an announcement"
                    )

                    submitted = st.form_submit_button(
                        "Publish",
                        use_container_width=True
                    )

                    if submitted and announcement.strip():
                        if send_channel_message(
                            supabase,
                            channel_id,
                            user_id,
                            announcement
                        ):
                            st.success("Announcement published.")
                            st.rerun()


# ============================================================
# COMMUNITY HOME — OPENING CARDS
# ============================================================

def render_community_home():
    st.markdown("## Welcome to EcoLoop Community")
    st.caption(
        "Connect, share ideas, learn and take action together."
    )

    cards = [
        ("💬", "Chats", "Private and group conversations"),
        ("👥", "Groups", "Find people with shared interests"),
        ("🌍", "Communities", "Join wider community spaces"),
        ("📢", "Channels", "Read community announcements")
    ]

    for row_start in range(0, len(cards), 2):
        columns = st.columns(2)

        for column, card in zip(
            columns, cards[row_start:row_start + 2]
        ):
            emoji, title, description = card

            with column:
                with st.container(border=True):
                    st.markdown(f"## {emoji}")
                    st.markdown(f"**{title}**")
                    st.caption(description)

                    if st.button(
                        f"Open {title}",
                        key=f"community_home_{title}",
                        use_container_width=True
                    ):
                        st.session_state[
                            "community_page"
                        ] = title
                        st.rerun()


# ============================================================
# FINAL PAGE ENTRY POINT
# ============================================================

def render_community_groups_page(supabase, user_id):
    if "community_page" not in st.session_state:
        st.session_state["community_page"] = "Home"

    st.markdown(
        """
        <div class="community-header">
            <h1>EcoLoop Community</h1>
            <p>Connect • Share • Collaborate • Take Action</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    pages = [
        "Home",
        "Chats",
        "Groups",
        "Communities",
        "Channels"
    ]

    selected_page = st.session_state.get(
        "community_page", "Home"
    )

    if selected_page not in pages:
        selected_page = "Home"

    selected_page = st.radio(
        "Community navigation",
        pages,
        index=pages.index(selected_page),
        horizontal=True,
        key="community_navigation"
    )

    st.session_state["community_page"] = selected_page

    st.divider()

    if selected_page == "Home":
        render_community_home()

    elif selected_page == "Chats":
        render_chats_page(supabase, user_id)

    elif selected_page == "Groups":
        render_groups_page(supabase, user_id)

    elif selected_page == "Communities":
        render_communities_page(supabase, user_id)

    elif selected_page == "Channels":
        render_channels_page(supabase, user_id)

    st.divider()

    st.caption(
        "Powered by Next Gen Impact Hub (NGIH)"
        )
