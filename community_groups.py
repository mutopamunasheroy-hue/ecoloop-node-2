
# ============================================================
# ECOLOOP NODE — COMMUNITY HUB
# Next Gen Impact Hub (NGIH)
# Complete rebuild
# ============================================================

import streamlit as st
import uuid
import html
import mimetypes
from datetime import datetime, timezone, timedelta


# ============================================================
# 1. CONFIGURATION
# ============================================================

MEDIA_BUCKET = "community-media"

REACTIONS = ["👍", "❤️", "😂", "😮", "😢", "🔥", "👏"]

COMMUNITY_SECTIONS = [
    "Chats",
    "Updates",
    "Communities",
    "Channels"
]


# ============================================================
# 2. GENERAL HELPERS
# ============================================================

def eco_rows(response):
    if response and response.data:
        return response.data
    return []


def eco_escape(value):
    return html.escape(str(value or ""))


def eco_now():
    return datetime.now(timezone.utc).isoformat()


def eco_profile(supabase, user_id):
    try:
        result = (
            supabase.table("member_profiles")
            .select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else {}

    except Exception:
        return {}



def eco_member_name(supabase, user_id):
    if not user_id:
        return "EcoLoop Member"

    profile = eco_profile(supabase, user_id) or {}

    return (
        profile.get("display_name")
        or profile.get("username")
        or "EcoLoop Member"
    )

def eco_show_error(message, error=None):
    st.error(message)

    if error:
        st.caption(str(error))


# ============================================================
# 3. COMMUNITY HUB DESIGN
# ============================================================

def community_styles():

    st.markdown("""
    <style>

    .eco-community-hero {
        background: linear-gradient(120deg,#063b57,#087d72);
        padding: 23px;
        border-radius: 18px;
        color: white;
        margin-bottom: 18px;
    }

    .eco-community-hero h2 {
        color: white;
        margin: 0;
    }

    .eco-community-hero p {
        color: #e5ffff;
        margin-bottom: 0;
    }

    .eco-opening-card {
        border: 1px solid rgba(128,128,128,.30);
        border-radius: 16px;
        padding: 17px;
        min-height: 115px;
        margin-bottom: 8px;
    }

    .eco-opening-card h3 {
        margin-top: 0;
        font-size: 18px;
    }

    .eco-opening-card p {
        font-size: 13px;
        opacity: .75;
    }

    .eco-chat-bubble {
        padding: 11px 14px;
        border-radius: 15px;
        background: rgba(128,128,128,.13);
        margin: 7px 0;
        overflow-wrap: anywhere;
    }

    .eco-chat-own {
        background: rgba(0,160,120,.19);
        margin-left: 12%;
    }

    .eco-small-text {
        font-size: 11px;
        opacity: .65;
    }

    .eco-community-footer {
        text-align: center;
        font-size: 11px;
        opacity: .65;
        padding: 22px 5px;
    }

    div.stButton > button {
        border-radius: 12px;
        min-height: 42px;
    }

    </style>
    """, unsafe_allow_html=True)


# ============================================================
# 4. MEMBER PROFILES
# ============================================================

def save_member_profile(
    supabase,
    user_id,
    display_name,
    username,
    bio="",
    location="",
    interests=""
):

    payload = {
        "user_id": user_id,
        "display_name": display_name.strip(),
        "username": username.strip().lstrip("@"),
        "bio": bio.strip(),
        "location": location.strip(),
        "interests": interests.strip(),
        "updated_at": eco_now()
    }

    try:
        supabase.table("member_profiles").upsert(
            payload,
            on_conflict="user_id"
        ).execute()

        return True

    except Exception as exc:
        eco_show_error("Could not save your profile.", exc)
        return False


def render_member_profile(supabase, user_id):

    st.subheader("👤 My EcoLoop Profile")

    profile = eco_profile(supabase, user_id)

    with st.form("eco_member_profile_form"):

        display_name = st.text_input(
            "Display name",
            value=profile.get("display_name", "")
        )

        username = st.text_input(
            "Username",
            value=profile.get("username", ""),
            help="Other EcoLoop members can find you using this username."
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

        save = st.form_submit_button(
            "Save profile",
            use_container_width=True
        )

    if save:

        if not display_name.strip():
            st.warning("Please enter your display name.")

        elif not username.strip():
            st.warning("Please choose a username.")

        else:
            if save_member_profile(
                supabase,
                user_id,
                display_name,
                username,
                bio,
                location,
                interests
            ):
                st.success("Your profile has been saved.")
                st.rerun()


# ============================================================
# END OF PART 1
# NEXT: MEMBER DIRECTORY & PRIVATE CONVERSATIONS
# ============================================================

# ============================================================
# 5. MEMBER DIRECTORY — FIND PEOPLE
# ============================================================

def get_member_directory(supabase, search=""):

    try:
        query = (
            supabase.table("member_profiles")
            .select(
                "user_id, display_name, username, bio, avatar_url"
            )
        )

        if search.strip():
            term = search.strip().replace(",", "")
            query = query.or_(
                f"display_name.ilike.%{term}%,"
                f"username.ilike.%{term}%"
            )

        result = query.order(
            "display_name"
        ).limit(40).execute()

        return eco_rows(result)

    except Exception as exc:
        eco_show_error("Could not find members.", exc)
        return []


# ============================================================
# 6. PRIVATE CONVERSATIONS
# ============================================================

def get_or_create_direct_conversation(
    supabase,
    current_user_id,
    other_user_id
):

    if str(current_user_id) == str(other_user_id):
        return None

    user_one, user_two = sorted([
        str(current_user_id),
        str(other_user_id)
    ])

    try:
        existing = (
            supabase.table("direct_conversations")
            .select("id")
            .eq("user_one_id", user_one)
            .eq("user_two_id", user_two)
            .limit(1)
            .execute()
        )

        if existing.data:
            return existing.data[0]["id"]

        created = (
            supabase.table("direct_conversations")
            .insert({
                "user_one_id": user_one,
                "user_two_id": user_two
            })
            .execute()
        )

        if created.data:
            return created.data[0]["id"]

        return None

    except Exception as exc:
        eco_show_error("Could not start private conversation.", exc)
        return None


# ============================================================
# 7. LIST PRIVATE CONVERSATIONS
# ============================================================

def get_direct_conversations(supabase, user_id):

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

        conversations = eco_rows(first) + eco_rows(second)

        return conversations

    except Exception as exc:
        eco_show_error("Could not load conversations.", exc)
        return []


# ============================================================
# 8. GET PRIVATE MESSAGES
# ============================================================

def get_direct_messages(supabase, conversation_id):

    try:
        result = (
            supabase.table("direct_messages")
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=False)
            .limit(200)
            .execute()
        )

        return eco_rows(result)

    except Exception as exc:
        eco_show_error("Could not load messages.", exc)
        return []


# ============================================================
# 9. SEND PRIVATE MESSAGE
# ============================================================

def send_direct_message(
    supabase,
    conversation_id,
    sender_id,
    message_text
):

    if not message_text.strip():
        return False

    try:
        supabase.table("direct_messages").insert({
            "conversation_id": conversation_id,
            "sender_id": sender_id,
            "message_text": message_text.strip()
        }).execute()

        return True

    except Exception as exc:
        eco_show_error("Message could not be sent.", exc)
        return False


# ============================================================
# 10. MEMBER SEARCH SCREEN
# ============================================================

def render_member_directory(supabase, current_user_id):

    st.subheader("Find people")

    search = st.text_input(
        "Search EcoLoop members",
        placeholder="Search name or @username...",
        key="eco_people_search"
    )

    members = get_member_directory(supabase, search)

    if not members:
        st.info("No members found.")
        return

    for member in members:

        member_id = member.get("user_id")

        if str(member_id) == str(current_user_id):
            continue

        with st.container(border=True):

            col1, col2 = st.columns([1, 4])

            with col1:
                if member.get("avatar_url"):
                    st.image(member["avatar_url"], width=52)
                else:
                    st.markdown("👤")

            with col2:

                st.write(
                    f"**{member.get('display_name') or 'EcoLoop Member'}**"
                )

                if member.get("username"):
                    st.caption("@" + member["username"])

                if member.get("bio"):
                    st.caption(member["bio"])

                if st.button(
                    "Message",
                    key=f"eco_start_chat_{member_id}",
                    use_container_width=True
                ):

                    conversation_id = get_or_create_direct_conversation(
                        supabase,
                        current_user_id,
                        member_id
                    )

                    if conversation_id:

                        st.session_state["eco_active_direct_chat"] = (
                            conversation_id
                        )

                        st.session_state["eco_active_chat_user"] = (
                            member_id
                        )

                        st.session_state["eco_community_section"] = "Chats"

                        st.rerun()


# ============================================================
# 11. PRIVATE CHAT WINDOW
# ============================================================

def render_direct_chat(supabase, current_user_id):

    conversation_id = st.session_state.get(
        "eco_active_direct_chat"
    )

    other_user_id = st.session_state.get(
        "eco_active_chat_user"
    )

    if not conversation_id or not other_user_id:
        st.info("Select a conversation to open it.")
        return

    profile = eco_profile(supabase, other_user_id)

    display_name = (
        profile.get("display_name")
        or profile.get("username")
        or "EcoLoop Member"
    )

    if st.button("← Back to chats"):
        st.session_state.pop("eco_active_direct_chat", None)
        st.session_state.pop("eco_active_chat_user", None)
        st.rerun()

    col1, col2 = st.columns([1, 4])

    with col1:
        if profile.get("avatar_url"):
            st.image(profile["avatar_url"], width=55)
        else:
            st.markdown("👤")

    with col2:
        st.markdown(f"### {display_name}")

        if profile.get("username"):
            st.caption("@" + profile["username"])

    st.divider()

    messages = get_direct_messages(
        supabase,
        conversation_id
    )

    if not messages:
        st.info("This is the beginning of your conversation.")

    for message in messages:

        own_message = (
            str(message.get("sender_id"))
            == str(current_user_id)
        )

        with st.chat_message(
            "user" if own_message else "assistant"
        ):

            st.write(message.get("message_text") or "")

            if message.get("attachment_name"):
                st.caption(
                    "📎 " + str(message["attachment_name"])
                )

            if message.get("created_at"):
                st.caption(str(message["created_at"]))

    with st.form(
        f"eco_direct_chat_form_{conversation_id}",
        clear_on_submit=True
    ):

        message_text = st.text_area(
            "Message",
            placeholder="Type a message...",
            height=75
        )

        send = st.form_submit_button(
            "Send ➤",
            use_container_width=True
        )

    if send:

        if send_direct_message(
            supabase,
            conversation_id,
            current_user_id,
            message_text
        ):
            st.rerun()


# ============================================================
# END OF PART 2
# NEXT: UNIFIED WHATSAPP-STYLE CHAT LIST
# ============================================================

# ============================================================
# 12. UNIFIED WHATSAPP-STYLE CHAT LIST
# Private chats + group chats in ONE conversation list
# ============================================================

def get_latest_direct_message(supabase, conversation_id):

    try:
        result = (
            supabase.table("direct_messages")
            .select("message_text, sender_id, created_at")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        return result.data[0] if result.data else {}

    except Exception:
        return {}


def get_latest_group_message(supabase, group_id):

    try:
        result = (
            supabase.table("group_messages")
            .select("message_text, sender_id, created_at")
            .eq("group_id", group_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        return result.data[0] if result.data else {}

    except Exception:
        return {}


def get_my_approved_groups(supabase, user_id):

    try:
        result = (
            supabase.table("group_memberships")
            .select("group_id, status")
            .eq("user_id", user_id)
            .eq("status", "approved")
            .execute()
        )

        memberships = eco_rows(result)
        group_ids = [item["group_id"] for item in memberships]

        if not group_ids:
            return []

        groups_result = (
            supabase.table("community_groups")
            .select("*")
            .in_("id", group_ids)
            .execute()
        )

        return eco_rows(groups_result)

    except Exception as exc:
        eco_show_error("Could not load your groups.", exc)
        return []


def get_other_conversation_member(conversation, user_id):

    if str(conversation.get("user_one_id")) == str(user_id):
        return conversation.get("user_two_id")

    return conversation.get("user_one_id")


def get_unified_chat_items(supabase, user_id):

    items = []

    # ---------------- PRIVATE CHATS ----------------

    conversations = get_direct_conversations(supabase, user_id)

    for conversation in conversations:

        conversation_id = conversation.get("id")

        if not conversation_id:
            continue

        other_id = get_other_conversation_member(
            conversation, user_id
        )

        if not other_id:
            continue

        profile = eco_profile(supabase, other_id)

        latest = get_latest_direct_message(
            supabase, conversation_id
        )

        items.append({
            "type": "private",
            "id": conversation_id,
            "other_user_id": other_id,
            "name": (
                profile.get("display_name")
                or profile.get("username")
                or "EcoLoop Member"
            ),
            "username": profile.get("username") or "",
            "avatar_url": profile.get("avatar_url"),
            "preview": latest.get("message_text") or "Start a conversation",
            "timestamp": latest.get("created_at") or "",
            "sort_time": latest.get("created_at") or ""
        })

    # ---------------- GROUP CHATS ----------------

    groups = get_my_approved_groups(supabase, user_id)

    for group in groups:

        group_id = group.get("id")

        if not group_id:
            continue

        latest = get_latest_group_message(
            supabase, group_id
        )

        items.append({
            "type": "group",
            "id": group_id,
            "name": group.get("name") or "EcoLoop Group",
            "username": "",
            "avatar_url": group.get("image_url"),
            "preview": latest.get("message_text") or "No messages yet",
            "timestamp": latest.get("created_at") or "",
            "sort_time": latest.get("created_at") or ""
        })

    items.sort(
        key=lambda item: item.get("sort_time") or "",
        reverse=True
    )

    return items


# ============================================================
# 13. OPEN A CONVERSATION
# ============================================================

def open_eco_chat(item):

    if item["type"] == "private":

        st.session_state["eco_active_direct_chat"] = item["id"]

        st.session_state["eco_active_chat_user"] = (
            item["other_user_id"]
        )

        st.session_state.pop("eco_active_group", None)

    else:

        st.session_state["eco_active_group"] = item["id"]

        st.session_state.pop("eco_active_direct_chat", None)
        st.session_state.pop("eco_active_chat_user", None)

    st.rerun()


# ============================================================
# 14. WHATSAPP-INSPIRED CONVERSATION LIST
# ============================================================

def render_unified_chat_list(supabase, user_id):

    st.markdown("### 💬 Chats")

    search = st.text_input(
        "Search conversations",
        placeholder="Search chats and groups...",
        key="eco_chat_list_search"
    )

    items = get_unified_chat_items(supabase, user_id)

    if search.strip():

        term = search.strip().lower()

        items = [
            item for item in items
            if term in item["name"].lower()
            or term in item["preview"].lower()
        ]

    if not items:
        st.info(
            "Your conversations will appear here. "
            "Find EcoLoop members to start chatting."
        )
    else:

        for item in items:

            with st.container(border=True):

                col1, col2, col3 = st.columns([1, 4, 1])

                with col1:

                    if item.get("avatar_url"):
                        st.image(
                            item["avatar_url"],
                            width=48
                        )
                    else:
                        st.markdown(
                            "👥" if item["type"] == "group" else "👤"
                        )

                with col2:

                    label = (
                        "👥 " if item["type"] == "group" else ""
                    )

                    st.markdown(
                        f"**{label}{item['name']}**"
                    )

                    if item.get("username"):
                        st.caption("@" + item["username"])

                    st.caption(
                        str(item["preview"])[:75]
                    )

                with col3:

                    if item.get("timestamp"):
                        st.caption(
                            str(item["timestamp"])[11:16]
                        )

                    if st.button(
                        "Open",
                        key=f"eco_open_chat_{item['type']}_{item['id']}"
                    ):
                        open_eco_chat(item)


# ============================================================
# 15. COMPLETE CHATS PAGE
# ============================================================

def render_chats_page(supabase, user_id):

    active_direct = st.session_state.get(
        "eco_active_direct_chat"
    )

    active_group = st.session_state.get(
        "eco_active_group"
    )

    if active_direct:
        render_direct_chat(supabase, user_id)
        return

    if active_group:
        groups = get_groups(supabase)

        selected_group = next(
            (
                group for group in groups
                if str(group.get("id")) == str(active_group)
            ),
            None
        )

        if selected_group:
            render_group_chat(
                supabase, selected_group, user_id
            )
            return

        st.session_state.pop("eco_active_group", None)

    chat_tab, people_tab = st.tabs(
        ["💬 Chats", "🔎 Find people"]
    )

    with chat_tab:
        render_unified_chat_list(supabase, user_id)

    with people_tab:
        render_member_directory(supabase, user_id)


# ============================================================
# END OF PART 3
# NEXT: GROUP CREATION, DISCOVERY & ADMIN MEMBER MANAGEMENT
# ============================================================
# ============================================================
# PART 4 — GROUPS
# Create groups, discover groups, join, and manage members
# ============================================================

def get_groups(supabase, search=""):
    try:
        query = (
            supabase.table("community_groups")
            .select("*")
            .order("created_at", desc=True)
            .limit(100)
        )

        if search.strip():
            query = query.ilike("name", f"%{search.strip()}%")

        return eco_rows(query.execute())

    except Exception as e:
        eco_show_error("Could not load groups", e)
        return []


def get_group_memberships(supabase, group_id):
    try:
        response = (
            supabase.table("group_memberships")
            .select("*")
            .eq("group_id", str(group_id))
            .execute()
        )
        return eco_rows(response)

    except Exception as e:
        eco_show_error("Could not load group members", e)
        return []


def get_my_groups(supabase, user_id):
    try:
        memberships = (
            supabase.table("group_memberships")
            .select("group_id, membership_role, status")
            .eq("user_id", str(user_id))
            .eq("status", "approved")
            .execute()
        )

        group_ids = [
            row.get("group_id")
            for row in eco_rows(memberships)
            if row.get("group_id")
        ]

        created = (
            supabase.table("community_groups")
            .select("*")
            .eq("created_by", str(user_id))
            .execute()
        )

        groups = eco_rows(created)

        if group_ids:
            member_groups = (
                supabase.table("community_groups")
                .select("*")
                .in_("id", group_ids)
                .execute()
            )
            groups.extend(eco_rows(member_groups))

        unique = {}
        for group in groups:
            if group.get("id"):
                unique[str(group["id"])] = group

        return list(unique.values())

    except Exception as e:
        eco_show_error("Could not load your groups", e)
        return []


def create_community_group(
    supabase,
    user_id,
    name,
    description=""
):
    if not name.strip():
        st.warning("Enter a group name first.")
        return None

    try:
        result = (
            supabase.table("community_groups")
            .insert({
                "name": name.strip(),
                "description": description.strip(),
                "created_by": str(user_id)
            })
            .execute()
        )

        created = eco_rows(result)

        if not created:
            st.error("The group could not be created.")
            return None

        group = created[0]

        # Make the creator an approved group admin.
        supabase.table("group_memberships").insert({
            "group_id": str(group["id"]),
            "user_id": str(user_id),
            "membership_role": "admin",
            "status": "approved"
        }).execute()

        return group

    except Exception as e:
        eco_show_error("Could not create the group", e)
        return None


def request_group_membership(supabase, group_id, user_id):
    try:
        existing = (
            supabase.table("group_memberships")
            .select("id, status")
            .eq("group_id", str(group_id))
            .eq("user_id", str(user_id))
            .execute()
        )

        rows = eco_rows(existing)

        if rows:
            status = rows[0].get("status", "")

            if status == "approved":
                st.info("You are already a member of this group.")
            elif status == "pending":
                st.info("Your membership request is already pending.")
            else:
                st.info("Your existing membership record needs attention.")

            return

        supabase.table("group_memberships").insert({
            "group_id": str(group_id),
            "user_id": str(user_id),
            "membership_role": "member",
            "status": "pending"
        }).execute()

        st.success("Membership request sent.")

    except Exception as e:
        eco_show_error("Could not request group membership", e)


def is_group_admin(supabase, group_id, user_id):
    try:
        result = (
            supabase.table("group_memberships")
            .select("membership_role, status")
            .eq("group_id", str(group_id))
            .eq("user_id", str(user_id))
            .eq("status", "approved")
            .execute()
        )

        rows = eco_rows(result)

        if rows and rows[0].get("membership_role") in [
            "admin",
            "owner",
            "moderator"
        ]:
            return True

        group = (
            supabase.table("community_groups")
            .select("created_by")
            .eq("id", str(group_id))
            .limit(1)
            .execute()
        )

        group_rows = eco_rows(group)

        return bool(
            group_rows
            and str(group_rows[0].get("created_by")) == str(user_id)
        )

    except Exception:
        return False


def add_group_member(supabase, group_id, admin_id, member_id):
    if not is_group_admin(supabase, group_id, admin_id):
        st.error("Only group admins can add members.")
        return False

    try:
        existing = (
            supabase.table("group_memberships")
            .select("id")
            .eq("group_id", str(group_id))
            .eq("user_id", str(member_id))
            .execute()
        )

        if eco_rows(existing):
            st.info("This person already has a membership record.")
            return False

        supabase.table("group_memberships").insert({
            "group_id": str(group_id),
            "user_id": str(member_id),
            "membership_role": "member",
            "status": "approved"
        }).execute()

        st.success("Member added to the group.")
        return True

    except Exception as e:
        eco_show_error("Could not add this member", e)
        return False


def update_group_membership(
    supabase,
    group_id,
    admin_id,
    member_id,
    new_status
):
    if not is_group_admin(supabase, group_id, admin_id):
        st.error("Only group admins can manage membership.")
        return False

    if new_status not in ["approved", "rejected"]:
        st.error("Invalid membership status.")
        return False

    try:
        supabase.table("group_memberships").update({
            "status": new_status
        }).eq(
            "group_id", str(group_id)
        ).eq(
            "user_id", str(member_id)
        ).execute()

        st.success("Membership updated.")
        return True

    except Exception as e:
        eco_show_error("Could not update membership", e)
        return False


def render_group_card(group, supabase, user_id, show_join=True):
    group_id = group.get("id")
    name = group.get("name", "Community group")
    description = group.get("description", "")

    with st.container(border=True):
        st.markdown(f"### 👥 {eco_escape(name)}")

        if description:
            st.write(description)

        st.caption("EcoLoop community group")

        if show_join:
            if st.button(
                "Request to join",
                key=f"join_group_{group_id}",
                use_container_width=True
            ):
                request_group_membership(
                    supabase,
                    group_id,
                    user_id
                )
                st.rerun()

        if st.button(
            "Open group chat",
            key=f"open_group_{group_id}",
            use_container_width=True
        ):
            open_eco_chat("group", group_id)
            st.rerun()


def render_group_admin_members(supabase, group, user_id):
    group_id = group.get("id")

    st.markdown("#### Manage members")

    members = get_group_memberships(supabase, group_id)

    if not members:
        st.caption("No membership records found yet.")
        return

    for membership in members:
        member_id = membership.get("user_id")

        if not member_id:
            continue

        status = membership.get("status", "pending")
        role = membership.get("membership_role", "member")

        member_name = eco_member_name(supabase, member_id)

        with st.container(border=True):
            st.write(f"**{member_name}**")
            st.caption(f"{role.title()} · {status.title()}")

            if status == "pending":
                left, right = st.columns(2)

                with left:
                    if st.button(
                        "Approve",
                        key=f"approve_{group_id}_{member_id}",
                        use_container_width=True
                    ):
                        update_group_membership(
                            supabase,
                            group_id,
                            user_id,
                            member_id,
                            "approved"
                        )
                        st.rerun()

                with right:
                    if st.button(
                        "Reject",
                        key=f"reject_{group_id}_{member_id}",
                        use_container_width=True
                    ):
                        update_group_membership(
                            supabase,
                            group_id,
                            user_id,
                            member_id,
                            "rejected"
                        )
                        st.rerun()
    
            st.info("No new groups found.")
        else:
            for group in discover:
                render_group_card(
                    group,
                    supabase,
                    user_id,
                    show_join=True
                )

    with tabs[2]:
        st.markdown("### Create a group")

        with st.form("create_community_group_form"):
            group_name = st.text_input(
                "Group name",
                placeholder="e.g. Bulawayo Climate Action"
            )

            group_description = st.text_area(
                "What is this group about?",
                placeholder="Tell people what your group focuses on."
            )

            submitted = st.form_submit_button(
                "Create group",
                use_container_width=True
            )

        if submitted:
            group = create_community_group(
                supabase,
                user_id,
                group_name,
                group_description
            )

            if group:
                st.success("Your group has been created.")
                open_eco_chat("group", group.get("id"))
                st.rerun()

# ============================================================
# PART 5 — GROUP CHAT
# ============================================================

def get_group_messages(supabase, group_id):
    try:
        response = (
            supabase.table("group_messages")
            .select("*")
            .eq("group_id", str(group_id))
            .order("created_at", desc=False)
            .limit(200)
            .execute()
        )
        return eco_rows(response)

    except Exception as e:
        eco_show_error("Could not load group messages", e)
        return []


def send_group_message(supabase, group_id, sender_id, message_text):
    message_text = (message_text or "").strip()

    if not message_text:
        return False

    try:
        supabase.table("group_messages").insert({
            "group_id": str(group_id),
            "sender_id": str(sender_id),
            "message_text": message_text
        }).execute()

        return True

    except Exception as e:
        eco_show_error("Could not send your message", e)
        return False


def render_group_chat(supabase, group, user_id):
    group_id = group.get("id")
    group_name = group.get("name", "Group chat")

    st.markdown(
        f"## 👥 {eco_escape(group_name)}"
    )

    if group.get("description"):
        st.caption(group.get("description"))

    if st.button(
        "← Back to chats",
        key=f"group_back_{group_id}"
    ):
        st.session_state["eco_active_chat"] = None
        st.rerun()

    st.divider()

    if is_group_admin(supabase, group_id, user_id):
        with st.expander("Group settings and members"):
            render_group_admin_members(
                supabase,
                group,
                user_id
            )

    messages = get_group_messages(supabase, group_id)

    st.markdown("### Conversation")

    if not messages:
        st.info(
            "This group is ready. Send the first message to start the conversation."
        )

    for message in messages:
        sender_id = message.get("sender_id")
        text = message.get("message_text", "")
        created_at = message.get("created_at", "")

        profile = eco_profile(supabase, sender_id)
        sender_name = eco_member_name(profile)

        is_mine = str(sender_id) == str(user_id)

        with st.chat_message(
            "user" if is_mine else "assistant",
            avatar="🟢" if is_mine else "👤"
        ):
            if not is_mine:
                st.caption(sender_name)

            st.write(text)

            if created_at:
                st.caption(str(created_at)[:16].replace("T", " "))

    st.divider()

    with st.form(f"group_message_form_{group_id}", clear_on_submit=True):
        message_text = st.text_area(
            "Message",
            placeholder=f"Message {group_name}...",
            label_visibility="collapsed",
            height=75
        )

        submitted = st.form_submit_button(
            "Send message ➤",
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

# ============================================================
# PART 6 — COMMUNITIES
# ============================================================

def get_communities(supabase, search=""):
    try:
        query = (
            supabase.table("communities")
            .select("*")
            .order("created_at", desc=True)
            .limit(100)
        )

        if search.strip():
            query = query.ilike("name", f"%{search.strip()}%")

        return eco_rows(query.execute())

    except Exception as e:
        eco_show_error("Could not load communities", e)
        return []


def get_my_communities(supabase, user_id):
    try:
        memberships = (
            supabase.table("community_memberships")
            .select("community_id, status")
            .eq("user_id", str(user_id))
            .eq("status", "approved")
            .execute()
        )

        ids = [
            row.get("community_id")
            for row in eco_rows(memberships)
            if row.get("community_id")
        ]

        created = (
            supabase.table("communities")
            .select("*")
            .eq("created_by", str(user_id))
            .execute()
        )

        communities = eco_rows(created)

        if ids:
            joined = (
                supabase.table("communities")
                .select("*")
                .in_("id", ids)
                .execute()
            )
            communities.extend(eco_rows(joined))

        unique = {}
        for community in communities:
            if community.get("id"):
                unique[str(community["id"])] = community

        return list(unique.values())

    except Exception as e:
        eco_show_error("Could not load your communities", e)
        return []


def create_community(supabase, user_id, name, description=""):
    if not name.strip():
        st.warning("Enter a community name.")
        return None

    try:
        result = (
            supabase.table("communities")
            .insert({
                "name": name.strip(),
                "description": description.strip(),
                "created_by": str(user_id)
            })
            .execute()
        )

        rows = eco_rows(result)

        if not rows:
            st.error("The community could not be created.")
            return None

        community = rows[0]

        supabase.table("community_memberships").insert({
            "community_id": str(community["id"]),
            "user_id": str(user_id),
            "membership_role": "admin",
            "status": "approved"
        }).execute()

        return community

    except Exception as e:
        eco_show_error("Could not create community", e)
        return None


def join_community(supabase, community_id, user_id):
    try:
        existing = (
            supabase.table("community_memberships")
            .select("id, status")
            .eq("community_id", str(community_id))
            .eq("user_id", str(user_id))
            .execute()
        )

        rows = eco_rows(existing)

        if rows:
            if rows[0].get("status") == "approved":
                st.info("You are already a member.")
            else:
                st.info("You already have a membership request.")
            return

        supabase.table("community_memberships").insert({
            "community_id": str(community_id),
            "user_id": str(user_id),
            "membership_role": "member",
            "status": "pending"
        }).execute()

        st.success("Community membership request sent.")

    except Exception as e:
        eco_show_error("Could not join community", e)


def render_community_card(
    community,
    supabase,
    user_id,
    show_join=True
):
    community_id = community.get("id")

    with st.container(border=True):
        st.markdown(
            f"### 🌍 {eco_escape(community.get('name', 'Community'))}"
        )

        if community.get("description"):
            st.write(community.get("description"))

        if show_join:
            if st.button(
                "Join community",
                key=f"join_community_{community_id}",
                use_container_width=True
            ):
                join_community(
                    supabase,
                    community_id,
                    user_id
                )
                st.rerun()

        if st.button(
            "Open community",
            key=f"open_community_{community_id}",
            use_container_width=True
        ):
            st.session_state["eco_active_community"] = community_id
            st.rerun()


def render_community_detail(supabase, community, user_id):
    community_id = community.get("id")

    st.markdown(
        f"## 🌍 {eco_escape(community.get('name', 'Community'))}"
    )

    if community.get("description"):
        st.write(community.get("description"))

    if st.button(
        "← Back to communities",
        key=f"community_back_{community_id}"
    ):
        st.session_state["eco_active_community"] = None
        st.rerun()

    st.divider()
    st.markdown("### Groups in this community")

    st.info(
        "Community group linking will be connected once the community-group "
        "relationship in your database is confirmed."
    )

    st.markdown("### Community channels")

    try:
        channels = (
            supabase.table("community_channels")
            .select("*")
            .eq("community_id", str(community_id))
            .eq("is_active", True)
            .order("created_at", desc=True)
            .execute()
        )

        channel_rows = eco_rows(channels)

        if not channel_rows:
            st.caption("No channels have been created here yet.")

        for channel in channel_rows:
            with st.container(border=True):
                st.markdown(
                    f"**📢 {eco_escape(channel.get('name', 'Channel'))}**"
                )

                if st.button(
                    "Open channel",
                    key=f"open_channel_{channel.get('id')}"
                ):
                    st.session_state["eco_active_channel"] = channel.get("id")
                    st.rerun()

    except Exception as e:
        eco_show_error("Could not load community channels", e)


def render_communities_page(supabase, user_id):
    active_id = st.session_state.get("eco_active_community")

    if active_id:
        communities = get_my_communities(supabase, user_id)
        community = next(
            (
                item for item in communities
                if str(item.get("id")) == str(active_id)
            ),
            None
        )

        if community:
            render_community_detail(
                supabase,
                community,
                user_id
            )
            return

        st.session_state["eco_active_community"] = None

    st.title("Communities")
    st.caption("Connect groups and people around shared causes.")

    tabs = st.tabs([
        "My Communities",
        "Discover",
        "Create"
    ])

    with tabs[0]:
        mine = get_my_communities(supabase, user_id)

        if not mine:
            st.info("You haven't joined any communities yet.")

        for community in mine:
            render_community_card(
                community,
                supabase,
                user_id,
                show_join=False
            )

    with tabs[1]:
        search = st.text_input(
            "Search communities",
            placeholder="Find a community..."
        )

        mine_ids = {
            str(item.get("id"))
            for item in get_my_communities(supabase, user_id)
        }

        discover = [
            item for item in get_communities(supabase, search)
            if str(item.get("id")) not in mine_ids
        ]

        if not discover:
            st.info("No new communities found.")

        for community in discover:
            render_community_card(
                community,
                supabase,
                user_id,
                show_join=True
            )

    with tabs[2]:
        with st.form("create_community_form"):
            name = st.text_input(
                "Community name",
                placeholder="e.g. Bulawayo Green Network"
            )

            description = st.text_area(
                "Community description",
                placeholder="What brings this community together?"
            )

            submitted = st.form_submit_button(
                "Create community",
                use_container_width=True
            )

        if submitted:
            created = create_community(
                supabase,
                user_id,
                name,
                description
            )

            if created:
                st.success("Community created.")
                st.session_state["eco_active_community"] = created.get("id")
                st.rerun()

# ============================================================
# PART 7 — CHANNELS
# ============================================================

def get_community_channels(supabase, community_id):
    try:
        result = (
            supabase.table("community_channels")
            .select("*")
            .eq("community_id", str(community_id))
            .eq("is_active", True)
            .order("created_at", desc=True)
            .execute()
        )
        return eco_rows(result)

    except Exception as e:
        eco_show_error("Could not load channels", e)
        return []


def create_community_channel(
    supabase,
    community_id,
    user_id,
    channel_name,
    channel_description=""
):
    if not channel_name.strip():
        st.warning("Enter a channel name.")
        return None

    try:
        result = (
            supabase.table("community_channels")
            .insert({
                "community_id": str(community_id),
                "name": channel_name.strip(),
                "description": channel_description.strip(),
                "channel_type": "announcement",
                "is_active": True
            })
            .execute()
        )

        rows = eco_rows(result)

        if not rows:
            st.error("The channel could not be created.")
            return None

        return rows[0]

    except Exception as e:
        eco_show_error("Could not create channel", e)
        return None


def get_channel_messages(supabase, channel_id):
    try:
        result = (
            supabase.table("channel_messages")
            .select("*")
            .eq("channel_id", str(channel_id))
            .order("created_at", desc=False)
            .limit(200)
            .execute()
        )
        return eco_rows(result)

    except Exception as e:
        eco_show_error("Could not load channel posts", e)
        return []


def send_channel_message(
    supabase,
    channel_id,
    sender_id,
    message_text
):
    message_text = (message_text or "").strip()

    if not message_text:
        return False

    try:
        supabase.table("channel_messages").insert({
            "channel_id": str(channel_id),
            "sender_id": str(sender_id),
            "message_text": message_text
        }).execute()

        return True

    except Exception as e:
        eco_show_error("Could not publish your message", e)
        return False


def is_community_admin(supabase, community_id, user_id):
    try:
        result = (
            supabase.table("community_memberships")
            .select("membership_role, status")
            .eq("community_id", str(community_id))
            .eq("user_id", str(user_id))
            .eq("status", "approved")
            .execute()
        )

        rows = eco_rows(result)

        if rows and rows[0].get("membership_role") in [
            "admin", "owner", "moderator"
        ]:
            return True

        community = (
            supabase.table("communities")
            .select("created_by")
            .eq("id", str(community_id))
            .limit(1)
            .execute()
        )

        community_rows = eco_rows(community)

        return bool(
            community_rows
            and str(community_rows[0].get("created_by")) == str(user_id)
        )

    except Exception:
        return False


def render_channel_chat(supabase, channel, user_id):
    channel_id = channel.get("id")
    channel_name = channel.get("name", "Announcement channel")

    st.markdown(f"## 📢 {eco_escape(channel_name)}")
    st.caption("Community announcements and updates")

    if st.button(
        "← Back to channels",
        key=f"channel_back_{channel_id}"
    ):
        st.session_state["eco_active_channel"] = None
        st.rerun()

    st.divider()

    messages = get_channel_messages(supabase, channel_id)

    if not messages:
        st.info("No announcements have been published yet.")

    for message in messages:
        sender_id = message.get("sender_id")
        profile = eco_profile(supabase, sender_id)
        sender_name = eco_member_name(profile)

        with st.container(border=True):
            st.caption(f"📣 {sender_name}")
            st.write(message.get("message_text", ""))

            if message.get("created_at"):
                st.caption(
                    str(message["created_at"])[:16].replace("T", " ")
                )

    if is_community_admin(
        supabase,
        channel.get("community_id"),
        user_id
    ):
        st.divider()
        st.markdown("### Publish an announcement")

        with st.form(
            f"channel_post_form_{channel_id}",
            clear_on_submit=True
        ):
            message_text = st.text_area(
                "Announcement",
                placeholder="Share an update with this community...",
                height=110
            )

            submitted = st.form_submit_button(
                "Publish announcement 📢",
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
        st.caption("Only community admins can publish announcements.")


def render_channels_page(supabase, user_id):
    active_id = st.session_state.get("eco_active_channel")

    if active_id:
        try:
            result = (
                supabase.table("community_channels")
                .select("*")
                .eq("id", str(active_id))
                .limit(1)
                .execute()
            )

            rows = eco_rows(result)

            if rows:
                render_channel_chat(
                    supabase,
                    rows[0],
                    user_id
                )
                return

        except Exception as e:
            eco_show_error("Could not open channel", e)

        st.session_state["eco_active_channel"] = None

    st.title("Channels")
    st.caption("Follow announcements from your communities.")

    communities = get_my_communities(supabase, user_id)

    if not communities:
        st.info("Join or create a community before creating a channel.")
        return

    community_names = {
        item.get("name", "Community"): item.get("id")
        for item in communities
        if item.get("id")
    }

    tabs = st.tabs(["Explore Channels", "Create Channel"])

    with tabs[0]:
        selected_community = st.selectbox(
            "Choose a community",
            list(community_names.keys()),
            key="channel_explore_community"
        )

        community_id = community_names[selected_community]
        channels = get_community_channels(supabase, community_id)

        if not channels:
            st.info("No active channels in this community yet.")

        for channel in channels:
            with st.container(border=True):
                st.markdown(
                    f"### 📢 {eco_escape(channel.get('name', 'Channel'))}"
                )

                st.caption("Announcement channel")

                if st.button(
                    "Open channel",
                    key=f"open_channel_chat_{channel.get('id')}",
                    use_container_width=True
                ):
                    st.session_state["eco_active_channel"] = channel.get("id")
                    st.rerun()

    with tabs[1]:
        selected_community = st.selectbox(
            "Create channel in",
            list(community_names.keys()),
            key="channel_create_community"
        )

        community_id = community_names[selected_community]

        if not is_community_admin(supabase, community_id, user_id):
            st.info("Only community admins can create channels.")
        else:
            with st.form("create_channel_form"):
                channel_name = st.text_input(
                    "Channel name",
                    placeholder="e.g. Official Announcements"
                )

                channel_description = st.text_area(
                    "Channel description",
                    placeholder="What will this channel share?"
                )

                submitted = st.form_submit_button(
                    "Create channel",
                    use_container_width=True
                )

            if submitted:
                channel = create_community_channel(
                    supabase,
                    community_id,
                    user_id,
                    channel_name,
                    channel_description
                )

                if channel:
                    st.success("Channel created.")
                    st.session_state["eco_active_channel"] = channel.get("id")
                    st.rerun()

# ============================================================
# PART 8 — UPDATES AND STORIES
# Stories expire after 24 hours
# ============================================================

def upload_story_media(supabase, user_id, uploaded_file):
    if uploaded_file is None:
        return None, None

    try:
        file_bytes = uploaded_file.getvalue()
        original_name = uploaded_file.name
        extension = original_name.rsplit(".", 1)[-1].lower()

        safe_name = (
            f"stories/{user_id}/"
            f"{uuid.uuid4().hex}.{extension}"
        )

        content_type = (
            uploaded_file.type
            or mimetypes.guess_type(original_name)[0]
            or "application/octet-stream"
        )

        supabase.storage.from_(MEDIA_BUCKET).upload(
            safe_name,
            file_bytes,
            {"content-type": content_type}
        )

        media_type = (
            "image" if content_type.startswith("image/")
            else "video" if content_type.startswith("video/")
            else "file"
        )

        return safe_name, media_type

    except Exception as e:
        eco_show_error("Could not upload story media", e)
        return None, None


def get_story_media_url(supabase, storage_path):
    if not storage_path:
        return None

    try:
        result = supabase.storage.from_(MEDIA_BUCKET).create_signed_url(
            storage_path,
            3600
        )

        if isinstance(result, dict):
            return (
                result.get("signedURL")
                or result.get("signedUrl")
            )

        return None

    except Exception:
        return None


def create_story(
    supabase,
    user_id,
    caption,
    uploaded_file=None
):
    media_path = None
    media_type = None

    if uploaded_file is not None:
        media_path, media_type = upload_story_media(
            supabase,
            user_id,
            uploaded_file
        )

        if not media_path:
            return False

    try:
        now = datetime.now(timezone.utc)

        supabase.table("stories").insert({
            "user_id": str(user_id),
            "caption": (caption or "").strip(),
            "media_url": media_path,
            "media_type": media_type,
            "created_at": now.isoformat(),
            "expires_at": (
                now + timedelta(hours=24)
            ).isoformat()
        }).execute()

        return True

    except Exception as e:
        eco_show_error("Could not publish your story", e)
        return False


def get_active_stories(supabase):
    try:
        now = datetime.now(timezone.utc).isoformat()

        result = (
            supabase.table("stories")
            .select("*")
            .gt("expires_at", now)
            .order("created_at", desc=True)
            .limit(100)
            .execute()
        )

        return eco_rows(result)

    except Exception as e:
        eco_show_error("Could not load stories", e)
        return []


def render_story_card(supabase, story):
    user_id = story.get("user_id")
    profile = eco_profile(supabase, user_id)
    name = eco_member_name(profile)

    created_at = story.get("created_at", "")
    caption = story.get("caption", "")
    media_path = story.get("media_url")
    media_type = story.get("media_type")

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
                if media_type == "image":
                    st.image(
                        media_url,
                        use_container_width=True
                    )
                elif media_type == "video":
                    st.video(media_url)
                else:
                    st.caption("Story attachment")
            else:
                st.caption("Story media is currently unavailable.")

        st.caption("Stories disappear after 24 hours.")


def render_updates_page(supabase, user_id):
    st.title("Updates")
    st.caption("Share moments and see what's happening in EcoLoop.")

    with st.expander("＋ Create a story", expanded=False):
        with st.form(
            "create_story_form",
            clear_on_submit=True
        ):
            caption = st.text_area(
                "What's happening?",
                placeholder="Share an update with the community..."
            )

            uploaded_file = st.file_uploader(
                "Add a photo or video (optional)",
                type=[
                    "jpg", "jpeg", "png", "webp",
                    "mp4", "mov"
                ]
            )

            submitted = st.form_submit_button(
                "Share story",
                use_container_width=True
            )

        if submitted:
            if not caption.strip() and uploaded_file is None:
                st.warning("Add some text or a photo/video first.")
            else:
                if create_story(
                    supabase,
                    user_id,
                    caption,
                    uploaded_file
                ):
                    st.success("Your story has been shared.")
                    st.rerun()

    st.divider()
    st.markdown("### Recent stories")

    stories = get_active_stories(supabase)

    if not stories:
        st.info("No active stories yet. Be the first to share one.")
        return

    for story in stories:
        render_story_card(supabase, story)

# ============================================================
# PART 9 — COMMUNITY HUB DASHBOARD AND NAVIGATION
# ============================================================

def render_community_dashboard(supabase, user_id):
    st.title("💬 Community Hub")
    st.caption("Connect. Share. Organise. Make an impact.")

    st.markdown("""
    <div style="
        padding:18px;
        border-radius:16px;
        background:linear-gradient(120deg,#102c45,#145b55);
        color:white;
        margin-bottom:18px;
    ">
        <div style="font-size:12px;opacity:0.85;">
            ECOLOOP NODE COMMUNITY
        </div>
        <div style="font-size:23px;font-weight:800;margin-top:5px;">
            Your community starts here.
        </div>
        <div style="font-size:13px;margin-top:7px;opacity:0.9;">
            Meet people, join groups and work together for change.
        </div>
    </div>
    """, unsafe_allow_html=True)

    sections = [
        ("💬", "Chats", "Private and group conversations"),
        ("👥", "Groups", "Find people with shared interests"),
        ("🌍", "Communities", "Connect groups around shared causes"),
        ("📢", "Channels", "Follow community announcements"),
        ("⭕", "Updates", "See stories and recent updates"),
    ]

    for icon, name, description in sections:
        with st.container(border=True):
            left, right = st.columns([4, 1])

            with left:
                st.markdown(f"### {icon} {name}")
                st.caption(description)

            with right:
                if st.button(
                    "Open",
                    key=f"community_dashboard_{name}",
                    use_container_width=True
                ):
                    st.session_state["eco_community_section"] = name
                    st.session_state["eco_active_chat"] = None
                    st.session_state["eco_active_community"] = None
                    st.session_state["eco_active_channel"] = None
                    st.rerun()

    st.divider()

    st.caption("Powered by Next Gen Impact Hub (NGIH)")


def render_community_groups_page(supabase, user_id):
    community_styles()

    if not user_id:
        st.warning("Please sign in to use the Community Hub.")
        return

    if "eco_community_section" not in st.session_state:
        st.session_state["eco_community_section"] = "Home"

    if "eco_active_chat" not in st.session_state:
        st.session_state["eco_active_chat"] = None

    if "eco_active_community" not in st.session_state:
        st.session_state["eco_active_community"] = None

    if "eco_active_channel" not in st.session_state:
        st.session_state["eco_active_channel"] = None

    current = st.session_state["eco_community_section"]

    # Main navigation
    navigation = [
        "Home",
        "Chats",
        "Updates",
        "Communities",
        "Channels",
        "Groups"
    ]

    selected = st.radio(
        "Community navigation",
        navigation,
        index=navigation.index(current)
        if current in navigation else 0,
        horizontal=True,
        key="eco_community_navigation"
    )

    if selected != current:
        st.session_state["eco_community_section"] = selected
        st.session_state["eco_active_chat"] = None
        st.session_state["eco_active_community"] = None
        st.session_state["eco_active_channel"] = None
        st.rerun()

    st.divider()

    section = st.session_state["eco_community_section"]

    if section == "Home":
        render_community_dashboard(supabase, user_id)

    elif section == "Chats":
        render_chats_page(supabase, user_id)

    elif section == "Updates":
        render_updates_page(supabase, user_id)

    elif section == "Communities":
        render_communities_page(supabase, user_id)

    elif section == "Channels":
        render_channels_page(supabase, user_id)

    elif section == "Groups":
        render_groups_page(supabase, user_id)
