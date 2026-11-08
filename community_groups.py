import streamlit as st
import uuid
from datetime import datetime, timedelta

def render_community_groups_page(*args, **kwargs):
    supabase = None
    user_id = None
    if len(args) >= 1:
        supabase = args[0]
    if len(args) >= 2:
        user_id = args[1]
    if "supabase" in kwargs:
        supabase = kwargs["supabase"]
    if "user_id" in kwargs:
        user_id = kwargs["user_id"]

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
            u = supabase.auth.get_user().user
            if u:
                uid = u.id
        except Exception:
            pass
    if not uid:
        st.warning("Login first to open Community.")
        return

    BUCKET = "community-media"

    # ============ BEIGE WHATSAPP BACKGROUND ============
    st.markdown("""
    <style>
    .stApp { background-color: #ECE5DD !important; }
    .main { background-color: #ECE5DD !important; }
    [data-testid="stAppViewContainer"] { background-color: #ECE5DD !important; }
    .wa-header { background:#075E54; color:white; padding:14px 16px; border-radius:12px 12px 0 0; font-weight:800; font-size:20px; }
    .wa-sub { background:#075E54; color:#D9FDD3; padding:0 16px 12px 16px; font-size:12px; border-radius:0 0 12px 12px; }
    .wa-bubble-mine { background:#D9FDD3; padding:8px 10px; border-radius:12px 12px 0 12px; margin:6px 0 6px 40px; }
    .wa-bubble-theirs { background:white; padding:8px 10px; border-radius:12px 12px 12px 0; margin:6px 40px 6px 0; border:1px solid #eee; }
    .wa-name { font-weight:800; font-size:13px; color:#075E54; }
    .wa-time { font-size:11px; color:#667781; text-align:right; }
    .wa-chat-header { background:#F0F2F5; padding:10px; border-radius:8px; }
    .wa-profile { background:white; padding:14px; border-radius:12px; border:1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="wa-header">♻️ EcoLoop Node Community</div><div class="wa-sub">Powered by Next Gen Impact Hub (NGIH) • Chats & Groups like WhatsApp • No Calls • No Audios</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # --- Helpers - USERNAMES ---
    def get_profile(uid2):
        try:
            r = supabase.table("profiles").select("*").eq("id", uid2).single().execute()
            return r.data or {}
        except Exception:
            return {}

    def get_name(p):
        u = p.get("username")
        if u:
            return f"@{u}"
        return p.get("display_name") or p.get("full_name") or p.get("email") or "User"

    def is_online(p):
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
                    return f"last seen {mins}m ago"
                return f"last seen {mins//60}h ago"
            except Exception:
                return "Offline"
        return "Offline"

    def storage_url(path):
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

    def upload(file, folder="chat"):
        try:
            ext = str(file.name).split(".")[-1].lower() if "." in str(file.name) else "jpg"
            path = f"{folder}/{uid}_{uuid.uuid4().hex[:8]}.{ext}"
            supabase.storage.from_(BUCKET).upload(path, file.getvalue(), {"content-type": file.type})
            return path
        except Exception as e:
            st.error(f"Upload failed: {e}")
            return None

    def fmt_time(ts):
        try:
            dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            return dt.strftime("%H:%M")
        except Exception:
            return ""

    # --- FOLLOWERS HELPERS - like we had with ChatGPT ---
    def get_follow_counts(uid2):
        try:
            f = supabase.table("followers").select("*").eq("following_id", uid2).execute().data or []
            fg = supabase.table("followers").select("*").eq("follower_id", uid2).execute().data or []
            return len(f), len(fg)
        except Exception:
            # fallback: if you used follows table
            try:
                f = supabase.table("follows").select("*").eq("following_id", uid2).execute().data or []
                fg = supabase.table("follows").select("*").eq("follower_id", uid2).execute().data or []
                return len(f), len(fg)
            except Exception:
                return 0, 0

    def is_following(uid2):
        try:
            r = supabase.table("followers").select("*").eq("follower_id", uid).eq("following_id", uid2).execute().data or []
            if r:
                return True
            r2 = supabase.table("follows").select("*").eq("follower_id", uid).eq("following_id", uid2).execute().data or []
            return bool(r2)
        except Exception:
            return False

    def follow_toggle(uid2):
        try:
            if is_following(uid2):
                try:
                    supabase.table("followers").delete().eq("follower_id", uid).eq("following_id", uid2).execute()
                except Exception:
                    supabase.table("follows").delete().eq("follower_id", uid).eq("following_id", uid2).execute()
            else:
                try:
                    supabase.table("followers").insert({"follower_id": uid, "following_id": uid2}).execute()
                except Exception:
                    supabase.table("follows").insert({"follower_id": uid, "following_id": uid2}).execute()
            st.rerun()
        except Exception as e:
            st.error(str(e))

    def show_profile_card(uid2):
        p = get_profile(uid2)
        followers_n, following_n = get_follow_counts(uid2)
        with st.container():
            st.markdown(f'<div class="wa-profile"><b style="font-size:18px;">{get_name(p)}</b><br><span style="color:#667781;">{p.get("display_name") or ""} • {is_online(p)}</span><br><b>{followers_n} Followers</b> • <b>{following_n} Following</b><br><span style="font-size:13px;">{p.get("bio") or ""}</span></div>', unsafe_allow_html=True)
            if str(uid2) != str(uid):
                if is_following(uid2):
                    if st.button(f"Unfollow {get_name(p)}", key=f"wa_unfollow_{uid2}"):
                        follow_toggle(uid2)
                else:
                    if st.button(f"Follow {get_name(p)}", key=f"wa_follow_{uid2}"):
                        follow_toggle(uid2)

    try:
        supabase.table("profiles").update({"is_online": True, "last_seen": "now()"}).eq("id", uid).execute()
    except Exception:
        pass

    # --- MY PROFILE ON TOP - with Followers ---
    my_p = get_profile(uid)
    my_f, my_fg = get_follow_counts(uid)
    st.markdown(f'<div class="wa-profile">👤 <b>{get_name(my_p)}</b> • {is_online(my_p)} &nbsp;|&nbsp; <b>{my_f} Followers</b> • <b>{my_fg} Following</b> &nbsp;|&nbsp; {my_p.get("bio") or "No bio yet"}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # --- Load My Groups + DMs ---
    try:
        mems = supabase.table("group_members").select("group_id").eq("user_id", uid).execute().data or []
        gids = [m.get("group_id") for m in mems]
        my_groups = supabase.table("groups").select("*").in_("id", gids).execute().data or [] if gids else []
    except Exception:
        my_groups = []
    try:
        my_dms = supabase.table("direct_chats").select("*").or_(f"user1.eq.{uid},user2.eq.{uid}").execute().data or []
    except Exception:
        my_dms = []

    chats = []
    for g in my_groups:
        chats.append({"type": "group", "id": g.get("id"), "name": g.get("name"), "code": g.get("invite_code"), "desc": g.get("description")})
    for d in my_dms:
        other = d.get("user2") if str(d.get("user1")) == str(uid) else d.get("user1")
        op = get_profile(other)
        chats.append({"type": "dm", "id": d.get("id"), "other_id": other, "name": get_name(op), "profile": op})

    if "wa_selected" not in st.session_state:
        st.session_state["wa_selected"] = None

    t1, t2, t3, t4 = st.tabs(["💬 Chats", "📸 Stories", "👥 People", "➕ New"])

    # ================= NEW =================
    with t4:
        st.markdown("### ➕ New Group — like WhatsApp")
        gname = st.text_input("Group Name", key="wa_new_group_name", placeholder="e.g. Harare Clean-Up Team")
        gdesc = st.text_input("Group Description (optional)", key="wa_new_group_desc")
        if st.button("✅ Create Group", use_container_width=True):
            if not gname.strip():
                st.error("Enter group name")
            else:
                try:
                    code = str(uuid.uuid4())[:8].upper()
                    r = supabase.table("groups").insert({"name": gname.strip(), "description": gdesc, "created_by": uid, "invite_code": code}).execute()
                    gid = r.data[0].get("id")
                    supabase.table("group_members").insert({"group_id": gid, "user_id": uid, "role": "Admin"}).execute()
                    st.success(f"Group created! Invite Code: {code}")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        st.divider()
        st.markdown("### 🔗 Join Group via Invite Code")
        code_in = st.text_input("Paste Invite Code", key="wa_join_code")
        if st.button("Join Group"):
            try:
                r = supabase.table("groups").select("*").eq("invite_code", code_in.strip().upper()).single().execute()
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
        st.divider()
        st.markdown("### 👤 New Chat — Search by @username")
        search_new = st.text_input("Search @username", key="wa_search_new", placeholder="@munashe")
        if search_new.strip():
            try:
                q = search_new.replace("@", "")
                found = supabase.table("profiles").select("*").or_(f"username.ilike.%{q}%,display_name.ilike.%{q}%,full_name.ilike.%{q}%").limit(10).execute().data or []
                for f in found:
                    if str(f.get("id")) == str(uid):
                        continue
                    if st.button(f"💬 {get_name(f)} — {is_online(f)}", key=f"wa_new_dm_{f.get('id')}"):
                        try:
                            ex = supabase.table("direct_chats").select("*").or_(f"and(user1.eq.{uid},user2.eq.{f.get('id')}),and(user1.eq.{f.get('id')},user2.eq.{uid})").execute().data or []
                            if ex:
                                chat_id = ex[0].get("id")
                            else:
                                r2 = supabase.table("direct_chats").insert({"user1": uid, "user2": f.get("id")}).execute()
                                chat_id = r2.data[0].get("id")
                            st.session_state["wa_selected"] = {"type": "dm", "id": chat_id, "other_id": str(f.get("id")), "name": get_name(f)}
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
            except Exception as e:
                st.error(str(e))

    # ================= PEOPLE - FOLLOWERS =================
    with t3:
        st.markdown("### 👥 People — Followers / Following")
        pq = st.text_input("Search @username", key="wa_people_search", placeholder="@username")
        if pq.strip():
            try:
                q = pq.replace("@", "")
                found = supabase.table("profiles").select("*").or_(f"username.ilike.%{q}%,display_name.ilike.%{q}%").limit(10).execute().data or []
                for f in found:
                    if str(f.get("id")) == str(uid):
                        continue
                    show_profile_card(f.get("id"))
            except Exception as e:
                st.error(str(e))
        else:
            st.write("Search someone to see their Followers / Following and Follow them.")

    # ================= STORIES - WITH VIEWS =================
    with t2:
        st.markdown("### 📸 Stories — 24 hours")
        sf = st.file_uploader("Post Story Photo/Video", type=["jpg", "jpeg", "png", "mp4", "mov", "webp"], key="wa_story_file")
        scap = st.text_input("Caption", key="wa_story_cap")
        if st.button("Post Story"):
            if sf is None:
                st.error("Pick photo first")
            else:
                path = upload(sf, "stories")
                if path:
                    try:
                        supabase.table("stories").insert({"user_id": uid, "media_url": path, "media_type": "video" if str(sf.type).startswith("video") else "image", "caption": scap, "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()}).execute()
                        st.success("Story posted!")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
        try:
            all_st = supabase.table("stories").select("*").order("created_at", desc=True).limit(50).execute().data or []
        except Exception:
            all_st = []
        seen_users = []
        for s in all_st:
            try:
                if s.get("expires_at") and datetime.fromisoformat(str(s.get("expires_at")).replace("Z", "+00:00")) < datetime.now().astimezone():
                    continue
            except Exception:
                pass
            if s.get("user_id") in seen_users:
                continue
            seen_users.append(s.get("user_id"))
            p = get_profile(s.get("user_id"))
            # Count views for this user's stories
            try:
                v_ids = [x.get("id") for x in all_st if x.get("user_id") == s.get("user_id")]
                views = supabase.table("story_views").select("*").in_("story_id", v_ids).execute().data or []
                views_n = len(views)
            except Exception:
                views = []
                views_n = 0
            with st.expander(f"📸 {get_name(p)} — 👁️ {views_n} views — {is_online(p)}"):
                # Profile card with followers inside story
                show_profile_card(s.get("user_id"))
                for us in [x for x in all_st if x.get("user_id") == s.get("user_id")]:
                    # Record view - if not owner
                    if str(us.get("user_id")) != str(uid):
                        try:
                            supabase.table("story_views").insert({"story_id": us.get("id"), "viewer_id": uid}).execute()
                        except Exception:
                            pass
                    if us.get("caption"):
                        st.write(us.get("caption"))
                    url = storage_url(us.get("media_url"))
                    if us.get("media_type") == "video":
                        st.video(url)
                    else:
                        st.image(url, width=300)
                    # Views for this single story
                    try:
                        sv = supabase.table("story_views").select("*").eq("story_id", us.get("id")).execute().data or []
                        st.caption(f"👁️ {len(sv)} views")
                        if str(us.get("user_id")) == str(uid):
                            for vv in sv:
                                vp = get_profile(vv.get("viewer_id"))
                                st.write(f"👁️ Viewed by {get_name(vp)}")
                    except Exception:
                        pass

    # ================= CHATS =================
    with t1:
        col_list, col_chat = st.columns([1, 2])
        with col_list:
            st.markdown("**Chats**")
            st.text_input("🔍 Search", key="wa_search_chats", label_visibility="collapsed", placeholder="Search")
            search_q = st.session_state.get("wa_search_chats", "").lower().replace("@", "")
            if not chats:
                st.info("No chats yet. Go to ➕ New to create a group or DM.")
            for c in chats:
                if search_q and search_q not in c.get("name", "").lower().replace("@", ""):
                    continue
                label = f"👥 {c.get('name')}" if c["type"] == "group" else f"👤 {c.get('name')}"
                if st.button(label, key=f"wa_list_{c['type']}_{c['id']}", use_container_width=True):
                    st.session_state["wa_selected"] = c
                    st.rerun()
        with col_chat:
            sel = st.session_state.get("wa_selected")
            if not sel:
                st.markdown("""
                <div style="background:#F0F2F5; padding:40px; text-align:center; border-radius:12px;">
                <h3>💬 EcoLoop Node Community</h3>
                <p>Select a chat on the left<br>or create a new group / DM in ➕ New</p>
                <p>Send photos, messages, react — like WhatsApp.<br>No calls, no audios.</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                if sel["type"] == "group":
                    st.markdown(f'<div class="wa-chat-header"><b>👥 {sel.get("name")}</b><br><span style="font-size:12px;">Invite Code: {sel.get("code") or ""} • Tap ⋮ for Group Info</span></div>', unsafe_allow_html=True)
                    with st.expander("⋮ Group Info — Members, Add / Remove / Make Admin"):
                        st.write(f"Description: {sel.get('desc') or ''}")
                        st.code(f"Invite Code: {sel.get('code') or ''}", language="text")
                        try:
                            me = supabase.table("group_members").select("*").eq("group_id", sel["id"]).eq("user_id", uid).single().execute().data or {}
                            is_admin = me.get("role") == "Admin"
                        except Exception:
                            is_admin = False
                        st.write(f"You are: **{'👑 Admin' if is_admin else 'Member'}**")
                        if is_admin:
                            st.markdown("**➕ Add Participant — like WhatsApp**")
                            add_q = st.text_input("Search @username to add", key=f"wa_add_{sel['id']}", placeholder="@username")
                            if add_q.strip():
                                try:
                                    q2 = add_q.replace("@", "")
                                    found = supabase.table("profiles").select("*").or_(f"username.ilike.%{q2}%,display_name.ilike.%{q2}%").limit(5).execute().data or []
                                    for f in found:
                                        if str(f.get("id")) == str(uid):
                                            continue
                                        if st.button(f"➕ Add {get_name(f)}", key=f"wa_add_btn_{sel['id']}_{f.get('id')}"):
                                            try:
                                                supabase.table("group_members").insert({"group_id": sel["id"], "user_id": f.get("id"), "role": "Member"}).execute()
                                                st.success(f"Added {get_name(f)}")
                                                st.rerun()
                                            except Exception:
                                                st.error("Already in group")
                                except Exception as e:
                                    st.error(str(e))
                        try:
                            members = supabase.table("group_members").select("*").eq("group_id", sel["id"]).execute().data or []
                            st.markdown(f"**Participants ({len(members)})**")
                            for mm in members:
                                pp = get_profile(mm.get("user_id"))
                                mf, mfg = get_follow_counts(mm.get("user_id"))
                                c1, c2, c3 = st.columns([3, 1, 1])
                                with c1:
                                    st.write(f"{get_name(pp)} — {mm.get('role')} — {is_online(pp)} — {mf} Followers")
                                if is_admin and str(mm.get("user_id")) != str(uid):
                                    with c2:
                                        if mm.get("role") != "Admin":
                                            if st.button("Make Admin", key=f"wa_mkadmin_{sel['id']}_{mm.get('user_id')}"):
                                                supabase.table("group_members").update({"role": "Admin"}).eq("group_id", sel["id"]).eq("user_id", mm.get("user_id")).execute()
                                                st.rerun()
                                        else:
                                            if st.button("Remove Admin", key=f"wa_rmadmin_{sel['id']}_{mm.get('user_id')}"):
                                                supabase.table("group_members").update({"role": "Member"}).eq("group_id", sel["id"]).eq("user_id", mm.get("user_id")).execute()
                                                st.rerun()
                                    with c3:
                                        if st.button("Remove", key=f"wa_rem_{sel['id']}_{mm.get('user_id')}"):
                                            supabase.table("group_members").delete().eq("group_id", sel["id"]).eq("user_id", mm.get("user_id")).execute()
                                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
                        st.divider()
                        if is_admin:
                            if st.button("🗑️ Delete Group", key=f"wa_del_group_{sel['id']}"):
                                supabase.table("group_members").delete().eq("group_id", sel["id"]).execute()
                                try:
                                    supabase.table("group_messages").delete().eq("group_id", sel["id"]).execute()
                                except Exception:
                                    pass
                                supabase.table("groups").delete().eq("id", sel["id"]).execute()
                                st.session_state["wa_selected"] = None
                                st.rerun()
                        else:
                            if st.button("🚪 Exit Group", key=f"wa_exit_{sel['id']}"):
                                supabase.table("group_members").delete().eq("group_id", sel["id"]).eq("user_id", uid).execute()
                                st.session_state["wa_selected"] = None
                                st.rerun()
                    try:
                        msgs = supabase.table("group_messages").select("*").eq("group_id", sel["id"]).order("created_at").execute().data or []
                    except Exception:
                        msgs = []
                    for m in msgs:
                        p = get_profile(m.get("sender_id"))
                        mine = str(m.get("sender_id")) == str(uid)
                        tick = " ✓✓" if m.get("status") == "read" else " ✓"
                        bubble_class = "wa-bubble-mine" if mine else "wa-bubble-theirs"
                        name_html = "" if mine else f'<div class="wa-name">{get_name(p)}</div>'
                        st.markdown(f'<div class="{bubble_class}">{name_html}<div>{m.get("message_text") or ""}</div><div class="wa-time">{fmt_time(m.get("created_at"))}{tick if mine else ""}</div></div>', unsafe_allow_html=True)
                        if m.get("media_url"):
                            url = storage_url(m.get("media_url"))
                            if m.get("media_type") == "video":
                                st.video(url)
                            else:
                                st.image(url, width=250)
                        try:
                            reacts = supabase.table("group_message_reactions").select("*").eq("message_id", m.get("id")).execute().data or []
                        except Exception:
                            reacts = []
                        if reacts:
                            counts = {}
                            for x in reacts:
                                counts[x.get("emoji")] = counts.get(x.get("emoji"), 0) + 1
                            st.caption(" ".join([f"{k} {v}" for k, v in counts.items()]))
                        rc = st.columns(6)
                        for i, em in enumerate(["❤️", "😂", "🔥", "👍", "😮", "😢"]):
                            with rc[i]:
                                if st.button(em, key=f"wa_greact_{m.get('id')}_{em}"):
                                    try:
                                        supabase.table("group_message_reactions").delete().eq("message_id", m.get("id")).eq("user_id", uid).execute()
                                    except Exception:
                                        pass
                                    try:
                                        supabase.table("group_message_reactions").insert({"message_id": m.get("id"), "user_id": uid, "emoji": em}).execute()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(str(e))
                    msg_in = st.text_input("Message", key=f"wa_gmsg_{sel['id']}", label_visibility="collapsed", placeholder="Type a message...")
                    up = st.file_uploader("Photo", type=["jpg", "jpeg", "png", "mp4", "mov", "webp"], key=f"wa_gup_{sel['id']}", label_visibility="collapsed")
                    if st.button("➤ Send", key=f"wa_gsend_{sel['id']}", use_container_width=True):
                        mp = None
                        mt = None
                        if up is not None:
                            mp = upload(up, "group_chat")
                            mt = "video" if str(up.type).startswith("video") else "image"
                        if msg_in.strip() or mp:
                            supabase.table("group_messages").insert({"group_id": sel["id"], "sender_id": uid, "message_text": msg_in.strip(), "status": "sent", "media_url": mp, "media_type": mt}).execute()
                            st.rerun()
                else:
                    op = get_profile(sel.get("other_id"))
                    st.markdown(f'<div class="wa-chat-header"><b>👤 {get_name(op)}</b><br><span style="font-size:12px;">{is_online(op)}</span></div>', unsafe_allow_html=True)
                    show_profile_card(sel.get("other_id"))
                    chat_id = sel["id"]
                    try:
                        dmsgs = supabase.table("messages").select("*").eq("chat_id", chat_id).order("created_at").execute().data or []
                    except Exception:
                        try:
                            dmsgs = supabase.table("direct_messages").select("*").eq("chat_id", chat_id).order("created_at").execute().data or []
                        except Exception:
                            dmsgs = []
                    for m in dmsgs:
                        sender = m.get("sender_id") or m.get("user_id")
                        mine = str(sender) == str(uid)
                        p = get_profile(sender)
                        tick = " ✓✓" if m.get("status") == "read" else " ✓"
                        bubble_class = "wa-bubble-mine" if mine else "wa-bubble-theirs"
                        name_html = "" if mine else f'<div class="wa-name">{get_name(p)}</div>'
                        st.markdown(f'<div class="{bubble_class}">{name_html}<div>{m.get("message_text") or m.get("content") or ""}</div><div class="wa-time">{fmt_time(m.get("created_at"))}{tick if mine else ""}</div></div>', unsafe_allow_html=True)
                        if m.get("media_url"):
                            st.image(storage_url(m.get("media_url")), width=250)
                    dm_in = st.text_input("Message", key=f"wa_dm_{chat_id}", label_visibility="collapsed", placeholder="Type a message...")
                    dm_up = st.file_uploader("Photo", type=["jpg", "jpeg", "png", "mp4", "mov", "webp"], key=f"wa_dmup_{chat_id}", label_visibility="collapsed")
                    if st.button("➤ Send", key=f"wa_dmsend_{chat_id}", use_container_width=True):
                        mp = None
                        mt = None
                        if dm_up is not None:
                            mp = upload(dm_up, "dm_chat")
                            mt = "video" if str(dm_up.type).startswith("video") else "image"
                        if dm_in.strip() or mp:
                            try:
                                supabase.table("messages").insert({"chat_id": chat_id, "sender_id": uid, "message_text": dm_in.strip(), "status": "sent", "media_url": mp, "media_type": mt}).execute()
                            except Exception:
                                supabase.table("direct_messages").insert({"chat_id": chat_id, "sender_id": uid, "message_text": dm_in.strip(), "status": "sent", "media_url": mp}).execute()
                            st.rerun()
