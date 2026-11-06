
import streamlit as st
import uuid
import mimetypes
from urllib.parse import quote

# ==========================================================
# ECOLOOP NODE — COMMUNITY HUB
# Next Gen Impact Hub (NGIH)
# ==========================================================

BUCKET = "community-media"
MAX_FILE_SIZE = 100 * 1024 * 1024

ADMIN_ROLES = ("admin", "group_admin", "owner", "moderator")


# ==========================================================
# GENERAL HELPERS
# ==========================================================

def rows(response):
    return getattr(response, "data", None) or []


def show_error(message, error=None):
    st.error(message)
    if error:
        with st.expander("Technical details"):
            st.code(str(error))


def upload_media(supabase, target_id, user_id, file):
    if not file:
        return None

    content = file.getvalue()

    if len(content) > MAX_FILE_SIZE:
        raise ValueError("Maximum attachment size is 100 MB.")

    safe_name = "".join(
        c if c.isalnum() or c in "._-" else "_"
        for c in file.name
    )

    path = (
        f"{target_id}/{user_id}/"
        f"{uuid.uuid4().hex}_{safe_name}"
    )

    mime = (
        file.type
        or mimetypes.guess_type(file.name)[0]
        or "application/octet-stream"
    )

    supabase.storage.from_(BUCKET).upload(
        path,
        content,
        file_options={
            "content-type": mime,
            "upsert": "false"
        }
    )

    return {
        "path": path,
        "name": file.name,
        "type": mime
    }


def media_url(supabase, path):
    if not path:
        return None

    try:
        result = supabase.storage.from_(BUCKET).create_signed_url(
            path, 3600
        )

        if isinstance(result, dict):
            return result.get("signedURL") or result.get("signedUrl")

    except Exception:
        return None

    return None


def get_profiles(supabase, user_ids):
    ids = list(set(str(x) for x in user_ids if x))

    if not ids:
        return {}

    try:
        response = (
            supabase.table("member_profiles")
            .select("*")
            .in_("user_id", ids)
            .execute()
        )

        return {
            str(p["user_id"]): p
            for p in rows(response)
        }

    except Exception:
        return {}


def show_person(supabase, user_id, profiles=None):
    if not user_id:
        st.write("Unknown member")
        return

    profiles = profiles or get_profiles(supabase, [user_id])
    profile = profiles.get(str(user_id), {})

    name = (
        profile.get("display_name")
        or profile.get("username")
        or "EcoLoop member"
    )

    avatar = profile.get("avatar_url")

    left, right = st.columns([1, 5])

    with left:
        if avatar:
            st.image(avatar, width=55)
        else:
            st.markdown("👤")

    with right:
        st.markdown(f"**{name}**")
        if profile.get("username"):
            st.caption("@" + profile["username"])


def is_admin(group, user_id, memberships):
    if str(group.get("created_by")) == str(user_id):
        return True

    return any(
        str(m.get("user_id")) == str(user_id)
        and str(m.get("group_id")) == str(group.get("id"))
        and m.get("status") == "approved"
        and str(m.get("membership_role", "")).lower() in ADMIN_ROLES
        for m in memberships
    )


def is_member(group, user_id, memberships):
    if str(group.get("created_by")) == str(user_id):
        return True

    return any(
        str(m.get("user_id")) == str(user_id)
        and str(m.get("group_id")) == str(group.get("id"))
        and m.get("status") == "approved"
        for m in memberships
    )


def invite_url(code):
    base = st.get_option("server.address")
    return f"EcoLoop invitation code: {code}"


# ==========================================================
# PERSONAL PROFILE
# ==========================================================

