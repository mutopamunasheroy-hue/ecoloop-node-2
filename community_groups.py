
import streamlit as st
import uuid
import mimetypes
from datetime import datetime, timezone
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


def safe_text(value, default=""):
    return str(value or default).strip()


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


def profile_picture(supabase, profile):
    if not profile:
        return None

    value = profile.get("avatar_url")
    if not value:
        return None

    if str(value).startswith("http"):
        return value

    return media_url(supabase, value)


def format_time(value):
    if not value:
        return ""

    try:
        dt = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

        now = datetime.now(timezone.utc)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        dt = dt.astimezone(timezone.utc)

        if dt.date() == now.date():
            return dt.strftime("%H:%M")

        if dt.year == now.year:
            return dt.strftime("%d %b")

        return dt.strftime("%d %b %Y")

    except Exception:
        return ""


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


def is_member(supabase, group_id, user_id):
    try:
        group = get_group(supabase, group_id)

        if group and str(group.get("created_by")) == str(user_id):
            return True

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
    try:
        group = get_group(supabase, group_id)

        if group and str(group.get("created_by")) == str(user_id):
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
            role = safe_text(
                rows(result)[0].get("membership_role")
            ).lower()

            return role in ADMIN_ROLES

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
                "content-type": uploaded_file.type
                or mimetypes.guess_type(filename)[0]
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

        return (
            result.get("signedURL")
            or result.get("signedUrl")
        )

    except Exception:
        return None


# =========================================================
# PROFILE
# =========================================================

def profile_editor(supabase, user_id):
    st.subheader("My profile")

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
            data = {
                "user_id": user_id,
                "display_name": display_name.strip(),
                "username": username.strip(),
                "bio": bio.strip(),
                "location": location.strip(),
                "interests": interests.strip(),
                "avatar_url": avatar_url.strip(),
                "updated_at": datetime.now(
                    timezone.utc
                ).isoformat()
            }

            try:
                supabase.table(
                    "member_profiles"
                ).upsert(
                    data,
                    on_conflict="user_id"
                ).execute()

                st.success("Your profile has been updated.")
                st.rerun()

            except Exception as e:
                show_error(e, "Could not save profile")


# =========================================================
# COMMUNITIES
# =========================================================

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


def communities_page(supabase, user_id):
    st.subheader("Communities")

    communities = load_communities(supabase)

    if not communities:
        st.info("No communities have been created yet.")
        return

    for community in communities:
        community_id = community.get("id")

        with st.container(border=True):
            st.markdown(
                f"### 🌍 {community.get('name', 'Community')}"
            )

            st.write(
                community.get(
                    "description",
                    "No description available."
                )
            )

            if community.get("location"):
                st.caption(community["location"])

            try:
                group_result = supabase.table(
                    "community_groups"
                ).select("*").eq(
                    "community_id", community_id
                ).order(
                    "created_at", desc=True
                ).execute()

                linked_groups = rows(group_result)

            except Exception:
                linked_groups = []

            st.caption(
                f"{len(linked_groups)} groups in this community"
            )

            if linked_groups:
                for group in linked_groups:
                    st.write(
                        f"👥 **{group.get('name', 'Group')}**"
                    )

                    if is_member(
                        supabase,
                        group["id"],
                        user_id
                    ):
                        if st.button(
                            "Open group",
                            key=f"community_group_{group['id']}"
                        ):
                            st.session_state[
                                "ecoloop_open_group_id"
                            ] = str(group["id"])

                            st.rerun()


# =========================================================
# CREATE GROUP
# =========================================================

