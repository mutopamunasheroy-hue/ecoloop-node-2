# ============================================================
# ECOLOOP NODE COMMUNITY — ENTIRE FILE — FINAL WHATSAPP STYLE
# Chats + Groups + Stories ONE PAGE + Profiles + Discover
# Composer = [ Message ........ 📎 ] ➤  — 📎 opens popup, no big Upload boxes
# Clean chat: NO dashboard inside chat, Members hidden until you tap 👥
# Fixes: invite_code missing, membership P0001, uploads everywhere,
# stories picture, Discover username, Profile view/edit, Add as Member
# ============================================================
import mimetypes, os, re, uuid, secrets
from datetime import datetime, timedelta, timezone
import streamlit as st

BUCKET = "community-media"
MAX_IMAGE_MB = 8
MAX_VIDEO_MB = 35
MAIN_NAV_KEY = "eco_node_nav_final"
REACTION_EMOJIS = ["❤️","😂","🔥","👍","😮","😢"]
HEADER = "EcoLoop Node Community"

def eco_now(): return datetime.now(timezone.utc)
def eco_iso(v=None):
    v = v or eco_now()
    return v if isinstance(v, str) else v.isoformat()
def eco_safe_text(v, d=""):
    t = str(v or "").strip()
    return t if t else d
def eco_init_state():
    defaults = {"eco_community_section":"Chats","eco_chat_view":"Inbox","eco_active_conversation":None,"eco_active_chatroom":None,"eco_group_view":"Discover","eco_story_view":"Stories","eco_profile_view_user":None,"eco_group_members_open":None,"eco_composer_gen":0,"eco_story_open_id":None,"eco_join_code":"","eco_attach_open":False}
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
    if ext not in allowed: raise ValueError(f"File type {ext} not allowed. Use image / video / pdf / docx.")
    lim=MAX_VIDEO_MB if ext in {".mp4",".mov",".webm"} else MAX_IMAGE_MB
    size = getattr(up,"size",0) or len(up.getvalue() or b"")
    if size>lim*1024*1024: raise ValueError(f"Too large. Max {lim} MB. Your file is {size//1024//1024} MB.")
    path=f"{folder}/{uid}/{uuid.uuid4().hex}{ext}"
    try:
        supabase.storage.from_(BUCKET).upload(path, up.getvalue(), {"content-type": up.type or mimetypes.guess_type(name)[0] or "application/octet-stream","upsert":"false"})
    except Exception as e:
        msg=str(e)
        if "Bucket not found" in msg or "not found" in msg.lower(): raise ValueError("Storage bucket 'community-media' not found. Create it in Supabase Storage + make it Public.")
        if "policy" in msg.lower() or "403" in msg or "Unauthorized" in msg: raise ValueError("Storage policy blocked upload. In Supabase Storage -> community-media -> Policies, allow INSERT + SELECT for everyone.")
        raise ValueError(f"Upload failed: {msg[:200]}")
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

# ---------- REACTIONS ----------
def eco_get_reactions(supabase, message_ids):
    out={}
    if not message_ids: return out
    sess=st.session_state.get("eco_reactions_local",{})
    for mid in message_ids:
        if mid in sess: out[mid]=dict(sess[mid])
    try:
        rows=eco_result_data(supabase.table("message_reactions").select("*").in_("message_id", list(message_ids)).execute())
        for r in rows:
            mid=str(r.get("message_id")); em=r.get("emoji")
            if mid not in out: out[mid]={}
            out[mid][em]=out[mid].get(em,0)+1
    except Exception: pass
    return out
def eco_get_my_reactions(supabase, message_ids, uid):
    mine={}
    try:
        rows=eco_result_data(supabase.table("message_reactions").select("*").in_("message_id", list(message_ids)).eq("user_id", str(uid)).execute())
        for r in rows: mine[str(r.get("message_id"))]=r.get("emoji")
    except Exception:
        sess=st.session_state.get("eco_my_reactions_local",{})
        for mid in message_ids:
            if mid in sess: mine[mid]=sess[mid]
    return mine
def eco_toggle_reaction(supabase, message_id, uid, emoji, is_group=False):
    mid=str(message_id)
    try:
        existing=eco_result_data(supabase.table("message_reactions").select("*").eq("message_id", mid).eq("user_id", str(uid)).execute())
        if existing and existing[0].get("emoji")==emoji:
            supabase.table("message_reactions").delete().eq("message_id", mid).eq("user_id", str(uid)).execute(); return
        if existing:
            supabase.table("message_reactions").update({"emoji": emoji}).eq("message_id", mid).eq("user_id", str(uid)).execute(); return
        supabase.table("message_reactions").insert({"message_id": mid, "user_id": str(uid), "emoji": emoji, "is_group": bool(is_group)}).execute(); return
    except Exception: pass
    if "eco_my_reactions_local" not in st.session_state: st.session_state["eco_my_reactions_local"]={}
    if "eco_reactions_local" not in st.session_state: st.session_state["eco_reactions_local"]={}
    my=st.session_state["eco_my_reactions_local"]; allr=st.session_state["eco_reactions_local"]
    if my.get(mid)==emoji:
        if mid in allr and emoji in allr[mid]:
            allr[mid][emoji]-=1
            if allr[mid][emoji]<=0: del allr[mid][emoji]
        del my[mid]
    else:
        old=my.get(mid)
        if old and mid in allr and old in allr[mid]:
            allr[mid][old]-=1
            if allr[mid][old]<=0: del allr[mid][old]
        my[mid]=emoji
        if mid not in allr: allr[mid]={}
        allr[mid][emoji]=allr[mid].get(emoji,0)+1

# ---------- MEMBERSHIP — FIX P0001: delete + re-insert, never UPDATE role ----------
def eco_set_membership(supabase, gid, uid, role="member", status="approved"):
    # Delete first, then insert. UPDATE triggers "Membership identity cannot be changed" in many setups.
    try: supabase.table("group_memberships").delete().eq("group_id", gid).eq("user_id", uid).execute()
    except Exception: pass
    return supabase.table("group_memberships").insert({"group_id": gid, "user_id": uid, "membership_role": role, "status": status}).execute()
def eco_add_member_as(supabase, gid, uid, role):
    return eco_set_membership(supabase, gid, uid, role=role, status="approved")

