import streamlit as st
import uuid
import mimetypes
from datetime import datetime
from urllib.parse import quote


BUCKET = "community-media"
MAX_FILE_SIZE = 100 * 1024 * 1024
ADMIN_ROLES = ("admin", "group_admin", "owner", "moderator")


# =========================================================
# GENERAL HELPERS
# =========================================================

def rows(response):
    return response.data if response and response.data else []


def show_error(error, title="Something went wrong"):
    st.error(f"{title}: {error}")


def get_profiles(supabase, user_ids):
    user_ids = list(set(str(x) for x in user_ids if x))
    if not user_ids:
        return {}

    try:
        result = supabase.table("member_profiles").select(
            "*"
        ).in_("user_id", user_ids).execute()

        return {
            str(p["user_id"]): p
            for p in rows(result)
        }
    except Exception:
        return {}


def profile_name(profile):
    if not profile:
        return "EcoLoop member"

    return (
        profile.get("display_name")
        or profile.get("username")
        or "EcoLoop member"
    )


def show_person(profile):
    name = profile_name(profile)

    if profile and profile.get("avatar_url"):
        st.image(profile["avatar_url"], width=55)

    st.write(f"**{name}**")

    if profile and profile.get("username"):
        st.caption(f"@{profile['username']}")


def is_member(supabase, group_id, user_id):
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

        if rows(result):
            return True

        group = supabase.table(
            "community_groups"
        ).select("created_by").eq(
            "id", group_id
        ).limit(1).execute()

        return bool(
            rows(group)
            and str(rows(group)[0].get("created_by")) == str(user_id)
        )

    except Exception:
        return False


def is_admin(supabase, group_id, user_id):
    try:
        group = supabase.table(
            "community_groups"
        ).select("created_by").eq(
            "id", group_id
        ).limit(1).execute()

        if rows(group) and str(
            rows(group)[0].get("created_by")
        ) == str(user_id):
            return True

        result = supabase.table(
            "group_memberships"
        ).select("membership_role").eq(
            "group_id", group_id
        ).eq(
            "user_id", user_id
        ).eq(
            "status", "approved"
        ).limit(1).execute()

        if rows(result):
            return rows(result)[0].get(
                "membership_role", ""
            ).lower() in ADMIN_ROLES

    except Exception:
        pass

    return False