def create_group(supabase, user_id):
    communities = load_communities(supabase)

    community_options = {
        "No community": None
    }

    for community in communities:
        community_options[
            community.get("name", "Community")
        ] = community.get("id")

    with st.expander("＋ Create a group"):
        with st.form("ecoloop_create_group"):
            name = st.text_input("Group name")
            description = st.text_area("Group description")
            location = st.text_input("Location")

            selected_community = st.selectbox(
                "Belongs to community",
                list(community_options.keys())
            )

            image = st.file_uploader(
                "Group picture",
                type=["png", "jpg", "jpeg"],
                key="new_group_picture"
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

                community_id = community_options[
                    selected_community
                ]

                if community_id:
                    data["community_id"] = community_id

                try:
                    result = supabase.table(
                        "community_groups"
                    ).insert(data).execute()

                    created = rows(result)

                    if not created:
                        st.error(
                            "The group was not returned by Supabase."
                        )
                        return

                    group_id = created[0]["id"]

                    # The storage path must begin with group_id/user_id.
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
                            }).eq(
                                "id", group_id
                            ).execute()

                    try:
                        supabase.table(
                            "group_memberships"
                        ).insert({
                            "group_id": group_id,
                            "user_id": user_id,
                            "membership_role": "admin",
                            "status": "approved"
                        }).execute()

                    except Exception as membership_error:
                        st.warning(
                            "Group created, but automatic admin "
                            f"membership needs attention: {membership_error}"
                        )

                    st.success("Your group has been created.")

                    st.session_state[
                        "ecoloop_open_group_id"
                    ] = str(group_id)

                    st.rerun()

                except Exception as e:
                    show_error(e, "Group creation failed")


# =========================================================
# MESSAGE DATA
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
        show_error(e, "Could not load messages")
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
        attachment = "📎 " + message["attachment_name"]
        text = f"{text} · {attachment}" if text else attachment

    if not text:
        text = "Sent an attachment"

    if len(text) > 65:
        text = text[:62] + "..."

    return text


def unread_count(messages, group_id, user_id):
    key = f"ecoloop_last_read_{group_id}_{user_id}"
    last_read = st.session_state.get(key)

    if not last_read:
        return 0

    count = 0

    for message in messages:
        if str(message.get("sender_id")) == str(user_id):
            continue

        created = message.get("created_at")

        if created and str(created) > str(last_read):
            count += 1

    return count


# =========================================================
# MY GROUPS CHAT LIST
# =========================================================

def get_my_groups(supabase, user_id):
    try:
        result = supabase.table(
            "community_groups"
        ).select("*").order(
            "created_at", desc=True
        ).execute()

        all_groups = rows(result)

    except Exception as e:
        show_error(e, "Could not load groups")
        return []

    mine = []

    for group in all_groups:
        if is_member(supabase, group["id"], user_id):
            mine.append(group)

    return mine


def my_groups_page(supabase, user_id):
    st.subheader("My Groups")

    groups = get_my_groups(supabase, user_id)

    if not groups:
        st.info(
            "You haven't joined any groups yet. "
            "Explore groups to find your community."
        )
        return

    total_unread = 0

    for group in groups:
        group_id = group["id"]
        latest = get_latest_message(supabase, group_id)

        messages = [latest] if latest else []

        count = unread_count(
            messages,
            group_id,
            user_id
        )

        total_unread += count

    if total_unread:
        st.info(
            f"📩 You have {total_unread} unread messages "
            "across your groups."
        )
    else:
        st.caption("Your group conversations")

    for group in groups:
        group_id = group["id"]
        latest = get_latest_message(supabase, group_id)

        profile = None

        if latest and latest.get("sender_id"):
            profiles = get_profiles(
                supabase,
                [latest["sender_id"]]
            )
            profile = profiles.get(str(latest["sender_id"]))

        picture = media_url(
            supabase,
            group.get("image_url")
        )

        # Session-based unread indicator.
        key = f"ecoloop_last_read_{group_id}_{user_id}"
        last_read = st.session_state.get(key)

        count = 0

        if last_read:
            try:
                recent = supabase.table(
                    "group_messages"
                ).select(
                    "id,sender_id,created_at"
                ).eq(
                    "group_id", group_id
                ).gt(
                    "created_at", last_read
                ).execute()

                count = sum(
                    1 for m in rows(recent)
                    if str(m.get("sender_id")) != str(user_id)
                )

            except Exception:
                count = 0

        with st.container(border=True):
            col1, col2, col3 = st.columns([1, 4, 1])

            with col1:
                if picture:
                    st.image(picture, width=60)
                else:
                    st.markdown("## 👥")

            with col2:
                st.markdown(
                    f"**{group.get('name', 'Group')}**"
                )

                if latest:
                    st.caption(
                        f"{profile_name(profile)}: "
                        f"{message_preview(latest)}"
                    )
                else:
                    st.caption("Start the conversation")

            with col3:
                if latest:
                    st.caption(
                        format_time(latest.get("created_at"))
                    )

                if count:
                    st.success(str(count))

            if st.button(
                "Open chat →",
                key=f"my_group_open_{group_id}",
                use_container_width=True
            ):
                st.session_state[
                    "ecoloop_open_group_id"
                ] = str(group_id)

                st.session_state[key] = datetime.now(
                    timezone.utc
                ).isoformat()

                st.rerun()


