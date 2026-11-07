import streamlit as st
import uuid
import mimetypes
import html

from datetime import datetime, timezone, timedelta


# ==========================================================
# ECOLOOP NODE — COMMUNITY HUB
# NEXT GEN IMPACT HUB (NGIH)
# ==========================================================

MEDIA_BUCKET = "community-media"


# ==========================================================
# PART 1 — CORE HELPERS
# ==========================================================

def eco_now():
    return datetime.now(timezone.utc)


def eco_escape(value):
    if value is None:
        return ""
    return html.escape(str(value))


def eco_init_state():
    defaults = {
        "eco_community_section": "Chats",
        "eco_active_conversation": None,
        "eco_active_chatroom": None,
        "eco_view_profile_id": None,
        "eco_people_search": "",
        "eco_chatroom_search": "",
        "eco_chat_inbox_search": "",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def eco_set_section(section):
    st.session_state["eco_community_section"] = section


def eco_profile(supabase, user_id):
    try:
        result = (
            supabase.table("member_profiles")
            .select("*")
            .eq("user_id", str(user_id))
            .limit(1)
            .execute()
        )

        if result.data:
            return result.data[0]

    except Exception as e:
        st.error(f"Could not load profile: {e}")

    return {
        "user_id": str(user_id),
        "display_name": "EcoLoop Member",
        "username": "",
        "avatar_url": "",
        "bio": "",
        "location": "",
        "interests": "",
        "country_of_origin": "",
        "instagram_handle": "",
        "facebook_handle": "",
        "tiktok_handle": "",
        "linkedin_handle": "",
    }


def eco_member_name(supabase, user_id):
    profile = eco_profile(supabase, user_id)

    return (
        profile.get("display_name")
        or profile.get("username")
        or "EcoLoop Member"
    )


def eco_member_username(supabase, user_id):
    profile = eco_profile(supabase, user_id)
    username = profile.get("username") or ""

    return f"@{username}" if username else "@member"


# ==========================================================
# PART 2 — MEDIA HELPERS
# ==========================================================

def eco_valid_storage_path(file_path, allowed_folders=None):
    if not isinstance(file_path, str):
        return False

    file_path = file_path.strip()

    if not file_path or file_path.startswith("http"):
        return False

    if "\\" in file_path or ".." in file_path:
        return False

    parts = file_path.split("/")

    if len(parts) < 3:
        return False

    if allowed_folders and parts[0] not in allowed_folders:
        return False

    return True


def get_story_media_url(supabase, file_path):
    if not file_path:
        return None

    file_path = str(file_path).strip()

    # Support existing external image URLs.
    if file_path.startswith("https://") or file_path.startswith("http://"):
        return file_path

    if not eco_valid_storage_path(
        file_path,
        ["profiles", "chatrooms", "stories"]
    ):
        return None

    try:
        result = (
            supabase.storage
            .from_(MEDIA_BUCKET)
            .create_signed_url(file_path, 3600)
        )

        if isinstance(result, dict):
            return (
                result.get("signedURL")
                or result.get("signedUrl")
                or result.get("signed_url")
            )

        if hasattr(result, "signedURL"):
            return result.signedURL

        if hasattr(result, "signedUrl"):
            return result.signedUrl

        if hasattr(result, "data") and isinstance(result.data, dict):
            return (
                result.data.get("signedURL")
                or result.data.get("signedUrl")
            )

        return None

    except Exception:
        # Invalid legacy image paths should not break the page.
        return None


def eco_avatar(supabase, user_id):
    profile = eco_profile(supabase, user_id)
    avatar_path = profile.get("avatar_url") or ""

    return get_story_media_url(supabase, avatar_path)


def eco_show_avatar(supabase, avatar_path, width=70):
    avatar_url = get_story_media_url(supabase, avatar_path)

    if avatar_url:
        try:
            st.image(avatar_url, width=width)
            return True
        except Exception:
            pass

    st.markdown("### 👤")
    return False


def eco_upload_image(supabase, user_id, uploaded_file, folder):
    if uploaded_file is None:
        return ""

    extension = uploaded_file.name.rsplit(".", 1)[-1].lower()

    if extension not in ["jpg", "jpeg", "png", "webp"]:
        st.error("Please upload a JPG, PNG or WEBP image.")
        return None

    content_type = (
        uploaded_file.type
        or mimetypes.guess_type(uploaded_file.name)[0]
        or "application/octet-stream"
    )

    file_path = (
        f"{folder}/{user_id}/{uuid.uuid4().hex}.{extension}"
    )

    try:
        supabase.storage.from_(MEDIA_BUCKET).upload(
            file_path,
            uploaded_file.getvalue(),
            {
                "content-type": content_type,
                "upsert": "true",
            }
        )

        return file_path

    except Exception as e:
        st.error(f"Image upload failed: {e}")
        return None


# ==========================================================
# PART 3 — MEMBER PROFILES
# ==========================================================

def get_member_directory(supabase, search=""):
    try:
        query = (
            supabase.table("member_profiles")
            .select("*")
            .order("username")
        )

        if search and search.strip():
            query = query.ilike(
                "username",
                f"%{search.strip()}%"
            )

        result = query.limit(100).execute()
        return result.data or []

    except Exception as e:
        st.error(f"Could not load members: {e}")
        return []


def save_member_profile(
    supabase,
    user_id,
    display_name,
    username,
    avatar_path,
    bio,
    location,
    interests,
    country_of_origin="",
    instagram_handle="",
    facebook_handle="",
    tiktok_handle="",
    linkedin_handle="",
):
    username = username.strip().lower().replace("@", "")

    if not username:
        st.error("Please enter a username.")
        return False

    if len(username) < 3:
        st.error("Your username must contain at least 3 characters.")
        return False

    if not all(
        char.isalnum() or char in "._"
        for char in username
    ):
        st.error(
            "Use only letters, numbers, dots and underscores "
            "in your username."
        )
        return False

    try:
        existing = (
            supabase.table("member_profiles")
            .select("user_id,username")
            .ilike("username", username)
            .limit(1)
            .execute()
        )

        for profile in existing.data or []:
            if str(profile.get("user_id")) != str(user_id):
                st.error("That username is already taken.")
                return False

        payload = {
            "user_id": str(user_id),
            "display_name": display_name.strip(),
            "username": username,
            "avatar_url": avatar_path or "",
            "bio": bio.strip(),
            "location": location.strip(),
            "interests": interests.strip(),
            "country_of_origin": country_of_origin.strip(),
            "instagram_handle": instagram_handle.strip(),
            "facebook_handle": facebook_handle.strip(),
            "tiktok_handle": tiktok_handle.strip(),
            "linkedin_handle": linkedin_handle.strip(),
            "updated_at": eco_now().isoformat(),
        }

        supabase.table("member_profiles").upsert(
            payload,
            on_conflict="user_id"
        ).execute()

        st.success("Profile saved successfully.")
        return True

    except Exception as e:
        st.error(f"Could not save profile: {e}")
        return False


def render_profile_editor(supabase, user_id):
    profile = eco_profile(supabase, user_id)

    st.subheader("Your Profile")
    st.caption(
        "Build your EcoLoop identity and let other members "
        "get to know you."
    )

    current_avatar = profile.get("avatar_url") or ""

    if current_avatar:
        eco_show_avatar(supabase, current_avatar, 120)

    uploaded_photo = st.file_uploader(
        "Upload profile picture from your device",
        type=["jpg", "jpeg", "png", "webp"],
        key="eco_profile_photo"
    )

    if uploaded_photo:
        st.image(uploaded_photo, width=120)

    with st.form("eco_profile_form"):
        st.markdown("**Basic information**")

        display_name = st.text_input(
            "Display name",
            value=profile.get("display_name") or ""
        )

        username = st.text_input(
            "Username",
            value=profile.get("username") or "",
            help="Your unique username helps people find you."
        )

        bio = st.text_area(
            "About me",
            value=profile.get("bio") or "",
            max_chars=300,
            placeholder="Tell the community a little about yourself..."
        )

        location = st.text_input(
            "Current location",
            value=profile.get("location") or ""
        )

        country_of_origin = st.text_input(
            "Country of origin",
            value=profile.get("country_of_origin") or ""
        )

        interests = st.text_input(
            "Interests",
            value=profile.get("interests") or "",
            placeholder="Climate action, technology, entrepreneurship..."
        )

        st.divider()
        st.markdown("**Social media (optional)**")

        instagram_handle = st.text_input(
            "Instagram username",
            value=profile.get("instagram_handle") or ""
        )

        facebook_handle = st.text_input(
            "Facebook profile",
            value=profile.get("facebook_handle") or ""
        )

        tiktok_handle = st.text_input(
            "TikTok username",
            value=profile.get("tiktok_handle") or ""
        )

        linkedin_handle = st.text_input(
            "LinkedIn profile",
            value=profile.get("linkedin_handle") or ""
        )

        submitted = st.form_submit_button(
            "Save Profile",
            use_container_width=True
        )

    if submitted:
        avatar_path = current_avatar

        if uploaded_photo:
            new_path = eco_upload_image(
                supabase,
                user_id,
                uploaded_photo,
                "profiles"
            )

            if new_path is None:
                return

            if new_path:
                avatar_path = new_path

        saved = save_member_profile(
            supabase,
            user_id,
            display_name,
            username,
            avatar_path,
            bio,
            location,
            interests,
            country_of_origin,
            instagram_handle,
            facebook_handle,
            tiktok_handle,
            linkedin_handle,
        )

        if saved:
            st.rerun()


# ==========================================================
# PART 4 — FOLLOW CONTROLS
# TEMPORARY SESSION-BASED FOLLOWING
# PERSISTENT FOLLOWING WILL BE CONNECTED LATER
# ==========================================================

def init_follow_state():
    if "eco_following" not in st.session_state:
        st.session_state["eco_following"] = set()


def render_follow_controls(member_id):
    if not member_id:
        return

    init_follow_state()

    following = st.session_state["eco_following"]
    member_id = str(member_id)

    if member_id in following:
        if st.button(
            "Following ✓",
            key=f"eco_unfollow_{member_id}"
        ):
            following.discard(member_id)
            st.rerun()
    else:
        if st.button(
            "＋ Follow",
            key=f"eco_follow_{member_id}"
        ):
            following.add(member_id)
            st.rerun()


# ==========================================================
# PART 5 — PUBLIC MEMBER PROFILES
# ==========================================================

def render_public_profile(supabase, user_id, member):
    member_id = str(member.get("user_id") or "")

    if st.button(
        "← Back to Discover",
        key="eco_back_to_discover"
    ):
        st.session_state["eco_view_profile_id"] = None
        st.rerun()

    name = member.get("display_name") or "EcoLoop Member"
    username = member.get("username") or "member"
    avatar = member.get("avatar_url") or ""
    bio = member.get("bio") or ""
    location = member.get("location") or ""
    interests = member.get("interests") or ""
    country = member.get("country_of_origin") or ""

    st.divider()

    col1, col2 = st.columns([1, 3])

    with col1:
        eco_show_avatar(supabase, avatar, 120)

    with col2:
        st.title(name)
        st.caption(f"@{username}")

        if location:
            st.caption(f"📍 {location}")

        if country:
            st.caption(f"🌍 From {country}")

        if member_id != str(user_id):
            render_follow_controls(member_id)

    st.divider()

    st.markdown("**About**")
    st.write(bio or "No bio added yet.")

    st.markdown("**Interests**")
    st.write(interests or "No interests added yet.")

    social_links = {
        "Instagram": member.get("instagram_handle"),
        "Facebook": member.get("facebook_handle"),
        "TikTok": member.get("tiktok_handle"),
        "LinkedIn": member.get("linkedin_handle"),
    }

    available_socials = {
        name: value
        for name, value in social_links.items()
        if value
    }

    if available_socials:
        st.divider()
        st.markdown("**Social profiles**")

        for platform, handle in available_socials.items():
            st.caption(f"{platform}: {handle}")

    if member_id and member_id != str(user_id):
        st.divider()

        if st.button(
            "Message",
            key=f"eco_public_message_{member_id}",
            use_container_width=True
        ):
            conversation_id = get_or_create_direct_conversation(
                supabase,
                user_id,
                member_id
            )

            if conversation_id:
                st.session_state["eco_active_conversation"] = (
                    conversation_id
                )
                eco_set_section("Chats")
                st.rerun()


# ==========================================================
# PART 6 — DISCOVER PEOPLE
# ==========================================================

def render_people_directory(supabase, user_id):
    selected_id = st.session_state.get("eco_view_profile_id")

    if selected_id:
        try:
            result = (
                supabase.table("member_profiles")
                .select("*")
                .eq("user_id", str(selected_id))
                .limit(1)
                .execute()
            )

            if result.data:
                render_public_profile(
                    supabase,
                    user_id,
                    result.data[0]
                )
                return

        except Exception as e:
            st.error(f"Could not open profile: {e}")

        st.session_state["eco_view_profile_id"] = None

    st.subheader("Discover People")
    st.caption("Find members and connect with the EcoLoop community.")

    search = st.text_input(
        "Search by username",
        key="eco_people_search",
        placeholder="Enter a username..."
    )

    members = get_member_directory(supabase, search)

    members = [
        member for member in members
        if str(member.get("user_id")) != str(user_id)
    ]

    if not members:
        st.info("No members found.")
        return

    for member in members:
        member_id = str(member.get("user_id"))
        name = member.get("display_name") or "EcoLoop Member"
        username = member.get("username") or "member"
        avatar = member.get("avatar_url") or ""
        bio = member.get("bio") or ""
        location = member.get("location") or ""

        with st.container(border=True):
            col1, col2 = st.columns([1, 4])

            with col1:
                eco_show_avatar(supabase, avatar, 70)

            with col2:
                st.markdown(f"**{eco_escape(name)}**")
                st.caption(f"@{eco_escape(username)}")

                if bio:
                    st.write(bio[:160])

                if location:
                    st.caption(f"📍 {eco_escape(location)}")

                if st.button(
                    "View Profile",
                    key=f"eco_view_profile_{member_id}",
                    use_container_width=True
                ):
                    st.session_state["eco_view_profile_id"] = member_id
                    st.rerun()


# ==========================================================
# PART 7 — PRIVATE DIRECT MESSAGES
# ==========================================================

def get_or_create_direct_conversation(
    supabase,
    user_id,
    other_user_id
):
    user_a = str(user_id)
    user_b = str(other_user_id)

    if user_a == user_b:
        st.warning("You cannot start a conversation with yourself.")
        return None

    try:
        existing = (
            supabase.table("direct_conversations")
            .select("*")
            .or_(
                f"and(user_one_id.eq.{user_a},user_two_id.eq.{user_b}),"
                f"and(user_one_id.eq.{user_b},user_two_id.eq.{user_a})"
            )
            .limit(1)
            .execute()
        )

        if existing.data:
            return existing.data[0]["id"]

        # Keep a consistent participant order.
        first_user, second_user = sorted([user_a, user_b])

        result = (
            supabase.table("direct_conversations")
            .insert({
                "user_one_id": first_user,
                "user_two_id": second_user,
            })
            .execute()
        )

        if result.data:
            return result.data[0]["id"]

        return None

    except Exception as e:
        st.error(f"Could not open conversation: {e}")
        return None


def get_direct_conversations(supabase, user_id):
    try:
        result = (
            supabase.table("direct_conversations")
            .select("*")
            .or_(
                f"user_one_id.eq.{user_id},"
                f"user_two_id.eq.{user_id}"
            )
            .order("created_at", desc=True)
            .execute()
        )

        return result.data or []

    except Exception as e:
        st.error(f"Could not load chats: {e}")
        return []


def get_direct_messages(supabase, conversation_id):
    try:
        result = (
            supabase.table("direct_messages")
            .select("*")
            .eq("conversation_id", str(conversation_id))
            .is_("deleted_at", "null")
            .order("created_at")
            .execute()
        )

        return result.data or []

    except Exception as e:
        st.error(f"Could not load messages: {e}")
        return []


def send_direct_message(
    supabase,
    conversation_id,
    user_id,
    message
):
    message = message.strip()

    if not message:
        return False

    try:
        supabase.table("direct_messages").insert({
            "conversation_id": str(conversation_id),
            "sender_id": str(user_id),
            "message_text": message,
        }).execute()

        return True

    except Exception as e:
        st.error(f"Could not send message: {e}")
        return False


def get_other_conversation_user(conversation, user_id):
    if str(conversation.get("user_one_id")) == str(user_id):
        return conversation.get("user_two_id")

    return conversation.get("user_one_id")


def render_direct_chat(supabase, user_id, conversation_id):
    try:
        conversation_result = (
            supabase.table("direct_conversations")
            .select("*")
            .eq("id", str(conversation_id))
            .limit(1)
            .execute()
        )

        if not conversation_result.data:
            st.error("Conversation not found.")
            return

        conversation = conversation_result.data[0]

        # Check that the current user belongs to this conversation.
        participants = [
            str(conversation.get("user_one_id")),
            str(conversation.get("user_two_id")),
        ]

        if str(user_id) not in participants:
            st.error("You do not have access to this conversation.")
            return

        other_user_id = get_other_conversation_user(
            conversation,
            user_id
        )

        other_profile = eco_profile(supabase, other_user_id)

    except Exception as e:
        st.error(f"Could not open conversation: {e}")
        return

    col1, col2 = st.columns([1, 5])

    with col1:
        eco_show_avatar(
            supabase,
            other_profile.get("avatar_url"),
            55
        )

    with col2:
        st.markdown(
            f"### {eco_escape(other_profile.get('display_name') or 'Member')}"
        )
        st.caption(
            f"@{eco_escape(other_profile.get('username') or 'member')}"
        )

    if st.button("← Back to Chats", key="eco_back_to_chats"):
        st.session_state["eco_active_conversation"] = None
        st.rerun()

    st.divider()

    messages = get_direct_messages(supabase, conversation_id)

    if not messages:
        st.info("This is the beginning of your conversation.")

    for message in messages:
        sender_id = str(message.get("sender_id"))
        mine = sender_id == str(user_id)

        with st.chat_message("user" if mine else "assistant"):
            st.caption("You" if mine else (
                other_profile.get("display_name") or "Member"
            ))

            message_text = message.get("message_text") or ""

            if message_text:
                st.write(message_text)

            if message.get("attachment_path"):
                st.caption(
                    f"📎 {message.get('attachment_name') or 'Attachment'}"
                )

            created = message.get("created_at")

            if created:
                st.caption(
                    str(created).replace("T", " ")[:16]
                )

    st.divider()

    with st.form(
        f"eco_direct_message_form_{conversation_id}",
        clear_on_submit=True
    ):
        message_text = st.text_input(
            "Message",
            placeholder="Write a message..."
        )

        submitted = st.form_submit_button(
            "Send",
            use_container_width=True
        )

    if submitted and message_text.strip():
        if send_direct_message(
            supabase,
            conversation_id,
            user_id,
            message_text
        ):
            st.rerun()


# ==========================================================
# PART 8 — CHATS INBOX AND NEW CHAT PICKER
# ==========================================================

def render_new_chat_picker(supabase, user_id):
    st.subheader("Start a new conversation")

    members = get_member_directory(supabase)

    members = [
        member for member in members
        if str(member.get("user_id")) != str(user_id)
    ]

    if not members:
        st.info("No other EcoLoop members are available yet.")
        return

    member_options = {}

    for member in members:
        member_id = str(member.get("user_id"))
        name = member.get("display_name") or "EcoLoop Member"
        username = member.get("username") or "member"

        member_options[
            f"{name} (@{username})"
        ] = member_id

    selected_label = st.selectbox(
        "Choose a member",
        list(member_options.keys()),
        key="eco_new_chat_member"
    )

    selected_id = member_options.get(selected_label)

    if selected_id:
        selected_profile = next(
            (
                member for member in members
                if str(member.get("user_id")) == selected_id
            ),
            {}
        )

        eco_show_avatar(
            supabase,
            selected_profile.get("avatar_url"),
            75
        )

        if st.button(
            "Open Conversation",
            use_container_width=True,
            key="eco_start_new_conversation"
        ):
            conversation_id = get_or_create_direct_conversation(
                supabase,
                user_id,
                selected_id
            )

            if conversation_id:
                st.session_state["eco_active_conversation"] = (
                    conversation_id
                )
                st.rerun()


def render_chats_page(supabase, user_id):
    st.title("Chats")
    st.caption("Your private conversations on EcoLoop Node.")

    active_conversation = st.session_state.get(
        "eco_active_conversation"
    )

    if active_conversation:
        render_direct_chat(
            supabase,
            user_id,
            active_conversation
        )
        return

    if st.session_state.get("eco_show_new_chat"):
        if st.button("← Back to Inbox", key="eco_close_new_chat"):
            st.session_state["eco_show_new_chat"] = False
            st.rerun()

        render_new_chat_picker(supabase, user_id)
        return

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("**PRIVATE MESSAGES**")

    with col2:
        if st.button(
            "＋ New Chat",
            use_container_width=True,
            key="eco_new_chat_button"
        ):
            st.session_state["eco_show_new_chat"] = True
            st.rerun()

    search = st.text_input(
        "🔍 Search conversations",
        key="eco_chat_inbox_search",
        placeholder="Search names or usernames..."
    )

    conversations = get_direct_conversations(
        supabase,
        user_id
    )

    inbox_items = []

    for conversation in conversations:
        other_user_id = get_other_conversation_user(
            conversation,
            user_id
        )

        profile = eco_profile(supabase, other_user_id)

        name = profile.get("display_name") or "EcoLoop Member"
        username = profile.get("username") or "member"

        if search:
            term = search.strip().lower()

            if (
                term not in name.lower()
                and term not in username.lower()
            ):
                continue

        messages = get_direct_messages(
            supabase,
            conversation.get("id")
        )

        last_message = messages[-1] if messages else {}

        message_text = (
            last_message.get("message_text")
            or (
                "📎 Attachment"
                if last_message.get("attachment_path")
                else "Start a conversation"
            )
        )

        inbox_items.append({
            "conversation": conversation,
            "user_id": other_user_id,
            "profile": profile,
            "name": name,
            "username": username,
            "message": message_text,
            "time": last_message.get("created_at") or "",
        })

    if not inbox_items:
        st.info(
            "No conversations found. "
            "Start a new chat with an EcoLoop member."
        )
        return

    for item in inbox_items:
        conversation = item["conversation"]
        profile = item["profile"]

        with st.container(border=True):
            col1, col2, col3 = st.columns([1, 4, 1.5])

            with col1:
                eco_show_avatar(
                    supabase,
                    profile.get("avatar_url"),
                    55
                )

            with col2:
                st.markdown(f"**{eco_escape(item['name'])}**")
                st.caption(f"@{eco_escape(item['username'])}")
                st.caption(
                    eco_escape(str(item["message"]))[:90]
                )

                if item["time"]:
                    st.caption(
                        str(item["time"]).replace("T", " ")[:16]
                    )

            with col3:
                if st.button(
                    "Open",
                    key=f"eco_open_chat_{conversation.get('id')}",
                    use_container_width=True
                ):
                    st.session_state["eco_active_conversation"] = (
                        conversation.get("id")
                    )
                    st.rerun()

                if st.button(
                    "Profile",
                    key=f"eco_chat_profile_{item['user_id']}",
                    use_container_width=True
                ):
                    st.session_state["eco_view_profile_id"] = (
                        str(item["user_id"])
                    )
                    eco_set_section("Discover People")
                    st.rerun()


# ==========================================================
# PART 9 — CHATROOM DATABASE HELPERS
# ==========================================================

def get_chatrooms(supabase, search=""):
    try:
        query = (
            supabase.table("community_groups")
            .select("*")
            .order("created_at", desc=True)
        )

        if search and search.strip():
            query = query.or_(
                f"name.ilike.%{search.strip()}%,"
                f"description.ilike.%{search.strip()}%"
            )

        result = query.limit(100).execute()
        return result.data or []

    except Exception as e:
        st.error(f"Could not load chatrooms: {e}")
        return []


def get_my_chatrooms(supabase, user_id):
    try:
        memberships = (
            supabase.table("group_memberships")
            .select("group_id,status")
            .eq("user_id", str(user_id))
            .eq("status", "approved")
            .execute()
        )

        group_ids = {
            str(item.get("group_id"))
            for item in (memberships.data or [])
        }

        result = (
            supabase.table("community_groups")
            .select("*")
            .order("created_at", desc=True)
            .limit(200)
            .execute()
        )

        return [
            group for group in (result.data or [])
            if (
                str(group.get("id")) in group_ids
                or str(group.get("created_by")) == str(user_id)
            )
        ]

    except Exception as e:
        st.error(f"Could not load your chatrooms: {e}")
        return []


def create_chatroom(
    supabase,
    user_id,
    name,
    description,
    image_url="",
    location=""
):
    name = name.strip()

    if not name:
        st.error("Enter a chatroom name.")
        return False

    try:
        result = supabase.table("community_groups").insert({
            "name": name,
            "description": description.strip(),
            "created_by": str(user_id),
            "image_url": image_url or "",
            "location": location.strip(),
        }).execute()

        if result.data:
            st.success("Chatroom created successfully.")
            return True

        st.error("Chatroom could not be created.")
        return False

    except Exception as e:
        st.error(f"Could not create chatroom: {e}")
        return False


def request_chatroom_join(supabase, group_id, user_id):
    try:
        existing = (
            supabase.table("group_memberships")
            .select("id,status")
            .eq("group_id", str(group_id))
            .eq("user_id", str(user_id))
            .limit(1)
            .execute()
        )

        if existing.data:
            status = existing.data[0].get("status")

            if status == "approved":
                st.info("You are already a member.")
            elif status == "pending":
                st.info("Your request is awaiting approval.")
            else:
                st.info("A membership record already exists.")

            return False

        supabase.table("group_memberships").insert({
            "group_id": str(group_id),
            "user_id": str(user_id),
            "membership_role": "member",
            "status": "pending",
        }).execute()

        st.success("Join request sent.")
        return True

    except Exception as e:
        st.error(f"Could not request to join: {e}")
        return False


def leave_chatroom(supabase, group_id, user_id):
    try:
        supabase.table("group_memberships").delete().eq(
            "group_id", str(group_id)
        ).eq(
            "user_id", str(user_id)
        ).execute()

        st.success("You have left the chatroom.")
        return True

    except Exception as e:
        st.error(f"Could not leave chatroom: {e}")
        return False


def manage_chatroom_requests(supabase, group):
    group_id = group.get("id")

    try:
        result = (
            supabase.table("group_memberships")
            .select("*")
            .eq("group_id", str(group_id))
            .eq("status", "pending")
            .execute()
        )

        requests = result.data or []

        if not requests:
            st.caption("No pending join requests.")
            return

        st.markdown("**Pending join requests**")

        for request in requests:
            requester_id = request.get("user_id")
            profile = eco_profile(supabase, requester_id)

            name = profile.get("display_name") or "Member"
            username = profile.get("username") or "member"

            with st.container(border=True):
                st.write(f"**{eco_escape(name)}**")
                st.caption(f"@{eco_escape(username)}")

                col1, col2 = st.columns(2)

                with col1:
                    if st.button(
                        "Approve",
                        key=f"eco_approve_{request.get('id')}",
                        use_container_width=True
                    ):
                        supabase.table("group_memberships").update({
                            "status": "approved"
                        }).eq(
                            "id", str(request.get("id"))
                        ).execute()

                        st.success("Member approved.")
                        st.rerun()

                with col2:
                    if st.button(
                        "Reject",
                        key=f"eco_reject_{request.get('id')}",
                        use_container_width=True
                    ):
                        supabase.table("group_memberships").delete().eq(
                            "id", str(request.get("id"))
                        ).execute()

                        st.rerun()

    except Exception as e:
        st.error(f"Could not manage join requests: {e}")


# ==========================================================
# PART 10 — CHATROOMS PAGE
# ==========================================================

def render_chatrooms_page(supabase, user_id):
    st.title("👥 Chatrooms")
    st.caption(
        "Find people, join conversations and build communities."
    )

    tab_discover, tab_mine, tab_create = st.tabs([
        "Discover",
        "My Chatrooms",
        "Create"
    ])

    # ------------------------------------------------------
    # DISCOVER CHATROOMS
    # ------------------------------------------------------

    with tab_discover:
        search = st.text_input(
            "Search chatrooms",
            key="eco_chatroom_search",
            placeholder="Search by name or description..."
        )

        chatrooms = get_chatrooms(supabase, search)

        if not chatrooms:
            st.info("No chatrooms found.")

        for group in chatrooms:
            group_id = group.get("id")
            creator_id = str(group.get("created_by"))

            with st.container(border=True):
                image_path = group.get("image_url") or ""

                if image_path:
                    image_url = get_story_media_url(
                        supabase,
                        image_path
                    )

                    if image_url:
                        st.image(
                            image_url,
                            use_container_width=True
                        )

                st.markdown(
                    f"### {eco_escape(group.get('name') or '')}"
                )

                if group.get("description"):
                    st.write(group.get("description"))

                if group.get("location"):
                    st.caption(
                        f"📍 {eco_escape(group.get('location'))}"
                    )

                if creator_id == str(user_id):
                    st.caption("You created this chatroom.")

                else:
                    if st.button(
                        "Request to Join",
                        key=f"eco_join_{group_id}",
                        use_container_width=True
                    ):
                        request_chatroom_join(
                            supabase,
                            group_id,
                            user_id
                        )

    # ------------------------------------------------------
    # MY CHATROOMS
    # ------------------------------------------------------

    with tab_mine:
        my_chatrooms = get_my_chatrooms(supabase, user_id)

        if not my_chatrooms:
            st.info("You have not joined any chatrooms yet.")

        for group in my_chatrooms:
            group_id = group.get("id")
            is_owner = (
                str(group.get("created_by")) == str(user_id)
            )

            with st.container(border=True):
                image_path = group.get("image_url") or ""

                if image_path:
                    image_url = get_story_media_url(
                        supabase,
                        image_path
                    )

                    if image_url:
                        st.image(
                            image_url,
                            use_container_width=True
                        )

                st.markdown(
                    f"### {eco_escape(group.get('name') or '')}"
                )

                if group.get("description"):
                    st.write(group.get("description"))

                if is_owner:
                    st.caption("Chatroom owner")
                    manage_chatroom_requests(supabase, group)

                if st.button(
                    "Open Chatroom",
                    key=f"eco_open_room_{group_id}",
                    use_container_width=True
                ):
                    st.session_state["eco_active_chatroom"] = group_id
                    st.rerun()

                if not is_owner:
                    if st.button(
                        "Leave Chatroom",
                        key=f"eco_leave_room_{group_id}",
                        use_container_width=True
                    ):
                        if leave_chatroom(
                            supabase,
                            group_id,
                            user_id
                        ):
                            st.rerun()

    # ------------------------------------------------------
    # CREATE CHATROOM
    # ------------------------------------------------------

    with tab_create:
        st.subheader("Create a Chatroom")

        uploaded_photo = st.file_uploader(
            "Choose a chatroom picture",
            type=["jpg", "jpeg", "png", "webp"],
            key="eco_chatroom_photo"
        )

        if uploaded_photo:
            st.image(
                uploaded_photo,
                caption="Chatroom picture preview",
                use_container_width=True
            )

        with st.form("eco_create_chatroom_form"):
            name = st.text_input("Chatroom name")
            description = st.text_area("Description")
            location = st.text_input("Location")

            submitted = st.form_submit_button(
                "Create Chatroom",
                use_container_width=True
            )

        if submitted:
            if not name.strip():
                st.error("Enter a chatroom name.")
                return

            image_path = ""

            if uploaded_photo:
                image_path = eco_upload_image(
                    supabase,
                    user_id,
                    uploaded_photo,
                    "chatrooms"
                )

                if image_path is None:
                    return

            if create_chatroom(
                supabase,
                user_id,
                name,
                description,
                image_path,
                location
            ):
                st.rerun()


# ==========================================================
# PART 11 — CHATROOM MEMBERSHIP AND MESSAGES
# ==========================================================

def is_chatroom_member(supabase, group, user_id):
    if str(group.get("created_by")) == str(user_id):
        return True

    try:
        result = (
            supabase.table("group_memberships")
            .select("id")
            .eq("group_id", str(group.get("id")))
            .eq("user_id", str(user_id))
            .eq("status", "approved")
            .limit(1)
            .execute()
        )

        return bool(result.data)

    except Exception:
        return False


def get_chatroom_messages(supabase, group_id):
    try:
        result = (
            supabase.table("group_messages")
            .select("*")
            .eq("group_id", str(group_id))
            .is_("deleted_at", "null")
            .order("created_at")
            .execute()
        )

        return result.data or []

    except Exception as e:
        st.error(f"Could not load chatroom messages: {e}")
        return []


def send_chatroom_message(
    supabase,
    group_id,
    user_id,
    message
):
    message = message.strip()

    if not message:
        return False

    try:
        supabase.table("group_messages").insert({
            "group_id": str(group_id),
            "sender_id": str(user_id),
            "message_text": message,
        }).execute()

        return True

    except Exception as e:
        st.error(f"Could not send message: {e}")
        return False


def render_chatroom_chat(supabase, user_id, group_id):
    try:
        result = (
            supabase.table("community_groups")
            .select("*")
            .eq("id", str(group_id))
            .limit(1)
            .execute()
        )

        if not result.data:
            st.error("Chatroom not found.")
            return

        group = result.data[0]

    except Exception as e:
        st.error(f"Could not open chatroom: {e}")
        return

    if not is_chatroom_member(supabase, group, user_id):
        st.warning(
            "You must be an approved member to enter this chatroom."
        )
        return

    image_path = group.get("image_url") or ""

    if image_path:
        image_url = get_story_media_url(supabase, image_path)

        if image_url:
            st.image(
                image_url,
                use_container_width=True
            )

    st.markdown(
        f"## {eco_escape(group.get('name') or 'Chatroom')}"
    )

    if group.get("description"):
        st.caption(group.get("description"))

    if st.button(
        "← Back to Chatrooms",
        key="eco_back_to_rooms"
    ):
        st.session_state["eco_active_chatroom"] = None
        st.rerun()

    st.divider()

    messages = get_chatroom_messages(supabase, group_id)

    if not messages:
        st.info("No messages yet. Start the conversation!")

    for message in messages:
        sender_id = str(message.get("sender_id"))
        mine = sender_id == str(user_id)

        sender_name = (
            "You"
            if mine
            else eco_member_name(supabase, sender_id)
        )

        with st.chat_message("user" if mine else "assistant"):
            st.caption(sender_name)

            message_text = message.get("message_text") or ""

            if message_text:
                st.write(message_text)

            if message.get("attachment_path"):
                st.caption(
                    f"📎 {message.get('attachment_name') or 'Attachment'}"
                )

            created = message.get("created_at")

            if created:
                st.caption(
                    str(created).replace("T", " ")[:16]
                )

    st.divider()

    with st.form(
        f"eco_chatroom_message_form_{group_id}",
        clear_on_submit=True
    ):
        message_text = st.text_input(
            "Write a message",
            placeholder="Message everyone in this chatroom..."
        )

        submitted = st.form_submit_button(
            "Send",
            use_container_width=True
        )

    if submitted and message_text.strip():
        if send_chatroom_message(
            supabase,
            group_id,
            user_id,
            message_text
        ):
            st.rerun()


# ==========================================================
# PART 12 — STORIES
# ==========================================================

def upload_story_media(supabase, user_id, uploaded_file):
    if uploaded_file is None:
        return None

    extension = uploaded_file.name.rsplit(".", 1)[-1].lower()

    allowed = [
        "jpg", "jpeg", "png", "webp",
        "mp4", "mov", "webm"
    ]

    if extension not in allowed:
        st.error("Unsupported story file type.")
        return None

    file_path = (
        f"stories/{user_id}/{uuid.uuid4().hex}.{extension}"
    )

    content_type = (
        uploaded_file.type
        or mimetypes.guess_type(uploaded_file.name)[0]
        or "application/octet-stream"
    )

    try:
        supabase.storage.from_(MEDIA_BUCKET).upload(
            file_path,
            uploaded_file.getvalue(),
            {
                "content-type": content_type,
                "upsert": "false",
            }
        )

        return file_path

    except Exception as e:
        st.error(f"Could not upload story media: {e}")
        return None


def create_story(
    supabase,
    user_id,
    caption,
    media_path,
    media_type
):
    try:
        now = eco_now()

        supabase.table("stories").insert({
            "user_id": str(user_id),
            "caption": caption.strip(),
            "media_url": media_path,
            "media_type": media_type or "",
            "created_at": now.isoformat(),
            "expires_at": (
                now + timedelta(hours=24)
            ).isoformat(),
        }).execute()

        return True

    except Exception as e:
        st.error(f"Could not publish story: {e}")
        return False


def get_active_stories(supabase):
    try:
        result = (
            supabase.table("stories")
            .select("*")
            .gt("expires_at", eco_now().isoformat())
            .order("created_at", desc=True)
            .execute()
        )

        return result.data or []

    except Exception as e:
        st.error(f"Could not load stories: {e}")
        return []


def render_story_card(supabase, story, current_user_id):
    owner_id = story.get("user_id")
    profile = eco_profile(supabase, owner_id)

    name = (
        profile.get("display_name")
        or profile.get("username")
        or "EcoLoop Member"
    )

    username = profile.get("username") or "member"
    avatar = profile.get("avatar_url") or ""

    with st.container(border=True):
        col1, col2 = st.columns([1, 4])

        with col1:
            eco_show_avatar(supabase, avatar, 50)

        with col2:
            st.markdown(f"**{eco_escape(name)}**")
            st.caption(f"@{eco_escape(username)}")

        media_url = get_story_media_url(
            supabase,
            story.get("media_url")
        )

        if media_url:
            media_type = story.get("media_type") or ""

            if media_type.startswith("image"):
                st.image(
                    media_url,
                    use_container_width=True
                )

            elif media_type.startswith("video"):
                st.video(media_url)

        if story.get("caption"):
            st.write(story.get("caption"))

        created = story.get("created_at")

        if created:
            st.caption(
                f"Posted: {str(created).replace('T', ' ')[:16]}"
            )

        if str(owner_id) == str(current_user_id):
            if st.button(
                "Delete Story",
                key=f"eco_delete_story_{story.get('id')}"
            ):
                try:
                    supabase.table("stories").delete().eq(
                        "id", str(story.get("id"))
                    ).eq(
                        "user_id", str(current_user_id)
                    ).execute()

                    st.success("Story deleted.")
                    st.rerun()

                except Exception as e:
                    st.error(f"Could not delete story: {e}")


def render_updates_page(supabase, user_id):
    st.title("📸 Stories")
    st.caption(
        "Share photos and videos with the EcoLoop community. "
        "Stories expire after 24 hours."
    )

    tab_feed, tab_create = st.tabs([
        "Recent Stories",
        "Create Story"
    ])

    with tab_feed:
        stories = get_active_stories(supabase)

        if not stories:
            st.info(
                "No active stories yet. Be the first to share one!"
            )

        for story in stories:
            render_story_card(
                supabase,
                story,
                user_id
            )

    with tab_create:
        st.subheader("Share an Update")

        uploaded_file = st.file_uploader(
            "Choose a photo or video",
            type=[
                "jpg", "jpeg", "png", "webp",
                "mp4", "mov", "webm"
            ],
            key="eco_story_upload"
        )

        caption = st.text_area(
            "Caption",
            max_chars=500,
            placeholder="Share what's happening..."
        )

        if uploaded_file:
            uploaded_type = uploaded_file.type or ""

            if uploaded_type.startswith("image"):
                st.image(
                    uploaded_file,
                    use_container_width=True
                )

            elif uploaded_type.startswith("video"):
                st.video(uploaded_file)

        if st.button(
            "Publish Story",
            use_container_width=True,
            disabled=uploaded_file is None
        ):
            media_path = upload_story_media(
                supabase,
                user_id,
                uploaded_file
            )

            if media_path:
                if create_story(
                    supabase,
                    user_id,
                    caption,
                    media_path,
                    uploaded_file.type
                ):
                    st.success("Your story has been published.")
                    st.rerun()


# ==========================================================
# PART 13 — COMMUNITY HUB NAVIGATION
# ==========================================================

def render_community_groups_page(supabase, user_id):
    eco_init_state()

    st.title("🌍 Community Hub")
    st.caption(
        "Connect, communicate and make an impact together."
    )

    active_chatroom = st.session_state.get(
        "eco_active_chatroom"
    )

    if active_chatroom:
        render_chatroom_chat(
            supabase,
            user_id,
            active_chatroom
        )
        return

    sections = [
        "Chats",
        "Chatrooms",
        "Stories",
        "Discover People",
        "My Profile",
    ]

    current_section = st.session_state.get(
        "eco_community_section",
        "Chats"
    )

    if current_section not in sections:
        current_section = "Chats"

    selected_section = st.radio(
        "Community navigation",
        sections,
        index=sections.index(current_section),
        horizontal=True,
        key="eco_community_navigation",
        label_visibility="collapsed",
    )

    st.session_state["eco_community_section"] = selected_section

    st.divider()

    if selected_section == "Chats":
        render_chats_page(supabase, user_id)

    elif selected_section == "Chatrooms":
        render_chatrooms_page(supabase, user_id)

    elif selected_section == "Stories":
        render_updates_page(supabase, user_id)

    elif selected_section == "Discover People":
        render_people_directory(supabase, user_id)

    elif selected_section == "My Profile":
        render_profile_editor(supabase, user_id)

    st.divider()
    st.caption("Powered by Next Gen Impact Hub (NGIH)")

# ==========================================================
# FIX — DISCOVER PEOPLE SEARCH
# Searches BOTH display names and usernames
# ==========================================================

def get_member_directory(supabase, search=""):
    try:
        result = (
            supabase.table("member_profiles")
            .select("*")
            .order("username")
            .limit(1000)
            .execute()
        )

        members = result.data or []

        if not search or not search.strip():
            return members

        term = search.strip().lower().lstrip("@")

        return [
            member for member in members
            if (
                term in str(member.get("username") or "").lower()
                or term in str(member.get("display_name") or "").lower()
            )
        ]

    except Exception as e:
        st.error(f"Could not search members: {e}")
        return []

# ==========================================================
# WHATSAPP-STYLE PRIVATE CHAT BUBBLES
# ==========================================================

def render_direct_chat(supabase, user_id, conversation_id):
    try:
        result = (
            supabase.table("direct_conversations")
            .select("*")
            .eq("id", str(conversation_id))
            .limit(1)
            .execute()
        )

        if not result.data:
            st.error("Conversation not found.")
            return

        conversation = result.data[0]

        participants = [
            str(conversation.get("user_one_id")),
            str(conversation.get("user_two_id")),
        ]

        if str(user_id) not in participants:
            st.error("You do not have access to this conversation.")
            return

        other_user_id = get_other_conversation_user(
            conversation, user_id
        )

        other_profile = eco_profile(supabase, other_user_id)

    except Exception as e:
        st.error(f"Could not open conversation: {e}")
        return

    col1, col2 = st.columns([1, 5])

    with col1:
        eco_show_avatar(
            supabase,
            other_profile.get("avatar_url"),
            55
        )

    with col2:
        st.markdown(
            f"### {eco_escape(other_profile.get('display_name') or 'Member')}"
        )
        st.caption(
            f"@{eco_escape(other_profile.get('username') or 'member')}"
        )

    if st.button("← Back to Chats", key="eco_back_to_chats"):
        st.session_state["eco_active_conversation"] = None
        st.rerun()

    st.divider()

    st.markdown("""
    <style>
    .eco-chat-row {
        display: flex;
        width: 100%;
        margin: 9px 0;
    }
    .eco-chat-mine {
        justify-content: flex-end;
    }
    .eco-chat-theirs {
        justify-content: flex-start;
    }
    .eco-chat-bubble {
        max-width: 78%;
        padding: 10px 14px;
        border-radius: 16px;
        overflow-wrap: anywhere;
        font-size: 15px;
        line-height: 1.5;
    }
    .eco-chat-bubble-mine {
        background: #075E45;
        color: white;
        border-bottom-right-radius: 4px;
    }
    .eco-chat-bubble-theirs {
        background: #30343B;
        color: white;
        border-bottom-left-radius: 4px;
    }
    .eco-chat-time {
        font-size: 10px;
        opacity: 0.75;
        text-align: right;
        margin-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

    messages = get_direct_messages(supabase, conversation_id)

    if not messages:
        st.info("This is the beginning of your conversation.")

    for message in messages:
        mine = str(message.get("sender_id")) == str(user_id)

        message_text = eco_escape(
            message.get("message_text") or ""
        )

        created = message.get("created_at") or ""
        timestamp = eco_escape(
            str(created).replace("T", " ")[:16]
        )

        row_class = "eco-chat-mine" if mine else "eco-chat-theirs"
        bubble_class = (
            "eco-chat-bubble-mine"
            if mine else "eco-chat-bubble-theirs"
        )

        st.markdown(
            f"""
            <div class="eco-chat-row {row_class}">
                <div class="eco-chat-bubble {bubble_class}">
                    {message_text}
                    <div class="eco-chat-time">{timestamp}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if message.get("attachment_path"):
            st.caption(
                f"📎 {eco_escape(message.get('attachment_name') or 'Attachment')}"
            )

    st.divider()

    with st.form(
        f"eco_direct_message_form_{conversation_id}",
        clear_on_submit=True
    ):
        message_text = st.text_input(
            "Message",
            placeholder="Type a message..."
        )

        submitted = st.form_submit_button(
            "➤ Send",
            use_container_width=True
        )

    if submitted and message_text.strip():
        if send_direct_message(
            supabase,
            conversation_id,
            user_id,
            message_text
        ):
            st.rerun()

# ==========================================================
# ECOLOOP NODE — MESSAGING REDESIGN
# Instagram-inspired inbox + WhatsApp-style conversations
# Private chats + chatrooms + file sharing + voice notes
# ==========================================================

import mimetypes as eco_mimetypes


# ----------------------------------------------------------
# MESSAGE MEDIA
# ----------------------------------------------------------

def eco_upload_chat_attachment(supabase, user_id, uploaded_file):
    if uploaded_file is None:
        return None

    filename = uploaded_file.name or "attachment"
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"

    safe_extensions = [
        "jpg", "jpeg", "png", "webp",
        "pdf", "doc", "docx", "xls", "xlsx",
        "ppt", "pptx", "txt", "csv",
        "mp3", "wav", "ogg", "m4a", "aac",
        "mp4", "mov", "webm", "zip"
    ]

    if extension not in safe_extensions:
        st.error("This file type is not supported.")
        return None

    content_type = (
        uploaded_file.type
        or eco_mimetypes.guess_type(filename)[0]
        or "application/octet-stream"
    )

    # Uses the existing chatrooms storage folder permission.
    # Each member uploads into their own folder.
    path = (
        f"chatrooms/{user_id}/"
        f"{uuid.uuid4().hex}.{extension}"
    )

    try:
        supabase.storage.from_(MEDIA_BUCKET).upload(
            path,
            uploaded_file.getvalue(),
            {
                "content-type": content_type,
                "upsert": "false",
            }
        )

        return {
            "path": path,
            "name": filename,
            "type": content_type,
        }

    except Exception as e:
        st.error(f"Attachment upload failed: {e}")
        return None


def eco_save_attachment_message(
    supabase,
    table,
    parent_field,
    parent_id,
    user_id,
    attachment,
    message_text=""
):
    if not attachment:
        return False

    try:
        payload = {
            parent_field: str(parent_id),
            "sender_id": str(user_id),
            "message_text": message_text.strip(),
            "attachment_path": attachment["path"],
            "attachment_name": attachment["name"],
            "attachment_type": attachment["type"],
        }

        supabase.table(table).insert(payload).execute()
        return True

    except Exception as e:
        st.error(f"Could not send attachment: {e}")
        return False


def eco_render_message_attachment(supabase, message):
    path = message.get("attachment_path")

    if not path:
        return

    url = get_story_media_url(supabase, path)

    if not url:
        st.caption("📎 Attachment unavailable")
        return

    filename = message.get("attachment_name") or "Attachment"
    media_type = message.get("attachment_type") or ""

    if media_type.startswith("image/"):
        st.image(url, use_container_width=True)

    elif media_type.startswith("audio/"):
        st.audio(url)

    elif media_type.startswith("video/"):
        st.video(url)

    else:
        st.link_button(
            f"📎 {filename}",
            url,
            use_container_width=True
        )


# ----------------------------------------------------------
# MESSAGE BUBBLE STYLING
# ----------------------------------------------------------

def eco_message_styles():
    st.markdown("""
    <style>
    .eco-message-row {
        display: flex;
        width: 100%;
        margin: 10px 0;
    }

    .eco-message-left {
        justify-content: flex-start;
    }

    .eco-message-right {
        justify-content: flex-end;
    }

    .eco-message-bubble {
        max-width: 78%;
        padding: 11px 15px;
        border-radius: 19px;
        overflow-wrap: anywhere;
        font-size: 15px;
        line-height: 1.5;
        box-shadow: 0 2px 7px rgba(0,0,0,0.12);
    }

    .eco-message-sent {
        background: #075E45;
        color: #FFFFFF;
        border-bottom-right-radius: 5px;
    }

    .eco-message-received {
        background: #30343B;
        color: #FFFFFF;
        border-bottom-left-radius: 5px;
    }

    .eco-message-sender {
        font-size: 11px;
        font-weight: 700;
        color: #70D6A7;
        margin-bottom: 4px;
    }

    .eco-message-time {
        font-size: 10px;
        opacity: 0.7;
        text-align: right;
        margin-top: 6px;
    }

    .eco-inbox-heading {
        font-size: 22px;
        font-weight: 800;
        letter-spacing: -0.5px;
    }

    .eco-inbox-subtitle {
        opacity: 0.7;
        font-size: 13px;
    }

    .eco-chat-divider {
        margin-top: 12px;
        margin-bottom: 12px;
        border-bottom: 1px solid rgba(128,128,128,0.2);
    }
    </style>
    """, unsafe_allow_html=True)


def eco_render_bubble(
    message,
    user_id,
    supabase,
    group_chat=False
):
    mine = str(message.get("sender_id")) == str(user_id)

    row_class = (
        "eco-message-right" if mine
        else "eco-message-left"
    )

    bubble_class = (
        "eco-message-sent" if mine
        else "eco-message-received"
    )

    text_content = eco_escape(
        message.get("message_text") or ""
    )

    created = message.get("created_at") or ""
    timestamp = eco_escape(
        str(created).replace("T", " ")[:16]
    )

    sender_html = ""

    if group_chat and not mine:
        sender = eco_escape(
            eco_member_name(
                supabase,
                message.get("sender_id")
            )
        )

        sender_html = (
            f'<div class="eco-message-sender">{sender}</div>'
        )

    st.markdown(
        f"""
        <div class="eco-message-row {row_class}">
            <div class="eco-message-bubble {bubble_class}">
                {sender_html}
                {text_content}
                <div class="eco-message-time">{timestamp}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if message.get("attachment_path"):
        attachment_col1, attachment_col2, attachment_col3 = (
            st.columns([1, 3, 1])
        )

        with attachment_col2:
            eco_render_message_attachment(
                supabase,
                message
            )


# ----------------------------------------------------------
# MESSAGE COMPOSER
# ----------------------------------------------------------

def eco_message_composer(
    supabase,
    user_id,
    parent_id,
    is_group=False
):
    table = "group_messages" if is_group else "direct_messages"

    parent_field = "group_id" if is_group else "conversation_id"

    st.markdown("")

    with st.expander("＋ Attach a file or send a voice note"):
        uploaded_file = st.file_uploader(
            "Choose a file",
            key=f"eco_attach_{parent_id}",
            help="Photos, documents, audio and video files."
        )

        audio_recorder = getattr(st, "audio_input", None)

        recorded_audio = None

        if audio_recorder:
            recorded_audio = audio_recorder(
                "Record a voice note",
                key=f"eco_voice_{parent_id}"
            )
        else:
            st.caption(
                "Voice recording requires a Streamlit version "
                "that supports audio_input."
            )

        if uploaded_file:
            st.caption(f"Selected: {uploaded_file.name}")

        if recorded_audio:
            st.audio(recorded_audio)

        if st.button(
            "Send Attachment",
            key=f"eco_send_attachment_{parent_id}",
            use_container_width=True,
            disabled=not uploaded_file and not recorded_audio
        ):
            source_file = uploaded_file

            if recorded_audio:
                source_file = recorded_audio

                if not getattr(source_file, "name", None):
                    source_file.name = (
                        f"voice_note_{uuid.uuid4().hex}.wav"
                    )

                if not getattr(source_file, "type", None):
                    source_file.type = "audio/wav"

            attachment = eco_upload_chat_attachment(
                supabase,
                user_id,
                source_file
            )

            if attachment:
                success = eco_save_attachment_message(
                    supabase,
                    table,
                    parent_field,
                    parent_id,
                    user_id,
                    attachment
                )

                if success:
                    st.success("Attachment sent!")
                    st.rerun()

    with st.form(
        f"eco_new_message_{parent_id}",
        clear_on_submit=True
    ):
        col1, col2 = st.columns([5, 1])

        with col1:
            message_text = st.text_input(
                "Message",
                placeholder="Write a message...",
                label_visibility="collapsed"
            )

        with col2:
            submitted = st.form_submit_button(
                "➤",
                use_container_width=True
            )

    if submitted and message_text.strip():
        if is_group:
            success = send_chatroom_message(
                supabase,
                parent_id,
                user_id,
                message_text
            )
        else:
            success = send_direct_message(
                supabase,
                parent_id,
                user_id,
                message_text
            )

        if success:
            st.rerun()


# ----------------------------------------------------------
# PRIVATE CHAT — NEW DESIGN
# ----------------------------------------------------------

def render_direct_chat(supabase, user_id, conversation_id):
    try:
        result = (
            supabase.table("direct_conversations")
            .select("*")
            .eq("id", str(conversation_id))
            .limit(1)
            .execute()
        )

        if not result.data:
            st.error("Conversation not found.")
            return

        conversation = result.data[0]

        participants = [
            str(conversation.get("user_one_id")),
            str(conversation.get("user_two_id"))
        ]

        if str(user_id) not in participants:
            st.error("You do not have access to this conversation.")
            return

        other_id = get_other_conversation_user(
            conversation,
            user_id
        )

        profile = eco_profile(supabase, other_id)

    except Exception as e:
        st.error(f"Could not open conversation: {e}")
        return

    eco_message_styles()

    col1, col2, col3 = st.columns([1, 4, 1])

    with col1:
        eco_show_avatar(
            supabase,
            profile.get("avatar_url"),
            55
        )

    with col2:
        st.markdown(
            f"**{eco_escape(profile.get('display_name') or 'Member')}**"
        )
        st.caption(
            f"@{eco_escape(profile.get('username') or 'member')}"
        )

    with col3:
        if st.button(
            "⋯",
            key=f"eco_private_options_{conversation_id}"
        ):
            st.info("More conversation options will be added.")

    if st.button(
        "← Inbox",
        key=f"eco_private_back_{conversation_id}"
    ):
        st.session_state["eco_active_conversation"] = None
        st.rerun()

    st.divider()

    messages = get_direct_messages(
        supabase,
        conversation_id
    )

    if not messages:
        st.info("Say hello and start your conversation.")

    for message in messages:
        eco_render_bubble(
            message,
            user_id,
            supabase
        )

    st.divider()

    eco_message_composer(
        supabase,
        user_id,
        conversation_id,
        False
    )


# ----------------------------------------------------------
# PRIVATE INBOX — INSTAGRAM-INSPIRED DESIGN
# ----------------------------------------------------------

def render_chats_page(supabase, user_id):
    eco_message_styles()

    active = st.session_state.get(
        "eco_active_conversation"
    )

    if active:
        render_direct_chat(
            supabase,
            user_id,
            active
        )
        return

    st.markdown(
        '<div class="eco-inbox-heading">Messages</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="eco-inbox-subtitle">'
        'Your EcoLoop conversations'
        '</div>',
        unsafe_allow_html=True
    )

    st.write("")

    col1, col2 = st.columns([5, 1])

    with col1:
        search = st.text_input(
            "Search",
            placeholder="Search conversations...",
            key="eco_chat_inbox_search",
            label_visibility="collapsed"
        )

    with col2:
        if st.button(
            "✚",
            key="eco_compose_button",
            help="New message",
            use_container_width=True
        ):
            st.session_state["eco_show_new_chat"] = True
            st.rerun()

    if st.session_state.get("eco_show_new_chat"):
        if st.button(
            "← Back",
            key="eco_new_chat_back"
        ):
            st.session_state["eco_show_new_chat"] = False
            st.rerun()

        render_new_chat_picker(
            supabase,
            user_id
        )
        return

    conversations = get_direct_conversations(
        supabase,
        user_id
    )

    inbox = []

    for conversation in conversations:
        other_id = get_other_conversation_user(
            conversation,
            user_id
        )

        profile = eco_profile(
            supabase,
            other_id
        )

        name = (
            profile.get("display_name")
            or "EcoLoop Member"
        )

        username = profile.get("username") or "member"

        if search:
            term = search.strip().lower()

            if (
                term not in name.lower()
                and term not in username.lower()
            ):
                continue

        messages = get_direct_messages(
            supabase,
            conversation.get("id")
        )

        last = messages[-1] if messages else {}

        preview = (
            last.get("message_text")
            or (
                "📎 Attachment"
                if last.get("attachment_path")
                else "Start a conversation"
            )
        )

        inbox.append({
            "conversation": conversation,
            "profile": profile,
            "other_id": other_id,
            "name": name,
            "username": username,
            "preview": preview,
            "time": last.get("created_at") or ""
        })

    if not inbox:
        st.info(
            "No conversations yet. Tap ✚ to start a new message."
        )
        return

    for item in inbox:
        conversation_id = item["conversation"].get("id")
        profile = item["profile"]
        other_id = item["other_id"]

        with st.container(border=True):
            avatar_col, details_col, action_col = st.columns(
                [1, 4, 1]
            )

            with avatar_col:
                eco_show_avatar(
                    supabase,
                    profile.get("avatar_url"),
                    55
                )

            with details_col:
                st.markdown(
                    f"**{eco_escape(item['name'])}**"
                )

                st.caption(
                    f"@{eco_escape(item['username'])}"
                )

                st.caption(
                    eco_escape(str(item["preview"]))[:75]
                )

                if item["time"]:
                    st.caption(
                        str(item["time"]).replace("T", " ")[:16]
                    )

            with action_col:
                if st.button(
                    "›",
                    key=f"eco_open_inbox_{conversation_id}",
                    help="Open conversation"
                ):
                    st.session_state[
                        "eco_active_conversation"
                    ] = conversation_id
                    st.rerun()

                if st.button(
                    "👤",
                    key=f"eco_profile_inbox_{other_id}",
                    help="View profile"
                ):
                    st.session_state[
                        "eco_view_profile_id"
                    ] = str(other_id)

                    eco_set_section("Discover People")
                    st.rerun()


# ----------------------------------------------------------
# CHATROOM — NEW GROUP MESSAGE DESIGN
# ----------------------------------------------------------

def render_chatroom_chat(supabase, user_id, group_id):
    try:
        result = (
            supabase.table("community_groups")
            .select("*")
            .eq("id", str(group_id))
            .limit(1)
            .execute()
        )

        if not result.data:
            st.error("Chatroom not found.")
            return

        group = result.data[0]

    except Exception as e:
        st.error(f"Could not open chatroom: {e}")
        return

    if not is_chatroom_member(
        supabase,
        group,
        user_id
    ):
        st.warning(
            "You must be an approved member to enter this chatroom."
        )
        return

    eco_message_styles()

    image_path = group.get("image_url") or ""

    col1, col2 = st.columns([1, 5])

    with col1:
        if image_path:
            eco_show_avatar(
                supabase,
                image_path,
                60
            )
        else:
            st.markdown("## 👥")

    with col2:
        st.markdown(
            f"### {eco_escape(group.get('name') or 'Chatroom')}"
        )

        st.caption(
            group.get("description") or "EcoLoop community conversation"
        )

    if st.button(
        "← Chatrooms",
        key=f"eco_group_back_{group_id}"
    ):
        st.session_state["eco_active_chatroom"] = None
        st.rerun()

    st.divider()

    messages = get_chatroom_messages(
        supabase,
        group_id
    )

    if not messages:
        st.info("No messages yet. Start the conversation!")

    for message in messages:
        eco_render_bubble(
            message,
            user_id,
            supabase,
            group_chat=True
        )

    st.divider()

    eco_message_composer(
        supabase,
        user_id,
        group_id,
        True
    )


# ==========================================================
# END OF MESSAGING REDESIGN
# ==========================================================

# ==========================================================
# WHATSAPP-STYLE FLOATING NEW CHAT BUTTON
# ==========================================================

def render_chats_page(supabase, user_id):
    eco_message_styles()

    active = st.session_state.get("eco_active_conversation")

    if active:
        render_direct_chat(supabase, user_id, active)
        return

    st.markdown("""
    <style>
    div.st-key-eco_floating_compose button {
        position: fixed;
        right: 24px;
        bottom: 85px;
        z-index: 999999;
        width: 54px;
        height: 54px;
        min-height: 54px;
        border-radius: 50%;
        background: #20C875;
        color: white;
        border: none;
        box-shadow: 0 4px 14px rgba(0,0,0,0.3);
        font-size: 24px;
        font-weight: bold;
    }
    div.st-key-eco_floating_compose button:hover {
        background: #16A765;
        color: white;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="eco-inbox-heading">Messages</div>',
        unsafe_allow_html=True
    )
    st.caption("Your EcoLoop conversations")

    if st.session_state.get("eco_show_new_chat"):
        if st.button("← Back to messages", key="eco_float_compose_back"):
            st.session_state["eco_show_new_chat"] = False
            st.rerun()

        render_new_chat_picker(supabase, user_id)
        return

    with st.container(key="eco_floating_compose"):
        if st.button("✎", key="eco_float_compose_button",
                     help="Start a new message"):
            st.session_state["eco_show_new_chat"] = True
            st.rerun()

    search = st.text_input(
        "Search conversations",
        placeholder="Search messages...",
        key="eco_floating_inbox_search"
    )

    conversations = get_direct_conversations(supabase, user_id)

    inbox = []

    for conversation in conversations:
        other_id = get_other_conversation_user(
            conversation, user_id
        )
        profile = eco_profile(supabase, other_id)

        name = profile.get("display_name") or "EcoLoop Member"
        username = profile.get("username") or "member"

        if search:
            term = search.strip().lower()
            if term not in name.lower() and term not in username.lower():
                continue

        messages = get_direct_messages(
            supabase, conversation.get("id")
        )
        last = messages[-1] if messages else {}

        preview = (
            last.get("message_text")
            or ("📎 Attachment" if last.get("attachment_path")
                else "Start a conversation")
        )

        inbox.append((conversation, profile, other_id, name, username,
                      preview, last.get("created_at") or ""))

    if not inbox:
        st.info("No conversations yet. Tap the green button to start a chat.")

    for conversation, profile, other_id, name, username, preview, timestamp in inbox:
        conversation_id = conversation.get("id")

        with st.container(border=True):
            avatar_col, details_col, open_col = st.columns([1, 4, 1])

            with avatar_col:
                eco_show_avatar(
                    supabase,
                    profile.get("avatar_url"),
                    52
                )

            with details_col:
                st.markdown(f"**{eco_escape(name)}**")
                st.caption(f"@{eco_escape(username)}")
                st.caption(str(preview)[:70])

                if timestamp:
                    st.caption(str(timestamp).replace("T", " ")[:16])

            with open_col:
                if st.button(
                    "›",
                    key=f"eco_float_open_{conversation_id}"
                ):
                    st.session_state["eco_active_conversation"] = conversation_id
                    st.rerun()


# ==========================================================
# END FLOATING COMPOSE BUTTON
# ==========================================================

# ==========================================================
# ECOLOOP NODE — WHATSAPP-INSPIRED COMMUNITY MESSAGING V2
# Profiles | Calls | Video Notes | Floating Compose | Composer
# ==========================================================

# ----------------------------------------------------------
# 1. PROFILE VIEWER INSIDE MESSAGING
# ----------------------------------------------------------

def eco_chat_profile_viewer(supabase, member_id):
    profile = eco_profile(supabase, member_id) or {}

    st.divider()

    top1, top2 = st.columns([4, 1])

    with top1:
        st.markdown("### Member profile")

    with top2:
        if st.button("✕", key=f"eco_close_profile_{member_id}"):
            st.session_state["eco_chat_profile_id"] = None
            st.rerun()

    avatar = profile.get("avatar_url")

    if avatar:
        eco_show_avatar(supabase, avatar, 110)
    else:
        st.markdown("### 👤")

    display_name = profile.get("display_name") or "EcoLoop Member"
    username = profile.get("username") or "member"

    st.markdown(f"## {eco_escape(display_name)}")
    st.markdown(f"**@{eco_escape(username)}**")

    bio = profile.get("bio") or "This member hasn't added a bio yet."
    st.write(bio)

    if profile.get("location"):
        st.caption(f"📍 {eco_escape(profile['location'])}")

    if profile.get("country_of_origin"):
        st.caption(
            f"🌍 {eco_escape(profile['country_of_origin'])}"
        )

    st.divider()
    st.markdown("**Social profiles**")

    social_fields = [
        ("Instagram", "instagram_handle"),
        ("Facebook", "facebook_handle"),
        ("TikTok", "tiktok_handle"),
        ("LinkedIn", "linkedin_handle"),
    ]

    found_social = False

    for label, field in social_fields:
        value = profile.get(field)

        if value:
            found_social = True
            st.caption(f"{label}: {eco_escape(value)}")

    if not found_social:
        st.caption("No social profiles added.")

    if st.button(
        "Message member",
        key=f"eco_profile_message_{member_id}",
        use_container_width=True
    ):
        try:
            conversation_id = get_or_create_direct_conversation(
                supabase,
                st.session_state.get("user_id", member_id),
                member_id
            )

            st.session_state["eco_active_conversation"] = conversation_id
            st.session_state["eco_chat_profile_id"] = None
            st.rerun()

        except Exception as e:
            st.error(f"Could not open conversation: {e}")


# ----------------------------------------------------------
# 2. CALL CONTROLS — READY FOR FUTURE IN-APP CALLING
# ----------------------------------------------------------

def eco_chat_call_controls(conversation_id):
    call1, call2 = st.columns(2)

    with call1:
        if st.button(
            "📞",
            key=f"eco_voice_call_{conversation_id}",
            help="Voice call"
        ):
            st.session_state["eco_call_notice"] = "voice"

    with call2:
        if st.button(
            "📹",
            key=f"eco_video_call_{conversation_id}",
            help="Video call"
        ):
            st.session_state["eco_call_notice"] = "video"

    notice = st.session_state.get("eco_call_notice")

    if notice:
        if notice == "voice":
            st.info(
                "Voice calling is coming to EcoLoop. "
                "In-app calls are not available yet."
            )
        elif notice == "video":
            st.info(
                "Video calling is coming to EcoLoop. "
                "In-app calls are not available yet."
            )

        if st.button(
            "Close",
            key=f"eco_close_call_notice_{conversation_id}"
        ):
            st.session_state["eco_call_notice"] = None
            st.rerun()


# ----------------------------------------------------------
# 3. WHATSAPP-STYLE MESSAGE COMPOSER
# ----------------------------------------------------------

def eco_message_composer(
    supabase,
    user_id,
    parent_id,
    is_group=False
):
    table = "group_messages" if is_group else "direct_messages"
    parent_field = "group_id" if is_group else "conversation_id"

    st.markdown("---")

    # Attachment options
    with st.expander("＋ Attach / Record"):
        uploaded_file = st.file_uploader(
            "Photos, documents, audio or video",
            type=[
                "jpg", "jpeg", "png", "webp",
                "pdf", "doc", "docx", "xls", "xlsx",
                "ppt", "pptx", "txt", "csv",
                "mp3", "wav", "ogg", "m4a", "aac",
                "mp4", "mov", "webm"
            ],
            key=f"eco_v2_file_{parent_id}"
        )

        if uploaded_file:
            st.caption(f"Selected: {uploaded_file.name}")

            if uploaded_file.type.startswith("video/"):
                st.video(uploaded_file)

        audio_recorder = getattr(st, "audio_input", None)
        recorded_audio = None

        if audio_recorder:
            recorded_audio = audio_recorder(
                "🎙 Record voice note",
                key=f"eco_v2_audio_{parent_id}"
            )

        if recorded_audio:
            st.audio(recorded_audio)

        st.caption(
            "Video notes can currently be sent as uploaded video files. "
            "Direct camera recording will be added in a later update."
        )

    # Main message bar
    col_plus, col_message, col_send = st.columns(
        [0.7, 4.5, 0.9]
    )

    with col_plus:
        st.markdown("")

        if st.button(
            "＋",
            key=f"eco_v2_plus_{parent_id}",
            help="Attach a file"
        ):
            st.session_state[
                f"eco_v2_attachment_open_{parent_id}"
            ] = True

    with col_message:
        message_text = st.text_input(
            "Message",
            placeholder="Message...",
            label_visibility="collapsed",
            key=f"eco_v2_text_{parent_id}"
        )

    with col_send:
        send_clicked = st.button(
            "➤",
            key=f"eco_v2_send_{parent_id}",
            use_container_width=True,
            help="Send message"
        )

    # Open attachment panel when plus is tapped
    if st.session_state.get(
        f"eco_v2_attachment_open_{parent_id}"
    ):
        st.info(
            "Open the Attach / Record section above "
            "to choose your file or record audio."
        )

    if not send_clicked:
        return

    # If both file and audio are selected, use the uploaded file.
    selected_attachment = uploaded_file or recorded_audio

    if selected_attachment:
        attachment = eco_upload_chat_attachment(
            supabase,
            user_id,
            selected_attachment
        )

        if not attachment:
            return

        success = eco_save_attachment_message(
            supabase,
            table,
            parent_field,
            parent_id,
            user_id,
            attachment,
            message_text or ""
        )

        if success:
            st.session_state[
                f"eco_v2_attachment_open_{parent_id}"
            ] = False
            st.rerun()

        return

    if message_text and message_text.strip():
        if is_group:
            send_chatroom_message(
                supabase,
                parent_id,
                user_id,
                message_text.strip()
            )
        else:
            send_direct_message(
                supabase,
                parent_id,
                user_id,
                message_text.strip()
            )

        st.rerun()


# ----------------------------------------------------------
# 4. PRIVATE CHAT HEADER + PROFILE + CALL BUTTONS
# ----------------------------------------------------------

def render_direct_chat(supabase, user_id, conversation_id):
    profile_id = st.session_state.get("eco_chat_profile_id")

    if profile_id:
        eco_chat_profile_viewer(supabase, profile_id)
        return

    try:
        result = (
            supabase.table("direct_conversations")
            .select("*")
            .eq("id", str(conversation_id))
            .limit(1)
            .execute()
        )

        if not result.data:
            st.error("Conversation not found.")
            return

        conversation = result.data[0]

        participants = [
            str(conversation.get("user_one_id")),
            str(conversation.get("user_two_id"))
        ]

        if str(user_id) not in participants:
            st.error("You cannot access this conversation.")
            return

        other_id = get_other_conversation_user(
            conversation,
            user_id
        )

        profile = eco_profile(supabase, other_id) or {}

    except Exception as e:
        st.error(f"Could not open chat: {e}")
        return

    # WhatsApp-inspired header
    avatar_col, name_col, call_col1, call_col2 = st.columns(
        [1, 3.2, 0.8, 0.8]
    )

    with avatar_col:
        if st.button(
            "👤",
            key=f"eco_chat_profile_avatar_{conversation_id}",
            help="View profile"
        ):
            st.session_state["eco_chat_profile_id"] = str(other_id)
            st.rerun()

    with name_col:
        if st.button(
            profile.get("display_name") or "Member",
            key=f"eco_chat_profile_name_{conversation_id}"
        ):
            st.session_state["eco_chat_profile_id"] = str(other_id)
            st.rerun()

        st.caption(
            f"@{eco_escape(profile.get('username') or 'member')}"
        )

    with call_col1:
        if st.button(
            "📞",
            key=f"eco_chat_voice_{conversation_id}",
            help="Voice call"
        ):
            st.session_state["eco_call_notice"] = "voice"

    with call_col2:
        if st.button(
            "📹",
            key=f"eco_chat_video_{conversation_id}",
            help="Video call"
        ):
            st.session_state["eco_call_notice"] = "video"

    notice = st.session_state.get("eco_call_notice")

    if notice:
        st.info(
            f"{notice.title()} calling is coming soon. "
            "EcoLoop will support in-app calling in a future update."
        )

        if st.button(
            "Close",
            key=f"eco_chat_call_close_{conversation_id}"
        ):
            st.session_state["eco_call_notice"] = None
            st.rerun()

    if st.button(
        "← Messages",
        key=f"eco_chat_back_{conversation_id}"
    ):
        st.session_state["eco_active_conversation"] = None
        st.session_state["eco_chat_profile_id"] = None
        st.rerun()

    st.divider()

    messages = get_direct_messages(
        supabase,
        conversation_id
    )

    if not messages:
        st.info("This is the beginning of your conversation.")

    for message in messages:
        eco_render_bubble(
            message,
            user_id,
            supabase
        )

    eco_message_composer(
        supabase,
        user_id,
        conversation_id,
        False
    )


# ----------------------------------------------------------
# 5. INBOX WITH PROFILE ACCESS + FLOATING COMPOSE
# ----------------------------------------------------------

def render_chats_page(supabase, user_id):
    profile_id = st.session_state.get("eco_chat_profile_id")

    if profile_id:
        eco_chat_profile_viewer(supabase, profile_id)
        return

    active = st.session_state.get("eco_active_conversation")

    if active:
        render_direct_chat(
            supabase,
            user_id,
            active
        )
        return

    st.markdown("## Messages")
    st.caption("Connect and communicate with your EcoLoop community.")

    # Floating compose button
    st.markdown("""
    <style>
    div.st-key-eco_v2_floating_compose button {
        position: fixed;
        right: 23px;
        bottom: 85px;
        z-index: 999999;
        width: 57px;
        height: 57px;
        min-height: 57px;
        border-radius: 50%;
        background: #20C875;
        color: white;
        border: none;
        box-shadow: 0 4px 15px rgba(0,0,0,0.35);
        font-size: 25px;
        font-weight: bold;
    }
    div.st-key-eco_v2_floating_compose button:hover {
        background: #159B5A;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.container(key="eco_v2_floating_compose"):
        if st.button(
            "✎",
            key="eco_v2_compose_button",
            help="New message"
        ):
            st.session_state["eco_show_new_chat"] = True
            st.rerun()

    if st.session_state.get("eco_show_new_chat"):
        if st.button(
            "← Back to messages",
            key="eco_v2_back_new_chat"
        ):
            st.session_state["eco_show_new_chat"] = False
            st.rerun()

        render_new_chat_picker(
            supabase,
            user_id
        )
        return

    search = st.text_input(
        "Search",
        placeholder="Search by name or username...",
        key="eco_v2_inbox_search"
    )

    conversations = get_direct_conversations(
        supabase,
        user_id
    )

    inbox = []

    for conversation in conversations:
        other_id = get_other_conversation_user(
            conversation,
            user_id
        )

        profile = eco_profile(supabase, other_id) or {}

        name = profile.get("display_name") or "EcoLoop Member"
        username = profile.get("username") or "member"

        if search:
            term = search.strip().lower().lstrip("@")

            if (
                term not in name.lower()
                and term not in username.lower()
            ):
                continue

        messages = get_direct_messages(
            supabase,
            conversation.get("id")
        )

        last = messages[-1] if messages else {}

        preview = (
            last.get("message_text")
            or (
                "📎 Attachment"
                if last.get("attachment_path")
                else "Start a conversation"
            )
        )

        inbox.append({
            "conversation": conversation,
            "profile": profile,
            "other_id": other_id,
            "name": name,
            "username": username,
            "preview": preview,
            "time": last.get("created_at") or ""
        })

    if not inbox:
        st.info(
            "No conversations found. Use the green compose button "
            "to start a new chat."
        )
        return

    for item in inbox:
        conversation_id = item["conversation"].get("id")
        other_id = item["other_id"]
        profile = item["profile"]

        with st.container(border=True):
            avatar_col, details_col, profile_col, open_col = (
                st.columns([1, 3.5, 0.8, 0.8])
            )

            with avatar_col:
                if st.button(
                    "👤",
                    key=f"eco_v2_avatar_{other_id}",
                    help="View member profile"
                ):
                    st.session_state["eco_chat_profile_id"] = str(other_id)
                    st.rerun()

            with details_col:
                st.markdown(
                    f"**{eco_escape(item['name'])}**"
                )

                st.caption(
                    f"@{eco_escape(item['username'])}"
                )

                st.caption(
                    eco_escape(str(item["preview"]))[:75]
                )

                if item["time"]:
                    st.caption(
                        str(item["time"]).replace("T", " ")[:16]
                    )

            with profile_col:
                if st.button(
                    "ⓘ",
                    key=f"eco_v2_profile_{other_id}",
                    help="View profile"
                ):
                    st.session_state["eco_chat_profile_id"] = str(other_id)
                    st.rerun()

            with open_col:
                if st.button(
                    "›",
                    key=f"eco_v2_open_{conversation_id}",
                    help="Open chat"
                ):
                    st.session_state[
                        "eco_active_conversation"
                    ] = conversation_id
                    st.rerun()


# ----------------------------------------------------------
# 6. CHATROOMS — PROFILE ACCESS + NEW COMPOSER
# ----------------------------------------------------------

def render_chatroom_chat(supabase, user_id, group_id):
    profile_id = st.session_state.get("eco_chat_profile_id")

    if profile_id:
        eco_chat_profile_viewer(supabase, profile_id)
        return

    try:
        result = (
            supabase.table("community_groups")
            .select("*")
            .eq("id", str(group_id))
            .limit(1)
            .execute()
        )

        if not result.data:
            st.error("Chatroom not found.")
            return

        group = result.data[0]

    except Exception as e:
        st.error(f"Could not open chatroom: {e}")
        return

    if not is_chatroom_member(
        supabase,
        group,
        user_id
    ):
        st.warning("You must be an approved member to enter this chatroom.")
        return

    col1, col2 = st.columns([1, 5])

    with col1:
        if group.get("image_url"):
            eco_show_avatar(
                supabase,
                group.get("image_url"),
                55
            )
        else:
            st.markdown("## 👥")

    with col2:
        st.markdown(
            f"### {eco_escape(group.get('name') or 'Chatroom')}"
        )
        st.caption(
            group.get("description") or "EcoLoop community"
        )

    if st.button(
        "← Chatrooms",
        key=f"eco_v2_group_back_{group_id}"
    ):
        st.session_state["eco_active_chatroom"] = None
        st.rerun()

    st.divider()

    messages = get_chatroom_messages(
        supabase,
        group_id
    )

    if not messages:
        st.info("No messages yet. Start the conversation!")

    for message in messages:
        eco_render_bubble(
            message,
            user_id,
            supabase,
            group_chat=True
        )

    eco_message_composer(
        supabase,
        user_id,
        group_id,
        True
    )


# ==========================================================
# END ECOLOOP NODE MESSAGING V2
# ==========================================================

# ==========================================================
# FIX — CLICK ANYWHERE ON INBOX CONVERSATION TO OPEN
# ==========================================================

def render_chats_page(supabase, user_id):
    profile_id = st.session_state.get("eco_chat_profile_id")

    if profile_id:
        eco_chat_profile_viewer(supabase, profile_id)
        return

    active = st.session_state.get("eco_active_conversation")

    if active:
        render_direct_chat(supabase, user_id, active)
        return

    st.markdown("## Messages")
    st.caption("Your EcoLoop conversations")

    st.markdown("""
    <style>
    div.st-key-eco_v3_compose button {
        position: fixed;
        right: 23px;
        bottom: 85px;
        z-index: 999999;
        width: 56px;
        height: 56px;
        min-height: 56px;
        border-radius: 50%;
        background: #20C875;
        color: white;
        border: none;
        font-size: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,.3);
    }
    </style>
    """, unsafe_allow_html=True)

    with st.container(key="eco_v3_compose"):
        if st.button("✎", key="eco_v3_compose_button"):
            st.session_state["eco_show_new_chat"] = True
            st.rerun()

    if st.session_state.get("eco_show_new_chat"):
        if st.button("← Back", key="eco_v3_back"):
            st.session_state["eco_show_new_chat"] = False
            st.rerun()

        render_new_chat_picker(supabase, user_id)
        return

    search = st.text_input(
        "Search",
        placeholder="Search by name or username...",
        key="eco_v3_search"
    )

    conversations = get_direct_conversations(supabase, user_id)

    for conversation in conversations:
        other_id = get_other_conversation_user(
            conversation, user_id
        )

        profile = eco_profile(supabase, other_id) or {}

        name = profile.get("display_name") or "EcoLoop Member"
        username = profile.get("username") or "member"

        if search:
            term = search.strip().lower().lstrip("@")
            if term not in name.lower() and term not in username.lower():
                continue

        messages = get_direct_messages(
            supabase, conversation.get("id")
        )

        last = messages[-1] if messages else {}

        preview = (
            last.get("message_text")
            or ("📎 Attachment" if last.get("attachment_path")
                else "Start a conversation")
        )

        conversation_id = conversation.get("id")

        with st.container(border=True):
            avatar_col, details_col, profile_col = st.columns(
                [1, 4, 0.8]
            )

            with avatar_col:
                if st.button(
                    "👤",
                    key=f"eco_v3_avatar_{other_id}",
                    help="View profile"
                ):
                    st.session_state["eco_chat_profile_id"] = str(other_id)
                    st.rerun()

            with details_col:
                # The conversation itself is now the clickable item.
                if st.button(
                    f"{name}\n@{username}\n{str(preview)[:65]}",
                    key=f"eco_v3_open_{conversation_id}",
                    use_container_width=True
                ):
                    st.session_state[
                        "eco_active_conversation"
                    ] = conversation_id
                    st.rerun()

                if last.get("created_at"):
                    st.caption(
                        str(last["created_at"]).replace("T", " ")[:16]
                    )

            with profile_col:
                if st.button(
                    "ⓘ",
                    key=f"eco_v3_info_{other_id}",
                    help="View profile"
                ):
                    st.session_state["eco_chat_profile_id"] = str(other_id)
                    st.rerun()

    st.caption("Powered by Next Gen Impact Hub (NGIH)")


# ==========================================================
# END INBOX CLICK FIX
# ==========================================================

# ==========================================================
# ECOLOOP — CLEAN WHATSAPP / INSTAGRAM STYLE INBOX
# ==========================================================

def render_chats_page(supabase, user_id):

    profile_id = st.session_state.get("eco_chat_profile_id")

    if profile_id:
        eco_chat_profile_viewer(supabase, profile_id)
        return

    active = st.session_state.get("eco_active_conversation")

    if active:
        render_direct_chat(supabase, user_id, active)
        return

    st.markdown("""
    <style>
    div.st-key-eco_v4_compose button {
        position: fixed;
        right: 22px;
        bottom: 85px;
        z-index: 999999;
        width: 55px;
        height: 55px;
        min-height: 55px;
        border-radius: 50%;
        background: #20C875;
        color: white;
        border: none;
        font-size: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,.3);
    }

    div.st-key-eco_v4_compose button:hover {
        background: #159B5A;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

    title_col, compose_col = st.columns([5, 1])

    with title_col:
        st.markdown("## Messages")

    with compose_col:
        st.write("")

    with st.container(key="eco_v4_compose"):
        if st.button("✎", key="eco_v4_compose_button",
                     help="New message"):
            st.session_state["eco_show_new_chat"] = True
            st.rerun()

    if st.session_state.get("eco_show_new_chat"):
        if st.button("← Back", key="eco_v4_back"):
            st.session_state["eco_show_new_chat"] = False
            st.rerun()

        render_new_chat_picker(supabase, user_id)
        return

    search = st.text_input(
        "Search",
        placeholder="Search people...",
        key="eco_v4_search"
    )

    conversations = get_direct_conversations(supabase, user_id)

    if not conversations:
        st.info("Your conversations will appear here.")
        return

    for conversation in conversations:

        other_id = get_other_conversation_user(
            conversation, user_id
        )

        profile = eco_profile(supabase, other_id) or {}

        name = profile.get("display_name") or "EcoLoop Member"
        username = profile.get("username") or "member"
        avatar = profile.get("avatar_url")

        if search:
            term = search.strip().lower().lstrip("@")

            if (
                term not in name.lower()
                and term not in username.lower()
            ):
                continue

        messages = get_direct_messages(
            supabase,
            conversation.get("id")
        )

        last = messages[-1] if messages else {}

        preview = (
            last.get("message_text")
            or (
                "📎 Attachment"
                if last.get("attachment_path")
                else "Start a conversation"
            )
        )

        timestamp = last.get("created_at") or ""
        conversation_id = conversation.get("id")

        with st.container(border=True):

            avatar_col, details_col, profile_col = st.columns(
                [1, 4, 0.7]
            )

            with avatar_col:
                if avatar:
                    eco_show_avatar(supabase, avatar, 54)
                else:
                    st.markdown("### 👤")

            with details_col:

                if st.button(
                    f"{name}  ·  @{username}\n{str(preview)[:65]}",
                    key=f"eco_v4_conversation_{conversation_id}",
                    use_container_width=True
                ):
                    st.session_state[
                        "eco_active_conversation"
                    ] = conversation_id
                    st.rerun()

                if timestamp:
                    st.caption(
                        str(timestamp).replace("T", " ")[:16]
                    )

            with profile_col:
                if st.button(
                    "ⓘ",
                    key=f"eco_v4_profile_{other_id}",
                    help="View profile"
                ):
                    st.session_state[
                        "eco_chat_profile_id"
                    ] = str(other_id)
                    st.rerun()

    st.caption("Powered by Next Gen Impact Hub (NGIH)")


# ==========================================================
# END — CLEAN INBOX
# ==========================================================


# ==========================================================
# ECOLOOP NODE — CHATROOMS + STORIES REDESIGN
# WhatsApp-inspired Groups and Status
# ==========================================================


# ----------------------------------------------------------
# 1. CHATROOM CARD
# ----------------------------------------------------------

def eco_render_chatroom_item(supabase, group, user_id, is_member=False):
    group_id = str(group.get("id"))
    name = group.get("name") or "EcoLoop Community"
    description = group.get("description") or "Community group"

    image_path = group.get("image_url")

    with st.container(border=True):
        image_col, details_col, action_col = st.columns([1, 3.8, 1])

        with image_col:
            if image_path:
                image_url = get_story_media_url(supabase, image_path)
                if image_url:
                    st.image(image_url, width=55)
                else:
                    st.markdown("## 👥")
            else:
                st.markdown("## 👥")

        with details_col:
            st.markdown(f"**{eco_escape(name)}**")
            st.caption(eco_escape(description)[:90])

            if str(group.get("created_by")) == str(user_id):
                st.caption("👑 Group administrator")
            elif is_member:
                st.caption("✓ Member")

        with action_col:
            if is_member:
                if st.button(
                    "Open",
                    key=f"eco_v5_open_group_{group_id}",
                    use_container_width=True
                ):
                    st.session_state["eco_active_chatroom"] = group_id
                    st.rerun()
            else:
                if st.button(
                    "Join",
                    key=f"eco_v5_join_group_{group_id}",
                    use_container_width=True
                ):
                    try:
                        request_chatroom_join(
                            supabase,
                            user_id,
                            group_id
                        )
                        st.success("Join request submitted.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not request membership: {e}")


# ----------------------------------------------------------
# 2. CHATROOMS PAGE
# ----------------------------------------------------------

def render_chatrooms_page(supabase, user_id):

    active_group = st.session_state.get("eco_active_chatroom")

    if active_group:
        render_chatroom_chat(
            supabase,
            user_id,
            active_group
        )
        return

    st.markdown("## 👥 Chatrooms")
    st.caption("Find your community. Join conversations. Make an impact.")

    discover_tab, my_tab, create_tab = st.tabs(
        ["Discover", "My Groups", "＋ Create"]
    )

    # DISCOVER GROUPS
    with discover_tab:
        search = st.text_input(
            "Search groups",
            placeholder="Search communities...",
            key="eco_v5_group_search"
        )

        groups = get_chatrooms(
            supabase,
            search
        )

        if not groups:
            st.info("No communities found.")
        else:
            for group in groups:
                is_member = is_chatroom_member(
                    supabase,
                    group,
                    user_id
                )

                eco_render_chatroom_item(
                    supabase,
                    group,
                    user_id,
                    is_member
                )

                if str(group.get("created_by")) == str(user_id):
                    with st.expander(
                        f"Manage requests — {group.get('name')}"
                    ):
                        manage_chatroom_requests(
                            supabase,
                            group
                        )

    # MY GROUPS
    with my_tab:
        my_groups = get_my_chatrooms(
            supabase,
            user_id
        )

        if not my_groups:
            st.info(
                "You haven't joined any groups yet. "
                "Explore communities in Discover."
            )
        else:
            for group in my_groups:
                eco_render_chatroom_item(
                    supabase,
                    group,
                    user_id,
                    True
                )

                if str(group.get("created_by")) == str(user_id):
                    with st.expander(
                        f"Manage requests — {group.get('name')}"
                    ):
                        manage_chatroom_requests(
                            supabase,
                            group
                        )

                elif is_chatroom_member(
                    supabase,
                    group,
                    user_id
                ):
                    with st.expander(
                        f"Group options — {group.get('name')}"
                    ):
                        if st.button(
                            "Leave group",
                            key=f"eco_v5_leave_{group.get('id')}"
                        ):
                            try:
                                leave_chatroom(
                                    supabase,
                                    user_id,
                                    group.get("id")
                                )
                                st.success("You left the group.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Could not leave group: {e}")

    # CREATE GROUP
    with create_tab:
        st.markdown("### Create a community")

        with st.form("eco_v5_create_group_form"):
            group_name = st.text_input(
                "Group name",
                placeholder="e.g. Bulawayo Climate Action"
            )

            group_description = st.text_area(
                "Description",
                placeholder="What is this group about?"
            )

            group_location = st.text_input(
                "Location (optional)",
                placeholder="e.g. Bulawayo"
            )

            group_image = st.file_uploader(
                "Group picture (optional)",
                type=["jpg", "jpeg", "png", "webp"],
                key="eco_v5_group_image"
            )

            create_clicked = st.form_submit_button(
                "Create group",
                use_container_width=True
            )

        if create_clicked:
            if not group_name.strip():
                st.warning("Enter a group name.")
            else:
                image_path = ""

                if group_image:
                    uploaded = eco_upload_image(
                        supabase,
                        user_id,
                        group_image,
                        "chatrooms"
                    )

                    image_path = uploaded or ""

                try:
                    result = create_chatroom(
                        supabase,
                        user_id,
                        group_name.strip(),
                        group_description.strip(),
                        image_path=image_path,
                        location=group_location.strip()
                    )

                    if result:
                        st.success("Your group has been created!")
                        st.rerun()

                except TypeError:
                    # Compatibility with the original four-argument helper.
                    result = create_chatroom(
                        supabase,
                        user_id,
                        group_name.strip(),
                        group_description.strip()
                    )

                    if result:
                        st.success("Your group has been created!")
                        st.rerun()

                except Exception as e:
                    st.error(f"Could not create group: {e}")

    st.caption("Powered by Next Gen Impact Hub (NGIH)")


# ----------------------------------------------------------
# 3. STORY STATUS VIEWER
# ----------------------------------------------------------

def eco_render_status_viewer(supabase, story, user_id):

    story_user_id = story.get("user_id")
    profile = eco_profile(supabase, story_user_id) or {}

    name = (
        "Your status"
        if str(story_user_id) == str(user_id)
        else profile.get("display_name") or "EcoLoop Member"
    )

    st.markdown(f"### {eco_escape(name)}")

    avatar = profile.get("avatar_url")

    if avatar:
        eco_show_avatar(supabase, avatar, 45)

    media_path = (
        story.get("media_url")
        or story.get("media_path")
    )

    media_url = get_story_media_url(
        supabase,
        media_path
    ) if media_path else None

    media_type = story.get("media_type") or ""

    if media_url:
        if media_type.startswith("video/"):
            st.video(media_url)
        elif media_type.startswith("image/"):
            st.image(media_url, use_container_width=True)
        else:
            st.info("Status media")
            st.link_button("Open attachment", media_url)

    caption = story.get("caption") or ""

    if caption:
        st.markdown(f"**{eco_escape(caption)}**")

    created = story.get("created_at") or ""

    if created:
        st.caption(
            str(created).replace("T", " ")[:16]
        )

    if st.button(
        "← Back to Status",
        key=f"eco_v5_status_back_{story.get('id')}"
    ):
        st.session_state["eco_active_story"] = None
        st.rerun()


# ----------------------------------------------------------
# 4. WHATSAPP-STYLE STATUS PAGE
# ----------------------------------------------------------

def render_updates_page(supabase, user_id):

    active_story_id = st.session_state.get("eco_active_story")

    stories = get_active_stories(supabase) or []

    if active_story_id:
        selected = next(
            (
                story for story in stories
                if str(story.get("id")) == str(active_story_id)
            ),
            None
        )

        if selected:
            eco_render_status_viewer(
                supabase,
                selected,
                user_id
            )
            return

        st.session_state["eco_active_story"] = None

    st.markdown("## Updates")
    st.caption("Share moments with your EcoLoop community.")

    # MY STATUS
    my_stories = [
        story for story in stories
        if str(story.get("user_id")) == str(user_id)
    ]

    st.markdown("### My Status")

    col1, col2 = st.columns([1, 4])

    with col1:
        if my_stories:
            my_profile = eco_profile(supabase, user_id) or {}

            if my_profile.get("avatar_url"):
                eco_show_avatar(
                    supabase,
                    my_profile.get("avatar_url"),
                    58
                )
            else:
                st.markdown("## 👤")

        else:
            st.markdown("## ➕")

    with col2:
        if my_stories:
            st.markdown("**My updates**")
            st.caption(f"{len(my_stories)} active status update(s)")

            if st.button(
                "View my status",
                key="eco_v5_my_status"
            ):
                st.session_state["eco_active_story"] = str(
                    my_stories[-1].get("id")
                )
                st.rerun()
        else:
            st.markdown("**Add a status**")
            st.caption("Share a photo, video or thought.")

    # ADD STATUS
    with st.expander("＋ Add a status"):
        with st.form("eco_v5_add_status_form"):
            status_file = st.file_uploader(
                "Choose a photo or video",
                type=[
                    "jpg", "jpeg", "png", "webp",
                    "mp4", "mov", "webm"
                ],
                key="eco_v5_status_file"
            )

            status_caption = st.text_area(
                "Caption",
                placeholder="What's happening?"
            )

            status_submit = st.form_submit_button(
                "Share status",
                use_container_width=True
            )

        if status_submit:
            if not status_file and not status_caption.strip():
                st.warning("Add a photo, video or caption first.")
            else:
                media_path = None
                media_type = None

                if status_file:
                    media_path = upload_story_media(
                        supabase,
                        user_id,
                        status_file
                    )

                    media_type = (
                        status_file.type
                        or "application/octet-stream"
                    )

                try:
                    result = create_story(
                        supabase,
                        user_id,
                        status_caption.strip(),
                        media_path,
                        media_type
                    )

                    if result:
                        st.success("Status shared!")
                        st.rerun()

                except Exception as e:
                    st.error(f"Could not share status: {e}")

    st.divider()

    # RECENT UPDATES
    st.markdown("### Recent Updates")

    other_stories = [
        story for story in stories
        if str(story.get("user_id")) != str(user_id)
    ]

    # Group stories by member, keeping the latest first.
    grouped = {}

    for story in other_stories:
        member_id = str(story.get("user_id"))

        grouped.setdefault(member_id, []).append(story)

    if not grouped:
        st.info(
            "No recent updates yet. "
            "When community members share statuses, they'll appear here."
        )

    for member_id, member_stories in grouped.items():

        latest = member_stories[-1]
        profile = eco_profile(supabase, member_id) or {}

        name = profile.get("display_name") or "EcoLoop Member"
        username = profile.get("username") or "member"

        with st.container(border=True):
            avatar_col, details_col, view_col = st.columns(
                [1, 3.5, 1]
            )

            with avatar_col:
                if profile.get("avatar_url"):
                    eco_show_avatar(
                        supabase,
                        profile.get("avatar_url"),
                        55
                    )
                else:
                    st.markdown("## 👤")

            with details_col:
                st.markdown(f"**{eco_escape(name)}**")
                st.caption(f"@{eco_escape(username)}")

                caption = latest.get("caption") or "New status update"
                st.caption(eco_escape(caption)[:65])

                if len(member_stories) > 1:
                    st.caption(
                        f"{len(member_stories)} updates"
                    )

            with view_col:
                if st.button(
                    "View",
                    key=f"eco_v5_view_status_{member_id}"
                ):
                    st.session_state["eco_active_story"] = str(
                        latest.get("id")
                    )
                    st.rerun()

    st.caption("Powered by Next Gen Impact Hub (NGIH)")


# ==========================================================
# END CHATROOMS + STORIES REDESIGN
# ==========================================================


# ==========================================================
# ECOLOOP NODE — EXACT WHATSAPP-STYLE PRIVATE CHAT
# CONVERSATION SCREEN OVERRIDE
# ==========================================================

import streamlit as st
import html


# ----------------------------------------------------------
# WHATSAPP-STYLE MESSAGE BUBBLES
# ----------------------------------------------------------

def eco_render_bubble(message, user_id, supabase, group_chat=False):

    mine = str(message.get("sender_id")) == str(user_id)

    message_text = html.escape(
        str(message.get("message_text") or "")
    ).replace("\n", "<br>")

    created = str(message.get("created_at") or "")
    timestamp = created.replace("T", " ")[:16]

    background = "#075E45" if mine else "#FFFFFF"
    text_color = "#FFFFFF" if mine else "#202124"

    alignment = "flex-end" if mine else "flex-start"

    radius = (
        "18px 18px 4px 18px"
        if mine else "18px 18px 18px 4px"
    )

    sender_html = ""

    if group_chat and not mine:
        sender_name = eco_member_name(
            supabase,
            message.get("sender_id")
        )

        sender_html = f"""
        <div style="font-size:12px;color:#16865B;
                    font-weight:700;margin-bottom:5px;">
            {html.escape(str(sender_name))}
        </div>
        """

    bubble = f"""
    <div style="
        display:flex;
        justify-content:{alignment};
        width:100%;
        margin:7px 0;
    ">
        <div style="
            max-width:82%;
            min-width:65px;
            background:{background};
            color:{text_color};
            padding:10px 13px;
            border-radius:{radius};
            font-size:14px;
            line-height:1.5;
            overflow-wrap:anywhere;
            box-shadow:0 1px 2px rgba(0,0,0,.12);
        ">
            {sender_html}
            {message_text}
            <div style="
                text-align:right;
                font-size:10px;
                opacity:.65;
                margin-top:5px;
            ">
                {html.escape(timestamp)}
                {" ✓✓" if mine else ""}
            </div>
        </div>
    </div>
    """

    st.markdown(bubble, unsafe_allow_html=True)

    if message.get("attachment_path"):
        eco_render_message_attachment(supabase, message)


# ----------------------------------------------------------
# PRIVATE CHAT SCREEN
# ----------------------------------------------------------

def render_direct_chat(supabase, user_id, conversation_id):

    # Profile viewer
    profile_id = st.session_state.get(
        "eco_chat_profile_id"
    )

    if profile_id:
        eco_chat_profile_viewer(
            supabase,
            profile_id
        )
        return

    # Retrieve conversation
    try:
        result = (
            supabase.table("direct_conversations")
            .select("*")
            .eq("id", str(conversation_id))
            .limit(1)
            .execute()
        )

        if not result.data:
            st.error("Conversation not found.")
            return

        conversation = result.data[0]

        participants = [
            str(conversation.get("user_one_id")),
            str(conversation.get("user_two_id"))
        ]

        if str(user_id) not in participants:
            st.error("You cannot access this conversation.")
            return

        other_id = get_other_conversation_user(
            conversation,
            user_id
        )

        profile = eco_profile(
            supabase,
            other_id
        ) or {}

    except Exception as e:
        st.error(f"Unable to open conversation: {e}")
        return

    display_name = (
        profile.get("display_name")
        or "EcoLoop Member"
    )

    username = (
        profile.get("username")
        or "member"
    )

    # ------------------------------------------------------
    # CHAT SCREEN STYLING
    # ------------------------------------------------------

    st.markdown("""
    <style>

    .eco-wa-header {
        background:#075E45;
        padding:12px 10px;
        border-radius:12px 12px 0 0;
        color:white;
        margin-bottom:8px;
    }

    .eco-wa-name {
        font-size:16px;
        font-weight:700;
        color:white;
    }

    .eco-wa-status {
        font-size:11px;
        color:#D5EEE3;
    }

    div[data-testid="stButton"] button {
        border-radius:22px;
    }

    </style>
    """, unsafe_allow_html=True)

    # ------------------------------------------------------
    # HEADER
    # ------------------------------------------------------

    st.markdown(
        '<div class="eco-wa-header"></div>',
        unsafe_allow_html=True
    )

    back_col, avatar_col, name_col, video_col, phone_col, menu_col = (
        st.columns([0.45, 0.8, 3.0, 0.65, 0.65, 0.45])
    )

    with back_col:
        if st.button(
            "‹",
            key=f"eco_wa_back_{conversation_id}"
        ):
            st.session_state["eco_active_conversation"] = None
            st.session_state["eco_pending_call"] = None
            st.rerun()

    with avatar_col:
        if profile.get("avatar_url"):
            eco_show_avatar(
                supabase,
                profile.get("avatar_url"),
                42
            )
        else:
            st.markdown("👤")

    with name_col:
        if st.button(
            display_name,
            key=f"eco_wa_profile_{conversation_id}"
        ):
            st.session_state["eco_chat_profile_id"] = str(other_id)
            st.rerun()

        st.caption(f"@{username}")

    with video_col:
        if st.button(
            "📹",
            key=f"eco_wa_video_{conversation_id}"
        ):
            st.session_state["eco_pending_call"] = "video"

    with phone_col:
        if st.button(
            "📞",
            key=f"eco_wa_phone_{conversation_id}"
        ):
            st.session_state["eco_pending_call"] = "voice"

    with menu_col:
        if st.button(
            "⋮",
            key=f"eco_wa_menu_{conversation_id}"
        ):
            st.session_state["eco_chat_profile_id"] = str(other_id)
            st.rerun()

    # Call placeholders
    pending_call = st.session_state.get(
        "eco_pending_call"
    )

    if pending_call:
        call_name = (
            "Video calling"
            if pending_call == "video"
            else "Voice calling"
        )

        st.info(
            f"{call_name} is coming soon to EcoLoop Node."
        )

        if st.button(
            "Close",
            key=f"eco_wa_close_call_{conversation_id}"
        ):
            st.session_state["eco_pending_call"] = None
            st.rerun()

    # ------------------------------------------------------
    # CHAT BACKGROUND
    # ------------------------------------------------------

    st.markdown("""
    <div style="
        background:#E8E2D8;
        height:8px;
        border-radius:5px;
        margin:5px 0 12px 0;
    "></div>
    """, unsafe_allow_html=True)

    # ------------------------------------------------------
    # MESSAGE HISTORY
    # ------------------------------------------------------

    messages = get_direct_messages(
        supabase,
        conversation_id
    )

    if not messages:
        st.markdown("""
        <div style="
            text-align:center;
            padding:35px 10px;
            color:#777;
            font-size:13px;
        ">
            This is the beginning of your conversation.
        </div>
        """, unsafe_allow_html=True)

    else:
        for message in messages:

            eco_render_bubble(
                message,
                user_id,
                supabase,
                False
            )

    # ------------------------------------------------------
    # COMPOSER
    # ------------------------------------------------------

    st.markdown("---")

    eco_message_composer(
        supabase,
        user_id,
        conversation_id,
        False
    )

    st.caption("Powered by Next Gen Impact Hub (NGIH)")


# ==========================================================
# END — WHATSAPP-STYLE PRIVATE CHAT OVERRIDE
# ==========================================================
