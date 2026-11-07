# ============================================================
# ECOLOOP NODE — COMMUNITY HUB — WHATSAPP 2.0 — FULL REDO
# Paste whole file, replace old community_hub.py, Reboot
# No bottom overrides. No patches.
# ============================================================
import mimetypes, os, re, uuid
from datetime import datetime, timedelta, timezone
import streamlit as st

BUCKET = "community-media"
MAX_IMAGE_MB = 8
MAX_VIDEO_MB = 35
MAIN_NAV_KEY = "eco_community_navigation_v3"

def eco_now(): return datetime.now(timezone.utc)
def eco_iso(v=None):
    v = v or eco_now()
    return v if isinstance(v, str) else v.isoformat()
def eco_safe_text(v, d=""):
    t = str(v or "").strip()
    return t if t else d
def eco_init_state():
    defaults = {"eco_community_section":"Chats","eco_chat_view":"Inbox","eco_active_conversation":None,"eco_active_chatroom":None,"eco_group_view":"Discover","eco_story_view":"Stories","eco_profile_view_user":None,"eco_story_open_id":None,"eco_group_members_open":None}
    for k,v in defaults.items():
        if k not in st.session_state: st.session_state[k]=v
def eco_result_data(r):
    try: return r.data or []
    except Exception: return []
def eco_select(supabase, table, cols="*", filters=None, order=None, limit=None):
    q = supabase.table(table).select(cols)
    for m,c,v in (filters or []):
        if m=="is_": q=q.is_(c, None if v in ("null",None) else v)
        else: q=getattr(q,m)(c,v)
    if order: q=q.order(order[0], desc=order[1])
    if limit: q=q.limit(limit)
    return eco_result_data(q.execute())
def eco_profile(supabase, uid):
    if not uid: return {}
    try:
        rows = eco_select(supabase,"member_profiles","*",[("eq","user_id",uid)],limit=1)
        return rows[0] if rows else {}
    except Exception: return {}
def eco_profile_with_avatar(supabase, uid):
    p = eco_profile(supabase, uid)
    if p: p["_avatar_resolved"]=eco_storage_url(supabase, p.get("avatar_url"))
    return p
def eco_display_name(p, fb="EcoLoop member"): return eco_safe_text((p or {}).get("display_name") or (p or {}).get("username"), fb)
def eco_initials(n):
    w=[x for x in str(n or "E").strip().split() if x]
    return "".join(x[0].upper() for x in w[:2]) or "E"
def eco_storage_url(supabase, path, expires=3600):
    if not path: return ""
    if str(path).startswith("http"): return str(path)
    try:
        r=supabase.storage.from_(BUCKET).create_signed_url(path, expires)
        if hasattr(r,"signed_url"): return r.signed_url or ""
        if isinstance(r, dict): return r.get("signedURL") or r.get("signedUrl") or ""
        return str(r) if isinstance(r,str) else ""
    except Exception: return ""
def eco_upload(supabase, up, folder, uid, allow_video=False, allow_doc=False):
    if not up: return ""
    name=os.path.basename(up.name or "upload"); ext=os.path.splitext(name)[1].lower()
    allowed={".jpg",".jpeg",".png",".webp"} | ({".mp4",".mov",".webm"} if allow_video else set()) | ({".pdf",".docx"} if allow_doc else set())
    if ext not in allowed: raise ValueError("Choose a supported image/video/file.")
    lim=MAX_VIDEO_MB if ext in {".mp4",".mov",".webm"} else MAX_IMAGE_MB
    if getattr(up,"size",0)>lim*1024*1024: raise ValueError(f"Too large. Max {lim} MB.")
    path=f"{folder}/{uid}/{uuid.uuid4().hex}{ext}"
    supabase.storage.from_(BUCKET).upload(path, up.getvalue(), {"content-type": up.type or mimetypes.guess_type(name)[0] or "application/octet-stream","upsert":"false"})
    return path
def _parse_dt(v):
    if not v: return None
    try: return datetime.fromisoformat(str(v).replace("Z","+00:00"))
    except Exception: return None
def eco_time_label(v):
    dt=_parse_dt(v)
    if not dt: return ""
    try:
        local=dt.astimezone(); today=eco_now().astimezone().date()
        if local.date()==today: return local.strftime("%H:%M")
        if (today-local.date()).days==1: return "Yesterday"
        return local.strftime("%d/%m/%Y")
    except Exception: return str(v)[:16]
def eco_time_short(v):
    dt=_parse_dt(v)
    return dt.astimezone().strftime("%H:%M") if dt else ""

def eco_inject_styles():
    st.markdown("""
    <style>
    .block-container{padding:0!important;max-width:100%!important}
    header[data-testid="stHeader"]{display:none} [data-testid="stSidebar"]{display:none}
    .wa-topbar{background:#075E54;color:white;padding:12px 16px;display:flex;align-items:center;justify-content:space-between}
    .wa-topbar b{font-size:19px} .wa-topbar span{font-size:12px;opacity:.9}
    .wa-chat-bg{background:#ECE5DD;background-image:radial-gradient(#d5d0c8 .6px,transparent .6px);background-size:18px 18px;min-height:72vh;padding:14px 10px 16px 10px;border-radius:10px}
    .wa-bubble-me{background:#DCF8C6;border-radius:10px 10px 0 10px;padding:8px 10px;margin:5px 0 5px auto;max-width:80%;width:fit-content;box-shadow:0 1px 1px rgba(0,0,0,.08);font-size:14.5px;line-height:1.4}
    .wa-bubble-other{background:#fff;border-radius:10px 10px 10px 0;padding:8px 10px;margin:5px auto 5px 0;max-width:80%;width:fit-content;box-shadow:0 1px 1px rgba(0,0,0,.08);font-size:14.5px;line-height:1.4}
    .wa-meta{font-size:11px;color:#667781;text-align:right;margin-top:2px}
    .wa-sender{font-size:12px;font-weight:700;color:#128C7E;margin-bottom:2px}
    .wa-avatar{width:44px;height:44px;border-radius:50%;background:#DFE5E7;display:flex;align-items:center;justify-content:center;font-weight:700;color:#54656F;font-size:16px;flex-shrink:0;overflow:hidden}
    .wa-unread{background:#25D366;color:white;font-size:11px;font-weight:700;min-width:20px;height:20px;border-radius:20px;display:flex;align-items:center;justify-content:center;padding:0 6px}
    .wa-empty{height:60vh;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#F8F9FA;color:#667781;text-align:center;padding:30px;border-radius:10px}
    .wa-composer{background:#F0F2F5;padding:8px;border-radius:12px}
    </style>""", unsafe_allow_html=True)