def profile_editor(supabase, user_id):
    st.subheader("👤 My EcoLoop profile")

    try:
        response = (
            supabase.table("member_profiles")
            .select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        existing = rows(response)
        profile = existing[0] if existing else {}

    except Exception as error:
        show_error("Could not load your profile.", error)
        return

    with st.form("community_personal_profile"):
        name = st.text_input(
            "Display name",
            value=profile.get("display_name") or ""
        )

        username = st.text_input(
            "Username",
            value=profile.get("username") or ""
        )

        bio = st.text_area(
            "Short bio",
            value=profile.get("bio") or ""
        )

        location = st.text_input(
            "Location",
            value=profile.get("location") or ""
        )

        interests = st.text_input(
            "Environmental interests",
            value=profile.get("interests") or ""
        )

        avatar = st.text_input(
            "Profile picture URL",
            value=profile.get("avatar_url") or "",
            help="Paste a publicly accessible image URL."
        )

        save = st.form_submit_button(
            "Save my profile",
            use_container_width=True
        )

    if save:
        if not name.strip():
            st.warning("Please enter a display name.")
            return

        if not username.strip():
            st.warning("Please choose a username.")
            return

        try:
            supabase.table("member_profiles").upsert({
                "user_id": user_id,
                "display_name": name.strip(),
                "username": username.strip().lstrip("@"),
                "bio": bio.strip(),
                "location": location.strip(),
                "interests": interests.strip(),
                "avatar_url": avatar.strip() or None
            }).execute()

            st.success("Your profile has been updated.")
            st.rerun()

        except Exception as error:
            show_error("Could not save your profile.", error)


# ==========================================================
# COMMUNITIES
# ==========================================================

def create_community(supabase, user_id):
    with st.expander("🌍 Create a community"):
        with st.form("create_ecoloop_community"):
            name = st.text_input("Community name")
            description = st.text_area("Community description")
            location = st.text_input("Location")

            submit = st.form_submit_button("Create community")

        if submit:
            if not name.strip():
                st.warning("Enter a community name.")
                return

            try:
                supabase.table("communities").insert({
                    "name": name.strip(),
                    "description": description.strip(),
                    "location": location.strip(),
                    "created_by": user_id
                }).execute()

                st.success("Community created!")
                st.rerun()

            except Exception as error:
                show_error("Could not create community.", error)


def create_group(supabase, user_id, communities):
    with st.expander("🌱 Create a group"):
        options = {"No community": None}

        for community in communities:
            options[community["name"]] = community["id"]

        with st.form("create_ecoloop_group"):
            name = st.text_input("Group name")
            description = st.text_area("Group description")
            location = st.text_input("Location")
            selected = st.selectbox(
                "Belongs to community",
                list(options.keys())
            )

            submit = st.form_submit_button("Create group")

        if submit:
            if not name.strip():
                st.warning("Enter a group name.")
                return

            try:
                supabase.table("community_groups").insert({
                    "name": name.strip(),
                    "description": description.strip(),
                    "location": location.strip(),
                    "community_id": options[selected],
                    "created_by": user_id
                }).execute()

                st.success("Group created!")
                st.rerun()

            except Exception as error:
                show_error("Could not create group.", error)


# ==========================================================
# INVITATION LINKS
# ==========================================================

def create_invitation(supabase, target_type, target_id, user_id):
    st.markdown("**Create an invitation link**")

    with st.form(f"invite_{target_type}_{target_id}"):
        expiry = st.selectbox(
            "Link expiry",
            ["Never", "24 hours", "7 days", "30 days"]
        )

        max_uses = st.number_input(
            "Maximum uses (0 = unlimited)",
            min_value=0,
            max_value=10000,
            value=0
        )

        submit = st.form_submit_button("Generate invitation")

    if submit:
        from datetime import datetime, timedelta, timezone

        expiry_map = {
            "Never": None,
            "24 hours": 1,
            "7 days": 7,
            "30 days": 30
        }

        days = expiry_map[expiry]
        expires_at = (
            (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
            if days else None
        )

        try:
            result = supabase.table("community_invites").insert({
                "target_type": target_type,
                "target_id": target_id,
                "created_by": user_id,
                "expires_at": expires_at,
                "max_uses": max_uses if max_uses else None
            }).execute()

            created = rows(result)

            if created:
                code = created[0]["invite_code"]
                st.success("Invitation created!")
                st.code(code)
                st.caption(
                    "Share this invitation code with people. "
                    "They can enter it in EcoLoop to request access."
                )

        except Exception as error:
            show_error("Could not create invitation.", error)


def redeem_invitation(supabase, user_id):
    with st.expander("🔗 Join using an invitation code"):
        code = st.text_input("Enter invitation code")

        if st.button("Find invitation"):
            if not code.strip():
                st.warning("Enter an invitation code.")
                return

            try:
                result = (
                    supabase.table("community_invites")
                    .select("*")
                    .eq("invite_code", code.strip())
                    .eq("is_active", True)
                    .limit(1)
                    .execute()
                )

                invitations = rows(result)

                if not invitations:
                    st.error("Invitation not found or inactive.")
                    return

                invitation = invitations[0]

                from datetime import datetime, timezone

                expires = invitation.get("expires_at")
                if expires:
                    expiry_time = datetime.fromisoformat(
                        expires.replace("Z", "+00:00")
                    )
                    if expiry_time <= datetime.now(timezone.utc):
                        st.error("This invitation has expired.")
                        return

                maximum = invitation.get("max_uses")
                uses = invitation.get("uses") or 0

                if maximum and uses >= maximum:
                    st.error("This invitation has reached its use limit.")
                    return

                target_id = invitation["target_id"]
                target_type = invitation["target_type"]

                if target_type == "group":
                    existing = rows(
                        supabase.table("group_memberships")
                        .select("*")
                        .eq("group_id", target_id)
                        .eq("user_id", user_id)
                        .execute()
                    )

                    if existing:
                        st.info("You already have a membership record.")
                        return

                    supabase.table("group_memberships").insert({
                        "group_id": target_id,
                        "user_id": user_id,
                        "status": "pending"
                    }).execute()

                else:
                    existing = rows(
                        supabase.table("community_memberships")
                        .select("*")
                        .eq("community_id", target_id)
                        .eq("user_id", user_id)
                        .execute()
                    )

                    if existing:
                        st.info("You already have a membership record.")
                        return

                    supabase.table("community_memberships").insert({
                        "community_id": target_id,
                        "user_id": user_id,
                        "status": "pending"
                    }).execute()

                supabase.table("community_invites").update({
                    "uses": uses + 1
                }).eq("id", invitation["id"]).execute()

                st.success("Your request to join has been submitted.")
                st.rerun()

            except Exception as error:
                show_error("Could not process invitation.", error)


# ==========================================================
# GROUP MEMBERSHIPS
# ==========================================================

def group_members(supabase, group, user_id, admin):
    group_id = group["id"]

    st.subheader("👥 Members")

    try:
        memberships = rows(
            supabase.table("group_memberships")
            .select("*")
            .eq("group_id", group_id)
            .execute()
        )

    except Exception as error:
        show_error("Could not load members.", error)
        return

    pending = [m for m in memberships if m.get("status") == "pending"]
    approved = [m for m in memberships if m.get("status") == "approved"]

    st.caption(f"{len(approved)} approved members")

    profiles = get_profiles(
        supabase,
        [m.get("user_id") for m in approved + pending]
    )

    if admin and pending:
        with st.expander(f"📩 Requests to join ({len(pending)})"):
            for member in pending:
                member_id = member["id"]
                show_person(
                    supabase,
                    member["user_id"],
                    profiles
                )

                col1, col2 = st.columns(2)

                with col1:
                    if st.button(
                        "Approve",
                        key=f"approve_{member_id}"
                    ):
                        try:
                            supabase.table("group_memberships").update({
                                "status": "approved",
                                "membership_role": "member"
                            }).eq("id", member_id).execute()

                            st.success("Member approved.")
                            st.rerun()
                        except Exception as error:
                            show_error("Approval failed.", error)

                with col2:
                    if st.button(
                        "Reject",
                        key=f"reject_{member_id}"
                    ):
                        try:
                            supabase.table("group_memberships").update({
                                "status": "rejected"
                            }).eq("id", member_id).execute()

                            st.rerun()
                        except Exception as error:
                            show_error("Rejection failed.", error)

    for member in approved:
        member_id = member["id"]
        member_user = member["user_id"]
        role = member.get("membership_role") or "member"

        with st.container(border=True):
            show_person(supabase, member_user, profiles)
            st.caption(role.title())

            if admin and str(member_user) != str(user_id):
                if role.lower() in ADMIN_ROLES:
                    if st.button(
                        "Remove administrator",
                        key=f"demote_{member_id}"
                    ):
                        try:
                            supabase.table("group_memberships").update({
                                "membership_role": "member"
                            }).eq("id", member_id).execute()
                            st.rerun()
                        except Exception as error:
                            show_error("Could not change role.", error)
                else:
                    if st.button(
                        "Appoint administrator",
                        key=f"promote_{member_id}"
                    ):
                        try:
                            supabase.table("group_memberships").update({
                                "membership_role": "admin"
                            }).eq("id", member_id).execute()
                            st.rerun()
                        except Exception as error:
                            show_error("Could not appoint administrator.", error)

                if st.button(
                    "Remove member",
                    key=f"remove_{member_id}"
                ):
                    try:
                        supabase.table("group_memberships").delete().eq(
                            "id", member_id
                        ).execute()
                        st.rerun()
                    except Exception as error:
                        show_error("Could not remove member.", error)


# ==========================================================
# GROUP PROFILE
# ==========================================================

def group_profile(supabase, group, admin):
    st.subheader("🌱 " + group.get("name", "Community group"))

    st.write(group.get("description") or "No description provided.")

    if group.get("location"):
        st.caption("📍 " + group["location"])

    if group.get("image_url"):
        image = media_url(supabase, group["image_url"])
        if image:
            st.image(image, use_container_width=True)

    if admin:
        with st.expander("Edit group profile"):
            with st.form(f"edit_group_{group['id']}"):
                name = st.text_input(
                    "Group name",
                    value=group.get("name") or ""
                )
                description = st.text_area(
                    "Description",
                    value=group.get("description") or ""
                )
                location = st.text_input(
                    "Location",
                    value=group.get("location") or ""
                )

                save = st.form_submit_button("Save changes")

            if save:
                try:
                    supabase.table("community_groups").update({
                        "name": name.strip(),
                        "description": description.strip(),
                        "location": location.strip()
                    }).eq("id", group["id"]).execute()

                    st.success("Group updated.")
                    st.rerun()
                except Exception as error:
                    show_error("Could not update group.", error)


# ==========================================================
# MESSAGE DISPLAY
# ==========================================================

def display_messages(supabase, messages, user_id, table, target_id):
    sender_ids = [m.get("sender_id") for m in messages]
    profiles = get_profiles(supabase, sender_ids)

    pinned = [m for m in messages if m.get("is_pinned")]

    if pinned:
        with st.expander(f"📌 Pinned messages ({len(pinned)})", expanded=True):
            for message in pinned:
                profile = profiles.get(str(message.get("sender_id")), {})
                name = profile.get("display_name") or profile.get("username") or "Member"
                st.markdown(f"**{name}:** {message.get('message_text') or 'Attachment'}")

    for message in messages:
        sender = message.get("sender_id")
        profile = profiles.get(str(sender), {})
        name = (
            profile.get("display_name")
            or profile.get("username")
            or "EcoLoop member"
        )

        with st.container(border=True):
            col1, col2 = st.columns([1, 5])

            with col1:
                if profile.get("avatar_url"):
                    st.image(profile["avatar_url"], width=48)
                else:
                    st.markdown("👤")

            with col2:
                st.markdown(f"**{name}**")
                st.caption(str(message.get("created_at") or ""))

            if message.get("forwarded_from"):
                st.caption("↪ Forwarded message")

            if message.get("is_pinned"):
                st.caption("📌 Pinned")

            if message.get("message_text"):
                st.write(message["message_text"])

            path = message.get("attachment_path")
            if path:
                url = media_url(supabase, path)
                mime = message.get("attachment_type") or ""
                filename = message.get("attachment_name") or "Attachment"

                if url:
                    if mime.startswith("image/"):
                        st.image(url, caption=filename)
                    elif mime.startswith("video/"):
                        st.video(url)
                    elif mime.startswith("audio/"):
                        st.audio(url)
                    else:
                        st.markdown(f"[📎 Open {filename}]({url})")
                else:
                    st.warning("Attachment unavailable.")

            if st.button(
                "↪ Forward",
                key=f"forward_{table}_{message['id']}"
            ):
                st.session_state[
                    f"forward_message_{target_id}"
                ] = message["id"]

            if st.session_state.get(
                f"forward_message_{target_id}"
            ) == message["id"]:
                st.caption("Choose a destination group below.")

            if sender and str(sender) != str(user_id):
                st.caption("Sent by another member")


# ==========================================================
# CHAT SENDING
# ==========================================================

def send_chat_message(
    supabase,
    table,
    target_column,
    target_id,
    user_id,
    text,
    file,
    forwarded_from=None
):
    if not text.strip() and not file and not forwarded_from:
        st.warning("Write a message or attach a file.")
        return

    try:
        payload = {
            target_column: target_id,
            "sender_id": user_id,
            "message_text": text.strip() or None
        }

        if file:
            attachment = upload_media(
                supabase, target_id, user_id, file
            )

            payload.update({
                "attachment_path": attachment["path"],
                "attachment_name": attachment["name"],
                "attachment_type": attachment["type"]
            })

        if forwarded_from:
            payload["forwarded_from"] = forwarded_from

        supabase.table(table).insert(payload).execute()

        st.success("Message sent.")
        st.rerun()

    except Exception as error:
        show_error("Could not send your message.", error)


def chat_area(supabase, target_id, user_id, table, target_column):
    st.subheader("💬 Conversation")

    try:
        messages = rows(
            supabase.table(table)
            .select("*")
            .eq(target_column, target_id)
            .order("created_at", desc=False)
            .limit(200)
            .execute()
        )

    except Exception as error:
        show_error("Could not load messages.", error)
        return

    display_messages(
        supabase, messages, user_id, table, target_id
    )

    forward_key = f"forward_message_{target_id}"
    forwarded_from = st.session_state.get(forward_key)

    if forwarded_from:
        st.info("You selected a message to forward.")
        if st.button("Cancel forwarding", key=f"cancel_forward_{target_id}"):
            st.session_state.pop(forward_key, None)
            st.rerun()

    with st.form(f"chat_form_{table}_{target_id}", clear_on_submit=True):
        text = st.text_area("Write a message")

        file = st.file_uploader(
            "Attach image, video, audio or document",
            type=[
                "png", "jpg", "jpeg", "webp",
                "mp4", "mov", "webm",
                "mp3", "wav", "m4a", "ogg",
                "pdf", "doc", "docx",
                "xls", "xlsx", "ppt", "pptx",
                "txt", "csv"
            ],
            key=f"file_{table}_{target_id}",
            max_upload_size=100
        )

        send = st.form_submit_button(
            "Send",
            use_container_width=True
        )

    if send:
        send_chat_message(
            supabase,
            table,
            target_column,
            target_id,
            user_id,
            text,
            file,
            forwarded_from
        )

        if forwarded_from:
            st.session_state.pop(forward_key, None)


# ==========================================================
# PIN MESSAGES
# ==========================================================

def pin_manager(supabase, table, target_column, target_id, admin):
    if not admin:
        return

    with st.expander("📌 Manage pinned messages"):
        try:
            messages = rows(
                supabase.table(table)
                .select("*")
                .eq(target_column, target_id)
                .order("created_at", desc=True)
                .limit(100)
                .execute()
            )

            for message in messages:
                label = (
                    message.get("message_text")
                    or message.get("attachment_name")
                    or "Attachment"
                )

                label = str(label)[:65]

                if message.get("is_pinned"):
                    if st.button(
                        f"Unpin: {label}",
                        key=f"unpin_{table}_{message['id']}"
                    ):
                        supabase.table(table).update({
                            "is_pinned": False,
                            "pinned_by": None,
                            "pinned_at": None
                        }).eq("id", message["id"]).execute()
                        st.rerun()
                else:
                    if st.button(
                        f"Pin: {label}",
                        key=f"pin_{table}_{message['id']}"
                    ):
                        from datetime import datetime, timezone

                        supabase.table(table).update({
                            "is_pinned": True,
                            "pinned_by": st.session_state.get(
                                "user_id"
                            ),
                            "pinned_at": datetime.now(
                                timezone.utc
                            ).isoformat()
                        }).eq("id", message["id"]).execute()
                        st.rerun()

        except Exception as error:
            show_error("Could not manage pinned messages.", error)


# ==========================================================
# CHANNELS
# ==========================================================

def community_channels(supabase, community, user_id, admin):
    community_id = community["id"]

    st.subheader("📢 Community channels")

    try:
        channels = rows(
            supabase.table("community_channels")
            .select("*")
            .eq("community_id", community_id)
            .order("created_at")
            .execute()
        )
    except Exception as error:
        show_error("Could not load channels.", error)
        return

    if admin:
        with st.expander("➕ Create channel"):
            with st.form(f"create_channel_{community_id}"):
                name = st.text_input("Channel name")
                description = st.text_area("Channel description")
                channel_type = st.selectbox(
                    "Channel type",
                    ["announcement", "discussion"]
                )

                create = st.form_submit_button("Create channel")

            if create:
                if not name.strip():
                    st.warning("Enter a channel name.")
                else:
                    try:
                        supabase.table("community_channels").insert({
                            "community_id": community_id,
                            "name": name.strip(),
                            "description": description.strip(),
                            "channel_type": channel_type,
                            "created_by": user_id
                        }).execute()

                        st.success("Channel created.")
                        st.rerun()
                    except Exception as error:
                        show_error("Could not create channel.", error)

    if not channels:
        st.info("No channels have been created yet.")
        return

    for channel in channels:
        with st.expander(
            f"📢 {channel['name']} — {channel.get('channel_type', 'discussion').title()}"
        ):
            st.write(channel.get("description") or "")

            chat_area(
                supabase,
                channel["id"],
                user_id,
                "channel_messages",
                "channel_id"
            )

            pin_manager(
                supabase,
                "channel_messages",
                "channel_id",
                channel["id"],
                admin
            )


# ==========================================================
# COMMUNITY PAGE
# ==========================================================

def community_page(supabase, community, user_id):
    community_id = community["id"]
    admin = str(community.get("created_by")) == str(user_id)

    st.subheader("🌍 " + community["name"])
    st.write(community.get("description") or "")

    if community.get("location"):
        st.caption("📍 " + community["location"])

    tabs = st.tabs([
        "Channels",
        "Groups",
        "Invitation",
        "Members"
    ])

    with tabs[0]:
        community_channels(
            supabase, community, user_id, admin
        )

    with tabs[1]:
        try:
            groups = rows(
                supabase.table("community_groups")
                .select("*")
                .eq("community_id", community_id)
                .execute()
            )

            for group in groups:
                st.markdown(f"**🌱 {group['name']}**")
                st.write(group.get("description") or "")

        except Exception as error:
            show_error("Could not load community groups.", error)

    with tabs[2]:
        if admin:
            create_invitation(
                supabase, "community", community_id, user_id
            )
        else:
            st.info("Community administrators manage invitations.")

    with tabs[3]:
        try:
            members = rows(
                supabase.table("community_memberships")
                .select("*")
                .eq("community_id", community_id)
                .eq("status", "approved")
                .execute()
            )

            profiles = get_profiles(
                supabase,
                [m.get("user_id") for m in members]
            )

            st.caption(f"{len(members)} community members")

            for member in members:
                show_person(
                    supabase,
                    member.get("user_id"),
                    profiles
                )

        except Exception as error:
            show_error("Could not load community members.", error)


# ==========================================================
# GROUP WORKSPACE
# ==========================================================

def group_workspace(supabase, group, user_id, memberships):
    admin = is_admin(group, user_id, memberships)

    tabs = st.tabs([
        "Chat",
        "Members",
        "Group profile",
        "Invitations",
        "Meetings"
    ])

    with tabs[0]:
        chat_area(
            supabase,
            group["id"],
            user_id,
            "group_messages",
            "group_id"
        )

        pin_manager(
            supabase,
            "group_messages",
            "group_id",
            group["id"],
            admin
        )

    with tabs[1]:
        group_members(supabase, group, user_id, admin)

    with tabs[2]:
        group_profile(supabase, group, admin)

    with tabs[3]:
        if admin:
            create_invitation(
                supabase, "group", group["id"], user_id
            )
        else:
            st.info("Group administrators manage invitation links.")

    with tabs[4]:
        st.subheader("📞 Group meetings")

        if admin:
            if st.button(
                "Create voice/video meeting",
                key=f"meeting_{group['id']}"
            ):
                room = (
                    "EcoLoopNode-"
                    + str(group["id"]).replace("-", "")
                    + "-"
                    + uuid.uuid4().hex[:12]
                )

                url = "https://meet.jit.si/" + quote(room)

                try:
                    supabase.table("group_messages").insert({
                        "group_id": group["id"],
                        "sender_id": user_id,
                        "message_text": "📞 Join our group meeting: " + url
                    }).execute()

                    st.success("Meeting invitation shared in chat.")
                    st.link_button("Join meeting", url)

                except Exception as error:
                    show_error("Could not share meeting link.", error)
        else:
            st.info("A group administrator can start a meeting.")


# ==========================================================
# MAIN COMMUNITY HUB
# ==========================================================

def render_community_groups_page(supabase, user_id):

    st.title("🤝 EcoLoop Community Hub")

    st.write(
        "Connect with individuals, schools, organisations "
        "and environmental communities."
    )

    if not supabase:
        st.error("Database connection unavailable.")
        return

    if not user_id:
        st.warning("Please log in first.")
        return

    tabs = st.tabs([
        "🏠 Discover",
        "🌍 Communities",
        "👤 My profile",
        "🔗 Join with code"
    ])

    try:
        community_response = (
            supabase.table("communities")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )

        communities = rows(community_response)

    except Exception as error:
        show_error("Could not load communities.", error)
        communities = []

    try:
        group_response = (
            supabase.table("community_groups")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )

        groups = rows(group_response)

    except Exception as error:
        show_error("Could not load groups.", error)
        groups = []

    try:
        membership_response = (
            supabase.table("group_memberships")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        memberships = rows(membership_response)

    except Exception as error:
        show_error("Could not load your memberships.", error)
        memberships = []

    # DISCOVER
    with tabs[0]:
        create_community(supabase, user_id)
        create_group(supabase, user_id, communities)

        st.divider()
        st.subheader("🌱 Discover groups")

        search = st.text_input(
            "Search groups",
            placeholder="Group name or location"
        )

        for group in groups:
            if search.strip():
                term = search.lower()
                if (
                    term not in str(group.get("name", "")).lower()
                    and term not in str(group.get("location", "")).lower()
                ):
                    continue

            member = is_member(group, user_id, memberships)
            admin = is_admin(group, user_id, memberships)

            with st.container(border=True):
                st.subheader("🌱 " + group.get("name", "Community group"))
                st.write(group.get("description") or "")

                if group.get("location"):
                    st.caption("📍 " + group["location"])

                if member:
                    st.success(
                        "Administrator" if admin else "Group member"
                    )

                    group_workspace(
                        supabase,
                        group,
                        user_id,
                        memberships
                    )

                else:
                    own = next(
                        (
                            m for m in memberships
                            if str(m.get("group_id")) == str(group["id"])
                        ),
                        None
                    )

                    if own and own.get("status") == "pending":
                        st.info("Your join request is pending.")
                    elif own and own.get("status") == "rejected":
                        st.warning("Your previous request was declined.")
                    else:
                        if st.button(
                            "Request to join",
                            key=f"join_group_{group['id']}"
                        ):
                            try:
                                supabase.table("group_memberships").insert({
                                    "group_id": group["id"],
                                    "user_id": user_id,
                                    "status": "pending"
                                }).execute()

                                st.success("Request submitted.")
                                st.rerun()

                            except Exception as error:
                                show_error("Could not request membership.", error)

    # COMMUNITIES
    with tabs[1]:
        st.subheader("🌍 Explore communities")

        community_search = st.text_input(
            "Search communities",
            key="community_search"
        )

        for community in communities:
            if community_search.strip():
                if community_search.lower() not in str(
                    community.get("name", "")
                ).lower():
                    continue

            creator = str(community.get("created_by")) == str(user_id)

            with st.container(border=True):
                st.subheader("🌍 " + community["name"])
                st.write(community.get("description") or "")

                if creator:
                    community_page(supabase, community, user_id)
                else:
                    st.caption("Community")
                    st.info(
                        "Community membership and private access "
                        "will be available after membership approval."
                    )

    # PROFILE
    with tabs[2]:
        profile_editor(supabase, user_id)

    # INVITATION REDEMPTION
    with tabs[3]:
        redeem_invitation(supabase, user_id)

    st.divider()
    st.caption(
        "EcoLoop Node | Powered by Next Gen Impact Hub (NGIH)"
    )
