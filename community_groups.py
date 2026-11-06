
import streamlit as st
import uuid
import mimetypes
import html
from datetime import datetime, timezone, timedelta

BUCKET = "community-media"
MAX_FILE_SIZE = 100 * 1024 * 1024

REACTIONS = ["👍", "❤️", "😂", "😮", "😢", "🔥", "👏"]

PAGES = [
    "Home",
    "Chats",
    "Groups",
    "Communities",
    "Channels",
    "Stories",
    "My Profile"
]


# ============================================================
# ECOLOOP COMMUNITY — DESIGN
# ============================================================

def community_styles():
    st.markdown("""
    <style>
    .eco-hero {
        background: linear-gradient(130deg,#073b35,#087e65,#16a085);
        color: white;
        padding: 24px 20px;
        border-radius: 20px;
        margin-bottom: 18px;
    }
    .eco-hero h1 {color:white;font-size:27px;margin:0;}
    .eco-hero p {color:#d9fff1;margin:5px 0 0 0;}

    .eco-card {
        background: rgba(20,150,110,.09);
        border: 1px solid rgba(30,160,120,.3);
        padding: 17px;
        border-radius: 18px;
        min-height: 115px;
        margin-bottom: 8px;
    }
    .eco-card-icon {font-size:28px;}
    .eco-card-title {font-size:17px;font-weight:750;}
    .eco-card-sub {font-size:12px;opacity:.75;}

    .chat-bubble {
        padding: 11px 14px;
        border-radius: 16px;
        margin: 7px 0;
        max-width: 88%;
        overflow-wrap: anywhere;
    }
    .chat-mine {
        background: #d8f8e8;
        color: #123c2d;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }
    .chat-theirs {
        background: rgba(130,140,150,.16);
        color: inherit;
        margin-right: auto;
        border-bottom-left-radius: 4px;
    }
    .chat-sender {font-size:11px;font-weight:700;opacity:.75;}
    .chat-time {font-size:10px;opacity:.65;text-align:right;margin-top:5px;}

    .eco-story {
        border:1px solid rgba(20,160,120,.5);
        border-radius:16px;
        padding:12px 7px;
        text-align:center;
        min-height:85px;
    }
    .eco-avatar {font-size:29px;}
    .eco-muted {opacity:.7;font-size:12px;}

    div.stButton > button {
        border-radius: 12px;
        min-height: 42px;
    }

    @media (max-width: 600px) {
        .eco-hero h1 {font-size:23px;}
        .eco-card {padding:13px;min-height:100px;}
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
        dt = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

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
        dt = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone().strftime(
            "%d %b %Y · %H:%M"
        )

    except Exception:
        return ""


def safe_query_table(supabase, table, columns="*"):
    try:
        return rows(
            supabase.table(table).select(columns).execute()
        )
    except Exception:
        return []


def get_profile(supabase, user_id):
    if not user_id:
        return {}

    try:
        result = (
            supabase.table("member_profiles")
            .select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        found = rows(result)
        return found[0] if found else {}

    except Exception:
        return {}


def get_member_profile(supabase, user_id):
    return get_profile(supabase, user_id)


def get_profiles(supabase, user_ids):
    ids = list(set(str(x) for x in user_ids if x))

    if not ids:
        return {}

    try:
        result = (
            supabase.table("member_profiles")
            .select("*")
            .in_("user_id", ids)
            .execute()
        )

        return {
            str(profile["user_id"]): profile
            for profile in rows(result)
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


# ============================================================
# MEDIA AND FILE SHARING
# ============================================================

def upload_media(supabase, uploaded_file, folder):
    if not uploaded_file:
        return None

    if uploaded_file.size > MAX_FILE_SIZE:
        st.error("Maximum file size is 100 MB.")
        return None

    filename = uploaded_file.name.replace(" ", "_")
    path = f"{folder}/{uuid.uuid4().hex}_{filename}"

    content_type = (
        uploaded_file.type
        or mimetypes.guess_type(filename)[0]
        or "application/octet-stream"
    )

    try:
        supabase.storage.from_(BUCKET).upload(
            path,
            uploaded_file.getvalue(),
            {
                "content-type": content_type,
                "upsert": "true"
            }
        )

        return path

    except Exception as error:
        show_error(error, "Media upload failed")
        return None


def upload_community_media(supabase, uploaded_file, user_id):
    return upload_media(
        supabase,
        uploaded_file,
        f"community/{user_id}"
    )


def media_url(supabase, path):
    if not path:
        return None

    if str(path).startswith("http"):
        return path

    try:
        result = supabase.storage.from_(BUCKET).create_signed_url(
            path,
            3600
        )

        return (
            result.get("signedURL")
            or result.get("signedUrl")
        )

    except Exception:
        return None


def display_attachment(
    supabase,
    path,
    name=None,
    file_type=None
):
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


def render_community_attachment(
    attachment_path,
    attachment_name=None,
    attachment_type=None
):
    supabase = st.session_state.get("supabase")

    if supabase:
        display_attachment(
            supabase,
            attachment_path,
            attachment_name,
            attachment_type
        )
    else:
        st.caption("Attachment unavailable.")


# ============================================================
# PROFILE SYSTEM
# ============================================================

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
            "Profile picture",
            type=["png", "jpg", "jpeg"],
            key="community_profile_avatar"
        )

        submitted = st.form_submit_button(
            "Save profile",
            use_container_width=True
        )

        if submitted:
            avatar_url = profile.get("avatar_url", "")

            if avatar:
                uploaded_path = upload_media(
                    supabase,
                    avatar,
                    f"profiles/{user_id}"
                )

                if uploaded_path:
                    avatar_url = uploaded_path

            try:
                supabase.table("member_profiles").upsert(
                    {
                        "user_id": user_id,
                        "display_name": display_name.strip(),
                        "username": username.strip(),
                        "bio": bio.strip(),
                        "location": location.strip(),
                        "interests": interests.strip(),
                        "avatar_url": avatar_url,
                        "updated_at": now_iso()
                    },
                    on_conflict="user_id"
                ).execute()

                st.success("Profile updated successfully.")
                st.rerun()

            except Exception as error:
                show_error(error, "Could not update profile")


def member_profile_card(supabase, user_id):
    profile = get_profile(supabase, user_id)
    picture = profile_picture(supabase, profile)

    with st.container(border=True):
        col1, col2 = st.columns([1, 4])

        with col1:
            if picture:
                st.image(picture, width=70)
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
# GROUP AND COMMUNITY LOOKUP HELPERS
# ============================================================

def get_group(supabase, group_id):
    try:
        found = rows(
            supabase.table("community_groups")
            .select("*")
            .eq("id", group_id)
            .limit(1)
            .execute()
        )

        return found[0] if found else None

    except Exception:
        return None


def get_community(supabase, community_id):
    try:
        found = rows(
            supabase.table("communities")
            .select("*")
            .eq("id", community_id)
            .limit(1)
            .execute()
        )

        return found[0] if found else None

    except Exception:
        return None

# ============================================================
# GROUPS AND MEMBERSHIPS
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

        found = rows(result)
        return found[0] if found else None

    except Exception:
        return None


def get_group_members(supabase, group_id):
    try:
        result = (
            supabase.table("group_memberships")
            .select("*")
            .eq("group_id", group_id)
            .eq("status", "approved")
            .execute()
        )

        return rows(result)

    except Exception:
        return []


def is_group_admin(supabase, group_id, user_id):
    membership = get_group_membership(
        supabase, group_id, user_id
    )

    if not membership:
        return False

    return (
        membership.get("status") == "approved"
        and membership.get("membership_role")
        in ["admin", "creator", "owner", "moderator"]
    )


def load_communities(supabase):
    try:
        result = (
            supabase.table("communities")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )

        return rows(result)

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

        return rows(query.execute())

    except Exception:
        return []


def create_community(
    supabase,
    user_id,
    name,
    description,
    location=""
):
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

        created = rows(result)
        return bool(created), created

    except Exception as error:
        show_error(error, "Could not create community")
        return False, []


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

        created = rows(result)

        if not created:
            return False, None

        group = created[0]

        supabase.table("group_memberships").insert({
            "group_id": group["id"],
            "user_id": user_id,
            "membership_role": "admin",
            "status": "approved"
        }).execute()

        return True, group

    except Exception as error:
        show_error(error, "Could not create group")
        return False, None


def request_group_membership(
    supabase,
    group_id,
    user_id
):
    existing = get_group_membership(
        supabase, group_id, user_id
    )

    if existing:
        return False, "You already have a membership record."

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
        show_error(error, "Could not approve member")
        return False


def remove_group_member(supabase, membership_id):
    try:
        supabase.table("group_memberships").delete().eq(
            "id", membership_id
        ).execute()

        return True

    except Exception as error:
        show_error(error, "Could not remove member")
        return False


def load_group_messages(
    supabase,
    group_id,
    limit=100
):
    try:
        result = (
            supabase.table("group_messages")
            .select("*")
            .eq("group_id", group_id)
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )

        return rows(result)

    except Exception:
        return []


# ============================================================
# GROUP READ STATUS AND UNREAD COUNTS
# ============================================================

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

        found = rows(existing)

        if found:
            supabase.table("group_read_status").update({
                "last_read_at": now_iso()
            }).eq("id", found[0]["id"]).execute()

        else:
            supabase.table("group_read_status").insert({
                "group_id": group_id,
                "user_id": user_id,
                "last_read_at": now_iso()
            }).execute()

    except Exception:
        pass


def get_group_unread_count(
    supabase,
    group_id,
    user_id
):
    try:
        status = (
            supabase.table("group_read_status")
            .select("last_read_at")
            .eq("group_id", group_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        found = rows(status)

        if not found:
            messages = load_group_messages(
                supabase, group_id
            )

            return sum(
                1 for message in messages
                if message.get("sender_id") != user_id
            )

        last_read = found[0].get("last_read_at")

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


# ============================================================
# GROUP MESSAGE SENDING
# ============================================================

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
            payload.update({
                "attachment_path": attachment_path,
                "attachment_name": attachment_name,
                "attachment_type": attachment_type
            })

        result = (
            supabase.table("group_messages")
            .insert(payload)
            .execute()
        )

        return bool(rows(result))

    except Exception as error:
        show_error(error, "Message could not be sent")
        return False


# ============================================================
# GROUP MESSAGE REACTIONS
# ============================================================

def load_group_reactions(supabase, message_id):
    try:
        result = (
            supabase.table("group_message_reactions")
            .select("*")
            .eq("message_id", message_id)
            .execute()
        )

        return rows(result)

    except Exception:
        return []


def add_group_reaction(
    supabase,
    message_id,
    user_id,
    reaction
):
    try:
        existing = (
            supabase.table("group_message_reactions")
            .select("*")
            .eq("message_id", message_id)
            .eq("user_id", user_id)
            .eq("reaction", reaction)
            .limit(1)
            .execute()
        )

        if rows(existing):
            supabase.table(
                "group_message_reactions"
            ).delete().eq(
                "message_id", message_id
            ).eq(
                "user_id", user_id
            ).eq(
                "reaction", reaction
            ).execute()

        else:
            supabase.table(
                "group_message_reactions"
            ).insert({
                "message_id": message_id,
                "user_id": user_id,
                "reaction": reaction
            }).execute()

        return True

    except Exception as error:
        show_error(error, "Could not update reaction")
        return False


def render_reaction_bar(
    supabase,
    table,
    message_id,
    user_id,
    key_prefix
):
    try:
        result = (
            supabase.table(table)
            .select("*")
            .eq("message_id", message_id)
            .execute()
        )

        reactions = rows(result)

    except Exception:
        reactions = []

    counts = {}

    for item in reactions:
        emoji = item.get("reaction", "👍")
        counts[emoji] = counts.get(emoji, 0) + 1

    if counts:
        st.caption(
            "  ".join(
                f"{emoji} {count}"
                for emoji, count in counts.items()
            )
        )

    columns = st.columns(len(REACTIONS))

    for column, emoji in zip(columns, REACTIONS):
        with column:
            if st.button(
                emoji,
                key=f"{key_prefix}_{message_id}_{emoji}"
            ):
                if table == "group_message_reactions":
                    add_group_reaction(
                        supabase,
                        message_id,
                        user_id,
                        emoji
                    )

                elif table == "direct_message_reactions":
                    add_direct_reaction(
                        supabase,
                        message_id,
                        user_id,
                        emoji
                    )

                st.rerun()


# ============================================================
# GROUP MESSAGE DISPLAY
# ============================================================

def render_group_message(
    supabase,
    message,
    user_id
):
    sender_id = message.get("sender_id")
    own_message = sender_id == user_id

    profile = get_member_profile(
        supabase, sender_id
    )

    sender_name = profile_name(profile)

    message_text = html.escape(
        message.get("message_text") or ""
    )

    timestamp = format_time(
        message.get("created_at")
    )

    bubble_class = (
        "chat-mine" if own_message
        else "chat-theirs"
    )

    label = "You" if own_message else html.escape(
        sender_name
    )

    st.markdown(
        f"""
        <div class="chat-bubble {bubble_class}">
            <div class="chat-sender">{label}</div>
            <div>{message_text}</div>
            <div class="chat-time">{timestamp}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if message.get("attachment_path"):
        display_attachment(
            supabase,
            message.get("attachment_path"),
            message.get("attachment_name"),
            message.get("attachment_type")
        )

    if message.get("id"):
        render_reaction_bar(
            supabase,
            "group_message_reactions",
            message["id"],
            user_id,
            "group_reaction"
        )


# ============================================================
# GROUP MESSAGE COMPOSER
# ============================================================

def render_group_chat_composer(
    supabase,
    group_id,
    user_id
):
    st.markdown("#### Send a message")

    with st.form(
        key=f"group_message_form_{group_id}",
        clear_on_submit=True
    ):
        message = st.text_area(
            "Message",
            placeholder="Write a message...",
            label_visibility="collapsed",
            height=75
        )

        attachment = st.file_uploader(
            "Photo, video, audio or document",
            type=[
                "png", "jpg", "jpeg", "gif",
                "mp4", "mov", "webm",
                "mp3", "wav", "ogg", "m4a",
                "pdf", "doc", "docx",
                "xls", "xlsx", "ppt", "pptx",
                "txt", "csv"
            ],
            key=f"group_attachment_{group_id}"
        )

        submitted = st.form_submit_button(
            "➤ Send",
            use_container_width=True
        )

        if submitted:
            attachment_path = None
            attachment_name = None
            attachment_type = None

            if attachment:
                attachment_path = upload_community_media(
                    supabase,
                    attachment,
                    user_id
                )

                if attachment_path:
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

            else:
                st.warning("Write a message or attach a file.")


# ============================================================
# GROUP MEMBERS AND ADMIN REQUESTS
# ============================================================

def render_group_members(
    supabase,
    group_id,
    user_id
):
    st.subheader("Members")

    members = get_group_members(
        supabase, group_id
    )

    if not members:
        st.info("No approved members yet.")
        return

    current_user_admin = is_group_admin(
        supabase, group_id, user_id
    )

    profiles = get_profiles(
        supabase,
        [member.get("user_id") for member in members]
    )

    for member in members:
        member_id = member.get("user_id")
        profile = profiles.get(str(member_id), {})

        with st.container(border=True):
            col1, col2 = st.columns([4, 1])

            with col1:
                st.write(f"**{profile_name(profile)}**")
                st.caption(
                    member.get("membership_role", "member").title()
                )

            with col2:
                if (
                    current_user_admin
                    and member_id != user_id
                ):
                    if st.button(
                        "Remove",
                        key=f"remove_member_{member.get('id')}"
                    ):
                        if remove_group_member(
                            supabase,
                            member.get("id")
                        ):
                            st.rerun()


def render_group_admin_requests(
    supabase,
    group_id
):
    st.subheader("Membership requests")

    try:
        result = (
            supabase.table("group_memberships")
            .select("*")
            .eq("group_id", group_id)
            .eq("status", "pending")
            .execute()
        )

        requests = rows(result)

    except Exception as error:
        show_error(error, "Could not load requests")
        return

    if not requests:
        st.caption("There are no pending requests.")
        return

    profiles = get_profiles(
        supabase,
        [item.get("user_id") for item in requests]
    )

    for request in requests:
        profile = profiles.get(
            str(request.get("user_id")),
            {}
        )

        with st.container(border=True):
            st.write(f"**{profile_name(profile)}**")

            if st.button(
                "Approve request",
                key=f"approve_request_{request.get('id')}",
                use_container_width=True
            ):
                if approve_group_member(
                    supabase,
                    request.get("id")
                ):
                    st.success("Member approved.")
                    st.rerun()


# ============================================================
# GROUP PROFILE AND WORKSPACE
# ============================================================

def render_group_profile(
    supabase,
    group,
    user_id
):
    group_id = group.get("id")

    st.subheader(
        group.get("name", "Group")
    )

    if group.get("image_url"):
        st.image(
            group["image_url"],
            use_container_width=True
        )

    st.write(
        group.get("description")
        or "No description added."
    )

    if group.get("location"):
        st.caption(f"📍 {group['location']}")

    members = get_group_members(
        supabase, group_id
    )

    st.caption(
        f"👥 {len(members)} approved members"
    )

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
                supabase,
                group_id,
                user_id
            )

            if success:
                st.success(message)
            else:
                st.info(message)

            st.rerun()

        return

    if membership.get("status") == "pending":
        st.info(
            "Your membership request is awaiting approval."
        )
        return

    if membership.get("status") != "approved":
        st.info("You are not an approved member.")
        return

    st.success("You are a member of this group.")