def eco_avatar_html(profile, size=44):
    name=eco_display_name(profile)
    url=(profile.get("_avatar_resolved") or profile.get("avatar_url")) if profile else None
    if url and str(url).startswith("http"):
        return f'<img src="{url}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;" />'
    return f'<div class="wa-avatar" style="width:{size}px;height:{size}px;">{eco_initials(name)}</div>'

def eco_bubble_html(text, time_label, is_me, sender_name="", edited=False):
    safe=str(text or "").replace("<","&lt;").replace(">","&gt;").replace("\n","<br>")
    tick=" ✓✓" if is_me else ""; edit=" · edited" if edited else ""
    sender=f'<div class="wa-sender">{sender_name}</div>' if (not is_me and sender_name) else ""
    cls="wa-bubble-me" if is_me else "wa-bubble-other"
    return f'<div class="{cls}">{sender}<div>{safe}</div><div class="wa-meta">{time_label}{edit}{tick}</div></div>'

def eco_render_bubbles_html(supabase, messages, uid, is_group=False):
    html=['<div class="wa-chat-bg">']
    if not messages:
        html.append('<div class="wa-empty"><div style="font-size:48px;">💬</div><b>Say hi</b><p>This is the beginning of your conversation.</p></div>')
    for m in messages:
        if m.get("deleted_at"): continue
        sent=str(m.get("sender_id"))==str(uid)
        sender=eco_profile_with_avatar(supabase, m.get("sender_id")) if is_group else {}
        name="You" if sent else eco_display_name(sender)
        body=str(m.get("message_text") or "")
        atts=[]
        if m.get("attachment_path"): atts=[{"path":m.get("attachment_path"),"type":m.get("attachment_type") or "","name":m.get("attachment_name") or "Attachment"}]
        if m.get("attachments"):
            a=m.get("attachments"); atts=a if isinstance(a,list) else [a]
        for it in atts:
            if not isinstance(it,dict): continue
            url=eco_storage_url(supabase, it.get("path") or it.get("url")); typ=str(it.get("type") or "")
            if url and typ.startswith("image"): html.append(f'<div style="text-align:{"right" if sent else "left"}"><img src="{url}" style="max-width:80%;border-radius:10px;margin:4px 0;" /></div>')
            elif url and typ.startswith("video"): html.append(f'<div>🎬 <a href="{url}" target="_blank">Watch video</a></div>')
            elif url and typ.startswith("audio"): html.append(f'<div>🎤 <a href="{url}" target="_blank">Play voice note</a></div>')
            elif url: html.append(f'<div>📎 <a href="{url}" target="_blank">{it.get("name") or "Open attachment"}</a></div>')
        if body: html.append(eco_bubble_html(body, eco_time_short(m.get("created_at")), sent, "" if sent else name, bool(m.get("edited_at"))))
    html.append('</div>')
    st.markdown("".join(html), unsafe_allow_html=True)

def eco_back_to_dashboard():
    st.session_state["eco_active_conversation"]=None
    st.session_state["eco_active_chatroom"]=None
    st.session_state["eco_chat_view"]="Inbox"
    st.session_state["eco_community_section"]="Chats"
    st.session_state["eco_return_to_dashboard"]=True
    st.session_state["current_page"]="Dashboard"
    st.session_state["page"]="Dashboard"
    st.session_state["eco_page"]="Dashboard"
    st.rerun()

# ---------------- Profile ----------------
def save_member_profile(supabase, uid, values):
    payload={"user_id":uid}
    for k in ("display_name","username","bio","location","interests","country_of_origin","instagram_handle","facebook_handle","tiktok_handle","linkedin_handle","avatar_url"):
        if k in values: payload[k]=values[k]
    return supabase.table("member_profiles").upsert(payload, on_conflict="user_id").execute()

def render_profile_editor(supabase, uid):
    profile=eco_profile_with_avatar(supabase, uid)
    st.markdown('<div class="wa-topbar"><b>My Profile</b><span>ECOLOOP</span></div>', unsafe_allow_html=True)
    if st.button("← Back to Dashboard", key="eco_profile_back_dash"): eco_back_to_dashboard()
    if st.button("‹ Back to chats"):
        st.session_state.eco_chat_view="Inbox"; st.rerun()
    st.markdown(eco_avatar_html(profile, 96), unsafe_allow_html=True)
    st.caption("Tap Upload below to change your picture. No more grey avatar.")
    avatar_file=st.file_uploader("Update profile picture", type=["jpg","jpeg","png","webp"], key="eco_profile_avatar_upload")
    if avatar_file and st.button("Upload profile picture", key="eco_profile_avatar_save", use_container_width=True):
        try:
            path=eco_upload(supabase, avatar_file, "profiles", uid)
            save_member_profile(supabase, uid, {"avatar_url": path})
            st.success("Profile picture updated."); st.rerun()
        except Exception as e: st.error(f"Could not upload picture: {e}")
    with st.form("eco_profile_edit_form", clear_on_submit=False):
        display_name=st.text_input("Display name", value=profile.get("display_name",""))
        username=st.text_input("Username", value=profile.get("username",""), help="Unique, no spaces.")
        bio=st.text_area("About me", value=profile.get("bio",""), max_chars=240)
        location=st.text_input("Location (optional)", value=profile.get("location",""))
        country=st.text_input("Country of origin (optional)", value=profile.get("country_of_origin",""))
        interests=st.text_input("Interests (comma separated)", value=profile.get("interests",""))
        instagram=st.text_input("Instagram", value=profile.get("instagram_handle",""))
        facebook=st.text_input("Facebook", value=profile.get("facebook_handle",""))
        tiktok=st.text_input("TikTok", value=profile.get("tiktok_handle",""))
        linkedin=st.text_input("LinkedIn", value=profile.get("linkedin_handle",""))
        submitted=st.form_submit_button("Save profile", use_container_width=True)
    if submitted:
        username=re.sub(r"[^a-zA-Z0-9_.]","",username).lower()
        if len(username)<3: st.error("Choose a username with at least 3 letters or numbers.")
        else:
            try:
                save_member_profile(supabase, uid, {"display_name":display_name.strip(),"username":username,"bio":bio.strip(),"location":location.strip(),"country_of_origin":country.strip(),"interests":interests.strip(),"instagram_handle":instagram.strip(),"facebook_handle":facebook.strip(),"tiktok_handle":tiktok.strip(),"linkedin_handle":linkedin.strip()})
                st.success("Profile saved."); st.rerun()
            except Exception as e: st.error(f"Could not save. Username may be taken. Details: {e}")