def upload_media(supabase, uploaded_file, folder):
    if not uploaded_file:
        return None

    if uploaded_file.size > MAX_FILE_SIZE:
        st.error("This file is larger than the 100 MB limit.")
        return None

    safe_name = uploaded_file.name.replace(" ", "_")
    path = f"{folder}/{uuid.uuid4().hex}_{safe_name}"

    try:
        supabase.storage.from_(BUCKET).upload(
            path,
            uploaded_file.getvalue(),
            {
                "content-type": uploaded_file.type
                or "application/octet-stream",
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

        return result.get("signedURL") or result.get("signedUrl")

    except Exception:
        return None


def format_time(value):
    if not value:
        return ""

    try:
        dt = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

        now = datetime.now(dt.tzinfo)

        if dt.date() == now.date():
            return dt.strftime("%H:%M")

        if dt.date().year == now.date().year:
            return dt.strftime("%d %b")

        return dt.strftime("%d %b %Y")

    except Exception:
        return ""


# =========================================================
# PROFILE
# =========================================================

def profile_editor(supabase, user_id):
    st.subheader("My community profile")

    try:
        result = supabase.table(
            "member_profiles"
        ).select("*").eq(
            "user_id", user_id
        ).limit(1).execute()

        existing = rows(result)
        profile = existing[0] if existing else {}

    except Exception as e:
        show_error(e, "Could not load profile")
        profile = {}

    with st.form("community_profile_form"):
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
            data = {
                "user_id": user_id,
                "display_name": display_name.strip(),
                "username": username.strip(),
                "bio": bio.strip(),
                "location": location.strip(),
                "interests": interests.strip(),
                "avatar_url": avatar_url.strip(),
                "updated_at": datetime.utcnow().isoformat()
            }

            try:
                supabase.table(
                    "member_profiles"
                ).upsert(data, on_conflict="user_id").execute()

                st.success("Profile updated.")
                st.rerun()

            except Exception as e:
                show_error(e, "Could not save profile")


# =========================================================
# CREATE COMMUNITY AND GROUP
# =========================================================

def create_community(supabase, user_id):
    with st.expander("Create a community"):
        with st.form("create_community_form"):
            name = st.text_input("Community name")
            description = st.text_area("Description")
            location = st.text_input("Location")
            image = st.file_uploader(
                "Community picture",
                type=["png", "jpg", "jpeg"],
                key="community_picture"
            )

            submitted = st.form_submit_button(
                "Create community",
                use_container_width=True
            )

            if submitted:
                if not name.strip():
                    st.warning("Enter a community name.")
                else:
                    image_path = upload_media(
                        supabase,
                        image,
                        f"communities/{user_id}"
                    ) if image else None

                    data = {
                        "name": name.strip(),
                        "description": description.strip(),
                        "location": location.strip(),
                        "created_by": user_id
                    }

                    if image_path:
                        data["image_url"] = image_path

                    try:
                        supabase.table(
                            "communities"
                        ).insert(data).execute()

                        st.success("Community created.")
                        st.rerun()

                    except Exception as e:
                        show_error(e, "Community creation failed")


def create_group(supabase, user_id):
    with st.expander("Create a group"):
        with st.form("create_group_form"):
            name = st.text_input("Group name")
            description = st.text_area("Group description")
            location = st.text_input("Group location")

            image = st.file_uploader(
                "Group picture",
                type=["png", "jpg", "jpeg"],
                key="group_picture"
            )

            submitted = st.form_submit_button(
                "Create group",
                use_container_width=True
            )

            if submitted:
                if not name.strip():
                    st.warning("Enter a group name.")
                else:
                    image_path = upload_media(
                        supabase,
                        image,
                        f"groups/{user_id}"
                    ) if image else None

                    data = {
                        "name": name.strip(),
                        "description": description.strip(),
                        "location": location.strip(),
                        "created_by": user_id
                    }

                    if image_path:
                        data["image_url"] = image_path

                    try:
                        result = supabase.table(
                            "community_groups"
                        ).insert(data).execute()

                        created = rows(result)

                        if created:
                            supabase.table(
                                "group_memberships"
                            ).insert({
                                "group_id": created[0]["id"],
                                "user_id": user_id,
                                "membership_role": "admin",
                                "status": "approved"
                            }).execute()

                        st.success("Group created.")
                        st.rerun()

                    except Exception as e:
                        show_error(e, "Group creation failed")


# =========================================================
# LATEST MESSAGE PREVIEW
# =========================================================

def get_latest_message(supabase, group_id):
    try:
        result = supabase.table(
            "group_messages"
        ).select("*").eq(
            "group_id", group_id
        ).order(
            "created_at", desc=True
        ).limit(1).execute()

        messages = rows(result)
        return messages[0] if messages else None

    except Exception:
        return None


def group_preview(supabase, group, user_id):
    group_id = group["id"]
    latest = get_latest_message(supabase, group_id)

    profile = None

    if latest and latest.get("sender_id"):
        profiles = get_profiles(
            supabase,
            [latest["sender_id"]]
        )
        profile = profiles.get(str(latest["sender_id"]))

    with st.container(border=True):
        col1, col2 = st.columns([1, 4])

        with col1:
            picture = media_url(
                supabase,
                group.get("image_url")
            )

            if picture:
                st.image(picture, width=65)
            else:
                st.markdown("### 👥")

        with col2:
            st.markdown(f"**{group.get('name', 'Unnamed group')}**")

            if group.get("description"):
                st.caption(group["description"])

            if latest:
                sender = profile_name(profile)

                preview = (
                    latest.get("message_text")
                    or ""
                ).strip()

                if latest.get("attachment_name"):
                    attachment_preview = (
                        f"📎 {latest['attachment_name']}"
                    )
                    preview = (
                        f"{preview} · {attachment_preview}"
                        if preview else attachment_preview
                    )

                if not preview:
                    preview = "Sent an attachment"

                if len(preview) > 75:
                    preview = preview[:72] + "..."

                st.write(f"**{sender}:** {preview}")
                st.caption(format_time(latest.get("created_at")))

            else:
                st.caption("No messages yet. Start the conversation.")

        if is_member(supabase, group_id, user_id):
            if st.button(
                "Open group →",
                key=f"open_group_{group_id}",
                use_container_width=True
            ):
                st.session_state["ecoloop_open_group_id"] = str(
                    group_id
                )
                st.rerun()

        else:
            if st.button(
                "Request to join",
                key=f"join_group_{group_id}",
                use_container_width=True
            ):
                try:
                    supabase.table(
                        "group_memberships"
                    ).insert({
                        "group_id": group_id,
                        "user_id": user_id,
                        "membership_role": "member",
                        "status": "pending"
                    }).execute()

                    st.success("Your join request has been sent.")
                    st.rerun()

                except Exception as e:
                    show_error(e, "Could not send join request")


# =========================================================
# GROUP CHAT
# =========================================================

def display_messages(supabase, messages):
    sender_ids = [
        m.get("sender_id")
        for m in messages
        if m.get("sender_id")
    ]

    profiles = get_profiles(supabase, sender_ids)

    for message in messages:
        sender_id = str(message.get("sender_id", ""))
        profile = profiles.get(sender_id)
        sender = profile_name(profile)

        timestamp = format_time(
            message.get("created_at")
        )

        with st.container(border=True):
            st.markdown(
                f"**{sender}**  "
                f"<small>{timestamp}</small>",
                unsafe_allow_html=True
            )

            text = message.get("message_text")

            if text:
                st.write(text)

            attachment_path = message.get("attachment_path")

            if attachment_path:
                url = media_url(
                    supabase,
                    attachment_path
                )

                attachment_name = message.get(
                    "attachment_name"
                ) or "Attachment"

                attachment_type = message.get(
                    "attachment_type"
                ) or ""

                if url:
                    if attachment_type.startswith("image/"):
                        st.image(url, use_container_width=True)
                    elif attachment_type.startswith("video/"):
                        st.video(url)
                    else:
                        st.markdown(
                            f"[📎 {attachment_name}]({url})"
                        )

            if message.get("is_pinned"):
                st.caption("📌 Pinned message")


def send_chat_message(
    supabase,
    group_id,
    user_id,
    message_text,
    uploaded_file
):
    message_text = (message_text or "").strip()

    if not message_text and not uploaded_file:
        st.warning("Write a message or attach a file.")
        return False

    attachment_path = None

    if uploaded_file:
        attachment_path = upload_media(
            supabase,
            uploaded_file,
            f"{group_id}/{user_id}"
        )

        if not attachment_path:
            return False

    data = {
        "group_id": group_id,
        "sender_id": user_id,
        "message_text": message_text
    }

    if uploaded_file and attachment_path:
        data.update({
            "attachment_path": attachment_path,
            "attachment_name": uploaded_file.name,
            "attachment_type": uploaded_file.type
            or mimetypes.guess_type(uploaded_file.name)[0]
            or "application/octet-stream"
        })

    try:
        supabase.table(
            "group_messages"
        ).insert(data).execute()

        return True

    except Exception as e:
        show_error(e, "Message could not be sent")
        return False


def chat_area(supabase, group_id, user_id):
    st.subheader("Group chat")

    try:
        result = supabase.table(
            "group_messages"
        ).select("*").eq(
            "group_id", group_id
        ).order(
            "created_at", desc=True
        ).limit(200).execute()

        messages = list(reversed(rows(result)))

    except Exception as e:
        show_error(e, "Could not load messages")
        messages = []

    if messages:
        display_messages(supabase, messages)
    else:
        st.info("No messages yet. Send the first message!")

    st.divider()
    st.markdown("**Write a message**")

    with st.form(
        f"group_chat_form_{group_id}",
        clear_on_submit=True
    ):
        message_text = st.text_area(
            "Message",
            placeholder="Type your message...",
            label_visibility="collapsed"
        )

        uploaded_file = st.file_uploader(
            "Attach a photo, video or document",
            key=f"chat_file_{group_id}"
        )

        submitted = st.form_submit_button(
            "Send message ➤",
            use_container_width=True
        )

        if submitted:
            success = send_chat_message(
                supabase,
                group_id,
                user_id,
                message_text,
                uploaded_file
            )

            if success:
                st.rerun()


# =========================================================
# GROUP MEMBERS
# =========================================================

def group_members(supabase, group_id, user_id):
    st.subheader("Group members")

    admin = is_admin(supabase, group_id, user_id)

    try:
        result = supabase.table(
            "group_memberships"
        ).select("*").eq(
            "group_id", group_id
        ).order(
            "joined_at"
        ).execute()

        memberships = rows(result)

    except Exception as e:
        show_error(e, "Could not load members")
        return

    profiles = get_profiles(
        supabase,
        [m.get("user_id") for m in memberships]
    )

    for member in memberships:
        member_id = str(member.get("user_id"))
        profile = profiles.get(member_id)
        status = member.get("status", "pending")
        role = member.get("membership_role", "member")

        with st.container(border=True):
            st.write(f"**{profile_name(profile)}**")
            st.caption(f"{role.title()} · {status.title()}")

            if status == "pending" and admin:
                col1, col2 = st.columns(2)

                with col1:
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

                with col2:
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
                            show_error(e, "Request removal failed")

            elif status == "approved" and admin and member_id != str(user_id):
                if st.button(
                    "Remove member",
                    key=f"remove_member_{member['id']}"
                ):
                    try:
                        supabase.table(
                            "group_memberships"
                        ).delete().eq(
                            "id", member["id"]
                        ).execute()

                        st.success("Member removed.")
                        st.rerun()

                    except Exception as e:
                        show_error(e, "Could not remove member")


# =========================================================
# GROUP PROFILE
# =========================================================

def group_profile(supabase, group, user_id):
    st.subheader("Group profile")

    group_id = group["id"]

    picture = media_url(
        supabase,
        group.get("image_url")
    )

    if picture:
        st.image(picture, width=150)

    st.write(f"**{group.get('name', '')}**")
    st.write(group.get("description", "No description yet."))
    st.caption(group.get("location", ""))

    if not is_admin(supabase, group_id, user_id):
        return

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
            "Change group picture",
            type=["png", "jpg", "jpeg"],
            key=f"edit_group_image_{group_id}"
        )

        submitted = st.form_submit_button(
            "Save group changes"
        )

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
                    f"groups/{user_id}"
                )

                if path:
                    data["image_url"] = path

            try:
                supabase.table(
                    "community_groups"
                ).update(data).eq(
                    "id", group_id
                ).execute()

                st.success("Group profile updated.")
                st.rerun()

            except Exception as e:
                show_error(e, "Could not update group")