def render_group_workspace(
    supabase,
    group,
    user_id
):
    group_id = group.get("id")

    st.markdown(
        f"## 👥 {group.get('name', 'Group')}"
    )

    if group.get("description"):
        st.caption(group["description"])

    tab_chat, tab_members, tab_manage = st.tabs([
        "💬 Chat",
        "👥 Members",
        "⚙️ Manage"
    ])

    with tab_chat:
        mark_group_as_read(
            supabase,
            group_id,
            user_id
        )

        messages = load_group_messages(
            supabase,
            group_id
        )

        if not messages:
            st.info(
                "No messages yet. Start the conversation."
            )

        for message in messages:
            render_group_message(
                supabase,
                message,
                user_id
            )

        render_group_chat_composer(
            supabase,
            group_id,
            user_id
        )

    with tab_members:
        render_group_members(
            supabase,
            group_id,
            user_id
        )

    with tab_manage:
        if is_group_admin(
            supabase,
            group_id,
            user_id
        ):
            render_group_admin_requests(
                supabase,
                group_id
            )
        else:
            st.info(
                "Group management is available to admins."
            )

# ============================================================
# PART 3 — PRIVATE CHATS, MEMBER SEARCH, MEDIA & REACTIONS
# ============================================================

import json


# ------------------------------------------------------------
# DIRECT CONVERSATIONS
# ------------------------------------------------------------