def get_member_directory(supabase, search=""):
    q=(search or "").strip().lower().lstrip("@").strip()
    try:
        if not q: return eco_select(supabase,"member_profiles","*",order=("display_name",False),limit=150)
        found={}
        for col in ("username","display_name","location"):
            try:
                rows=eco_result_data(supabase.table("member_profiles").select("*").ilike(col,f"%{q}%").limit(100).execute())
                for r in rows:
                    uid=str(r.get("user_id") or r.get("id") or "")
                    if uid: found[uid]=r
            except Exception: continue
        return sorted(found.values(), key=lambda r: str(r.get("username") or "").lower())
    except Exception: return []

def render_member_card(supabase, profile, current_uid, suffix):
    profile=dict(profile); profile["_avatar_resolved"]=eco_storage_url(supabase, profile.get("avatar_url"))
    uid=profile.get("user_id"); name=eco_display_name(profile); username=eco_safe_text(profile.get("username"),"member")
    with st.container(border=True):
        c1,c2=st.columns([1,4])
        with c1: st.markdown(eco_avatar_html(profile), unsafe_allow_html=True)
        with c2:
            st.markdown(f"**{name}**"); st.caption(f"@{username}")
            if profile.get("bio"): st.write(str(profile["bio"])[:150])
            if profile.get("location"): st.caption(f"📍 {profile['location']}")
        if uid and uid!=current_uid:
            a,b=st.columns(2)
            with a:
                if st.button("View profile", key=f"eco_person_profile_{suffix}_{uid}", use_container_width=True):
                    st.session_state.eco_profile_view_user=uid; st.session_state.eco_chat_view="Profile"; st.rerun()
            with b:
                if st.button("Message", key=f"eco_person_message_{suffix}_{uid}", use_container_width=True):
                    try:
                        conv=get_or_create_direct_conversation(supabase, current_uid, uid)
                        st.session_state.eco_active_conversation=conv; st.session_state.eco_chat_view="Conversation"; st.rerun()
                    except Exception as e: st.error(f"Could not open chat: {e}")

def render_public_profile(supabase, uid, current_uid):
    profile=eco_profile_with_avatar(supabase, uid)
    if not profile: st.warning("This profile is not available."); return
    if st.button("← Back to Dashboard", key=f"eco_pub_back_dash_{uid}"): eco_back_to_dashboard()
    if st.button("‹ Back"):
        st.session_state.eco_chat_view="Discover People"; st.rerun()
    st.markdown(eco_avatar_html(profile, 110), unsafe_allow_html=True)
    st.subheader(eco_display_name(profile)); st.caption("@"+eco_safe_text(profile.get("username"),"member"))
    if profile.get("location"): st.caption("📍 "+str(profile["location"]))
    if profile.get("bio"): st.write(profile["bio"])
    if profile.get("interests"): st.caption("Interests: "+str(profile["interests"]))
    socials=[("Instagram","instagram_handle"),("Facebook","facebook_handle"),("TikTok","tiktok_handle"),("LinkedIn","linkedin_handle")]
    present=[f"**{l}:** @{profile[k].lstrip('@')}" for l,k in socials if profile.get(k)]
    if present: st.markdown(" · ".join(present))
    if uid!=current_uid and st.button("Message", key=f"eco_public_profile_message_{uid}", use_container_width=True):
        try:
            conv=get_or_create_direct_conversation(supabase, current_uid, uid)
            st.session_state.eco_active_conversation=conv; st.session_state.eco_chat_view="Conversation"; st.rerun()
        except Exception as e: st.error(f"Could not start conversation: {e}")

# ---------------- Direct Messages ----------------
def get_or_create_direct_conversation(supabase, a, b):
    first,second=sorted([str(a),str(b)])
    rows=eco_select(supabase,"direct_conversations","*",[("eq","user_one_id",first),("eq","user_two_id",second)],limit=1)
    if rows: return rows[0]["id"]
    res=supabase.table("direct_conversations").insert({"user_one_id":first,"user_two_id":second}).execute()
    rows=eco_result_data(res)
    if rows: return rows[0]["id"]
    rows=eco_select(supabase,"direct_conversations","*",[("eq","user_one_id",first),("eq","user_two_id",second)],limit=1)
    if not rows: raise RuntimeError("Conversation could not be created.")
    return rows[0]["id"]
def get_direct_conversations(supabase, uid):
    try:
        a=eco_select(supabase,"direct_conversations","*",[("eq","user_one_id",uid)],order=("created_at",True),limit=150)
        b=eco_select(supabase,"direct_conversations","*",[("eq","user_two_id",uid)],order=("created_at",True),limit=150)
        return list({str(r["id"]):r for r in a+b if r.get("id")}.values())
    except Exception: return []
def get_direct_messages(supabase, cid, limit=100):
    try: return eco_select(supabase,"direct_messages","*",[("eq","conversation_id",cid),("is_","deleted_at","null")],order=("created_at",False),limit=limit)
    except Exception: return []
def get_latest_direct_message(supabase, cid):
    try:
        rows=eco_select(supabase,"direct_messages","*",[("eq","conversation_id",cid),("is_","deleted_at","null")],order=("created_at",True),limit=1)
        return rows[0] if rows else {}
    except Exception: return {}
def send_direct_message(supabase, cid, sender, text, path="", name="", typ=""):
    payload={"conversation_id":cid,"sender_id":sender,"message_text":(text or "").strip(),"attachment_path":path or None,"attachment_name":name or None,"attachment_type":typ or None}
    if not payload["message_text"] and not path: return False
    supabase.table("direct_messages").insert(payload).execute(); return True
def mark_direct_read(supabase, cid, uid):
    try: supabase.table("direct_conversation_reads").upsert({"conversation_id":cid,"user_id":uid,"last_read_at":eco_iso()}, on_conflict="conversation_id,user_id").execute()
    except Exception: pass
def get_read_ts(supabase, cid, uid):
    try:
        rows=eco_select(supabase,"direct_conversation_reads","last_read_at",[("eq","conversation_id",cid),("eq","user_id",uid)],limit=1)
        return rows[0].get("last_read_at") if rows else None
    except Exception: return None
def get_other_user(conv, cur): return conv.get("user_two_id") if str(conv.get("user_one_id"))==str(cur) else conv.get("user_one_id")

