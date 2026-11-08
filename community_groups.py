
import streamlit as st
import uuid
import html
from datetime import datetime, timedelta, timezone


def render_community_groups_page(*args, **kwargs):
    # =====================================================
    # CONNECTION AND AUTHENTICATION
    # =====================================================
    supabase = args[0] if len(args) >= 1 else kwargs.get("supabase")
    user_id = args[1] if len(args) >= 2 else kwargs.get("user_id")

    if supabase is None:
        supabase = st.session_state.get("supabase_client")

    if supabase is None:
        try:
            from supabase import create_client
            supabase = create_client(
                st.secrets["SUPABASE_URL"],
                st.secrets["SUPABASE_KEY"]
            )
            st.session_state["supabase_client"] = supabase
        except Exception as e:
            st.error(f"Supabase connection failed: {e}")
            return

    uid = user_id or st.session_state.get("uid") or st.session_state.get("user_id")

    if not uid:
        try:
            auth_user = supabase.auth.get_user().user
            if auth_user:
                uid = auth_user.id
        except Exception:
            pass

    if not uid:
        st.warning("Please log in to open the Community Hub.")
        return

    uid = str(uid)
    BUCKET = "community-media"
    MAX_UPLOAD_SIZE = 35 * 1024 * 1024

    # =====================================================
    # DESIGN — PRESERVED
    # =====================================================
    st.markdown("""
    <style>
    .stApp { background-color: #ECE5DD !important; }
    .main { background-color: #ECE5DD !important; }
    [data-testid="stAppViewContainer"] {
        background-color: #ECE5DD !important;
    }
    .wa-header {
        background:#075E54;
        color:white;
        padding:14px 16px;
        border-radius:12px 12px 0 0;
        font-weight:800;
        font-size:20px;
    }
    .wa-sub {
        background:#075E54;
        color:#D9FDD3;
        padding:0 16px 12px 16px;
        font-size:12px;
        border-radius:0 0 12px 12px;
    }
    .wa-panel {
        background:#FFFFFF;
        border-radius:12px;
        padding:10px;
        border:1px solid #d9d9d9;
    }
    .wa-bubble-mine {
        background:#D9FDD3;
        padding:8px 10px;
        border-radius:12px 12px 0 12px;
        margin:6px 0 6px 40px;
        box-shadow:0 1px 1px rgba(0,0,0,0.1);
        overflow-wrap:anywhere;
    }
    .wa-bubble-theirs {
        background:white;
        padding:8px 10px;
        border-radius:12px 12px 12px 0;
        margin:6px 40px 6px 0;
        border:1px solid #eee;
        box-shadow:0 1px 1px rgba(0,0,0,0.1);
        overflow-wrap:anywhere;
    }
    .wa-name {
        font-weight:800;
        font-size:13px;
        color:#075E54;
    }
    .wa-time {
        font-size:11px;
        color:#667781;
        text-align:right;
    }
    .wa-chat-header {
        background:#F0F2F5;
        padding:10px;
        border-radius:8px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="wa-header">♻️ EcoLoop Node Community</div>'
        '<div class="wa-sub">Powered by Next Gen Impact Hub (NGIH) '
        '• Chats & Groups like WhatsApp • No Calls • No Audios</div>',
        unsafe_allow_html=True
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # =====================================================
    # HELPERS
    # =====================================================
    profile_cache = {}

    def safe(value):
        return html.escape(str(value or ""))

    def get_profile(profile_uid):
        if not profile_uid:
            return {}

        profile_uid = str(profile_uid)

        if profile_uid in profile_cache:
            return profile_cache[profile_uid]

        try:
            result = (
                supabase.table("member_profiles")
                .select(
                    "user_id,display_name,username,avatar_url,"
                    "bio,location,interests"
                )
                .eq("user_id", profile_uid)
                .limit(1)
                .execute()
            )
            data = result.data or []
            profile = data[0] if data else {}
            profile_cache[profile_uid] = profile
            return profile
        except Exception:
            return {}

    def get_name(profile):
        username = profile.get("username")
        if username:
            return "@" + str(username)

        return (
            profile.get("display_name")
            or "EcoLoop Member"
        )

    def fmt_time(timestamp):
        if not timestamp:
            return ""

        try:
            dt = datetime.fromisoformat(
                str(timestamp).replace("Z", "+00:00")
            )
            return dt.astimezone().strftime("%H:%M")
        except Exception:
            return ""

    def storage_url(path):
        if not path:
            return ""

        path = str(path)

        # Only allow signed URLs for private storage objects.
        if path.startswith("https://") or path.startswith("http://"):
            return path

        try:
            result = supabase.storage.from_(BUCKET).create_signed_url(
                path, 3600
            )

            if isinstance(result, dict):
                return (
                    result.get("signedURL")
                    or result.get("signedUrl")
                    or ""
                )

            if hasattr(result, "get"):
                return result.get("signedURL") or result.get("signedUrl") or ""

            return ""
        except Exception:
            return ""

    def upload_media(file, folder):
        if file is None:
            return None

        try:
            file_bytes = file.getvalue()

            if len(file_bytes) > MAX_UPLOAD_SIZE:
                st.error("File is too large. Maximum upload size is 35 MB.")
                return None

            allowed = {
                "image/jpeg": "jpg",
                "image/png": "png",
                "image/webp": "webp",
                "video/mp4": "mp4",
                "video/quicktime": "mov"
            }

            content_type = str(file.type or "").lower()

            if content_type not in allowed:
                st.error("Unsupported media format.")
                return None

            extension = allowed[content_type]

            # User-owned folder path supports the private bucket policy.
            path = (
                f"{uid}/{folder}/"
                f"{uuid.uuid4().hex}.{extension}"
            )

            supabase.storage.from_(BUCKET).upload(
                path,
                file_bytes,
                {
                    "content-type": content_type,
                    "upsert": "false"
                }
            )

            return path

        except Exception as e:
            st.error(f"Media upload failed: {e}")
            return None

    def display_media(path, media_type, width=250):
        if not path:
            return

        url = storage_url(path)

        if not url:
            st.caption("Media is currently unavailable.")
            return

        if str(media_type or "").lower().startswith("video"):
            st.video(url)
        else:
            st.image(url, width=width)

    def show_message_bubble(message, sender_id, mine, timestamp):
        profile = get_profile(sender_id)
        bubble = "wa-bubble-mine" if mine else "wa-bubble-theirs"

        name_html = ""
        if not mine:
            name_html = (
                f'<div class="wa-name">{safe(get_name(profile))}</div>'
            )

        message_text = safe(message).replace("\n", "<br>")

        st.markdown(
            f"""
            <div class="{bubble}">
                {name_html}
                <div>{message_text}</div>
                <div class="wa-time">{safe(fmt_time(timestamp))}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    def get_group_memberships(group_id):
        try:
            result = (
                supabase.table("group_memberships")
                .select("*")
                .eq("group_id", group_id)
                .execute()
            )
            return result.data or []
        except Exception:
            return []

    def get_group_membership(group_id):
        try:
            result = (
                supabase.table("group_memberships")
                .select("*")
                .eq("group_id", group_id)
                .eq("user_id", uid)
                .limit(1)
                .execute()
            )
            rows = result.data or []
            return rows[0] if rows else {}
        except Exception:
            return {}

    def get_my_groups():
        groups = {}

        # Approved memberships.
        try:
            result = (
                supabase.table("group_memberships")
                .select("group_id,status")
                .eq("user_id", uid)
                .eq("status", "approved")
                .execute()
            )

            group_ids = [
                str(row["group_id"])
                for row in (result.data or [])
                if row.get("group_id")
            ]

            if group_ids:
                group_result = (
                    supabase.table("community_groups")
                    .select("*")
                    .in_("id", group_ids)
                    .execute()
                )

                for group in group_result.data or []:
                    groups[str(group["id"])] = group

        except Exception as e:
            st.error(f"Could not load group memberships: {e}")

        # The creator must still be able to see their own group.
        try:
            created = (
                supabase.table("community_groups")
                .select("*")
                .eq("created_by", uid)
                .execute()
            )

            for group in created.data or []:
                groups[str(group["id"])] = group

        except Exception:
            pass

        return list(groups.values())

    def get_my_direct_conversations():
        try:
            result = (
                supabase.table("direct_conversations")
                .select("*")
                .or_(
                    f"user_one_id.eq.{uid},user_two_id.eq.{uid}"
                )
                .order("created_at", desc=True)
                .execute()
            )
            return result.data or []
        except Exception as e:
            st.error(f"Could not load private conversations: {e}")
            return []

    def get_other_participant(conversation):
        one = str(conversation.get("user_one_id") or "")
        two = str(conversation.get("user_two_id") or "")
        return two if one == uid else one

    def find_or_create_conversation(other_id):
        other_id = str(other_id)

        try:
            result = (
                supabase.table("direct_conversations")
                .select("*")
                .or_(
                    f"and(user_one_id.eq.{uid},user_two_id.eq.{other_id}),"
                    f"and(user_one_id.eq.{other_id},user_two_id.eq.{uid})"
                )
                .limit(1)
                .execute()
            )

            rows = result.data or []

            if rows:
                return str(rows[0]["id"])

            created = (
                supabase.table("direct_conversations")
                .insert({
                    "user_one_id": uid,
                    "user_two_id": other_id
                })
                .execute()
            )

            if created.data:
                return str(created.data[0]["id"])

            raise Exception("Conversation was not returned by the database.")

        except Exception as e:
            raise Exception(f"Could not open private conversation: {e}")

    # =====================================================
    # LOAD CHATS
    # =====================================================
    my_groups = get_my_groups()
    my_dms = get_my_direct_conversations()

    chats = []

    for group in my_groups:
        chats.append({
            "type": "group",
            "id": str(group.get("id")),
            "name": group.get("name") or "Community Group",
            "code": group.get("invite_code"),
            "desc": group.get("description") or "",
            "created_by": str(group.get("created_by") or "")
        })

    for conversation in my_dms:
        other_id = get_other_participant(conversation)
        profile = get_profile(other_id)

        chats.append({
            "type": "dm",
            "id": str(conversation.get("id")),
            "other_id": other_id,
            "name": get_name(profile),
            "profile": profile
        })

    if "wa_selected" not in st.session_state:
        st.session_state["wa_selected"] = None

    # Validate that an old selected conversation still belongs to this user.
    selected = st.session_state.get("wa_selected")

    if selected:
        if selected.get("type") == "group":
            valid = any(
                str(group.get("id")) == str(selected.get("id"))
                for group in my_groups
            )
            if not valid:
                st.session_state["wa_selected"] = None

        elif selected.get("type") == "dm":
            valid = any(
                str(dm.get("id")) == str(selected.get("id"))
                for dm in my_dms
            )
            if not valid:
                st.session_state["wa_selected"] = None

    # =====================================================
    # MAIN TABS — ORIGINAL DESIGN
    # =====================================================
    t1, t2, t3 = st.tabs([
        "💬 Chats",
        "🟢 Status",
        "➕ New"
    ])

    # =====================================================
    # NEW TAB
    # =====================================================
    with t3:
        st.markdown("### ➕ New Group — like WhatsApp")

        group_name = st.text_input(
            "Group Name",
            key="wa_new_group_name",
            placeholder="e.g. Harare Clean-Up Team"
        )

        group_description = st.text_input(
            "Group Description (optional)",
            key="wa_new_group_desc"
        )

        if st.button(
            "✅ Create Group",
            use_container_width=True
        ):
            if not group_name.strip():
                st.error("Enter a group name.")
            else:
                try:
                    invite_code = uuid.uuid4().hex[:8].upper()

                    created = (
                        supabase.table("community_groups")
                        .insert({
                            "name": group_name.strip(),
                            "description": group_description.strip(),
                            "created_by": uid,
                            "invite_code": invite_code
                        })
                        .execute()
                    )

                    if not created.data:
                        raise Exception("Group creation was not confirmed.")

                    group_id = str(created.data[0]["id"])

                    # Creator membership is inserted as approved admin.
                    supabase.table("group_memberships").insert({
                        "group_id": group_id,
                        "user_id": uid,
                        "membership_role": "admin",
                        "status": "approved"
                    }).execute()

                    st.success(
                        f"Group created! Invite Code: {invite_code}"
                    )
                    st.session_state["wa_selected"] = {
                        "type": "group",
                        "id": group_id,
                        "name": group_name.strip(),
                        "code": invite_code,
                        "desc": group_description.strip(),
                        "created_by": uid
                    }
                    st.rerun()

                except Exception as e:
                    st.error(
                        "Group creation or owner membership failed. "
                        "Please check the database response: "
                        f"{e}"
                    )

        st.divider()

        st.markdown("### 🔗 Join Group via Invite Code")

        invite_input = st.text_input(
            "Paste Invite Code",
            key="wa_join_code"
        )

        if st.button("Join Group"):
            if not invite_input.strip():
                st.warning("Enter an invite code.")
            else:
                try:
                    found = (
                        supabase.table("community_groups")
                        .select("id,name,created_by,invite_code,description")
                        .eq(
                            "invite_code",
                            invite_input.strip().upper()
                        )
                        .limit(1)
                        .execute()
                    )

                    rows = found.data or []

                    if not rows:
                        st.error("Invite code not found.")
                    else:
                        group = rows[0]
                        group_id = str(group["id"])

                        existing = get_group_membership(group_id)

                        if existing:
                            if existing.get("status") == "approved":
                                st.info("You are already a group member.")
                            else:
                                st.info("Your membership request is already pending.")
                        else:
                            supabase.table("group_memberships").insert({
                                "group_id": group_id,
                                "user_id": uid,
                                "membership_role": "member",
                                "status": "pending"
                            }).execute()

                            st.success(
                                f"Membership request sent to "
                                f"{group.get('name')}."
                            )

                        st.rerun()

                except Exception as e:
                    st.error(f"Could not request group membership: {e}")

        st.divider()

        st.markdown("### 👤 New Chat — Search by @username")

        search_new = st.text_input(
            "Search @username",
            key="wa_search_new",
            placeholder="@username"
        )

        if search_new.strip():
            try:
                query = search_new.strip().lstrip("@").replace(",", "")

                found = (
                    supabase.table("member_profiles")
                    .select(
                        "user_id,username,display_name,avatar_url,"
                        "bio,location"
                    )
                    .or_(
                        f"username.ilike.%{query}%,"
                        f"display_name.ilike.%{query}%"
                    )
                    .limit(10)
                    .execute()
                )

                people = found.data or []

                if not people:
                    st.info("No members found.")

                for person in people:
                    person_id = str(person.get("user_id") or "")

                    if not person_id or person_id == uid:
                        continue

                    label = get_name(person)

                    if st.button(
                        f"💬 {label}",
                        key=f"wa_new_dm_{person_id}",
                        use_container_width=True
                    ):
                        try:
                            conversation_id = find_or_create_conversation(
                                person_id
                            )

                            st.session_state["wa_selected"] = {
                                "type": "dm",
                                "id": conversation_id,
                                "other_id": person_id,
                                "name": label
                            }

                            st.rerun()

                        except Exception as e:
                            st.error(str(e))

            except Exception as e:
                st.error(f"Member search failed: {e}")

    # =====================================================
    # STATUS TAB — STORIES
    # =====================================================
    with t2:
        st.markdown("### 🟢 Status — 24 hours")

        status_file = st.file_uploader(
            "Post Status Photo/Video",
            type=["jpg", "jpeg", "png", "mp4", "mov", "webp"],
            key="wa_status_file"
        )

        status_caption = st.text_input(
            "Caption",
            key="wa_status_cap"
        )

        if st.button("Post Status"):
            if status_file is None:
                st.error("Choose a photo or video first.")
            else:
                media_path = upload_media(status_file, "stories")

                if media_path:
                    try:
                        expires = (
                            datetime.now(timezone.utc)
                            + timedelta(hours=24)
                        )

                        supabase.table("stories").insert({
                            "user_id": uid,
                            "media_url": media_path,
                            "media_type": (
                                "video"
                                if str(status_file.type).startswith("video")
                                else "image"
                            ),
                            "caption": status_caption.strip(),
                            "expires_at": expires.isoformat()
                        }).execute()

                        st.success("Status posted!")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Could not publish status: {e}")

        st.divider()

        try:
            story_result = (
                supabase.table("stories")
                .select("*")
                .order("created_at", desc=True)
                .limit(100)
                .execute()
            )
            all_stories = story_result.data or []
        except Exception as e:
            all_stories = []
            st.error(f"Could not load stories: {e}")

        # Group stories by member.
        stories_by_user = {}

        now_utc = datetime.now(timezone.utc)

        for story in all_stories:
            try:
                expiry = datetime.fromisoformat(
                    str(story.get("expires_at")).replace("Z", "+00:00")
                )

                if expiry <= now_utc:
                    continue
            except Exception:
                continue

            story_user = str(story.get("user_id") or "")

            if not story_user:
                continue

            stories_by_user.setdefault(story_user, []).append(story)

        if not stories_by_user:
            st.info("No active statuses yet. Share the first update!")

        for story_user, user_stories in stories_by_user.items():
            profile = get_profile(story_user)

            with st.expander(
                f"🟢 {get_name(profile)}"
            ):
                for story in user_stories:
                    story_id = str(story.get("id"))

                    if story.get("caption"):
                        st.write(story.get("caption"))

                    display_media(
                        story.get("media_url"),
                        story.get("media_type"),
                        width=300
                    )

                    if story_user != uid:
                        # Avoid inserting the same view on every rerun.
                        try:
                            existing_view = (
                                supabase.table("story_views")
                                .select("id")
                                .eq("story_id", story_id)
                                .eq("viewer_id", uid)
                                .limit(1)
                                .execute()
                            )

                            if not existing_view.data:
                                supabase.table("story_views").insert({
                                    "story_id": story_id,
                                    "viewer_id": uid
                                }).execute()

                        except Exception:
                            # Viewing remains available if view tracking fails.
                            pass

                    if story_user == uid:
                        try:
                            view_result = (
                                supabase.table("story_views")
                                .select("id")
                                .eq("story_id", story_id)
                                .execute()
                            )

                            st.caption(
                                f"👁️ Views: {len(view_result.data or [])}"
                            )
                        except Exception:
                            pass

                    st.divider()

    # =====================================================
    # CHATS TAB — ORIGINAL TWO-COLUMN LAYOUT
    # =====================================================
    with t1:
        col_list, col_chat = st.columns([1, 2])

        # -------------------------------------------------
        # LEFT: CHAT LIST
        # -------------------------------------------------
        with col_list:
            st.markdown("**Chats**")

            st.text_input(
                "🔍 Search",
                key="wa_search_chats",
                label_visibility="collapsed",
                placeholder="Search"
            )

            search_query = (
                st.session_state.get("wa_search_chats", "")
                .lower()
                .replace("@", "")
            )

            visible_chats = [
                chat for chat in chats
                if (
                    not search_query
                    or search_query in str(chat.get("name", "")).lower().replace("@", "")
                )
            ]

            if not visible_chats:
                st.info(
                    "No chats yet. Go to ➕ New to create a group or private chat."
                )

            for chat in visible_chats:
                label = (
                    f"👥 {chat.get('name')}"
                    if chat["type"] == "group"
                    else f"👤 {chat.get('name')}"
                )

                if st.button(
                    label,
                    key=f"wa_list_{chat['type']}_{chat['id']}",
                    use_container_width=True
                ):
                    st.session_state["wa_selected"] = chat
                    st.rerun()

        # -------------------------------------------------
        # RIGHT: SELECTED CHAT
        # -------------------------------------------------
        with col_chat:
            selected = st.session_state.get("wa_selected")

            if not selected:
                st.markdown("""
                <div style="
                    background:#F0F2F5;
                    padding:40px;
                    text-align:center;
                    border-radius:12px;
                ">
                    <h3>💬 EcoLoop Node Community</h3>
                    <p>Select a chat on the left<br>
                    or create a new group / DM in ➕ New</p>
                    <p>Send photos, messages, react — like WhatsApp.<br>
                    No calls, no audios.</p>
                </div>
                """, unsafe_allow_html=True)

            # =================================================
            # GROUP CHAT
            # =================================================
            elif selected.get("type") == "group":
                group_id = str(selected.get("id"))

                # Re-fetch group to avoid relying on stale UI data.
                try:
                    group_result = (
                        supabase.table("community_groups")
                        .select("*")
                        .eq("id", group_id)
                        .limit(1)
                        .execute()
                    )

                    group_rows = group_result.data or []

                    if not group_rows:
                        st.warning("This group is no longer available.")
                        st.session_state["wa_selected"] = None
                        st.stop()

                    group = group_rows[0]

                except Exception as e:
                    st.error(f"Could not verify group access: {e}")
                    st.stop()

                membership = get_group_membership(group_id)

                is_creator = str(group.get("created_by")) == uid
                is_approved_member = (
                    membership.get("status") == "approved"
                )

                if not is_creator and not is_approved_member:
                    st.warning(
                        "You are not an approved member of this group."
                    )
                    st.session_state["wa_selected"] = None
                    st.stop()

                st.markdown(
                    f"""
                    <div class="wa-chat-header">
                        <b>👥 {safe(group.get('name'))}</b><br>
                        <span style="font-size:12px;">
                            Invite Code: {safe(group.get('invite_code'))}
                            • Tap ⋮ for Group Info
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # ---------------------------------------------
                # GROUP INFO
                # ---------------------------------------------
                with st.expander(
                    "⋮ Group Info — Members, Add / Remove / Make Admin"
                ):
                    st.write(
                        f"Description: {group.get('description') or ''}"
                    )

                    st.code(
                        str(group.get("invite_code") or ""),
                        language="text"
                    )

                    st.write(
                        "**You are:** "
                        + ("👑 Group Creator" if is_creator else "Member")
                    )

                    if is_creator:
                        st.markdown("**➕ Add Participant — like WhatsApp**")

                        add_query = st.text_input(
                            "Search @username to add",
                            key=f"wa_add_{group_id}",
                            placeholder="@username"
                        )

                        if add_query.strip():
                            try:
                                query = add_query.strip().lstrip("@")

                                found = (
                                    supabase.table("member_profiles")
                                    .select(
                                        "user_id,username,display_name"
                                    )
                                    .or_(
                                        f"username.ilike.%{query}%,"
                                        f"display_name.ilike.%{query}%"
                                    )
                                    .limit(5)
                                    .execute()
                                )

                                for person in found.data or []:
                                    person_id = str(person.get("user_id") or "")

                                    if not person_id or person_id == uid:
                                        continue

                                    if st.button(
                                        f"➕ Add {get_name(person)}",
                                        key=f"wa_add_btn_{group_id}_{person_id}"
                                    ):
                                        try:
                                            existing = (
                                                supabase.table("group_memberships")
                                                .select("id,status")
                                                .eq("group_id", group_id)
                                                .eq("user_id", person_id)
                                                .limit(1)
                                                .execute()
                                            )

                                            if existing.data:
                                                st.info(
                                                    "This person already has a membership record."
                                                )
                                            else:
                                                supabase.table(
                                                    "group_memberships"
                                                ).insert({
                                                    "group_id": group_id,
                                                    "user_id": person_id,
                                                    "membership_role": "member",
                                                    "status": "approved"
                                                }).execute()

                                                st.success(
                                                    f"Added {get_name(person)}."
                                                )
                                                st.rerun()

                                        except Exception as e:
                                            st.error(
                                                f"Could not add participant: {e}"
                                            )

                            except Exception as e:
                                st.error(f"Member search failed: {e}")

                    # Existing RLS only allows creators to list all memberships.
                    if is_creator:
                        members = get_group_memberships(group_id)

                        st.markdown(
                            f"**Participants ({len(members)})**"
                        )

                        for member in members:
                            member_id = str(member.get("user_id") or "")
                            member_profile = get_profile(member_id)

                            role = member.get("membership_role") or "member"
                            status = member.get("status") or "pending"

                            c1, c2, c3 = st.columns([3, 1, 1])

                            with c1:
                                st.write(
                                    f"{get_name(member_profile)} — "
                                    f"{role} — {status}"
                                )

                            if member_id != uid:
                                with c2:
                                    if status == "pending":
                                        if st.button(
                                            "Approve",
                                            key=f"wa_approve_{group_id}_{member_id}"
                                        ):
                                            try:
                                                supabase.table(
                                                    "group_memberships"
                                                ).update({
                                                    "status": "approved"
                                                }).eq(
                                                    "group_id", group_id
                                                ).eq(
                                                    "user_id", member_id
                                                ).execute()

                                                st.success("Membership approved.")
                                                st.rerun()

                                            except Exception as e:
                                                st.error(str(e))

                                    elif role.lower() != "admin":
                                        if st.button(
                                            "Make Admin",
                                            key=f"wa_mkadmin_{group_id}_{member_id}"
                                        ):
                                            try:
                                                supabase.table(
                                                    "group_memberships"
                                                ).update({
                                                    "membership_role": "admin"
                                                }).eq(
                                                    "group_id", group_id
                                                ).eq(
                                                    "user_id", member_id
                                                ).execute()

                                                st.success("Admin role updated.")
                                                st.rerun()

                                            except Exception as e:
                                                st.error(str(e))

                                    else:
                                        if st.button(
                                            "Remove Admin",
                                            key=f"wa_rmadmin_{group_id}_{member_id}"
                                        ):
                                            try:
                                                supabase.table(
                                                    "group_memberships"
                                                ).update({
                                                    "membership_role": "member"
                                                }).eq(
                                                    "group_id", group_id
                                                ).eq(
                                                    "user_id", member_id
                                                ).execute()

                                                st.success("Admin role removed.")
                                                st.rerun()

                                            except Exception as e:
                                                st.error(str(e))

                                with c3:
                                    if st.button(
                                        "Remove",
                                        key=f"wa_rem_{group_id}_{member_id}"
                                    ):
                                        try:
                                            supabase.table(
                                                "group_memberships"
                                            ).delete().eq(
                                                "group_id", group_id
                                            ).eq(
                                                "user_id", member_id
                                            ).execute()

                                            st.success("Member removed.")
                                            st.rerun()

                                        except Exception as e:
                                            st.error(
                                                f"Could not remove member: {e}"
                                            )

                    else:
                        st.caption(
                            "The current database permissions allow the "
                            "group creator to manage the full participant list."
                        )

                    st.divider()

                    if is_creator:
                        st.info(
                            "Group deletion is not enabled by the current "
                            "database permissions. Your group and messages "
                            "will remain intact."
                        )
                    else:
                        st.info(
                            "Leaving a group requires a self-removal "
                            "permission that is not currently enabled."
                        )

                # ---------------------------------------------
                # GROUP MESSAGES
                # ---------------------------------------------
                st.markdown("**Messages**")

                try:
                    message_result = (
                        supabase.table("group_messages")
                        .select("*")
                        .eq("group_id", group_id)
                        .order("created_at")
                        .limit(200)
                        .execute()
                    )

                    group_messages = message_result.data or []

                except Exception as e:
                    group_messages = []
                    st.error(f"Could not load group messages: {e}")

                for message in group_messages:
                    sender_id = str(message.get("sender_id") or "")
                    mine = sender_id == uid

                    show_message_bubble(
                        message.get("message_text"),
                        sender_id,
                        mine,
                        message.get("created_at")
                    )

                    # Message attachments use actual database columns.
                    if message.get("attachment_path"):
                        display_media(
                            message.get("attachment_path"),
                            message.get("attachment_type")
                        )

                    # Support JSONB attachments if present.
                    extra_attachments = message.get("attachments") or []

                    if isinstance(extra_attachments, list):
                        for attachment in extra_attachments:
                            if isinstance(attachment, dict):
                                display_media(
                                    attachment.get("path"),
                                    attachment.get("type")
                                )

                    # Reactions.
                    try:
                        reactions_result = (
                            supabase.table("group_message_reactions")
                            .select("user_id,reaction")
                            .eq("message_id", message.get("id"))
                            .execute()
                        )

                        reactions = reactions_result.data or []

                    except Exception:
                        reactions = []

                    if reactions:
                        counts = {}

                        for reaction in reactions:
                            emoji = reaction.get("reaction") or ""
                            if emoji:
                                counts[emoji] = counts.get(emoji, 0) + 1

                        if counts:
                            st.caption(
                                " ".join(
                                    f"{emoji} {count}"
                                    for emoji, count in counts.items()
                                )
                            )

                    reaction_columns = st.columns(6)

                    for index, emoji in enumerate(
                        ["❤️", "😂", "🔥", "👍", "😮", "😢"]
                    ):
                        with reaction_columns[index]:
                            if st.button(
                                emoji,
                                key=f"wa_greact_{message.get('id')}_{index}"
                            ):
                                try:
                                    # Toggle this user's reaction.
                                    existing = [
                                        item for item in reactions
                                        if str(item.get("user_id")) == uid
                                    ]

                                    if any(
                                        item.get("reaction") == emoji
                                        for item in existing
                                    ):
                                        supabase.table(
                                            "group_message_reactions"
                                        ).delete().eq(
                                            "message_id", message.get("id")
                                        ).eq(
                                            "user_id", uid
                                        ).eq(
                                            "reaction", emoji
                                        ).execute()
                                    else:
                                        supabase.table(
                                            "group_message_reactions"
                                        ).delete().eq(
                                            "message_id", message.get("id")
                                        ).eq(
                                            "user_id", uid
                                        ).execute()

                                        supabase.table(
                                            "group_message_reactions"
                                        ).insert({
                                            "message_id": message.get("id"),
                                            "user_id": uid,
                                            "reaction": emoji
                                        }).execute()

                                    st.rerun()

                                except Exception as e:
                                    st.error(f"Reaction failed: {e}")

                    st.divider()

                # ---------------------------------------------
                # SEND GROUP MESSAGE
                # ---------------------------------------------
                group_message_input = st.text_input(
                    "Message",
                    key=f"wa_gmsg_{group_id}",
                    label_visibility="collapsed",
                    placeholder="Type a message..."
                )

                group_upload = st.file_uploader(
                    "Photo",
                    type=["jpg", "jpeg", "png", "mp4", "mov", "webp"],
                    key=f"wa_gup_{group_id}",
                    label_visibility="collapsed"
                )

                if st.button(
                    "➤ Send",
                    key=f"wa_gsend_{group_id}",
                    use_container_width=True
                ):
                    attachment_path = None
                    attachment_type = None
                    attachment_name = None

                    if group_upload is not None:
                        attachment_path = upload_media(
                            group_upload,
                            "group_chat"
                        )

                        if attachment_path:
                            attachment_type = (
                                "video"
                                if str(group_upload.type).startswith("video")
                                else "image"
                            )
                            attachment_name = group_upload.name

                    if group_message_input.strip() or attachment_path:
                        try:
                            supabase.table("group_messages").insert({
                                "group_id": group_id,
                                "sender_id": uid,
                                "message_text": group_message_input.strip(),
                                "attachment_path": attachment_path,
                                "attachment_name": attachment_name,
                                "attachment_type": attachment_type,
                                "status": "sent"
                            }).execute()

                            st.rerun()

                        except Exception as e:
                            st.error(f"Message could not be sent: {e}")

            # =================================================
            # PRIVATE CHAT
            # =================================================
            elif selected.get("type") == "dm":
                conversation_id = str(selected.get("id"))
                other_id = str(selected.get("other_id") or "")

                # Verify this user is a participant before loading messages.
                try:
                    conversation_result = (
                        supabase.table("direct_conversations")
                        .select("*")
                        .eq("id", conversation_id)
                        .limit(1)
                        .execute()
                    )

                    conversation_rows = conversation_result.data or []

                    if not conversation_rows:
                        st.warning("Private conversation not found.")
                        st.session_state["wa_selected"] = None
                        st.stop()

                    conversation = conversation_rows[0]

                    participants = {
                        str(conversation.get("user_one_id")),
                        str(conversation.get("user_two_id"))
                    }

                    if uid not in participants:
                        st.error("You do not have access to this conversation.")
                        st.stop()

                    other_id = (
                        str(conversation.get("user_two_id"))
                        if str(conversation.get("user_one_id")) == uid
                        else str(conversation.get("user_one_id"))
                    )

                except Exception as e:
                    st.error(f"Could not verify private chat: {e}")
                    st.stop()

                other_profile = get_profile(other_id)

                st.markdown(
                    f"""
                    <div class="wa-chat-header">
                        <b>👤 {safe(get_name(other_profile))}</b><br>
                        <span style="font-size:12px;">
                            Private Conversation
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # ---------------------------------------------
                # LOAD PRIVATE MESSAGES
                # ---------------------------------------------
                try:
                    dm_result = (
                        supabase.table("direct_messages")
                        .select("*")
                        .eq("conversation_id", conversation_id)
                        .order("created_at")
                        .limit(200)
                        .execute()
                    )

                    direct_messages = dm_result.data or []

                except Exception as e:
                    direct_messages = []
                    st.error(f"Could not load private messages: {e}")

                for message in direct_messages:
                    sender_id = str(message.get("sender_id") or "")
                    mine = sender_id == uid

                    show_message_bubble(
                        message.get("message_text"),
                        sender_id,
                        mine,
                        message.get("created_at")
                    )

                    if message.get("attachment_path"):
                        display_media(
                            message.get("attachment_path"),
                            message.get("attachment_type")
                        )

                    if message.get("deleted_at"):
                        st.caption("This message has been deleted.")

                # ---------------------------------------------
                # SEND PRIVATE MESSAGE
                # ---------------------------------------------
                dm_input = st.text_input(
                    "Message",
                    key=f"wa_dm_{conversation_id}",
                    label_visibility="collapsed",
                    placeholder="Type a message..."
                )

                dm_upload = st.file_uploader(
                    "Photo",
                    type=["jpg", "jpeg", "png", "mp4", "mov", "webp"],
                    key=f"wa_dmup_{conversation_id}",
                    label_visibility="collapsed"
                )

                if st.button(
                    "➤ Send",
                    key=f"wa_dmsend_{conversation_id}",
                    use_container_width=True
                ):
                    attachment_path = None
                    attachment_type = None
                    attachment_name = None

                    if dm_upload is not None:
                        attachment_path = upload_media(
                            dm_upload,
                            "dm_chat"
                        )

                        if attachment_path:
                            attachment_type = (
                                "video"
                                if str(dm_upload.type).startswith("video")
                                else "image"
                            )
                            attachment_name = dm_upload.name

                    if dm_input.strip() or attachment_path:
                        try:
                            supabase.table("direct_messages").insert({
                                "conversation_id": conversation_id,
                                "sender_id": uid,
                                "message_text": dm_input.strip(),
                                "attachment_path": attachment_path,
                                "attachment_name": attachment_name,
                                "attachment_type": attachment_type
                            }).execute()

                            st.rerun()

                        except Exception as e:
                            st.error(
                                f"Private message could not be sent: {e}"
                            )
