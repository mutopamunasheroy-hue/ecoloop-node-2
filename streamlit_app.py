import streamlit as st
import pandas as pd
import qrcode
from PIL import Image, ImageEnhance
from pathlib import Path
from io import BytesIO
from datetime import datetime, date
import re

# =========================================================
# ECOLOOP NODE 2.0 | NGIH YOUTH-LED INITIATIVE
# =========================================================

st.set_page_config(
    page_title="EcoLoop Node 2.0",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

LOGO_CANDIDATES = [
    "NGIH_logo_HD.png",
    "ngih_logo_hd.png",
    "IMG-20261028-WA0000.jpg",
]

MATERIALS = [
    "Plastic", "Paper", "Metal",
    "Glass", "Organic", "Electronic"
]

STATIONS = {
    "ECO001": "City Centre Station",
    "ECO002": "Community Recycling Station",
    "ECO003": "School Recycling Station",
}

QUIZ = [
    {
        "question": "Which item is commonly recyclable when clean?",
        "options": [
            "Aluminium can", "Used tissue",
            "Dirty nappy", "Mixed food waste"
        ],
        "answer": "Aluminium can",
        "explanation": "Clean aluminium cans are widely recyclable. Local facilities may accept different materials."
    },
    {
        "question": "What should you do before recycling a container?",
        "options": [
            "Leave food inside",
            "Empty and rinse it if needed",
            "Mix it with general waste",
            "Burn it"
        ],
        "answer": "Empty and rinse it if needed",
        "explanation": "Keeping containers reasonably clean helps prevent contamination. Never burn waste."
    },
    {
        "question": "Which action helps reduce waste at the source?",
        "options": [
            "Use a reusable bottle",
            "Buy extra packaging",
            "Throw litter outdoors",
            "Burn plastic"
        ],
        "answer": "Use a reusable bottle",
        "explanation": "Reusable items can reduce the amount of single-use waste we generate."
    },
    {
        "question": "What does composting mainly help manage?",
        "options": [
            "Organic waste", "Glass bottles",
            "Metal cans", "Batteries"
        ],
        "answer": "Organic waste",
        "explanation": "Composting can turn suitable organic materials into a soil-improving product."
    },
    {
        "question": "Why should batteries be kept out of ordinary recycling bins?",
        "options": [
            "They are always harmless",
            "They can create fire and pollution risks",
            "They are food waste",
            "They dissolve in water"
        ],
        "answer": "They can create fire and pollution risks",
        "explanation": "Batteries need suitable collection and handling routes. Follow local guidance."
    },
]

# ------------------------- DESIGN -------------------------

st.markdown("""
<style>
:root {
  --forest:#123D2B;
  --green:#176B45;
  --lime:#B7F36B;
  --teal:#19B8A5;
  --amber:#FFB84D;
  --ink:#20352A;
}

.stApp {
    background:#F4F8F5;
    color:var(--ink);
}

[data-testid="stHeader"] {
    background:rgba(244,248,245,.92);
}

h1,h2,h3 {
    color:#145C3A !important;
    letter-spacing:-.025em;
}

p,li,label {
    color:#30463A;
}

[data-testid="stSidebar"] {
    background:linear-gradient(180deg,#123D2B,#0D3022);
}

[data-testid="stSidebar"] * {
    color:white !important;
}

[data-testid="stMetric"] {
    background:white;
    border:1px solid #DCE9DF;
    border-radius:16px;
    padding:16px;
    box-shadow:0 3px 14px rgba(18,61,43,.045);
}

[data-testid="stMetricLabel"] {
    color:#607568 !important;
}

[data-testid="stMetricValue"] {
    color:#145C3A !important;
}

.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
[data-baseweb="select"] {
    background:white !important;
}

div.stButton > button,
div.stFormSubmitButton > button {
    background:#176B45;
    color:white !important;
    border:0;
    border-radius:11px;
    min-height:43px;
    font-weight:650;
}

div.stButton > button:hover,
div.stFormSubmitButton > button:hover {
    background:#104D32;
    border:0;
}

.eco-hero {
    background:linear-gradient(
        115deg,
        #123D2B 0%,
        #176B45 58%,
        #19B8A5 100%
    );
    border-radius:22px;
    padding:30px;
    color:white;
    margin:8px 0 20px;
    box-shadow:0 10px 28px rgba(18,61,43,.13);
}

.eco-hero h1 {
    color:white !important;
    font-size:2.25rem;
    margin:0 0 8px;
}

.eco-hero p {
    color:#E8FFF0;
    font-size:1.02rem;
    margin:0;
}

.eco-tag {
    display:inline-block;
    background:#B7F36B;
    color:#173D29;
    border-radius:30px;
    padding:5px 12px;
    font-size:.78rem;
    font-weight:800;
    margin-bottom:12px;
}

.section-note {
    color:#65796D;
    font-size:.92rem;
}

.gallery-card {
    background:white;
    border:1px solid #DFEAE2;
    border-radius:15px;
    padding:10px;
    height:100%;
}

.gallery-caption {
    font-weight:700;
    color:#174A32;
    margin-top:7px;
}

.eco-footer {
    text-align:center;
    color:#66796D;
    padding:28px 8px;
    border-top:1px solid #DCE7DF;
    margin-top:40px;
    font-size:.9rem;
}
</style>
""", unsafe_allow_html=True)


# ------------------------- SESSION DATA -------------------------

defaults = {
    "users": [],
    "records": [],
    "collected": [],
    "gallery": [],
    "quiz_scores": {},
    "quiz_done": [],
    "groups": [],
    "active_page": "Home"
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ------------------------- HELPERS -------------------------

def find_logo():
    for candidate in LOGO_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    return None


def prepare_logo(path):
    image = Image.open(path).convert("RGBA")
    image.thumbnail((900, 900), Image.Resampling.LANCZOS)
    image = ImageEnhance.Sharpness(image).enhance(1.25)
    return image


def approved_records():
    return [
        r for r in st.session_state.records
        if r["status"] == "Approved"
    ]


def total_weight():
    return sum(r["weight"] for r in approved_records())


def user_points(username):
    waste_points = sum(
        r["points"] for r in approved_records()
        if r["username"] == username
    )

    quiz_points = st.session_state.quiz_scores.get(username, 0)

    return waste_points + quiz_points


def valid_email(email):
    return bool(
        re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email)
    )


def make_qr(station_id):
    qr = qrcode.QRCode(version=1, box_size=9, border=3)

    qr.add_data(
        f"EcoLoop Node 2.0 | Station: {station_id}"
    )

    qr.make(fit=True)

    img = qr.make_image(
        fill_color="#176B45",
        back_color="white"
    )

    out = BytesIO()
    img.save(out, format="PNG")

    return out.getvalue()


# ------------------------- BRAND / NAVIGATION -------------------------

logo_path = find_logo()

brand_left, brand_right = st.columns(
    [1, 5],
    vertical_alignment="center"
)

with brand_left:
    if logo_path:
        st.image(prepare_logo(logo_path), width=145)
    else:
        st.markdown("## 🌱 NGIH")

with brand_right:
    st.markdown(
        "<h1 style='margin:0'>EcoLoop Node 2.0</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p class='section-note'>Smart waste management · Community action · Environmental learning</p>",
        unsafe_allow_html=True
    )

st.divider()

st.sidebar.markdown("## ♻️ EcoLoop Node 2.0")

if logo_path:
    st.sidebar.image(prepare_logo(logo_path), width=125)

st.sidebar.caption("NGIH · A youth-led initiative")

pages = [
    "Home",
    "Explore & Learn",
    "Eco Quiz",
    "Action Gallery",
    "Community Groups",
    "Register",
    "My Profile",
    "Record Waste",
    "QR Stations",
    "Verify Contributions",
    "Leaderboard",
    "Collection Management",
    "Environmental Impact",
    "Admin Studio",
    "About"
]

page = st.sidebar.radio(
    "EXPLORE",
    pages,
    key="active_page"
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Platform status**")
st.sidebar.success("Interactive demonstration")
st.sidebar.caption(
    "Demo data is temporary and is not shared between visitors."
)


# ------------------------- HOME PAGE -------------------------

if page == "Home":

    st.markdown("""
    <div class="eco-hero">
      <span class="eco-tag">
        NGIH · YOUTH-LED INITIATIVE
      </span>

      <h1>
        Small actions. Smarter communities. A greener future.
      </h1>

      <p>
        Learn about waste, take environmental action,
        track contributions and celebrate community impact.
      </p>
    </div>
    """, unsafe_allow_html=True)

    records = approved_records()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Community members",
        len(st.session_state.users)
    )

    c2.metric(
        "Approved contributions",
        len(records)
    )

    c3.metric(
        "Waste recovered",
        f"{total_weight():.1f} kg"
    )

    c4.metric(
        "Action photos",
        len(st.session_state.gallery)
    )

    st.subheader("Our Impact in Action")

    st.markdown(
        "<p class='section-note'>Stories and photographs from environmental activities.</p>",
        unsafe_allow_html=True
    )

    if st.session_state.gallery:

        cols = st.columns(3)

        for i, item in enumerate(
            reversed(st.session_state.gallery[-6:])
        ):

            with cols[i % 3]:

                st.image(
                    item["image"],
                    use_container_width=True
                )

                st.markdown(
                    f"<div class='gallery-caption'>{item['title']}</div>",
                    unsafe_allow_html=True
                )

                st.caption(
                    f"{item['group']} · {item['date']}"
                )

                if item.get("caption"):
                    st.write(item["caption"])

    else:

        st.info(
            "The gallery is ready for its first NGIH and community uploads. Add photographs in Admin Studio."
        )

        sample_cols = st.columns(3)

        sample_cols[0].markdown("🌱 **Tree planting**")
        sample_cols[1].markdown("🧤 **Community clean-ups**")
        sample_cols[2].markdown("♻️ **Recycling activities**")

    st.subheader("Explore EcoLoop")

    feature_cols = st.columns(3)

    feature_cols[0].info(
        "🧠 **Learn**\n\nExplore environmental facts and take quick quizzes."
    )

    feature_cols[1].success(
        "🌍 **Participate**\n\nRecord contributions and join community activities."
    )

    feature_cols[2].warning(
        "🏆 **Celebrate**\n\nEarn demonstration points and recognise local action."
    )

    left, right = st.columns([1.3, 1])

    with left:

        st.subheader("Waste recovery overview")

        if records:

            df = pd.DataFrame(records)

            summary = df.groupby(
                "material",
                as_index=False
            )["weight"].sum()

            st.bar_chart(
                summary.set_index("material")
            )

        else:
            st.caption(
                "Approved contribution data will appear here."
            )

    with right:

        st.subheader("How it works")

        st.markdown(
            "**01 · Learn** — Build environmental knowledge.\n\n"
            "**02 · Take action** — Join clean-ups and recycling activities.\n\n"
            "**03 · Record** — Submit waste contributions.\n\n"
            "**04 · Verify** — Coordinators review submissions.\n\n"
            "**05 · Celebrate** — Track progress and community impact."
            )# ------------------------- LEARN -------------------------

elif page == "Explore & Learn":

    st.title("Explore & Learn 🌍")

    st.write(
        "Practical environmental knowledge for everyday decisions."
    )

    topics = {
        "Waste separation":
            "Separate materials according to the collection options available in your area. Keep recyclable materials as clean and dry as practical.",

        "Reduce and reuse":
            "Before recycling, consider whether you can avoid unnecessary packaging, repair an item or use it again.",

        "Organic waste":
            "Some food scraps and garden materials can be composted where suitable facilities and safe methods are available.",

        "E-waste":
            "Old electronics and batteries should go to suitable collection points. Do not dismantle or burn electronic waste.",

        "Community action":
            "Community clean-ups work best when participants have permission, safe equipment, supervision where needed and a plan for collected waste."
    }

    for title, detail in topics.items():

        with st.expander(title):
            st.write(detail)

    st.info(
        "Local recycling rules differ. Check what collection services in your area actually accept."
    )


# ------------------------- ECO QUIZ -------------------------

elif page == "Eco Quiz":

    st.title("Eco Challenge 🧠")

    st.write(
        "Test your knowledge with a short environmental quiz."
    )

    username = st.selectbox(
        "Choose your demo profile",
        ["Guest"] + [
            u["username"]
            for u in st.session_state.users
        ]
    )

    q_index = st.selectbox(
        "Choose a question",
        range(len(QUIZ)),
        format_func=lambda i: f"Question {i+1} of {len(QUIZ)}"
    )

    q = QUIZ[q_index]

    st.markdown(f"### {q['question']}")

    answer = st.radio(
        "Select one answer",
        q["options"],
        key=f"quiz_answer_{q_index}"
    )

    if st.button(
        "Check my answer",
        use_container_width=True
    ):

        quiz_key = f"{username}_{q_index}"

        first_attempt = (
            quiz_key not in st.session_state.quiz_done
        )

        if first_attempt:

            st.session_state.quiz_done.append(quiz_key)

            if answer == q["answer"] and username != "Guest":

                st.session_state.quiz_scores[username] = (
                    st.session_state.quiz_scores.get(username, 0) + 10
                )

        if answer == q["answer"]:

            st.success(
                "Correct! 🌟"
                + (
                    " You earned 10 demo EcoPoints."
                    if username != "Guest" and first_attempt
                    else ""
                )
            )

        else:

            st.info(
                f"Not quite. The correct answer is **{q['answer']}**."
            )

        st.write(q["explanation"])

    st.caption(
        "Quiz points are demonstration points, not money or prizes. "
        "Each profile can earn points once per question."
    )


# ------------------------- ACTION GALLERY -------------------------

elif page == "Action Gallery":

    st.title("Community Action Gallery 📸")

    st.write(
        "A space to document local environmental work and celebrate collective effort."
    )

    if not st.session_state.gallery:

        st.info(
            "No approved gallery photographs have been added yet. "
            "Upload photos through Admin Studio."
        )

    else:

        group_filter = st.selectbox(
            "Filter by group",
            ["All groups"] + sorted(
                set(
                    x["group"]
                    for x in st.session_state.gallery
                )
            )
        )

        if group_filter == "All groups":

            items = st.session_state.gallery

        else:

            items = [
                x for x in st.session_state.gallery
                if x["group"] == group_filter
            ]

        cols = st.columns(3)

        for i, item in enumerate(reversed(items)):

            with cols[i % 3]:

                st.image(
                    item["image"],
                    use_container_width=True
                )

                st.markdown(f"**{item['title']}**")

                st.caption(
                    f"{item['group']} · {item['date']}"
                )

                if item.get("caption"):
                    st.write(item["caption"])


# ------------------------- COMMUNITY GROUPS -------------------------

elif page == "Community Groups":

    st.title("Community Hubs 🤝")

    st.write(
        "Schools, clubs and informal community groups can request a space on EcoLoop."
    )

    with st.form("group_request"):

        group_name = st.text_input(
            "Group or community name"
        )

        group_type = st.selectbox(
            "Group type",
            [
                "Youth club",
                "School group",
                "University group",
                "Neighbourhood group",
                "Other community group"
            ]
        )

        group_area = st.text_input(
            "Community or area"
        )

        group_about = st.text_area(
            "What environmental activities does your group do?"
        )

        consent = st.checkbox(
            "I have permission to submit this group request."
        )

        submit_group = st.form_submit_button(
            "Submit group request"
        )

    if submit_group:

        if (
            not group_name.strip()
            or not group_area.strip()
            or not consent
        ):

            st.error(
                "Please enter the group name and area, "
                "and confirm permission to submit."
            )

        else:

            st.session_state.groups.append({

                "name": group_name.strip(),

                "type": group_type,

                "area": group_area.strip(),

                "about": group_about.strip(),

                "status": "Pending review"

            })

            st.success(
                "Your group request has been added to this demo for administrator review."
            )

    st.subheader("Groups in this demonstration")

    if st.session_state.groups:

        st.dataframe(
            pd.DataFrame(st.session_state.groups),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.caption("No group requests yet.")


# ------------------------- REGISTRATION -------------------------

elif page == "Register":

    st.title("Join the EcoLoop Community")

    st.write(
        "Create a demonstration profile to explore the platform."
    )

    with st.form("registration"):

        name = st.text_input("Display name")

        username = st.text_input("Choose a username")

        email = st.text_input(
            "Email address (demo only)"
        )

        account_type = st.selectbox(
            "I am joining as",
            [
                "Individual",
                "Youth club member",
                "School participant",
                "University participant",
                "Community member"
            ]
        )

        area = st.text_input("Community or area")

        st.caption(
            "Demo only: do not enter sensitive personal information. "
            "This form does not create a secure account."
        )

        submit = st.form_submit_button(
            "Create demo profile"
        )

    if submit:

        if not all([
            name.strip(),
            username.strip(),
            email.strip(),
            area.strip()
        ]):

            st.error("Please complete all fields.")

        elif not valid_email(email.strip()):

            st.error("Please enter a valid email address.")

        elif any(
            u["username"].lower() == username.strip().lower()
            for u in st.session_state.users
        ):

            st.error("That username is already in use.")

        else:

            st.session_state.users.append({

                "name": name.strip(),

                "username": username.strip(),

                "email": email.strip(),

                "type": account_type,

                "area": area.strip(),

                "joined": date.today().isoformat()

            })

            st.success(
                "Your demo profile has been created."
            )

            st.balloons()


# ------------------------- MY PROFILE -------------------------

elif page == "My Profile":

    st.title("My EcoLoop Profile")

    if not st.session_state.users:

        st.info("Create a demo profile first.")

    else:

        username = st.selectbox(
            "Select demo profile",
            [
                u["username"]
                for u in st.session_state.users
            ]
        )

        user = next(
            u for u in st.session_state.users
            if u["username"] == username
        )

        a, b, c = st.columns(3)

        a.metric(
            "EcoPoints",
            user_points(username)
        )

        b.metric(
            "Approved contributions",
            len([
                r for r in approved_records()
                if r["username"] == username
            ])
        )

        c.metric(
            "Waste recovered",
            f"{sum(
                r['weight']
                for r in approved_records()
                if r['username'] == username
            ):.1f} kg"
        )

        st.markdown(f"### {user['name']}")

        st.write(f"**Username:** {user['username']}")

        st.write(f"**Participant type:** {user['type']}")

        st.write(f"**Community:** {user['area']}")

        st.caption(
            "This is a demonstration profile selector, not secure sign-in."
        )