def render_whatsapp_composer(supabase, uid, conversation_id=None, group_id=None):
    st.markdown('<div class="wa-composer">', unsafe_allow_html=True)
    c1,c2,c3,c4=st.columns([1,6,1,1])
    with c1: attach=st.file_uploader("📎", type=["jpg","jpeg","png","webp","mp4","mov","pdf","docx"], label_visibility="collapsed", key=f"attach_{conversation_id or group_id}")
    with c2: text=st.text_input("Type a message...", label_visibility="collapsed", key=f"txt_{conversation_id or group_id}")
    with c3: voice=st.audio_input("🎤", label_visibility="collapsed", key=f"voice_{conversation_id or group_id}")
    with c4: send=st.button("➤", key=f"send_{conversation_id or group_id}")
    st.markdown('</div>', unsafe_allow_html=True)
    if not (send or voice is not None): return
    try:
        if voice is not None:
            path=f"voice/{uid}/{uuid.uuid4().hex}.wav"
            supabase.storage.from_(BUCKET).upload(path, voice.getvalue(), {"content-type":"audio/wav"})
            if conversation_id: send_direct_message(supabase, conversation_id, uid, "🎤 Voice note", path, "voice.wav", "audio")
            if group_id: supabase.table("group_messages").insert({"group_id":group_id,"sender_id":uid,"message_text":"🎤 Voice note","attachments":[{"path":path,"name":"voice.wav","type":"audio"}]}).execute()
            st.rerun()
        apath=""; aname=""; atyp=""
        if attach is not None:
            apath=eco_upload(supabase, attach, "chat", uid, allow_video=True, allow_doc=True); aname=attach.name; atyp=attach.type or ""
        if text.strip() or apath:
            if conversation_id: send_direct_message(supabase, conversation_id, uid, text or aname or "Attachment", apath, aname, atyp)
            if group_id: supabase.table("group_messages").insert({"group_id":group_id,"sender_id":uid,"message_text":text.strip() or aname or "Attachment","attachments":[{"path":apath,"name":aname,"type":atyp}] if apath else []}).execute()
            st.rerun()
    except Exception as e: st.error(f"Message could not be sent: {e}")

def render_direct_conversation(supabase, uid):
    cid=st.session_state.eco_active_conversation
    if not cid: st.session_state.eco_chat_view="Inbox"; st.rerun(); return
    convs=get_direct_conversations(supabase, uid)
    conv=next((c for c in convs if str(c.get("id"))==str(cid)), None)
    if not conv:
        st.error("This conversation is no longer available.")
        if st.button("‹ Back to chats"): st.session_state.eco_active_conversation=None; st.session_state.eco_chat_view="Inbox"; st.rerun()
        return
    other_id=get_other_user(conv, uid); other=eco_profile_with_avatar(supabase, other_id); name=eco_display_name(other)
    if st.button("← Back to Dashboard", key="eco_dm_back_dashboard"): eco_back_to_dashboard()
    h1,h2,h3=st.columns([0.6,1,5])
    with h1:
        if st.button("‹", key="eco_dm_back"): st.session_state.eco_active_conversation=None; st.session_state.eco_chat_view="Inbox"; st.rerun()
    with h2: st.markdown(eco_avatar_html(other,40), unsafe_allow_html=True)
    with h3: st.markdown(f"**{name}**"); st.caption("@"+eco_safe_text(other.get("username"),"member")+" · Online")
    mark_direct_read(supabase, cid, uid)
    msgs=get_direct_messages(supabase, cid)
    eco_render_bubbles_html(supabase, msgs, uid, is_group=False)
    render_whatsapp_composer(supabase, uid, conversation_id=cid)

def render_whatsapp_inbox(supabase, uid):
    search=st.text_input("Search or start new chat", key="eco_sidebar_search_input", placeholder="Search chats…", label_visibility="collapsed")
    c1,c2=st.columns(2)
    with c1:
        if st.button("＋ New chat", key="eco_new_chat_button", use_container_width=True): st.session_state.eco_chat_view="Discover People"; st.rerun()
    with c2:
        if st.button("My profile", key="eco_my_profile_button", use_container_width=True): st.session_state.eco_chat_view="My Profile"; st.rerun()
    st.divider()
    convs=get_direct_conversations(supabase, uid); enriched=[]
    for conv in convs:
        oid=get_other_user(conv, uid); prof=eco_profile_with_avatar(supabase, oid); latest=get_latest_direct_message(supabase, conv.get("id")); read_at=get_read_ts(supabase, conv.get("id"), uid); unread=0
        if read_at and latest and str(latest.get("sender_id"))!=str(uid):
            rd=_parse_dt(read_at); md=_parse_dt(latest.get("created_at"))
            if rd and md and md>rd: unread=1
        q=(search or "").strip().lower()
        if q and q not in eco_display_name(prof).lower() and q not in str(prof.get("username","")).lower(): continue
        enriched.append((latest.get("created_at") or conv.get("created_at") or "", conv, prof, latest, unread))
    enriched.sort(key=lambda x: x[0] or "", reverse=True)
    if not enriched: st.info("No chats yet. Tap + New chat to start one."); return
    for _,conv,prof,latest,unread in enriched:
        name=eco_display_name(prof); preview=eco_safe_text(latest.get("message_text"), "📎 Attachment" if latest.get("attachment_path") else "No messages yet")
        if str(latest.get("sender_id"))==str(uid): preview="✓✓ You: "+preview
        with st.container(border=True):
            a,b,c=st.columns([0.9,3.5,1])
            with a: st.markdown(eco_avatar_html(prof,44), unsafe_allow_html=True)
            with b: st.markdown(f"**{name}**"); st.caption(preview[:60]); st.caption("@"+eco_safe_text(prof.get("username"),"member"))
            with c:
                st.caption(eco_time_label(latest.get("created_at") or conv.get("created_at")))
                if unread: st.markdown(f'<div class="wa-unread">{unread}</div>', unsafe_allow_html=True)
                if st.button("Open", key=f"eco_inbox_open_{conv.get('id')}", use_container_width=True):
                    st.session_state.eco_active_conversation=conv.get("id"); st.session_state.eco_chat_view="Conversation"; st.rerun()

