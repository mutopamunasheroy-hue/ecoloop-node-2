import streamlit as st
import uuid
from datetime import datetime, timedelta

st.set_page_config(page_title="EcoLoop Node Community", page_icon="♻️", layout="wide")

# ---------- SUPABASE ----------
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

if "uid" not in st.session_state:
    st.session_state.uid = None
if "eco_current_page" not in st.session_state:
    st.session_state.eco_current_page = "Chats"
if "eco_chat_id" not in st.session_state:
    st.session_state.eco_chat_id = None
if "eco_chat_type" not in st.session_state:
    st.session_state.eco_chat_type = "direct"
if "eco_view_profile_id" not in st.session_state:
    st.session_state.eco_view_profile_id = None
if "eco_open_story_id" not in st.session_state:
    st.session_state.eco_open_story_id = None
if "eco_react_open_id" not in st.session_state:
    st.session_state.eco_react_open_id = None
if "eco_show_add_status" not in st.session_state:
    st.session_state.eco_show_add_status = False
if "eco_show_members" not in st.session_state:
    st.session_state.eco_show_members = False

# ---------- HELPERS ----------
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

def eco_upload_file(file, folder):
    ext = file.name.split(".")[-1] if "." in file.name else "jpg"
    path = f"{folder}/{uuid.uuid4()}.{ext}"
    supabase.storage.from_(BUCKET).upload(path, file.getvalue(), {"content-type": file.type or "image/jpeg"})
    return path

def eco_display_name(p):
    if not p:
        return "User"
    return p.get("display_name") or p.get("username") or "User"

def eco_profile_with_avatar(uid):
    try:
        r = supabase.table("profiles").select("*").eq("id", uid).single().execute()
        return r.data or {}
    except Exception:
        return {}

def eco_time_short(ts):
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        return dt.strftime("%H:%M")
    except Exception:
        return str(ts)[:5]

def eco_get_reactions(mids):
    if not mids:
        return {}
    try:
        r = supabase.table("message_reactions").select("*").in_("message_id", mids).execute()
        out = {}
        for row in r.data or []:
            mid = str(row.get("message_id"))
            out.setdefault(mid, {})
            em = row.get("emoji") or "❤️"
            out[mid][em] = out[mid].get(em, 0) + 1
        return out
    except Exception:
        return {}

def eco_get_my_reactions(mids, uid):
    if not mids:
        return {}
    try:
        r = supabase.table("message_reactions").select("*").in_("message_id", mids).eq("user_id", uid).execute()
        return {str(x.get("message_id")): x.get("emoji") for x in (r.data or [])}
    except Exception:
        return {}

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
    except Exception as e:
        st.error(f"Reaction failed: {e}")

def eco_bubble_html(body, time_str, sent, sender, edited=False):
    safe = str(body).replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
    sender_html = f'<div class="wa-sender">{sender}</div>' if sender else ""
    edit_html = " <span style='font-size:10px;'>(edited)</span>" if edited else ""
    cls = "wa-bubble-me" if sent else "wa-bubble-other"
    tick = " ✓✓" if sent else ""
    return f'<div class="{cls}">{sender_html}<div>{safe}</div><div class="wa-meta">{time_str}{edit_html}{tick}</div></div>'

# ---------- LOGIN ----------
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
                if signup:
                    supabase.auth.sign_up({"email": email, "password": pw})
                supabase.auth.sign_in_with_password({"email": email, "password": pw})
                user = supabase.auth.get_user().user
                st.session_state.uid = user.id
                try:
                    supabase.table("profiles").upsert({"id": user.id, "username": email.split("@")[0], "display_name": email.split("@")[0], "email": email}).execute()
                except Exception:
                    pass
                st.rerun()
            except Exception as e:
                st.error(str(e))
    st.stop()

uid = st.session_state.uid
me = eco_profile_with_avatar(uid)