def get_direct_conversation(supabase, user_id, other_user_id):
    """Find an existing private conversation between two members."""
    try:
        result = (
            supabase.table("direct_conversations")
            .select("*")
            .execute()
        )

        for conversation in rows(result):
            members = conversation.get("member_ids") or []
            if isinstance(members, str):
                try:
                    members = json.loads(members)
                except Exception:
                    members = []

            if user_id in members and other_user_id in members:
                return conversation

            # Compatibility with schemas storing the two participants
            participant_a = conversation.get("user_id")
            participant_b = conversation.get("other_user_id")

            if {participant_a, participant_b} == {
                user_id, other_user_id
            }:
                return conversation

        return None

    except Exception as e:
        show_error("Could not load private conversations", e)
        return None


def create_direct_conversation(supabase, user_id, other_user_id):
    """Create a private conversation using the existing table."""
    existing = get_direct_conversation(
        supabase, user_id, other_user_id
    )

    if existing:
        return existing

    # The current database may use either member_ids or paired user IDs.
    # Try the common member_ids structure first.
    payload = {
        "member_ids": [user_id, other_user_id]
    }

    try:
        result = (
            supabase.table("direct_conversations")
            .insert(payload)
            .execute()
        )

        created = rows(result)
        if created:
            return created[0]

        return None

    except Exception as first_error:
        # Fallback for schemas using user_id / other_user_id.
        try:
            result = (
                supabase.table("direct_conversations")
                .insert({
                    "user_id": user_id,
                    "other_user_id": other_user_id
                })
                .execute()
            )

            created = rows(result)
            return created[0] if created else None

        except Exception as second_error:
            show_error(
                "Could not create private conversation",
                second_error
            )
            return None


def conversation_id_of(conversation):
    return (
        conversation.get("id")
        or conversation.get("conversation_id")
    )


def load_direct_messages(supabase, conversation_id):
    try:
        result = (
            supabase.table("direct_messages")
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=False)
            .execute()
        )
        return rows(result)

    except Exception as e:
        show_error("Could not load private messages", e)
        return []


# ------------------------------------------------------------
# PRIVATE MESSAGE MEDIA FORMAT
# ------------------------------------------------------------

DIRECT_MEDIA_PREFIX = "ECOMEDIA:"


def encode_direct_message(message_text="", attachment=None):
    """
    Store private-message attachments inside message_text.
    This avoids requiring new database columns.
    """
    if not attachment:
        return message_text.strip()

    data = {
        "__ecoloop_media__": True,
        "text": message_text.strip(),
        "path": attachment.get("path"),
        "name": attachment.get("name"),
        "type": attachment.get("type")
    }

    return DIRECT_MEDIA_PREFIX + json.dumps(data)


def decode_direct_message(raw_text):
    if not raw_text:
        return {"text": "", "attachment": None}

    if not raw_text.startswith(DIRECT_MEDIA_PREFIX):
        return {"text": raw_text, "attachment": None}

    try:
        data = json.loads(
            raw_text[len(DIRECT_MEDIA_PREFIX):]
        )

        if not data.get("__ecoloop_media__"):
            return {"text": raw_text, "attachment": None}

        return {
            "text": data.get("text", ""),
            "attachment": {
                "path": data.get("path"),
                "name": data.get("name"),
                "type": data.get("type")
            }
        }

    except Exception:
        return {"text": raw_text, "attachment": None}


# ------------------------------------------------------------
# SEND PRIVATE MESSAGE
# ------------------------------------------------------------

def send_direct_message(
    supabase,
    conversation_id,
    sender_id,
    message_text,
    attachment=None
):
    message_text = (message_text or "").strip()

    if not message_text and not attachment:
        return False

    stored_message = encode_direct_message(
        message_text,
        attachment
    )

    try:
        supabase.table("direct_messages").insert({
            "conversation_id": conversation_id,
            "sender_id": sender_id,
            "message_text": stored_message
        }).execute()

        return True

    except Exception as e:
        show_error("Could not send private message", e)
        return False


# ------------------------------------------------------------
# PRIVATE MESSAGE REACTIONS
# ------------------------------------------------------------