# =========================================================
# DISCOVER GROUPS AND SEARCH
# =========================================================

def request_to_join(supabase, group_id, user_id):
    try:
        existing = supabase.table(
            "group_memberships"
        ).select("id,status").eq(
            "group_id", group_id
        ).eq(
            "user_id", user_id
        ).limit(1).execute()

        if rows(existing):
            status = rows(existing)[0].get("status")

            if status == "approved":
                st.info("You are already a member.")
            elif status == "pending":
                st.info("Your request is already pending.")
            else:
                st.info("Your membership already exists.")
            return

        supabase.table(
            "group_memberships"
        ).insert({
            "group_id": group_id,
            "user_id": user_id,
            "membership_role": "member",
            "status": "pending"
        }).execute()

        st.success("Your join request has been submitted.")
        st.rerun()

    except Exception as e:
        show_error(e, "Could not request membership")


def discover_groups_page(supabase, user_id):
    st.subheader("Discover Groups")

    search = st.text_input(
        "🔎 Search groups",
        placeholder="Search by group name, topic or location..."
    )

    communities = load_communities(supabase)

    community_names = ["All communities"] + [
        c.get("name", "Community")
        for c in communities
    ]

    selected_community = st.selectbox(
        "Filter by community",
        community_names
    )

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
        return

    community_lookup = {
        str(c["id"]): c.get("name", "")
        for c in communities
    }

    filtered = []

    for group in groups:
        searchable = " ".join([
            safe_text(group.get("name")),
            safe_text(group.get("description")),
            safe_text(group.get("location")),
            safe_text(
                community_lookup.get(
                    str(group.get("community_id")), ""
                )
            )
        ]).lower()

        if search.lower() not in searchable:
            continue

        if selected_community != "All communities":
            group_community = community_lookup.get(
                str(group.get("community_id")), ""
            )

            if group_community != selected_community:
                continue

        filtered.append(group)

    if not filtered:
        st.info("No matching groups found.")
        return

    for group in filtered:
        group_id = group["id"]

        picture = media_url(
            supabase,
            group.get("image_url")
        )

        latest = get_latest_message(supabase, group_id)

        with st.container(border=True):
            col1, col2 = st.columns([1, 4])

            with col1:
                if picture:
                    st.image(picture, width=75)
                else:
                    st.markdown("## 👥")

            with col2:
                st.markdown(
                    f"**{group.get('name', 'Group')}**"
                )

                st.write(
                    group.get(
                        "description",
                        "No description available."
                    )
                )

                if group.get("location"):
                    st.caption(group["location"])

                if latest:
                    st.caption(
                        "Latest: " + message_preview(latest)
                    )

            if is_member(supabase, group_id, user_id):
                if st.button(
                    "Open group",
                    key=f"discover_open_{group_id}",
                    use_container_width=True
                ):
                    st.session_state[
                        "ecoloop_open_group_id"
                    ] = str(group_id)
                    st.rerun()

            else:
                if st.button(
                    "Request to join",
                    key=f"discover_join_{group_id}",
                    use_container_width=True
                ):
                    request_to_join(
                        supabase,
                        group_id,
                        user_id
                    )


# =========================================================
# GROUP CHAT DISPLAY
# =========================================================

def display_messages(supabase, messages, user_id):
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
        timestamp = format_time(message.get("created_at"))

        mine = sender_id == str(user_id)

        left, right = st.columns([1, 1])

        with (right if mine else left):
            with st.container(border=True):
                if not mine:
                    st.caption(sender)
                else:
                    st.caption("You")

                text = message.get("message_text")

                if text:
                    st.write(text)

                attachment_path = message.get("attachment_path")

                if attachment_path:
                    url = media_url(
                        supabase,
                        attachment_path
                    )

                    name = message.get(
                        "attachment_name"
                    ) or "Attachment"

                    file_type = message.get(
                        "attachment_type"
                    ) or ""

                    if url:
                        if file_type.startswith("image/"):
                            st.image(
                                url,
                                use_container_width=True
                            )

                        elif file_type.startswith("video/"):
                            st.video(url)

                        else:
                            st.markdown(
                                f"[📎 {name}]({url})"
                            )

                if message.get("is_pinned"):
                    st.caption("📌 Pinned message")

                st.caption(timestamp)