# ------------------------- RECORD WASTE -------------------------

elif page == "Record Waste":

    st.title("Record a Waste Contribution")

    if not st.session_state.users:

        st.info("Create a demo profile first.")

    else:

        with st.form("waste_record"):

            username = st.selectbox(
                "Participant",
                [
                    u["username"]
                    for u in st.session_state.users
                ]
            )

            material = st.selectbox(
                "Material",
                MATERIALS
            )

            weight = st.number_input(
                "Weight (kg)",
                min_value=0.1,
                max_value=1000.0,
                value=1.0,
                step=0.1
            )

            station = st.selectbox(
                "Station",
                list(STATIONS),
                format_func=lambda x:
                    f"{x} — {STATIONS[x]}"
            )

            submit = st.form_submit_button(
                "Submit for verification"
            )

        if submit:

            rid = (
                f"ECO-{len(st.session_state.records)+1:04d}"
            )

            st.session_state.records.append({

                "id": rid,

                "username": username,

                "material": material,

                "weight": float(weight),

                "station": station,

                "date": datetime.now().strftime(
                    "%Y-%m-%d %H:%M"
                ),

                "status": "Pending",

                "points": 0

            })

            st.success(
                f"{rid} submitted for review."
)# ------------------------- QR STATIONS -------------------------