def eco_inject_styles():
    st.markdown("""
    <style>
    .block-container{padding:0!important;max-width:100%!important}
    header[data-testid="stHeader"]{display:none} [data-testid="stSidebar"]{display:none}
    .wa-topbar{background:#075E54;color:white;padding:12px 16px;display:flex;align-items:center;justify-content:space-between}
    .wa-topbar b{font-size:19px} .wa-topbar span{font-size:12px;opacity:.9}
    .wa-chat-bg{background-color:#ECE5DD!important;background-image:radial-gradient(#D5D0C8 1px, transparent 1px)!important;background-size:20px 20px!important;min-height:68vh!important;padding:14px 10px 16px 10px!important;display:block!important;width:100%!important}
    .wa-bubble-me{background:#DCF8C6;border-radius:10px 10px 0 10px;padding:8px 10px;margin:6px 0 6px auto;max-width:82%;width:fit-content;box-shadow:0 1px 1px rgba(0,0,0,.12);font-size:15px;line-height:1.45}
    .wa-bubble-other{background:#FFFFFF;border-radius:10px 10px 10px 0;padding:8px 10px;margin:6px auto 6px 0;max-width:82%;width:fit-content;box-shadow:0 1px 1px rgba(0,0,0,.12);font-size:15px;line-height:1.45}
    .wa-meta{font-size:11px;color:#667781;text-align:right;margin-top:3px}
    .wa-sender{font-size:12px;font-weight:700;color:#128C7E;margin-bottom:2px}
    .wa-avatar{width:44px;height:44px;border-radius:50%;background:#DFE5E7;display:flex;align-items:center;justify-content:center;font-weight:700;color:#54656F;font-size:16px;flex-shrink:0;overflow:hidden}
    .wa-unread{background:#25D366;color:white;font-size:11px;font-weight:700;min-width:20px;height:20px;border-radius:20px;display:flex;align-items:center;justify-content:center;padding:0 6px}
    .wa-empty{height:60vh;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#667781;text-align:center;padding:30px}
    .wa-pill{background:#FFFFFF;border-radius:16px;padding:10px 12px;margin:8px 0;border:1px solid #E9EDEF}
    .wa-react-count{background:#FFFFFF;border:1px solid #E9EDEF;border-radius:16px;padding:2px 8px;font-size:12px;display:inline-block;margin:2px 2px 6px 0;box-shadow:0 1px 1px rgba(0,0,0,.08)}
    .wa-composer{background:#F0F2F5!important;padding:8px 6px 10px 6px!important;position:sticky;bottom:0;z-index:99;width:100%!important}
    .wa-composer input{background:#FFFFFF!important;color:#111B21!important;border:none!important;height:48px!important;font-size:15px!important;padding:0 8px!important;box-shadow:none!important;width:100%!important}
    .wa-composer input::placeholder{color:#8696A0!important}
    [data-testid="stPopover"] button{border:none!important;background:transparent!important;font-size:20px!important}
    </style>""", unsafe_allow_html=True)
def eco_avatar_html(profile, size=44):
    name=eco_display_name(profile)
    url=(profile.get("_avatar_resolved") or profile.get("avatar_url")) if profile else None
    if url and str(url).startswith("http"): return f'<img src="{url}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;" />'
    return f'<div class="wa-avatar" style="width:{size}px;height:{size}px;">{eco_initials(name)}</div>'
def eco_bubble_html(text, time_label, is_me, sender_name="", edited=False):
    safe=str(text or "").replace("<","&lt;").replace(">","&gt;").replace("\n","<br>")
    tick=" ✓✓" if is_me else ""; edit=" · edited" if edited else ""
    sender=f'<div class="wa-sender">{sender_name}</div>' if (not is_me and sender_name) else ""
    cls="wa-bubble-me" if is_me else "wa-bubble-other"
    return f'<div class="{cls}">{sender}<div>{safe}</div><div class="wa-meta">{time_label}{edit}{tick}</div></div>'
def eco_render_bubbles_html(supabase, messages, uid, is_group=False):
    if not messages:
        st.markdown('<div class="wa-chat-bg"><div class="wa-empty"><div style="font-size:48px;">💬</div><b>Say hi</b><p>This is the beginning of your conversation.</p></div></div>', unsafe_allow_html=True); return
    mids=[str(m.get("id")) for m in messages if m.get("id")]
    all_reactions=eco_get_reactions(supabase, mids); my_reactions=eco_get_my_reactions(supabase, mids, uid)
    st.markdown('<div class="wa-chat-bg">', unsafe_allow_html=True)
    seen=set()
    for idx, m in enumerate(messages):
        if m.get("deleted_at"): continue
        mid=str(m.get("id") or "")+str(m.get("created_at") or "")
        if mid in seen: continue
        seen.add(mid); sent=str(m.get("sender_id"))==str(uid)
        sender=eco_profile_with_avatar(supabase, m.get("sender_id")) if is_group else {}; name="You" if sent else eco_display_name(sender); body=str(m.get("message_text") or "")
        atts=[]
        if m.get("attachment_path"): atts=[{"path":m.get("attachment_path"),"type":m.get("attachment_type") or "","name":m.get("attachment_name") or "Attachment"}]
        if m.get("attachments"):
            a=m.get("attachments"); atts=a if isinstance(a,list) else [a]
        uniq=[]; seen_att=set()
        for it in atts:
            if isinstance(it,dict):
                k=str(it.get("path") or it.get("url"))+str(it.get("name"))
                if k not in seen_att: seen_att.add(k); uniq.append(it)
        attach_html=""
        for it in uniq:
            url=eco_storage_url(supabase, it.get("path") or it.get("url")); typ=str(it.get("type") or "").lower()
            if url and typ.startswith("image"): attach_html+=f'<img src="{url}" style="max-width:100%;border-radius:10px;margin:4px 0;" />'
            elif url and typ.startswith("video"): attach_html+=f'<div>🎬 <a href="{url}" target="_blank">Watch video</a></div>'
            elif url: attach_html+=f'<div>📎 <a href="{url}" target="_blank">{it.get("name") or "Open attachment"}</a></div>'
            elif str(it.get("path") or "").startswith("http"): attach_html+=f'<img src="{it.get("path")}" style="max-width:100%;border-radius:10px;margin:4px 0;" />'
        if attach_html or body:
            if attach_html: st.markdown(f'<div class="{"wa-bubble-me" if sent else "wa-bubble-other"}">{("<div class=\"wa-sender\">"+name+"</div>") if (not sent and name) else ""}{attach_html}{("<div>"+body.replace("<","&lt;").replace(">","&gt;").replace(chr(10),"<br>")+"</div>") if body else ""}<div class="wa-meta">{eco_time_short(m.get("created_at"))}{" ✓✓" if sent else ""}</div></div>', unsafe_allow_html=True)
            else: st.markdown(eco_bubble_html(body, eco_time_short(m.get("created_at")), sent, "" if sent else name, bool(m.get("edited_at"))), unsafe_allow_html=True)
        real_id=str(m.get("id") or "")
        if real_id:
            counts=all_reactions.get(real_id,{})
            if counts:
                pills="".join([f'<span class="wa-react-count">{em} {cnt}</span>' for em,cnt in counts.items()]); align="right" if sent else "left"; st.markdown(f'<div style="text-align:{align};margin-top:-2px;">{pills}</div>', unsafe_allow_html=True)
            rcols=st.columns(6, gap="small"); my_em=my_reactions.get(real_id,"")
            for ri, em in enumerate(REACTION_EMOJIS):
                with rcols[ri]:
                    label=f"{em} ✓" if my_em==em else em
                    if st.button(label, key=f"eco_react_{'g' if is_group else 'd'}_{real_id}_{ri}", use_container_width=True): eco_toggle_reaction(supabase, real_id, uid, em, is_group=is_group); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
def eco_back_to_dashboard():
    st.session_state["eco_active_conversation"]=None; st.session_state["eco_active_chatroom"]=None; st.session_state["eco_chat_view"]="Inbox"; st.session_state["eco_community_section"]="Chats"; st.session_state["eco_return_to_dashboard"]=True; st.session_state["current_page"]="Dashboard"; st.session_state["page"]="Dashboard"; st.session_state["eco_page"]="Dashboard"; st.rerun()
def save_member_profile(supabase, uid, values):
    payload={"user_id":uid}
    for k in ("display_name","username","bio","location","interests","country_of_origin","instagram_handle","facebook_handle","tiktok_handle","linkedin_handle","avatar_url"):
        if k in values: payload[k]=values[k]
    return supabase.table("member_profiles").upsert(payload, on_conflict="user_id").execute()

