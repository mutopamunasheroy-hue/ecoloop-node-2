
import streamlit as st
import uuid
import html
from datetime import datetime, timedelta, timezone


def render_community_groups_page(*args, **kwargs):
    supabase = (
        kwargs.get("supabase")
        or (args[0] if args else st.session_state.get("supabase_client"))
    )

    if not supabase:
        st.error("Supabase connection is unavailable.")
        return

    try:
        auth_user = supabase.auth.get_user().user
        uid = str(auth_user.id) if auth_user else None
    except Exception:
        uid = None

    if not uid:
        uid = (
            kwargs.get("user_id")
            or st.session_state.get("uid")
            or st.session_state.get("user_id")
        )

    if not uid:
        st.warning("Please log in to access Community.")
        return

    BUCKET = "community-media"
    NAV_OPTIONS = ["EcoLoop Connect", "Stories"]

    defaults = {
        "eco_new_nav": "EcoLoop Connect",
        "eco_new_chat_id": None,
        "eco_new_chat_user": None,
        "eco_new_profile": None,
        "eco_new_notice": None,
        "eco_new_story_user": None,
        "eco_new_delete_chat": None,
        "eco_new_delete_story": None,
        "eco_new_story_upload_version": 0,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if st.session_state["eco_new_nav"] not in NAV_OPTIONS:
        st.session_state["eco_new_nav"] = "EcoLoop Connect"

    st.markdown("""
    <style>
    .block-container {
        max-width: 720px !important;
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
    }
    .community-heading {
        background: linear-gradient(120deg, #075E54, #087F70);
        color: white;
        padding: 23px;
        border-radius: 18px;
        margin: 10px 0 18px 0;
    }
    .community-heading h1 {
        color: white !important;
        font-size: 29px;
        margin: 0;
        font-weight: 750;
    }
    .community-heading p {
        color: #D9FDD3;
        margin: 5px 0 0 0;
        font-size: 14px;
    }
    .section-heading {
        font-size: 23px;
        font-weight: 750;
        margin: 4px 0 2px 0;
    }
    .section-subtitle {
        color: #75818a;
        font-size: 13px;
        margin-bottom: 15px;
    }
    .message-mine {
        background: #D9FDD3;
        color: #173b2c;
        padding: 11px 13px;
        border-radius: 14px 14px 3px 14px;
        margin: 8px 0 8px 38px;
        overflow-wrap: anywhere;
    }
    .message-other {
        background: #f0f2f3;
        color: #17212b;
        padding: 11px 13px;
        border-radius: 14px 14px 14px 3px;
        margin: 8px 38px 8px 0;
        overflow-wrap: anywhere;
    }
    .message-time {
        color: #667781;
        font-size: 10px;
        text-align: right;
        margin-top: 5px;
    }
    .story-caption {
        padding: 10px 12px;
        border-radius: 10px;
        background: rgba(128,128,128,.10);
        margin: 8px 0;
    }
    div.stButton > button {
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

    # --------------------------------------------------
    # HELPERS
    # --------------------------------------------------

    def esc(value):
        return html.escape(str(value or ""), quote=True)

    def get_profile(user_id):
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
            return result.data[0] if result.data else {}
        except Exception:
            return {}

    def display_name(profile):
        username = (profile.get("username") or "").strip()
        if username:
            return "@" + username
        return profile.get("display_name") or "Community member"

    def storage_url(path):
        if not path:
            return ""
        if str(path).startswith("http"):
            return str(path)
        try:
            result = supabase.storage.from_(BUCKET).create_signed_url(
                str(path), 3600
            )
            if isinstance(result, dict):
                return result.get("signedURL") or result.get("signedUrl") or ""
        except Exception:
            try:
                return supabase.storage.from_(BUCKET).get_public_url(str(path))
            except Exception:
                return ""
        return ""

    def upload_media(file, folder):
        if file is None:
            return None

        try:
            # Confirm the authenticated Supabase user before uploading.
            current_user = supabase.auth.get_user().user
            authenticated_uid = str(current_user.id) if current_user else None

            if not authenticated_uid or authenticated_uid != str(uid):
                st.error(
                    "Your login session could not be verified. "
                    "Please sign out and sign in again."
                )
                return None

            extension = (
                file.name.rsplit(".", 1)[-1].lower()
                if "." in file.name else "jpg"
            )

            # Every upload goes inside the authenticated user's own folder.
            path = (
                f"{authenticated_uid}/{folder}/"
                f"{uuid.uuid4().hex}.{extension}"
            )

            content_type = file.type or "application/octet-stream"

            result = supabase.storage.from_(BUCKET).upload(
                path,
                file.getvalue(),
                {
                    "content-type": content_type,
                    "upsert": "false",
                },
            )

            return path

        except Exception as error:
            st.error(f"Upload failed: {error}")
            return None

    def show_avatar(profile, width=55):
        url = storage_url(profile.get("avatar_url"))
        if url:
            try:
                st.image(url, width=width)
                return
            except Exception:
                pass
        name = display_name(profile).replace("@", "")
        st.markdown(f"**{name[:2].upper() or 'U'}**")

    def format_time(value):
        try:
            return datetime.fromisoformat(
                str(value).replace("Z", "+00:00")
            ).astimezone().strftime("%d %b · %H:%M")
        except Exception:
            return ""

    def search_members(query, limit=25):
        query = (query or "").strip().replace("@", "")
        if not query:
            return []
        try:
            result = (
                supabase.table("member_profiles")
                .select("*")
                .ilike("username", f"%{query}%")
                .limit(limit)
                .execute()
            )
            profiles = result.data or []
            profiles.sort(
                key=lambda p: (
                    not (p.get("username") or "").lower().startswith(
                        query.lower()
                    ),
                    (p.get("username") or "").lower(),
                )
            )
            return profiles
        except Exception:
            return []

    # --------------------------------------------------
    # CHAT HELPERS
    # --------------------------------------------------

    def get_other_user(conversation):
        if str(conversation.get("user_one_id")) == str(uid):
            return conversation.get("user_two_id")
        return conversation.get("user_one_id")

    def get_conversation(other_user_id):
        existing = (
            supabase.table("direct_conversations")
            .select("*")
            .or_(
                f"and(user_one_id.eq.{uid},user_two_id.eq.{other_user_id}),"
                f"and(user_one_id.eq.{other_user_id},user_two_id.eq.{uid})"
            )
            .execute()
            .data or []
        )

        if existing:
            existing.sort(
                key=lambda item: item.get("created_at") or "",
                reverse=True,
            )
            return existing[0]["id"]

        created = (
            supabase.table("direct_conversations")
            .insert({
                "user_one_id": uid,
                "user_two_id": other_user_id,
            })
            .execute()
        )
        return created.data[0]["id"]

    def open_chat(other_user_id):
        if not other_user_id or str(other_user_id) == str(uid):
            return
        try:
            conversation_id = get_conversation(other_user_id)

            (
                supabase.table("hidden_conversations")
                .delete()
                .eq("user_id", uid)
                .eq("conversation_id", conversation_id)
                .execute()
            )

            st.session_state["eco_new_chat_id"] = conversation_id
            st.session_state["eco_new_chat_user"] = other_user_id
            st.session_state["eco_new_profile"] = None
            st.rerun()

        except Exception as error:
            st.error(f"Could not open chat: {error}")

    def get_hidden_conversation_ids():
        result = (
            supabase.table("hidden_conversations")
            .select("conversation_id")
            .eq("user_id", uid)
            .execute()
        )
        return {
            str(row.get("conversation_id"))
            for row in (result.data or [])
        }

    def hide_conversation(other_user_id):
        conversations = (
            supabase.table("direct_conversations")
            .select("id,user_one_id,user_two_id")
            .or_(
                f"and(user_one_id.eq.{uid},user_two_id.eq.{other_user_id}),"
                f"and(user_one_id.eq.{other_user_id},user_two_id.eq.{uid})"
            )
            .execute()
            .data or []
        )

        for conversation in conversations:
            existing = (
                supabase.table("hidden_conversations")
                .select("id")
                .eq("user_id", uid)
                .eq("conversation_id", conversation["id"])
                .execute()
                .data or []
            )
            if not existing:
                (
                    supabase.table("hidden_conversations")
                    .insert({
                        "user_id": uid,
                        "conversation_id": conversation["id"],
                    })
                    .execute()
                )

    # --------------------------------------------------
    # HEADER
    # --------------------------------------------------

    st.button(
        "← Back to Dashboard",
        key="eco_new_back_dashboard",
        on_click=lambda: st.session_state.update({
            kwargs.get("dashboard_state_key", "page"):
                kwargs.get("dashboard_page", "Dashboard"),
            "eco_new_chat_id": None,
            "eco_new_chat_user": None,
            "eco_new_profile": None,
        }),
    )

    st.markdown("""
    <div class="community-heading">
        <h1>Community</h1>
        <p>Connect. Communicate. Share.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.get("eco_new_notice"):
        st.success(st.session_state["eco_new_notice"])
        st.session_state["eco_new_notice"] = None

    # --------------------------------------------------
    # PROFILE SCREEN
    # --------------------------------------------------

    profile_target = st.session_state.get("eco_new_profile")

    if profile_target:
        profile = get_profile(profile_target)

        st.button(
            "← Back",
            key="eco_new_profile_back",
            on_click=lambda: st.session_state.update({
                "eco_new_profile": None
            }),
        )

        st.divider()
        col1, col2 = st.columns([1, 3])

        with col1:
            show_avatar(profile, 100)

        with col2:
            st.subheader(display_name(profile))
            st.caption(profile.get("display_name") or "Community member")

        st.divider()
        st.markdown("### About")
        st.write(
            profile.get("bio")
            or "No About information has been added yet."
        )

        if profile.get("location"):
            st.write(f"📍 Location: {profile['location']}")
        if profile.get("country_of_origin"):
            st.write(f"🌍 Country: {profile['country_of_origin']}")
        if profile.get("interests"):
            st.write(f"✨ Interests: {profile['interests']}")

        social_fields = {
            "Instagram": "instagram_handle",
            "Facebook": "facebook_handle",
            "TikTok": "tiktok_handle",
            "LinkedIn": "linkedin_handle",
        }

        for label, column in social_fields.items():
            if profile.get(column):
                st.write(f"**{label}:** {profile[column]}")

        if str(profile_target) != str(uid):
            st.divider()
            if st.button(
                "💬 Message",
                key="eco_new_profile_message",
                use_container_width=True,
            ):
                open_chat(profile_target)

        else:
            st.caption("This is your profile.")
            st.divider()
            st.markdown("### Edit your profile")

            avatar_file = st.file_uploader(
                "Upload profile picture",
                type=["jpg", "jpeg", "png", "webp"],
                key="eco_new_avatar_upload",
            )

            display_name_input = st.text_input(
                "Display name",
                value=profile.get("display_name") or "",
                key="eco_new_display_name",
            )

            bio_input = st.text_area(
                "About",
                value=profile.get("bio") or "",
                key="eco_new_bio",
            )

            location_input = st.text_input(
                "Location",
                value=profile.get("location") or "",
                key="eco_new_location",
            )

            interests_input = st.text_input(
                "Interests",
                value=profile.get("interests") or "",
                key="eco_new_interests",
            )

            if st.button("Save Profile", key="eco_new_save_profile"):
                update_data = {
                    "display_name": display_name_input.strip(),
                    "bio": bio_input.strip(),
                    "location": location_input.strip(),
                    "interests": interests_input.strip(),
                }

                if avatar_file:
                    avatar_path = upload_media(avatar_file, "avatars")
                    if not avatar_path:
                        st.error(
                            "Profile was not saved because the picture "
                            "could not be uploaded."
                        )
                        return
                    update_data["avatar_url"] = avatar_path

                try:
                    (
                        supabase.table("member_profiles")
                        .update(update_data)
                        .eq("user_id", uid)
                        .execute()
                    )
                    st.session_state["eco_new_notice"] = "Profile updated."
                    st.rerun()
                except Exception as error:
                    st.error(f"Could not update profile: {error}")

        return

    # --------------------------------------------------
    # OPEN CHAT SCREEN
    # --------------------------------------------------

    selected_chat = st.session_state.get("eco_new_chat_id")

    if selected_chat:
        other_id = st.session_state.get("eco_new_chat_user")
        other_profile = get_profile(other_id)

        st.button(
            "← EcoLoop Connect",
            key="eco_new_chat_back",
            on_click=lambda: st.session_state.update({
                "eco_new_chat_id": None,
                "eco_new_chat_user": None,
                "eco_new_delete_chat": None,
            }),
        )

        col1, col2 = st.columns([1, 4])

        with col1:
            show_avatar(other_profile, 55)

        with col2:
            st.markdown(f"**{esc(display_name(other_profile))}**")
            if st.button("View Profile", key="eco_new_chat_view_profile"):
                st.session_state["eco_new_profile"] = other_id
                st.rerun()

        st.divider()

        if st.button("🗑️ Delete Chat", key="eco_new_delete_chat_button"):
            st.session_state["eco_new_delete_chat"] = selected_chat
            st.rerun()

        if st.session_state.get("eco_new_delete_chat") == selected_chat:
            st.warning(
                "This hides the chat from your account only. "
                "The other person keeps their conversation."
            )

            yes_col, no_col = st.columns(2)

            with yes_col:
                if st.button(
                    "Confirm Delete",
                    key="eco_new_confirm_delete_chat",
                    type="primary",
                    use_container_width=True,
                ):
                    try:
                        hide_conversation(other_id)
                        st.session_state["eco_new_chat_id"] = None
                        st.session_state["eco_new_chat_user"] = None
                        st.session_state["eco_new_delete_chat"] = None
                        st.session_state["eco_new_notice"] = (
                            "Chat removed from your list."
                        )
                        st.rerun()
                    except Exception as error:
                        st.error(f"Could not delete chat: {error}")

            with no_col:
                if st.button(
                    "Cancel",
                    key="eco_new_cancel_delete_chat",
                    use_container_width=True,
                ):
                    st.session_state["eco_new_delete_chat"] = None
                    st.rerun()

        try:
            messages = (
                supabase.table("direct_messages")
                .select("*")
                .eq("conversation_id", selected_chat)
                .order("created_at")
                .execute()
                .data or []
            )
        except Exception as error:
            messages = []
            st.error(f"Could not load messages: {error}")

        for message in messages:
            mine = str(message.get("sender_id")) == str(uid)
            css_class = "message-mine" if mine else "message-other"

            st.markdown(
                f'<div class="{css_class}">'
                f'{esc(message.get("message_text") or "")}'
                f'<div class="message-time">'
                f'{format_time(message.get("created_at"))}'
                f'</div></div>',
                unsafe_allow_html=True,
            )

            attachment = message.get("attachment_path")
            if attachment:
                media_url = storage_url(attachment)
                if media_url:
                    try:
                        if str(
                            message.get("attachment_type") or ""
                        ).startswith("video"):
                            st.video(media_url)
                        else:
                            st.image(media_url, width=280)
                    except Exception:
                        st.caption("Attachment unavailable.")

        st.divider()
        st.markdown("### Send a message")

        version_state_key = f"eco_new_compose_version_{selected_chat}"
        if version_state_key not in st.session_state:
            st.session_state[version_state_key] = 0

        compose_version = st.session_state[version_state_key]

        message_key = (
            f"eco_new_message_{selected_chat}_{compose_version}"
        )
        attachment_key = (
            f"eco_new_attachment_{selected_chat}_{compose_version}"
        )

        message_text = st.text_area(
            "Message",
            key=message_key,
            placeholder="Write a message...",
            label_visibility="collapsed",
            height=90,
        )

        attachment_file = st.file_uploader(
            "Attach a picture or video",
            type=["jpg", "jpeg", "png", "webp", "mp4", "mov"],
            key=attachment_key,
        )

        if st.button(
            "➤ Send",
            key=f"eco_new_send_{selected_chat}_{compose_version}",
            use_container_width=True,
        ):
            text_to_send = (message_text or "").strip()
            attachment_path = None

            if attachment_file:
                attachment_path = upload_media(
                    attachment_file, "direct-messages"
                )

            if not text_to_send and not attachment_path:
                st.warning("Write a message or attach a file.")

            elif attachment_file and not attachment_path and not text_to_send:
                st.error("The attachment could not be uploaded.")

            else:
                try:
                    supabase.table("direct_messages").insert({
                        "conversation_id": selected_chat,
                        "sender_id": uid,
                        "message_text": text_to_send,
                        "attachment_path": attachment_path,
                        "attachment_type": (
                            attachment_file.type
                            if attachment_path and attachment_file
                            else None
                        ),
                        "attachment_name": (
                            attachment_file.name
                            if attachment_path and attachment_file
                            else None
                        ),
                    }).execute()

                    st.session_state[version_state_key] = (
                        compose_version + 1
                    )
                    st.rerun()

                except Exception as error:
                    st.error(f"Message could not be sent: {error}")

        return

    # --------------------------------------------------
    # MAIN NAVIGATION
    # --------------------------------------------------

    selected_nav = st.radio(
        "Community sections",
        NAV_OPTIONS,
        horizontal=True,
        key="eco_new_nav",
        label_visibility="collapsed",
    )

    st.divider()

    # --------------------------------------------------
    # ECOLOOP CONNECT
    # --------------------------------------------------

    if selected_nav == "EcoLoop Connect":
        st.markdown(
            '<div class="section-heading">EcoLoop Connect</div>'
            '<div class="section-subtitle">'
            'Your private space to connect with the EcoLoop community.'
            '</div>',
            unsafe_allow_html=True,
        )

        # MY PROFILE IS NOW AT THE TOP.
        my_profile = get_profile(uid)

        profile_col1, profile_col2, profile_col3 = st.columns([1, 3, 2])

        with profile_col1:
            show_avatar(my_profile, 48)

        with profile_col2:
            st.write("**My Profile**")
            st.caption("View and edit your profile")

        with profile_col3:
            if st.button(
                "View Profile",
                key="eco_new_my_profile_top",
                use_container_width=True,
            ):
                st.session_state["eco_new_profile"] = uid
                st.rerun()

        st.divider()

        st.markdown("### Find People")

        search = st.text_input(
            "Find people",
            placeholder="Search by username...",
            key="eco_new_member_search",
        )

        if search.strip():
            results = search_members(search)

            if not results:
                st.info("No matching members found.")

            for profile in results:
                member_id = profile.get("user_id")

                if str(member_id) == str(uid):
                    continue

                col1, col2, col3 = st.columns([1, 3, 2])

                with col1:
                    show_avatar(profile, 45)

                with col2:
                    st.write(f"**{display_name(profile)}**")
                    st.caption(
                        profile.get("display_name") or "Community member"
                    )

                with col3:
                    if st.button(
                        "Profile",
                        key=f"eco_new_search_profile_{member_id}",
                    ):
                        st.session_state["eco_new_profile"] = member_id
                        st.rerun()

                    if st.button(
                        "Message",
                        key=f"eco_new_search_message_{member_id}",
                    ):
                        open_chat(member_id)

                st.divider()

        st.markdown("### Recent Conversations")

        try:
            conversations = (
                supabase.table("direct_conversations")
                .select("*")
                .or_(f"user_one_id.eq.{uid},user_two_id.eq.{uid}")
                .execute()
                .data or []
            )
            hidden_ids = get_hidden_conversation_ids()

        except Exception as error:
            conversations = []
            hidden_ids = set()
            st.error(f"Could not load conversations: {error}")

        grouped = {}

        for conversation in conversations:
            conversation_id = str(conversation.get("id"))

            if conversation_id in hidden_ids:
                continue

            other_id = get_other_user(conversation)

            if not other_id:
                continue

            try:
                latest = (
                    supabase.table("direct_messages")
                    .select("message_text,created_at,attachment_path")
                    .eq("conversation_id", conversation.get("id"))
                    .order("created_at", desc=True)
                    .limit(1)
                    .execute()
                    .data or []
                )
            except Exception:
                latest = []

            last_message = latest[0] if latest else {}

            activity = (
                last_message.get("created_at")
                or conversation.get("created_at")
                or ""
            )

            item = {
                "id": conversation.get("id"),
                "other_id": other_id,
                "profile": get_profile(other_id),
                "preview": (
                    last_message.get("message_text")
                    or (
                        "📎 Attachment"
                        if last_message.get("attachment_path")
                        else "Start a conversation"
                    )
                ),
                "activity": activity,
            }

            key = str(other_id)
            previous = grouped.get(key)

            if previous is None or activity > previous["activity"]:
                grouped[key] = item

        chat_items = list(grouped.values())
        chat_items.sort(
            key=lambda item: item["activity"],
            reverse=True,
        )

        if not chat_items:
            st.info(
                "Your conversations will appear here. "
                "Search for a username above to start connecting."
            )

        for item in chat_items:
            col1, col2, col3 = st.columns([1, 3, 2])

            with col1:
                show_avatar(item["profile"], 50)

            with col2:
                st.write(f"**{display_name(item['profile'])}**")
                st.caption(str(item["preview"])[:65])

            with col3:
                if st.button(
                    "Open",
                    key=f"eco_new_open_{item['id']}",
                    use_container_width=True,
                ):
                    st.session_state["eco_new_chat_id"] = item["id"]
                    st.session_state["eco_new_chat_user"] = item["other_id"]
                    st.rerun()

                if st.button(
                    "Delete",
                    key=f"eco_new_hide_{item['id']}",
                    use_container_width=True,
                ):
                    st.session_state["eco_new_delete_chat"] = item["id"]
                    st.session_state["eco_new_delete_chat_user"] = (
                        item["other_id"]
                    )
                    st.rerun()

            if st.session_state.get("eco_new_delete_chat") == item["id"]:
                st.warning(
                    f"Hide your conversation with "
                    f"{display_name(item['profile'])}?"
                )

                yes_col, no_col = st.columns(2)

                with yes_col:
                    if st.button(
                        "Confirm",
                        key=f"eco_new_confirm_list_delete_{item['id']}",
                        type="primary",
                        use_container_width=True,
                    ):
                        try:
                            hide_conversation(item["other_id"])
                            st.session_state["eco_new_delete_chat"] = None
                            st.session_state["eco_new_notice"] = (
                                "Chat removed from your list."
                            )
                            st.rerun()
                        except Exception as error:
                            st.error(f"Could not hide chat: {error}")

                with no_col:
                    if st.button(
                        "Cancel",
                        key=f"eco_new_cancel_list_delete_{item['id']}",
                        use_container_width=True,
                    ):
                        st.session_state["eco_new_delete_chat"] = None
                        st.rerun()

            st.divider()

    # --------------------------------------------------
    # STORIES
    # --------------------------------------------------

    elif selected_nav == "Stories":
        st.markdown(
            '<div class="section-heading">Stories</div>'
            '<div class="section-subtitle">'
            'Share moments with the community. Stories disappear after 24 hours.'
            '</div>',
            unsafe_allow_html=True,
        )

        story_version = st.session_state.get(
            "eco_new_story_upload_version", 0
        )

        with st.expander("＋ Share a Story", expanded=False):
            story_file = st.file_uploader(
                "Choose a photo or video",
                type=["jpg", "jpeg", "png", "webp", "mp4", "mov"],
                key=f"eco_new_story_upload_{story_version}",
            )

            story_caption = st.text_input(
                "Add a caption",
                key=f"eco_new_story_caption_{story_version}",
            )

            if st.button(
                "Post Story",
                key=f"eco_new_post_story_{story_version}",
                use_container_width=True,
            ):
                if not story_file:
                    st.warning("Choose a photo or video first.")
                else:
                    media_path = upload_media(story_file, "stories")

                    if media_path:
                        try:
                            supabase.table("stories").insert({
                                "user_id": uid,
                                "media_url": media_path,
                                "media_type": (
                                    "video"
                                    if story_file.type.startswith("video")
                                    else "image"
                                ),
                                "caption": story_caption.strip(),
                                "expires_at": (
                                    datetime.now(timezone.utc)
                                    + timedelta(hours=24)
                                ).isoformat(),
                            }).execute()

                            st.session_state[
                                "eco_new_story_upload_version"
                            ] = story_version + 1

                            st.session_state["eco_new_notice"] = (
                                "Your Story has been posted."
                            )
                            st.rerun()

                        except Exception as error:
                            st.error(f"Could not post Story: {error}")

        try:
            stories = (
                supabase.table("stories")
                .select("*")
                .order("created_at", desc=True)
                .limit(100)
                .execute()
                .data or []
            )
        except Exception as error:
            stories = []
            st.error(f"Could not load Stories: {error}")

        now = datetime.now(timezone.utc)
        active_stories = []

        for story in stories:
            try:
                expiry = datetime.fromisoformat(
                    str(story.get("expires_at")).replace("Z", "+00:00")
                )
                if expiry >= now:
                    active_stories.append(story)
            except Exception:
                continue

        story_users = []

        for story in active_stories:
            owner = str(story.get("user_id"))
            if owner not in story_users:
                story_users.append(owner)

        if not story_users:
            st.info("No active Stories yet. Share the first one!")

        for story_owner in story_users:
            profile = get_profile(story_owner)
            owner_stories = [
                story for story in active_stories
                if str(story.get("user_id")) == story_owner
            ]

            col1, col2, col3 = st.columns([1, 3, 2])

            with col1:
                show_avatar(profile, 50)

            with col2:
                st.write(f"**{display_name(profile)}**")
                st.caption(
                    f"{len(owner_stories)} active Story/Stories"
                )

            with col3:
                if st.button(
                    "View",
                    key=f"eco_new_view_stories_{story_owner}",
                    use_container_width=True,
                ):
                    st.session_state["eco_new_story_user"] = story_owner
                    st.rerun()

            st.divider()

        story_user = st.session_state.get("eco_new_story_user")

        if story_user:
            st.markdown("### Story viewer")

            if st.button(
                "← Back to Stories",
                key="eco_new_close_stories",
            ):
                st.session_state["eco_new_story_user"] = None
                st.rerun()

            story_profile = get_profile(story_user)
            st.write(f"**{display_name(story_profile)}**")

            selected_stories = [
                story for story in active_stories
                if str(story.get("user_id")) == str(story_user)
            ]

            if not selected_stories:
                st.info(
                    "This user's active Stories have expired or been deleted."
                )

            for story in selected_stories:
                story_id = story.get("id")
                is_owner = str(story_user) == str(uid)

                if story.get("caption"):
                    st.markdown(
                        f'<div class="story-caption">'
                        f'{esc(story.get("caption"))}</div>',
                        unsafe_allow_html=True,
                    )

                media_url = storage_url(story.get("media_url"))

                if media_url:
                    try:
                        if story.get("media_type") == "video":
                            st.video(media_url)
                        else:
                            st.image(media_url, use_container_width=True)
                    except Exception:
                        st.caption("Story media could not be displayed.")

                st.caption(
                    f"Posted {format_time(story.get('created_at'))}"
                )

                if not is_owner:
                    try:
                        already_viewed = (
                            supabase.table("story_views")
                            .select("id")
                            .eq("story_id", story_id)
                            .eq("viewer_id", uid)
                            .execute()
                            .data or []
                        )

                        if not already_viewed:
                            supabase.table("story_views").insert({
                                "story_id": story_id,
                                "viewer_id": uid,
                            }).execute()
                    except Exception:
                        pass

                if is_owner:
                    try:
                        views = (
                            supabase.table("story_views")
                            .select("viewer_id")
                            .eq("story_id", story_id)
                            .execute()
                            .data or []
                        )

                        viewer_ids = list(dict.fromkeys(
                            row.get("viewer_id")
                            for row in views
                            if row.get("viewer_id")
                        ))

                        with st.expander(
                            f"👁️ Viewed by {len(viewer_ids)} people"
                        ):
                            if not viewer_ids:
                                st.caption("No views yet.")

                            for viewer_id in viewer_ids:
                                viewer_profile = get_profile(viewer_id)
                                st.write(display_name(viewer_profile))

                    except Exception as error:
                        st.caption(f"Could not load viewers: {error}")

                    if st.button(
                        "🗑️ Delete this Story",
                        key=f"eco_new_delete_story_{story_id}",
                    ):
                        st.session_state["eco_new_delete_story"] = story_id
                        st.rerun()

                    if (
                        st.session_state.get("eco_new_delete_story")
                        == story_id
                    ):
                        st.warning(
                            "Are you sure you want to delete this Story?"
                        )

                        yes_col, no_col = st.columns(2)

                        with yes_col:
                            if st.button(
                                "Confirm Delete",
                                key=f"eco_new_confirm_story_{story_id}",
                                type="primary",
                                use_container_width=True,
                            ):
                                try:
                                    (
                                        supabase.table("stories")
                                        .delete()
                                        .eq("id", story_id)
                                        .eq("user_id", uid)
                                        .execute()
                                    )

                                    st.session_state[
                                        "eco_new_delete_story"
                                    ] = None
                                    st.session_state["eco_new_notice"] = (
                                        "Your Story has been deleted."
                                    )
                                    st.rerun()

                                except Exception as error:
                                    st.error(
                                        f"Could not delete Story: {error}"
                                    )

                        with no_col:
                            if st.button(
                                "Cancel",
                                key=f"eco_new_cancel_story_{story_id}",
                                use_container_width=True,
                            ):
                                st.session_state[
                                    "eco_new_delete_story"
                                ] = None
                                st.rerun()

                else:
                    st.markdown("#### Reply privately")

                    reply_version_key = (
                        f"eco_new_story_reply_version_{story_id}"
                    )
                    if reply_version_key not in st.session_state:
                        st.session_state[reply_version_key] = 0

                    reply_version = st.session_state[reply_version_key]

                    reply_text = st.text_input(
                        "Your reply",
                        placeholder="Send a private reply...",
                        key=f"eco_new_story_reply_{story_id}_{reply_version}",
                        label_visibility="collapsed",
                    )

                    if st.button(
                        "Send Reply",
                        key=f"eco_new_send_story_reply_{story_id}_{reply_version}",
                        use_container_width=True,
                    ):
                        if not reply_text.strip():
                            st.warning("Write a reply first.")
                        else:
                            try:
                                conversation_id = get_conversation(story_user)

                                (
                                    supabase.table("hidden_conversations")
                                    .delete()
                                    .eq("user_id", uid)
                                    .eq("conversation_id", conversation_id)
                                    .execute()
                                )

                                story_reference = (
                                    story.get("caption")
                                    or "A photo or video Story"
                                )

                                private_message = (
                                    f"↩️ Story reply: {story_reference}\n\n"
                                    f"{reply_text.strip()}"
                                )

                                supabase.table("direct_messages").insert({
                                    "conversation_id": conversation_id,
                                    "sender_id": uid,
                                    "message_text": private_message,
                                    "attachment_path": None,
                                    "attachment_type": None,
                                    "attachment_name": None,
                                }).execute()

                                st.session_state[reply_version_key] = (
                                    reply_version + 1
                                )
                                st.session_state["eco_new_chat_id"] = (
                                    conversation_id
                                )
                                st.session_state["eco_new_chat_user"] = (
                                    story_user
                                )
                                st.session_state["eco_new_story_user"] = None
                                st.session_state["eco_new_notice"] = (
                                    "Your private Story reply has been sent."
                                )
                                st.rerun()

                            except Exception as error:
                                st.error(
                                    f"Could not send Story reply: {error}"
                                )

                st.divider()