# ---------- STYLES - BEIGE + WHATSAPP ----------
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
.wa-pill{background:#FFFFFF;border-radius:16px;padding:10px 12px;margin:8px 0;border:1px solid #E9EDEF}
.wa-react-count{background:#FFFFFF;border:1px solid #E9EDEF;border-radius:16px;padding:2px 8px;font-size:12px;display:inline-block;margin:2px 2px 6px 0}
.wa-empty{height:60vh;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#667781;text-align:center;padding:30px}
[data-testid="stPills"]{background:#FFFFFF!important;border:1px solid #E9EDEF!important;border-radius:24px!important;padding:4px!important;box-shadow:0 2px 8px rgba(0,0,0,.15)!important;width:fit-content!important}
[data-testid="stPills"] button{border:none!important;background:transparent!important;font-size:20px!important;min-height:36px!important;height:36px!important;width:36px!important;padding:0!important;margin:0 2px!important}
.wa-updates{background:#0B141A!important;background-image:none!important;color:white;padding:0 0 90px 0;min-height:100vh}
.wa-status-card{min-width:130px;height:190px;border-radius:16px;overflow:hidden;position:relative;background:#1F2C34;flex-shrink:0;border:2px solid #00A884}
.wa-status-card img{width:100%;height:100%;object-fit:cover}
.wa-status-card span{position:absolute;bottom:8px;left:8px;color:white;font-weight:600;font-size:13px;text-shadow:0 1px 4px black}
.wa-status-add{position:absolute;top:8px;left:8px;background:#00A884;color:white;width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:18px}
</style>
""", unsafe_allow_html=True)

# ---------- TOPBAR ----------
st.markdown('<div class="wa-topbar"><div><b>EcoLoop Node Community</b><br><span>Talk like home, connect like family.</span></div><div>🔍 ⋮</div></div>', unsafe_allow_html=True)

# ---------- NAV ----------
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

# ---------- VIEW PROFILE (FIXED - actually opens) ----------
if st.session_state.eco_view_profile_id:
    pid = st.session_state.eco_view_profile_id
    prof = eco_profile_with_avatar(pid)
    if st.button("⬅️ Back"):
        st.session_state.eco_view_profile_id=None; st.rerun()
    st.markdown(f"### 👤 {eco_display_name(prof)}")
    if prof.get("avatar_url"):
        st.image(eco_storage_url(prof.get("avatar_url")), width=120)
    st.write(prof.get("bio") or "No bio yet")
    st.write(f"📍 {prof.get('location') or ''}")
    st.write(f"🎯 {prof.get('interests') or ''}")
    if prof.get("instagram"): st.write(f"IG: {prof.get('instagram')}")
    if prof.get("tiktok"): st.write(f"TikTok: {prof.get('tiktok')}")
    if pid != uid:
        if st.button("💬 Chat with this person"):
            try:
                ex = supabase.table("direct_chats").select("*").or_(f"and(user1.eq.{uid},user2.eq.{pid}),and(user1.eq.{pid},user2.eq.{uid})").execute()
                if ex.data:
                    cid = ex.data[0].get("id")
                else:
                    cr = supabase.table("direct_chats").insert({"user1": uid, "user2": pid}).execute()
                    cid = cr.data[0].get("id")
                st.session_state.eco_view_profile_id=None
                st.session_state.eco_chat_id=cid
                st.session_state.eco_chat_type="direct"
                st.session_state.eco_current_page="Chats"
                st.rerun()
            except Exception as e:
                st.error(str(e))
    st.stop()

# ---------- RENDER CHAT BUBBLES - BEIGE + WHATSAPP REACTIONS ----------
def eco_render_chat(messages, is_group=False, chat_id=None):
    if not messages:
        st.markdown('<div class="wa-chat-bg"><div class="wa-empty"><div style="font-size:48px;">💬</div><b>Say hi</b><p>This is the beginning of your conversation.</p></div></div>', unsafe_allow_html=True)
        return
    mids=[str(m.get("id")) for m in messages if m.get("id")]
    all_reactions=eco_get_reactions(mids)
    my_reactions=eco_get_my_reactions(mids, uid)
    st.markdown('<div class="wa-chat-bg">', unsafe_allow_html=True)
    seen=set()
    for m in messages:
        if m.get("deleted_at"):
            continue
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
            if url and typ.startswith("image"):
                attach_html=f'<img src="{url}" style="max-width:100%;border-radius:10px;margin:4px 0;" />'
            elif url and typ.startswith("video"):
                attach_html=f'<div>🎬 <a href="{url}" target="_blank">Watch video</a></div>'
            elif url:
                attach_html=f'<div>📎 <a href="{url}" target="_blank">{m.get("attachment_name") or "Open attachment"}</a></div>'
        if attach_html or body:
            if attach_html:
                st.markdown(f'<div class="{"wa-bubble-me" if sent else "wa-bubble-other"}">{("<div class=\"wa-sender\">"+name+"</div>") if (not sent and name) else ""}{attach_html}{("<div>"+body.replace("<","&lt;").replace(">","&gt;")+"</div>") if body else ""}<div class="wa-meta">{eco_time_short(m.get("created_at"))}{" ✓✓" if sent else ""}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(eco_bubble_html(body, eco_time_short(m.get("created_at")), sent, "" if sent else name, bool(m.get("edited_at"))), unsafe_allow_html=True)
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
            st.session_state.eco_react_open_id=None if is_open else real_id
            st.rerun()
        if is_open:
            picked=st.pills("React", REACTION_EMOJIS, key=f"eco_pills_{'g' if is_group else 'd'}_{real_id}", label_visibility="collapsed")
            if picked:
                eco_toggle_reaction(real_id, uid, picked, is_group=is_group)
                st.session_state.eco_react_open_id=None
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def eco_composer(chat_id, is_group=False):
    st.markdown('<div style="background:#F0F2F5;padding:8px 6px;">', unsafe_allow_html=True)
    with st.form(f"eco_send_{'g' if is_group else 'd'}_{chat_id}", clear_on_submit=True):
        c1, c2, c3 = st.columns([6, 1, 1])
        with c1:
            msg = st.text_input("Message", label_visibility="collapsed", placeholder="Message")
        with c2:
            up = st.file_uploader("📎", label_visibility="collapsed", key=f"eco_up_{'g' if is_group else 'd'}_{chat_id}", type=["jpg","jpeg","png","webp","mp4","pdf","docx"])
        with c3:
            send = st.form_submit_button("➤")
        if send and (msg.strip() or up):
            try:
                data={"sender_id": uid, "message_text": msg.strip()}
                if is_group: data["group_id"]=chat_id
                else: data["chat_id"]=chat_id
                if up:
                    path=eco_upload_file(up, "chat")
                    data["attachment_path"]=path
                    data["attachment_type"]=up.type
                    data["attachment_name"]=up.name
                tbl="group_messages" if is_group else "messages"
                supabase.table(tbl).insert(data).execute()
                st.rerun()
            except Exception as e:
                st.error(str(e))
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- CHATS ----------
if st.session_state.eco_current_page=="Chats":
    if st.session_state.eco_chat_id:
        cid=st.session_state.eco_chat_id
        try:
            msgs=supabase.table("messages").select("*").eq("chat_id", cid).order("created_at").execute().data or []
        except Exception:
            msgs=[]
        eco_render_chat(msgs, is_group=False, chat_id=cid)
        eco_composer(cid, is_group=False)
        if st.button("⬅️ Back to chats"):
            st.session_state.eco_chat_id=None; st.rerun()
    else:
        st.markdown("### 💬 Chats")
        try:
            chats=supabase.table("direct_chats").select("*").or_(f"user1.eq.{uid},user2.eq.{uid}").order("created_at", desc=True).execute().data or []
        except Exception:
            chats=[]
        if not chats:
            st.info("No chats yet. Go to Discover to find people.")
        for ch in chats:
            other=ch.get("user2") if str(ch.get("user1"))==str(uid) else ch.get("user1")
            p=eco_profile_with_avatar(other)
            if st.button(f"{eco_display_name(p)}  •  Tap to chat", key=f"eco_chat_{ch.get('id')}"):
                st.session_state.eco_chat_id=ch.get("id"); st.session_state.eco_chat_type="direct"; st.rerun()

# ---------- CHAT ROOMS ----------
elif st.session_state.eco_current_page=="Chat Rooms":
    if st.session_state.eco_chat_id:
        gid=st.session_state.eco_chat_id
        try:
            grp=supabase.table("groups").select("*").eq("id", gid).single().execute().data or {}
        except Exception:
            grp={}
        c1, c2 = st.columns([4, 1])
        with c1: st.markdown(f"### 👥 {grp.get('name') or 'Chat Room'}")
        with c2:
            if st.button("👥 Members"): st.session_state.eco_show_members=not st.session_state.eco_show_members; st.rerun()
        if st.session_state.eco_show_members:
            try:
                mems=supabase.table("group_members").select("*").eq("group_id", gid).execute().data or []
                for mm in mems:
                    pp=eco_profile_with_avatar(mm.get("user_id"))
                    st.write(f"{eco_display_name(pp)} — {mm.get('role') or 'Member'}")
            except Exception: pass
            if st.button("✕ Close members"): st.session_state.eco_show_members=False; st.rerun()
        try:
            msgs=supabase.table("group_messages").select("*").eq("group_id", gid).order("created_at").execute().data or []
        except Exception:
            msgs=[]
        eco_render_chat(msgs, is_group=True, chat_id=gid)
        eco_composer(gid, is_group=True)
        if st.button("⬅️ Back to Chat Rooms"):
            st.session_state.eco_chat_id=None; st.rerun()
    else:
        st.markdown("### 👥 Chat Rooms")
        with st.expander("➕ Create New Chat Room"):
            gname=st.text_input("Chat Room Name")
            gdesc=st.text_area("Description (optional)")
            if st.button("Create Chat Room"):
                if not gname.strip(): st.error("Enter a name")
                else:
                    try:
                        payload={"name": gname.strip(), "description": gdesc, "created_by": uid}
                        try: payload["invite_code"]=str(uuid.uuid4())[:8].upper()
                        except Exception: pass
                        r=supabase.table("groups").insert(payload).execute()
                        gid=r.data[0].get("id")
                        supabase.table("group_members").insert({"group_id": gid, "user_id": uid, "role": "Admin"}).execute()
                        st.success("Chat Room created!")
                        st.rerun()
                    except Exception as e: st.error(str(e))
        with st.expander("🔗 Join Chat Room via Code"):
            code=st.text_input("Invite Code")
            if st.button("Join"):
                try:
                    r=supabase.table("groups").select("*").eq("invite_code", code.strip().upper()).single().execute()
                    if r.data:
                        supabase.table("group_members").insert({"group_id": r.data.get("id"), "user_id": uid, "role": "Member"}).execute()
                        st.success("Joined!"); st.rerun()
                    else: st.error("Code not found")
                except Exception as e: st.error(str(e))
        try:
            mems=supabase.table("group_members").select("group_id").eq("user_id", uid).execute().data or []
            gids=[m.get("group_id") for m in mems]
            if gids:
                rooms=supabase.table("groups").select("*").in_("id", gids).execute().data or []
            else: rooms=[]
        except Exception: rooms=[]
        for room in rooms:
            if st.button(f"👥 {room.get('name')}  •  Tap to open", key=f"eco_room_{room.get('id')}"):
                st.session_state.eco_chat_id=room.get("id"); st.session_state.eco_chat_type="group"; st.rerun()
        if not rooms: st.info("No Chat Rooms yet. Create one above.")

# ---------- UPDATES - WHATSAPP STYLE ----------
elif st.session_state.eco_current_page=="Updates":
    st.markdown('<div class="wa-updates">', unsafe_allow_html=True)
    st.markdown('<div style="display:flex;justify-content:space-between;padding:16px;"><b style="font-size:24px;color:white;">Updates</b><span style="color:white;">🔍 ⋮</span></div>', unsafe_allow_html=True)
    st.markdown('<div style="padding:0 16px;font-size:18px;font-weight:700;color:white;">Status</div>', unsafe_allow_html=True)
    # Add status
    if st.button("➕ Add your status", key="eco_add_status_btn"):
        st.session_state.eco_show_add_status=True
    if st.session_state.eco_show_add_status:
        up=st.file_uploader("Tap here to pick photo / video for story", type=["jpg","jpeg","png","webp","mp4","mov"], key="eco_status_up")
        cap=st.text_input("Add a caption (optional)", key="eco_status_cap")
        if st.button("Publish story"):
            if up:
                try:
                    path=eco_upload_file(up, "stories")
                    supabase.table("stories").insert({"user_id": uid, "media_path": path, "caption": cap, "created_at": datetime.utcnow().isoformat()}).execute()
                    st.session_state.eco_show_add_status=False
                    st.success("Story published!"); st.rerun()
                except Exception as e: st.error(str(e))
            else: st.error("Pick a photo first")
    # Load stories last 24h
    try:
        since=(datetime.utcnow()-timedelta(hours=24)).isoformat()
        stories=supabase.table("stories").select("*").gte("created_at", since).order("created_at", desc=True).execute().data or []
    except Exception: stories=[]
    # Status cards row - use columns for Streamlit, styled as cards
    if stories:
        cols=st.columns(min(len(stories)+1, 4))
        # My status is first handled in loop, but show all as cards
        for i, s in enumerate(stories):
            with cols[i % len(cols)]:
                url=eco_storage_url(s.get("media_path") or s.get("image_path") or "")
                name=eco_display_name(eco_profile_with_avatar(s.get("user_id")))
                if url:
                    st.image(url, use_container_width=True)
                st.caption(name)
                if st.button("View", key=f"eco_story_view_{s.get('id')}"):
                    st.session_state.eco_open_story_id=s.get("id"); st.rerun()
    else:
        st.caption("No stories yet. Be the first to post.")
    # Open story - shows picture, never Media: path
    if st.session_state.eco_open_story_id:
        sid=st.session_state.eco_open_story_id
        s=next((x for x in stories if str(x.get("id"))==str(sid)), None)
        if s:
            if st.button("✕ Close story"):
                st.session_state.eco_open_story_id=None; st.rerun()
            url=eco_storage_url(s.get("media_path") or s.get("image_path") or "")
            st.markdown(f"### {eco_display_name(eco_profile_with_avatar(s.get('user_id')))}")
            st.caption(f"{eco_time_short(s.get('created_at'))} • disappears in 24h")
            if url:
                if url.lower().split("?")[0].endswith((".mp4",".mov",".webm")): st.video(url)
                else: st.image(url, use_container_width=True)
            if s.get("caption"): st.write(s.get("caption"))
            st.write(f"👁️ {s.get('views_count', 0)} views")
            if st.button("Delete this story"):
                try: supabase.table("stories").delete().eq("id", sid).execute()
                except Exception: pass
                st.session_state.eco_open_story_id=None; st.rerun()
    # Channels = Chat Rooms
    st.markdown('<div style="display:flex;justify-content:space-between;padding:16px;"><b style="font-size:18px;color:white;">Channels</b><span style="background:#1F2C34;color:white;padding:6px 12px;border-radius:20px;font-size:13px;">Explore</span></div>', unsafe_allow_html=True)
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

# ---------- DISCOVER ----------
elif st.session_state.eco_current_page=="Discover":
    st.markdown("### 🔎 Discover")
    q=st.text_input("Search username, name, or location")
    try:
        if q.strip():
            profs=supabase.table("profiles").select("*").or_(f"username.ilike.%{q}%,display_name.ilike.%{q}%,location.ilike.%{q}%").limit(20).execute().data or []
        else:
            profs=supabase.table("profiles").select("*").neq("id", uid).limit(20).execute().data or []
    except Exception: profs=[]
    for p in profs:
        if str(p.get("id"))==str(uid): continue
        c1, c2 = st.columns([1, 3])
        with c1:
            if p.get("avatar_url"): st.image(eco_storage_url(p.get("avatar_url")), width=60)
            else: st.markdown(f"<div style='width:60px;height:60px;border-radius:50%;background:#DFE5E7;display:flex;align-items:center;justify-content:center;font-weight:700;'>{eco_display_name(p)[:2].upper()}</div>", unsafe_allow_html=True)
        with c2:
            st.write(f"**{eco_display_name(p)}**  @{p.get('username') or ''}")
            st.caption(f"{p.get('location') or ''} • {p.get('interests') or ''}")
            if st.button("👀 View Profile", key=f"eco_disc_view_{p.get('id')}"):
                st.session_state.eco_view_profile_id=p.get("id"); st.rerun()

# ---------- PROFILE ----------
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
                payload={"display_name": dn, "bio": bio, "location": loc, "interests": inter, "instagram": ig, "tiktok": tt}
                if av:
                    payload["avatar_url"]=eco_upload_file(av, "avatars")
                supabase.table("profiles").update(payload).eq("id", uid).execute()
                st.success("Saved!"); st.rerun()
            except Exception as e: st.error(str(e))
    if st.button("Logout"):
        supabase.auth.sign_out(); st.session_state.uid=None; st.rerun()

st.caption("Powered by Next Gen Impact Hub (NGIH) — Talk like home, connect like family.")