def send_chat_message(
    supabase,
    group_id,
    user_id,
    message_text,
    uploaded_file
):
    message_text = safe_text(message_text)

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
            "attachment_type": (
                uploaded_file.type
                or mimetypes.guess_type(
                    uploaded_file.name
                )[0]
                or "application/octet-stream"
            )
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
    st.subheader("Messages")

    if st.button(
        "↻ Refresh messages",
        key=f"refresh_chat_{group_id}"
    ):
        st.rerun()

    messages = get_messages(
        supabase,
        group_id,
        200
    )

    if messages:
        display_messages(
            supabase,
            messages,
            user_id
        )
    else:
        st.info("No messages yet. Start the conversation!")

    st.divider()

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
            "Photo, video or document",
            key=f"chat_upload_{group_id}"
        )

        submitted = st.form_submit_button(
            "Send ➤",
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
                st.session_state[
                    f"ecoloop_last_read_{group_id}_{user_id}"
                ] = datetime.now(
                    timezone.utc
                ).isoformat()

                st.rerun()


# =========================================================
# GROUP MEMBERS AND ADMINISTRATION
# =========================================================

def group_members(supabase, group_id, user_id):
    st.subheader("Members")

    admin = is_admin(
        supabase,
        group_id,
        user_id
    )

    memberships = get_memberships(
        supabase,
        group_id
    )

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
            member_id = str(member.get("user_id"))
            profile = profiles.get(member_id)

            with st.container(border=True):
                st.write(f"**{profile_name(profile)}**")

                if profile and profile.get("username"):
                    st.caption("@" + profile["username"])

                col1, col2 = st.columns(2)

                with col1:
                    if st.button(
                        "Approve",
                        key=f"approve_member_{member['id']}"
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
                        key=f"reject_member_{member['id']}"
                    ):
                        try:
                            supabase.table(
                                "group_memberships"
                            ).delete().eq(
                                "id", member["id"]
                            ).execute()

                            st.rerun()

                        except Exception as e:
                            show_error(e, "Request rejection failed")

    st.markdown("### Group members")

    for member in approved:
        member_id = str(member.get("user_id"))
        profile = profiles.get(member_id)
        role = member.get("membership_role", "member")

        with st.container(border=True):
            col1, col2 = st.columns([1, 4])

            with col1:
                picture = profile_picture(
                    supabase,
                    profile
                )

                if picture:
                    st.image(picture, width=50)
                else:
                    st.markdown("### 👤")

            with col2:
                st.write(f"**{profile_name(profile)}**")
                st.caption(role.title())

            if (
                admin
                and member_id != str(user_id)
                and member_id != str(
                    get_group(supabase, group_id).get("created_by")
                    if get_group(supabase, group_id)
                    else ""
                )
            ):
                if role not in ADMIN_ROLES:
                    if st.button(
                        "Make admin",
                        key=f"make_admin_{member['id']}"
                    ):
                        try:
                            supabase.table(
                                "group_memberships"
                            ).update({
                                "membership_role": "admin"
                            }).eq(
                                "id", member["id"]
                            ).execute()

                            st.success("Admin role assigned.")
                            st.rerun()

                        except Exception as e:
                            show_error(e, "Could not assign admin")

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

    if admin:
        st.divider()
        st.markdown("### Add a member")

        with st.form(f"add_member_{group_id}"):
            new_user_id = st.text_input(
                "Member user ID",
                placeholder="Enter their EcoLoop user ID"
            )

            submitted = st.form_submit_button(
                "Add member"
            )

            if submitted:
                if not new_user_id.strip():
                    st.warning("Enter a user ID.")
                else:
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
# GROUP INFORMATION AND PICTURE
# =========================================================

def group_profile(supabase, group, user_id):
    group_id = group["id"]
    admin = is_admin(
        supabase,
        group_id,
        user_id
    )

    st.subheader("Group information")

    picture = media_url(
        supabase,
        group.get("image_url")
    )

    if picture:
        st.image(picture, width=150)
    else:
        st.markdown("### 👥 No group picture")

    st.markdown(f"## {group.get('name', 'Group')}")

    st.write(
        group.get(
            "description",
            "No group description."
        )
    )

    if group.get("location"):
        st.caption("📍 " + group["location"])

    memberships = get_memberships(
        supabase,
        group_id
    )

    approved = [
        m for m in memberships
        if m.get("status") == "approved"
    ]

    st.caption(f"👥 {len(approved)} members")

    if not admin:
        return

    st.divider()
    st.markdown("### Edit group")

    with st.form(f"edit_group_profile_{group_id}"):
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
            key=f"group_profile_picture_{group_id}"
        )

        submitted = st.form_submit_button(
            "Save group information",
            use_container_width=True
        )

        if submitted:
            data = {
                "name": name.strip(),
                "description": description.strip(),
                "location": location.strip()
            }

            try:
                if image:
                    # Correct folder format:
                    # group_id/user_id/filename
                    path = upload_media(
                        supabase,
                        image,
                        f"{group_id}/{user_id}"
                    )

                    if not path:
                        return

                    data["image_url"] = path

                supabase.table(
                    "community_groups"
                ).update(data).eq(
                    "id", group_id
                ).execute()

                st.success("Group information updated.")
                st.rerun()

            except Exception as e:
                show_error(e, "Could not update group")