def render_chats_section(supabase, uid):
    v=st.session_state.get("eco_chat_view","Inbox")
    if v=="Conversation": render_direct_conversation(supabase, uid); return
    if v=="Profile": render_public_profile(supabase, st.session_state.get("eco_profile_view_user"), uid); return
    if v=="Discover People":
        st.markdown('<div class="wa-topbar"><b>New Chat</b><span>Find people</span></div>', unsafe_allow_html=True)
        if st.button("← Back to Dashboard", key="eco_newchat_back_dash"): eco_back_to_dashboard()
        if st.button("‹ Back"): st.session_state.eco_chat_view="Inbox"; st.rerun()
        q=st.text_input("Search people", key="eco_people_search_input", placeholder="Search username or name…")
        profs=[p for p in get_member_directory(supabase, q) if p.get("user_id")!=uid]
        if not profs: st.info("No members found yet. Try another username."); return
        for i,p in enumerate(profs): render_member_card(supabase, p, uid, f"directory_{i}")
        return
    if v=="My Profile": render_profile_editor(supabase, uid); return
    render_whatsapp_inbox(supabase, uid)

# ---------------- Groups ----------------
def get_chatrooms(supabase, search=""):
    try:
        rows=eco_select(supabase,"community_groups","*",order=("created_at",True),limit=150)
        q=(search or "").strip().lower()
        if q: rows=[r for r in rows if q in str(r.get("name","")).lower() or q in str(r.get("description","")).lower() or q in str(r.get("location","")).lower()]
        return rows
    except Exception: return []
def get_my_chatrooms(supabase, uid):
    try:
        ms=eco_select(supabase,"group_memberships","*",[("eq","user_id",uid),("eq","status","approved")],limit=200)
        ids={str(m.get("group_id")) for m in ms}
        return [g for g in get_chatrooms(supabase) if str(g.get("id")) in ids]
    except Exception: return []
def create_chatroom(supabase, uid, name, desc, img="", loc=""):
    res=supabase.table("community_groups").insert({"name":name.strip(),"description":desc.strip(),"created_by":uid,"image_url":img or None,"location":loc.strip() or None}).execute()
    rows=eco_result_data(res); gid=rows[0].get("id") if rows else None
    if not gid:
        m=eco_select(supabase,"community_groups","*",[("eq","created_by",uid),("eq","name",name.strip())],order=("created_at",True),limit=1); gid=m[0].get("id") if m else None
    if gid:
        try: supabase.table("group_memberships").upsert({"group_id":gid,"user_id":uid,"membership_role":"admin","status":"approved"}, on_conflict="group_id,user_id").execute()
        except Exception: pass
    return gid
def request_join(supabase, gid, uid): return supabase.table("group_memberships").upsert({"group_id":gid,"user_id":uid,"membership_role":"member","status":"pending"}, on_conflict="group_id,user_id").execute()
def leave_chatroom(supabase, gid, uid): return supabase.table("group_memberships").delete().eq("group_id",gid).eq("user_id",uid).execute()
def is_member(supabase, group, uid):
    try:
        rows=eco_select(supabase,"group_memberships","*",[("eq","group_id",group.get("id")),("eq","user_id",uid),("eq","status","approved")],limit=1)
        return bool(rows)
    except Exception: return str(group.get("created_by"))==str(uid)
def get_membership(supabase, gid, uid):
    try:
        rows=eco_select(supabase,"group_memberships","*",[("eq","group_id",gid),("eq","user_id",uid)],limit=1); return rows[0] if rows else {}
    except Exception: return {}
def get_group_messages(supabase, gid, limit=100):
    try: return eco_select(supabase,"group_messages","*",[("eq","group_id",gid),("is_","deleted_at","null")],order=("created_at",False),limit=limit)
    except Exception: return []
def get_group_members(supabase, gid):
    try:
        ms=eco_select(supabase,"group_memberships","*",[("eq","group_id",gid),("eq","status","approved")],limit=200)
        out=[]
        for m in ms:
            p=eco_profile_with_avatar(supabase, m.get("user_id"))
            if p: p["_role"]=m.get("membership_role"); out.append(p)
        return out
    except Exception: return []

def render_chatroom_chat(supabase, group, uid):
    gid=group.get("id")
    if not is_member(supabase, group, uid):
        st.warning("You need approved membership to view this group chat.")
        if st.button("‹ Back to groups"): st.session_state.eco_active_chatroom=None; st.rerun()
        return
    if st.button("← Back to Dashboard", key=f"eco_room_back_dash_{gid}"): eco_back_to_dashboard()
    h1,h2=st.columns([0.6,5])
    with h1:
        if st.button("‹", key=f"eco_room_back_{gid}"): st.session_state.eco_active_chatroom=None; st.rerun()
    with h2: st.markdown(f"**{group.get('name','Community group')}**"); st.caption(eco_safe_text(group.get("description"),"Community conversation"))
    if st.button(f"👥 Members ({len(get_group_members(supabase, gid))}) — tap to see", key=f"eco_members_btn_{gid}"):
        st.session_state.eco_group_members_open=gid if st.session_state.get("eco_group_members_open")!=gid else None; st.rerun()
    if st.session_state.get("eco_group_members_open")==gid:
        st.markdown("### Members")
        for i,m in enumerate(get_group_members(supabase, gid)):
            with st.container(border=True):
                c1,c2=st.columns([1,4])
                with c1: st.markdown(eco_avatar_html(m,44), unsafe_allow_html=True)
                with c2: st.markdown(f"**{eco_display_name(m)}**"); st.caption(f"@{eco_safe_text(m.get('username'),'member')} · {m.get('_role','member')}")
            if str(m.get("user_id"))!=str(uid) and st.button("View profile", key=f"eco_member_view_{gid}_{i}"):
                st.session_state.eco_profile_view_user=m.get("user_id"); st.session_state.eco_chat_view="Profile"; st.rerun()
    msgs=get_group_messages(supabase, gid)
    eco_render_bubbles_html(supabase, msgs, uid, is_group=True)
    render_whatsapp_composer(supabase, uid, group_id=gid)