# =========================================================
# GROUP INVITATIONS
# =========================================================

def group_invitations(supabase, group_id, user_id):
    st.subheader("Group invitations")

    if not is_admin(supabase, group_id, user_id):
        st.info("Only group admins can create invitations.")
        return

    if st.button(
        "Generate invitation code",
        key=f"generate_invite_{group_id}"
    ):
        code = uuid.uuid4().hex[:10].upper()

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
                f"new_invite_{group_id}"
            ] = code

        except Exception as e:
            show_error(e, "Could not create invitation")

    code = st.session_state.get(
        f"new_invite_{group_id}"
    )

    if code:
        st.success(f"Invitation code: {code}")
        st.code(code)


def redeem_invitation(supabase, user_id):
    st.subheader("Join with invitation code")

    with st.form("redeem_group_invite"):
        code = st.text_input(
            "Enter invitation code"
        ).strip().upper()

        submitted = st.form_submit_button(
            "Join"
        )

        if submitted:
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

                invitations = rows(result)

                if not invitations:
                    st.error("Invitation code not found or inactive.")
                    return

                invite = invitations[0]

                if invite.get("target_type") != "group":
                    st.error("This code is not a group invitation.")
                    return

                if invite.get("max_uses") is not None:
                    if invite.get("uses", 0) >= invite["max_uses"]:
                        st.error("This invitation has reached its limit.")
                        return

                group_id = invite["target_id"]

                supabase.table(
                    "group_memberships"
                ).insert({
                    "group_id": group_id,
                    "user_id": user_id,
                    "membership_role": "member",
                    "status": "pending"
                }).execute()

                st.success(
                    "Join request submitted. A group admin must approve it."
                )

            except Exception as e:
                show_error(e, "Could not redeem invitation")


