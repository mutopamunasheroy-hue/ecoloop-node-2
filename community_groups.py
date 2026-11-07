import streamlit as st
import uuid
from datetime import datetime, timedelta

st.set_page_config(page_title="EcoLoop Node Community", page_icon="♻️", layout="wide")

try:
    from supabase import create_client
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
    st.error("Add SUPABASE_URL and SUPABASE_KEY in Streamlit Secrets")
    st.stop()

BUCKET = "community-media"
REACTION_EMOJIS = ["❤️", "😂", "🔥", "👍", "😮", "😢"]

if "uid" not in st.session_state: st.session_state.uid = None
if "eco_current_page" not in st.session_state: st.session_state.eco_current_page = "Chats"
if "eco_chat_id" not in st.session_state: st.session_state.eco_chat_id = None
if "eco_chat_type" not in st.session_state: st.session_state.eco_chat_type = "direct"
if "eco_view_profile_id" not in st.session_state: st.session_state.eco_view_profile_id = None
if "eco_open_story_id" not in st.session_state: st.session_state.eco_open_story_id = None
if "eco_react_open_id" not in st.session_state: st.session_state.eco_react_open_id = None
if "eco_show_add_status" not in st.session_state: st.session_state.eco_show_add_status = False
if "eco_show_members" not in st.session_state: st.session_state.eco_show_members = False
if "eco_last_unread" not in st.session_state: st.session_state.eco_last_unread = 0

def eco_storage_url(path):
    if not path: return ""
    if str(path).startswith("http"): return str(path)
    try:
        res = supabase.storage.from_(BUCKET).create_signed_url(str(path), 3600)
        if isinstance(res, dict): return res.get("signedURL") or res.get("signedUrl") or ""
        return str(res)
    except Exception:
        try: return supabase.storage.from_(BUCKET).get_public_url(str(path))
        except Exception: return ""

def eco_upload_file(file, folder):
    ext = file.name.split(".")[-1] if "." in file.name else "jpg"
    path = f"{folder}/{uuid.uuid4()}.{ext}"
    supabase.storage.from_(BUCKET).upload(path, file.getvalue(), {"content-type": file.type or "image/jpeg"})
    return path

def eco_display_name(p):
    if not p: return "User"
    return p.get("display_name") or p.get("username") or "User"

def eco_profile_with_avatar(uid):
    try:
        r = supabase.table("profiles").select("*").eq("id", uid).single().execute()
        return r.data or {}
    except Exception: return {}

def eco_time_short(ts):
    if not ts: return ""
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        return dt.strftime("%H:%M")
    except Exception: return str(ts)[:5]

def eco_get_reactions(mids):
    if not mids: return {}
    try:
        r = supabase.table("message_reactions").select("*").in_("message_id", mids).execute()
        out = {}
        for row in r.data or []:
            mid = str(row.get("message_id"))
            out.setdefault(mid, {})
            em = row.get("emoji") or "❤️"
            out[mid][em] = out[mid].get(em, 0) + 1
        return out
    except Exception: return {}

def eco_get_my_reactions(mids, uid):
    if not mids: return {}
    try:
        r = supabase.table("message_reactions").select("*").in_("message_id", mids).eq("user_id", uid).execute()
        return {str(x.get("message_id")): x.get("emoji") for x in (r.data or [])}
    except Exception: return {}

def eco_toggle_reaction(message_id, uid, emoji, is_group=False):
    try:
        ex = supabase.table("message_reactions").select("*").eq("message_id", message_id).eq("user_id", uid).execute()
        if ex.data:
            old = ex.data[0]
            if old.get("emoji") == emoji:
                supabase.table("message_reactions").delete().eq("id", old.get("id")).execute()
            else:
                supabase.table("message_reactions").update({"emoji": emoji}).eq("id", old.get("id")).execute()
        else:
            supabase.table("message_reactions").insert({"message_id": message_id, "user_id": uid, "emoji": emoji, "is_group": is_group}).execute()
    except Exception as e: st.error(f"Reaction failed: {e}")

def eco_update_presence(uid):
    try: supabase.table("profiles").update({"last_seen": datetime.utcnow().isoformat(), "is_online": True}).eq("id", uid).execute()
    except Exception: pass

def eco_presence_text(prof):
    if not prof: return "Offline"
    ls = prof.get("last_seen")
    if not ls: return "Offline"
    try:
        dt = datetime.fromisoformat(str(ls).replace("Z", "+00:00"))
        diff = (datetime.now(dt.tzinfo) - dt).total_seconds()
        if diff < 120: return "Online"
        if diff < 86400: return f"last seen today at {dt.strftime('%H:%M')}"
        return f"last seen {dt.strftime('%d/%m %H:%M')}"
    except Exception: return "Offline"

