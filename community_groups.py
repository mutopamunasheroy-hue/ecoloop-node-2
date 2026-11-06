import streamlit as st
import uuid
import html
import mimetypes

from datetime import datetime, timezone, timedelta


# ==========================================================
# ECOLOOP NODE — COMMUNITY HUB
# POWERED BY NEXT GEN IMPACT HUB (NGIH)
# ==========================================================

MEDIA_BUCKET = "community-media"

REACTIONS = ["👍", "❤️", "😂", "😮", "👏", "🌱"]


# ==========================================================
# GENERAL HELPERS
# ==========================================================

def eco_now():
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def eco_id():
    """Generate a UUID string."""
    return str(uuid.uuid4())


def eco_escape(value):
    """Safely escape text before displaying it in HTML."""
    if value is None:
        return ""
    return html.escape(str(value))


def eco_profile(supabase, user_id):
    """Retrieve a member profile."""
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
        st.error(f"Could not load member profile: {e}")

    return {}


def eco_member_name(supabase, user_id):
    """Get a member's display name."""
    profile = eco_profile(supabase, user_id)

    return (
        profile.get("display_name")
        or profile.get("username")
        or "EcoLoop Member"
    )


def eco_member_username(supabase, user_id):
    """Get a member's username."""
    profile = eco_profile(supabase, user_id)

    username = profile.get("username")

    if username:
        return f"@{username.lstrip('@')}"

    return "@member"


def eco_avatar(supabase, user_id):
    """Get a member's profile picture URL."""
    profile = eco_profile(supabase, user_id)
    return profile.get("avatar_url")


def eco_is_valid_user_id(user_id):
    """Check that a user ID is available."""
    return bool(user_id and str(user_id).strip())


def eco_set_section(section):
    """Change the Community Hub section and clear open detail views."""
    st.session_state["eco_community_section"] = section
    st.session_state["eco_community_navigation"] = section

    for key in (
        "eco_active_chat",
        "eco_active_group",
        "eco_active_community",
        "eco_active_channel",
    ):
        st.session_state.pop(key, None)


def eco_show_error(action, error):
    """Show a readable database error."""
    st.error(f"{action}: {error}")

# ==========================================================
# PART 2 — MEMBER PROFILES AND PRIVATE CONVERSATIONS
# ==========================================================


def get_member_directory(supabase, search_text=""):
    """Return searchable member profiles."""
    try:
        query = (
            supabase.table("member_profiles")
            .select("*")
            .order("username")
        )

        result = query.execute()
        profiles = result.data or []

        if search_text:
            term = search_text.strip().lower()

            profiles = [
                profile for profile in profiles
                if term in str(profile.get("username") or "").lower()
                or term in str(profile.get("display_name") or "").lower()
                or term in str(profile.get("bio") or "").lower()
            ]

        return profiles

    except Exception as e:
        eco_show_error("Could not load member directory", e)
        return []


def save_member_profile(
    supabase,
    user_id,
    display_name,
    username,
    bio="",
    location="",
    interests="",
    avatar_url=None
):
    """Create or update the current user's profile."""

    username = username.strip().lower().replace(" ", "")

    if not username:
        st.warning("Please enter a username.")
        return False

    if not username.replace("_", "").isalnum():
        st.warning("Use only letters, numbers and underscores in your username.")
        return False

    try:
        existing = (
            supabase.table("member_profiles")
            .select("user_id")
            .eq("username", username)
            .limit(1)
            .execute()
        )

        if existing.data:
            owner_id = str(existing.data[0].get("user_id"))

            if owner_id != str(user_id):
                st.error("That username is already taken.")
                return False

        profile_data = {
            "user_id": str(user_id),
            "display_name": display_name.strip(),
            "username": username,
            "bio": bio.strip(),
            "location": location.strip(),
            "interests": interests.strip(),
            "updated_at": eco_now(),
        }

        if avatar_url:
            profile_data["avatar_url"] = avatar_url

        supabase.table("member_profiles").upsert(
            profile_data,
            on_conflict="user_id"
        ).execute()

        return True

    except Exception as e:
        eco_show_error("Could not save profile", e)
        return False


def get_or_create_direct_conversation(
    supabase,
    user_id,
    other_user_id
):
    """Find an existing private conversation or create one."""

    user_id = str(user_id)
    other_user_id = str(other_user_id)

    if user_id == other_user_id:
        return None

    first_id, second_id = sorted([user_id, other_user_id])

    try:
        existing = (
            supabase.table("direct_conversations")
            .select("*")
            .eq("user_one_id", first_id)
            .eq("user_two_id", second_id)
            .limit(1)
            .execute()
        )

        if existing.data:
            return existing.data[0]

        try:
            created = (
                supabase.table("direct_conversations")
                .insert({
                    "user_one_id": first_id,
                    "user_two_id": second_id,
                    "created_at": eco_now(),
                })
                .execute()
            )

            if created.data:
                return created.data[0]

        except Exception:
            # Another request may have created the conversation
            # at almost the same time. Fetch it again.
            existing = (
                supabase.table("direct_conversations")
                .select("*")
                .eq("user_one_id", first_id)
                .eq("user_two_id", second_id)
                .limit(1)
                .execute()
            )

            if existing.data:
                return existing.data[0]

            raise

    except Exception as e:
        eco_show_error("Could not open private conversation", e)

    return None


def get_direct_conversations(supabase, user_id):
    """List all private conversations belonging to a user."""

    user_id = str(user_id)

    try:
        first = (
            supabase.table("direct_conversations")
            .select("*")
            .eq("user_one_id", user_id)
            .execute()
        )

        second = (
            supabase.table("direct_conversations")
            .select("*")
            .eq("user_two_id", user_id)
            .execute()
        )

        conversations = (first.data or []) + (second.data or [])

        unique = {}

        for conversation in conversations:
            unique[str(conversation["id"])] = conversation

        return sorted(
            unique.values(),
            key=lambda item: item.get("created_at") or "",
            reverse=True
        )

    except Exception as e:
        eco_show_error("Could not load private conversations", e)
        return []


def get_direct_messages(supabase, conversation_id):
    """Retrieve messages in a private conversation."""

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
        eco_show_error("Could not load private messages", e)
        return []


def send_direct_message(
    supabase,
    conversation_id,
    sender_id,
    message_text
):
    """Send a text message in a private conversation."""

    message_text = (message_text or "").strip()

    if not message_text:
        return False

    try:
        supabase.table("direct_messages").insert({
            "conversation_id": str(conversation_id),
            "sender_id": str(sender_id),
            "message_text": message_text,
            "created_at": eco_now(),
        }).execute()

        return True

    except Exception as e:
        eco_show_error("Message could not be sent", e)
        return False


def get_other_conversation_user(conversation, current_user_id):
    """Find the other participant in a private conversation."""

    current_user_id = str(current_user_id)

    first = str(conversation.get("user_one_id"))
    second = str(conversation.get("user_two_id"))

    return second if first == current_user_id else first


