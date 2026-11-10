import streamlit as st
import uuid
import html
from datetime import datetime, timedelta, timezone


def render_community_groups_page(*args, **kwargs):
    supabase = (
        kwargs.get("supabase")
        or (args[0] if len(args) >= 1 else st.session_state.get("supabase_client"))
    )
    uid = (
        kwargs.get("user_id")
        or (args[1] if len(args) >= 2 else None)
        or st.session_state.get("uid")
        or st.session_state.get("user_id")
    )

    if not uid:
        try:
            u = supabase.auth.get_user().user
            if u:
                uid = u.id
        except Exception:
            pass

    if not uid:
        st.warning("Login first to open Community.")
        return

    BUCKET = "community-media"

    # ---------- STATE ----------
    defaults = {
        "eco_nav": "Chats",
        "eco_sel": None,
        "eco_sel_type": None,
        "eco_room_info": None,
        "eco_profile_view": None,
        "eco_notice": None,
        "eco_last_created": None,
        "eco_last_seen": {},
        "eco_reply_to": None,
        "eco_forward": None,
        "eco_show_new": False,
        "eco_msg_opt": None,
        "eco_story_user": None,
        "eco_show_create_room": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # ---------- STYLE ----------
    st.markdown("""
    <style>
    .stApp, [data-testid="stAppViewContainer"] {
        background:#ECE5DD !important;
    }
    .block-container {
        max-width:520px !important;
        padding:0 0 92px 0 !important;
    }
    header { visibility:hidden; }

    .wa-head {
        background:#075E54;
        color:white;
        padding:15px 16px;
    }
    .wa-head h1 {
        font-size:21px;
        margin:0;
        font-weight:800;
        letter-spacing:.2px;
        color:white !important;
    }
    .wa-head p {
        font-size:12px;
        margin:3px 0 0 0;
        color:#D9FDD3;
    }
    .card {
        background:white;
        padding:14px;
        border-radius:14px;
        margin:10px;
        border:1px solid #e9e9e9;
    }
    .bubble-mine {
        background:#D9FDD3;
        padding:9px 11px;
        border-radius:14px 14px 0 14px;
        margin:6px 0 6px 52px;
    }
    .bubble-theirs {
        background:white;
        padding:9px 11px;
        border-radius:14px 14px 14px 0;
        margin:6px 52px 6px 0;
        border:1px solid #eee;
    }
    .name {
        font-weight:800;
        font-size:13px;
        color:#075E54;
    }
    .time {
        font-size:11px;
        color:#667781;
        text-align:right;
    }
    .pending-box {
        background:#FFF3CD;
        padding:10px;
        border-radius:10px;
        border:1px solid #FFC107;
        margin:10px;
    }
    .notice-box {
        background:#D1E7DD;
        padding:10px;
        border-radius:10px;
        border:1px solid #198754;
        margin:10px;
    }
    .reply-box {
        background:#F0F2F5;
        padding:8px 10px;
        border-radius:10px;
        margin:10px;
        border-left:4px solid #075E54;
        font-size:13px;
    }
    .inbox-wrap div[data-testid="stButton"] > button {
        background:white !important;
        border:none !important;
        border-bottom:1px solid #f0f0f0 !important;
        border-radius:0 !important;
        text-align:left !important;
        padding:13px 12px !important;
        box-shadow:none !important;
        color:#111 !important;
        width:100% !important;
        min-height:64px;
    }
    .inbox-wrap div[data-testid="stButton"] > button:hover {
        background:#F7F7F7 !important;
    }
    .bottom-bar {
        position:fixed;
        bottom:0;
        left:50%;
        transform:translateX(-50%);
        width:100%;
        max-width:520px;
        background:white;
        border-top:1px solid #e0e0e0;
        z-index:99;
        padding-bottom:6px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ---------- HELPERS ----------
    def esc(value):
        return html.escape(str(value if value is not None else ""), quote=True)

    def is_admin(role):
        return str(role or "").strip().lower() == "admin"

    def is_approved(status):
        return str(status or "").strip().lower() == "approved"

    def fmt_time(ts):
        try:
            return datetime.fromisoformat(
                str(ts).replace("Z", "+00:00")
            ).strftime("%H:%M")
        except Exception:
            return ""

    def get_profile(user_id):
        if not user_id:
            return {}
        try:
            result = (
                supabase.table("member_profiles")
                .select("*")
                .eq("user_id", user_id)
                .single()
                .execute()
            )
            return result.data or {}
        except Exception:
            return {}

    def get_name(profile):
        username = (profile.get("username") or "").strip()
        return f"@{username}" if username else (
            profile.get("display_name") or "User"
        )

    def show_social_handles(profile):
        fields = {
            "Instagram": "instagram_handle",
            "Facebook": "facebook_handle",
            "TikTok": "tiktok_handle",
            "LinkedIn": "linkedin_handle",
        }
        for label, column in fields.items():
            value = profile.get(column)
            if value:
                st.write(f"**{label}:** {esc(value)}")

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
            return str(result)
        except Exception:
            try:
                return supabase.storage.from_(BUCKET).get_public_url(str(path))
            except Exception:
                return ""

    def upload(file, folder):
        try:
            ext = (
                str(file.name).split(".")[-1].lower()
                if "." in str(file.name)
                else "jpg"
            )
            path = f"{uid}/{folder}/{uuid.uuid4().hex[:12]}.{ext}"
            supabase.storage.from_(BUCKET).upload(
                path,
                file.getvalue(),
                {"content-type": file.type},
            )
            return path
        except Exception as error:
            st.error(f"Upload failed: {error}")
            return None

    # FIX: avatar_url may be a storage path, not a full URL.
    # st.image() treats non-http strings as local files -> FileNotFoundError.
    def avatar_src(profile):
        """Return a usable image URL for a profile's avatar, or ''."""
        raw = (profile or {}).get("avatar_url")
        if not raw:
            return ""
        return storage_url(raw)

    def show_avatar(profile, width=110):
        """Safely render an avatar. Returns True if shown, else False."""
        src = avatar_src(profile)
        if not src:
            return False
        try:
            st.image(src, width=width)
            return True
        except Exception:
            return False

    def search_by_username(query, limit=20):
        query = (query or "").strip().replace("@", "").strip()
        if not query:
            return []

        try:
            results = (
                supabase.table("member_profiles")
                .select("*")
                .ilike("username", f"%{query}%")
                .limit(limit)
                .execute()
                .data or []
            )
        except Exception:
            return []

        query_lower = query.lower()
        starts = [
            row for row in results
            if (row.get("username") or "").lower().startswith(query_lower)
        ]
        others = [row for row in results if row not in starts]

        starts.sort(key=lambda row: (row.get("username") or "").lower())
        others.sort(key=lambda row: (row.get("username") or "").lower())

        return starts + others

    def get_app_url():
        try:
            headers = st.context.headers
            host = headers.get("host") or ""
            return f"https://{host}" if host else None
        except Exception:
            return None

    def open_dm(other_id):
        try:
            existing = (
                supabase.table("direct_conversations")
                .select("*")
                .or_(
                    f"and(user_one_id.eq.{uid},user_two_id.eq.{other_id}),"
                    f"and(user_one_id.eq.{other_id},user_two_id.eq.{uid})"
                )
                .execute()
                .data or []
            )

            if existing:
                conversation_id = existing[0].get("id")
            else:
                created = (
                    supabase.table("direct_conversations")
                    .insert({
                        "user_one_id": uid,
                        "user_two_id": other_id,
                    })
                    .execute()
                )
                conversation_id = created.data[0].get("id")

            st.session_state["eco_sel"] = conversation_id
            st.session_state["eco_sel_type"] = "dm"
            st.session_state["eco_nav"] = "Chats"
            st.session_state["eco_msg_opt"] = None
            st.rerun()

        except Exception as error:
            st.error(f"Could not start chat: {error}")

    def go(nav):
        st.session_state["eco_nav"] = nav
        st.session_state["eco_sel"] = None
        st.session_state["eco_room_info"] = None
        st.session_state["eco_profile_view"] = None
        st.session_state["eco_msg_opt"] = None
        st.session_state["eco_story_user"] = None
        st.rerun()

    def reply_preview(message, messages):
        reply_id = message.get("reply_to_id")
        if not reply_id:
            return None

        original = next(
            (item for item in messages if str(item.get("id")) == str(reply_id)),
            None,
        )
        if not original:
            return "Original message unavailable"

        original_text = original.get("message_text") or "Attachment"
        return original_text[:100]

    # ---------- HEADER ----------
    st.markdown(
        '<div class="wa-head">'
        '<h1>EcoLoop Community Hub</h1>'
        '<p>Next Gen Impact Hub (NGIH) • Community</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.get("eco_notice"):
        st.markdown(
            f'<div class="notice-box">{esc(st.session_state["eco_notice"])}</div>',
            unsafe_allow_html=True,
        )
        if st.button("Dismiss", key="dismiss_n"):
            st.session_state["eco_notice"] = None
            st.rerun()

    # ---------- LOAD DATA ----------
    try:
        memberships = (
            supabase.table("group_memberships")
            .select("group_id,membership_role,status")
            .eq("user_id", uid)
            .execute()
            .data or []
        )

        group_ids = [item.get("group_id") for item in memberships]

        my_rooms = (
            supabase.table("community_groups")
            .select("*")
            .in_("id", group_ids)
            .execute()
            .data or []
        ) if group_ids else []

        membership_map = {
            item.get("group_id"): item for item in memberships
        }

    except Exception:
        my_rooms = []
        membership_map = {}

    try:
        my_dms = (
            supabase.table("direct_conversations")
            .select("*")
            .or_(f"user_one_id.eq.{uid},user_two_id.eq.{uid}")
            .execute()
            .data or []
        )
    except Exception:
        my_dms = []

    def enrich_dm(conversation):
        other_id = (
            conversation.get("user_two_id")
            if str(conversation.get("user_one_id")) == str(uid)
            else conversation.get("user_one_id")
        )

        profile = get_profile(other_id)
        last_text = ""
        last_at = ""
        last_sender = ""

        try:
            latest = (
                supabase.table("direct_messages")
                .select("message_text,created_at,sender_id,attachment_path")
                .eq("conversation_id", conversation.get("id"))
                .order("created_at", desc=True)
                .limit(1)
                .execute()
                .data or []
            )

            if latest:
                item = latest[0]
                last_text = item.get("message_text") or (
                    "📷 Attachment" if item.get("attachment_path") else ""
                )
                last_at = item.get("created_at") or ""
                last_sender = str(item.get("sender_id") or "")

        except Exception:
            pass

        return {
            "type": "dm",
            "id": conversation.get("id"),
            "other_id": other_id,
            "name": get_name(profile),
            "profile": profile,
            "last_text": last_text,
            "last_at": last_at,
            "last_sender": last_sender,
        }

    def enrich_room(group):
        membership = membership_map.get(group.get("id"), {})
        last_text = ""
        last_at = ""
        last_sender = ""

        try:
            latest = (
                supabase.table("group_messages")
                .select("message_text,created_at,sender_id,attachment_path")
                .eq("group_id", group.get("id"))
                .order("created_at", desc=True)
                .limit(1)
                .execute()
                .data or []
            )

            if latest:
                item = latest[0]
                last_text = item.get("message_text") or (
                    "📷 Attachment" if item.get("attachment_path") else ""
                )
                last_at = item.get("created_at") or ""
                last_sender = str(item.get("sender_id") or "")

        except Exception:
            pass

        return {
            "type": "room",
            "id": group.get("id"),
            "name": group.get("name"),
            "desc": group.get("description"),
            "code": group.get("invite_code"),
            "created_by": group.get("created_by"),
            "my_role": membership.get("membership_role"),
            "my_status": membership.get("status"),
            "last_text": last_text,
            "last_at": last_at,
            "last_sender": last_sender,
        }

    dm_list = sorted(
        [enrich_dm(item) for item in my_dms],
        key=lambda item: item.get("last_at") or "",
        reverse=True,
    )

    room_list = sorted(
        [enrich_room(item) for item in my_rooms],
        key=lambda item: item.get("last_at") or "",
        reverse=True,
    )

    dm_list = list({str(item["id"]): item for item in dm_list}.values())
    room_list = list({str(item["id"]): item for item in room_list}.values())

    def is_unread(conversation):
        key = f"{conversation['type']}_{conversation['id']}"
        seen = st.session_state["eco_last_seen"].get(key, "")

        return bool(
            conversation.get("last_at")
            and conversation.get("last_sender")
            and str(conversation.get("last_sender")) != str(uid)
            and str(conversation.get("last_at")) > str(seen)
        )

    def mark_read(conversation):
        if conversation.get("last_at"):
            key = f"{conversation['type']}_{conversation['id']}"
            st.session_state["eco_last_seen"][key] = conversation.get("last_at")

    def inbox_label(conversation):
        unread = "  ●" if is_unread(conversation) else ""
        time_label = (
            fmt_time(conversation.get("last_at"))
            if conversation.get("last_at")
            else ""
        )
        preview = (conversation.get("last_text") or "No messages yet")[:42]

        suffix = (
            " • pending"
            if conversation["type"] == "room"
            and str(conversation.get("my_status") or "").lower() == "pending"
            else ""
        )

        return (
            f"{conversation.get('name')}{suffix}   {time_label}{unread}\n"
            f"{preview}"
        )

    # ---------- INVITATION LINK ----------
    try:
        query_params = st.query_params
        room_code = query_params.get("room", None)
        if isinstance(room_code, list):
            room_code = room_code[0] if room_code else None
    except Exception:
        room_code = None

    if room_code and not st.session_state.get("eco_sel"):
        clean_code = str(room_code).strip().upper()
        st.info(f"Invitation for Chat Room code: {esc(clean_code)}")

        try:
            result = (
                supabase.table("community_groups")
                .select("*")
                .eq("invite_code", clean_code)
                .single()
                .execute()
            )

            if result.data:
                invited_room = result.data

                st.write(
                    f"**{esc(invited_room.get('name'))}** — "
                    f"{esc(invited_room.get('description') or '')}"
                )

                existing = (
                    supabase.table("group_memberships")
                    .select("*")
                    .eq("group_id", invited_room.get("id"))
                    .eq("user_id", uid)
                    .execute()
                    .data or []
                )

                if existing:
                    status = str(existing[0].get("status") or "").lower()
                    st.write(f"Status: **{esc(status)}**")

                    if status == "approved":
                        if st.button("Open This Chat Room", key="open_invited"):
                            st.session_state["eco_sel"] = invited_room.get("id")
                            st.session_state["eco_sel_type"] = "room"
                            st.rerun()

                    elif status == "pending":
                        st.warning("Pending approval — you cannot send yet.")

                else:
                    if st.button("Request to Join", key="join_invited"):
                        supabase.table("group_memberships").insert({
                            "group_id": invited_room.get("id"),
                            "user_id": uid,
                            "membership_role": "member",
                            "status": "pending",
                        }).execute()

                        st.session_state["eco_notice"] = (
                            "Join request sent — pending approval"
                        )
                        st.rerun()

            else:
                st.error("Invitation code not found.")

        except Exception as error:
            st.error(f"Could not load invitation: {error}")

    # ---------- PROFILE VIEW ----------
    if st.session_state.get("eco_profile_view"):
        profile_id = st.session_state["eco_profile_view"]
        profile = get_profile(profile_id)

        if st.button("⬅ Back", key="back_profile"):
            st.session_state["eco_profile_view"] = None
            st.rerun()

        st.markdown(
            '<div class="card" style="text-align:center;">',
            unsafe_allow_html=True,
        )

        # FIX: resolve storage path to a real URL
        show_avatar(profile, 110)

        st.markdown(f"### {esc(get_name(profile))}", unsafe_allow_html=True)
        st.write(f"**{esc(profile.get('display_name') or '')}**")
        st.write(esc(profile.get("bio") or "No bio yet"))
        st.write(
            f"📍 {esc(profile.get('location') or '—')} • "
            f"{esc(profile.get('country_of_origin') or '')}"
        )

        if profile.get("interests"):
            st.write(f"✨ Interests: {esc(profile.get('interests'))}")

        show_social_handles(profile)

        st.markdown("</div>", unsafe_allow_html=True)

        if str(profile_id) != str(uid):
            if st.button(
                "💬 Message",
                use_container_width=True,
                key="msg_profile_btn",
            ):
                open_dm(profile_id)
        else:
            st.caption("This is your profile.")

    # ---------- ROOM INFO ----------
    elif st.session_state.get("eco_room_info"):
        room = st.session_state["eco_room_info"]

        if st.button("⬅ Back to Chat", key="back_roominfo"):
            st.session_state["eco_room_info"] = None
            st.rerun()

        st.markdown(
            f'<div class="card"><h3>👥 {esc(room.get("name"))}</h3>'
            f'<p style="color:#667781;">{esc(room.get("desc") or "")}</p></div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="card">Invite Code: <b>{esc(room.get("code") or "")}</b>'
            '<br><span style="font-size:12px;color:#667781;">'
            'Share the code or link below</span></div>',
            unsafe_allow_html=True,
        )

        app_url = get_app_url()
        if app_url and room.get("code"):
            st.code(f"{app_url}/?room={room.get('code')}")

        is_creator = str(room.get("created_by")) == str(uid)

        try:
            me = (
                supabase.table("group_memberships")
                .select("*")
                .eq("group_id", room["id"])
                .eq("user_id", uid)
                .single()
                .execute()
                .data or {}
            )
        except Exception:
            me = {}

        st.write(
            f"You are: **{'👑 Creator' if is_creator else me.get('membership_role', 'Member')}** "
            f"— {me.get('status', '')}"
        )

        if is_creator:
            try:
                pending = (
                    supabase.table("group_memberships")
                    .select("*")
                    .eq("group_id", room["id"])
                    .eq("status", "pending")
                    .execute()
                    .data or []
                )
            except Exception:
                pending = []

            if pending:
                st.markdown(
                    '<div class="pending-box"><b>⏳ Pending Requests — Creator approval</b></div>',
                    unsafe_allow_html=True,
                )

                for member in pending:
                    member_profile = get_profile(member.get("user_id"))
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.write(esc(get_name(member_profile)))

                    with col2:
                        if st.button(
                            "Approve",
                            key=f"ap_{room['id']}_{member.get('user_id')}",
                        ):
                            supabase.table("group_memberships").update(
                                {"status": "approved"}
                            ).eq("group_id", room["id"]).eq(
                                "user_id", member.get("user_id")
                            ).execute()

                            st.session_state["eco_notice"] = (
                                f"Approved {get_name(member_profile)}"
                            )
                            st.rerun()

                    with col3:
                        if st.button(
                            "Reject",
                            key=f"rj_{room['id']}_{member.get('user_id')}",
                        ):
                            supabase.table("group_memberships").delete().eq(
                                "group_id", room["id"]
                            ).eq("user_id", member.get("user_id")).execute()

                            st.session_state["eco_notice"] = "Rejected"
                            st.rerun()

        try:
            members = (
                supabase.table("group_memberships")
                .select("*")
                .eq("group_id", room["id"])
                .execute()
                .data or []
            )
        except Exception:
            members = []

        st.write(f"**Members ({len(members)})**")

        members.sort(
            key=lambda item: (
                str(item.get("status") or "").lower() != "approved"
            )
        )

        for member in members:
            member_profile = get_profile(member.get("user_id"))
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                if st.button(
                    f"{get_name(member_profile)} — "
                    f"{member.get('membership_role')} — "
                    f"{member.get('status')}",
                    key=f"mem_{room['id']}_{member.get('user_id')}",
                ):
                    st.session_state["eco_profile_view"] = member.get("user_id")
                    st.rerun()

            if (
                is_creator
                and str(member.get("user_id")) != str(uid)
                and is_approved(member.get("status"))
            ):
                with col2:
                    if not is_admin(member.get("membership_role")):
                        if st.button(
                            "Make Admin",
                            key=f"mk_{room['id']}_{member.get('user_id')}",
                        ):
                            supabase.table("group_memberships").update(
                                {"membership_role": "admin"}
                            ).eq("group_id", room["id"]).eq(
                                "user_id", member.get("user_id")
                            ).execute()
                            st.rerun()
                    else:
                        if st.button(
                            "Remove Admin",
                            key=f"rmad_{room['id']}_{member.get('user_id')}",
                        ):
                            supabase.table("group_memberships").update(
                                {"membership_role": "member"}
                            ).eq("group_id", room["id"]).eq(
                                "user_id", member.get("user_id")
                            ).execute()
                            st.rerun()

                with col3:
                    if st.button(
                        "Remove",
                        key=f"rem_{room['id']}_{member.get('user_id')}",
                    ):
                        supabase.table("group_memberships").delete().eq(
                            "group_id", room["id"]
                        ).eq("user_id", member.get("user_id")).execute()
                        st.rerun()

        st.divider()

        if not is_creator:
            if st.button(
                "🚪 Exit Chat Room",
                use_container_width=True,
                key=f"exit_{room['id']}",
            ):
                try:
                    supabase.table("group_memberships").delete().eq(
                        "group_id", room["id"]
                    ).eq("user_id", uid).execute()

                    st.session_state["eco_room_info"] = None
                    st.session_state["eco_sel"] = None
                    st.session_state["eco_notice"] = (
                        "You exited the Chat Room."
                    )
                    st.rerun()

                except Exception as error:
                    st.error(f"Exit failed: {error}")
        else:
            st.caption("Creator cannot exit — would orphan the room.")

    # ---------- CONVERSATION ----------
    elif st.session_state.get("eco_sel"):
        selected_id = st.session_state["eco_sel"]
        selected_type = st.session_state["eco_sel_type"]

        selected = next(
            (
                item for item in (
                    dm_list if selected_type == "dm" else room_list
                )
                if str(item["id"]) == str(selected_id)
            ),
            None,
        )

        if not selected:
            st.error("Chat not found.")
            if st.button("Back", key="conv_notfound"):
                st.session_state["eco_sel"] = None
                st.rerun()

        else:
            mark_read(selected)

            if selected_type == "room":
                col1, col2 = st.columns([1, 5])

                with col1:
                    if st.button("⬅", key="conv_back_room"):
                        st.session_state["eco_sel"] = None
                        st.session_state["eco_msg_opt"] = None
                        st.rerun()

                with col2:
                    st.markdown(
                        f"**👥 {esc(selected.get('name'))}** • "
                        f"{esc(selected.get('my_status') or '')}",
                        unsafe_allow_html=True,
                    )

                    if st.button("ℹ️ Room Info", key="room_info_open"):
                        st.session_state["eco_room_info"] = selected
                        st.rerun()

            else:
                col1, col2 = st.columns([1, 5])

                with col1:
                    if st.button("⬅", key="conv_back_dm"):
                        st.session_state["eco_sel"] = None
                        st.session_state["eco_msg_opt"] = None
                        st.rerun()

                with col2:
                    st.markdown(
                        f"**👤 {esc(selected.get('name'))}**",
                        unsafe_allow_html=True,
                    )

                    if st.button("👤 View Profile", key="dm_profile_open"):
                        st.session_state["eco_profile_view"] = selected.get(
                            "other_id"
                        )
                        st.rerun()

            if (
                selected_type == "room"
                and not is_approved(selected.get("my_status"))
            ):
                st.warning(
                    "Pending approval — only approved members can send. "
                    f"Status: {esc(selected.get('my_status'))}"
                )

            # Load messages
            if selected_type == "room":
                try:
                    messages = (
                        supabase.table("group_messages")
                        .select("*")
                        .eq("group_id", selected_id)
                        .order("created_at")
                        .execute()
                        .data or []
                    )
                except Exception:
                    messages = []
            else:
                try:
                    messages = (
                        supabase.table("direct_messages")
                        .select("*")
                        .eq("conversation_id", selected_id)
                        .order("created_at")
                        .execute()
                        .data or []
                    )
                except Exception:
                    messages = []

            # Persistent pinned messages for Chat Rooms
            if selected_type == "room":
                pinned_messages = [
                    item for item in messages
                    if item.get("is_pinned")
                ]

                for pinned_message in pinned_messages:
                    st.markdown(
                        '<div class="notice-box">📌 '
                        f'{esc(pinned_message.get("message_text") or "Pinned attachment")}'
                        '</div>',
                        unsafe_allow_html=True,
                    )

            if st.session_state.get("eco_forward"):
                st.info(
                    "Forwarding ready — open Chats or Chat Rooms "
                    "and choose a destination."
                )

            # Cache profiles for this render pass (avoids one query per message)
            profile_cache = {}

            def cached_profile(user_id):
                key = str(user_id)
                if key not in profile_cache:
                    profile_cache[key] = get_profile(user_id)
                return profile_cache[key]

            # Render messages
            for message in messages:
                profile = cached_profile(message.get("sender_id"))
                mine = str(message.get("sender_id")) == str(uid)
                bubble_class = "bubble-mine" if mine else "bubble-theirs"

                name_html = (
                    ""
                    if mine
                    else f'<div class="name">{esc(get_name(profile))}</div>'
                )

                # FIX: resolve avatar path to a real URL for the HTML <img>
                _avatar = avatar_src(profile) if not mine else ""
                avatar_html = (
                    f'<img src="{esc(_avatar)}" '
                    'width="26" style="border-radius:50%;"> '
                    if _avatar
                    else ""
                )

                quoted = reply_preview(message, messages)
                reply_html = (
                    f'<div class="reply-box">↩️ {esc(quoted)}</div>'
                    if quoted
                    else ""
                )

                pinned_label = (
                    '<div style="font-size:11px;color:#667781;">📌 Pinned</div>'
                    if message.get("is_pinned")
                    else ""
                )

                st.markdown(
                    f'<div class="{bubble_class}">'
                    f'{avatar_html}{name_html}{pinned_label}{reply_html}'
                    f'<div>{esc(message.get("message_text") or "")}</div>'
                    f'<div class="time">{fmt_time(message.get("created_at"))}</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

                if message.get("attachment_path"):
                    attachment_url = storage_url(
                        message.get("attachment_path")
                    )

                    if attachment_url:
                        try:
                            if (
                                message.get("attachment_type") or ""
                            ).startswith("video"):
                                st.video(attachment_url)
                            else:
                                st.image(attachment_url, width=260)
                        except Exception:
                            st.caption("Attachment unavailable")

                # Reactions: existing database table supports Chat Rooms
                if selected_type == "room":
                    try:
                        reactions = (
                            supabase.table("group_message_reactions")
                            .select("*")
                            .eq("message_id", message.get("id"))
                            .execute()
                            .data or []
                        )
                    except Exception:
                        reactions = []

                    if reactions:
                        counts = {}
                        for reaction in reactions:
                            key = reaction.get("reaction")
                            counts[key] = counts.get(key, 0) + 1

                        st.caption(
                            " ".join(
                                f"{esc(key)} {count}"
                                for key, count in counts.items()
                            )
                        )

                if st.button("⋯", key=f"opt_{message.get('id')}"):
                    current = st.session_state.get("eco_msg_opt")
                    st.session_state["eco_msg_opt"] = (
                        None if current == message.get("id")
                        else message.get("id")
                    )
                    st.rerun()

                if (
                    st.session_state.get("eco_msg_opt")
                    == message.get("id")
                ):
                    opt1, opt2, opt3, opt4 = st.columns(4)

                    with opt1:
                        if st.button(
                            "↩️ Reply",
                            key=f"rep_{message.get('id')}",
                        ):
                            st.session_state["eco_reply_to"] = {
                                "id": message.get("id"),
                                "text": (
                                    message.get("message_text")
                                    or "📷 Attachment"
                                ),
                            }
                            st.session_state["eco_msg_opt"] = None
                            st.rerun()

                    with opt2:
                        if st.button(
                            "❤️ React",
                            key=f"react_{message.get('id')}",
                        ):
                            if selected_type == "room":
                                try:
                                    existing_reaction = (
                                        supabase.table("group_message_reactions")
                                        .select("*")
                                        .eq("message_id", message.get("id"))
                                        .eq("user_id", uid)
                                        .execute()
                                        .data or []
                                    )

                                    if existing_reaction:
                                        supabase.table(
                                            "group_message_reactions"
                                        ).delete().eq(
                                            "message_id", message.get("id")
                                        ).eq("user_id", uid).execute()
                                    else:
                                        supabase.table(
                                            "group_message_reactions"
                                        ).insert({
                                            "message_id": message.get("id"),
                                            "user_id": uid,
                                            "reaction": "❤️",
                                        }).execute()

                                    st.session_state["eco_msg_opt"] = None
                                    st.rerun()

                                except Exception as error:
                                    st.error(f"Reaction failed: {error}")
                            else:
                                st.info(
                                    "DM reactions are not enabled in the "
                                    "currently confirmed database schema."
                                )

                    with opt3:
                        if st.button(
                            "↪️ Forward",
                            key=f"fwd_{message.get('id')}",
                        ):
                            st.session_state["eco_forward"] = {
                                "text": message.get("message_text") or "",
                                "attachment_path": message.get("attachment_path"),
                                "attachment_name": message.get("attachment_name"),
                                "attachment_type": message.get("attachment_type"),
                                "source_type": selected_type,
                                "source_message_id": message.get("id"),
                            }

                            st.session_state["eco_msg_opt"] = None
                            st.session_state["eco_notice"] = (
                                "Forwarding — choose a destination in Chats "
                                "or Chat Rooms."
                            )
                            st.rerun()

                    with opt4:
                        if st.button(
                            "📌 Pin",
                            key=f"pin_{message.get('id')}",
                        ):
                            if selected_type == "room":
                                try:
                                    new_pin_state = not bool(
                                        message.get("is_pinned")
                                    )

                                    update_data = {
                                        "is_pinned": new_pin_state,
                                        "pinned_by": uid if new_pin_state else None,
                                        "pinned_at": (
                                            datetime.now(timezone.utc).isoformat()
                                            if new_pin_state
                                            else None
                                        ),
                                    }

                                    supabase.table("group_messages").update(
                                        update_data
                                    ).eq("id", message.get("id")).execute()

                                    st.session_state["eco_msg_opt"] = None
                                    st.rerun()

                                except Exception as error:
                                    st.error(f"Pin update failed: {error}")
                            else:
                                st.info(
                                    "Persistent DM pins are not enabled "
                                    "in the confirmed database schema."
                                )

            # Reply preview above composer
            reply_to = st.session_state.get("eco_reply_to")

            if reply_to:
                reply_text = (
                    reply_to.get("text", "")
                    if isinstance(reply_to, dict)
                    else str(reply_to)
                )

                st.markdown(
                    f'<div class="reply-box">Replying to: '
                    f'{esc(reply_text[:80])}</div>',
                    unsafe_allow_html=True,
                )

                if st.button("Cancel Reply", key="cancel_reply"):
                    st.session_state["eco_reply_to"] = None
                    st.rerun()

            # Composer
            st.divider()

            message_input = st.text_input(
                "Message",
                key=f"msg_{selected_type}_{selected_id}",
                label_visibility="collapsed",
                placeholder="Type a message...",
            )

            attach_col, send_col = st.columns([3, 1])

            with attach_col:
                uploaded_file = st.file_uploader(
                    "📎 Attach photo / video",
                    type=["jpg", "jpeg", "png", "mp4", "mov", "webp"],
                    key=f"up_{selected_type}_{selected_id}",
                    label_visibility="collapsed",
                )

            with send_col:
                if st.button(
                    "➤ Send",
                    key=f"send_{selected_type}_{selected_id}",
                    use_container_width=True,
                ):
                    if (
                        selected_type == "room"
                        and not is_approved(selected.get("my_status"))
                    ):
                        st.error("Only approved members can send.")

                    else:
                        attachment_path = None
                        attachment_type = None
                        attachment_name = None

                        if uploaded_file is not None:
                            attachment_path = upload(
                                uploaded_file,
                                "chatrooms"
                                if selected_type == "room"
                                else "direct-messages",
                            )
                            attachment_type = uploaded_file.type
                            attachment_name = uploaded_file.name

                        final_text = message_input.strip()
                        reply_id = None

                        if isinstance(reply_to, dict):
                            reply_id = reply_to.get("id")

                        if final_text or attachment_path:
                            try:
                                message_data = {
                                    "sender_id": uid,
                                    "message_text": final_text,
                                    "attachment_path": attachment_path,
                                    "attachment_type": attachment_type,
                                    "attachment_name": attachment_name,
                                }

                                if selected_type == "room":
                                    message_data.update({
                                        "group_id": selected_id,
                                        "status": "sent",
                                        "reply_to_id": reply_id,
                                    })

                                    supabase.table(
                                        "group_messages"
                                    ).insert(message_data).execute()

                                else:
                                    message_data.update({
                                        "conversation_id": selected_id,
                                        "reply_to_id": reply_id,
                                    })

                                    supabase.table(
                                        "direct_messages"
                                    ).insert(message_data).execute()

                                st.session_state["eco_reply_to"] = None
                                st.rerun()

                            except Exception as error:
                                st.error(f"Send failed: {error}")

    # ---------- MAIN SCREENS ----------
    else:
        nav = st.session_state["eco_nav"]

        # ---------- CHATS ----------
        if nav == "Chats":
            st.markdown("### 💬 Chats")

            st.text_input(
                "Search @username",
                key="search_chats_main",
                placeholder="Search @username",
            )

            search_query = (
                st.session_state.get("search_chats_main", "")
                .lower()
                .replace("@", "")
            )

            if st.button(
                "➕ New Chat",
                use_container_width=True,
                key="new_dm_toggle",
            ):
                st.session_state["eco_show_new"] = (
                    not st.session_state["eco_show_new"]
                )
                st.rerun()

            if st.session_state.get("eco_show_new"):
                new_query = st.text_input(
                    "Find member",
                    key="new_dm_search",
                    placeholder="@roy or roy",
                )

                if new_query.strip():
                    for profile in search_by_username(new_query):
                        if str(profile.get("user_id")) == str(uid):
                            continue

                        if st.button(
                            f"💬 {get_name(profile)} — "
                            f"{profile.get('display_name') or ''}",
                            key=f"ndm_{profile.get('user_id')}",
                        ):
                            open_dm(profile.get("user_id"))

            forwarding = st.session_state.get("eco_forward")

            if forwarding:
                st.info(
                    f"Forwarding: {esc(forwarding.get('text', '')[:60])} "
                    "— choose a private chat below."
                )

            if not dm_list:
                st.info(
                    "No private chats yet. Tap ➕ New Chat to start one."
                )

            st.markdown('<div class="inbox-wrap">', unsafe_allow_html=True)

            for conversation in dm_list:
                if (
                    search_query
                    and search_query not in conversation.get(
                        "name", ""
                    ).lower().replace("@", "")
                ):
                    continue

                if st.button(
                    inbox_label(conversation),
                    key=f"open_dm_{conversation['id']}",
                    use_container_width=True,
                ):
                    mark_read(conversation)
                    st.session_state["eco_sel"] = conversation["id"]
                    st.session_state["eco_sel_type"] = "dm"
                    st.rerun()

                if forwarding and st.button(
                    f"➡️ Forward to {conversation.get('name')}",
                    key=f"fwd_dm_{conversation['id']}",
                ):
                    try:
                        forward_data = {
                            "conversation_id": conversation["id"],
                            "sender_id": uid,
                            "message_text": (
                                f"Forwarded: {forwarding['text']}"
                                if forwarding.get("text")
                                else "Forwarded attachment"
                            ),
                            "attachment_path": forwarding.get("attachment_path"),
                            "attachment_name": forwarding.get("attachment_name"),
                            "attachment_type": forwarding.get("attachment_type"),
                        }

                        supabase.table("direct_messages").insert(
                            forward_data
                        ).execute()

                        st.session_state["eco_forward"] = None
                        st.session_state["eco_notice"] = "Forwarded!"
                        st.rerun()

                    except Exception as error:
                        st.error(f"Forward failed: {error}")

            st.markdown("</div>", unsafe_allow_html=True)

        # ---------- CHAT ROOMS ----------
        elif nav == "Chat Rooms":
            st.markdown("### 👥 Chat Rooms")

            action1, action2 = st.columns(2)

            with action1:
                if st.button(
                    "➕ Create Room",
                    use_container_width=True,
                    key="create_room_toggle",
                ):
                    st.session_state["eco_show_create_room"] = (
                        not st.session_state["eco_show_create_room"]
                    )
                    st.session_state["eco_show_new"] = False
                    st.rerun()

            with action2:
                if st.button(
                    "🔗 Join via Code",
                    use_container_width=True,
                    key="join_toggle",
                ):
                    st.session_state["eco_show_new"] = (
                        not st.session_state["eco_show_new"]
                    )
                    st.session_state["eco_show_create_room"] = False
                    st.rerun()

            if st.session_state.get("eco_show_create_room"):
                st.markdown('<div class="card">', unsafe_allow_html=True)

                room_name = st.text_input(
                    "Room Name",
                    key="new_room_name2",
                    placeholder="e.g. Harare Clean-Up Team",
                )

                room_description = st.text_input(
                    "Description",
                    key="new_room_desc2",
                )

                if st.button(
                    "✅ Create Chat Room",
                    use_container_width=True,
                    key="create_room_do",
                ):
                    if not room_name.strip():
                        st.error("Enter name.")
                    else:
                        code = uuid.uuid4().hex[:8].upper()

                        try:
                            created = (
                                supabase.table("community_groups")
                                .insert({
                                    "name": room_name.strip(),
                                    "description": room_description,
                                    "created_by": uid,
                                    "invite_code": code,
                                })
                                .execute()
                            )

                            group_id = created.data[0].get("id")

                            supabase.table("group_memberships").insert({
                                "group_id": group_id,
                                "user_id": uid,
                                "membership_role": "admin",
                                "status": "approved",
                            }).execute()

                            st.session_state["eco_last_created"] = {
                                "name": room_name.strip(),
                                "code": code,
                            }

                            st.session_state["eco_notice"] = (
                                f"Room created! Code: {code}"
                            )
                            st.session_state["eco_show_create_room"] = False
                            st.rerun()

                        except Exception as error:
                            st.error(f"Create failed: {error}")

                st.markdown("</div>", unsafe_allow_html=True)

            if st.session_state.get("eco_show_new"):
                st.markdown('<div class="card">', unsafe_allow_html=True)

                code_input = st.text_input(
                    "Invite Code / Link",
                    key="join_code_main",
                    placeholder="ABC12345 or ?room=ABC12345",
                )

                if st.button(
                    "Request to Join",
                    key="join_room_main",
                    use_container_width=True,
                ):
                    clean = code_input.strip().upper()

                    if "ROOM=" in clean:
                        clean = (
                            clean.split("ROOM=")[-1]
                            .split("&")[0]
                            .split("/")[0]
                            .strip()
                        )
                    else:
                        clean = clean.split("/")[-1].strip()

                    if clean:
                        try:
                            room_result = (
                                supabase.table("community_groups")
                                .select("*")
                                .eq("invite_code", clean)
                                .single()
                                .execute()
                            )

                            room_data = room_result.data

                            if room_data:
                                existing_membership = (
                                    supabase.table("group_memberships")
                                    .select("*")
                                    .eq("group_id", room_data.get("id"))
                                    .eq("user_id", uid)
                                    .execute()
                                    .data or []
                                )

                                if existing_membership:
                                    st.info(
                                        "You already have a membership or "
                                        "join request for this Chat Room."
                                    )
                                else:
                                    supabase.table(
                                        "group_memberships"
                                    ).insert({
                                        "group_id": room_data.get("id"),
                                        "user_id": uid,
                                        "membership_role": "member",
                                        "status": "pending",
                                    }).execute()

                                    st.session_state["eco_notice"] = (
                                        "Join request sent — pending approval"
                                    )
                                    st.session_state["eco_show_new"] = False
                                    st.rerun()

                            else:
                                st.error("Code not found.")

                        except Exception as error:
                            st.error(f"Join failed: {error}")

                st.markdown("</div>", unsafe_allow_html=True)

            if st.session_state.get("eco_last_created"):
                last_created = st.session_state["eco_last_created"]

                st.markdown(
                    '<div class="notice-box">✅ Created: '
                    f'<b>{esc(last_created["name"])}</b> — Code: '
                    f'<b>{esc(last_created["code"])}</b></div>',
                    unsafe_allow_html=True,
                )

                app_url = get_app_url()
                if app_url:
                    st.code(f"{app_url}/?room={last_created['code']}")

            forwarding = st.session_state.get("eco_forward")

            if forwarding:
                st.info(
                    f"Forwarding: {esc(forwarding.get('text', '')[:60])} "
                    "— choose a Chat Room below."
                )

            if not room_list:
                st.info("No rooms yet. Create one or join via code.")

            st.markdown('<div class="inbox-wrap">', unsafe_allow_html=True)

            for conversation in room_list:
                if st.button(
                    inbox_label(conversation),
                    key=f"open_room_{conversation['id']}",
                    use_container_width=True,
                ):
                    mark_read(conversation)
                    st.session_state["eco_sel"] = conversation["id"]
                    st.session_state["eco_sel_type"] = "room"
                    st.rerun()

                if forwarding and st.button(
                    f"➡️ Forward to {conversation.get('name')}",
                    key=f"fwd_room_{conversation['id']}",
                ):
                    try:
                        forward_data = {
                            "group_id": conversation["id"],
                            "sender_id": uid,
                            "message_text": forwarding.get("text") or "",
                            "status": "sent",
                            "attachment_path": forwarding.get("attachment_path"),
                            "attachment_name": forwarding.get("attachment_name"),
                            "attachment_type": forwarding.get("attachment_type"),
                        }

                        if (
                            forwarding.get("source_type") == "room"
                            and forwarding.get("source_message_id")
                        ):
                            forward_data["forwarded_from"] = (
                                forwarding.get("source_message_id")
                            )

                        supabase.table("group_messages").insert(
                            forward_data
                        ).execute()

                        st.session_state["eco_forward"] = None
                        st.session_state["eco_notice"] = "Forwarded!"
                        st.rerun()

                    except Exception as error:
                        st.error(f"Forward failed: {error}")

            st.markdown("</div>", unsafe_allow_html=True)

        # ---------- UPDATES ----------
        elif nav == "Updates":
            st.markdown("### 📸 Updates")

            st.markdown('<div class="card">', unsafe_allow_html=True)

            story_file = st.file_uploader(
                "Add Update — photo / video",
                type=["jpg", "jpeg", "png", "mp4", "mov", "webp"],
                key="story_file_main",
            )

            story_caption = st.text_input(
                "Caption (optional)",
                key="story_cap_main",
            )

            if st.button(
                "➕ Post Update",
                key="post_story_main",
                use_container_width=True,
            ):
                if story_file is None:
                    st.error("Pick a photo or video first.")
                else:
                    path = upload(story_file, "stories")

                    if path:
                        try:
                            supabase.table("stories").insert({
                                "user_id": uid,
                                "media_url": path,
                                "media_type": (
                                    "video"
                                    if str(story_file.type).startswith("video")
                                    else "image"
                                ),
                                "caption": story_caption,
                                "expires_at": (
                                    datetime.now(timezone.utc)
                                    + timedelta(hours=24)
                                ).isoformat(),
                            }).execute()

                            st.session_state["eco_notice"] = "Story posted!"
                            st.rerun()

                        except Exception as error:
                            st.error(f"Post failed: {error}")

            st.markdown("</div>", unsafe_allow_html=True)

            try:
                all_stories = (
                    supabase.table("stories")
                    .select("*")
                    .order("created_at", desc=True)
                    .limit(50)
                    .execute()
                    .data or []
                )
            except Exception:
                all_stories = []

            now_utc = datetime.now(timezone.utc)
            valid_stories = []

            for story in all_stories:
                try:
                    expiry = datetime.fromisoformat(
                        str(story.get("expires_at")).replace("Z", "+00:00")
                    )
                    if expiry >= now_utc:
                        valid_stories.append(story)
                except Exception:
                    continue

            # One story circle per member, arranged horizontally
            unique_users = []
            story_circles = []

            for story in valid_stories:
                if story.get("user_id") not in unique_users:
                    unique_users.append(story.get("user_id"))
                    story_circles.append(story)

            if not story_circles:
                st.info("No active stories. Stories expire after 24 hours.")

            else:
                story_columns = st.columns(min(4, len(story_circles)))

                for index, story in enumerate(story_circles):
                    profile = get_profile(story.get("user_id"))
                    column = story_columns[index % len(story_columns)]

                    with column:
                        # FIX: resolve avatar path; fall back to initials
                        if not show_avatar(profile, 60):
                            st.markdown(
                                f"**{esc(get_name(profile)[:2].upper())}**"
                            )

                        st.caption(get_name(profile))

                        if st.button(
                            "View",
                            key=f"view_story_{story.get('user_id')}",
                            use_container_width=True,
                        ):
                            st.session_state["eco_story_user"] = (
                                story.get("user_id")
                            )
                            st.rerun()

            # Story viewer
            if st.session_state.get("eco_story_user"):
                story_user = st.session_state["eco_story_user"]
                story_profile = get_profile(story_user)

                st.divider()
                st.markdown(
                    f"#### 📸 {esc(get_name(story_profile))}'s Updates"
                )

                if st.button(
                    "✕ Close Viewer",
                    key="close_story_viewer",
                ):
                    st.session_state["eco_story_user"] = None
                    st.rerun()

                user_stories = [
                    story for story in valid_stories
                    if str(story.get("user_id")) == str(story_user)
                ]

                for story in user_stories:
                    if str(story_user) != str(uid):
                        try:
                            existing_view = (
                                supabase.table("story_views")
                                .select("id")
                                .eq("story_id", story.get("id"))
                                .eq("viewer_id", uid)
                                .execute()
                                .data or []
                            )

                            if not existing_view:
                                supabase.table("story_views").insert({
                                    "story_id": story.get("id"),
                                    "viewer_id": uid,
                                }).execute()

                        except Exception:
                            pass

                    if story.get("caption"):
                        st.write(esc(story.get("caption")))

                    media_url = storage_url(story.get("media_url"))

                    if media_url:
                        try:
                            if story.get("media_type") == "video":
                                st.video(media_url)
                            else:
                                st.image(media_url, width=320)
                        except Exception:
                            st.caption("Media unavailable")

                    if str(story_user) == str(uid):
                        try:
                            views = (
                                supabase.table("story_views")
                                .select("*")
                                .eq("story_id", story.get("id"))
                                .execute()
                                .data or []
                            )

                            st.caption(f"👁️ {len(views)} views")

                            for view in views:
                                viewer = get_profile(view.get("viewer_id"))
                                st.write(
                                    f"👁️ {esc(get_name(viewer))}"
                                )

                        except Exception:
                            st.caption("Views unavailable")
                    else:
                        st.caption("👁️ Views visible only to owner")

                    st.divider()

        # ---------- PROFILE ----------
        elif nav == "Profile":
            my_profile = get_profile(uid)

            st.markdown(
                '<div class="card" style="text-align:center;">',
                unsafe_allow_html=True,
            )

            # FIX: this was the line that crashed the app
            show_avatar(my_profile, 110)

            st.markdown(
                f"### {esc(get_name(my_profile))}",
                unsafe_allow_html=True,
            )

            st.write(f"**{esc(my_profile.get('display_name') or '')}**")
            st.write(esc(my_profile.get("bio") or "No bio yet"))

            st.write(
                f"📍 {esc(my_profile.get('location') or '—')} • "
                f"{esc(my_profile.get('country_of_origin') or '')}"
            )

            if my_profile.get("interests"):
                st.write(f"✨ Interests: {esc(my_profile.get('interests'))}")

            show_social_handles(my_profile)

            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("**Find Member**")

            profile_query = st.text_input(
                "Search @username",
                key="profile_search",
                placeholder="@roy",
            )

            if profile_query.strip():
                for profile in search_by_username(profile_query):
                    if str(profile.get("user_id")) == str(uid):
                        continue

                    if st.button(
                        f"👤 {get_name(profile)} — View Profile",
                        key=f"prof_{profile.get('user_id')}",
                    ):
                        st.session_state["eco_profile_view"] = (
                            profile.get("user_id")
                        )
                        st.rerun()

    # ---------- BOTTOM NAV ----------
    st.markdown('<div class="bottom-bar"></div>', unsafe_allow_html=True)

    nav1, nav2, nav3, nav4 = st.columns(4)

    with nav1:
        if st.button(
            "💬\nChats",
            key="nav_chats",
            use_container_width=True,
        ):
            go("Chats")

    with nav2:
        if st.button(
            "📸\nUpdates",
            key="nav_updates",
            use_container_width=True,
        ):
            go("Updates")

    with nav3:
        if st.button(
            "👥\nChat Rooms",
            key="nav_rooms",
            use_container_width=True,
        ):
            go("Chat Rooms")

    with nav4:
        if st.button(
            "👤\nProfile",
            key="nav_profile",
            use_container_width=True,
        ):
            go("Profile")