# ---------- PROFILE — FIXED: view + edit on one page, uploader NOT in form ----------
def render_profile_editor(supabase, uid):
    profile=eco_profile_with_avatar(supabase, uid)
    st.markdown(f'<div class="wa-topbar"><b>My Profile</b><span>{HEADER}</span></div>', unsafe_allow_html=True)
    if st.button("← Back to Dashboard", key="eco_profile_back_dash"): eco_back_to_dashboard()
    if st.button("‹ Back to chats"): st.session_state.eco_chat_view="Inbox"; st.rerun()
    st.markdown(eco_avatar_html(profile, 96), unsafe_allow_html=True)
    st.markdown(f'<div class="wa-pill"><b>{eco_display_name(profile)}</b><br>@{eco_safe_text(profile.get("username"),"set-username")}<br><span style="color:#667781;font-size:13px;">Share this username — anyone can search it and message you.</span></div>', unsafe_allow_html=True)
    if profile.get("bio"): st.write(profile["bio"])
    if profile.get("location"): st.caption("📍 "+str(profile["location"]))
    if profile.get("interests"): st.caption("Interests: "+str(profile["interests"]))
    # Avatar uploader OUTSIDE form — this is why it stuck before
    st.markdown("### 📷 Change profile picture")
    avatar_file=st.file_uploader("Tap to pick a photo", type=["jpg","jpeg","png","webp"], key="eco_profile_avatar_upload_v2")
    if avatar_file:
        st.success(f"Picked: {avatar_file.name}")
        if st.button("Upload profile picture", key="eco_profile_avatar_save_v2", use_container_width=True):
            try:
                with st.spinner("Uploading..."): path=eco_upload(supabase, avatar_file, "profiles", uid)
                save_member_profile(supabase, uid, {"avatar_url": path}); st.success("Profile picture updated."); st.rerun()
            except Exception as e: st.error(str(e))
    st.markdown("### ✏️ Edit profile")
    with st.form("eco_profile_edit_form_v2", clear_on_submit=False):
        display_name=st.text_input("Display name", value=profile.get("display_name","")); username=st.text_input("Username — people search this", value=profile.get("username","")); bio=st.text_area("About me", value=profile.get("bio",""), max_chars=240); location=st.text_input("Location", value=profile.get("location","")); country=st.text_input("Country of origin", value=profile.get("country_of_origin","")); interests=st.text_input("Interests (comma separated)", value=profile.get("interests","")); instagram=st.text_input("Instagram", value=profile.get("instagram_handle","")); facebook=st.text_input("Facebook", value=profile.get("facebook_handle","")); tiktok=st.text_input("TikTok", value=profile.get("tiktok_handle","")); linkedin=st.text_input("LinkedIn", value=profile.get("linkedin_handle","")); submitted=st.form_submit_button("Save profile", use_container_width=True)
    if submitted:
        username=re.sub(r"[^a-zA-Z0-9_.]","",username).lower()
        if len(username)<3: st.error("Choose a username with at least 3 letters or numbers.")
        else:
            try: save_member_profile(supabase, uid, {"display_name":display_name.strip(),"username":username,"bio":bio.strip(),"location":location.strip(),"country_of_origin":country.strip(),"interests":interests.strip(),"instagram_handle":instagram.strip(),"facebook_handle":facebook.strip(),"tiktok_handle":tiktok.strip(),"linkedin_handle":linkedin.strip()}); st.success("Profile saved."); st.rerun()
            except Exception as e: st.error(f"Could not save. Username may be taken. Details: {e}")
def get_member_directory(supabase, search=""):
    q=(search or "").strip().lower().lstrip("@").strip()
    try:
        if not q: return eco_select(supabase,"member_profiles","*",order=("display_name",False),limit=150)
        found={}
        # FIX Discover: try ilike on username, display_name, location + exact
        for col in ("username","display_name","location"):
            try:
                rows=eco_result_data(supabase.table("member_profiles").select("*").ilike(col,f"%{q}%").limit(100).execute())
                for r in rows:
                    uid=str(r.get("user_id") or r.get("id") or "")
                    if uid: found[uid]=r
            except Exception: continue
        # Fallback: if ilike returns nothing (RLS / case), scan all and filter in Python
        if not found:
            allp=eco_select(supabase,"member_profiles","*",limit=200)
            for r in allp:
                hay=(str(r.get("username",""))+" "+str(r.get("display_name",""))+" "+str(r.get("location",""))).lower()
                if q in hay: found[str(r.get("user_id"))]=r
        return sorted(found.values(), key=lambda r: str(r.get("username") or "").lower())
    except Exception: return []
def render_member_card(supabase, profile, current_uid, suffix):
    profile=dict(profile); profile["_avatar_resolved"]=eco_storage_url(supabase, profile.get("avatar_url")); uid=profile.get("user_id"); name=eco_display_name(profile); username=eco_safe_text(profile.get("username"),"member")
    with st.container(border=True):
        c1,c2=st.columns([1,4])
        with c1: st.markdown(eco_avatar_html(profile), unsafe_allow_html=True)
        with c2: st.markdown(f"**{name}**"); st.caption(f"@{username}")
        with c2:
            if profile.get("bio"): st.write(str(profile["bio"])[:150])
            if profile.get("location"): st.caption(f"📍 {profile['location']}")
        if uid and uid!=current_uid:
            a,b=st.columns(2)
            with a:
                if st.button("View profile", key=f"eco_person_profile_{suffix}_{uid}", use_container_width=True): st.session_state.eco_profile_view_user=uid; st.session_state.eco_chat_view="Profile"; st.rerun()
            with b:
                if st.button("💬 Message", key=f"eco_person_message_{suffix}_{uid}", use_container_width=True):
                    try: conv=get_or_create_direct_conversation(supabase, current_uid, uid); st.session_state.eco_active_conversation=conv; st.session_state.eco_chat_view="Conversation"; st.rerun()
                    except Exception as e: st.error(f"Could not open chat: {e}")
def render_public_profile(supabase, uid, current_uid):
    profile=eco_profile_with_avatar(supabase, uid)
    if not profile: st.warning("This profile is not available."); 
    if not profile:
        if st.button("‹ Back"): st.session_state.eco_chat_view="Discover People"; st.rerun()
        return
    if st.button("← Back to Dashboard", key=f"eco_pub_back_dash_{uid}"): eco_back_to_dashboard()
    if st.button("‹ Back"): st.session_state.eco_chat_view="Discover People"; st.rerun()
    st.markdown(eco_avatar_html(profile, 110), unsafe_allow_html=True); st.subheader(eco_display_name(profile)); st.caption("@"+eco_safe_text(profile.get("username"),"member"))
    if profile.get("location"): st.caption("📍 "+str(profile["location"]))
    if profile.get("country_of_origin"): st.caption("🌍 From: "+str(profile["country_of_origin"]))
    if profile.get("bio"): st.write(profile["bio"])
    if profile.get("interests"): st.caption("Interests: "+str(profile["interests"]))
    socials=[("Instagram","instagram_handle"),("Facebook","facebook_handle"),("TikTok","tiktok_handle"),("LinkedIn","linkedin_handle")]; present=[f"**{l}:** @{profile[k].lstrip('@')}" for l,k in socials if profile.get(k)]
    if present: st.markdown(" · ".join(present))
    else: st.caption("No social links yet.")
    if uid!=current_uid and st.button("💬 Message", key=f"eco_public_profile_message_{uid}", use_container_width=True):
        try: conv=get_or_create_direct_conversation(supabase, current_uid, uid); st.session_state.eco_active_conversation=conv; st.session_state.eco_chat_view="Conversation"; st.rerun()
        except Exception as e: st.error(f"Could not start conversation: {e}")