def _render_group_card(supabase, group, uid, idx, view):
    gid=group.get("id"); mem=get_membership(supabase, gid, uid); status=mem.get("status"); is_owner=str(group.get("created_by"))==str(uid); approved=status=="approved" or is_owner
    with st.container(border=True):
        img=eco_storage_url(supabase, group.get("image_url"))
        if img: st.image(img, use_container_width=True)
        else: st.markdown(f'<div class="wa-avatar">{eco_initials(group.get("name","G"))}</div>', unsafe_allow_html=True)
        st.markdown(f"**{group.get('name','Community group')}**")
        if group.get("location"): st.caption("📍 "+str(group["location"]))
        st.write(str(group.get("description") or "A space for people to connect.")[:220])
        if approved:
            st.caption("🟢 Member" if not is_owner else "⭐ Group admin")
            if st.button("Open group chat", key=f"eco_group_open_{view}_{gid}_{idx}", use_container_width=True): st.session_state.eco_active_chatroom=gid; st.rerun()
            if not is_owner and st.button("Leave group", key=f"eco_group_leave_{view}_{gid}_{idx}"):
                try: leave_chatroom(supabase, gid, uid); st.success("You left the group."); st.rerun()
                except Exception as e: st.error(f"Could not leave: {e}")
        elif status=="pending": st.info("Your join request is waiting for approval.")
        elif status=="rejected":
            st.caption("Your previous request was not approved.")
            if st.button("Request to join again", key=f"eco_group_rejoin_{view}_{gid}_{idx}", use_container_width=True):
                try: request_join(supabase, gid, uid); st.success("Join request sent."); st.rerun()
                except Exception as e: st.error(f"Could not request: {e}")
        else:
            if st.button("Request to join", key=f"eco_group_join_{view}_{gid}_{idx}", use_container_width=True):
                try: request_join(supabase, gid, uid); st.success("Join request sent."); st.rerun()
                except Exception as e: st.error(f"Could not request: {e}")

def render_chatrooms_page(supabase, uid):
    if st.session_state.get("eco_active_chatroom"):
        gid=st.session_state.eco_active_chatroom; group=next((g for g in get_chatrooms(supabase) if str(g.get("id"))==str(gid)), None)
        if group: render_chatroom_chat(supabase, group, uid)
        else:
            st.warning("This group could not be found.")
            if st.button("Back to groups"): st.session_state.eco_active_chatroom=None; st.rerun()
        return
    st.markdown('<div class="wa-topbar"><b>Groups</b><span>Community</span></div>', unsafe_allow_html=True)
    if st.button("← Back to Dashboard", key="eco_groups_back_dash"): eco_back_to_dashboard()
    views=["Discover","My Groups","Create"]; cur=st.session_state.get("eco_group_view","Discover")
    sel=st.radio("Group sections", views, horizontal=True, key="eco_group_view_radio", label_visibility="collapsed", index=views.index(cur) if cur in views else 0); st.session_state.eco_group_view=sel
    if sel=="Discover":
        s=st.text_input("Search groups", placeholder="Search by group name, topic or location…", key="eco_group_search")
        for i,g in enumerate(get_chatrooms(supabase, s)): _render_group_card(supabase, g, uid, i, "discover")
    elif sel=="My Groups":
        groups=get_my_chatrooms(supabase, uid)
        if not groups: st.info("You have not joined any groups yet.")
        for i,g in enumerate(groups): _render_group_card(supabase, g, uid, i, "mine")
        for g in groups:
            if str(g.get("created_by"))!=str(uid): continue
            with st.expander(f"Manage requests · {g.get('name','Group')}"):
                try: pending=eco_select(supabase,"group_memberships","*",[("eq","group_id",g.get("id")),("eq","status","pending")],limit=100)
                except Exception: pending=[]
                if not pending: st.caption("No pending requests.")
                for j,req in enumerate(pending):
                    person=eco_profile_with_avatar(supabase, req.get("user_id"))
                    a,b,c=st.columns([3,1,1])
                    with a: st.write(eco_display_name(person)); st.caption("@"+eco_safe_text(person.get("username"),"member"))
                    with b:
                        if st.button("Approve", key=f"eco_req_approve_{g.get('id')}_{j}"):
                            try: supabase.table("group_memberships").update({"status":"approved"}).eq("group_id",g.get("id")).eq("user_id",req.get("user_id")).execute(); st.rerun()
                            except Exception as e: st.error(str(e))
                    with c:
                        if st.button("Reject", key=f"eco_req_reject_{g.get('id')}_{j}"):
                            try: supabase.table("group_memberships").update({"status":"rejected"}).eq("group_id",g.get("id")).eq("user_id",req.get("user_id")).execute(); st.rerun()
                            except Exception as e: st.error(str(e))
    else:
        with st.form("eco_create_group_form", clear_on_submit=True):
            name=st.text_input("Group name", placeholder="e.g. Bulawayo Climate Action"); desc=st.text_area("What is this group about?", max_chars=500); loc=st.text_input("Location (optional)"); imgf=st.file_uploader("Group cover image (optional)", type=["jpg","jpeg","png","webp"], key="eco_group_cover_upload"); submit=st.form_submit_button("Create community group", use_container_width=True)
        if submit:
            if len(name.strip())<3 or len(desc.strip())<8: st.error("Add a group name and a short description.")
            else:
                try:
                    path=eco_upload(supabase, imgf, "chatrooms", uid) if imgf else ""
                    gid=create_chatroom(supabase, uid, name, desc, path, loc)
                    if gid: st.success("Your group has been created."); st.session_state.eco_active_chatroom=gid; st.rerun()
                    else: st.success("Group created. Find it under My Groups.")
                except Exception as e: st.error(f"Could not create group: {e}")

# ---------------- Stories ----------------
def create_story(supabase, uid, caption, path, typ):
    now=eco_now(); exp=now+timedelta(hours=24)
    return supabase.table("stories").insert({"user_id":uid,"caption":(caption or "").strip(),"media_url":path,"media_type":typ,"created_at":now.isoformat(),"expires_at":exp.isoformat()}).execute()
def get_active_stories(supabase):
    try: return eco_select(supabase,"stories","*",[("gt","expires_at",eco_iso())],order=("created_at",True),limit=150)
    except Exception: return []
def get_story_views(supabase, sid):
    try: return eco_select(supabase,"story_views","*",[("eq","story_id",sid)],limit=200)
    except Exception: return []
def mark_story_viewed(supabase, sid, viewer):
    try: supabase.table("story_views").upsert({"story_id":sid,"viewer_id":viewer,"viewed_at":eco_iso()}, on_conflict="story_id,viewer_id").execute()
    except Exception: pass