# =========================================================
# GROUP WORKSPACE
# =========================================================

def group_workspace(supabase, group_id, user_id):
    try:
        result = supabase.table(
            "community_groups"
        ).select("*").eq(
            "id", group_id
        ).limit(1).execute()

        groups = rows(result)

        if not groups:
            st.error("This group could not be found.")
            return

        group = groups[0]

    except Exception as e:
        show_error(e, "Could not open group")
        return

    if not is_member(supabase, group_id, user_id):
        st.error("You are not an approved member of this group.")
        return

    if st.button("← Back to groups"):
        st.session_state["ecoloop_open_group_id"] = None
        st.rerun()

    st.title(f"👥 {group.get('name', 'Group')}")

    if group.get("description"):
        st.caption(group["description"])

    chat_tab, members_tab, profile_tab, invites_tab, meetings_tab = st.tabs([
        "💬 Chat",
        "👥 Members",
        "⚙️ Group profile",
        "🔗 Invitations",
        "📞 Meetings"
    ])

    with chat_tab:
        chat_area(supabase, group_id, user_id)

    with members_tab:
        group_members(supabase, group_id, user_id)

    with profile_tab:
        group_profile(supabase, group, user_id)

    with invites_tab:
        group_invitations(supabase, group_id, user_id)

    with meetings_tab:
        st.subheader("Group meetings")

        st.write(
            "Create a video meeting using a Jitsi meeting room."
        )

        if st.button(
            "Create meeting room",
            key=f"meeting_{group_id}"
        ):
            room = (
                "EcoLoop-"
                + str(group_id).replace("-", "")[:12]
                + "-"
                + uuid.uuid4().hex[:6]
            )

            meeting_url = (
                "https://meet.jit.si/"
                + quote(room)
            )

            st.session_state[
                f"meeting_url_{group_id}"
            ] = meeting_url

        meeting_url = st.session_state.get(
            f"meeting_url_{group_id}"
        )

        if meeting_url:
            st.success("Meeting room created.")
            st.markdown(
                f"[Join group meeting]({meeting_url})"
            )
            st.code(meeting_url)