def eco_tick_html(msg, sent):
    if not sent: return ""
    s = str(msg.get("status") or "sent")
    if s == "read": return " <span style='color:#53BDEB;'>✓✓</span>"
    if s == "delivered": return " <span style='color:#8696A0;'>✓✓</span>"
    return " <span style='color:#8696A0;'>✓</span>"

def eco_mark_as_read(chat_id, is_group, uid):
    try:
        tbl = "group_messages" if is_group else "messages"
        col = "group_id" if is_group else "chat_id"
        supabase.table(tbl).update({"status": "read", "read_at": datetime.utcnow().isoformat()}).eq(col, chat_id).neq("sender_id", uid).neq("status", "read").execute()
    except Exception: pass

def eco_get_unread_count(chat_id, is_group, uid):
    try:
        tbl = "group_messages" if is_group else "messages"
        col = "group_id" if is_group else "chat_id"
        r = supabase.table(tbl).select("id", count="exact").eq(col, chat_id).neq("sender_id", uid).neq("status", "read").execute()
        return r.count or 0
    except Exception: return 0

def eco_get_last_message(chat_id, is_group):
    try:
        tbl = "group_messages" if is_group else "messages"
        col = "group_id" if is_group else "chat_id"
        r = supabase.table(tbl).select("*").eq(col, chat_id).order("created_at", desc=True).limit(1).execute()
        return r.data[0] if r.data else None
    except Exception: return None

def eco_check_notifications(uid):
    try:
        total = 0
        chats = supabase.table("direct_chats").select("*").or_(f"user1.eq.{uid},user2.eq.{uid}").execute().data or []
        for ch in chats:
            total += eco_get_unread_count(ch.get("id"), False, uid)
        if total > 0:
            prev = st.session_state.get("eco_last_unread", 0)
            if total > prev: st.toast(f"💬 {total - prev} new message(s)", icon="💬")
            st.session_state.eco_last_unread = total
        return total
    except Exception: return 0

def eco_bubble_html(body, time_str, sent, sender, msg=None):
    safe = str(body).replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
    sender_html = f'<div class="wa-sender">{sender}</div>' if sender else ""
    cls = "wa-bubble-me" if sent else "wa-bubble-other"
    tick = eco_tick_html(msg or {}, sent) if sent else ""
    return f'<div class="{cls}">{sender_html}<div>{safe}</div><div class="wa-meta">{time_str}{tick}</div></div>'

if not st.session_state.uid:
    st.markdown("## ♻️ EcoLoop Node Community")
    st.caption("Talk like home, connect like family.")
    with st.form("login"):
        email = st.text_input("Email")
        pw = st.text_input("Password", type="password")
        b1, b2 = st.columns(2)
        login = b1.form_submit_button("Login")
        signup = b2.form_submit_button("Sign Up")
        if login or signup:
            try:
                if signup: supabase.auth.sign_up({"email": email, "password": pw})
                supabase.auth.sign_in_with_password({"email": email, "password": pw})
                user = supabase.auth.get_user().user
                st.session_state.uid = user.id
                try: supabase.table("profiles").upsert({"id": user.id, "username": email.split("@")[0], "display_name": email.split("@")[0], "email": email, "last_seen": datetime.utcnow().isoformat(), "is_online": True}).execute()
                except Exception: pass
                st.rerun()
            except Exception as e: st.error(str(e))
    st.stop()

uid = st.session_state.uid
me = eco_profile_with_avatar(uid)
eco_update_presence(uid)
total_unread_global = eco_check_notifications(uid)