def render_stories_page(supabase, uid):
    st.markdown('<div class="wa-topbar"><b>Stories</b><span>24 hours · WhatsApp 2.0</span></div>', unsafe_allow_html=True)
    if st.button("← Back to Dashboard", key="eco_stories_back_dash"): eco_back_to_dashboard()
    views=["Stories","Create Story"]; cur=st.session_state.get("eco_story_view","Stories")
    sel=st.radio("Story sections", views, horizontal=True, key="eco_story_view_radio", label_visibility="collapsed", index=views.index(cur) if cur in views else 0); st.session_state.eco_story_view=sel
    if sel=="Create Story":
        st.markdown("### Share a story")
        up=st.file_uploader("Choose a photo or short video", type=["jpg","jpeg","png","webp","mp4","mov","webm"], key="eco_story_upload")
        cap=st.text_area("Add a caption (optional)", max_chars=180, key="eco_story_caption")
        if st.button("Publish story", key="eco_story_publish", use_container_width=True):
            if not up: st.warning("Choose a photo or video first.")
            else:
                try:
                    path=eco_upload(supabase, up, "stories", uid, allow_video=True); typ=up.type or "image"
                    create_story(supabase, uid, cap, path, typ); st.success("Your story is live for 24 hours."); st.session_state.eco_story_view="Stories"; st.rerun()
                except Exception as e: st.error(f"Could not publish story: {e}")
        return
    stories=get_active_stories(supabase)
    chat_ids=set()
    for c in get_direct_conversations(supabase, uid): chat_ids.add(str(get_other_user(c, uid)))
    mine=[s for s in stories if str(s.get("user_id"))==str(uid)]
    friends=[s for s in stories if str(s.get("user_id")) in chat_ids and str(s.get("user_id"))!=str(uid)]
    others=[s for s in stories if str(s.get("user_id")) not in chat_ids and str(s.get("user_id"))!=str(uid)]
    st.markdown("### Stories")
    if not stories: st.info("No stories yet. Be the first to share.")
    for label, lst in [("My story", mine), ("Stories from people you chat with", friends), ("All stories", others)]:
        if not lst: continue
        st.markdown(f"#### {label}")
        for i,s in enumerate(lst):
            prof=eco_profile_with_avatar(supabase, s.get("user_id")); name="Your story" if str(s.get("user_id"))==str(uid) else eco_display_name(prof)
            views=get_story_views(supabase, s.get("id"))
            with st.container(border=True):
                c1,c2=st.columns([1,4])
                with c1: st.markdown(eco_avatar_html(prof,48), unsafe_allow_html=True)
                with c2: st.markdown(f"**{name}**"); st.caption(eco_time_label(s.get("created_at"))+f" · 👁 {len(views)} views")
                url=eco_storage_url(supabase, s.get("media_url")); mt=str(s.get("media_type") or "")
                if url and mt.startswith("video"): st.video(url)
                elif url: st.image(url, use_container_width=True)
                if s.get("caption"): st.write(s["caption"])
                if st.button("View story", key=f"eco_story_view_{s.get('id')}_{i}"):
                    mark_story_viewed(supabase, s.get("id"), uid); st.session_state.eco_story_open_id=s.get("id"); st.rerun()
                if str(s.get("user_id"))==str(uid):
                    st.caption("Viewers:")
                    if not views: st.caption("No views yet.")
                    for v in views:
                        vp=eco_profile_with_avatar(supabase, v.get("viewer_id")); st.caption(f"👁 {eco_display_name(vp)} (@{eco_safe_text(vp.get('username'),'member')})")
                    if st.button("Delete story", key=f"eco_story_del_{s.get('id')}_{i}"):
                        try: supabase.table("stories").delete().eq("id", s.get("id")).eq("user_id", uid).execute(); st.success("Story deleted."); st.rerun()
                        except Exception as e: st.error(f"Could not delete: {e}")

def render_discover(supabase, uid):
    st.markdown('<div class="wa-topbar"><b>Discover</b><span>People & Groups</span></div>', unsafe_allow_html=True)
    if st.button("← Back to Dashboard", key="eco_discover_back_dash"): eco_back_to_dashboard()
    q=st.text_input("Search people or groups", key="eco_discover_search_input", placeholder="Search names, usernames, groups or locations…")
    st.markdown("### People")
    people=[p for p in get_member_directory(supabase, q) if str(p.get("user_id"))!=str(uid)]
    if people:
        for i,p in enumerate(people[:30]): render_member_card(supabase, p, uid, f"discover_{i}")
    else: st.caption("No matching people found.")
    st.divider(); st.markdown("### Groups")
    groups=get_chatrooms(supabase, q)
    if groups:
        for i,g in enumerate(groups[:30]): _render_group_card(supabase, g, uid, i, "discover_hub")
    else: st.caption("No matching groups found.")

def render_community_groups_page(supabase, user_id):
    eco_init_state(); eco_inject_styles()
    # BACK TO DASHBOARD - always at top, never stuck
    if st.button("← Back to Dashboard", key="eco_main_back_dashboard_top"): eco_back_to_dashboard()
    private_open=st.session_state.get("eco_chat_view")=="Conversation"; room_open=bool(st.session_state.get("eco_active_chatroom"))
    st.session_state["eco_hide_app_footer"]=bool(private_open or room_open)
    if private_open:
        try: render_direct_conversation(supabase, user_id)
        except Exception as e: st.error("Private conversation could not load."); st.caption(f"Detail: {e}")
        return
    if room_open:
        try: render_chatrooms_page(supabase, user_id)
        except Exception as e: st.error("Chatroom could not load."); st.caption(f"Detail: {e}")
        return
    me=eco_profile_with_avatar(supabase, user_id)
    st.markdown(f'<div class="wa-topbar"><div style="display:flex;align-items:center;gap:10px;">{eco_avatar_html(me,38)}<div><b>Community Hub</b><br><span>Next Gen Impact Hub · {eco_display_name(me)}</span></div></div><span>Connect · Collaborate · Create impact</span></div>', unsafe_allow_html=True)
    options=["💬 Chats","👥 Groups","🟢 Stories","🔎 Discover"]; labels={"💬 Chats":"Chats","👥 Groups":"Groups","🟢 Stories":"Stories","🔎 Discover":"Discover"}
    cur=st.session_state.get("eco_community_section","Chats"); cur_opt=next((k for k,v in labels.items() if v==cur), options[0])
    sel=st.radio("Community navigation", options, horizontal=True, key=MAIN_NAV_KEY, index=options.index(cur_opt), label_visibility="collapsed"); section=labels[sel]; st.session_state.eco_community_section=section
    try:
        if section=="Chats":
            left,right=st.columns([1,1.2])
            with left: render_whatsapp_inbox(supabase, user_id)
            with right: st.markdown('<div class="wa-empty"><div style="font-size:64px;">💬</div><h3>EcoLoop Web</h3><p>Select a chat to start messaging.</p><p style="font-size:12px;color:#8696A0;">Powered by Next Gen Impact Hub (NGIH)</p></div>', unsafe_allow_html=True)
        elif section=="Groups": render_chatrooms_page(supabase, user_id)
        elif section=="Stories": render_stories_page(supabase, user_id)
        else: render_discover(supabase, user_id)
    except Exception as e: st.error("Community Hub section could not load."); st.caption(f"Detail: {e}")
    st.divider(); st.caption("Powered by Next Gen Impact Hub (NGIH)")