def add_direct_reaction(
    supabase,
    message_id,
    user_id,
    reaction
):
    try:
        existing = (
            supabase.table("direct_message_reactions")
            .select("*")
            .eq("message_id", message_id)
            .eq("user_id", user_id)
            .execute()
        )

        existing_rows = rows(existing)

        if existing_rows:
            existing_reaction = existing_rows[0]

            if existing_reaction.get("reaction") == reaction:
                supabase.table(
                    "direct_message_reactions"
                ).delete().eq(
                    "id", existing_reaction["id"]
                ).execute()
            else:
                supabase.table(
                    "direct_message_reactions"
                ).update({
                    "reaction": reaction
                }).eq(
                    "id", existing_reaction["id"]
                ).execute()

        else:
            supabase.table(
                "direct_message_reactions"
            ).insert({
                "message_id": message_id,
                "user_id": user_id,
                "reaction": reaction
            }).execute()

        return True

    except Exception as e:
        show_error("Could not update reaction", e)
        return False


def load_direct_reactions(supabase, message_id):
    try:
        result = (
            supabase.table("direct_message_reactions")
            .select("*")
            .eq("message_id", message_id)
            .execute()
        )
        return rows(result)

    except Exception:
        return []


# ------------------------------------------------------------
# DIRECT MESSAGE DISPLAY
# ------------------------------------------------------------