elif page == "QR Stations":

    st.title("EcoLoop Collection Stations")

    for station_id, station_name in STATIONS.items():

        with st.expander(
            f"{station_id} — {station_name}"
        ):

            data = make_qr(station_id)

            st.image(data, width=190)

            st.download_button(
                "Download station QR",
                data,
                f"{station_id}_QR.png",
                "image/png",
                key=f"download_{station_id}"
            )

            st.caption(
                "Demo QR code for station identification only."
            )


# ------------------------- VERIFY CONTRIBUTIONS -------------------------

elif page == "Verify Contributions":

    st.title("Contribution Review")

    st.warning(
        "Demonstration coordinator controls only. "
        "There is no secure administrator login in this build."
    )

    pending = [
        r for r in st.session_state.records
        if r["status"] == "Pending"
    ]

    if not pending:

        st.info(
            "No contributions are waiting for review."
        )

    for r in pending:

        with st.container(border=True):

            st.markdown(
                f"**{r['id']}** · {r['username']}"
            )

            st.write(
                f"{r['material']} · "
                f"{r['weight']:.1f} kg · "
                f"{r['station']} · "
                f"{r['date']}"
            )

            yes, no = st.columns(2)

            if yes.button(
                "Approve",
                key=f"yes_{r['id']}"
            ):

                r["status"] = "Approved"

                r["points"] = (
                    5 + int(r["weight"] * 2)
                )

                st.rerun()

            if no.button(
                "Reject",
                key=f"no_{r['id']}"
            ):

                r["status"] = "Rejected"

                st.rerun()