def get_or_create_direct_conversation(supabase, a, b):
    first,second=sorted([str(a),str(b)]); rows=eco_select(supabase,"direct_conversations","*",[("eq","user_one_id",first),("eq","user_two_id",second)],limit=1)
    if rows: return rows[0]["id"]
    res=supabase.table("direct_conversations").insert({"user_one_id":first,"user_two_id":second}).execute(); rows=eco_result_data(res)
    if rows: return rows[0]["id"]
    rows=eco_select(supabase,"direct_conversations","*",[("eq","user_one_id",first),("eq","user_two_id",second)],limit=1)
    if not rows: raise RuntimeError("Conversation could not be created.")
    return rows[0]["id"]
def get_direct_conversations(supabase, uid):
    try: a=eco_select(supabase,"direct_conversations","*",[("eq","user_one_id",uid)],order=("created_at",True),limit=150); b=eco_select(supabase,"direct_conversations","*",[("eq","user_two_id",uid)],order=("created_at",True),limit=150); return list({str(r["id"]):r for r in a+b if r.get("id")}.values())
    except Exception: return []
def get_direct_messages(supabase, cid, limit=100):
    try: return eco_select(supabase,"direct_messages","*",[("eq","conversation_id",cid),("is_","deleted_at","null")],order=("created_at",False),limit=limit)
    except Exception: return []
def get_latest_direct_message(supabase, cid):
    try: rows=eco_select(supabase,"direct_messages","*",[("eq","conversation_id",cid),("is_","deleted_at","null")],order=("created_at",True),limit=1); return rows[0] if rows else {}
    except Exception: return {}
def send_direct_message(supabase, cid, sender, text, path="", name="", typ=""):
    payload={"conversation_id":cid,"sender_id":sender,"message_text":(text or "").strip(),"attachment_path":path or None,"attachment_name":name or None,"attachment_type":typ or None}
    if not payload["message_text"] and not path: return False
    supabase.table("direct_messages").insert(payload).execute(); return True
def mark_direct_read(supabase, cid, uid):
    try: supabase.table("direct_conversation_reads").upsert({"conversation_id":cid,"user_id":uid,"last_read_at":eco_iso()}, on_conflict="conversation_id,user_id").execute()
    except Exception: pass
def get_read_ts(supabase, cid, uid):
    try: rows=eco_select(supabase,"direct_conversation_reads","last_read_at",[("eq","conversation_id",cid),("eq","user_id",uid)],limit=1); return rows[0].get("last_read_at") if rows else None
    except Exception: return None
def get_other_user(conv, cur): return conv.get("user_two_id") if str(conv.get("user_one_id"))==str(cur) else conv.get("user_one_id")
def eco_send_message_with_uploads(supabase, uid, conversation_id, group_id, text, uploads):
    if conversation_id:
        if uploads:
            for idx,(apath,aname,atyp) in enumerate(uploads): send_direct_message(supabase, conversation_id, uid, text.strip() if idx==0 and text.strip() else aname, apath, aname, atyp)
        elif text.strip(): send_direct_message(supabase, conversation_id, uid, text.strip(), "", "", "")
    if group_id:
        if text.strip() or uploads:
            atts=[{"path":p,"name":n,"type":t} for p,n,t in uploads]
            msg_text=text.strip() if text.strip() else (uploads[0][1] if uploads else "Attachment")
            supabase.table("group_messages").insert({"group_id":group_id,"sender_id":uid,"message_text":msg_text,"attachments":atts}).execute()