def render_direct_message(
    supabase,
    message,
    current_user_id
):
    sender_id = message.get("sender_id")
    is_mine = sender_id == current_user_id

    raw_text = message.get("message_text") or ""
    decoded = decode_direct_message(raw_text)

    message_text = decoded["text"]
    attachment = decoded["attachment"]

    profile = get_member_profile(supabase, sender_id)
    sender_name = profile_name(profile) if profile else "Member"

    timestamp = format_time(message.get("created_at"))

    bubble_class = "eco-chat-bubble mine" if is_mine else "eco-chat-bubble"

    st.markdown(
        f"""
        <div class="{bubble_class}">
            <div class="eco-message-sender">
                {safe_text("You" if is_mine else sender_name)}
            </div>
            <div class="eco-message-text">
                {safe_text(message_text)}
            </div>
            <div class="eco-message-time">
                {safe_text(timestamp)}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if attachment:
        attachment_path = attachment.get("path")
        if attachment_path:
            display_attachment(
                supabase,
                attachment_path,
                attachment.get("name", "Shared file"),
                attachment.get("type", "application/octet-stream")
            )

    message_id = message.get("id")

    if message_id:
        render_reaction_bar(
            supabase,
            message_id,
            current_user_id,
            table_name="direct_message_reactions"
        )


# ------------------------------------------------------------
# MEMBER DIRECTORY / SEARCH
# ------------------------------------------------------------

def render_member_search(supabase, current_user_id):
    st.markdown("### Find people")
    st.caption(
        "Search EcoLoop members and start a private conversation."
    )

    search_term = st.text_input(
        "Search by name, username or interests",
        key="community_member_search"
    )

    try:
        result = (
            supabase.table("member_profiles")
            .select("*")
            .execute()
        )
        members = rows(result)

    except Exception as e:
        show_error("Could not load member directory", e)
        return

    search_term = search_term.strip().lower()

    matches = []

    for member in members:
        member_id = (
            member.get("user_id")
            or member.get("id")
        )

        if not member_id or member_id == current_user_id:
            continue

        searchable = " ".join([
            str(member.get("display_name") or ""),
            str(member.get("username") or ""),
            str(member.get("bio") or ""),
            str(member.get("location") or ""),
            str(member.get("interests") or "")
        ]).lower()

        if not search_term or search_term in searchable:
            matches.append(member)

    if not matches:
        st.info("No members found. Try another search.")
        return

    for member in matches[:30]:
        member_id = (
            member.get("user_id")
            or member.get("id")
        )

        name = profile_name(member)
        username = member.get("username") or ""

        with st.container(border=True):
            left, right = st.columns([3, 1])

            with left:
                st.markdown(f"**{safe_text(name)}**")
                if username:
                    st.caption("@" + safe_text(username))

                if member.get("bio"):
                    st.caption(
                        safe_text(member.get("bio"))
                    )

            with right:
                if st.button(
                    "Message",
                    key=f"start_private_{member_id}",
                    use_container_width=True
                ):
                    conversation = create_direct_conversation(
                        supabase,
                        current_user_id,
                        member_id
                    )

                    if conversation:
                        st.session_state[
                            "active_direct_conversation"
                        ] = conversation_id_of(conversation)

                        st.session_state[
                            "active_direct_member"
                        ] = member_id

                        st.session_state[
                            "community_page"
                        ] = "Chats"

                        st.session_state[
                            "community_navigation"
                        ] = "Chats"

                        st.rerun()


# ------------------------------------------------------------
# PRIVATE CHAT COMPOSER
# ------------------------------------------------------------

def render_direct_chat_composer(
    supabase,
    conversation_id,
    current_user_id
):
    st.markdown("---")
    st.markdown("**Send a message**")

    message_text = st.text_area(
        "Write a message",
        key=f"direct_text_{conversation_id}",
        height=80,
        label_visibility="collapsed",
        placeholder="Type your message..."
    )

    attachment_file = st.file_uploader(
        "Attach a picture, video, audio or document",
        key=f"direct_attachment_{conversation_id}",
        accept_multiple_files=False,
        type=None
    )

    # Voice recording is available on Streamlit versions
    # that provide st.audio_input.
    audio_input_function = getattr(st, "audio_input", None)

    voice_recording = None

    if audio_input_function:
        try:
            voice_recording = audio_input_function(
                "Record a voice note",
                key=f"direct_voice_{conversation_id}"
            )
        except Exception:
            voice_recording = None

    if st.button(
        "Send message",
        key=f"send_direct_{conversation_id}",
        type="primary",
        use_container_width=True
    ):
        attachment = None
        selected_file = voice_recording or attachment_file

        if selected_file:
            uploaded = upload_media(
                supabase,
                selected_file,
                current_user_id
            )

            if uploaded:
                attachment = {
                    "path": uploaded,
                    "name": getattr(
                        selected_file, "name", "Voice note"
                    ),
                    "type": getattr(
                        selected_file,
                        "type",
                        "application/octet-stream"
                    )
                }
            else:
                st.error(
                    "The attachment could not be uploaded. "
                    "Your message was not sent."
                )
                return

        success = send_direct_message(
            supabase,
            conversation_id,
            current_user_id,
            message_text,
            attachment
        )

        if success:
            st.session_state[
                f"direct_text_{conversation_id}"
            ] = ""

            st.rerun()


# ------------------------------------------------------------
# PRIVATE CHAT VIEW
# ------------------------------------------------------------

def render_direct_chat(
    supabase,
    conversation_id,
    current_user_id,
    other_user_id=None
):
    if not conversation_id:
        st.info("Choose a conversation to open.")
        return

    other_profile = (
        get_member_profile(supabase, other_user_id)
        if other_user_id else None
    )

    if other_profile:
        st.markdown(
            f"### {safe_text(profile_name(other_profile))}"
        )
    else:
        st.markdown("### Private conversation")

    if st.button(
        "← Back to conversations",
        key="back_from_direct_chat"
    ):
        st.session_state.pop(
            "active_direct_conversation", None
        )
        st.session_state.pop("active_direct_member", None)
        st.rerun()

    messages = load_direct_messages(
        supabase,
        conversation_id
    )

    if not messages:
        st.info(
            "This conversation is ready. Send the first message."
        )
    else:
        for message in messages:
            render_direct_message(
                supabase,
                message,
                current_user_id
            )

    render_direct_chat_composer(
        supabase,
        conversation_id,
        current_user_id
    )


# ------------------------------------------------------------
# PRIVATE CONVERSATION LIST
# ------------------------------------------------------------

def render_direct_chat_list(supabase, current_user_id):
    st.markdown("### Your private chats")

    try:
        result = (
            supabase.table("direct_conversations")
            .select("*")
            .execute()
        )
        conversations = rows(result)

    except Exception as e:
        show_error("Could not load your conversations", e)
        conversations = []

    my_conversations = []

    for conversation in conversations:
        members = conversation.get("member_ids") or []

        if isinstance(members, str):
            try:
                members = json.loads(members)
            except Exception:
                members = []

        if current_user_id in members:
            my_conversations.append(conversation)
            continue

        if (
            conversation.get("user_id") == current_user_id
            or conversation.get("other_user_id") == current_user_id
        ):
            my_conversations.append(conversation)

    active_id = st.session_state.get(
        "active_direct_conversation"
    )

    if active_id:
        active_member = st.session_state.get(
            "active_direct_member"
        )

        render_direct_chat(
            supabase,
            active_id,
            current_user_id,
            active_member
        )
        return

    if not my_conversations:
        st.info(
            "You don't have any private chats yet. "
            "Use Find people to start one."
        )
        return

    for conversation in my_conversations:
        conversation_id = conversation_id_of(conversation)

        if not conversation_id:
            continue

        members = conversation.get("member_ids") or []

        if isinstance(members, str):
            try:
                members = json.loads(members)
            except Exception:
                members = []

        other_user_id = next(
            (
                member for member in members
                if member != current_user_id
            ),
            None
        )

        if not other_user_id:
            if conversation.get("user_id") == current_user_id:
                other_user_id = conversation.get("other_user_id")
            else:
                other_user_id = conversation.get("user_id")

        profile = (
            get_member_profile(supabase, other_user_id)
            if other_user_id else None
        )

        name = (
            profile_name(profile)
            if profile else "Private conversation"
        )

        with st.container(border=True):
            left, right = st.columns([3, 1])

            with left:
                st.markdown(f"**{safe_text(name)}**")
                st.caption("Private chat")

            with right:
                if st.button(
                    "Open",
                    key=f"open_direct_{conversation_id}",
                    use_container_width=True
                ):
                    st.session_state[
                        "active_direct_conversation"
                    ] = conversation_id

                    st.session_state[
                        "active_direct_member"
                    ] = other_user_id

                    st.rerun()


# ------------------------------------------------------------
# SHARED MEDIA VIEW
# ------------------------------------------------------------

def render_private_shared_media(
    supabase,
    conversation_id
):
    st.markdown("### Shared media")

    messages = load_direct_messages(
        supabase,
        conversation_id
    )

    found = False

    for message in messages:
        decoded = decode_direct_message(
            message.get("message_text") or ""
        )

        attachment = decoded.get("attachment")

        if not attachment:
            continue

        found = True

        display_attachment(
            supabase,
            attachment.get("path"),
            attachment.get("name", "Shared file"),
            attachment.get("type", "application/octet-stream")
        )

    if not found:
        st.info("No shared files in this conversation yet.")

# ============================================================
# PART 4 — COMMUNITIES, CHANNELS, STORIES & SHARED CONTENT
# ============================================================


# ------------------------------------------------------------
# COMMUNITY MANAGEMENT
# ------------------------------------------------------------

def connect_group_to_community(
    supabase,
    group_id,
    community_id,
    user_id
):
    """Connect an existing group to a community."""
    try:
        group = get_group(supabase, group_id)

        if not group:
            st.error("Group not found.")
            return False

        if not is_group_admin(supabase, group_id, user_id):
            st.error(
                "Only a group administrator can connect this group."
            )
            return False

        supabase.table("community_groups").update({
            "community_id": community_id
        }).eq("id", group_id).execute()

        st.success("Group connected to the community.")
        return True

    except Exception as e:
        show_error("Could not connect group", e)
        return False


def render_connect_groups(supabase, user_id, community):
    st.markdown("### Connect existing groups")
    st.caption(
        "Bring groups you administer into this community."
    )

    community_id = community.get("id")

    if not community_id:
        st.warning("This community has no valid ID.")
        return

    groups = load_groups(supabase)

    manageable_groups = []

    for group in groups:
        group_id = group.get("id")

        if not group_id:
            continue

        if is_group_admin(supabase, group_id, user_id):
            manageable_groups.append(group)

    if not manageable_groups:
        st.info(
            "You don't currently administer any groups "
            "that can be connected."
        )
        return

    for group in manageable_groups:
        group_id = group.get("id")
        group_name = group.get("name") or "Unnamed group"
        current_community = group.get("community_id")

        with st.container(border=True):
            st.markdown(f"**{safe_text(group_name)}**")

            if current_community == community_id:
                st.caption("Already connected")
            elif current_community:
                st.caption(
                    "This group is already connected to another community."
                )
            else:
                if st.button(
                    "Connect group",
                    key=f"connect_group_{group_id}_{community_id}",
                    use_container_width=True
                ):
                    if connect_group_to_community(
                        supabase,
                        group_id,
                        community_id,
                        user_id
                    ):
                        st.rerun()


def render_community_profile(
    supabase,
    community,
    user_id
):
    community_name = (
        community.get("name") or "Community"
    )

    st.markdown(f"## {safe_text(community_name)}")

    if community.get("description"):
        st.write(community.get("description"))

    if community.get("image_url"):
        st.image(
            community.get("image_url"),
            use_container_width=True
        )

    community_id = community.get("id")

    try:
        linked_groups = (
            supabase.table("community_groups")
            .select("*")
            .eq("community_id", community_id)
            .execute()
        )

        groups = rows(linked_groups)

    except Exception:
        groups = []

    st.markdown("### Connected groups")

    if not groups:
        st.info("No groups have been connected yet.")
    else:
        for group in groups:
            st.markdown(
                f"- **{safe_text(group.get('name') or 'Group')}**"
            )

    render_connect_groups(
        supabase,
        user_id,
        community
    )


def render_communities_page(supabase, user_id):
    st.markdown("## Communities")
    st.caption(
        "Find people and groups working towards shared goals."
    )

    tab_create, tab_explore, tab_manage = st.tabs([
        "Create",
        "Explore",
        "Manage"
    ])

    with tab_create:
        st.markdown("### Start a community")

        with st.form("create_community_form"):
            name = st.text_input(
                "Community name",
                placeholder="e.g. Bulawayo Climate Action"
            )

            description = st.text_area(
                "What is this community about?",
                placeholder="Describe its purpose and activities."
            )

            submitted = st.form_submit_button(
                "Create community",
                type="primary",
                use_container_width=True
            )

            if submitted:
                if not name.strip():
                    st.error("Please enter a community name.")
                else:
                    created = create_community(
                        supabase,
                        user_id,
                        name.strip(),
                        description.strip()
                    )

                    if created:
                        st.success("Community created successfully.")
                        st.rerun()

    with tab_explore:
        communities = load_communities(supabase)

        if not communities:
            st.info("No communities are available yet.")
        else:
            for community in communities:
                community_id = community.get("id")

                with st.container(border=True):
                    st.markdown(
                        f"### {safe_text(community.get('name') or 'Community')}"
                    )

                    if community.get("description"):
                        st.write(community.get("description"))

                    if st.button(
                        "Open community",
                        key=f"open_community_{community_id}",
                        use_container_width=True
                    ):
                        st.session_state[
                            "active_community"
                        ] = community_id
                        st.rerun()

        active_community_id = st.session_state.get(
            "active_community"
        )

        if active_community_id:
            selected = next(
                (
                    item for item in communities
                    if item.get("id") == active_community_id
                ),
                None
            )

            if selected:
                st.markdown("---")

                if st.button(
                    "Close community",
                    key="close_community_profile"
                ):
                    st.session_state.pop(
                        "active_community", None
                    )
                    st.rerun()

                render_community_profile(
                    supabase,
                    selected,
                    user_id
                )

    with tab_manage:
        communities = load_communities(supabase)

        my_communities = [
            community for community in communities
            if community.get("created_by") == user_id
        ]

        if not my_communities:
            st.info(
                "Communities you create will appear here."
            )
        else:
            for community in my_communities:
                with st.container(border=True):
                    st.markdown(
                        f"**{safe_text(community.get('name') or 'Community')}**"
                    )

                    render_connect_groups(
                        supabase,
                        user_id,
                        community
                    )


# ------------------------------------------------------------
# CHANNELS
# ------------------------------------------------------------

def load_channels(supabase):
    try:
        result = (
            supabase.table("community_channels")
            .select("*")
            .eq("is_active", True)
            .order("created_at", desc=True)
            .execute()
        )
        return rows(result)

    except Exception:
        # Some existing channel schemas may not have created_at.
        try:
            result = (
                supabase.table("community_channels")
                .select("*")
                .eq("is_active", True)
                .execute()
            )
            return rows(result)

        except Exception as e:
            show_error("Could not load channels", e)
            return []


def create_channel(
    supabase,
    user_id,
    name,
    description,
    community_id=None
):
    payload = {
        "name": name,
        "description": description,
        "created_by": user_id,
        "is_active": True
    }

    if community_id:
        payload["community_id"] = community_id

    try:
        result = (
            supabase.table("community_channels")
            .insert(payload)
            .execute()
        )

        created = rows(result)
        return created[0] if created else None

    except Exception as e:
        show_error(
            "Could not create channel. Check that the channel "
            "table supports the fields used by this app.",
            e
        )
        return None


def load_channel_messages(supabase, channel_id):
    try:
        result = (
            supabase.table("channel_messages")
            .select("*")
            .eq("channel_id", channel_id)
            .order("created_at", desc=False)
            .execute()
        )
        return rows(result)

    except Exception as e:
        show_error("Could not load channel posts", e)
        return []


def publish_channel_message(
    supabase,
    channel_id,
    user_id,
    message_text
):
    if not message_text.strip():
        st.warning("Write an announcement first.")
        return False

    try:
        supabase.table("channel_messages").insert({
            "channel_id": channel_id,
            "sender_id": user_id,
            "message_text": message_text.strip()
        }).execute()

        return True

    except Exception as e:
        show_error("Could not publish announcement", e)
        return False


def render_channel_view(
    supabase,
    channel,
    user_id
):
    channel_id = channel.get("id")

    st.markdown(
        f"### {safe_text(channel.get('name') or 'Channel')}"
    )

    if channel.get("description"):
        st.write(channel.get("description"))

    if st.button(
        "← Back to channels",
        key="back_from_channel"
    ):
        st.session_state.pop("active_channel", None)
        st.rerun()

    messages = load_channel_messages(
        supabase,
        channel_id
    )

    st.markdown("#### Announcements")

    if not messages:
        st.info("No announcements have been published.")
    else:
        for message in messages:
            profile = get_member_profile(
                supabase,
                message.get("sender_id")
            )

            name = (
                profile_name(profile)
                if profile else "Channel administrator"
            )

            with st.container(border=True):
                st.caption(
                    f"{safe_text(name)} · "
                    f"{safe_text(format_time(message.get('created_at')))}"
                )
                st.write(message.get("message_text") or "")

    if channel.get("created_by") == user_id:
        st.markdown("---")
        st.markdown("#### Publish an announcement")

        announcement = st.text_area(
            "Announcement",
            key=f"channel_announcement_{channel_id}",
            placeholder="Share an update with your followers..."
        )

        if st.button(
            "Publish",
            key=f"publish_channel_{channel_id}",
            type="primary",
            use_container_width=True
        ):
            if publish_channel_message(
                supabase,
                channel_id,
                user_id,
                announcement
            ):
                st.success("Announcement published.")
                st.rerun()


def render_channels_page(supabase, user_id):
    st.markdown("## Channels")
    st.caption(
        "Follow updates, announcements and information from organisations."
    )

    create_tab, explore_tab = st.tabs([
        "Create channel",
        "Explore channels"
    ])

    with create_tab:
        st.markdown("### Start a channel")

        communities = load_communities(supabase)

        community_options = {
            "No community connection": None
        }

        for community in communities:
            community_options[
                community.get("name") or "Community"
            ] = community.get("id")

        with st.form("create_channel_form"):
            channel_name = st.text_input(
                "Channel name",
                placeholder="e.g. EcoLoop Updates"
            )

            channel_description = st.text_area(
                "Channel description"
            )

            selected_community = st.selectbox(
                "Connect to a community (optional)",
                list(community_options.keys())
            )

            create_submitted = st.form_submit_button(
                "Create channel",
                type="primary",
                use_container_width=True
            )

            if create_submitted:
                if not channel_name.strip():
                    st.error("Enter a channel name.")
                else:
                    channel = create_channel(
                        supabase,
                        user_id,
                        channel_name.strip(),
                        channel_description.strip(),
                        community_options[selected_community]
                    )

                    if channel:
                        st.success("Channel created.")
                        st.rerun()

    with explore_tab:
        channels = load_channels(supabase)

        if not channels:
            st.info(
                "No channels are available yet. "
                "You can create the first one."
            )
        else:
            for channel in channels:
                channel_id = channel.get("id")

                with st.container(border=True):
                    st.markdown(
                        f"**{safe_text(channel.get('name') or 'Channel')}**"
                    )

                    if channel.get("description"):
                        st.caption(channel.get("description"))

                    if st.button(
                        "Open channel",
                        key=f"open_channel_{channel_id}",
                        use_container_width=True
                    ):
                        st.session_state[
                            "active_channel"
                        ] = channel_id
                        st.rerun()

        active_channel_id = st.session_state.get(
            "active_channel"
        )

        if active_channel_id:
            selected_channel = next(
                (
                    channel for channel in channels
                    if channel.get("id") == active_channel_id
                ),
                None
            )

            if selected_channel:
                st.markdown("---")
                render_channel_view(
                    supabase,
                    selected_channel,
                    user_id
                )


# ------------------------------------------------------------
# STORIES
# ------------------------------------------------------------

def load_active_stories(supabase):
    try:
        result = (
            supabase.table("community_stories")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )

        all_stories = rows(result)
        current_time = datetime.now(timezone.utc)

        active = []

        for story in all_stories:
            expiry = story.get("expires_at")

            if not expiry:
                continue

            try:
                expiry_time = datetime.fromisoformat(
                    expiry.replace("Z", "+00:00")
                )

                if expiry_time > current_time:
                    active.append(story)

            except Exception:
                continue

        return active

    except Exception as e:
        show_error("Could not load stories", e)
        return []


def create_story(
    supabase,
    user_id,
    caption,
    uploaded_file
):
    uploaded_path = upload_media(
        supabase,
        uploaded_file,
        user_id
    )

    if not uploaded_path:
        return False

    public_url = media_url(
        supabase,
        uploaded_path
    )

    if not public_url:
        st.error("Could not create a link for the uploaded story.")
        return False

    file_type = (
        getattr(uploaded_file, "type", "")
        or mimetypes.guess_type(
            getattr(uploaded_file, "name", "")
        )[0]
        or "image"
    )

    if file_type.startswith("video/"):
        media_type = "video"
    elif file_type.startswith("audio/"):
        media_type = "audio"
    else:
        media_type = "image"

    expiry_time = (
        datetime.now(timezone.utc)
        + timedelta(hours=24)
    ).isoformat()

    try:
        supabase.table("community_stories").insert({
            "user_id": user_id,
            "caption": caption.strip(),
            "media_url": public_url,
            "media_type": media_type,
            "expires_at": expiry_time
        }).execute()

        return True

    except Exception as e:
        show_error("Could not publish story", e)
        return False


def render_story_item(supabase, story):
    profile = get_member_profile(
        supabase,
        story.get("user_id")
    )

    name = (
        profile_name(profile)
        if profile else "EcoLoop member"
    )

    st.markdown(
        f"**{safe_text(name)}** · "
        f"{safe_text(format_time(story.get('created_at')))}"
    )

    caption = story.get("caption") or ""

    if caption:
        st.write(caption)

    media_type = story.get("media_type") or "image"
    media_url_value = story.get("media_url")

    if not media_url_value:
        return

    if media_type == "video":
        st.video(media_url_value)
    elif media_type == "audio":
        st.audio(media_url_value)
    else:
        st.image(
            media_url_value,
            use_container_width=True
        )


def render_stories_page(supabase, user_id):
    st.markdown("## Stories")
    st.caption(
        "Share a moment with the EcoLoop community. "
        "Stories expire after 24 hours."
    )

    with st.expander("＋ Create a story", expanded=False):
        caption = st.text_area(
            "Add a caption",
            key="story_caption",
            placeholder="What's happening?"
        )

        story_file = st.file_uploader(
            "Choose a picture, video or audio file",
            key="story_upload",
            type=[
                "png", "jpg", "jpeg", "webp",
                "mp4", "mov", "webm",
                "mp3", "wav", "m4a", "ogg"
            ]
        )

        if st.button(
            "Publish story",
            key="publish_story",
            type="primary",
            use_container_width=True
        ):
            if not story_file:
                st.warning("Choose a file first.")
            elif create_story(
                supabase,
                user_id,
                caption,
                story_file
            ):
                st.success("Your story has been published.")
                st.rerun()

    st.markdown("---")
    st.markdown("### Recent stories")

    stories = load_active_stories(supabase)

    if not stories:
        st.info("No active stories yet. Be the first to share one.")
        return

    for story in stories:
        with st.container(border=True):
            render_story_item(supabase, story)


# ------------------------------------------------------------
# SHARED MEDIA — GROUP CHAT
# ------------------------------------------------------------

def render_group_shared_media(
    supabase,
    group_id
):
    st.markdown("### Shared media")

    messages = load_group_messages(
        supabase,
        group_id
    )

    found = False

    for message in messages:
        attachment_path = message.get("attachment_path")

        if not attachment_path:
            continue

        found = True

        display_attachment(
            supabase,
            attachment_path,
            message.get("attachment_name", "Shared file"),
            message.get(
                "attachment_type",
                "application/octet-stream"
            )
        )

    if not found:
        st.info("No shared files in this group yet.")


# ------------------------------------------------------------
# SHARED MEDIA — PRIVATE CHAT
# ------------------------------------------------------------

def render_direct_shared_media_page(supabase):
    conversation_id = st.session_state.get(
        "active_direct_conversation"
    )

    if not conversation_id:
        st.info(
            "Open a private chat first to view its shared media."
        )
        return

    render_private_shared_media(
        supabase,
        conversation_id
    )


# ------------------------------------------------------------
# SHARED CONTENT PAGE
# ------------------------------------------------------------

def render_shared_content_page(supabase):
    st.markdown("## Shared content")
    st.caption(
        "View files and media shared in your active conversations."
    )

    tab_private, tab_group = st.tabs([
        "Private chat",
        "Group chat"
    ])

    with tab_private:
        render_direct_shared_media_page(supabase)

    with tab_group:
        group_id = st.session_state.get("active_group")

        if group_id:
            render_group_shared_media(
                supabase,
                group_id
            )
        else:
            st.info(
                "Open a group chat first to view its shared media."
            )

# ============================================================
# PART 5 — DASHBOARD, NAVIGATION & FINAL INTEGRATION
# ============================================================

from datetime import datetime, timezone, timedelta


# ------------------------------------------------------------
# NAVIGATION
# ------------------------------------------------------------

COMMUNITY_PAGES = [
    "Home",
    "Chats",
    "Groups",
    "Communities",
    "Channels",
    "Stories",
    "Profile",
    "Shared content"
]


def navigate_community(page):
    st.session_state["community_page"] = page
    st.session_state["community_navigation"] = page


def community_navigation_changed():
    selected = st.session_state.get(
        "community_navigation",
        "Home"
    )
    st.session_state["community_page"] = selected


# ------------------------------------------------------------
# HOME DASHBOARD
# ------------------------------------------------------------

def render_community_home(supabase, user_id):
    profile = get_member_profile(supabase, user_id)
    display_name = (
        profile_name(profile)
        if profile else "EcoLoop member"
    )

    st.markdown(
        f"""
        <div class="eco-community-hero">
            <div class="eco-community-kicker">
                ECOLOOP NODE · COMMUNITY HUB
            </div>
            <h1>Connect. Share. Make an impact.</h1>
            <p>
                Welcome, {safe_text(display_name)}.
                Find people, join groups and share ideas
                with your community.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### Your community spaces")
    st.caption(
        "Choose where you want to go."
    )

    cards = [
        (
            "Chats",
            "💬",
            "Private conversations and group messages",
            "Chats"
        ),
        (
            "Groups",
            "👥",
            "Join groups and work together",
            "Groups"
        ),
        (
            "Communities",
            "🌍",
            "Connect groups around shared goals",
            "Communities"
        ),
        (
            "Channels",
            "📢",
            "Follow news and announcements",
            "Channels"
        ),
        (
            "Stories",
            "📸",
            "Share moments with the community",
            "Stories"
        ),
        (
            "Profile",
            "👤",
            "Manage your community identity",
            "Profile"
        )
    ]

    for start in range(0, len(cards), 2):
        columns = st.columns(2)

        for offset, column in enumerate(columns):
            index = start + offset

            if index >= len(cards):
                continue

            title, emoji, description, page = cards[index]

            with column:
                with st.container(border=True):
                    st.markdown(
                        f"""
                        <div class="eco-home-card">
                            <div class="eco-home-card-icon">
                                {emoji}
                            </div>
                            <h3>{safe_text(title)}</h3>
                            <p>{safe_text(description)}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    if st.button(
                        f"Open {title}",
                        key=f"home_open_{page}",
                        use_container_width=True
                    ):
                        navigate_community(page)
                        st.rerun()

    st.markdown("---")
    st.markdown("### Your community at a glance")

    col1, col2, col3 = st.columns(3)

    try:
        direct_result = (
            supabase.table("direct_conversations")
            .select("*")
            .execute()
        )
        direct_count = len(rows(direct_result))
    except Exception:
        direct_count = 0

    try:
        group_result = (
            supabase.table("community_groups")
            .select("*")
            .execute()
        )
        group_count = len(rows(group_result))
    except Exception:
        group_count = 0

    try:
        channel_result = (
            supabase.table("community_channels")
            .select("*")
            .eq("is_active", True)
            .execute()
        )
        channel_count = len(rows(channel_result))
    except Exception:
        channel_count = 0

    with col1:
        st.metric("Conversations", direct_count)

    with col2:
        st.metric("Groups", group_count)

    with col3:
        st.metric("Channels", channel_count)


# ------------------------------------------------------------
# GROUP DISCOVERY AND GROUP LIST
# ------------------------------------------------------------

def render_group_directory(supabase, user_id):
    st.markdown("### Discover groups")

    groups = load_groups(supabase)

    if not groups:
        st.info("No groups have been created yet.")
        return

    search = st.text_input(
        "Search groups",
        key="community_group_search",
        placeholder="Search by group name..."
    ).strip().lower()

    for group in groups:
        group_id = group.get("id")
        name = group.get("name") or "Unnamed group"
        description = group.get("description") or ""

        searchable = f"{name} {description}".lower()

        if search and search not in searchable:
            continue

        membership = get_group_membership(
            supabase,
            group_id,
            user_id
        )

        with st.container(border=True):
            st.markdown(f"**{safe_text(name)}**")

            if description:
                st.write(description)

            if membership:
                st.caption("You are a member of this group.")

                if st.button(
                    "Open group",
                    key=f"directory_open_{group_id}",
                    use_container_width=True
                ):
                    st.session_state["active_group"] = group_id
                    st.rerun()

            else:
                if st.button(
                    "Request to join",
                    key=f"directory_join_{group_id}",
                    use_container_width=True
                ):
                    if request_group_membership(
                        supabase,
                        group_id,
                        user_id
                    ):
                        st.success("Membership request submitted.")
                        st.rerun()


def render_my_groups(supabase, user_id):
    st.markdown("### My groups")

    groups = load_groups(supabase)
    my_groups = []

    for group in groups:
        group_id = group.get("id")

        if not group_id:
            continue

        membership = get_group_membership(
            supabase,
            group_id,
            user_id
        )

        if membership:
            my_groups.append(group)

    if not my_groups:
        st.info(
            "You haven't joined a group yet. "
            "Explore groups or create one."
        )
        return

    for group in my_groups:
        group_id = group.get("id")
        name = group.get("name") or "Group"

        with st.container(border=True):
            st.markdown(f"**{safe_text(name)}**")

            if st.button(
                "Open group chat",
                key=f"my_group_open_{group_id}",
                use_container_width=True
            ):
                st.session_state["active_group"] = group_id
                st.rerun()


# ------------------------------------------------------------
# GROUP PAGE
# ------------------------------------------------------------

def render_groups_page(supabase, user_id):
    st.markdown("## Groups")
    st.caption(
        "Create a group, discover other groups or open your group chats."
    )

    create_tab, discover_tab, mine_tab = st.tabs([
        "Create group",
        "Discover",
        "My groups"
    ])

    with create_tab:
        st.markdown("### Create a group")

        communities = load_communities(supabase)

        community_options = {
            "No community": None
        }

        for community in communities:
            community_options[
                community.get("name") or "Community"
            ] = community.get("id")

        with st.form("community_create_group_form"):
            group_name = st.text_input(
                "Group name",
                placeholder="e.g. Bulawayo Youth Climate Action"
            )

            group_description = st.text_area(
                "Group description"
            )

            selected_community = st.selectbox(
                "Connect to a community (optional)",
                list(community_options.keys())
            )

            submitted = st.form_submit_button(
                "Create group",
                type="primary",
                use_container_width=True
            )

            if submitted:
                if not group_name.strip():
                    st.error("Enter a group name.")
                else:
                    created = create_group(
                        supabase,
                        user_id,
                        group_name.strip(),
                        group_description.strip(),
                        community_options[selected_community]
                    )

                    if created:
                        st.success("Group created successfully.")
                        st.session_state["active_group"] = (
                            created.get("id")
                        )
                        st.rerun()

    with discover_tab:
        render_group_directory(
            supabase,
            user_id
        )

    with mine_tab:
        render_my_groups(
            supabase,
            user_id
        )

    active_group_id = st.session_state.get("active_group")

    if active_group_id:
        selected_group = get_group(
            supabase,
            active_group_id
        )

        if selected_group:
            st.markdown("---")

            if st.button(
                "Close group",
                key="close_active_group"
            ):
                st.session_state.pop("active_group", None)
                st.rerun()

            render_group_workspace(
                supabase,
                active_group_id,
                user_id
            )


# ------------------------------------------------------------
# CHATS PAGE
# ------------------------------------------------------------

def render_chats_page(supabase, user_id):
    st.markdown("## Chats")
    st.caption(
        "Your private conversations and group chats."
    )

    private_tab, group_tab, find_tab = st.tabs([
        "Private chats",
        "Group chats",
        "Find people"
    ])

    with private_tab:
        render_direct_chat_list(
            supabase,
            user_id
        )

    with group_tab:
        render_my_groups(
            supabase,
            user_id
        )

        active_group_id = st.session_state.get(
            "active_group"
        )

        if active_group_id:
            selected_group = get_group(
                supabase,
                active_group_id
            )

            if selected_group:
                st.markdown("---")

                if st.button(
                    "Close group chat",
                    key="close_group_chat_from_chats"
                ):
                    st.session_state.pop(
                        "active_group", None
                    )
                    st.rerun()

                render_group_workspace(
                    supabase,
                    active_group_id,
                    user_id
                )

    with find_tab:
        render_member_search(
            supabase,
            user_id
        )


# ------------------------------------------------------------
# PROFILE PAGE
# ------------------------------------------------------------

def render_community_profile_page(supabase, user_id):
    st.markdown("## Your profile")
    st.caption(
        "Manage how other EcoLoop members see you."
    )

    profile = get_member_profile(
        supabase,
        user_id
    )

    if profile:
        member_profile_card(
            supabase,
            user_id
        )

    st.markdown("---")
    st.markdown("### Edit your profile")

    profile_editor(
        supabase,
        user_id
    )


# ------------------------------------------------------------
# COMMUNITY HUB MAIN ENTRY POINT
# ------------------------------------------------------------

def render_community_groups_page(supabase, user_id):
    """
    Main Community Hub page.
    Call this function from the main EcoLoop app.
    """

    # Make the active Supabase client available to
    # attachment helper functions from earlier parts.
    st.session_state["supabase"] = supabase

    # Styling
    community_styles()

    # Initial navigation state
    if "community_page" not in st.session_state:
        st.session_state["community_page"] = "Home"

    if "community_navigation" not in st.session_state:
        st.session_state["community_navigation"] = (
            st.session_state["community_page"]
        )

    if st.session_state["community_page"] not in COMMUNITY_PAGES:
        st.session_state["community_page"] = "Home"

    if st.session_state["community_navigation"] not in COMMUNITY_PAGES:
        st.session_state["community_navigation"] = "Home"

    st.markdown(
        """
        <div class="eco-community-header">
            <div class="eco-community-brand">
                <span class="eco-community-brand-icon">♻️</span>
                <span>EcoLoop Node</span>
            </div>
            <div class="eco-community-subtitle">
                COMMUNITY HUB
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Main navigation
    st.radio(
        "Community navigation",
        COMMUNITY_PAGES,
        key="community_navigation",
        horizontal=True,
        label_visibility="collapsed",
        on_change=community_navigation_changed
    )

    selected_page = st.session_state.get(
        "community_navigation",
        "Home"
    )

    st.session_state["community_page"] = selected_page

    st.markdown("---")

    # Route to selected page
    if selected_page == "Home":
        render_community_home(
            supabase,
            user_id
        )

    elif selected_page == "Chats":
        render_chats_page(
            supabase,
            user_id
        )

    elif selected_page == "Groups":
        render_groups_page(
            supabase,
            user_id
        )

    elif selected_page == "Communities":
        render_communities_page(
            supabase,
            user_id
        )

    elif selected_page == "Channels":
        render_channels_page(
            supabase,
            user_id
        )

    elif selected_page == "Stories":
        render_stories_page(
            supabase,
            user_id
        )

    elif selected_page == "Profile":
        render_community_profile_page(
            supabase,
            user_id
        )

    elif selected_page == "Shared content":
        render_shared_content_page(
            supabase
        )

    # Footer
    st.markdown(
        """
        <div class="eco-community-footer">
            <strong>EcoLoop Node</strong>
            <br>
            Powered by Next Gen Impact Hub (NGIH)
        </div>
        """,
        unsafe_allow_html=True
    )