# ============================================================
# ECOLOOP NODE — COMMUNITY HUB
# WHATSAPP 2.0 — VOICE MESSAGE FIX
# Add this entire section at the VERY BOTTOM of the file.
# Overrides the older composer and message renderer.
# ============================================================

def render_whatsapp_composer(supabase, uid, conversation_id=None, group_id=None):
    import hashlib

    target = str(conversation_id or group_id or uid)
    counter_key = f"eco_voice_widget_counter_{target}"

    if counter_key not in st.session_state:
        st.session_state[counter_key] = 0

    # A new widget key after sending clears the previous recording.
    voice_key = f"voice_{target}_{st.session_state[counter_key]}"

    st.markdown('<div class="wa-composer">', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns([1, 6, 1, 1])

    with c1:
        attach = st.file_uploader(
            "📎",
            type=["jpg", "jpeg", "png", "webp", "mp4", "mov", "pdf", "docx"],
            label_visibility="collapsed",
            key=f"attach_{target}"
        )

    with c2:
        text = st.text_input(
            "Type a message...",
            label_visibility="collapsed",
            key=f"txt_{target}"
        )

    with c3:
        voice = st.audio_input(
            "🎤",
            label_visibility="collapsed",
            key=voice_key
        )

    with c4:
        send = st.button(
            "➤",
            key=f"send_{target}",
            help="Send message",
            use_container_width=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

    # Nothing is sent until the user taps Send.
    if not send:
        return

    try:
        sent_any = False

        # ---------------- VOICE MESSAGE ----------------
        if voice is not None:
            audio_bytes = voice.getvalue()

            if not audio_bytes:
                st.warning("The recording appears to be empty.")
                return

            # Prevent the same recording being submitted twice.
            signature = hashlib.sha256(audio_bytes).hexdigest()
            sent_key = f"eco_voice_last_sent_{target}"

            if st.session_state.get(sent_key) != signature:

                path = f"voice/{uid}/{uuid.uuid4().hex}.wav"

                supabase.storage.from_(BUCKET).upload(
                    path,
                    audio_bytes,
                    {
                        "content-type": "audio/wav",
                        "upsert": "false"
                    }
                )

                if conversation_id:
                    send_direct_message(
                        supabase,
                        conversation_id,
                        uid,
                        "🎤 Voice note",
                        path,
                        "voice.wav",
                        "audio"
                    )

                elif group_id:
                    supabase.table("group_messages").insert({
                        "group_id": group_id,
                        "sender_id": uid,
                        "message_text": "🎤 Voice note",
                        "attachments": [{
                            "path": path,
                            "name": "voice.wav",
                            "type": "audio"
                        }]
                    }).execute()

                st.session_state[sent_key] = signature
                sent_any = True

                # Change the audio widget key so its old recording clears.
                st.session_state[counter_key] += 1

        # ---------------- FILE ATTACHMENT ----------------
        apath = ""
        aname = ""
        atyp = ""

        if attach is not None:
            apath = eco_upload(
                supabase,
                attach,
                "chat",
                uid,
                allow_video=True,
                allow_doc=True
            )
            aname = attach.name
            atyp = attach.type or ""

        # ---------------- TEXT MESSAGE ----------------
        if text.strip() or apath:
            message_text = text.strip() or aname or "Attachment"

            if conversation_id:
                send_direct_message(
                    supabase,
                    conversation_id,
                    uid,
                    message_text,
                    apath,
                    aname,
                    atyp
                )

            elif group_id:
                supabase.table("group_messages").insert({
                    "group_id": group_id,
                    "sender_id": uid,
                    "message_text": message_text,
                    "attachments": [{
                        "path": apath,
                        "name": aname,
                        "type": atyp
                    }] if apath else []
                }).execute()

            sent_any = True

        if sent_any:
            st.rerun()

    except Exception as e:
        st.error(f"Message could not be sent: {e}")


# ============================================================
# MESSAGE DISPLAY — REAL AUDIO PLAYBACK
# ============================================================

def eco_render_bubbles_html(supabase, messages, uid, is_group=False):

    if not messages:
        st.markdown(
            '<div class="wa-empty">'
            '<div style="font-size:48px;">💬</div>'
            '<b>Say hi</b>'
            '<p>This is the beginning of your conversation.</p>'
            '</div>',
            unsafe_allow_html=True
        )
        return

    for m in messages:

        if m.get("deleted_at"):
            continue

        sent = str(m.get("sender_id")) == str(uid)

        sender = (
            eco_profile_with_avatar(supabase, m.get("sender_id"))
            if is_group else {}
        )

        name = "You" if sent else eco_display_name(sender)
        body = str(m.get("message_text") or "")

        # Collect attachments.
        atts = []

        if m.get("attachment_path"):
            atts = [{
                "path": m.get("attachment_path"),
                "type": m.get("attachment_type") or "",
                "name": m.get("attachment_name") or "Attachment"
            }]

        if m.get("attachments"):
            a = m.get("attachments")
            atts = a if isinstance(a, list) else [a]

        # Display media.
        for it in atts:

            if not isinstance(it, dict):
                continue

            url = eco_storage_url(
                supabase,
                it.get("path") or it.get("url")
            )

            typ = str(it.get("type") or "").lower()

            if not url:
                continue

            if typ.startswith("image"):
                st.markdown(
                    f'<div style="text-align:{"right" if sent else "left"};">'
                    f'<img src="{url}" '
                    f'style="max-width:80%;border-radius:10px;margin:5px 0;" />'
                    f'</div>',
                    unsafe_allow_html=True
                )

            elif typ.startswith("video"):
                st.markdown(
                    f'<div>🎬 <a href="{url}" target="_blank">'
                    f'Watch video</a></div>',
                    unsafe_allow_html=True
                )

            elif typ.startswith("audio"):
                st.caption("🎤 Voice note")
                st.audio(url, format="audio/wav")

            else:
                filename = it.get("name") or "Open attachment"

                st.markdown(
                    f'📎 <a href="{url}" target="_blank">'
                    f'{filename}</a>',
                    unsafe_allow_html=True
                )

        # Display message text.
        if body:
            st.markdown(
                eco_bubble_html(
                    body,
                    eco_time_short(m.get("created_at")),
                    sent,
                    "" if sent else name,
                    bool(m.get("edited_at"))
                ),
                unsafe_allow_html=True
            )