def render_people_directory(supabase, user_id):
    """Search for members and start private conversations."""

    st.subheader("Discover People")
    st.caption("Find EcoLoop members by username or display name.")

    search_text = st.text_input(
        "Search members",
        placeholder="Search by username or name...",
        key="eco_people_search"
    )

    profiles = get_member_directory(supabase, search_text)

    profiles = [
        profile for profile in profiles
        if str(profile.get("user_id")) != str(user_id)
    ]

    if not profiles:
        st.info("No members found.")
        return

    for profile in profiles:
        member_id = str(profile.get("user_id"))
        name = profile.get("display_name") or "EcoLoop Member"
        username = profile.get("username") or "member"
        avatar = profile.get("avatar_url")
        bio = profile.get("bio") or "No bio added yet."

        with st.container(border=True):
            left, right = st.columns([1, 4])

            with left:
                if avatar:
                    st.image(avatar, width=65)
                else:
                    st.markdown("### 👤")

            with right:
                st.markdown(f"**{eco_escape(name)}**")
                st.caption(f"@{eco_escape(username)}")
                st.write(bio)

                if st.button(
                    "Message",
                    key=f"eco_message_member_{member_id}",
                    use_container_width=True
                ):
                    conversation = get_or_create_direct_conversation(
                        supabase,
                        user_id,
                        member_id
                    )

                    if conversation:
                        st.session_state["eco_active_chat"] = (
                            conversation["id"]
                        )
                        st.session_state["eco_active_chat_type"] = "direct"
                        st.session_state["eco_community_section"] = "Chats"
                        st.rerun()


def render_direct_chat(supabase, user_id, conversation_id):
    """Display a private WhatsApp-style conversation."""

    conversation_result = (
        supabase.table("direct_conversations")
        .select("*")
        .eq("id", str(conversation_id))
        .limit(1)
        .execute()
    )

    if not conversation_result.data:
        st.error("This conversation could not be found.")
        return

    conversation = conversation_result.data[0]

    first = str(conversation.get("user_one_id"))
    second = str(conversation.get("user_two_id"))

    if str(user_id) not in (first, second):
        st.error("You are not a participant in this conversation.")
        return

    other_user_id = get_other_conversation_user(
        conversation,
        user_id
    )

    other_profile = eco_profile(supabase, other_user_id)

    name = (
        other_profile.get("display_name")
        or other_profile.get("username")
        or "EcoLoop Member"
    )

    username = other_profile.get("username") or "member"

    top_left, top_right = st.columns([1, 5])

    with top_left:
        if st.button("← Back", key="eco_direct_chat_back"):
            st.session_state.pop("eco_active_chat", None)
            st.session_state.pop("eco_active_chat_type", None)
            st.session_state["eco_community_section"] = "Chats"
            st.rerun()

    with top_right:
        st.markdown(f"### {eco_escape(name)}")
        st.caption(f"@{eco_escape(username)}")

    st.divider()

    messages = get_direct_messages(supabase, conversation_id)

    if not messages:
        st.info("This is the beginning of your conversation.")

    for message in messages:
        sender_id = str(message.get("sender_id"))
        message_text = message.get("message_text") or ""

        is_mine = sender_id == str(user_id)

        with st.chat_message("user" if is_mine else "assistant"):
            st.write(message_text)

            created_at = message.get("created_at")

            if created_at:
                st.caption(str(created_at)[:16].replace("T", " "))

    st.divider()

    with st.form(
        key=f"eco_direct_message_form_{conversation_id}",
        clear_on_submit=True
    ):
        message_text = st.text_input(
            "Message",
            placeholder="Type a message..."
        )

        submitted = st.form_submit_button(
            "Send",
            use_container_width=True
        )

        if submitted:
            if send_direct_message(
                supabase,
                conversation_id,
                user_id,
                message_text
            ):
                st.rerun()

# ==========================================================
# PART 3 — UNIFIED CHATS AND GROUP MANAGEMENT
# ==========================================================


def get_my_approved_groups(supabase, user_id):
    """Get approved groups plus groups created by the current user."""

    user_id = str(user_id)
    groups = {}

    try:
        memberships = (
            supabase.table("group_memberships")
            .select("group_id")
            .eq("user_id", user_id)
            .eq("status", "approved")
            .execute()
        )

        group_ids = list({
            str(item["group_id"])
            for item in (memberships.data or [])
            if item.get("group_id")
        })

        if group_ids:
            result = (
                supabase.table("community_groups")
                .select("*")
                .in_("id", group_ids)
                .execute()
            )

            for group in result.data or []:
                groups[str(group["id"])] = group

        # Always include groups created by the current user.
        created = (
            supabase.table("community_groups")
            .select("*")
            .eq("created_by", user_id)
            .execute()
        )

        for group in created.data or []:
            groups[str(group["id"])] = group

        return list(groups.values())

    except Exception as e:
        eco_show_error("Could not load your groups", e)
        return list(groups.values())