# ------------------------- LEADERBOARD -------------------------

elif page == "Leaderboard":

    st.title("Community Leaderboard 🏆")

    if not st.session_state.users:

        st.info(
            "Participant rankings will appear when demo profiles are created."
        )

    else:

        rows = []

        for u in st.session_state.users:

            rows.append({

                "Participant": u["username"],

                "Community": u["area"],

                "Recovered (kg)": sum(
                    r["weight"]
                    for r in approved_records()
                    if r["username"] == u["username"]
                ),

                "EcoPoints": user_points(
                    u["username"]
                )

            })

        df = pd.DataFrame(rows)

        df = df.sort_values(
            "EcoPoints",
            ascending=False
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    st.caption(
        "EcoPoints are participation points in this demonstration, not cash rewards."
    )


# ------------------------- COLLECTION MANAGEMENT -------------------------

elif page == "Collection Management":

    st.title("Collection Management")

    waiting = [
        r for r in approved_records()
        if r["id"] not in st.session_state.collected
    ]

    st.metric(
        "Approved waste awaiting collection",
        f"{sum(r['weight'] for r in waiting):.1f} kg"
    )

    if not waiting:

        st.info(
            "No approved waste is awaiting collection."
        )

    for r in waiting:

        with st.container(border=True):

            st.write(
                f"**{r['id']}** · "
                f"{r['material']} · "
                f"{r['weight']:.1f} kg · "
                f"{STATIONS[r['station']]}"
            )

            if st.button(
                "Mark as collected",
                key=f"col_{r['id']}"
            ):

                st.session_state.collected.append(
                    r["id"]
                )

                st.rerun()


# ------------------------- ENVIRONMENTAL IMPACT -------------------------

elif page == "Environmental Impact":

    st.title("Environmental Impact Tracker")

    records = approved_records()

    a, b, c = st.columns(3)

    a.metric(
        "Waste recovered",
        f"{total_weight():.1f} kg"
    )

    b.metric(
        "Material categories",
        len(set(r["material"] for r in records))
    )

    c.metric(
        "Approved contributions",
        len(records)
    )

    if records:

        df = pd.DataFrame(records)

        summary = df.groupby(
            "material",
            as_index=False
        )["weight"].sum()

        st.bar_chart(
            summary.set_index("material")
        )

        st.dataframe(
            summary,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "Impact information will appear after contributions are reviewed."
        )

    st.caption(
        "This reports recorded quantities only; it does not calculate verified carbon savings."
    )


# ------------------------- ADMIN STUDIO -------------------------

elif page == "Admin Studio":

    st.title("Admin Studio ⚙️")

    st.warning(
        "This is an open demonstration admin page, not protected by secure sign-in. "
        "Do not publish sensitive content or use it as a live moderation system."
    )

    st.subheader("Upload activity photographs")

    st.write(
        "Add NGIH or community activity photos to the gallery."
    )

    with st.form("gallery_upload"):

        photo = st.file_uploader(
            "Choose a photograph",
            type=["png", "jpg", "jpeg", "webp"]
        )

        title = st.text_input(
            "Activity title",
            placeholder="e.g. Community clean-up day"
        )

        group = st.text_input(
            "Group name",
            value="NGIH — Youth-led initiative"
        )

        activity_date = st.date_input(
            "Activity date",
            value=date.today()
        )

        caption = st.text_area(
            "Photo caption or short description"
        )

        permission = st.checkbox(
            "I have permission to share this photograph, including from identifiable people shown."
        )

        upload = st.form_submit_button(
            "Add to gallery"
        )

    if upload:

        if (
            photo is None
            or not title.strip()
            or not group.strip()
        ):

            st.error(
                "Please choose a photo and enter the activity title and group."
            )

        elif not permission:

            st.error(
                "Please confirm you have permission to share the photograph."
            )

        else:

            try:

                img = Image.open(photo).convert("RGB")

                img.thumbnail(
                    (1600, 1600),
                    Image.Resampling.LANCZOS
                )

                out = BytesIO()

                img.save(
                    out,
                    format="JPEG",
                    quality=88,
                    optimize=True
                )

                st.session_state.gallery.append({

                    "image": out.getvalue(),

                    "title": title.strip(),

                    "group": group.strip(),

                    "date": activity_date.isoformat(),

                    "caption": caption.strip()

                })

                st.success(
                    "Photo added to this session's gallery."
                )

                st.rerun()

            except Exception:

                st.error(
                    "That image could not be opened. Please try a JPG or PNG."
                )

    st.caption(
        "Important: uploaded photos currently last only for this active app session. "
        "They will disappear when the session resets or the app restarts. "
        "Permanent shared galleries need Supabase Storage and a database."
    )

    st.divider()

    st.subheader("NGIH logo")

    st.write(
        "The app looks for NGIH_logo_HD.png first, "
        "then falls back to the existing JPG."
    )

    new_logo = st.file_uploader(
        "Upload a higher-resolution NGIH logo (PNG recommended)",
        type=["png", "jpg", "jpeg"],
        key="logo_upload"
    )

    if new_logo:

        try:

            logo_preview = Image.open(
                new_logo
            ).convert("RGBA")

            st.image(
                logo_preview,
                caption="Logo preview",
                width=220
            )

            st.info(
                "To use this logo after deployment, add it to the GitHub repository "
                "as NGIH_logo_HD.png (for PNG) and redeploy."
            )

        except Exception:

            st.error(
                "Could not read that logo file."
            )

    st.divider()

    st.subheader("Review group requests")

    if st.session_state.groups:

        for i, g in enumerate(
            st.session_state.groups
        ):

            with st.container(border=True):

                st.markdown(
                    f"**{g['name']}** · {g['type']}"
                )

                st.write(
                    f"{g['area']} — {g['about']}"
                )

                st.caption(g["status"])

                x, y = st.columns(2)

                if x.button(
                    "Approve request",
                    key=f"group_ok_{i}"
                ):

                    g["status"] = "Approved (demo)"

                    st.rerun()

                if y.button(
                    "Decline request",
                    key=f"group_no_{i}"
                ):

                    g["status"] = "Declined (demo)"

                    st.rerun()

    else:

        st.caption(
            "No group requests to review."
        )


# ------------------------- ABOUT -------------------------

elif page == "About":

    st.title("About EcoLoop Node 2.0")

    st.markdown("""
### A youth-led environmental technology project

EcoLoop Node 2.0 is being developed under
**Next Gen Impact Hub (NGIH), a youth-led initiative**.

It explores how accessible digital tools can support
waste separation, recycling participation, community action
and collection coordination.

### Our mission

Make waste management more accessible, organised and
data-informed through practical technology and community participation.

### Our approach

- Learn through short environmental activities and quizzes.
- Record and review waste contributions.
- Celebrate community clean-ups and environmental projects.
- Help groups document their activities and progress.
- Explore future integration with smart collection hardware.

### Future development

- Secure user accounts and administrator roles.
- Shared database and permanent photo storage.
- ESP32 sensor-enabled collection stations.
- Fill-level and weight monitoring.
- AI-assisted material classification, tested responsibly.
- Collection notifications and local recycling partnerships.

**Developed by:** Munashe R. Mutopa

**Initiative:** Next Gen Impact Hub (NGIH) — a youth-led initiative.
""")


# ------------------------- FOOTER -------------------------

st.markdown("""
<div class="eco-footer">

  <strong>EcoLoop Node 2.0</strong><br>

  A project of Next Gen Impact Hub (NGIH),
  a youth-led initiative.<br>

  Designed and developed by Munashe R. Mutopa.<br>

  <span>
    Building smarter and more sustainable communities.
  </span>

</div>
""", unsafe_allow_html=True)
