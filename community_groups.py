import streamlit as st
import uuid
from datetime import datetime, timedelta

def render_community_groups_page(supabase=None, user_id=None):
    st.markdown("## 👥 Community Hub")
    st.caption("Talk like home, connect like family.")

    # --- Use what main app passed ---
    if supabase is None:
        supabase = st.session_state.get("supabase_client")
    if supabase is None:
        try:
            from supabase import create_client
            supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
            st.session_state["supabase_client"] = supabase
        except Exception as e:
            st.error(f"Supabase not connected: {e}")
            return

    uid = user_id or st.session_state.get("uid") or st.session_state.get("user_id")
    if not uid:
        try:
            user = supabase.auth.get_user().user
            if user:
                uid = user.id
                st.session_state["uid"] = uid
        except Exception:
            pass
    if not uid:
        st.warning("Please login first, then come back to Community Hub.")
        return

    BUCKET = "community-media"
    REACTION_EMOJIS = ["❤️", "😂", "🔥", "👍", "😮", "😢"]

    # --- Mark me online ---
    try:
        supabase.table("profiles").update({"is_online": True, "last_seen": "now()"}).eq("id", uid).execute()
    except Exception:
        pass

    # --- Helpers ---
    def eco_profile(uid2):
        try:
            r = supabase.table("profiles").select("*").eq("id", uid2).single().execute()
            return r.data or {}
        except Exception:
            return {}

    def eco_name(p):
        return p.get("display_name") or p.get("username") or "User"

    def eco_avatar(p):
        return p.get("avatar_url") or p.get("profile_pic_url") or ""

    def eco_online(p):
        if p.get("is_online"):
            return "🟢 Online"
        ls = p.get("last_seen")
        if ls:
            try:
                dt = datetime.fromisoformat(str(ls).replace("Z", "+00:00"))
                mins = int((datetime.now(dt.tzinfo) - dt).total_seconds() // 60)
                if mins < 1:
                    return "🟢 Just now"
                if mins < 60:
                    return f"⚪ {mins}m ago"
                return f"⚪ {mins//60}h ago"
            except Exception:
                return "⚪ Offline"
        return "⚪ Offline"

    def eco_storage_url(path):
        if not path:
            return ""
        if str(path).startswith("http"):
            return str(path)
        try:
            res = supabase.storage.from_(BUCKET).create_signed_url(str(path), 3600)
            if isinstance(res, dict):
                return res.get("signedURL") or res.get("signedUrl") or ""
            return str(res)
        except Exception:
            try:
                return supabase.storage.from_(BUCKET).get_public_url(str(path))
            except Exception:
                return ""

    def eco_upload(file, folder="chat"):
        try:
            ext = str(file.name).split(".")[-1].lower() if "." in str(file.name) else "jpg"
            path = f"{folder}/{uid}_{uuid.uuid4().hex[:8]}.{ext}"
            supabase.storage.from_(BUCKET).upload(path, file.getvalue(), {"content-type": file.type})
            return path
        except Exception as e:
            st.error(f"Upload failed: {e}")
            return None

    def eco_reactions(msg_id, table="message_reactions", msg_col="message_id"):
        try:
            r = supabase.table(table).select("*").eq(msg_col, msg_id).execute().data or []
            return r
        except Exception:
            return []

    def eco_show_reactions(msg_id, table="message_reactions", msg_col="message_id"):
        reacts = eco_reactions(msg_id, table, msg_col)
        if reacts:
            counts = {}
            for x in reacts:
                counts[x.get("emoji")] = counts.get(x.get("emoji"), 0) + 1
            st.caption(" ".join([f"{k} {v}" for k, v in counts.items()]))

    def eco_reaction_buttons(msg_id, table="message_reactions", msg_col="message_id"):
        cols = st.columns(len(REACTION_EMOJIS))
        for i, em in enumerate(REACTION_EMOJIS):
            with cols[i]:
                if st.button(em, key=f"react_{table}_{msg_id}_{em}_{uid}"):
                    try:
                        supabase.table(table).delete().eq(msg_col, msg_id).eq("user_id", uid).execute()
                    except Exception:
                        pass
                    try:
                        supabase.table(table).insert({msg_col: msg_id, "user_id": uid, "emoji": em}).execute()
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    def eco_tick(m, is_mine):
        if not is_mine:
            return ""
        if m.get("status") == "read":
            return " ✓✓"
        elif m.get("status") == "delivered":
            return " ✓✓"
        return " ✓"

    # ================= TABS =================
    tab_rooms, tab_dm, tab_stories, tab_members = st.tabs(["👥 Chat Rooms", "💬 Direct Chats", "📸 Stories", "🧑‍🤝‍🧑 Members"])

    # ============ TAB 1: CHAT ROOMS ============
    with tab_rooms:
        with st.expander("➕ Create New Chat Room"):
            gname = st.text_input("Chat Room Name", key="room_name")
            gdesc = st.text_area("Description (optional)", key="room_desc")
            if st.button("Create Chat Room"):
                if not gname.strip():
                    st.error("Enter a name")
                else:
                    try:
                        payload = {"name": gname.strip(), "description": gdesc, "created_by": uid, "invite_code": str(uuid.uuid4())[:8].upper()}
                        r = supabase.table("groups").insert(payload).execute()
                        gid = r.data[0].get("id")
                        supabase.table("group_members").insert({"group_id": gid, "user_id": uid, "role": "Admin"}).execute()
                        st.success(f"Created! Invite Code: {payload['invite_code']}")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

        with st.expander("🔗 Join Chat Room via Code"):
            code = st.text_input("Paste Invite Code here", key="join_code")
            if st.button("Join Room"):
                try:
                    r = supabase.table("groups").select("*").eq("invite_code", code.strip().upper()).single().execute()
                    if r.data:
                        try:
                            supabase.table("group_members").insert({"group_id": r.data.get("id"), "user_id": uid, "role": "Member"}).execute()
                        except Exception:
                            pass
                        st.success(f"Joined {r.data.get('name')}!")
                        st.rerun()
                    else:
                        st.error("Code not found")
                except Exception as e:
                    st.error(str(e))

        try:
            mems = supabase.table("group_members").select("group_id").eq("user_id", uid).execute().data or []
            gids = [m.get("group_id") for m in mems]
            rooms = supabase.table("groups").select("*").in_("id", gids).execute().data or [] if gids else []
        except Exception as e:
            st.error(str(e))
            rooms = []

        if not rooms:
            st.info("No Chat Rooms yet. Create one above or join with a code.")
        else:
            for room in rooms:
                st.markdown(f"### 👥 {room.get('name')}")
                st.caption(f"Invite Code: `{room.get('invite_code') or ''}` — Copy and send on WhatsApp")
                if room.get("description"):
                    st.write(room.get("description"))
                try:
                    my_mem = supabase.table("group_members").select("*").eq("group_id", room.get("id")).eq("user_id", uid).single().execute().data or {}
                    is_admin = my_mem.get("role") == "Admin"
                except Exception:
                    is_admin = False
                st.write(f"You are: **{'👑 Admin' if is_admin else 'Member'}**")

                try:
                    msgs = supabase.table("group_messages").select("*").eq("group_id", room.get("id")).order("created_at").execute().data or []
                except Exception:
                    msgs = []

                for m in msgs:
                    p = eco_profile(m.get("sender_id"))
                    is_mine = str(m.get("sender_id")) == str(uid)
                    if not is_mine and m.get("status") != "read":
                        try:
                            supabase.table("group_messages").update({"status": "read", "read_at": "now()"}).eq("id", m.get("id")).execute()
                        except Exception:
                            pass
                    st.write(f"**{eco_name(p)}** {eco_online(p)}: {m.get('message_text') or ''}{eco_tick(m, is_mine)}")
                    if m.get("media_url"):
                        url = eco_storage_url(m.get("media_url"))
                        if m.get("media_type") == "video":
                            st.video(url)
                        else:
                            st.image(url, width=250)
                    eco_show_reactions(m.get("id"), "group_message_reactions", "message_id")
                    with st.expander("React", expanded=False):
                        eco_reaction_buttons(m.get("id"), "group_message_reactions", "message_id")

                c1, c2 = st.columns([4, 1])
                with c1:
                    msg = st.text_input(f"Message in {room.get('name')}", key=f"msg_{room.get('id')}", label_visibility="collapsed", placeholder="Type a message...")
                with c2:
                    send = st.button("Send", key=f"send_{room.get('id')}")
                up = st.file_uploader(f"Photo/Video for {room.get('name')}", type=["jpg", "jpeg", "png", "mp4", "mov", "webp"], key=f"up_{room.get('id')}")
                if send:
                    media_path = None
                    media_type = None
                    if up is not None:
                        media_path = eco_upload(up, "group_chat")
                        media_type = "video" if str(up.type).startswith("video") else "image"
                    if msg.strip() or media_path:
                        supabase.table("group_messages").insert({"group_id": room.get("id"), "sender_id": uid, "message_text": msg.strip(), "status": "sent", "media_url": media_path, "media_type": media_type}).execute()
                        st.rerun()

                if is_admin:
                    st.markdown("#### 👑 Admin Controls")
                    search_user = st.text_input(f"Search person to add to {room.get('name')}", key=f"add_search_{room.get('id')}")
                    if search_user.strip():
                        try:
                            found = supabase.table("profiles").select("*").or_(f"username.ilike.%{search_user}%,display_name.ilike.%{search_user}%").limit(5).execute().data or []
                            for f in found:
                                if str(f.get("id")) == str(uid):
                                    continue
                                if st.button(f"➕ Add {eco_name(f)}", key=f"add_{room.get('id')}_{f.get('id')}"):
                                    try:
                                        supabase.table("group_members").insert({"group_id": room.get("id"), "user_id": f.get("id"), "role": "Member"}).execute()
                                        st.success(f"Added {eco_name(f)}")
                                        st.rerun()
                                    except Exception:
                                        st.error("Already in room")
                        except Exception as e:
                            st.error(str(e))
                    try:
                        all_mems = supabase.table("group_members").select("*").eq("group_id", room.get("id")).execute().data or []
                        for mm in all_mems:
                            if str(mm.get("user_id")) == str(uid):
                                continue
                            pp = eco_profile(mm.get("user_id"))
                            cc1, cc2, cc3 = st.columns([3, 1, 1])
                            with cc1:
                                st.write(f"{eco_name(pp)} — {mm.get('role')} — {eco_online(pp)}")
                            with cc2:
                                if mm.get("role") != "Admin":
                                    if st.button("Make Admin", key=f"mkadmin_{room.get('id')}_{mm.get('user_id')}"):
                                        supabase.table("group_members").update({"role": "Admin"}).eq("group_id", room.get("id")).eq("user_id", mm.get("user_id")).execute()
                                        st.rerun()
                            with cc3:
                                if st.button("Remove", key=f"rem_{room.get('id')}_{mm.get('user_id')}"):
                                    supabase.table("group_members").delete().eq("group_id", room.get("id")).eq("user_id", mm.get("user_id")).execute()
                                    st.rerun()
                    except Exception:
                        pass
                    if st.button(f"🗑️ Delete {room.get('name')}", key=f"del_{room.get('id')}"):
                        supabase.table("group_members").delete().eq("group_id", room.get("id")).execute()
                        supabase.table("group_messages").delete().eq("group_id", room.get("id")).execute()
                        supabase.table("groups").delete().eq("id", room.get("id")).execute()
                        st.rerun()
                else:
                    if st.button(f"🚪 Leave {room.get('name')}", key=f"leave_{room.get('id')}"):
                        supabase.table("group_members").delete().eq("group_id", room.get("id")).eq("user_id", uid).execute()
                        st.rerun()
                st.divider()

    # ============ TAB 2: DIRECT CHATS ============
    with tab_dm:
        st.markdown("#### 💬 Direct Chats")
        search_dm = st.text_input("Search person to DM", key="dm_search")
        selected_dm = None
        if search_dm.strip():
            try:
                found = supabase.table("profiles").select("*").or_(f"username.ilike.%{search_dm}%,display_name.ilike.%{search_dm}%").limit(10).execute().data or []
                for f in found:
                    if str(f.get("id")) == str(uid):
                        continue
                    if st.button(f"💬 Chat with {eco_name(f)} — {eco_online(f)}", key=f"dm_start_{f.get('id')}"):
                        st.session_state["dm_with"] = str(f.get("id"))
                        st.rerun()
            except Exception as e:
                st.error(str(e))

        # List existing DM chats
        try:
            my_chats = supabase.table("direct_chats").select("*").or_(f"user1_id.eq.{uid},user2_id.eq.{uid}").execute().data or []
        except Exception:
            my_chats = []
        for ch in my_chats:
            other = ch.get("user2_id") if str(ch.get("user1_id")) == str(uid) else ch.get("user1_id")
            op = eco_profile(other)
            if st.button(f"💬 {eco_name(op)} — {eco_online(op)}", key=f"dm_open_{ch.get('id')}"):
                st.session_state["dm_with"] = str(other)
                st.rerun()

        dm_with = st.session_state.get("dm_with")
        if dm_with:
            op = eco_profile(dm_with)
            st.markdown(f"### 💬 Chat with {eco_name(op)} — {eco_online(op)}")
            # Find or create chat
            chat_id = None
            try:
                r = supabase.table("direct_chats").select("*").or_(f"and(user1_id.eq.{uid},user2_id.eq.{dm_with}),and(user1_id.eq.{dm_with},user2_id.eq.{uid})").execute().data or []
                if r:
                    chat_id = r[0].get("id")
                else:
                    r2 = supabase.table("direct_chats").insert({"user1_id": uid, "user2_id": dm_with}).execute()
                    chat_id = r2.data[0].get("id")
            except Exception as e:
                st.error(str(e))
            if chat_id:
                try:
                    dmsgs = supabase.table("messages").select("*").eq("chat_id", chat_id).order("created_at").execute().data or []
                except Exception:
                    try:
                        dmsgs = supabase.table("direct_messages").select("*").eq("chat_id", chat_id).order("created_at").execute().data or []
                    except Exception:
                        dmsgs = []
                for m in dmsgs:
                    sender = m.get("sender_id") or m.get("user_id")
                    p = eco_profile(sender)
                    is_mine = str(sender) == str(uid)
                    if not is_mine and m.get("status") != "read":
                        try:
                            supabase.table("messages").update({"status": "read", "read_at": "now()"}).eq("id", m.get("id")).execute()
                        except Exception:
                            pass
                    st.write(f"**{eco_name(p)}**: {m.get('message_text') or m.get('content') or ''}{eco_tick(m, is_mine)}")
                    if m.get("media_url"):
                        st.image(eco_storage_url(m.get("media_url")), width=250)
                    eco_show_reactions(m.get("id"), "message_reactions", "message_id")
                dm_text = st.text_input("Type a DM...", key=f"dm_text_{chat_id}")
                dm_file = st.file_uploader("Photo/Video", type=["jpg", "jpeg", "png", "mp4", "mov", "webp"], key=f"dm_file_{chat_id}")
                if st.button("Send DM", key=f"dm_send_{chat_id}"):
                    media_path = None
                    media_type = None
                    if dm_file is not None:
                        media_path = eco_upload(dm_file, "dm_chat")
                        media_type = "video" if str(dm_file.type).startswith("video") else "image"
                    if dm_text.strip() or media_path:
                        try:
                            supabase.table("messages").insert({"chat_id": chat_id, "sender_id": uid, "message_text": dm_text.strip(), "status": "sent", "media_url": media_path, "media_type": media_type}).execute()
                        except Exception:
                            supabase.table("direct_messages").insert({"chat_id": chat_id, "sender_id": uid, "message_text": dm_text.strip(), "status": "sent", "media_url": media_path}).execute()
                        st.rerun()

    # ============ TAB 3: STORIES ============
    with tab_stories:
        st.markdown("#### 📸 Stories — 24 hours")
        story_file = st.file_uploader("Post a Story", type=["jpg", "jpeg", "png", "mp4", "mov", "webp"], key="story_upload")
        story_caption = st.text_input("Story caption (optional)", key="story_caption")
        if st.button("Post Story"):
            if story_file is None:
                st.error("Pick a photo/video first")
            else:
                path = eco_upload(story_file, "stories")
                if path:
                    try:
                        supabase.table("stories").insert({"user_id": uid, "media_url": path, "media_type": "video" if str(story_file.type).startswith("video") else "image", "caption": story_caption, "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()}).execute()
                        st.success("Story posted!")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
        try:
            all_stories = supabase.table("stories").select("*").order("created_at", desc=True).limit(50).execute().data or []
        except Exception:
            all_stories = []
        # Group by user
        users_seen = []
        for s in all_stories:
            # Skip expired
            try:
                exp = s.get("expires_at")
                if exp and datetime.fromisoformat(str(exp).replace("Z", "+00:00")) < datetime.now().astimezone():
                    continue
            except Exception:
                pass
            if s.get("user_id") in users_seen:
                continue
            users_seen.append(s.get("user_id"))
            p = eco_profile(s.get("user_id"))
            with st.expander(f"📸 {eco_name(p)} — {eco_online(p)}"):
                user_stories = [x for x in all_stories if x.get("user_id") == s.get("user_id")]
                for us in user_stories:
                    if us.get("caption"):
                        st.write(us.get("caption"))
                    url = eco_storage_url(us.get("media_url"))
                    if us.get("media_type") == "video":
                        st.video(url)
                    else:
                        st.image(url, width=300)
                    # Mark viewed
                    try:
                        supabase.table("story_views").insert({"story_id": us.get("id"), "viewer_id": uid}).execute()
                    except Exception:
                        pass

    # ============ TAB 4: MEMBERS ============
    with tab_members:
        st.markdown("#### 🧑‍🤝‍🧑 All Members")
        try:
            all_profiles = supabase.table("profiles").select("*").limit(100).execute().data or []
        except Exception:
            all_profiles = []
        for p in all_profiles:
            if str(p.get("id")) == str(uid):
                continue
            c1, c2 = st.columns([4, 1])
            with c1:
                st.write(f"**{eco_name(p)}** — {eco_online(p)}")
            with c2:
                if st.button("💬 DM", key=f"member_dm_{p.get('id')}"):
                    st.session_state["dm_with"] = str(p.get("id"))
                    st.rerun()