# =========================================================
# COMMUNITIES
# =========================================================

def communities_page(supabase, user_id):
    st.subheader("Communities")

    try:
        result = supabase.table(
            "communities"
        ).select("*").order(
            "created_at", desc=True
        ).execute()

        communities = rows(result)

    except Exception as e:
        show_error(e, "Could not load communities")
        return

    if not communities:
        st.info("No communities have been created yet.")
        return

    for community in communities:
        with st.container(border=True):
            st.markdown(
                f"**{community.get('name', 'Community')}**"
            )

            if community.get("description"):
                st.write(community["description"])

            if community.get("location"):
                st.caption(community["location"])


# =========================================================
# MAIN COMMUNITY PAGE
# =========================================================

def render_community_groups_page(supabase, user_id):

    if not user_id:
        st.warning("Please sign in to access the Community.")
        return

    # -----------------------------------------------------
    # OPEN SELECTED GROUP
    # -----------------------------------------------------

    open_group_id = st.session_state.get(
        "ecoloop_open_group_id"
    )

    if open_group_id:
        group_workspace(
            supabase,
            open_group_id,
            user_id
        )
        return

    # -----------------------------------------------------
    # COMMUNITY HOME
    # -----------------------------------------------------

    st.title("🌍 EcoLoop Community")

    discover_tab, communities_tab, profile_tab, join_tab = st.tabs([
        "🔎 Discover",
        "🌍 Communities",
        "👤 My profile",
        "🔗 Join with code"
    ])

    # -----------------------------------------------------
    # DISCOVER GROUPS
    # -----------------------------------------------------

    with discover_tab:
        st.subheader("Discover groups")

        create_group(supabase, user_id)

        try:
            result = supabase.table(
                "community_groups"
            ).select("*").order(
                "created_at", desc=True
            ).execute()

            groups = rows(result)

        except Exception as e:
            show_error(e, "Could not load groups")
            groups = []

        if not groups:
            st.info(
                "No groups yet. Create the first EcoLoop group!"
            )

        for group in groups:
            group_preview(
                supabase,
                group,
                user_id
            )

    # -----------------------------------------------------
    # COMMUNITIES
    # -----------------------------------------------------

    with communities_tab:
        create_community(supabase, user_id)
        communities_page(supabase, user_id)

    # -----------------------------------------------------
    # MY PROFILE
    # -----------------------------------------------------

    with profile_tab:
        profile_editor(supabase, user_id)

    # -----------------------------------------------------
    # JOIN WITH CODE
    # -----------------------------------------------------

    with join_tab:
        redeem_invitation(supabase, user_id)

    # -----------------------------------------------------
    # MY PROFILE
    # -----------------------------------------------------

    with profile_tab:

        profile_editor(
            supabase,
            user_id
        )

    # -----------------------------------------------------
    # JOIN WITH INVITATION CODE
    # -----------------------------------------------------

    with join_tab:

        redeem_invitation(
            supabase,
            user_id
    )


