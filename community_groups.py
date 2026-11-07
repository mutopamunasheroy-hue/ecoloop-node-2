import streamlit as st
import uuid

def render_community_groups_page():
    st.markdown("## 👥 Community")
    st.caption("Talk like home, connect like family.")

    # --- Get supabase + user from main app ---
    supabase = st.session_state.get("supabase_client")
    if supabase is None:
        try:
            from supabase import create_client
            supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
            st.session_state["supabase_client"] = supabase
        except Exception as e:
            st.error(f"Supabase not connected: {e}")
            return

    uid = st.session_state.get("uid") or st.session_state.get("user_id")
    if not uid:
        try:
            user = supabase.auth.get_user().user
            if user:
                uid = user.id
                st.session_state["uid"] = uid
        except Exception:
            pass
    if not uid:
        st.warning("Please login first, then come back to Community.")
        return

    # --- Mark me online ---
    try:
        supabase.table("profiles").update({"is_online": True, "last_seen": "now()"}).eq("id", uid).execute()
    except Exception:
        pass

    def eco_profile(uid2):
        try:
            r = supabase.table("profiles").select("*").eq("id", uid2).single().execute()
            return r.data or {}
        except Exception:
            return {}

    def eco_name(p):
        return p.get("display_name") or p.get("username") or "User"

    def eco_online(p):
        if p.get("is_online"):
            return "🟢 Online"
        return "⚪ Offline"

    # --- CREATE ROOM ---
    with st.expander("➕ Create New Chat Room"):
        gname = st.text_input("Chat Room Name")
        gdesc = st.text_area("Description (optional)")
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

    # --- JOIN VIA CODE ---
    with st.expander("🔗 Join Chat Room via Code"):
        code = st.text_input("Paste Invite Code here")
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

    # --- LIST MY ROOMS ---
    try:
        mems = supabase.table("group_members").select("group_id").eq("user_id", uid).execute().data or []
        gids = [m.get("group_id") for m in mems]
        rooms = supabase.table("groups").select("*").in_("id", gids).execute().data or [] if gids else []
    except Exception as e:
        st.error(str(e))
        rooms = []

    if not rooms:
        st.info("No Chat Rooms yet. Create one above.")
        return

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

        # --- MESSAGES WITH TICKS ---
        try:
            msgs = supabase.table("group_messages").select("*").eq("group_id", room.get("id")).order("created_at").execute().data or []
        except Exception:
            msgs = []

        for m in msgs:
            p = eco_profile(m.get("sender_id"))
            is_mine = str(m.get("sender_id")) == str(uid)
            # Mark as read if not mine
            if not is_mine and m.get("status") != "read":
                try:
                    supabase.table("group_messages").update({"status": "read", "read_at": "now()"}).eq("id", m.get("id")).execute()
                except Exception:
                    pass
            tick = ""
            if is_mine:
                if m.get("status") == "read":
                    tick = " ✓✓"
                elif m.get("status") == "delivered":
                    tick = " ✓✓"
                else:
                    tick = " ✓"
            st.write(f"**{eco_name(p)}** {eco_online(p)}: {m.get('message_text') or ''}{tick}")

        # --- SEND ---
        msg = st.text_input(f"Message in {room.get('name')}", key=f"msg_{room.get('id')}")
        if st.button(f"Send in {room.get('name')}", key=f"send_{room.get('id')}"):
            if msg.strip():
                supabase.table("group_messages").insert({"group_id": room.get("id"), "sender_id": uid, "message_text": msg.strip(), "status": "sent"}).execute()
                st.rerun()

        # --- ADMIN CONTROLS ---
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
                    c1, c2, c3 = st.columns([3, 1, 1])
                    with c1:
                        st.write(f"{eco_name(pp)} — {mm.get('role')} — {eco_online(pp)}")
                    with c2:
                        if mm.get("role") != "Admin":
                            if st.button("Make Admin", key=f"mkadmin_{room.get('id')}_{mm.get('user_id')}"):
                                supabase.table("group_members").update({"role": "Admin"}).eq("group_id", room.get("id")).eq("user_id", mm.get("user_id")).execute()
                                st.rerun()
                    with c3:
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