def get_groups(supabase):
    """Get all discoverable groups."""

    try:
        result = (
            supabase.table("community_groups")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    except Exception as e:
        eco_show_error("Could not load groups", e)
        return []


def get_group_memberships(supabase, group_id):
    """Get memberships belonging to a group."""

    try:
        result = (
            supabase.table("group_memberships")
            .select("*")
            .eq("group_id", str(group_id))
            .execute()
        )
        return result.data or []

    except Exception as e:
        eco_show_error("Could not load group members", e)
        return []


def is_group_admin(supabase, group_id, user_id):
    """Check whether a user is the group creator or an approved admin."""

    user_id = str(user_id)

    try:
        group = (
            supabase.table("community_groups")
            .select("created_by")
            .eq("id", str(group_id))
            .limit(1)
            .execute()
        )

        if group.data:
            if str(group.data[0].get("created_by")) == user_id:
                return True

        membership = (
            supabase.table("group_memberships")
            .select("membership_role,status")
            .eq("group_id", str(group_id))
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        if membership.data:
            item = membership.data[0]

            return (
                item.get("status") == "approved"
                and item.get("membership_role") == "admin"
            )

    except Exception:
        return False

    return False


def get_my_group_membership(supabase, group_id, user_id):
    """Get the current user's membership in a group."""

    try:
        result = (
            supabase.table("group_memberships")
            .select("*")
            .eq("group_id", str(group_id))
            .eq("user_id", str(user_id))
            .limit(1)
            .execute()
        )

        if result.data:
            return result.data[0]

    except Exception:
        pass

    return None


def create_community_group(
    supabase,
    user_id,
    name,
    description="",
    location="",
    community_id=None
):
    """Create a group. Creator ownership is stored on the group itself."""

    name = (name or "").strip()

    if not name:
        st.warning("Enter a group name.")
        return None

    group_data = {
        "name": name,
        "description": (description or "").strip(),
        "created_by": str(user_id),
        "created_at": eco_now(),
        "location": (location or "").strip() or None,
    }

    if community_id:
        group_data["community_id"] = str(community_id)

    try:
        result = (
            supabase.table("community_groups")
            .insert(group_data)
            .execute()
        )

        if not result.data:
            st.error("The group was not created.")
            return None

        group = result.data[0]

        # Try to create the creator's admin membership.
        # Ownership remains available through created_by if RLS
        # prevents this additional membership record.
        try:
            supabase.table("group_memberships").insert({
                "group_id": str(group["id"]),
                "user_id": str(user_id),
                "membership_role": "admin",
                "status": "approved",
                "joined_at": eco_now(),
            }).execute()

        except Exception:
            pass

        return group

    except Exception as e:
        eco_show_error("Could not create group", e)
        return None


def request_group_membership(supabase, group_id, user_id):
    """Request membership in a group."""

    existing = get_my_group_membership(
        supabase,
        group_id,
        user_id
    )

    if existing:
        status = existing.get("status")

        if status == "approved":
            return True

        if status == "pending":
            st.info("Your membership request is already pending.")
            return False

    try:
        supabase.table("group_memberships").insert({
            "group_id": str(group_id),
            "user_id": str(user_id),
            "membership_role": "member",
            "status": "pending",
            "joined_at": eco_now(),
        }).execute()

        return True

    except Exception as e:
        eco_show_error("Could not request group membership", e)
        return False


def update_group_membership(
    supabase,
    membership_id,
    new_status
):
    """Approve or reject a pending membership."""

    if new_status not in ("approved", "rejected"):
        return False

    try:
        supabase.table("group_memberships").update({
            "status": new_status
        }).eq("id", str(membership_id)).execute()

        return True

    except Exception as e:
        eco_show_error("Could not update membership", e)
        return False


def add_group_member(supabase, group_id, user_id):
    """Add a member through a pending membership request."""

    existing = get_my_group_membership(
        supabase,
        group_id,
        user_id
    )

    if existing:
        if existing.get("status") == "approved":
            return True

        st.info("This person already has a membership request.")
        return False

    try:
        supabase.table("group_memberships").insert({
            "group_id": str(group_id),
            "user_id": str(user_id),
            "membership_role": "member",
            "status": "pending",
            "joined_at": eco_now(),
        }).execute()

        return True

    except Exception as e:
        eco_show_error("Could not add group member", e)
        return False


def get_group_messages(supabase, group_id):
    """Retrieve group messages."""

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
        eco_show_error("Could not load group messages", e)
        return []


def send_group_message(
    supabase,
    group_id,
    sender_id,
    message_text
):
    """Send a message to a group."""

    message_text = (message_text or "").strip()

    if not message_text:
        return False

    try:
        supabase.table("group_messages").insert({
            "group_id": str(group_id),
            "sender_id": str(sender_id),
            "message_text": message_text,
            "created_at": eco_now(),
        }).execute()

        return True

    except Exception as e:
        eco_show_error("Message could not be sent", e)
        return False


def render_group_chat(supabase, user_id, group_id):
    """Display a group conversation."""

    groups = get_groups(supabase)

    group = next(
        (
            item for item in groups
            if str(item.get("id")) == str(group_id)
        ),
        None
    )

    if not group:
        st.error("Group not found.")
        return

    is_admin = is_group_admin(supabase, group_id, user_id)

    membership = get_my_group_membership(
        supabase,
        group_id,
        user_id
    )

    is_approved = (
        membership
        and membership.get("status") == "approved"
    )

    if not is_admin and not is_approved:
        st.error("You must be an approved member to access this group chat.")
        return

    if st.button("← Back to Chats", key=f"eco_group_back_{group_id}"):
        st.session_state.pop("eco_active_group", None)
        st.session_state.pop("eco_active_chat", None)
        st.session_state.pop("eco_active_chat_type", None)
        st.session_state["eco_community_section"] = "Chats"
        st.rerun()

    st.subheader(group.get("name") or "Group")
    st.caption(group.get("description") or "EcoLoop group conversation")

    st.divider()

    messages = get_group_messages(supabase, group_id)

    if not messages:
        st.info("No messages yet. Start the conversation.")

    for message in messages:
        sender_id = str(message.get("sender_id"))
        text = message.get("message_text") or ""
        is_mine = sender_id == str(user_id)

        with st.chat_message("user" if is_mine else "assistant"):
            if not is_mine:
                st.caption(eco_member_name(supabase, sender_id))

            st.write(text)

            if message.get("created_at"):
                st.caption(
                    str(message["created_at"])[:16].replace("T", " ")
                )

    with st.form(
        key=f"eco_group_message_form_{group_id}",
        clear_on_submit=True
    ):
        message_text = st.text_input(
            "Message",
            placeholder="Write to the group..."
        )

        submitted = st.form_submit_button(
            "Send",
            use_container_width=True
        )

        if submitted:
            if send_group_message(
                supabase,
                group_id,
                user_id,
                message_text
            ):
                st.rerun()


def render_chats_page(supabase, user_id):
    """Unified list of private and group conversations."""

    st.subheader("Chats")
    st.caption("Your private and group conversations.")

    tab_chats, tab_people, tab_groups = st.tabs([
        "Messages",
        "Discover People",
        "My Groups"
    ])

    with tab_chats:
        direct_conversations = get_direct_conversations(
            supabase,
            user_id
        )

        groups = get_my_approved_groups(
            supabase,
            user_id
        )

        if not direct_conversations and not groups:
            st.info("Your chats will appear here when you connect with people or join groups.")

        st.markdown("#### Private conversations")

        for conversation in direct_conversations:
            other_id = get_other_conversation_user(
                conversation,
                user_id
            )

            profile = eco_profile(supabase, other_id)

            name = (
                profile.get("display_name")
                or profile.get("username")
                or "EcoLoop Member"
            )

            username = profile.get("username") or "member"

            with st.container(border=True):
                left, right = st.columns([4, 1])

                with left:
                    st.markdown(f"**{eco_escape(name)}**")
                    st.caption(f"@{eco_escape(username)}")

                with right:
                    if st.button(
                        "Open",
                        key=f"eco_open_direct_{conversation['id']}"
                    ):
                        st.session_state["eco_active_chat"] = conversation["id"]
                        st.session_state["eco_active_chat_type"] = "direct"
                        st.rerun()

        st.markdown("#### Group conversations")

        for group in groups:
            group_id = str(group["id"])

            with st.container(border=True):
                st.markdown(f"**👥 {eco_escape(group.get('name'))}**")
                st.caption(group.get("description") or "EcoLoop group")

                if st.button(
                    "Open group chat",
                    key=f"eco_open_group_{group_id}",
                    use_container_width=True
                ):
                    st.session_state["eco_active_group"] = group_id
                    st.rerun()

    with tab_people:
        render_people_directory(supabase, user_id)

    with tab_groups:
        render_groups_page(supabase, user_id)

# ==========================================================
# PART 4 — GROUPS DISCOVERY AND MANAGEMENT
# ==========================================================


def render_groups_page(supabase, user_id):
    """Groups page with discovery, membership and creation."""

    st.subheader("Groups")
    st.caption("Find people, build communities and work together.")

    tab_my, tab_discover, tab_create = st.tabs([
        "My Groups",
        "Discover",
        "Create Group"
    ])

    with tab_my:
        groups = get_my_approved_groups(supabase, user_id)

        if not groups:
            st.info("You haven't joined any groups yet.")

        for group in groups:
            group_id = str(group["id"])

            with st.container(border=True):
                st.markdown(f"### 👥 {eco_escape(group.get('name'))}")

                if group.get("description"):
                    st.write(group["description"])

                if group.get("location"):
                    st.caption(f"📍 {eco_escape(group['location'])}")

                members = get_group_memberships(supabase, group_id)
                approved_count = sum(
                    1 for member in members
                    if member.get("status") == "approved"
                )

                st.caption(f"Members: {approved_count}")

                if st.button(
                    "Open Group Chat",
                    key=f"eco_my_group_chat_{group_id}",
                    use_container_width=True
                ):
                    st.session_state["eco_active_group"] = group_id
                    st.rerun()

                if is_group_admin(supabase, group_id, user_id):
                    with st.expander("Manage group"):
                        render_group_admin_members(
                            supabase,
                            group_id,
                            user_id
                        )

    with tab_discover:
        search = st.text_input(
            "Find a group",
            placeholder="Search groups...",
            key="eco_group_search"
        )

        all_groups = get_groups(supabase)

        if search.strip():
            term = search.strip().lower()

            all_groups = [
                group for group in all_groups
                if term in str(group.get("name") or "").lower()
                or term in str(group.get("description") or "").lower()
                or term in str(group.get("location") or "").lower()
            ]

        for group in all_groups:
            group_id = str(group["id"])

            membership = get_my_group_membership(
                supabase,
                group_id,
                user_id
            )

            is_admin = is_group_admin(
                supabase,
                group_id,
                user_id
            )

            with st.container(border=True):
                st.markdown(f"### 👥 {eco_escape(group.get('name'))}")

                st.write(
                    group.get("description")
                    or "No group description available."
                )

                if group.get("location"):
                    st.caption(f"📍 {eco_escape(group['location'])}")

                if is_admin or (
                    membership
                    and membership.get("status") == "approved"
                ):
                    st.success("You're a member.")

                    if st.button(
                        "Open Group",
                        key=f"eco_discover_open_{group_id}",
                        use_container_width=True
                    ):
                        st.session_state["eco_active_group"] = group_id
                        st.rerun()

                elif membership and membership.get("status") == "pending":
                    st.info("Membership request pending.")

                elif membership and membership.get("status") == "rejected":
                    st.warning("Your previous request was rejected.")

                else:
                    if st.button(
                        "Request to Join",
                        key=f"eco_join_group_{group_id}",
                        use_container_width=True
                    ):
                        if request_group_membership(
                            supabase,
                            group_id,
                            user_id
                        ):
                            st.success("Your request has been submitted.")
                            st.rerun()

    with tab_create:
        render_create_group_tab(supabase, user_id)


def render_create_group_tab(supabase, user_id):
    """Group creation form."""

    st.markdown("### Create a new group")

    with st.form("eco_create_group_form"):
        name = st.text_input(
            "Group name",
            placeholder="e.g. Bulawayo Climate Action"
        )

        description = st.text_area(
            "Description",
            placeholder="What is this group about?"
        )

        location = st.text_input(
            "Location (optional)",
            placeholder="e.g. Bulawayo"
        )

        submitted = st.form_submit_button(
            "Create Group",
            use_container_width=True
        )

        if submitted:
            if not name.strip():
                st.warning("Please enter a group name.")

            else:
                group = create_community_group(
                    supabase,
                    user_id,
                    name,
                    description,
                    location
                )

                if group:
                    st.success("Your group has been created!")

                    st.session_state["eco_active_group"] = group["id"]
                    st.rerun()


def render_group_admin_members(supabase, group_id, user_id):
    """Show membership requests and current group members."""

    if not is_group_admin(supabase, group_id, user_id):
        st.error("Only group administrators can manage members.")
        return

    members = get_group_memberships(supabase, group_id)

    st.markdown("**Membership requests**")

    pending = [
        member for member in members
        if member.get("status") == "pending"
    ]

    if not pending:
        st.caption("There are no pending requests.")

    for member in pending:
        member_id = str(member.get("id"))
        requested_user = str(member.get("user_id"))

        profile = eco_profile(supabase, requested_user)

        name = (
            profile.get("display_name")
            or profile.get("username")
            or "EcoLoop Member"
        )

        with st.container(border=True):
            st.write(f"**{eco_escape(name)}**")

            approve_col, reject_col = st.columns(2)

            with approve_col:
                if st.button(
                    "Approve",
                    key=f"eco_approve_{member_id}",
                    use_container_width=True
                ):
                    if update_group_membership(
                        supabase,
                        member_id,
                        "approved"
                    ):
                        st.success("Membership approved.")
                        st.rerun()

            with reject_col:
                if st.button(
                    "Reject",
                    key=f"eco_reject_{member_id}",
                    use_container_width=True
                ):
                    if update_group_membership(
                        supabase,
                        member_id,
                        "rejected"
                    ):
                        st.success("Request rejected.")
                        st.rerun()

    st.divider()
    st.markdown("**Current members**")

    approved = [
        member for member in members
        if member.get("status") == "approved"
    ]

    for member in approved:
        member_user_id = str(member.get("user_id"))

        profile = eco_profile(supabase, member_user_id)

        name = (
            profile.get("display_name")
            or profile.get("username")
            or "EcoLoop Member"
        )

        role = member.get("membership_role") or "member"

        st.write(f"👤 **{eco_escape(name)}** — {eco_escape(role)}")

# ==========================================================
# PART 5 — COMMUNITIES
# ==========================================================


def get_communities(supabase):
    """Retrieve all communities."""

    try:
        result = (
            supabase.table("communities")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    except Exception as e:
        eco_show_error("Could not load communities", e)
        return []


def get_my_communities(supabase, user_id):
    """Retrieve communities the user created or has joined."""

    user_id = str(user_id)
    communities = {}

    try:
        memberships = (
            supabase.table("community_memberships")
            .select("community_id,status")
            .eq("user_id", user_id)
            .eq("status", "approved")
            .execute()
        )

        community_ids = list({
            str(item["community_id"])
            for item in (memberships.data or [])
            if item.get("community_id")
        })

        if community_ids:
            result = (
                supabase.table("communities")
                .select("*")
                .in_("id", community_ids)
                .execute()
            )

            for community in result.data or []:
                communities[str(community["id"])] = community

        created = (
            supabase.table("communities")
            .select("*")
            .eq("created_by", user_id)
            .execute()
        )

        for community in created.data or []:
            communities[str(community["id"])] = community

        return list(communities.values())

    except Exception as e:
        eco_show_error("Could not load your communities", e)
        return list(communities.values())


def get_my_community_membership(supabase, community_id, user_id):
    """Get the current user's community membership."""

    try:
        result = (
            supabase.table("community_memberships")
            .select("*")
            .eq("community_id", str(community_id))
            .eq("user_id", str(user_id))
            .limit(1)
            .execute()
        )

        if result.data:
            return result.data[0]

    except Exception:
        pass

    return None


def is_community_admin(supabase, community_id, user_id):
    """Check community creator or approved admin membership."""

    user_id = str(user_id)

    try:
        community = (
            supabase.table("communities")
            .select("created_by")
            .eq("id", str(community_id))
            .limit(1)
            .execute()
        )

        if community.data:
            if str(community.data[0].get("created_by")) == user_id:
                return True

        membership = get_my_community_membership(
            supabase,
            community_id,
            user_id
        )

        if membership:
            return (
                membership.get("status") == "approved"
                and membership.get("membership_role") == "admin"
            )

    except Exception:
        return False

    return False


def create_community(
    supabase,
    user_id,
    name,
    description="",
    location=""
):
    """Create a community."""

    name = (name or "").strip()

    if not name:
        st.warning("Enter a community name.")
        return None

    try:
        result = (
            supabase.table("communities")
            .insert({
                "name": name,
                "description": (description or "").strip(),
                "location": (location or "").strip() or None,
                "created_by": str(user_id),
                "created_at": eco_now(),
            })
            .execute()
        )

        if not result.data:
            st.error("The community was not created.")
            return None

        community = result.data[0]

        # The creator is treated as admin through created_by,
        # even if RLS prevents inserting an extra membership.
        try:
            supabase.table("community_memberships").insert({
                "community_id": str(community["id"]),
                "user_id": str(user_id),
                "membership_role": "admin",
                "status": "approved",
                "joined_at": eco_now(),
            }).execute()
        except Exception:
            pass

        return community

    except Exception as e:
        eco_show_error("Could not create community", e)
        return None


def join_community(supabase, community_id, user_id):
    """Request membership in a community."""

    existing = get_my_community_membership(
        supabase,
        community_id,
        user_id
    )

    if existing:
        if existing.get("status") == "approved":
            return True

        if existing.get("status") == "pending":
            st.info("Your request is already pending.")
            return False

    try:
        supabase.table("community_memberships").insert({
            "community_id": str(community_id),
            "user_id": str(user_id),
            "membership_role": "member",
            "status": "pending",
            "joined_at": eco_now(),
        }).execute()

        return True

    except Exception as e:
        eco_show_error("Could not request community membership", e)
        return False


def get_community_groups(supabase, community_id):
    """Retrieve groups linked to a community."""

    try:
        result = (
            supabase.table("community_groups")
            .select("*")
            .eq("community_id", str(community_id))
            .order("created_at", desc=True)
            .execute()
        )

        return result.data or []

    except Exception as e:
        eco_show_error("Could not load community groups", e)
        return []


def render_community_card(supabase, community, user_id):
    """Display one community card."""

    community_id = str(community["id"])
    is_admin = is_community_admin(
        supabase,
        community_id,
        user_id
    )

    membership = get_my_community_membership(
        supabase,
        community_id,
        user_id
    )

    approved = (
        membership
        and membership.get("status") == "approved"
    )

    with st.container(border=True):
        st.markdown(f"### 🌍 {eco_escape(community.get('name'))}")

        st.write(
            community.get("description")
            or "A space for EcoLoop members to connect."
        )

        if community.get("location"):
            st.caption(f"📍 {eco_escape(community['location'])}")

        if is_admin or approved:
            st.success("You are a community member.")

            if st.button(
                "Open Community",
                key=f"eco_open_community_{community_id}",
                use_container_width=True
            ):
                st.session_state["eco_active_community"] = community_id
                st.rerun()

        elif membership and membership.get("status") == "pending":
            st.info("Your membership request is pending.")

        else:
            if st.button(
                "Join Community",
                key=f"eco_join_community_{community_id}",
                use_container_width=True
            ):
                if join_community(
                    supabase,
                    community_id,
                    user_id
                ):
                    st.success("Your request has been submitted.")
                    st.rerun()


def render_community_detail(supabase, community_id, user_id):
    """Display an approved community's details and linked groups."""

    communities = get_communities(supabase)

    community = next(
        (
            item for item in communities
            if str(item.get("id")) == str(community_id)
        ),
        None
    )

    if not community:
        st.error("Community not found.")
        return

    is_admin = is_community_admin(
        supabase,
        community_id,
        user_id
    )

    membership = get_my_community_membership(
        supabase,
        community_id,
        user_id
    )

    approved = (
        membership
        and membership.get("status") == "approved"
    )

    if not is_admin and not approved:
        st.error("You must be an approved member to open this community.")
        return

    if st.button(
        "← Back to Communities",
        key=f"eco_community_back_{community_id}"
    ):
        st.session_state.pop("eco_active_community", None)
        st.session_state["eco_community_section"] = "Communities"
        st.rerun()

    st.title(f"🌍 {community.get('name')}")
    st.write(
        community.get("description")
        or "Connect with people working towards shared goals."
    )

    if community.get("location"):
        st.caption(f"📍 {community['location']}")

    st.divider()

    tab_groups, tab_channels = st.tabs([
        "Groups",
        "Channels"
    ])

    with tab_groups:
        groups = get_community_groups(supabase, community_id)

        if not groups:
            st.info("No groups are linked to this community yet.")

        for group in groups:
            group_id = str(group["id"])

            with st.container(border=True):
                st.markdown(f"**👥 {eco_escape(group.get('name'))}**")
                st.write(group.get("description") or "")

                group_membership = get_my_group_membership(
                    supabase,
                    group_id,
                    user_id
                )

                group_admin = is_group_admin(
                    supabase,
                    group_id,
                    user_id
                )

                if group_admin or (
                    group_membership
                    and group_membership.get("status") == "approved"
                ):
                    if st.button(
                        "Open Group Chat",
                        key=f"eco_community_group_{group_id}"
                    ):
                        st.session_state["eco_active_group"] = group_id
                        st.rerun()

                elif group_membership and group_membership.get("status") == "pending":
                    st.info("Your group request is pending.")

                else:
                    if st.button(
                        "Request to Join Group",
                        key=f"eco_community_join_group_{group_id}"
                    ):
                        if request_group_membership(
                            supabase,
                            group_id,
                            user_id
                        ):
                            st.success("Request submitted.")
                            st.rerun()

        if is_admin:
            st.divider()
            st.markdown("**Create a group in this community**")

            with st.form(f"eco_community_create_group_{community_id}"):
                group_name = st.text_input("Group name")
                group_description = st.text_area("Group description")

                submitted = st.form_submit_button("Create Group")

                if submitted:
                    group = create_community_group(
                        supabase,
                        user_id,
                        group_name,
                        group_description,
                        community.get("location") or "",
                        community_id
                    )

                    if group:
                        st.success("Group created.")
                        st.rerun()

    with tab_channels:
        channels = get_community_channels(
            supabase,
            community_id
        )

        if not channels:
            st.info("There are no channels in this community yet.")

        for channel in channels:
            channel_id = str(channel["id"])

            with st.container(border=True):
                st.markdown(f"**📢 {eco_escape(channel.get('name'))}**")
                st.caption(channel.get("description") or "")

                if st.button(
                    "Open Channel",
                    key=f"eco_community_channel_{channel_id}",
                    use_container_width=True
                ):
                    st.session_state["eco_active_channel"] = channel_id
                    st.rerun()

        if is_admin:
            st.divider()
            st.markdown("**Create a channel**")

            with st.form(f"eco_create_channel_{community_id}"):
                channel_name = st.text_input("Channel name")
                channel_description = st.text_area("Channel description")

                channel_type = st.selectbox(
                    "Channel type",
                    ["Announcements", "Discussion", "Updates"]
                )

                submitted = st.form_submit_button("Create Channel")

                if submitted:
                    channel = create_community_channel(
                        supabase,
                        community_id,
                        user_id,
                        channel_name,
                        channel_description,
                        channel_type
                    )

                    if channel:
                        st.success("Channel created.")
                        st.rerun()


def render_communities_page(supabase, user_id):
    """Community discovery, membership and creation."""

    st.subheader("Communities")
    st.caption("Find your people. Share ideas. Create impact.")

    active_community = st.session_state.get(
        "eco_active_community"
    )

    if active_community:
        render_community_detail(
            supabase,
            active_community,
            user_id
        )
        return

    tab_my, tab_discover, tab_create = st.tabs([
        "My Communities",
        "Discover",
        "Create"
    ])

    with tab_my:
        communities = get_my_communities(supabase, user_id)

        if not communities:
            st.info("You haven't joined any communities yet.")

        for community in communities:
            render_community_card(
                supabase,
                community,
                user_id
            )

    with tab_discover:
        search = st.text_input(
            "Search communities",
            placeholder="Find a community...",
            key="eco_community_search"
        )

        communities = get_communities(supabase)

        if search.strip():
            term = search.strip().lower()

            communities = [
                community for community in communities
                if term in str(community.get("name") or "").lower()
                or term in str(community.get("description") or "").lower()
                or term in str(community.get("location") or "").lower()
            ]

        if not communities:
            st.info("No communities found.")

        for community in communities:
            render_community_card(
                supabase,
                community,
                user_id
            )

    with tab_create:
        st.markdown("### Create a community")

        with st.form("eco_create_community_form"):
            name = st.text_input("Community name")
            description = st.text_area("Description")
            location = st.text_input("Location (optional)")

            submitted = st.form_submit_button(
                "Create Community",
                use_container_width=True
            )

            if submitted:
                community = create_community(
                    supabase,
                    user_id,
                    name,
                    description,
                    location
                )

                if community:
                    st.success("Community created!")
                    st.session_state["eco_active_community"] = community["id"]
                    st.rerun()

# ==========================================================
# PART 6 — COMMUNITY CHANNELS
# ==========================================================


def get_community_channels(supabase, community_id):
    """Retrieve active channels belonging to a community."""

    try:
        result = (
            supabase.table("community_channels")
            .select("*")
            .eq("community_id", str(community_id))
            .eq("is_active", True)
            .order("created_at", desc=True)
            .execute()
        )

        return result.data or []

    except Exception as e:
        eco_show_error("Could not load community channels", e)
        return []


def create_community_channel(
    supabase,
    community_id,
    user_id,
    name,
    description="",
    channel_type="Announcements"
):
    """Create a channel. The required created_by field is included."""

    name = (name or "").strip()

    if not name:
        st.warning("Enter a channel name.")
        return None

    if not is_community_admin(supabase, community_id, user_id):
        st.error("Only community administrators can create channels.")
        return None

    try:
        result = (
            supabase.table("community_channels")
            .insert({
                "community_id": str(community_id),
                "name": name,
                "description": (description or "").strip(),
                "channel_type": channel_type,
                "created_by": str(user_id),
                "created_at": eco_now(),
                "is_active": True,
            })
            .execute()
        )

        if result.data:
            return result.data[0]

        st.error("The channel was not created.")
        return None

    except Exception as e:
        eco_show_error("Could not create channel", e)
        return None


def get_channel_messages(supabase, channel_id):
    """Retrieve messages in a channel."""

    try:
        result = (
            supabase.table("channel_messages")
            .select("*")
            .eq("channel_id", str(channel_id))
            .order("created_at")
            .execute()
        )

        return result.data or []

    except Exception as e:
        eco_show_error("Could not load channel messages", e)
        return []


def send_channel_message(
    supabase,
    channel_id,
    sender_id,
    message_text
):
    """Publish a message in a community channel."""

    message_text = (message_text or "").strip()

    if not message_text:
        return False

    try:
        supabase.table("channel_messages").insert({
            "channel_id": str(channel_id),
            "sender_id": str(sender_id),
            "message_text": message_text,
            "created_at": eco_now(),
        }).execute()

        return True

    except Exception as e:
        eco_show_error("Could not publish channel message", e)
        return False


def get_channel_details(supabase, channel_id):
    """Retrieve a single channel."""

    try:
        result = (
            supabase.table("community_channels")
            .select("*")
            .eq("id", str(channel_id))
            .limit(1)
            .execute()
        )

        if result.data:
            return result.data[0]

    except Exception as e:
        eco_show_error("Could not load channel", e)

    return None


def can_access_channel(supabase, channel, user_id):
    """Only approved community members and admins can read a channel."""

    community_id = str(channel.get("community_id"))

    return (
        is_community_admin(supabase, community_id, user_id)
        or (
            get_my_community_membership(
                supabase,
                community_id,
                user_id
            )
            or {}
        ).get("status") == "approved"
    )


def render_channel_chat(supabase, channel_id, user_id):
    """Display a channel and its announcements."""

    channel = get_channel_details(supabase, channel_id)

    if not channel:
        st.error("Channel not found.")
        return

    if not channel.get("is_active"):
        st.warning("This channel is no longer active.")
        return

    if not can_access_channel(supabase, channel, user_id):
        st.error("You must be an approved community member to access this channel.")
        return

    community_id = str(channel.get("community_id"))

    is_admin = is_community_admin(
        supabase,
        community_id,
        user_id
    )

    if st.button(
        "← Back to Community",
        key=f"eco_channel_back_{channel_id}"
    ):
        st.session_state.pop("eco_active_channel", None)
        st.rerun()

    st.subheader(f"📢 {channel.get('name')}")
    st.caption(
        channel.get("description")
        or channel.get("channel_type")
        or "Community channel"
    )

    st.divider()

    messages = get_channel_messages(supabase, channel_id)

    if not messages:
        st.info("There are no announcements yet.")

    for message in messages:
        sender_id = str(message.get("sender_id"))
        sender_name = eco_member_name(supabase, sender_id)

        with st.container(border=True):
            st.markdown(f"**{eco_escape(sender_name)}**")

            if message.get("message_text"):
                st.write(message["message_text"])

            if message.get("created_at"):
                st.caption(
                    str(message["created_at"])[:16].replace("T", " ")
                )

            if message.get("attachment_name"):
                st.caption(
                    f"📎 {eco_escape(message['attachment_name'])}"
                )

    if is_admin:
        st.divider()
        st.markdown("**Publish an announcement**")

        with st.form(
            key=f"eco_channel_message_form_{channel_id}",
            clear_on_submit=True
        ):
            message_text = st.text_area(
                "Announcement",
                placeholder="Share an update with your community..."
            )

            submitted = st.form_submit_button(
                "Publish",
                use_container_width=True
            )

            if submitted:
                if send_channel_message(
                    supabase,
                    channel_id,
                    user_id,
                    message_text
                ):
                    st.success("Announcement published.")
                    st.rerun()

    else:
        st.info("Only community administrators can publish announcements.")


def render_channels_page(supabase, user_id):
    """Display channels from communities the user can access."""

    st.subheader("Channels")
    st.caption("Announcements and updates from your communities.")

    communities = get_my_communities(supabase, user_id)

    if not communities:
        st.info("Join a community to access its channels.")
        return

    all_channels = []

    for community in communities:
        community_id = str(community["id"])

        channels = get_community_channels(
            supabase,
            community_id
        )

        for channel in channels:
            channel["_community_name"] = community.get("name") or "Community"
            all_channels.append(channel)

    if not all_channels:
        st.info("There are no active channels in your communities yet.")
        return

    for channel in all_channels:
        channel_id = str(channel["id"])

        with st.container(border=True):
            st.markdown(f"### 📢 {eco_escape(channel.get('name'))}")
            st.caption(
                f"{eco_escape(channel['_community_name'])} "
                f"• {eco_escape(channel.get('channel_type') or 'Channel')}"
            )

            if channel.get("description"):
                st.write(channel["description"])

            if st.button(
                "Open Channel",
                key=f"eco_open_channel_{channel_id}",
                use_container_width=True
            ):
                st.session_state["eco_active_channel"] = channel_id
                st.rerun()

# ==========================================================
# PART 7 — UPDATES AND STORIES
# ==========================================================


def upload_story_media(supabase, user_id, uploaded_file):
    """Upload story media to the community-media bucket."""

    if uploaded_file is None:
        return None

    try:
        extension = mimetypes.guess_extension(
            uploaded_file.type
        ) or ""

        file_name = (
            f"stories/{user_id}/"
            f"{uuid.uuid4().hex}{extension}"
        )

        supabase.storage.from_(MEDIA_BUCKET).upload(
            file_name,
            uploaded_file.getvalue(),
            {
                "content-type": uploaded_file.type,
                "upsert": "false",
            }
        )

        return file_name

    except Exception as e:
        eco_show_error("Could not upload story media", e)
        return None


def get_story_media_url(supabase, media_path):
    """Generate a signed URL for uploaded story media."""

    if not media_path:
        return None

    try:
        result = supabase.storage.from_(MEDIA_BUCKET).create_signed_url(
            media_path,
            3600
        )

        if isinstance(result, dict):
            return (
                result.get("signedURL")
                or result.get("signedUrl")
                or result.get("signed_url")
            )

        return getattr(result, "signedURL", None)

    except Exception as e:
        eco_show_error("Could not retrieve story media", e)
        return None


def create_story(
    supabase,
    user_id,
    caption="",
    media_path=None,
    media_type=None
):
    """Create a story that expires after 24 hours."""

    try:
        now = datetime.now(timezone.utc)

        story_data = {
            "user_id": str(user_id),
            "caption": (caption or "").strip(),
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=24)).isoformat(),
        }

        if media_path:
            story_data["media_url"] = media_path
            story_data["media_type"] = media_type

        result = (
            supabase.table("stories")
            .insert(story_data)
            .execute()
        )

        return bool(result.data)

    except Exception as e:
        eco_show_error("Could not create update", e)
        return False


def get_active_stories(supabase):
    """Retrieve stories that have not expired."""

    try:
        result = (
            supabase.table("stories")
            .select("*")
            .gt("expires_at", eco_now())
            .order("created_at", desc=True)
            .execute()
        )

        return result.data or []

    except Exception as e:
        eco_show_error("Could not load updates", e)
        return []


def render_story_card(supabase, story, current_user_id):
    """Display one active story."""

    user_id = str(story.get("user_id"))

    name = eco_member_name(supabase, user_id)

    created_at = story.get("created_at") or ""
    caption = story.get("caption") or ""
    media_path = story.get("media_url")

    with st.container(border=True):
        st.markdown(f"**{eco_escape(name)}**")

        if created_at:
            st.caption(
                str(created_at)[:16].replace("T", " ")
            )

        if caption:
            st.write(caption)

        if media_path:
            media_url = get_story_media_url(
                supabase,
                media_path
            )

            if media_url:
                media_type = story.get("media_type") or ""

                if media_type.startswith("image/"):
                    st.image(media_url, use_container_width=True)

                elif media_type.startswith("video/"):
                    st.video(media_url)

                else:
                    st.caption("Story media is available but its type is unsupported.")

            else:
                st.warning("Story media could not be displayed.")


def render_updates_page(supabase, user_id):
    """Updates feed with story creation and active stories."""

    st.subheader("Updates")
    st.caption("Share what's happening in your EcoLoop community.")

    tab_create, tab_feed = st.tabs([
        "Create Update",
        "Recent Updates"
    ])

    with tab_create:
        st.markdown("### Share an update")

        with st.form(
            "eco_create_story_form",
            clear_on_submit=True
        ):
            caption = st.text_area(
                "What's happening?",
                placeholder="Share an environmental action, achievement or announcement..."
            )

            uploaded_file = st.file_uploader(
                "Add an image or video (optional)",
                type=[
                    "png",
                    "jpg",
                    "jpeg",
                    "webp",
                    "mp4",
                    "mov"
                ],
                key="eco_story_upload"
            )

            submitted = st.form_submit_button(
                "Share Update",
                use_container_width=True
            )

            if submitted:
                if not caption.strip() and uploaded_file is None:
                    st.warning("Add some text or media before sharing.")
                else:
                    media_path = None
                    media_type = None

                    if uploaded_file is not None:
                        media_path = upload_story_media(
                            supabase,
                            user_id,
                            uploaded_file
                        )

                        if not media_path:
                            st.error("Your update was not published because the media upload failed.")
                            st.stop()

                        media_type = uploaded_file.type

                    if create_story(
                        supabase,
                        user_id,
                        caption,
                        media_path,
                        media_type
                    ):
                        st.success("Your update has been shared.")
                        st.rerun()

    with tab_feed:
        stories = get_active_stories(supabase)

        if not stories:
            st.info("No recent updates yet. Be the first to share one!")

        for story in stories:
            render_story_card(
                supabase,
                story,
                user_id
            )

# ==========================================================
# PART 8 — COMMUNITY HUB DASHBOARD AND ROUTER
# ==========================================================


def render_community_dashboard(supabase, user_id):
    """Display the Community Hub opening dashboard."""

    st.markdown(
        """
        <div style="
            padding: 22px;
            border-radius: 18px;
            background: linear-gradient(120deg, #102d4d, #075b50);
            color: white;
            margin-bottom: 18px;
        ">
            <div style="font-size: 13px; opacity: .85;">
                ECOLOOP NODE
            </div>
            <div style="font-size: 28px; font-weight: 800;">
                Community Hub
            </div>
            <div style="font-size: 14px; margin-top: 7px;">
                Connect. Collaborate. Create impact.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### Your community")

    direct_chats = get_direct_conversations(supabase, user_id)
    groups = get_my_approved_groups(supabase, user_id)
    communities = get_my_communities(supabase, user_id)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Chats", len(direct_chats))

    with col2:
        st.metric("Groups", len(groups))

    with col3:
        st.metric("Communities", len(communities))

    st.divider()
    st.markdown("### Explore Community Hub")

    cards = [
        ("💬", "Chats", "Private and group conversations."),
        ("👥", "Groups", "Join or create interest groups."),
        ("🌍", "Communities", "Connect around shared interests."),
        ("📢", "Channels", "Read community announcements."),
        ("⭕", "Updates", "Share photos, videos and updates."),
        ("🔎", "Discover People", "Find members by username."),
    ]

    for start in range(0, len(cards), 2):
        first = cards[start]
        second = cards[start + 1]

        left, right = st.columns(2)

        with left:
            with st.container(border=True):
                st.markdown(f"## {first[0]}")
                st.markdown(f"**{first[1]}**")
                st.caption(first[2])

                if st.button(
                    f"Open {first[1]}",
                    key=f"eco_dashboard_{first[1]}",
                    use_container_width=True
                ):
                    st.session_state["eco_community_section"] = first[1]
                    st.rerun()

        with right:
            with st.container(border=True):
                st.markdown(f"## {second[0]}")
                st.markdown(f"**{second[1]}**")
                st.caption(second[2])

                if st.button(
                    f"Open {second[1]}",
                    key=f"eco_dashboard_{second[1]}",
                    use_container_width=True
                ):
                    st.session_state["eco_community_section"] = second[1]
                    st.rerun()

    st.divider()

    st.markdown(
        """
        <div style="
            text-align: center;
            padding: 12px;
            color: #888;
            font-size: 12px;
        ">
            Powered by Next Gen Impact Hub (NGIH)
        </div>
        """,
        unsafe_allow_html=True
    )


def render_community_groups_page(supabase, user_id):
    """
    Main Community Hub entry point.

    Keep this function name because the main EcoLoop application
    uses it to open the Community Hub.
    """

    if not eco_is_valid_user_id(user_id):
        st.error("Please sign in to access the Community Hub.")
        return

    # Initialise navigation state.
    if "eco_community_section" not in st.session_state:
        st.session_state["eco_community_section"] = "Home"

    if "eco_community_navigation" not in st.session_state:
        st.session_state["eco_community_navigation"] = (
            st.session_state["eco_community_section"]
        )

    if "eco_active_chat" not in st.session_state:
        st.session_state["eco_active_chat"] = None

    if "eco_active_chat_type" not in st.session_state:
        st.session_state["eco_active_chat_type"] = None

    if "eco_active_group" not in st.session_state:
        st.session_state["eco_active_group"] = None

    if "eco_active_community" not in st.session_state:
        st.session_state["eco_active_community"] = None

    if "eco_active_channel" not in st.session_state:
        st.session_state["eco_active_channel"] = None

    # Header.
    st.markdown(
        """
        <div style="
            padding: 14px 4px 8px 4px;
        ">
            <div style="
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 2px;
                color: #19b5a5;
            ">
                ECOLOOP NODE
            </div>
            <div style="
                font-size: 26px;
                font-weight: 800;
            ">
                Community Hub
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Sidebar navigation.
    sections = [
        "Home",
        "Chats",
        "Groups",
        "Communities",
        "Channels",
        "Updates",
        "Discover People",
    ]

    icons = {
        "Home": "🏠",
        "Chats": "💬",
        "Groups": "👥",
        "Communities": "🌍",
        "Channels": "📢",
        "Updates": "⭕",
        "Discover People": "🔎",
    }

    # If a conversation or detail page is open, prioritise it.
    active_group = st.session_state.get("eco_active_group")
    active_chat = st.session_state.get("eco_active_chat")
    active_community = st.session_state.get("eco_active_community")
    active_channel = st.session_state.get("eco_active_channel")

    if active_group:
        render_group_chat(supabase, user_id, active_group)
        return

    if active_chat:
        chat_type = st.session_state.get("eco_active_chat_type")

        if chat_type == "direct":
            render_direct_chat(supabase, user_id, active_chat)
            return

    if active_channel:
        render_channel_chat(supabase, active_channel, user_id)
        return

    if active_community:
        render_community_detail(supabase, active_community, user_id)
        return

    # Navigation selector.
    with st.container(border=True):
        selected = st.radio(
            "Community navigation",
            sections,
            index=sections.index(
                st.session_state["eco_community_section"]
            )
            if st.session_state["eco_community_section"] in sections
            else 0,
            format_func=lambda item: f"{icons[item]}  {item}",
            key="eco_community_navigation",
            horizontal=True
        )

    if selected != st.session_state["eco_community_section"]:
        st.session_state["eco_community_section"] = selected

        # Clear old detail states when changing sections.
        for key in (
            "eco_active_chat",
            "eco_active_chat_type",
            "eco_active_group",
            "eco_active_community",
            "eco_active_channel",
        ):
            st.session_state.pop(key, None)

        st.rerun()

    section = st.session_state["eco_community_section"]

    if section == "Home":
        render_community_dashboard(supabase, user_id)

    elif section == "Chats":
        render_chats_page(supabase, user_id)

    elif section == "Groups":
        render_groups_page(supabase, user_id)

    elif section == "Communities":
        render_communities_page(supabase, user_id)

    elif section == "Channels":
        render_channels_page(supabase, user_id)

    elif section == "Updates":
        render_updates_page(supabase, user_id)

    elif section == "Discover People":
        render_people_directory(supabase, user_id)

    st.divider()

    st.caption(
        "Powered by Next Gen Impact Hub (NGIH)"
    )
