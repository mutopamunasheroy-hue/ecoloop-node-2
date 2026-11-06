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
# CORE HELPERS
# ==========================================================

def eco_now():
    return datetime.now(timezone.utc)


def eco_escape(value):
    if value is None:
        return ""
    return html.escape(str(value))


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

    if username:
        return f"@{username}"

    return "@member"


def eco_avatar(supabase, user_id):
    profile = eco_profile(supabase, user_id)

    return profile.get("avatar_url") or ""


def eco_set_section(section):
    st.session_state["eco_community_section"] = section


def eco_error(message):
    st.error(message)


def eco_success(message):
    st.success(message)


def eco_init_state():
    defaults = {
        "eco_community_section": "Chats",
        "eco_active_conversation": None,
        "eco_active_chatroom": None,
        "eco_profile_view": None,
        "eco_chat_search": "",
        "eco_people_search": "",
        "eco_chatroom_search": "",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ==========================================================
# PART 2 — MEMBER PROFILES
# ==========================================================

def upload_profile_photo(supabase, user_id, uploaded_file):
    if not uploaded_file:
        return ""

    try:
        extension = uploaded_file.name.rsplit(".", 1)[-1].lower()

        if extension not in ["jpg", "jpeg", "png", "webp"]:
            st.error("Please upload a JPG, PNG or WEBP image.")
            return None

        file_path = (
            f"profiles/{user_id}/{uuid.uuid4().hex}.{extension}"
        )

        supabase.storage.from_(MEDIA_BUCKET).upload(
            file_path,
            uploaded_file.getvalue(),
            {
                "content-type": uploaded_file.type,
                "upsert": "true",
            }
        )

        return file_path

    except Exception as e:
        st.error(f"Could not upload profile picture: {e}")
        return None


def get_member_directory(supabase, search=""):
    try:
        query = (
            supabase.table("member_profiles")
            .select("*")
            .order("username")
        )

        if search:
            query = query.ilike("username", f"%{search}%")

        result = query.limit(100).execute()
        return result.data or []

    except Exception as e:
        st.error(f"Could not load members: {e}")
        return []

def init_follow_state():
    if "eco_following" not in st.session_state:
        st.session_state["eco_following"] = set()


def init_follow_state():
    if "eco_following" not in st.session_state:
        st.session_state["eco_following"] = set()


def render_follow_controls(member_id):
    init_follow_state()

    following = st.session_state["eco_following"]
    is_following = str(member_id) in following

    if is_following:
        if st.button("Following ✓", key=f"unfollow_{member_id}"):
            following.discard(str(member_id))
            st.rerun()
    else:
        if st.button("＋ Follow", key=f"follow_{member_id}"):
            following.add(str(member_id))
            st.rerun()

def save_member_profile(
    supabase,
    user_id,
    display_name,
    username,
    avatar_path,
    bio,
    location,
    interests,
):
    username = username.strip().lower().replace("@", "")

    if not username:
        st.error("Please enter a username.")
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
            "avatar_url": avatar_path,
            "bio": bio.strip(),
            "location": location.strip(),
            "interests": interests.strip(),
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
    st.caption("Let other EcoLoop members get to know you.")

    current_avatar = profile.get("avatar_url") or ""

    if current_avatar:
        avatar_url = get_story_media_url(supabase, current_avatar)
        if avatar_url:
            st.image(avatar_url, width=120)

    uploaded_photo = st.file_uploader(
        "Upload profile picture from your device",
        type=["jpg", "jpeg", "png", "webp"],
        key="eco_profile_photo"
    )

    if uploaded_photo:
        st.image(uploaded_photo, width=120)

    with st.form("eco_profile_form"):
        display_name = st.text_input(
            "Display name",
            value=profile.get("display_name") or ""
        )

        username = st.text_input(
            "Username",
            value=profile.get("username") or "",
            help="Choose a unique username people can search for."
        )

        bio = st.text_area(
            "About me",
            value=profile.get("bio") or "",
            max_chars=300
        )

        location = st.text_input(
            "Location",
            value=profile.get("location") or ""
        )

        interests = st.text_input(
            "Interests",
            value=profile.get("interests") or ""
        )

        submitted = st.form_submit_button(
            "Save Profile",
            use_container_width=True
        )

    if submitted:
        avatar_path = current_avatar

        if uploaded_photo:
            new_path = upload_profile_photo(
                supabase,
                user_id,
                uploaded_photo
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
        )

        if saved:
            st.rerun()


def render_public_profile(supabase, user_id, member):
    st.button(
        "← Back to Discover",
        key="eco_back_to_discover",
        on_click=lambda: st.session_state.pop(
            "eco_view_profile_id", None
        )
    )

    name = member.get("display_name") or "EcoLoop Member"
    username = member.get("username") or "member"
    avatar = member.get("avatar_url") or ""
    bio = member.get("bio") or ""
    location = member.get("location") or ""
    interests = member.get("interests") or ""

    st.subheader("Member Profile")

    if avatar:
        avatar_url = get_story_media_url(supabase, avatar)

        if avatar_url:
            st.image(avatar_url, width=150)
        else:
            st.markdown("### 👤")
    else:
        st.markdown("### 👤")

    st.title(name)
    st.caption(f"@{username}")
    render_follow_controls(member.get("user_id"))

    if location:
        st.caption(f"📍 {location}")

    st.divider()

    st.markdown("**About**")
    st.write(bio or "No bio added yet.")

    st.markdown("**Interests**")
    st.write(interests or "No interests added yet.")

    st.divider()

    if st.button(
        "Message",
        key=f"eco_public_profile_message_{member.get('user_id')}",
        use_container_width=True
    ):
        conversation_id = get_or_create_direct_conversation(
            supabase,
            user_id,
            member.get("user_id")
        )

        if conversation_id:
            st.session_state["eco_active_conversation"] = conversation_id
            eco_set_section("Chats")
            st.rerun()


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

        st.session_state.pop("eco_view_profile_id", None)

    st.subheader("Discover People")
    st.caption("Find people and explore their profiles.")

    search = st.text_input(
        "Search by username",
        key="eco_people_search"
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
        name = member.get("display_name") or "EcoLoop Member"
        username = member.get("username") or "member"
        avatar = member.get("avatar_url") or ""
        bio = member.get("bio") or ""
        location = member.get("location") or ""

        with st.container(border=True):
            col1, col2 = st.columns([1, 4])

            with col1:
                if avatar:
                    avatar_url = get_story_media_url(
                        supabase,
                        avatar
                    )

                    if avatar_url:
                        st.image(avatar_url, width=70)
                    else:
                        st.markdown("### 👤")
                else:
                    st.markdown("### 👤")

            with col2:
                st.markdown(f"**{eco_escape(name)}**")
                st.caption(f"@{eco_escape(username)}")

                if bio:
                    st.write(bio)

                if location:
                    st.caption(f"📍 {eco_escape(location)}")

                if st.button(
                    "View Profile",
                    key=f"eco_view_profile_{member.get('user_id')}",
                    use_container_width=True
                ):
                    st.session_state["eco_view_profile_id"] = (
                        str(member.get("user_id"))
                    )
                    st.rerun()
        
        

# ==========================================================
# PART 3 — PRIVATE DIRECT CHATS
# ==========================================================

def get_or_create_direct_conversation(supabase, user_id, other_user_id):
    try:
        user_a = str(user_id)
        user_b = str(other_user_id)

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

        result = (
            supabase.table("direct_conversations")
            .insert({
                "user_one_id": user_a,
                "user_two_id": user_b,
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


def send_direct_message(supabase, conversation_id, user_id, message):
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
    other_user_id = get_other_conversation_user(
        conversation,
        user_id
    )

    other_profile = eco_profile(supabase, other_user_id)

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

    for message in messages:
        sender_id = str(message.get("sender_id"))
        mine = sender_id == str(user_id)

        sender_name = (
            "You" if mine
            else eco_member_name(supabase, sender_id)
        )

        with st.chat_message("user" if mine else "assistant"):
            st.caption(sender_name)
            st.write(message.get("message_text") or "")

            created = message.get("created_at")
            if created:
                st.caption(str(created)[:16].replace("T", " "))

    st.divider()

    with st.form(
        f"eco_direct_message_form_{conversation_id}",
        clear_on_submit=True
    ):
        message_text = st.text_input(
            "Write a message",
            placeholder="Type your message..."
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
# PART 4 — CHATS PAGE
# ==========================================================

def render_chats_page(supabase, user_id):
    st.title("Chats")
    st.caption("Your conversations on EcoLoop Node.")

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

    search = st.text_input(
        "🔍 Search conversations",
        key="eco_chat_inbox_search",
        placeholder="Search names or usernames..."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.caption("PRIVATE MESSAGES")

    with col2:
        if st.button(
            "＋ New Chat",
            use_container_width=True
        ):
            st.session_state["eco_community_section"] = "Discover People"
            st.rerun()

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

        profile = eco_profile(
            supabase,
            other_user_id
        )

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

        created_at = last_message.get("created_at") or ""

        inbox_items.append({
            "conversation": conversation,
            "user_id": other_user_id,
            "profile": profile,
            "name": name,
            "username": username,
            "message": message_text,
            "time": created_at,
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
        avatar = profile.get("avatar_url") or ""

        with st.container(border=True):
            col1, col2, col3 = st.columns([1, 4, 1])

            with col1:
                if avatar:
                    avatar_url = get_story_media_url(
                        supabase,
                        avatar
                    )

                    if avatar_url:
                        st.image(avatar_url, width=58)
                    else:
                        st.markdown("### 👤")
                else:
                    st.markdown("### 👤")

            with col2:
                st.markdown(
                    f"**{eco_escape(item['name'])}**"
                )
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
                    key=f"eco_open_chat_{conversation.get('id')}"
                ):
                    st.session_state[
                        "eco_active_conversation"
                    ] = conversation.get("id")
                    st.rerun()
                    

# ==========================================================
# PART 5 — CHATROOMS
# ==========================================================

def get_chatrooms(supabase, search=""):
    try:
        query = (
            supabase.table("community_groups")
            .select("*")
            .order("created_at", desc=True)
        )

        if search:
            query = query.or_(
                f"name.ilike.%{search}%,"
                f"description.ilike.%{search}%"
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

        group_ids = [
            item["group_id"]
            for item in (memberships.data or [])
        ]

        result = (
            supabase.table("community_groups")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )

        return [
            group for group in (result.data or [])
            if str(group.get("id")) in
            [str(group_id) for group_id in group_ids]
            or str(group.get("created_by")) == str(user_id)
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
            "image_url": image_url.strip(),
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
                        key=f"eco_approve_{request.get('id')}"
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
                        key=f"eco_reject_{request.get('id')}"
                    ):
                        supabase.table("group_memberships").delete().eq(
                            "id", str(request.get("id"))
                        ).execute()

                        st.rerun()

    except Exception as e:
        st.error(f"Could not manage join requests: {e}")


def render_chatrooms_page(supabase, user_id):
    st.title("👥 Chatrooms")
    st.caption("Find people, join conversations and build communities.")

    tab_discover, tab_mine, tab_create = st.tabs([
        "Discover",
        "My Chatrooms",
        "Create"
    ])

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
                image_url = group.get("image_url") or ""

                if image_url:
                    st.image(image_url, use_container_width=True)

                st.markdown(f"### {eco_escape(group.get('name'))}")

                if group.get("description"):
                    st.write(group.get("description"))

                if group.get("location"):
                    st.caption(f"📍 {eco_escape(group.get('location'))}")

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
                st.markdown(f"### {eco_escape(group.get('name'))}")

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
                        if leave_chatroom(supabase, group_id, user_id):
                            st.rerun()

    with tab_create:
        with st.form("eco_create_chatroom_form"):
            name = st.text_input("Chatroom name")
            description = st.text_area("Description")
            image_url = st.text_input("Chatroom image URL")
            location = st.text_input("Location")

            submitted = st.form_submit_button(
                "Create Chatroom",
                use_container_width=True
            )

            if submitted:
                if create_chatroom(
                    supabase,
                    user_id,
                    name,
                    description,
                    image_url,
                    location
                ):
                    st.rerun()

# ==========================================================
# PART 6 — CHATROOM MESSAGES
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


def send_chatroom_message(supabase, group_id, user_id, message):
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
        st.warning("You must be an approved member to enter this chatroom.")
        return

    st.markdown(f"## {eco_escape(group.get('name'))}")

    if group.get("description"):
        st.caption(group.get("description"))

    if st.button("← Back to Chatrooms", key="eco_back_to_rooms"):
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

        sender_username = (
            ""
            if mine
            else eco_member_username(supabase, sender_id)
        )

        with st.chat_message("user" if mine else "assistant"):
            st.caption(
                f"{sender_name} {sender_username}"
            )

            st.write(message.get("message_text") or "")

            created = message.get("created_at")
            if created:
                st.caption(str(created)[:16].replace("T", " "))

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
# PART 7 — STORIES
# ==========================================================

def upload_story_media(supabase, user_id, uploaded_file):
    if uploaded_file is None:
        return None

    try:
        file_bytes = uploaded_file.getvalue()
        extension = uploaded_file.name.rsplit(".", 1)[-1].lower()
        file_path = f"{user_id}/{uuid.uuid4()}.{extension}"

        content_type = (
            uploaded_file.type
            or mimetypes.guess_type(uploaded_file.name)[0]
            or "application/octet-stream"
        )

        supabase.storage.from_(MEDIA_BUCKET).upload(
            file_path,
            file_bytes,
            {
                "content-type": content_type,
                "upsert": "false",
            }
        )

        return file_path

    except Exception as e:
        st.error(f"Could not upload story media: {e}")
        return None


def get_story_media_url(supabase, file_path):
    if not file_path:
        return None

    try:
        result = supabase.storage.from_(MEDIA_BUCKET).create_signed_url(
            file_path,
            3600
        )

        if isinstance(result, dict):
            return (
                result.get("signedURL")
                or result.get("signedUrl")
            )

        return None

    except Exception as e:
        st.error(f"Could not load story media: {e}")
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
            "media_type": media_type,
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
            if avatar:
                st.image(avatar, width=50)
            else:
                st.markdown("### 👤")

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
                st.image(media_url, use_container_width=True)

            elif media_type.startswith("video"):
                st.video(media_url)

        if story.get("caption"):
            st.write(story.get("caption"))

        created = story.get("created_at")
        if created:
            st.caption(
                f"Posted: {str(created)[:16].replace('T', ' ')}"
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
    st.caption("Share photos and videos with the EcoLoop community. Stories expire after 24 hours.")

    tab_feed, tab_create = st.tabs([
        "Recent Stories",
        "Create Story"
    ])

    with tab_feed:
        stories = get_active_stories(supabase)

        if not stories:
            st.info("No active stories yet. Be the first to share one!")

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
            if uploaded_file.type.startswith("image"):
                st.image(
                    uploaded_file,
                    use_container_width=True
                )
            elif uploaded_file.type.startswith("video"):
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
# PART 8 — COMMUNITY HUB NAVIGATION
# ==========================================================

def render_community_groups_page(supabase, user_id):
    eco_init_state()

    st.title("🌍 Community Hub")
    st.caption("Connect, communicate and make an impact together.")

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