# ---------- COMPOSER — WHATSAPP STYLE: [ Message ... 📎 ] ➤ ----------
def render_whatsapp_composer(supabase, uid, conversation_id=None, group_id=None):
    eco_init_state()
    gen=int(st.session_state.get("eco_composer_gen",0))
    base=f"{conversation_id or group_id}_{gen}"
    txt_key=f"txt_{base}"
    if txt_key not in st.session_state: st.session_state[txt_key]=""
    # Attach popup — 📎 on far right INSIDE message box area
    # We render the composer as 3 columns: [Message][📎][➤] — 📎 is a popover, not a big box
    st.markdown('<div class="wa-composer">', unsafe_allow_html=True)
    c_msg, c_attach, c_send = st.columns([7, 1, 1], gap="small")
    with c_msg:
        text = st.text_input("Message", label_visibility="collapsed", placeholder="Message", key=txt_key)
    with c_attach:
        # Popover = WhatsApp attach menu. File uploaders live INSIDE popover, full width, so they work.
        with st.popover("📎", use_container_width=True):
            st.markdown("**Attach**")
            photo_up = st.file_uploader("📷 Photo / Video", type=["jpg","jpeg","png","webp","mp4","mov"], key=f"photo_pop_{base}")
            if photo_up is not None:
                st.success(f"Picked: {photo_up.name}")
                if st.button("➤ Send Photo / Video", key=f"send_photo_pop_{base}", use_container_width=True):
                    try:
                        with st.spinner("Uploading photo..."):
                            p=eco_upload(supabase, photo_up, "chat", uid, allow_video=True, allow_doc=False)
                        eco_send_message_with_uploads(supabase, uid, conversation_id, group_id, st.session_state.get(txt_key,""), [(p, photo_up.name, photo_up.type or "")])
                        st.success("Photo sent ✅"); st.session_state["eco_composer_gen"]=gen+1; st.rerun()
                    except Exception as e: st.error(str(e))
            file_up = st.file_uploader("📄 File (PDF / DOCX)", type=["pdf","docx"], key=f"file_pop_{base}")
            if file_up is not None:
                st.success(f"Picked: {file_up.name}")
                if st.button("➤ Send File", key=f"send_file_pop_{base}", use_container_width=True):
                    try:
                        with st.spinner("Uploading file..."):
                            p=eco_upload(supabase, file_up, "chat", uid, allow_video=False, allow_doc=True)
                        eco_send_message_with_uploads(supabase, uid, conversation_id, group_id, st.session_state.get(txt_key,""), [(p, file_up.name, file_up.type or "")])
                        st.success("File sent ✅"); st.session_state["eco_composer_gen"]=gen+1; st.rerun()
                    except Exception as e: st.error(str(e))
    with c_send:
        send = st.button("➤", key=f"send_txt_{base}", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    if not send: return
    if not (text or "").strip(): return
    try:
        eco_send_message_with_uploads(supabase, uid, conversation_id, group_id, text.strip(), [])
        st.session_state["eco_composer_gen"]=gen+1; st.rerun()
    except Exception as e: st.error(f"Message could not be sent: {e}")

def render_direct_conversation(supabase, uid):
    cid=st.session_state.eco_active_conversation
    if not cid: st.session_state.eco_chat_view="Inbox"; st.rerun(); return
    convs=get_direct_conversations(supabase, uid); conv=next((c for c in convs if str(c.get("id"))==str(cid)), None)
    if not conv:
        st.error("This conversation is no longer available.")
        if st.button("‹ Back to chats"): st.session_state.eco_active_conversation=None; st.session_state.eco_chat_view="Inbox"; st.rerun()
        return
    other_id=get_other_user(conv, uid); other=eco_profile_with_avatar(supabase, other_id); name=eco_display_name(other)
    # CLEAN CHAT HEADER — no dashboard inside chat
    h1,h2,h3=st.columns([0.6,1,5])
    with h1:
        if st.button("‹", key="eco_dm_back"): st.session_state.eco_active_conversation=None; st.session_state.eco_chat_view="Inbox"; st.rerun()
    with h2: st.markdown(eco_avatar_html(other,40), unsafe_allow_html=True)
    with h3: st.markdown(f"**{name}**"); st.caption("@"+eco_safe_text(other.get("username"),"member")+" · Online")
    mark_direct_read(supabase, cid, uid); msgs=get_direct_messages(supabase, cid); eco_render_bubbles_html(supabase, msgs, uid, is_group=False); render_whatsapp_composer(supabase, uid, conversation_id=cid)
def render_whatsapp_inbox(supabase, uid):
    search=st.text_input("Search or start new chat", key="eco_sidebar_search_input", placeholder="Search chats…", label_visibility="collapsed")
    c1,c2=st.columns(2)
    with c1:
        if st.button("＋ New chat", key="eco_new_chat_button", use_container_width=True): st.session_state.eco_chat_view="Discover People"; st.rerun()
    with c2:
        if st.button("My profile", key="eco_my_profile_button", use_container_width=True): st.session_state.eco_chat_view="My Profile"; st.rerun()
    st.markdown('<div class="wa-pill"><b>🔗 Join group via invite code</b></div>', unsafe_allow_html=True)
    j1,j2=st.columns([3,1])
    with j1: code=st.text_input("Invite code", placeholder="Paste invite code e.g. ECO-AB12CD", key="eco_join_code_input", label_visibility="collapsed")
    with j2:
        if st.button("Join", key="eco_join_via_code_btn", use_container_width=True):
            if code.strip(): join_via_code(supabase, uid, code.strip())
            else: st.warning("Paste an invite code first.")
    st.divider(); convs=get_direct_conversations(supabase, uid); enriched=[]
    for conv in convs:
        oid=get_other_user(conv, uid); prof=eco_profile_with_avatar(supabase, oid); latest=get_latest_direct_message(supabase, conv.get("id")); read_at=get_read_ts(supabase, conv.get("id"), uid); unread=0
        if read_at and latest and str(latest.get("sender_id"))!=str(uid):
            rd=_parse_dt(read_at); md=_parse_dt(latest.get("created_at"))
            if rd and md and md>rd: unread=1
        q=(search or "").strip().lower()
        if q and q not in eco_display_name(prof).lower() and q not in str(prof.get("username","")).lower(): continue
        enriched.append((latest.get("created_at") or conv.get("created_at") or "", conv, prof, latest, unread))
    enriched.sort(key=lambda x: x[0] or "", reverse=True)
    if not enriched: st.info("No chats yet. Tap + New chat, search a @username, and start talking."); return
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
                if st.button("Open", key=f"eco_inbox_open_{conv.get('id')}", use_container_width=True): st.session_state.eco_active_conversation=conv.get("id"); st.session_state.eco_chat_view="Conversation"; st.rerun()
def render_chats_section(supabase, uid):
    v=st.session_state.get("eco_chat_view","Inbox")
    if v=="Conversation": render_direct_conversation(supabase, uid); return
    if v=="Profile": render_public_profile(supabase, st.session_state.get("eco_profile_view_user"), uid); return
    if v=="Discover People":
        st.markdown(f'<div class="wa-topbar"><b>New Chat</b><span>Find people by username</span></div>', unsafe_allow_html=True)
        if st.button("← Back to Dashboard", key="eco_newchat_back_dash"): eco_back_to_dashboard()
        if st.button("‹ Back"): st.session_state.eco_chat_view="Inbox"; st.rerun()
        q=st.text_input("Search people", key="eco_people_search_input", placeholder="Search @username or name… e.g. @thando"); profs=[p for p in get_member_directory(supabase, q) if p.get("user_id")!=uid]
        if not profs: st.info("No members found. Try another @username."); return
        for i,p in enumerate(profs): render_member_card(supabase, p, uid, f"directory_{i}")
        return
    if v=="My Profile": render_profile_editor(supabase, uid); return
    render_whatsapp_inbox(supabase, uid)
def get_chatrooms(supabase, search=""):
    try: rows=eco_select(supabase,"community_groups","*",order=("created_at",True),limit=150); q=(search or "").strip().lower()
    except Exception: return []
    if q: rows=[r for r in rows if q in str(r.get("name","")).lower() or q in str(r.get("description","")).lower() or q in str(r.get("location","")).lower()]
    return rows
def get_my_chatrooms(supabase, uid):
    try: ms=eco_select(supabase,"group_memberships","*",[("eq","user_id",uid),("eq","status","approved")],limit=200); ids={str(m.get("group_id")) for m in ms}; return [g for g in get_chatrooms(supabase) if str(g.get("id")) in ids]
    except Exception: return []
def ensure_invite_code(supabase, group):
    # FIX PGRST204: if column doesn't exist, don't crash — use group id as fallback code
    code=group.get("invite_code")
    if code: return code
    code="ECO-"+secrets.token_hex(3).upper()
    try: supabase.table("community_groups").update({"invite_code":code}).eq("id", group.get("id")).execute()
    except Exception as e:
        if "invite_code" in str(e): return "ECO-"+str(group.get("id"))[:6].upper()+" (Add invite_code column in Supabase to get real codes)"
        pass
    return code
def get_group_by_code(supabase, code):
    code=(code or "").strip().upper()
    if not code: return None
    if "code=" in code: code=code.split("code=")[-1].split("&")[0].split("/")[0].strip()
    if "/" in code: code=code.split("/")[-1].strip()
    try:
        rows=eco_select(supabase,"community_groups","*",[("eq","invite_code",code)],limit=1)
        if rows: return rows[0]
        rows=eco_select(supabase,"community_groups","*",[("eq","invite_code",code.replace("ECO-",""))],limit=1)
        if rows: return rows[0]
    except Exception: pass
    # Fallback: match by id prefix if invite_code column missing
    for g in get_chatrooms(supabase):
        if str(g.get("id"))[:6].upper() in code: return g
    return None
def join_via_code(supabase, uid, code):
    g=get_group_by_code(supabase, code)
    if not g: st.error("That invite code is not valid. Ask admin to send a fresh link. Also run: ALTER TABLE community_groups ADD COLUMN invite_code TEXT; in Supabase."); return
    try:
        eco_set_membership(supabase, g.get("id"), uid, role="member", status="approved")
        st.success(f"You joined {g.get('name')} 🎉"); st.session_state.eco_active_chatroom=g.get("id"); st.rerun()
    except Exception as e: st.error(f"Could not join: {e}")
def create_chatroom(supabase, uid, name, desc, img="", loc=""):
    code="ECO-"+secrets.token_hex(3).upper()
    # Try WITH invite_code first, fallback WITHOUT if column missing (PGRST204)
    try:
        res=supabase.table("community_groups").insert({"name":name.strip(),"description":desc.strip(),"created_by":uid,"image_url":img or None,"location":loc.strip() or None,"invite_code":code}).execute(); rows=eco_result_data(res); gid=rows[0].get("id") if rows else None
    except Exception as e:
        if "invite_code" not in str(e): raise e
        res=supabase.table("community_groups").insert({"name":name.strip(),"description":desc.strip(),"created_by":uid,"image_url":img or None,"location":loc.strip() or None}).execute(); rows=eco_result_data(res); gid=rows[0].get("id") if rows else None
        st.warning("Group created, but invite_code column is missing in Supabase. Run: ALTER TABLE community_groups ADD COLUMN invite_code TEXT; to enable invite links.")
    if not gid:
        m=eco_select(supabase,"community_groups","*",[("eq","created_by",uid),("eq","name",name.strip())],order=("created_at",True),limit=1); gid=m[0].get("id") if m else None
    if gid:
        try: eco_set_membership(supabase, gid, uid, role="admin", status="approved")
        except Exception: pass
    return gid
def request_join(supabase, gid, uid):
    # Use delete+insert, not upsert, to avoid P0001 trigger
    try: supabase.table("group_memberships").delete().eq("group_id",gid).eq("user_id",uid).execute()
    except Exception: pass
    return supabase.table("group_memberships").insert({"group_id":gid,"user_id":uid,"membership_role":"member","status":"pending"}).execute()
def leave_chatroom(supabase, gid, uid): return supabase.table("group_memberships").delete().eq("group_id",gid).eq("user_id",uid).execute()
def is_member(supabase, group, uid):
    try: rows=eco_select(supabase,"group_memberships","*",[("eq","group_id",group.get("id")),("eq","user_id",uid),("eq","status","approved")],limit=1); return bool(rows)
    except Exception: return str(group.get("created_by"))==str(uid)
def is_group_admin(supabase, group, uid):
    if str(group.get("created_by"))==str(uid): return True
    try: rows=eco_select(supabase,"group_memberships","*",[("eq","group_id",group.get("id")),("eq","user_id",uid),("eq","status","approved")],limit=1); return bool(rows and rows[0].get("membership_role")=="admin")
    except Exception: return False
def get_membership(supabase, gid, uid):
    try: rows=eco_select(supabase,"group_memberships","*",[("eq","group_id",gid),("eq","user_id",uid)],limit=1); return rows[0] if rows else {}
    except Exception: return {}
def get_group_messages(supabase, gid, limit=100):
    try: return eco_select(supabase,"group_messages","*",[("eq","group_id",gid),("is_","deleted_at","null")],order=("created_at",False),limit=limit)
    except Exception: return []
def get_group_members(supabase, gid):
    try: ms=eco_select(supabase,"group_memberships","*",[("eq","group_id",gid),("eq","status","approved")],limit=200); out=[]
    except Exception: return []
    for m in ms:
        p=eco_profile_with_avatar(supabase, m.get("user_id"))
        if p: p["_role"]=m.get("membership_role"); out.append(p)
    return out
def render_group_invite_box(supabase, group, uid):
    if not is_group_admin(supabase, group, uid): return
    gid=group.get("id"); code=ensure_invite_code(supabase, group)
    st.markdown('<div class="wa-pill"><b>🔗 Invite link — share to add people</b><br><span style="color:#667781;font-size:13px;">Anyone with this code joins instantly, no approval needed.</span></div>', unsafe_allow_html=True)
    st.code(code, language="text"); st.caption(f"Share this code: {code}")
    if st.button("🔄 Generate new invite link", key=f"eco_regen_invite_{gid}"):
        new="ECO-"+secrets.token_hex(3).upper()
        try: supabase.table("community_groups").update({"invite_code":new}).eq("id",gid).execute(); st.success(f"New invite code: {new}"); st.rerun()
        except Exception as e:
            if "invite_code" in str(e): st.error("Add invite_code column first in Supabase: ALTER TABLE community_groups ADD COLUMN invite_code TEXT;")
            else: st.error(str(e))
def render_group_members_manager(supabase, group, uid):
    gid=group.get("id"); admin=is_group_admin(supabase, group, uid)
    st.markdown("### 👥 Members")
    members=get_group_members(supabase, gid)
    if not members: st.caption("No members yet.")
    for i,m in enumerate(members):
        mu=str(m.get("user_id")); is_owner=str(group.get("created_by"))==mu; role=m.get("_role","member")
        with st.container(border=True):
            c1,c2=st.columns([1,4])
            with c1: st.markdown(eco_avatar_html(m,44), unsafe_allow_html=True)
            with c2: st.markdown(f"**{eco_display_name(m)}**"); st.caption(f"@{eco_safe_text(m.get('username'),'member')} · {'⭐ Admin' if role=='admin' else 'Member'}{' · Owner' if is_owner else ''}")
            if admin and mu!=str(uid) and not is_owner:
                b1,b2,b3=st.columns(3)
                with b1:
                    if role=="admin":
                        if st.button("Demote to Member", key=f"eco_demote_{gid}_{i}"):
                            try: eco_set_membership(supabase, gid, mu, role="member"); st.rerun()
                            except Exception as e: st.error(str(e))
                    else:
                        if st.button("Make Admin ⭐", key=f"eco_make_admin_{gid}_{i}"):
                            try: eco_set_membership(supabase, gid, mu, role="admin"); st.success(f"{eco_display_name(m)} is now Admin"); st.rerun()
                            except Exception as e: st.error(str(e))
                with b2:
                    if st.button("Remove ❌", key=f"eco_remove_{gid}_{i}"):
                        try: leave_chatroom(supabase, gid, mu); st.success("Removed"); st.rerun()
                        except Exception as e: st.error(str(e))
                with b3:
                    if st.button("Message", key=f"eco_msg_member_{gid}_{i}"):
                        try: conv=get_or_create_direct_conversation(supabase, uid, mu); st.session_state.eco_active_conversation=conv; st.session_state.eco_chat_view="Conversation"; st.rerun()
                        except Exception as e: st.error(str(e))
    if admin:
        st.markdown("### ➕ Add member directly")
        st.caption("Search by @username — choose Member or Admin, not just Admin.")
        q=st.text_input("Search person to add", placeholder="Search @username or name…", key=f"eco_admin_add_search_{gid}"); candidates=[p for p in get_member_directory(supabase, q) if str(p.get("user_id"))!=str(uid)][:20]; existing={str(m.get("user_id")) for m in members}
        for i,p in enumerate(candidates):
            puid=str(p.get("user_id"))
            if puid in existing: continue
            st.write(f"{eco_display_name(p)} (@{eco_safe_text(p.get('username'),'member')})")
            a1,a2=st.columns(2)
            with a1:
                if st.button("Add as Member", key=f"eco_admin_add_member_{gid}_{i}_{puid}", use_container_width=True):
                    try: eco_add_member_as(supabase, gid, puid, "member"); st.success(f"Added {eco_display_name(p)} as Member"); st.rerun()
                    except Exception as e: st.error(f"Could not add: {e}")
            with a2:
                if st.button("Add as Admin ⭐", key=f"eco_admin_add_admin_{gid}_{i}_{puid}", use_container_width=True):
                    try: eco_add_member_as(supabase, gid, puid, "admin"); st.success(f"Added {eco_display_name(p)} as Admin"); st.rerun()
                    except Exception as e: st.error(f"Could not add: {e}")
        render_group_invite_box(supabase, group, uid)
def render_chatroom_chat(supabase, group, uid):
    gid=group.get("id")
    if not is_member(supabase, group, uid):
        st.warning("You need to be a member to view this group chat.")
        st.markdown("### 🔗 Have an invite code?"); code=st.text_input("Invite code", key=f"eco_join_code_in_chat_{gid}", placeholder="Paste ECO-XXXXXX")
        if st.button("Join with code", key=f"eco_join_code_btn_{gid}"): join_via_code(supabase, uid, code)
        if st.button("‹ Back to groups"): st.session_state.eco_active_chatroom=None; st.rerun()
        return
    # CLEAN GROUP CHAT HEADER — no dashboard, no members panel open by default
    h1,h2,h3=st.columns([0.6,4,1])
    with h1:
        if st.button("‹", key=f"eco_room_back_{gid}"): st.session_state.eco_active_chatroom=None; st.session_state.eco_group_members_open=None; st.rerun()
    with h2: st.markdown(f"**{group.get('name','Community group')}**"); st.caption(eco_safe_text(group.get("description"),"Community conversation"))
    with h3:
        if st.button("👥", key=f"eco_members_toggle_{gid}"): st.session_state.eco_group_members_open=gid if st.session_state.get("eco_group_members_open")!=gid else None; st.rerun()
    # Members panel ONLY when tapped — hidden by default, that's the fix for "looks stupid"
    if st.session_state.get("eco_group_members_open")==gid:
        if st.button("✕ Close Members", key=f"eco_members_close_{gid}"): st.session_state.eco_group_members_open=None; st.rerun()
        render_group_members_manager(supabase, group, uid)
        st.divider()
    msgs=get_group_messages(supabase, gid); eco_render_bubbles_html(supabase, msgs, uid, is_group=True); render_whatsapp_composer(supabase, uid, group_id=gid)
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
        else: st.warning("This group could not be found.")
        return
    st.markdown(f'<div class="wa-topbar"><b>Groups</b><span>{HEADER}</span></div>', unsafe_allow_html=True)
    if st.button("← Back to Dashboard", key="eco_groups_back_dash"): eco_back_to_dashboard()
    views=["Discover","My Groups","Create"]; cur=st.session_state.get("eco_group_view","Discover"); sel=st.radio("Group sections", views, horizontal=True, key="eco_group_view_radio", label_visibility="collapsed", index=views.index(cur) if cur in views else 0); st.session_state.eco_group_view=sel
    if sel=="Discover":
        s=st.text_input("Search groups", placeholder="Search by group name, topic or location…", key="eco_group_search")
        for i,g in enumerate(get_chatrooms(supabase, s)): _render_group_card(supabase, g, uid, i, "discover")
    elif sel=="My Groups":
        groups=get_my_chatrooms(supabase, uid)
        if not groups: st.info("You have not joined any groups yet.")
        for i,g in enumerate(groups): _render_group_card(supabase, g, uid, i, "mine")
        for g in groups:
            if not is_group_admin(supabase, g, uid): continue
            with st.expander(f"Manage · {g.get('name','Group')} — Approve requests, Invite, Members"):
                try: pending=eco_select(supabase,"group_memberships","*",[("eq","group_id",g.get("id")),("eq","status","pending")],limit=100)
                except Exception: pending=[]
                if not pending: st.caption("No pending requests.")
                for j,req in enumerate(pending):
                    person=eco_profile_with_avatar(supabase, req.get("user_id")); a,b,c=st.columns([3,1,1])
                    with a: st.write(eco_display_name(person)); st.caption("@"+eco_safe_text(person.get("username"),"member"))
                    with b:
                        if st.button("Approve", key=f"eco_req_approve_{g.get('id')}_{j}"):
                            try: eco_set_membership(supabase, g.get("id"), req.get("user_id"), role="member", status="approved"); st.rerun()
                            except Exception as e: st.error(str(e))
                    with c:
                        if st.button("Reject", key=f"eco_req_reject_{g.get('id')}_{j}"):
                            try:
                                try: supabase.table("group_memberships").delete().eq("group_id",g.get("id")).eq("user_id",req.get("user_id")).execute()
                                except Exception: pass
                                supabase.table("group_memberships").insert({"group_id":g.get("id"),"user_id":req.get("user_id"),"membership_role":"member","status":"rejected"}).execute(); st.rerun()
                            except Exception as e: st.error(str(e))
                render_group_members_manager(supabase, g, uid)
    else:
        st.markdown("### Create a group")
        # Cover uploader OUTSIDE form so it works
        imgf=st.file_uploader("📷 Group cover image (optional) — tap to pick", type=["jpg","jpeg","png","webp"], key="eco_group_cover_upload_v2")
        if imgf: st.success(f"Picked cover: {imgf.name}")
        with st.form("eco_create_group_form_v2", clear_on_submit=True):
            name=st.text_input("Group name", placeholder="e.g. Bulawayo Climate Action"); desc=st.text_area("What is this group about?", max_chars=500); loc=st.text_input("Location (optional)"); submit=st.form_submit_button("Create community group", use_container_width=True)
        if submit:
            if len(name.strip())<3 or len(desc.strip())<8: st.error("Add a group name and a short description.")
            else:
                try:
                    path=eco_upload(supabase, imgf, "chatrooms", uid) if imgf else ""
                    gid=create_chatroom(supabase, uid, name, desc, path, loc)
                except Exception as e: st.error(f"Could not create group: {e}")
                else:
                    if gid: st.success("Your group has been created. Share the invite code to add people."); st.session_state.eco_active_chatroom=gid; st.rerun()
                    else: st.success("Group created. Find it under My Groups.")
def create_story(supabase, uid, caption, path, typ):
    now=eco_now(); exp=now+timedelta(hours=24); return supabase.table("stories").insert({"user_id":uid,"caption":(caption or "").strip(),"media_url":path,"media_type":typ,"created_at":now.isoformat(),"expires_at":exp.isoformat()}).execute()
def get_active_stories(supabase):
    try: return eco_select(supabase,"stories","*",[("gt","expires_at",eco_iso())],order=("created_at",True),limit=150)
    except Exception: return []
def get_story_views(supabase, sid):
    try: return eco_select(supabase,"story_views","*",[("eq","story_id",sid)],limit=200)
    except Exception: return []
def mark_story_viewed(supabase, sid, viewer):
    try: supabase.table("story_views").upsert({"story_id":sid,"viewer_id":viewer,"viewed_at":eco_iso()}, on_conflict="story_id,viewer_id").execute()
    except Exception: pass

# ---------- STORIES — ONE PAGE: create + view together, NO second dashboard ----------
def render_stories_page(supabase, uid):
    st.markdown(f'<div class="wa-topbar"><b>Stories</b><span>{HEADER} · 24 hours</span></div>', unsafe_allow_html=True)
    if st.button("← Back to Dashboard", key="eco_stories_back_dash"): eco_back_to_dashboard()
    # --- CREATE ON SAME PAGE, at top, uploader NOT in form ---
    st.markdown("### ➕ Add your story")
    st.caption("Pick a photo/video, add caption, Publish — same page, no second dashboard.")
    up=st.file_uploader("Tap here to pick photo / video for story", type=["jpg","jpeg","png","webp","mp4","mov","webm"], key="eco_story_upload_final")
    if up: st.success(f"Picked: {up.name}")
    cap=st.text_area("Add a caption (optional)", max_chars=180, key="eco_story_caption_final")
    if st.button("Publish story", key="eco_story_publish_final", use_container_width=True):
        if not up: st.warning("Choose a photo or video first.")
        else:
            try:
                with st.spinner("Uploading story..."): path=eco_upload(supabase, up, "stories", uid, allow_video=True)
                typ=up.type or "image"; create_story(supabase, uid, cap, path, typ); st.success("Your story is live for 24 hours."); st.rerun()
            except Exception as e: st.error(str(e))
    st.divider()
    # --- VIEW ---
    open_id=st.session_state.get("eco_story_open_id")
    if open_id:
        stories=get_active_stories(supabase); s=next((x for x in stories if str(x.get("id"))==str(open_id)), None)
        if s:
            prof=eco_profile_with_avatar(supabase, s.get("user_id")); name="Your story" if str(s.get("user_id"))==str(uid) else eco_display_name(prof)
            if st.button("✕ Close story", key="eco_story_close_open"): st.session_state.eco_story_open_id=None; st.rerun()
            c1,c2=st.columns([1,5])
            with c1: st.markdown(eco_avatar_html(prof, 44), unsafe_allow_html=True)
            with c2: st.markdown(f"**{name}**"); st.caption(eco_time_label(s.get("created_at"))+" · disappears in 24h")
            # FIX: story picture was not showing because media_url is a storage path, not URL. Use signed URL.
            url=eco_storage_url(supabase, s.get("media_url")); mt=str(s.get("media_type") or "")
            if url and mt.startswith("video"): st.video(url)
            elif url: st.image(url, use_container_width=True)
            elif s.get("media_url"): st.caption(f"Media: {s.get('media_url')}")
            else: st.caption("No media — caption only.")
            if s.get("caption"): st.markdown(f"**{s['caption']}**")
            mark_story_viewed(supabase, s.get("id"), uid)
            if str(s.get("user_id"))==str(uid):
                views=get_story_views(supabase, s.get("id")); st.markdown(f"### 👁 {len(views)} views")
                if not views: st.caption("No views yet.")
                for v in views:
                    vp=eco_profile_with_avatar(supabase, v.get("viewer_id")); st.caption(f"👁 {eco_display_name(vp)} (@{eco_safe_text(vp.get('username'),'member')})")
                if st.button("Delete this story", key=f"eco_story_del_open_{s.get('id')}"):
                    try: supabase.table("stories").delete().eq("id", s.get("id")).eq("user_id", uid).execute(); st.session_state.eco_story_open_id=None; st.success("Story deleted."); st.rerun()
                    except Exception as e: st.error(str(e))
            else:
                if st.button(f"💬 Message {name}", key=f"eco_story_msg_{s.get('id')}", use_container_width=True):
                    try: conv=get_or_create_direct_conversation(supabase, uid, s.get("user_id")); st.session_state.eco_active_conversation=conv; st.session_state.eco_chat_view="Conversation"; st.session_state.eco_story_open_id=None; st.rerun()
                    except Exception as e: st.error(str(e))
            st.divider()
    stories=get_active_stories(supabase); chat_ids=set()
    for c in get_direct_conversations(supabase, uid): chat_ids.add(str(get_other_user(c, uid)))
    mine=[s for s in stories if str(s.get("user_id"))==str(uid)]; friends=[s for s in stories if str(s.get("user_id")) in chat_ids and str(s.get("user_id"))!=str(uid)]; others=[s for s in stories if str(s.get("user_id")) not in chat_ids and str(s.get("user_id"))!=str(uid)]
    st.markdown("### Stories")
    seen_users=set(); circle_items=[]
    me_prof=eco_profile_with_avatar(supabase, uid); circle_items.append({"user_id": uid, "profile": me_prof, "name": "Your story", "is_mine": True, "story": mine[0] if mine else None}); seen_users.add(str(uid))
    for lst in [friends, others]:
        for s in lst:
            u=str(s.get("user_id"))
            if u in seen_users: continue
            seen_users.add(u); p=eco_profile_with_avatar(supabase, s.get("user_id")); circle_items.append({"user_id": s.get("user_id"), "profile": p, "name": eco_display_name(p), "is_mine": False, "story": s})
    if not circle_items: st.info("No stories yet. Be the first to share above.")
    else:
        cols=st.columns(5, gap="small")
        for idx, item in enumerate(circle_items):
            with cols[idx % 5]:
                prof=item["profile"]; viewed=False
                if not item["is_mine"] and item.get("story"):
                    vs=get_story_views(supabase, item["story"].get("id")); viewed=any(str(v.get("viewer_id"))==str(uid) for v in vs)
                ring="#25D366" if not viewed and not item["is_mine"] else "#D9D9D9"; url=prof.get("_avatar_resolved") or prof.get("avatar_url")
                if url and str(url).startswith("http"): avatar_html=f'<div style="width:62px;height:62px;border-radius:50%;border:3px solid {ring};padding:2px;margin:0 auto;"><img src="{url}" style="width:54px;height:54px;border-radius:50%;object-fit:cover;" /></div>'
                else: avatar_html=f'<div style="width:62px;height:62px;border-radius:50%;border:3px solid {ring};display:flex;align-items:center;justify-content:center;background:#DFE5E7;font-weight:700;margin:0 auto;">{eco_initials(item["name"])}</div>'
                st.markdown(f'<div style="text-align:center;">{avatar_html}<div style="font-size:11px;margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{item["name"][:10]}{" +" if item["is_mine"] and not mine else ""}</div></div>', unsafe_allow_html=True)
                btn_label="➕ Add" if item["is_mine"] and not mine else "View"
                if st.button(btn_label, key=f"eco_circle_{item['user_id']}_{idx}", use_container_width=True):
                    if item["is_mine"] and not mine: st.info("Use Add your story at the top of this page 👆"); 
                    elif item.get("story"): st.session_state.eco_story_open_id=item["story"].get("id"); st.rerun()
def render_discover(supabase, uid):
    st.markdown(f'<div class="wa-topbar"><b>Discover</b><span>People & Groups</span></div>', unsafe_allow_html=True)
    if st.button("← Back to Dashboard", key="eco_discover_back_dash"): eco_back_to_dashboard()
    q=st.text_input("Search people or groups", key="eco_discover_search_input", placeholder="Search @username, names, groups or locations…"); st.markdown("### People — tap View profile or Message")
    people=[p for p in get_member_directory(supabase, q) if str(p.get("user_id"))!=str(uid)]
    if people:
        for i,p in enumerate(people[:30]): render_member_card(supabase, p, uid, f"discover_{i}")
    else: st.caption("No matching people found. Try without @, e.g. 'thando' not '@thando'.")
    st.divider(); st.markdown("### Groups"); groups=get_chatrooms(supabase, q)
    if groups:
        for i,g in enumerate(groups[:30]): _render_group_card(supabase, g, uid, i, "discover_hub")
    else: st.caption("No matching groups found.")
def render_community_groups_page(supabase, user_id):
    eco_init_state(); eco_inject_styles()
    try:
        params=st.query_params; code=params.get("code","") if hasattr(params,"get") else ""
        if code and not st.session_state.get("eco_auto_joined_code")==code: st.session_state["eco_auto_joined_code"]=code; join_via_code(supabase, user_id, code)
    except Exception: pass
    private_open=st.session_state.get("eco_chat_view")=="Conversation"; room_open=bool(st.session_state.get("eco_active_chatroom")); st.session_state["eco_hide_app_footer"]=bool(private_open or room_open)
    if private_open:
        try: render_direct_conversation(supabase, user_id)
        except Exception as e: st.error("Private conversation could not load."); st.caption(f"Detail: {e}")
        return
    if room_open:
        try: render_chatrooms_page(supabase, user_id)
        except Exception as e: st.error("Chatroom could not load."); st.caption(f"Detail: {e}")
        return
    me=eco_profile_with_avatar(supabase, user_id); st.markdown(f'<div class="wa-topbar"><div style="display:flex;align-items:center;gap:10px;">{eco_avatar_html(me,38)}<div><b>{HEADER}</b><br><span>Next Gen Impact Hub · {eco_display_name(me)} · @{eco_safe_text(me.get("username"),"you")}</span></div></div><span>Connect · Talk · Create impact</span></div>', unsafe_allow_html=True)
    options=["💬 Chats","👥 Groups","🟢 Stories","🔎 Discover"]; labels={"💬 Chats":"Chats","👥 Groups":"Groups","🟢 Stories":"Stories","🔎 Discover":"Discover"}; cur=st.session_state.get("eco_community_section","Chats"); cur_opt=next((k for k,v in labels.items() if v==cur), options[0]); sel=st.radio("Community navigation", options, horizontal=True, key=MAIN_NAV_KEY, index=options.index(cur_opt), label_visibility="collapsed"); section=labels[sel]; st.session_state.eco_community_section=section
    try:
        if section=="Chats": render_whatsapp_inbox(supabase, user_id)
        elif section=="Groups": render_chatrooms_page(supabase, user_id)
        elif section=="Stories": render_stories_page(supabase, user_id)
        else: render_discover(supabase, user_id)
    except Exception as e: st.error("Community Hub section could not load."); st.caption(f"Detail: {e}")
    st.divider(); st.caption("Powered by Next Gen Impact Hub (NGIH) — Talk like Home, connect like Family.")