# =========================================================
# INVITATIONS
# =========================================================

def group_invitations(supabase, group_id, user_id):
    st.subheader("Group invitations")

    if not is_admin(supabase, group_id, user_id):
        st.info("Only group admins can create invitations.")
        return

    if st.button(
        "＋ Create invitation link",
        key=f"create_invitation_{group_id}",
        use_container_width=True
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
        invite_link = "?invite=" + quote(code)

        st.success("Invitation created.")

        st.markdown("**Share this invitation link:**")
        st.code(invite_link)

        st.link_button(
            "Open invitation",
            invite_link,
            use_container_width=True
        )

        st.caption(
            "Recipients can open the link in EcoLoop and request to join."
        )


def redeem_invitation(supabase, user_id, code=None):
    st.subheader("Join a group")

    if code:
        st.info("Invitation code detected.")
    else:
        code = st.text_input(
            "Invitation code"
        ).strip().upper()

    if st.button(
        "Find invitation",
        use_container_width=True
    ):
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

            invites = rows(result)

            if not invites:
                st.error(
                    "Invitation not found or unavailable."
                )
                return

            invite = invites[0]

            if invite.get("target_type") != "group":
                st.error("This invitation is not for a group.")
                return

            expires = invite.get("expires_at")

            if expires:
                expiry = datetime.fromisoformat(
                    str(expires).replace("Z", "+00:00")
                )

                if expiry.tzinfo is None:
                    expiry = expiry.replace(
                        tzinfo=timezone.utc
                    )

                if expiry < datetime.now(timezone.utc):
                    st.error("This invitation has expired.")
                    return

            max_uses = invite.get("max_uses")
            uses = invite.get("uses") or 0

            if max_uses is not None and uses >= max_uses:
                st.error("This invitation has reached its limit.")
                return

            group_id = invite["target_id"]
            group = get_group(supabase, group_id)

            if not group:
                st.error("The group could not be found.")
                return

            if is_member(supabase, group_id, user_id):
                st.success("You are already a group member.")
                return

            request_to_join(
                supabase,
                group_id,
                user_id
            )

        except Exception as e:
            show_error(
                e,
                "Could not retrieve invitation. "
                "Check invitation table permissions."
            )


# =========================================================
# MEETINGS
# =========================================================

def group_meetings(group_id):
    st.subheader("Group meetings")

    st.write(
        "Create a meeting room for your group."
    )

    if st.button(
        "＋ Create meeting room",
        key=f"create_meeting_{group_id}",
        use_container_width=True
    ):
        room = (
            "EcoLoop-"
            + str(group_id).replace("-", "")[:12]
            + "-"
            + uuid.uuid4().hex[:8]
        )

        url = "https://meet.jit.si/" + quote(room)

        st.session_state[
            f"ecoloop_meeting_{group_id}"
        ] = url

    url = st.session_state.get(
        f"ecoloop_meeting_{group_id}"
    )

    if url:
        st.success("Your meeting room is ready.")

        st.link_button(
            "Join video meeting",
            url,
            use_container_width=True
        )

        st.markdown("**Meeting room**")

        try:
            st.components.v1.iframe(
                url,
                height=520,
                scrolling=False
            )

        except Exception:
            st.info(
                "Your browser may not support the embedded meeting. "
                "Use the Join video meeting link above."
            )


# =========================================================
# GROUP WORKSPACE
# =========================================================

def group_workspace(supabase, group_id, user_id):
    group = get_group(supabase, group_id)

    if not group:
        st.error("This group could not be found.")
        return

    if not is_member(supabase, group_id, user_id):
        st.error(
            "You must be an approved group member to open this chat."
        )
        return

    picture = media_url(
        supabase,
        group.get("image_url")
    )

    back_col, image_col, name_col = st.columns([1, 1, 5])

    with back_col:
        if st.button("←", key=f"group_back_{group_id}"):
            st.session_state[
                "ecoloop_open_group_id"
            ] = None
            st.session_state[
                "ecoloop_group_info_open"
            ] = False
            st.rerun()

    with image_col:
        if picture:
            st.image(picture, width=50)
        else:
            st.markdown("## 👥")

    with name_col:
        if st.button(
            group.get("name", "Group"),
            key=f"group_header_{group_id}"
        ):
            st.session_state[
                "ecoloop_group_info_open"
            ] = not st.session_state.get(
                "ecoloop_group_info_open",
                False
            )
            st.rerun()

        memberships = get_memberships(
            supabase,
            group_id
        )

        member_count = sum(
            1 for m in memberships
            if m.get("status") == "approved"
        )

        st.caption(
            f"{member_count} members · Tap group name for information"
        )

    st.divider()

    if st.session_state.get("ecoloop_group_info_open"):
        info_tab, members_tab, invite_tab, meetings_tab = st.tabs([
            "Group info",
            "Members",
            "Invitations",
            "Meetings"
        ])

        with info_tab:
            group_profile(
                supabase,
                group,
                user_id
            )

        with members_tab:
            group_members(
                supabase,
                group_id,
                user_id
            )

        with invite_tab:
            group_invitations(
                supabase,
                group_id,
                user_id
            )

        with meetings_tab:
            group_meetings(group_id)

    else:
        chat_area(
            supabase,
            group_id,
            user_id
        )

        st.divider()

        if st.button(
            "👥 View group information",
            key=f"view_group_info_{group_id}",
            use_container_width=True
        ):
            st.session_state[
                "ecoloop_group_info_open"
            ] = True
            st.rerun()


# =========================================================
# MAIN COMMUNITY PAGE
# =========================================================

def render_community_groups_page(supabase, user_id):

    if not user_id:
        st.warning("Please sign in to access EcoLoop Community.")
        return

    # Invitation links open the join screen.
    invite_code = st.query_params.get("invite")

    if invite_code:
        st.title("🔗 Group invitation")

        redeem_invitation(
            supabase,
            user_id,
            str(invite_code).upper()
        )

        if st.button("Back to Community"):
            st.query_params.clear()
            st.rerun()

        return

    # Open selected group directly into chat.
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

    # Main home screen.
    st.title("🌍 EcoLoop Community")

    unread_total = 0

    my_groups = get_my_groups(
        supabase,
        user_id
    )

    for group in my_groups:
        group_id = group["id"]
        last_read = st.session_state.get(
            f"ecoloop_last_read_{group_id}_{user_id}"
        )

        if last_read:
            try:
                result = supabase.table(
                    "group_messages"
                ).select(
                    "id,sender_id"
                ).eq(
                    "group_id", group_id
                ).gt(
                    "created_at", last_read
                ).execute()

                unread_total += sum(
                    1 for m in rows(result)
                    if str(m.get("sender_id")) != str(user_id)
                )

            except Exception:
                pass

    if unread_total:
        st.info(
            f"📩 {unread_total} unread messages "
            f"across {len(my_groups)} groups."
        )

    my_groups_tab, discover_tab, communities_tab, profile_tab, join_tab = st.tabs([
        "💬 My Groups",
        "🔎 Discover",
        "🌍 Communities",
        "👤 My Profile",
        "🔗 Join"
    ])

    with my_groups_tab:
        my_groups_page(
            supabase,
            user_id
        )

    with discover_tab:
        discover_groups_page(
            supabase,
            user_id
        )

    with communities_tab:
        create_community(
            supabase,
            user_id
        )

        communities_page(
            supabase,
            user_id
        )

    with profile_tab:
        profile_editor(
            supabase,
            user_id
        )

    with join_tab:
        redeem_invitation(
            supabase,
            user_id
        )