# =========================================================
# MAIN COMMUNITY PAGE
# =========================================================

def render_community_groups_page(supabase, user_id):

    if not user_id:
        st.warning("Please sign in to access the Community.")
        return

    # Open one group separately from the group listing.
    open_group_id = st.session_state.get("ecoloop_open_group_id")

   if open_group_id:
    group_workspace(supabase, open_group_id, user_id)
    st.stop()

    st.title("🌍 EcoLoop Community")

    discover_tab, communities_tab, profile_tab, join_tab = st.tabs([
        "🔎 Discover",
        "🌍 Communities",
        "👤 My profile",
        "🔗 Join with code"
    ])

    with discover_tab:
        st.subheader("Discover groups")

        create_group(supabase, user_id)

        try:
            result = supabase.table(
                "community_groups"
            ).select("*").order(
                "created_at", desc=True
            ).execute()

            groups = rows(result)

        except Exception as e:
            show_error(e, "Could not load groups")
            groups = []

        if not groups:
            st.info(
                "No groups yet. Create the first EcoLoop group!"
            )

        for group in groups:
            group_preview(
                supabase,
                group,
                user_id
            )

    with communities_tab:
        create_community(supabase, user_id)
        communities_page(supabase, user_id)

    with profile_tab:
        profile_editor(supabase, user_id)

    with join_tab:
        redeem_invitation(supabase, user_id)