st.markdown("""
<style>
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"], .block-container, [data-testid="stVerticalBlock"] {
    background-color:#ECE5DD !important;
    background-image: radial-gradient(#D5D0C8 1px, transparent 1px) !important;
    background-size: 20px 20px !important;
}
.block-container{padding:0!important;max-width:100%!important}
header[data-testid="stHeader"]{display:none} [data-testid="stSidebar"]{display:none}
.wa-topbar{background:#075E54;color:white;padding:12px 16px;display:flex;align-items:center;justify-content:space-between}
.wa-topbar b{font-size:19px} .wa-topbar span{font-size:12px;opacity:.9}
.wa-chat-bg{background-color:#ECE5DD!important;background-image:radial-gradient(#D5D0C8 1px, transparent 1px)!important;background-size:20px 20px!important;min-height:68vh!important;padding:14px 10px 16px 10px!important;width:100%!important}
.wa-bubble-me{background:#DCF8C6;border-radius:10px 10px 0 10px;padding:8px 10px;margin:6px 0 6px auto;max-width:82%;width:fit-content;box-shadow:0 1px 1px rgba(0,0,0,.12);font-size:15px;line-height:1.45}
.wa-bubble-other{background:#FFFFFF;border-radius:10px 10px 10px 0;padding:8px 10px;margin:6px auto 6px 0;max-width:82%;width:fit-content;box-shadow:0 1px 1px rgba(0,0,0,.12);font-size:15px;line-height:1.45}
.wa-meta{font-size:11px;color:#667781;text-align:right;margin-top:3px}
.wa-sender{font-size:12px;font-weight:700;color:#128C7E;margin-bottom:2px}
.wa-react-count{background:#FFFFFF;border:1px solid #E9EDEF;border-radius:16px;padding:2px 8px;font-size:12px;display:inline-block;margin:2px 2px 6px 0}
.wa-empty{height:60vh;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#667781;text-align:center;padding:30px}
[data-testid="stPills"]{background:#FFFFFF!important;border:1px solid #E9EDEF!important;border-radius:24px!important;padding:4px!important;box-shadow:0 2px 8px rgba(0,0,0,.15)!important;width:fit-content!important}
[data-testid="stPills"] button{border:none!important;background:transparent!important;font-size:20px!important;min-height:36px!important;height:36px!important;width:36px!important;padding:0!important;margin:0 2px!important}
.wa-updates{background:#0B141A!important;background-image:none!important;color:white;padding:0 0 90px 0;min-height:100vh}
</style>
""", unsafe_allow_html=True)

st.markdown(f'<div class="wa-topbar"><div><b>EcoLoop Node Community</b><br><span>Talk like home, connect like family. {" • 🔔 "+str(total_unread_global)+" new" if total_unread_global else ""}</span></div><div>🔍 ⋮</div></div>', unsafe_allow_html=True)

n1, n2, n3, n4, n5 = st.columns(5)
with n1:
    if st.button("💬 Chats"): st.session_state.eco_current_page="Chats"; st.session_state.eco_chat_id=None; st.rerun()
with n2:
    if st.button("👥 Chat Rooms"): st.session_state.eco_current_page="Chat Rooms"; st.session_state.eco_chat_id=None; st.rerun()
with n3:
    if st.button("🟢 Updates"): st.session_state.eco_current_page="Updates"; st.session_state.eco_chat_id=None; st.rerun()
with n4:
    if st.button("🔎 Discover"): st.session_state.eco_current_page="Discover"; st.session_state.eco_chat_id=None; st.rerun()
with n5:
    if st.button("👤 Profile"): st.session_state.eco_current_page="Profile"; st.session_state.eco_chat_id=None; st.rerun()

if st.session_state.eco_view_profile_id:
    pid = st.session_state.eco_view_profile_id
    prof = eco_profile_with_avatar(pid)
    if st.button("⬅️ Back"): st.session_state.eco_view_profile_id=None; st.rerun()
    st.markdown(f"### 👤 {eco_display_name(prof)}")
    if prof.get("avatar_url"): st.image(eco_storage_url(prof.get("avatar_url")), width=120)
    st.write(prof.get("bio") or "No bio yet")
    st.write(f"📍 {prof.get('location') or ''} | 🎯 {prof.get('interests') or ''}")
    st.write(f"Status: {eco_presence_text(prof)}")
    if pid != uid:
        if st.button("💬 Chat with this person"):
            try:
                ex = supabase.table("direct_chats").select("*").or_(f"and(user1.eq.{uid},user2.eq.{pid}),and(user1.eq.{pid},user2.eq.{uid})").execute()
                if ex.data: cid = ex.data[0].get("id")
                else:
                    cr = supabase.table("direct_chats").insert({"user1": uid, "user2": pid}).execute()
                    cid = cr.data[0].get("id")
                st.session_state.eco_view_profile_id=None; st.session_state.eco_chat_id=cid; st.session_state.eco_chat_type="direct"; st.session_state.eco_current_page="Chats"; st.rerun()
            except Exception as e: st.error(str(e))
    st.stop()

