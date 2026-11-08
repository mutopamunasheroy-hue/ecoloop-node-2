import streamlit as st
import uuid
import html
from datetime import datetime, timedelta, timezone

def render_community_groups_page(*args, **kwargs):
    supabase = kwargs.get("supabase") or (args[0] if len(args) >= 1 else st.session_state.get("supabase_client"))
    uid = kwargs.get("user_id") or (args[1] if len(args) >= 2 else None) or st.session_state.get("uid") or st.session_state.get("user_id")
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

    # ===== ECOLOOP COMMUNITY HUB - BEIGE #ECE5DD =====
    st.markdown("""
    <style>
    .stApp, [data-testid="stAppViewContainer"] { background-color: #ECE5DD !important; }
    .eco-head { background:#075E54; color:white; padding:12px 16px; border-radius:12px 12px 0 0; font-weight:800; font-size:20px; }
    .eco-sub { background:#075E54; color:#D9FDD3; padding:0 16px 12px 16px; font-size:12px; border-radius:0 0 12px 12px; }
    .bubble-mine { background:#D9FDD3; padding:8px 10px; border-radius:12px 12px 0 12px; margin:6px 0 6px 40px; }
    .bubble-theirs { background:white; padding:8px 10px; border-radius:12px 12px 12px 0; margin:6px 40px 6px 0; border:1px solid #eee; }
    .name { font-weight:800; font-size:13px; color:#075E54; }
    .time { font-size:11px; color:#667781; text-align:right; }
    .chat-head { background:#F0F2F5; padding:10px; border-radius:10px; }
    .prof { background:white; padding:14px; border-radius:12px; border:1px solid #ddd; }
    .pending-box { background:#FFF3CD; padding:10px; border-radius:10px; border:1px solid #FFC107; }
    .notice-box { background:#D1E7DD; padding:10px; border-radius:10px; border:1px solid #198754; }
    </style>
    """, unsafe_allow_html=True)

    if "eco_notice" not in st.session_state:
        st.session_state["eco_notice"] = None
    if "eco_last_created" not in st.session_state:
        st.session_state["eco_last_created"] = None
    if "eco_sel" not in st.session_state:
        st.session_state["eco_sel"] = None
    if "forward_msg" not in st.session_state:
        st.session_state["forward_msg"] = None
    if "forward_meta" not in st.session_state:
        st.session_state["forward_meta"] = None
    if "incomplete_room" not in st.session_state:
        st.session_state["incomplete_room"] = None

    def set_notice(msg):
        st.session_state["eco_notice"] = msg

    # ===== NAVIGATION =====
    c_back, c_title = st.columns([1, 5])
    with c_back:
        if st.button("⬅ Back", use_container_width=True, key="eco_back_top"):
            if st.session_state.get("eco_sel"):
                st.session_state["eco_sel"] = None
                st.rerun()
            else:
                st.session_state["page"] = "dashboard"
                st.session_state["current_page"] = "dashboard"
                st.rerun()
    with c_title:
        st.markdown('<div class="eco-head">♻️ EcoLoop Community Hub</div>', unsafe_allow_html=True)
    st.markdown('<div class="eco-sub">Next Gen Impact Hub (NGIH) • Chat Rooms • Stories • People</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state.get("eco_notice"):
        st.markdown(f'<div class="notice-box">{html.escape(str(st.session_state["eco_notice"]))}</div>', unsafe_allow_html=True)
        if st.button("Dismiss", key="dismiss_notice"):
            st.session_state["eco_notice"] = None
            st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)

    # ===== HELPERS =====
    def esc(v):
        return html.escape(str(v if v is not None else ""), quote=True)

    def is_admin_role(role):
        return str(role or "").strip().lower() == "admin"

    def is_approved_status(status):
        return str(status or "").strip().lower() == "approved"

    def get_profile(uid2):
        if not uid2:
            return {}
        try:
            r = supabase.table("member_profiles").select("*").eq("user_id", uid2).single().execute()
            return r.data or {}
        except Exception:
            return {}

    def get_name(p):
        u = (p.get("username") or "").strip()
        if u:
            return f"@{u}"
        return p.get("display_name") or "User"

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

    def upload(file, folder):
        try:
            ext = str(file.name).split(".")[-1].lower() if "." in str(file.name) else "jpg"
            path = f"{uid}/{folder}/{uuid.uuid4().hex[:12]}.{ext}"
            supabase.storage.from_(BUCKET).upload(path, file.getvalue(), {"content-type": file.type})
            return path
        except Exception as e:
            st.error(f"Upload failed: {e}. Check that your existing community-media policy allows uploads to your own folder.")
            return None

    def fmt_time(ts):
        try:
            return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).strftime("%H:%M")
        except Exception:
            return ""

    def get_app_url():
        try:
            headers = st.context.headers
            host = headers.get("host") or headers.get("Host") or ""
            if not host:
                return None
            proto = headers.get("x-forwarded-proto") or headers.get("X-Forwarded-Proto") or ""
            if isinstance(proto, str) and "," in proto:
                proto = proto.split(",")[0].strip()
            if not proto:
                proto = "http" if "localhost" in host or "127.0.0.1" in host else "https"
            return f"{proto}://{host}"
        except Exception:
            return None

    def show_profile_card(uid2):
        p = get_profile(uid2)
        av = p.get("avatar_url") or ""
        img = f'<img src="{esc(av)}" width="60" style="border-radius:50%;">' if av else ""
        st.markdown(
            f'<div class="prof">{img}<br><b style="font-size:18px;">{esc(get_name(p))}</b><br>'
            f'<span style="color:#667781;">{esc(p.get("display_name") or "")}</span><br>'
            f'<span style="font-size:13px;">{esc(p.get("bio") or "")}</span><br>'
            f'<span style="font-size:12px;">📍 {esc(p.get("location") or "")} • {esc(p.get("country_of_origin") or "")}</span></div>',
            unsafe_allow_html=True,
        )

    def search_by_username(q_raw, limit=20):
        q = (q_raw or "").strip().replace("@", "").strip()
        if not q:
            return []
        try:
            res = supabase.table("member_profiles").select("*").ilike("username", f"%{q}%").limit(limit).execute().data or []
        except Exception as e:
            st.error(f"Username search failed: {e}")
            return []
        ql = q.lower()
        starts = [r for r in res if (r.get("username") or "").lower().startswith(ql)]
        others = [r for r in res if r not in starts]
        starts.sort(key=lambda r: (r.get("username") or "").lower())
        others.sort(key=lambda r: (r.get("username") or "").lower())
        return starts + others

    # ===== INVITATION LINK: ?room=CODE =====
    try:
        qp = st.query_params
        room_code_param = qp.get("room", None)
        if isinstance(room_code_param, list):
            room_code_param = room_code_param[0] if room_code_param else None
    except Exception:
        room_code_param = None

    if room_code_param:
        clean = str(room_code_param).strip().upper()
        st.info(f"You opened an invitation for Chat Room code: {esc(clean)}")
        try:
            r = supabase.table("community_groups").select("*").eq("invite_code", clean).single().execute()
            if r.data:
                st.write(f"Chat Room: **{esc(r.data.get('name'))}** — {esc(r.data.get('description') or '')}")
                try:
                    ex = supabase.table("group_memberships").select("*").eq("group_id", r.data.get("id")).eq("user_id", uid).execute().data or []
                except Exception:
                    ex = []
                if ex:
                    status = str(ex[0].get("status") or "").strip().lower()
                    role = ex[0].get("membership_role") or ""
                    st.write(f"Your membership status: **{esc(ex[0].get('status'))}** / {esc(role)}")
                    if status == "pending":
                        st.warning("Your membership is pending approval. You cannot send messages yet. Please wait for the creator to approve you.")
                    elif status == "approved":
                        if st.button("Open This Chat Room", key="open_invited_room"):
                            st.session_state["eco_sel"] = {"type": "room", "id": r.data.get("id"), "name": r.data.get("name"), "code": r.data.get("invite_code"), "desc": r.data.get("description"), "created_by": r.data.get("created_by"), "my_role": role, "my_status": ex[0].get("status")}
                            st.rerun()
                    else:
                        st.warning(f"Your membership status is '{esc(ex[0].get('status'))}'. You are not approved to participate yet.")
                else:
                    if st.button("Request to Join This Chat Room", key="join_invited_room"):
                        try:
                            supabase.table("group_memberships").insert({"group_id": r.data.get("id"), "user_id": uid, "membership_role": "member", "status": "pending"}).execute()
                            set_notice("Join request sent — waiting for creator approval (status: pending).")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Join request failed: {e} — you may not have permission under the existing RLS policy.")
            else:
                st.error("Invitation code not found.")
        except Exception as e:
            st.error(f"Could not load invitation: {e}")

    my_p = get_profile(uid)
    st.markdown(f'<div class="prof">👤 <b>{esc(get_name(my_p))}</b> • {esc(my_p.get("display_name") or "")}<br><span style="font-size:13px;">{esc(my_p.get("bio") or "No bio yet")}</span></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ===== LOAD CHAT ROOMS + PRIVATE CONVERSATIONS =====
    try:
        mems = supabase.table("group_memberships").select("group_id,membership_role,status").eq("user_id", uid).execute().data or []
        gids = [m.get("group_id") for m in mems]
        my_rooms = supabase.table("community_groups").select("*").in_("id", gids).execute().data or [] if gids else []
        my_membership_map = {m.get("group_id"): m for m in mems}
    except Exception as e:
        st.error(f"Could not load your Chat Rooms: {e}")
        my_rooms = []
        my_membership_map = {}

    try:
        my_dms = supabase.table("direct_conversations").select("*").or_(f"user_one_id.eq.{uid},user_two_id.eq.{uid}").execute().data or []
    except Exception as e:
        st.error(f"Could not load private conversations: {e}")
        my_dms = []

    chats = []
    for g in my_rooms:
        mm = my_membership_map.get(g.get("id"), {})
        chats.append({"type": "room", "id": g.get("id"), "name": g.get("name"), "code": g.get("invite_code"), "desc": g.get("description"), "created_by": g.get("created_by"), "my_role": mm.get("membership_role"), "my_status": mm.get("status")})
    for d in my_dms:
        other = d.get("user_two_id") if str(d.get("user_one_id")) == str(uid) else d.get("user_one_id")
        op = get_profile(other)
        chats.append({"type": "dm", "id": d.get("id"), "other_id": other, "name": get_name(op)})

    if st.session_state.get("incomplete_room"):
        inc = st.session_state["incomplete_room"]
        st.warning(f"Chat Room '{esc(inc.get('name'))}' was created (code {esc(inc.get('code'))}) but your creator membership was NOT saved. You may not be able to manage it until membership is fixed.")
        if st.button("Retry Creator Membership", key="retry_incomplete_membership"):
            try:
                supabase.table("group_memberships").insert({"group_id": inc.get("id"), "user_id": uid, "membership_role": "admin", "status": "approved"}).execute()
                st.session_state["incomplete_room"] = None
                set_notice("Creator membership fixed.")
                st.rerun()
            except Exception as e:
                st.error(f"Retry failed — check RLS: {e}")

    if st.session_state.get("eco_last_created"):
        lc = st.session_state["eco_last_created"]
        st.markdown(f'<div class="notice-box">✅ Chat Room created: <b>{esc(lc.get("name"))}</b><br>Invite Code: <b>{esc(lc.get("code"))}</b></div>', unsafe_allow_html=True)
        app_url_lc = get_app_url()
        if app_url_lc and lc.get("code"):
            st.code(f"{app_url_lc}/?room={lc.get('code')}", language="text")
        else:
            st.code(f"?room={lc.get('code') or ''}", language="text")
            st.caption("Share link: copy your app URL from the browser and add ?room=CODE")
        if st.button("Hide This Invite", key="hide_last_created"):
            st.session_state["eco_last_created"] = None
            st.rerun()

    t1, t2, t3, t4 = st.tabs(["💬 Chats", "📸 Stories", "👥 People", "➕ New"])

    # ===== NEW =====
    with t4:
        st.markdown("### ➕ New Chat Room")
        gname = st.text_input("Chat Room Name", key="new_room_name", placeholder="e.g. Harare Clean-Up Team")
        gdesc = st.text_input("Description (optional)", key="new_room_desc")
        if st.button("✅ Create Chat Room", use_container_width=True, key="create_room_btn"):
            if not gname.strip():
                st.error("Enter Chat Room name")
            else:
                gid = None
                code = str(uuid.uuid4())[:8].upper()
                try:
                    r = supabase.table("community_groups").insert({"name": gname.strip(), "description": gdesc, "created_by": uid, "invite_code": code}).execute()
                    gid = r.data[0].get("id")
                except Exception as e:
                    st.error(f"Create Chat Room failed: {e}")
                    gid = None
                if gid:
                    try:
                        supabase.table("group_memberships").insert({"group_id": gid, "user_id": uid, "membership_role": "admin", "status": "approved"}).execute()
                        st.session_state["eco_last_created"] = {"id": gid, "name": gname.strip(), "code": code}
                        st.session_state["incomplete_room"] = None
                        set_notice(f"Chat Room '{gname.strip()}' created! Invite Code: {code} — share link shown above.")
                        st.rerun()
                    except Exception as e:
                        st.session_state["incomplete_room"] = {"id": gid, "name": gname.strip(), "code": code}
                        st.error(f"Chat Room row was created (code {code}) but creator membership could NOT be saved: {e}. The Chat Room is in an incomplete state. Use 'Retry Creator Membership' above.")
        st.divider()
        st.markdown("### 🔗 Join Chat Room via Link / Code")
        code_in = st.text_input("Paste Invite Code or Link", key="join_room_code", placeholder="ABC12345 or ?room=ABC12345")
        if st.button("Request to Join Chat Room", key="join_room_btn"):
            clean = code_in.strip().upper()
            if "ROOM=" in clean:
                clean = clean.split("ROOM=")[-1].split("&")[0].split("/")[0].strip()
            else:
                clean = clean.split("/")[-1].strip()
            if not clean:
                st.error("Enter a code")
            else:
                try:
                    r = supabase.table("community_groups").select("*").eq("invite_code", clean).single().execute()
                    if r.data:
                        try:
                            supabase.table("group_memberships").insert({"group_id": r.data.get("id"), "user_id": uid, "membership_role": "member", "status": "pending"}).execute()
                            set_notice(f"Join request sent to {r.data.get('name')} — status: pending. The creator must approve you.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Join request failed: {e}")
                    else:
                        st.error("Code not found")
                except Exception as e:
                    st.error(f"Join failed: {e}")
        st.divider()
        st.markdown("### 👤 New Chat — Search by @username ONLY")
        sq = st.text_input("Search @username", key="search_new_user", placeholder="@roy or roy")
        if sq.strip():
            found = search_by_username(sq, limit=20)
            if not found:
                st.info("No user with that @username")
            for f in found:
                if str(f.get("user_id")) == str(uid):
                    continue
                label = f"💬 {get_name(f)} — {f.get('display_name') or ''}"
                if st.button(label, key=f"newdm_{f.get('user_id')}"):
                    try:
                        ex = supabase.table("direct_conversations").select("*").or_(f"and(user_one_id.eq.{uid},user_two_id.eq.{f.get('user_id')}),and(user_one_id.eq.{f.get('user_id')},user_two_id.eq.{uid})").execute().data or []
                        if ex:
                            chat_id = ex[0].get("id")
                        else:
                            chat_id = supabase.table("direct_conversations").insert({"user_one_id": uid, "user_two_id": f.get("user_id")}).execute().data[0].get("id")
                        st.session_state["eco_sel"] = {"type": "dm", "id": chat_id, "other_id": str(f.get("user_id")), "name": get_name(f)}
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not start private conversation: {e}")

    # ===== PEOPLE =====
    with t3:
        st.markdown("### 👥 People — Search by @username")
        pq = st.text_input("Search @username", key="people_search_user", placeholder="roy")
        if pq.strip():
            found = search_by_username(pq, limit=20)
            for f in found:
                if str(f.get("user_id")) == str(uid):
                    continue
                show_profile_card(f.get("user_id"))
                if st.button(f"💬 Message {get_name(f)}", key=f"people_msg_{f.get('user_id')}"):
                    try:
                        ex = supabase.table("direct_conversations").select("*").or_(f"and(user_one_id.eq.{uid},user_two_id.eq.{f.get('user_id')}),and(user_one_id.eq.{f.get('user_id')},user_two_id.eq.{uid})").execute().data or []
                        if ex:
                            chat_id = ex[0].get("id")
                        else:
                            chat_id = supabase.table("direct_conversations").insert({"user_one_id": uid, "user_two_id": f.get("user_id")}).execute().data[0].get("id")
                        st.session_state["eco_sel"] = {"type": "dm", "id": chat_id, "other_id": str(f.get("user_id")), "name": get_name(f)}
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not start private conversation: {e}")
        else:
            st.write("Search someone by part of their unique @username. Example: roy")

    # ===== STORIES =====
    with t2:
        st.markdown("### 📸 Stories — 24 hours")
        sf = st.file_uploader("Post Story Photo/Video", type=["jpg", "jpeg", "png", "mp4", "mov", "webp"], key="story_file")
        scap = st.text_input("Caption", key="story_cap")
        if st.button("Post Story", key="post_story_btn"):
            if sf is None:
                st.error("Pick photo first")
            else:
                path = upload(sf, "stories")
                if path:
                    try:
                        supabase.table("stories").insert({"user_id": uid, "media_url": path, "media_type": "video" if str(sf.type).startswith("video") else "image", "caption": scap, "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()}).execute()
                        set_notice("Story posted!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Post Story failed: {e}")
        try:
            all_st = supabase.table("stories").select("*").order("created_at", desc=True).limit(50).execute().data or []
        except Exception as e:
            st.error(f"Could not load Stories: {e}")
            all_st = []
        now_utc = datetime.now(timezone.utc)
        seen = []
        for s in all_st:
            try:
                exp = datetime.fromisoformat(str(s.get("expires_at")).replace("Z", "+00:00"))
                if exp < now_utc:
                    continue
            except Exception:
                continue
            if s.get("user_id") in seen:
                continue
            seen.append(s.get("user_id"))
            p = get_profile(s.get("user_id"))
            is_owner = str(s.get("user_id")) == str(uid)
            header = f"📸 {esc(get_name(p))}"
            if is_owner:
                try:
                    v_ids_owner = [x.get("id") for x in all_st if x.get("user_id") == s.get("user_id")]
                    views_owner = supabase.table("story_views").select("*").in_("story_id", v_ids_owner).execute().data or [] if v_ids_owner else []
                    header += f" — 👁️ {len(views_owner)} visible views"
                except Exception:
                    header += " — 👁️ views unavailable"
            with st.expander(header):
                show_profile_card(s.get("user_id"))
                for us in [x for x in all_st if x.get("user_id") == s.get("user_id")]:
                    if str(us.get("user_id")) != str(uid):
                        try:
                            existing = supabase.table("story_views").select("id").eq("story_id", us.get("id")).eq("viewer_id", uid).execute().data or []
                            if not existing:
                                supabase.table("story_views").insert({"story_id": us.get("id"), "viewer_id": uid}).execute()
                        except Exception as e:
                            st.error(f"Could not record Story view: {e}")
                    if us.get("caption"):
                        st.write(esc(us.get("caption")))
                    url = storage_url(us.get("media_url"))
                    if us.get("media_type") == "video":
                        st.video(url)
                    else:
                        st.image(url, width=300)
                    if is_owner:
                        try:
                            sv = supabase.table("story_views").select("*").eq("story_id", us.get("id")).execute().data or []
                            st.caption(f"👁️ {len(sv)} visible views (limited by privacy / RLS)")
                            for vv in sv:
                                vp = get_profile(vv.get("viewer_id"))
                                st.write(f"👁️ Viewed by {esc(get_name(vp))}")
                        except Exception as e:
                            st.error(f"Could not load Story views: {e}")
                    else:
                        st.caption("👁️ Views are only visible to the Story owner.")

    # ===== FORWARD BAR =====
    if st.session_state.get("forward_msg") is not None:
        fm = st.session_state.get("forward_msg") or ""
        meta = st.session_state.get("forward_meta") or {}
        has_att = bool(meta.get("attachment_path"))
        src = meta.get("source_type") or ""
        st.info(f"Forwarding from {esc(src)}: {esc(fm[:80])}{' + attachment' if has_att else ' (text only)'} — pick a Chat Room / DM below, then tap Forward")
        if st.button("Cancel Forward", key="cancel_forward"):
            st.session_state["forward_msg"] = None
            st.session_state["forward_meta"] = None
            st.rerun()

    # ===== CHATS =====
    with t1:
        col_list, col_chat = st.columns([1, 2])
        with col_list:
            st.markdown("**Chats**")
            st.text_input("🔍 Search", key="search_chats", label_visibility="collapsed", placeholder="Search @username or Chat Room")
            sq2 = st.session_state.get("search_chats", "").lower().replace("@", "")
            if not chats:
                st.info("No chats yet. Go to ➕ New to create a Chat Room or DM.")
            for c in chats:
                if sq2 and sq2 not in c.get("name", "").lower().replace("@", ""):
                    continue
                icon = "👥" if c["type"] == "room" else "👤"
                suffix = ""
                if c["type"] == "room" and str(c.get("my_status") or "").lower() == "pending":
                    suffix = " (pending approval)"
                if st.button(f"{icon} {c.get('name')}{suffix}", key=f"list_{c['type']}_{c['id']}", use_container_width=True):
                    st.session_state["eco_sel"] = c
                    st.rerun()
                if st.session_state.get("forward_msg") is not None and st.button(f"➡️ Forward here → {c.get('name')}", key=f"fwd_{c['type']}_{c['id']}"):
                    txt = st.session_state.get("forward_msg") or ""
                    meta = st.session_state.get("forward_meta") or {}
                    try:
                        if c["type"] == "room":
                            supabase.table("group_messages").insert({
                                "group_id": c["id"], "sender_id": uid, "message_text": txt, "status": "sent",
                                "attachment_path": meta.get("attachment_path"),
                                "attachment_name": meta.get("attachment_name"),
                                "attachment_type": meta.get("attachment_type"),
                            }).execute()
                        else:
                            fwd_text = f"Forwarded: {txt}" if txt else "Forwarded attachment"
                            supabase.table("direct_messages").insert({
                                "conversation_id": c["id"], "sender_id": uid, "message_text": fwd_text,
                                "attachment_path": meta.get("attachment_path"),
                                "attachment_name": meta.get("attachment_name"),
                                "attachment_type": meta.get("attachment_type"),
                            }).execute()
                        st.session_state["forward_msg"] = None
                        st.session_state["forward_meta"] = None
                        set_notice("Forwarded!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Forward failed: {e}")
        with col_chat:
            sel = st.session_state.get("eco_sel")
            if not sel:
                st.markdown('<div style="background:#F0F2F5; padding:40px; text-align:center; border-radius:12px;"><h3>💬 EcoLoop Community Hub</h3><p>Select a chat on the left<br>or create a new Chat Room / DM in ➕ New</p></div>', unsafe_allow_html=True)
            else:
                if sel["type"] == "room":
                    hb1, hb2 = st.columns([1, 5])
                    with hb1:
                        if st.button("⬅", key=f"back_room_{sel['id']}"):
                            st.session_state["eco_sel"] = None
                            st.rerun()
                    with hb2:
                        st.markdown(f'<div class="chat-head"><b>👥 {esc(sel.get("name"))}</b><br><span style="font-size:12px;">Chat Room • Status: {esc(sel.get("my_status") or "")}</span></div>', unsafe_allow_html=True)
                    # Only approved members may send - block ALL other statuses
                    if not is_approved_status(sel.get("my_status")):
                        st.warning(f"Your membership status is '{esc(sel.get('my_status') or 'unknown')}'. Only approved members can send messages in this Chat Room. Please wait for creator approval.")
                    with st.expander("⋮ Chat Room Info — Members, Add / Remove / Make Admin, Link"):
                        st.write(f"Description: {esc(sel.get('desc') or '')}")
                        st.code(f"Invite Code: {sel.get('code') or ''}", language="text")
                        app_url2 = get_app_url()
                        if app_url2 and sel.get("code"):
                            st.code(f"{app_url2}/?room={sel.get('code')}", language="text")
                            st.caption("Share this full link.")
                        else:
                            st.code(f"?room={sel.get('code') or ''}", language="text")
                            st.caption("Share link: copy your app URL from the browser and add ?room=CODE")
                        is_creator = str(sel.get("created_by")) == str(uid)
                        try:
                            me = supabase.table("group_memberships").select("*").eq("group_id", sel["id"]).eq("user_id", uid).single().execute().data or {}
                            is_admin = is_admin_role(me.get("membership_role"))
                        except Exception:
                            is_admin = False
                        if is_creator:
                            st.write(f"You are: **👑 Creator / Admin** — Status: **{esc(me.get('status') or '')}**")
                        elif is_admin:
                            st.write(f"You are: **Admin (not creator)** — Status: **{esc(me.get('status') or '')}**")
                            st.caption("Membership management (Approve / Make Admin / Remove) is reserved for the Chat Room creator under existing RLS. Admins can view members.")
                        else:
                            st.write(f"You are: **Member** — Status: **{esc(me.get('status') or '')}**")
                        if is_creator:
                            try:
                                pending = supabase.table("group_memberships").select("*").eq("group_id", sel["id"]).eq("status", "pending").execute().data or []
                            except Exception as e:
                                st.error(f"Could not load pending requests: {e}")
                                pending = []
                            if pending:
                                st.markdown('<div class="pending-box"><b>⏳ Pending Requests — Creator approval only</b></div>', unsafe_allow_html=True)
                                for pm in pending:
                                    pp = get_profile(pm.get("user_id"))
                                    pc1, pc2, pc3 = st.columns([3, 1, 1])
                                    with pc1:
                                        st.write(f"{esc(get_name(pp))} — {esc(pp.get('display_name') or '')}")
                                    with pc2:
                                        if st.button("Approve", key=f"approve_{sel['id']}_{pm.get('user_id')}"):
                                            try:
                                                supabase.table("group_memberships").update({"status": "approved"}).eq("group_id", sel["id"]).eq("user_id", pm.get("user_id")).execute()
                                                set_notice(f"Approved {get_name(pp)}")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Approve failed — only creator can approve under RLS: {e}")
                                    with pc3:
                                        if st.button("Reject", key=f"reject_{sel['id']}_{pm.get('user_id')}"):
                                            try:
                                                supabase.table("group_memberships").delete().eq("group_id", sel["id"]).eq("user_id", pm.get("user_id")).execute()
                                                set_notice("Rejected")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Reject failed: {e}")
                            st.markdown("**➕ Add Participant by @username**")
                            st.caption("This creates a pending request. Creator approval is needed.")
                            add_q = st.text_input("Search @username to add", key=f"add_{sel['id']}", placeholder="@username")
                            if add_q.strip():
                                found_add = search_by_username(add_q, limit=5)
                                for f in found_add:
                                    if str(f.get("user_id")) == str(uid):
                                        continue
                                    if st.button(f"➕ Add {get_name(f)}", key=f"addbtn_{sel['id']}_{f.get('user_id')}"):
                                        try:
                                            supabase.table("group_memberships").insert({"group_id": sel["id"], "user_id": f.get("user_id"), "membership_role": "member", "status": "pending"}).execute()
                                            set_notice(f"Join request created for {get_name(f)} — status: pending")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Add failed: {e} — may already be a member or RLS denied.")
                        try:
                            members = supabase.table("group_memberships").select("*").eq("group_id", sel["id"]).execute().data or []
                            st.markdown(f"**Members ({len(members)})**")
                            members_sorted = sorted(members, key=lambda x: (str(x.get("status") or "").lower() != "approved", (x.get("membership_role") or "")))
                            for mm in members_sorted:
                                pp = get_profile(mm.get("user_id"))
                                c1, c2, c3 = st.columns([3, 1, 1])
                                with c1:
                                    st.write(f"{esc(get_name(pp))} — {esc(mm.get('membership_role'))} — {esc(mm.get('status'))}")
                                if is_creator and str(mm.get("user_id")) != str(uid) and is_approved_status(mm.get("status")):
                                    with c2:
                                        if not is_admin_role(mm.get("membership_role")):
                                            if st.button("Make Admin", key=f"mk_{sel['id']}_{mm.get('user_id')}"):
                                                try:
                                                    supabase.table("group_memberships").update({"membership_role": "admin"}).eq("group_id", sel["id"]).eq("user_id", mm.get("user_id")).execute()
                                                    set_notice("Made Admin")
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"Make Admin failed — only creator can do this under RLS: {e}")
                                        else:
                                            if st.button("Remove Admin", key=f"rmad_{sel['id']}_{mm.get('user_id')}"):
                                                try:
                                                    supabase.table("group_memberships").update({"membership_role": "member"}).eq("group_id", sel["id"]).eq("user_id", mm.get("user_id")).execute()
                                                    set_notice("Admin removed")
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"Remove Admin failed: {e}")
                                    with c3:
                                        if st.button("Remove", key=f"rem_{sel['id']}_{mm.get('user_id')}"):
                                            try:
                                                supabase.table("group_memberships").delete().eq("group_id", sel["id"]).eq("user_id", mm.get("user_id")).execute()
                                                set_notice("Removed")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Remove failed — only creator can do this under RLS: {e}")
                        except Exception as e:
                            st.error(f"Could not load members: {e}")
                        st.divider()
                        # Delete Chat Room removed - not confirmed supported by RLS.
                        st.caption("Chat Room deletion is not available — existing permissions do not confirm it is supported.")
                        # EXIT - KEPT for ordinary members. Requires the SQL policy below to work.
                        # Creator is excluded to avoid orphaning the room; ordinary members can always leave.
                        if not is_creator:
                            st.markdown("**🚪 Exit Chat Room**")
                            st.caption("Leave this Chat Room voluntarily. This removes only your own membership.")
                            if st.button("🚪 Exit Chat Room", key=f"exit_{sel['id']}"):
                                try:
                                    supabase.table("group_memberships").delete().eq("group_id", sel["id"]).eq("user_id", uid).execute()
                                    st.session_state["eco_sel"] = None
                                    set_notice("You exited the Chat Room.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Exit failed: {e}. If you have not yet run the 'members_can_exit_own_membership' SQL policy, ordinary members cannot delete their own membership yet.")
                        else:
                            st.caption("As creator, you remain a member. Exit is not shown for the creator to avoid orphaning the Chat Room.")
                    try:
                        msgs = supabase.table("group_messages").select("*").eq("group_id", sel["id"]).order("created_at").execute().data or []
                    except Exception as e:
                        st.error(f"Could not load Chat Room messages: {e}")
                        msgs = []
                    for m in msgs:
                        p = get_profile(m.get("sender_id"))
                        mine = str(m.get("sender_id")) == str(uid)
                        tick = " ✓✓" if m.get("status") == "read" else " ✓"
                        bc = "bubble-mine" if mine else "bubble-theirs"
                        nh = "" if mine else f'<div class="name">{esc(get_name(p))}</div>'
                        st.markdown(f'<div class="{bc}">{nh}<div>{esc(m.get("message_text") or "")}</div><div class="time">{fmt_time(m.get("created_at"))}{tick if mine else ""}</div></div>', unsafe_allow_html=True)
                        ap = m.get("attachment_path")
                        if not ap and m.get("attachments"):
                            try:
                                atts = m.get("attachments")
                                if isinstance(atts, list) and len(atts) > 0:
                                    ap = atts[0].get("path") or atts[0].get("url")
                            except Exception:
                                pass
                        if ap:
                            url = storage_url(ap)
                            if (m.get("attachment_type") or "").startswith("video"):
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
                                counts[x.get("reaction")] = counts.get(x.get("reaction"), 0) + 1
                            st.caption(" ".join([f"{esc(k)} {v}" for k, v in counts.items()]))
                        rc = st.columns([1, 1, 1, 1, 1, 1, 1])
                        for i, em in enumerate(["❤️", "😂", "🔥", "👍", "😮", "😢"]):
                            with rc[i]:
                                if st.button(em, key=f"react_{m.get('id')}_{em}"):
                                    try:
                                        existing = supabase.table("group_message_reactions").select("*").eq("message_id", m.get("id")).eq("user_id", uid).execute().data or []
                                        if existing and existing[0].get("reaction") == em:
                                            pass
                                        else:
                                            if existing:
                                                try:
                                                    supabase.table("group_message_reactions").delete().eq("message_id", m.get("id")).eq("user_id", uid).execute()
                                                except Exception as e:
                                                    st.error(f"Could not remove old reaction — check RLS: {e}")
                                                    raise e
                                            supabase.table("group_message_reactions").insert({"message_id": m.get("id"), "user_id": uid, "reaction": em}).execute()
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"Reaction failed — check RLS: {e}")
                        with rc[6]:
                            if st.button("↪️", key=f"fwdmsg_{m.get('id')}"):
                                st.session_state["forward_msg"] = m.get("message_text") or ""
                                st.session_state["forward_meta"] = {"orig_id": m.get("id"), "source_type": "room", "attachment_path": m.get("attachment_path"), "attachment_name": m.get("attachment_name"), "attachment_type": m.get("attachment_type")}
                                st.rerun()
                    msg_in = st.text_input("Message", key=f"gmsg_{sel['id']}", label_visibility="collapsed", placeholder="Type a message...")
                    up = st.file_uploader("Photo", type=["jpg", "jpeg", "png", "mp4", "mov", "webp"], key=f"gup_{sel['id']}", label_visibility="collapsed")
                    if st.button("➤ Send", key=f"gsend_{sel['id']}", use_container_width=True):
                        # Only approved members may send - block ALL other statuses
                        if not is_approved_status(sel.get("my_status")):
                            st.error(f"You cannot send — your membership status is '{esc(sel.get('my_status') or 'unknown')}'. Only approved members can send messages.")
                        else:
                            ap = None
                            at = None
                            an = None
                            if up is not None:
                                ap = upload(up, "chatrooms")
                                at = up.type
                                an = up.name
                            if msg_in.strip() or ap:
                                try:
                                    supabase.table("group_messages").insert({"group_id": sel["id"], "sender_id": uid, "message_text": msg_in.strip(), "status": "sent", "attachment_path": ap, "attachment_type": at, "attachment_name": an}).execute()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Send failed: {e}")
                else:
                    op = get_profile(sel.get("other_id"))
                    hb1, hb2 = st.columns([1, 5])
                    with hb1:
                        if st.button("⬅", key=f"back_dm_{sel['id']}"):
                            st.session_state["eco_sel"] = None
                            st.rerun()
                    with hb2:
                        st.markdown(f'<div class="chat-head"><b>👤 {esc(get_name(op))}</b></div>', unsafe_allow_html=True)
                    show_profile_card(sel.get("other_id"))
                    chat_id = sel["id"]
                    try:
                        dmsgs = supabase.table("direct_messages").select("*").eq("conversation_id", chat_id).order("created_at").execute().data or []
                    except Exception as e:
                        st.error(f"Could not load private messages: {e}")
                        dmsgs = []
                    for m in dmsgs:
                        sender = m.get("sender_id")
                        mine = str(sender) == str(uid)
                        p = get_profile(sender)
                        bc = "bubble-mine" if mine else "bubble-theirs"
                        nh = "" if mine else f'<div class="name">{esc(get_name(p))}</div>'
                        st.markdown(f'<div class="{bc}">{nh}<div>{esc(m.get("message_text") or "")}</div><div class="time">{fmt_time(m.get("created_at"))}</div></div>', unsafe_allow_html=True)
                        if m.get("attachment_path"):
                            url2 = storage_url(m.get("attachment_path"))
                            if (m.get("attachment_type") or "").startswith("video"):
                                st.video(url2)
                            else:
                                st.image(url2, width=250)
                        if st.button("↪️ Forward", key=f"fwddm_{m.get('id')}"):
                            st.session_state["forward_msg"] = m.get("message_text") or ""
                            st.session_state["forward_meta"] = {"orig_id": m.get("id"), "source_type": "dm", "attachment_path": m.get("attachment_path"), "attachment_name": m.get("attachment_name"), "attachment_type": m.get("attachment_type")}
                            st.rerun()
                    dm_in = st.text_input("Message", key=f"dm_{chat_id}", label_visibility="collapsed", placeholder="Type a message...")
                    dm_up = st.file_uploader("Photo", type=["jpg", "jpeg", "png", "mp4", "mov", "webp"], key=f"dmup_{chat_id}", label_visibility="collapsed")
                    if st.button("➤ Send", key=f"dmsend_{chat_id}", use_container_width=True):
                        ap = None
                        at = None
                        an = None
                        if dm_up is not None:
                            ap = upload(dm_up, "direct-messages")
                            at = dm_up.type
                            an = dm_up.name
                        if dm_in.strip() or ap:
                            try:
                                supabase.table("direct_messages").insert({"conversation_id": chat_id, "sender_id": uid, "message_text": dm_in.strip(), "attachment_path": ap, "attachment_type": at, "attachment_name": an}).execute()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Send failed: {e}")