def eco_render_chat(messages, is_group=False, chat_id=None, search_text=""):
    if search_text.strip():
        messages = [m for m in messages if search_text.lower() in str(m.get("message_text") or "").lower()]
    if not messages:
        st.markdown('<div class="wa-chat-bg"><div class="wa-empty"><div style="font-size:48px;">💬</div><b>Say hi</b><p>This is the beginning of your conversation.</p></div></div>', unsafe_allow_html=True)
        return
    mids=[str(m.get("id")) for m in messages if m.get("id")]
    all_reactions=eco_get_reactions(mids)
    my_reactions=eco_get_my_reactions(mids, uid)
    st.markdown('<div class="wa-chat-bg">', unsafe_allow_html=True)
    seen=set()
    for m in messages:
        if m.get("deleted_at"): continue
        mid=str(m.get("id") or "")+str(m.get("created_at") or "")
        if mid in seen: continue
        seen.add(mid)
        sent=str(m.get("sender_id"))==str(uid)
        sender=eco_profile_with_avatar(m.get("sender_id")) if is_group else {}
        name="You" if sent else eco_display_name(sender)
        body=str(m.get("message_text") or "")
        attach_html=""
        if m.get("attachment_path"):
            url=eco_storage_url(m.get("attachment_path"))
            typ=str(m.get("attachment_type") or "").lower()
            if url and typ.startswith("image"): attach_html=f'<img src="{url}" style="max-width:100%;border-radius:10px;margin:4px 0;" />'
            elif url and typ.startswith("video"): attach_html=f'<div>🎬 <a href="{url}" target="_blank">Watch video</a></div>'
            elif url: attach_html=f'<div>📎 <a href="{url}" target="_blank">{m.get("attachment_name") or "Open attachment"}</a></div>'
        if attach_html or body:
            if attach_html:
                st.markdown(f'<div class="{"wa-bubble-me" if sent else "wa-bubble-other"}">{("<div class=\"wa-sender\">"+name+"</div>") if (not sent and name) else ""}{attach_html}{("<div>"+body.replace("<","&lt;").replace(">","&gt;")+"</div>") if body else ""}<div class="wa-meta">{eco_time_short(m.get("created_at"))}{eco_tick_html(m, sent) if sent else ""}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(eco_bubble_html(body, eco_time_short(m.get("created_at")), sent, "" if sent else name, m), unsafe_allow_html=True)
        real_id=str(m.get("id") or "")
        if not real_id: continue
        counts=all_reactions.get(real_id,{})
        if counts:
            pills="".join([f'<span class="wa-react-count">{em} {cnt}</span>' for em,cnt in counts.items()])
            align="right" if sent else "left"
            st.markdown(f'<div style="text-align:{align};margin-top:-2px;">{pills}</div>', unsafe_allow_html=True)
        is_open=st.session_state.get("eco_react_open_id")==real_id
        my_em=my_reactions.get(real_id,"")
        if st.button("😊" if not my_em else my_em, key=f"eco_react_{'g' if is_group else 'd'}_{real_id}"):
            st.session_state.eco_react_open_id=None if is_open else real_id; st.rerun()
        if is_open:
            picked=st.pills("React", REACTION_EMOJIS, key=f"eco_pills_{'g' if is_group else 'd'}_{real_id}", label_visibility="collapsed")
            if picked:
                eco_toggle_reaction(real_id, uid, picked, is_group=is_group)
                st.session_state.eco_react_open_id=None; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def eco_composer(chat_id, is_group=False):
    with st.form(f"eco_send_{'g' if is_group else 'd'}_{chat_id}", clear_on_submit=True):
        c1, c2, c3 = st.columns([6, 1, 1])
        with c1: msg = st.text_input("Message", label_visibility="collapsed", placeholder="Message")
        with c2: up = st.file_uploader("📎", label_visibility="collapsed", key=f"eco_up_{'g' if is_group else 'd'}_{chat_id}", type=["jpg","jpeg","png","webp","mp4","pdf","docx"])
        with c3: send = st.form_submit_button("➤")
        if send and (msg.strip() or up):
            try:
                data={"sender_id": uid, "message_text": msg.strip(), "status": "sent"}
                if is_group: data["group_id"]=chat_id
                else: data["chat_id"]=chat_id
                if up:
                    path=eco_upload_file(up, "chat")
                    data["attachment_path"]=path; data["attachment_type"]=up.type; data["attachment_name"]=up.name
                tbl="group_messages" if is_group else "messages"
                supabase.table(tbl).insert(data).execute(); st.rerun()
            except Exception as e: st.error(str(e))

if st.session_state.eco_current_page=="Chats":
    if st.session_state.eco_chat_id:
        cid=st.session_state.eco_chat_id
        eco_mark_as_read(cid, False, uid)
        try:
            ch_row = supabase.table("direct_chats").select("*").eq("id", cid).single().execute().data or {}
            other_id = ch_row.get("user2") if str(ch_row.get("user1"))==str(uid) else ch_row.get("user1")
            other_p = eco_profile_with_avatar(other_id)
            pres = eco_presence_text(other_p)
            dot = "🟢 Online" if pres=="Online" else f"⚪ {pres}"
            st.markdown(f"### {eco_display_name(other_p)}  <span style='font-size:13px;color:#667781;'>{dot}</span>", unsafe_allow_html=True)
        except Exception: pass
        search_in_chat = st.text_input("🔍 Search in this chat", key=f"eco_search_in_chat_{cid}", placeholder="Search messages...")
        try: msgs=supabase.table("messages").select("*").eq("chat_id", cid).order("created_at").execute().data or []
        except Exception: msgs=[]
        if search_in_chat.strip():
            st.caption(f"Found {len([m for m in msgs if search_in_chat.lower() in str(m.get('message_text') or '').lower()])} message(s) for '{search_in_chat}'")
        eco_render_chat(msgs, is_group=False, chat_id=cid, search_text=search_in_chat)
        eco_composer(cid, is_group=False)
        if st.button("⬅️ Back to chats"): st.session_state.eco_chat_id=None; st.rerun()
    else:
        st.markdown(f"### 💬 Chats {' • 🔔 '+str(total_unread_global)+' new' if total_unread_global else ''}")
        q = st.text_input("🔍 Search chats", placeholder="Search chats", key="eco_search_chats")
        try: chats=supabase.table("direct_chats").select("*").or_(f"user1.eq.{uid},user2.eq.{uid}").order("created_at", desc=True).execute().data or []
        except Exception: chats=[]
        if not chats: st.info("No chats yet. Go to Discover to find people.")
        for ch in chats:
            other=ch.get("user2") if str(ch.get("user1"))==str(uid) else ch.get("user1")
            p=eco_profile_with_avatar(other)
            name=eco_display_name(p)
            if q.strip() and q.lower() not in name.lower(): continue
            last=eco_get_last_message(ch.get("id"), False)
            last_text=(last.get("message_text") or "📎 Attachment") if last else "Say hi 👋"
            if len(last_text)>35: last_text=last_text[:35]+"..."
            last_time=eco_time_short(last.get("created_at")) if last else ""
            unread=eco_get_unread_count(ch.get("id"), False, uid)
            presence=eco_presence_text(p)
            dot="🟢" if presence=="Online" else "⚪"
            avatar_url=eco_storage_url(p.get("avatar_url"))
            c1, c2, c3 = st.columns([1, 5, 1])
            with c1:
                if avatar_url: st.image(avatar_url, width=52)
                else: st.markdown(f"<div style='width:52px;height:52px;border-radius:50%;background:#DFE5E7;display:flex;align-items:center;justify-content:center;font-weight:700;'>{name[:2].upper()}</div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"**{name}** {dot}")
                st.caption(f"{presence} • {last_text}")
            with c3:
                st.caption(last_time)
                if unread>0: st.markdown(f"<div style='background:#00A884;color:white;border-radius:50%;width:24px;height:24px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;margin-left:auto;'>{unread}</div>", unsafe_allow_html=True)
            if st.button(f"Open {name}", key=f"eco_open_chat_{ch.get('id')}"):
                st.session_state.eco_chat_id=ch.get("id"); st.session_state.eco_chat_type="direct"; st.rerun()
            st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)

elif st.session_state.eco_current_page=="Chat Rooms":
    if st.session_state.eco_chat_id:
        gid=st.session_state.eco_chat_id
        eco_mark_as_read(gid, True, uid)
        try: grp=supabase.table("groups").select("*").eq("id", gid).single().execute().data or {}
        except Exception: grp={}
        c1, c2 = st.columns([4, 1])
        with c1: st.markdown(f"### 👥 {grp.get('name') or 'Chat Room'}")
        with c2:
            if st.button("👥 Members"): st.session_state.eco_show_members=not st.session_state.eco_show_members; st.rerun()
        # ---------- INVITE LINK + CODE ----------
        invite = grp.get("invite_code") or "NO-CODE"
        st.markdown(f"**Invite Code:** `{invite}`")
        st.caption("Share this code with friends to join. They go to Chat Rooms > Join via Code and type it.")
        st.code(invite, language=None)
        if st.button("📋 Copy Invite Code - tap to show again"):
            st.code(invite, language=None)
            st.success("Copy that code and send it on WhatsApp")
        # ---------- MEMBERS + ADMIN ----------
        is_admin = False
        try:
            my_mem = supabase.table("group_members").select("*").eq("group_id", gid).eq("user_id", uid).single().execute().data or {}
            is_admin = my_mem.get("role") == "Admin"
        except Exception: pass
        if st.session_state.eco_show_members:
            try:
                mems=supabase.table("group_members").select("*").eq("group_id", gid).execute().data or []
                for mm in mems:
                    pp=eco_profile_with_avatar(mm.get("user_id"))
                    st.write(f"{eco_display_name(pp)} — {mm.get('role') or 'Member'} • {eco_presence_text(pp)}")
            except Exception: pass
            if st.button("✕ Close members"): st.session_state.eco_show_members=False; st.rerun()
        if is_admin:
            st.markdown("### 👑 Admin Controls")
            search_user = st.text_input("🔍 Search person to add", key=f"eco_add_search_{gid}", placeholder="Type name or username")
            if search_user.strip():
                try:
                    found = supabase.table("profiles").select("*").or_(f"username.ilike.%{search_user}%,display_name.ilike.%{search_user}%").limit(5).execute().data or []
                    for f in found:
                        if str(f.get("id")) == str(uid): continue
                        if st.button(f"➕ Add {eco_display_name(f)}", key=f"eco_add_{gid}_{f.get('id')}"):
                            try:
                                supabase.table("group_members").insert({"group_id": gid, "user_id": f.get("id"), "role": "Member"}).execute()
                                st.success(f"Added {eco_display_name(f)}"); st.rerun()
                            except Exception as e: st.error(f"Already in room or error: {e}")
                except Exception as e: st.error(str(e))
            try:
                mems2 = supabase.table("group_members").select("*").eq("group_id", gid).execute().data or []
                for mm in mems2:
                    if str(mm.get("user_id")) == str(uid): continue
                    pp = eco_profile_with_avatar(mm.get("user_id"))
                    a1, a2, a3 = st.columns([3, 1, 1])
                    with a1: st.write(f"{eco_display_name(pp)} — {mm.get('role')}")
                    with a2:
                        if mm.get("role") != "Admin":
                            if st.button("Make Admin", key=f"eco_make_admin_{gid}_{mm.get('user_id')}"):
                                supabase.table("group_members").update({"role": "Admin"}).eq("group_id", gid).eq("user_id", mm.get("user_id")).execute(); st.rerun()
                    with a3:
                        if st.button("Remove", key=f"eco_remove_{gid}_{mm.get('user_id')}"):
                            supabase.table("group_members").delete().eq("group_id", gid).eq("user_id", mm.get("user_id")).execute(); st.rerun()
            except Exception: pass
            if st.button("🗑️ Delete this Chat Room (Admin only)"):
                try:
                    supabase.table("group_members").delete().eq("group_id", gid).execute()
                    supabase.table("group_messages").delete().eq("group_id", gid).execute()
                    supabase.table("groups").delete().eq("id", gid).execute()
                    st.session_state.eco_chat_id = None; st.rerun()
                except Exception as e: st.error(str(e))
        else:
            if st.button("🚪 Leave this Chat Room"):
                supabase.table("group_members").delete().eq("group_id", gid).eq("user_id", uid).execute()
                st.session_state.eco_chat_id = None; st.rerun()
        search_in_chat = st.text_input("🔍 Search in this Chat Room", key=f"eco_search_room_{gid}", placeholder="Search messages...")
        try: msgs=supabase.table("group_messages").select("*").eq("group_id", gid).order("created_at").execute().data or []
        except Exception: msgs=[]
        eco_render_chat(msgs, is_group=True, chat_id=gid, search_text=search_in_chat)
        eco_composer(gid, is_group=True)
        if st.button("⬅️ Back to Chat Rooms"): st.session_state.eco_chat_id=None; st.rerun()
    else:
        st.markdown("### 👥 Chat Rooms")
        with st.expander("➕ Create New Chat Room"):
            gname=st.text_input("Chat Room Name")
            gdesc=st.text_area("Description (optional)")
            if st.button("Create Chat Room"):
                if not gname.strip(): st.error("Enter a name")
                else:
                    try:
                        payload={"name": gname.strip(), "description": gdesc, "created_by": uid, "invite_code": str(uuid.uuid4())[:8].upper()}
                        r=supabase.table("groups").insert(payload).execute()
                        gid=r.data[0].get("id")
                        supabase.table("group_members").insert({"group_id": gid, "user_id": uid, "role": "Admin"}).execute()
                        st.success(f"Chat Room created! Invite Code: {payload['invite_code']}"); st.rerun()
                    except Exception as e: st.error(str(e))
        with st.expander("🔗 Join Chat Room via Code / Link"):
            code=st.text_input("Paste Invite Code here")
            if st.button("Join"):
                try:
                    r=supabase.table("groups").select("*").eq("invite_code", code.strip().upper()).single().execute()
                    if r.data:
                        try: supabase.table("group_members").insert({"group_id": r.data.get("id"), "user_id": uid, "role": "Member"}).execute()
                        except Exception: pass
                        st.success(f"Joined {r.data.get('name')}!"); st.rerun()
                    else: st.error("Code not found - ask Admin for correct code")
                except Exception as e: st.error(str(e))
        try:
            mems=supabase.table("group_members").select("group_id").eq("user_id", uid).execute().data or []
            gids=[m.get("group_id") for m in mems]
            rooms=supabase.table("groups").select("*").in_("id", gids).execute().data or [] if gids else []
        except Exception: rooms=[]
        for room in rooms:
            last=eco_get_last_message(room.get("id"), True)
            last_text=(last.get("message_text") or "📎 Attachment") if last else "No messages yet"
            unread=eco_get_unread_count(room.get("id"), True, uid)
            c1, c2, c3 = st.columns([1, 5, 1])
            with c1: st.markdown(f"<div style='width:52px;height:52px;border-radius:50%;background:#075E54;color:white;display:flex;align-items:center;justify-content:center;font-weight:700;'>{str(room.get('name') or '?')[:2].upper()}</div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"**{room.get('name')}**")
                st.caption(last_text[:35])
                st.caption(f"Invite: {room.get('invite_code') or ''}")
            with c3:
                st.caption(eco_time_short(last.get("created_at")) if last else "")
                if unread>0: st.markdown(f"<div style='background:#00A884;color:white;border-radius:50%;width:24px;height:24px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;margin-left:auto;'>{unread}</div>", unsafe_allow_html=True)
            if st.button(f"Open {room.get('name')}", key=f"eco_room_{room.get('id')}"):
                st.session_state.eco_chat_id=room.get("id"); st.session_state.eco_chat_type="group"; st.rerun()
        if not rooms: st.info("No Chat Rooms yet. Create one above.")

elif st.session_state.eco_current_page=="Updates":
    st.markdown('<div class="wa-updates">', unsafe_allow_html=True)
    st.markdown('<div style="display:flex;justify-content:space-between;padding:16px;"><b style="font-size:24px;color:white;">Updates</b><span style="color:white;">🔍 ⋮</span></div>', unsafe_allow_html=True)
    st.markdown('<div style="padding:0 16px;font-size:18px;font-weight:700;color:white;">Status</div>', unsafe_allow_html=True)
    if st.button("➕ Add your status", key="eco_add_status_btn"): st.session_state.eco_show_add_status=True
    if st.session_state.eco_show_add_status:
        up=st.file_uploader("Tap here to pick photo / video for story", type=["jpg","jpeg","png","webp","mp4","mov"], key="eco_status_up")
        cap=st.text_input("Add a caption (optional)", key="eco_status_cap")
        if st.button("Publish story"):
            if up:
                try:
                    path=eco_upload_file(up, "stories")
                    supabase.table("stories").insert({"user_id": uid, "media_path": path, "caption": cap, "created_at": datetime.utcnow().isoformat()}).execute()
                    st.session_state.eco_show_add_status=False; st.success("Story published!"); st.rerun()
                except Exception as e: st.error(str(e))
            else: st.error("Pick a photo first")
    try:
        since=(datetime.utcnow()-timedelta(hours=24)).isoformat()
        stories=supabase.table("stories").select("*").gte("created_at", since).order("created_at", desc=True).execute().data or []
    except Exception: stories=[]
    if stories:
        cols=st.columns(min(len(stories), 4))
        for i, s in enumerate(stories):
            with cols[i % len(cols)]:
                url=eco_storage_url(s.get("media_path") or s.get("image_path") or "")
                name=eco_display_name(eco_profile_with_avatar(s.get("user_id")))
                if url: st.image(url, use_container_width=True)
                st.caption(name)
                if st.button("View", key=f"eco_story_view_{s.get('id')}"): st.session_state.eco_open_story_id=s.get("id"); st.rerun()
    else: st.caption("No stories yet. Be the first to post.")
    if st.session_state.eco_open_story_id:
        sid=st.session_state.eco_open_story_id
        s=next((x for x in stories if str(x.get("id"))==str(sid)), None)
        if s:
            if st.button("✕ Close story"): st.session_state.eco_open_story_id=None; st.rerun()
            url=eco_storage_url(s.get("media_path") or s.get("image_path") or "")
            st.markdown(f"### {eco_display_name(eco_profile_with_avatar(s.get('user_id')))}")
            st.caption(f"{eco_time_short(s.get('created_at'))} • disappears in 24h")
            if url:
                if url.lower().split("?")[0].endswith((".mp4",".mov",".webm")): st.video(url)
                else: st.image(url, use_container_width=True)
            if s.get("caption"): st.write(s.get("caption"))
    st.markdown('<div style="padding:16px;"><b style="font-size:18px;color:white;">Channels</b></div>', unsafe_allow_html=True)
    try:
        mems=supabase.table("group_members").select("group_id").eq("user_id", uid).execute().data or []
        gids=[m.get("group_id") for m in mems]
        chans=supabase.table("groups").select("*").in_("id", gids).execute().data or [] if gids else []
    except Exception: chans=[]
    for ch in chans:
        st.markdown(f'<div style="display:flex;gap:12px;padding:12px 16px;color:white;"><div style="width:52px;height:52px;border-radius:50%;background:#075E54;display:flex;align-items:center;justify-content:center;font-weight:700;">{str(ch.get("name") or "?")[:2].upper()}</div><div><b>{ch.get("name")}</b><br><span style="color:#8696A0;font-size:13px;">{ch.get("description") or "Tap to open"}</span></div></div>', unsafe_allow_html=True)
        if st.button(f"Open {ch.get('name')}", key=f"eco_chan_{ch.get('id')}"):
            st.session_state.eco_chat_id=ch.get("id"); st.session_state.eco_current_page="Chat Rooms"; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.eco_current_page=="Discover":
    st.markdown("### 🔎 Discover")
    q=st.text_input("Search username, name, or location")
    try:
        if q.strip(): profs=supabase.table("profiles").select("*").or_(f"username.ilike.%{q}%,display_name.ilike.%{q}%,location.ilike.%{q}%").limit(20).execute().data or []
        else: profs=supabase.table("profiles").select("*").neq("id", uid).limit(20).execute().data or []
    except Exception: profs=[]
    for p in profs:
        if str(p.get("id"))==str(uid): continue
        c1, c2 = st.columns([1, 3])
        with c1:
            if p.get("avatar_url"): st.image(eco_storage_url(p.get("avatar_url")), width=60)
            else: st.markdown(f"<div style='width:60px;height:60px;border-radius:50%;background:#DFE5E7;display:flex;align-items:center;justify-content:center;font-weight:700;'>{eco_display_name(p)[:2].upper()}</div>", unsafe_allow_html=True)
        with c2:
            st.write(f"**{eco_display_name(p)}**  @{p.get('username') or ''}")
            st.caption(f"{eco_presence_text(p)} • {p.get('location') or ''} • {p.get('interests') or ''}")
            if st.button("👀 View Profile", key=f"eco_disc_view_{p.get('id')}"): st.session_state.eco_view_profile_id=p.get("id"); st.rerun()

elif st.session_state.eco_current_page=="Profile":
    st.markdown("### 👤 My Profile")
    if me.get("avatar_url"): st.image(eco_storage_url(me.get("avatar_url")), width=120)
    st.write(f"**{eco_display_name(me)}**  @{me.get('username') or ''}")
    st.write(me.get("bio") or "No bio yet")
    st.write(f"📍 {me.get('location') or ''} | 🎯 {me.get('interests') or ''}")
    with st.form("edit_profile"):
        dn=st.text_input("Display Name", value=me.get("display_name") or "")
        bio=st.text_area("Bio", value=me.get("bio") or "")
        loc=st.text_input("Location", value=me.get("location") or "")
        inter=st.text_input("Interests", value=me.get("interests") or "")
        ig=st.text_input("Instagram", value=me.get("instagram") or "")
        tt=st.text_input("TikTok", value=me.get("tiktok") or "")
        av=st.file_uploader("Change Profile Picture", type=["jpg","jpeg","png","webp"])
        save=st.form_submit_button("Save Profile")
        if save:
            try:
                payload={"display_name": dn, "bio": bio, "location": loc, "interests": inter, "instagram": ig, "tiktok": tt, "last_seen": datetime.utcnow().isoformat(), "is_online": True}
                if av: payload["avatar_url"]=eco_upload_file(av, "avatars")
                supabase.table("profiles").update(payload).eq("id", uid).execute()
                st.success("Saved!"); st.rerun()
            except Exception as e: st.error(str(e))
    if st.button("Logout"):
        try: supabase.table("profiles").update({"is_online": False}).eq("id", uid).execute()
        except Exception: pass
        supabase.auth.sign_out(); st.session_state.uid=None; st.rerun()

st.caption("Powered by Next Gen Impact Hub (NGIH) — Talk like home, connect like family.")
