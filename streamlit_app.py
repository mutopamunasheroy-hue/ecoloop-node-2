import streamlit as st
import pandas as pd
import qrcode
from PIL import Image
from io import BytesIO
from pathlib import Path
from datetime import datetime
import uuid

# =====================================================
# ECOLOOP NODE 2.0 | NEXT GEN IMPACT HUB
# =====================================================

st.set_page_config(
    page_title="EcoLoop Node 2.0 | NGIH",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# BRAND COLOURS
DARK = "#123D2B"
GREEN = "#176B45"
LIME = "#B7F36B"
TEAL = "#19B8A5"
AMBER = "#FFB84D"
CREAM = "#F5F8F3"
WHITE = "#FFFFFF"

MISSION = (
    "To create a generation of youth who lead and influence "
    "across governance, economy, environment, and technology."
)

PILLARS = [
    "Governance & Civic Education",
    "Business & Entrepreneurship",
    "Climate Action & Environment",
    "Technology, Innovation, Media & Arts"
]

# =====================================================
# SESSION DATA
# =====================================================

defaults = {
    "users": {},
    "records": [],
    "gallery": [],
    "groups": ["NGIH"],
    "group_requests": [],
    "quiz_scores": {},
    "quiz_attempts": [],
    "active_user": None,
    "active_page": "Home",
    "collection_log": []
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def make_id():
    return str(uuid.uuid4())[:8]


def get_user():
    username = st.session_state.active_user
    if username:
        return st.session_state.users.get(username)
    return None


def approved_records():
    return [
        r for r in st.session_state.records
        if r["status"] == "Approved"
    ]


def total_waste():
    return sum(float(r["weight"]) for r in approved_records())


def points_for(username):
    quiz = st.session_state.quiz_scores.get(username, 0)

    waste = sum(
        int(float(r["weight"]) * 2) + 5
        for r in approved_records()
        if r["username"] == username
    )

    return quiz + waste


# =====================================================
# DESIGN AND MOBILE STYLING
# =====================================================

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif;
}}

.stApp {{
    background: {CREAM};
}}

[data-testid="stSidebar"] {{
    background: {DARK};
}}

[data-testid="stSidebar"] * {{
    color: white;
}}

.hero {{
    background: linear-gradient(120deg, {DARK}, {GREEN});
    padding: 34px 28px;
    border-radius: 20px;
    color: white;
    margin-bottom: 22px;
}}

.hero h1 {{
    color: white;
    font-size: clamp(30px, 5vw, 48px);
    font-weight: 800;
    line-height: 1.15;
}}

.hero p {{
    color: #EAF5E8;
    font-size: 17px;
    line-height: 1.65;
}}

.section-title {{
    color: {DARK};
    font-size: 25px;
    font-weight: 800;
    margin-top: 24px;
    margin-bottom: 14px;
}}

.feature-card {{
    background: white;
    border: 1px solid #E2EADF;
    border-radius: 16px;
    padding: 18px;
    min-height: 150px;
    margin-bottom: 12px;
}}

.feature-card h3 {{
    color: {DARK};
    font-size: 18px;
}}

.feature-card p {{
    color: #52645A;
    font-size: 14px;
    line-height: 1.6;
}}

.mission-card {{
    background: #EAF4E8;
    border-left: 5px solid {GREEN};
    padding: 20px;
    border-radius: 12px;
    color: {DARK};
    line-height: 1.7;
}}

div[data-testid="stMetric"] {{
    background: white;
    border: 1px solid #E2EADF;
    border-radius: 13px;
    padding: 12px;
}}

div.stButton > button {{
    border-radius: 10px;
    font-weight: 700;
    min-height: 42px;
}}

.gallery-card {{
    background: white;
    border: 1px solid #E2EADF;
    border-radius: 14px;
    padding: 12px;
    margin-bottom: 14px;
}}

@media(max-width: 700px) {{
    .hero {{
        padding: 24px 18px;
    }}
    .hero p {{
        font-size: 16px;
    }}
    .section-title {{
        font-size: 22px;
    }}
}}
</style>
""", unsafe_allow_html=True)


# =====================================================
# LOGO
# =====================================================

logo_options = [
    "NGIH_logo_HD.png",
    "ngih_logo_hd.png",
    "IMG-20261028-WA0000.jpg"
]

logo_path = next(
    (Path(x) for x in logo_options if Path(x).is_file()),
    None
)


# =====================================================
# NAVIGATION
# =====================================================

with st.sidebar:

    if logo_path:
        st.image(str(logo_path), width=135)
    else:
        st.markdown("## ♻️ NGIH")

    st.markdown("### ECOLOOP NODE 2.0")
    st.caption("Small actions. Smarter communities.")

    st.divider()

    navigation = {
        "EXPLORE": [
            "Home",
            "Explore & Learn",
            "Eco Quiz",
            "Action Gallery"
        ],
        "MY ACTION": [
            "My Profile",
            "Record Waste",
            "QR Stations",
            "Leaderboard"
        ],
        "COMMUNITY": [
            "Community Groups",
            "Collection Management",
            "Environmental Impact"
        ],
        "MANAGE": [
            "Register",
            "Verify Contributions",
            "Admin Studio",
            "About NGIH"
        ]
    }

    for heading, items in navigation.items():
        st.markdown(f"**{heading}**")

        for item in items:
            if st.button(
                item,
                key=f"nav_{item}",
                use_container_width=True
            ):
                st.session_state.active_page = item
                st.rerun()

    st.divider()

    user = get_user()

    if user:
        st.success(f"Welcome, {user['name']}")
        if st.button("Sign out", use_container_width=True):
            st.session_state.active_user = None
            st.rerun()
    else:
        st.caption("Browsing as a visitor.")

    st.caption("NGIH — A youth-led initiative")


page = st.session_state.active_page


# =====================================================
# HOME
# =====================================================

if page == "Home":

    st.markdown("""
    <div class="hero">
        <h1>Small actions.<br>
        Smarter communities.<br>
        A greener future.</h1>

        <p>
        Welcome to EcoLoop Node 2.0 — a digital platform
        connecting people, communities and recycling action.
        Learn, participate, record contributions and celebrate
        environmental impact.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">Explore EcoLoop</div>',
        unsafe_allow_html=True
    )

    a, b, c = st.columns(3)

    with a:
        st.markdown("""
        <div class="feature-card">
            <h3>📚 Learn</h3>
            <p>Explore recycling knowledge, waste separation
            and environmental awareness.</p>
        </div>
        """, unsafe_allow_html=True)

    with b:
        st.markdown("""
        <div class="feature-card">
            <h3>♻️ Participate</h3>
            <p>Record contributions, join community activities
            and take on EcoChallenges.</p>
        </div>
        """, unsafe_allow_html=True)

    with c:
        st.markdown("""
        <div class="feature-card">
            <h3>🏆 Celebrate</h3>
            <p>Earn EcoPoints, recognise participation and
            follow community progress.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">EcoLoop at a glance</div>',
        unsafe_allow_html=True
    )

    # Three columns to avoid squeezing mobile screens
    m1, m2, m3 = st.columns(3)

    with m1:
        st.metric("Approved", len(approved_records()))

    with m2:
        st.metric("Members", len(st.session_state.users))

    with m3:
        st.metric("Waste", f"{total_waste():.1f} kg")

    st.markdown(
        '<div class="section-title">Our Impact in Action</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Celebrating NGIH campaigns, clean-up exercises, "
        "youth participation and community environmental projects."
    )

    photos = [
        p for p in st.session_state.gallery
        if p["status"] == "Approved"
    ]

    if photos:
        cols = st.columns(3)

        for i, photo in enumerate(photos[-6:]):
            with cols[i % 3]:
                st.image(photo["image"], use_container_width=True)
                st.caption(
                    f"{photo['caption']} · {photo['group']}"
                )
    else:
        st.info(
            "The NGIH gallery is ready for its first campaign "
            "and community photographs."
        )

    st.markdown(
        '<div class="section-title">How EcoLoop works</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="mission-card">
    <b>1. Join</b> — Create a demonstration profile.<br><br>
    <b>2. Participate</b> — Record a waste contribution or
    join an environmental activity.<br><br>
    <b>3. Verify</b> — Contributions are reviewed before
    being counted.<br><br>
    <b>4. Track</b> — Follow approved contributions and
    community progress.
    </div>
    """, unsafe_allow_html=True)

    st.caption(
        "EcoLoop Node 2.0 is a demonstration platform. "
        "Physical smart-bin and sensor integration is planned "
        "for future development."
    )# =====================================================
# EXPLORE & LEARN
# =====================================================

elif page == "Explore & Learn":

    st.title("📚 Explore & Learn")

    st.write(
        "Build practical knowledge about waste management, "
        "recycling and environmental responsibility."
    )

    lessons = {
        "Understanding waste separation": (
            "Waste separation means sorting materials into "
            "different categories so they can be handled "
            "appropriately. Examples include paper, plastic, "
            "glass, metal and organic waste."
        ),
        "Why recycling matters": (
            "Recycling can reduce the amount of material sent "
            "to disposal sites, conserve resources and create "
            "opportunities for recovery and reuse."
        ),
        "The circular economy": (
            "A circular economy aims to keep products and "
            "materials in use for longer through reuse, repair, "
            "recycling and better product design."
        ),
        "Community environmental action": (
            "Community action includes clean-up campaigns, "
            "awareness activities, responsible disposal and "
            "working with local recycling partners."
        )
    }

    for title, description in lessons.items():
        with st.expander(title):
            st.write(description)


# =====================================================
# ECO QUIZ
# =====================================================

elif page == "Eco Quiz":

    st.title("🧠 Eco Quiz")

    st.write("Test your environmental knowledge.")

    questions = [
        {
            "question": "Which action helps reduce waste?",
            "options": [
                "Reusing materials",
                "Throwing everything away",
                "Mixing all waste"
            ],
            "answer": "Reusing materials"
        },
        {
            "question": "What is waste separation?",
            "options": [
                "Sorting waste into categories",
                "Burning all waste",
                "Mixing all materials"
            ],
            "answer": "Sorting waste into categories"
        },
        {
            "question": "Which is an example of organic waste?",
            "options": [
                "Fruit peels",
                "Glass bottles",
                "Metal cans"
            ],
            "answer": "Fruit peels"
        },
        {
            "question": "What does a circular economy encourage?",
            "options": [
                "Reuse and recovery",
                "Unnecessary disposal",
                "More littering"
            ],
            "answer": "Reuse and recovery"
        },
        {
            "question": "Why are community clean-ups useful?",
            "options": [
                "They improve shared spaces",
                "They increase litter",
                "They prevent recycling"
            ],
            "answer": "They improve shared spaces"
        }
    ]

    username = st.session_state.active_user

    if not username:
        st.warning("Register first to save your quiz score.")

    else:

        number = st.selectbox(
            "Choose a question",
            range(1, len(questions) + 1)
        )

        q = questions[number - 1]

        st.subheader(f"Question {number}")
        st.write(q["question"])

        answer = st.radio(
            "Select your answer",
            q["options"],
            key=f"quiz_answer_{number}"
        )

        if st.button("Submit answer"):

            attempt_key = f"{username}_{number}"

            attempted = attempt_key in st.session_state.quiz_attempts

            if answer == q["answer"]:

                st.success("Correct! Well done.")

                if not attempted:

                    st.session_state.quiz_scores[username] = (
                        st.session_state.quiz_scores.get(username, 0) + 10
                    )

                    st.session_state.quiz_attempts.append(attempt_key)

                    st.info("You earned 10 EcoPoints!")

                else:
                    st.caption("Points for this question were already awarded.")

            else:
                st.error("Not quite. Review the learning section and try again.")

        st.metric(
            "Quiz EcoPoints",
            st.session_state.quiz_scores.get(username, 0)
        )


# =====================================================
# ACTION GALLERY
# =====================================================

elif page == "Action Gallery":

    st.title("📸 Our Impact in Action")

    st.write(
        "A visual record of NGIH campaigns, clean-up activities, "
        "youth participation and community environmental projects."
    )

    # Gallery filtering
    approved_photos = [
        p for p in st.session_state.gallery
        if p["status"] == "Approved"
    ]

    available_groups = sorted(
        set(p["group"] for p in approved_photos)
    )

    selected_group = st.selectbox(
        "Explore gallery",
        ["All groups"] + available_groups
    )

    if selected_group == "All groups":
        display_photos = approved_photos
    else:
        display_photos = [
            p for p in approved_photos
            if p["group"] == selected_group
        ]

    if display_photos:

        cols = st.columns(2)

        for i, photo in enumerate(reversed(display_photos)):

            with cols[i % 2]:

                st.markdown(
                    '<div class="gallery-card">',
                    unsafe_allow_html=True
                )

                st.image(
                    photo["image"],
                    use_container_width=True
                )

                st.markdown(f"**{photo['caption']}**")

                st.caption(
                    f"{photo['group']} · {photo['date']}"
                )

                if photo.get("credit"):
                    st.caption(f"Credit: {photo['credit']}")

                st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.info(
            "No approved photographs yet. The gallery is ready "
            "for NGIH and participating community uploads."
        )

    st.divider()

    st.subheader("Upload campaign photographs")

    st.write(
        "Submit photographs from NGIH activities or participating "
        "community groups. Photos are reviewed before appearing publicly."
    )

    if not get_user():

        st.warning("Create a profile before submitting photographs.")

    else:

        group = st.selectbox(
            "Choose gallery",
            st.session_state.groups,
            key="upload_gallery_group"
        )

        caption = st.text_input(
            "Photo caption",
            placeholder="Example: Community clean-up activity"
        )

        credit = st.text_input(
            "Photographer or group credit (optional)"
        )

        uploads = st.file_uploader(
            "Select photographs",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="ngih_gallery_upload",
            help="You can select several JPG or PNG photographs."
        )

        # Preview selected files
        if uploads:

            st.success(f"{len(uploads)} photograph(s) selected.")

            preview_columns = st.columns(3)

            for i, uploaded in enumerate(uploads):

                try:
                    uploaded.seek(0)
                    image = Image.open(uploaded)
                    image.verify()

                    uploaded.seek(0)
                    image = Image.open(uploaded).convert("RGB")

                    with preview_columns[i % 3]:
                        st.image(
                            image,
                            caption=uploaded.name,
                            use_container_width=True
                        )

                except Exception:
                    st.error(
                        f"Unable to read {uploaded.name}. "
                        "Please try another image."
                    )

        permission = st.checkbox(
            "I confirm that I have permission to submit these "
            "photographs and that appropriate permission has been "
            "obtained from identifiable people shown."
        )

        if st.button(
            "Submit photographs for review",
            use_container_width=True
        ):

            if not uploads:
                st.error("Select at least one photograph.")

            elif not caption.strip():
                st.error("Please add a photo caption.")

            elif not permission:
                st.error("Please confirm the photo permissions.")

            else:

                saved = 0

                for uploaded in uploads:

                    try:
                        uploaded.seek(0)

                        image = Image.open(uploaded).convert("RGB")
                        image.thumbnail((1600, 1600))

                        buffer = BytesIO()

                        image.save(
                            buffer,
                            format="JPEG",
                            quality=88,
                            optimize=True
                        )

                        st.session_state.gallery.append({
                            "id": make_id(),
                            "image": buffer.getvalue(),
                            "caption": caption.strip(),
                            "credit": credit.strip(),
                            "group": group,
                            "date": datetime.now().strftime("%d %b %Y"),
                            "status": "Pending"
                        })

                        saved += 1

                    except Exception:
                        st.error(
                            f"Problem processing {uploaded.name}."
                        )

                if saved:
                    st.success(
                        f"{saved} photograph(s) submitted successfully."
                    )

                    st.info(
                        "Your photographs are awaiting administrator approval."
                    )


# =====================================================
# COMMUNITY GROUPS
# =====================================================

elif page == "Community Groups":

    st.title("🌍 Community Groups")

    st.write(
        "A space for schools, youth groups, community teams "
        "and environmental initiatives."
    )

    st.subheader("Participating galleries")

    for group in st.session_state.groups:
        st.markdown(f"♻️ **{group}**")

    st.divider()

    st.subheader("Request a community gallery")

    st.write(
        "Groups can request their own profile and dedicated "
        "campaign gallery."
    )

    group_name = st.text_input("Group or school name")
    area = st.text_input("Community or area")
    description = st.text_area("Describe your group's activities")

    if st.button("Submit group request"):

        if not group_name.strip() or not area.strip():

            st.error("Please provide the group name and area.")

        else:

            st.session_state.group_requests.append({
                "id": make_id(),
                "name": group_name.strip(),
                "area": area.strip(),
                "description": description.strip(),
                "status": "Pending"
            })

            st.success("Your request has been submitted for review.")


# =====================================================
# REGISTER
# =====================================================

elif page == "Register":

    st.title("👋 Join EcoLoop")

    st.write("Create a demonstration profile.")

    with st.form("register_form"):

        name = st.text_input("Display name")
        username = st.text_input("Choose a username")
        email = st.text_input("Email address")

        account_type = st.selectbox(
            "Joining as",
            [
                "Individual",
                "Student",
                "Community group member",
                "Volunteer"
            ]
        )

        area = st.text_input("Community or area")

        submit = st.form_submit_button("Create profile")

    if submit:

        key = username.strip().lower()

        if not name.strip() or not key:

            st.error("Please provide a name and username.")

        elif key in st.session_state.users:

            st.error("That username is already taken.")

        else:

            st.session_state.users[key] = {
                "name": name.strip(),
                "username": key,
                "email": email.strip(),
                "type": account_type,
                "area": area.strip(),
                "joined": datetime.now().strftime("%d %b %Y")
            }

            st.session_state.active_user = key

            st.success("Your profile has been created!")
            st.rerun()

    st.warning(
        "This is a demonstration registration system, not secure "
        "account authentication. Avoid entering sensitive information."
    )


# =====================================================
# MY PROFILE
# =====================================================

elif page == "My Profile":

    st.title("👤 My Profile")

    user = get_user()

    if not user:

        st.warning("Please register first.")

    else:

        username = user["username"]

        st.subheader(user["name"])

        st.write(f"**Username:** {username}")
        st.write(f"**Account type:** {user['type']}")
        st.write(f"**Community:** {user['area'] or 'Not provided'}")
        st.write(f"**Joined:** {user['joined']}")

        st.divider()

        c1, c2 = st.columns(2)

        with c1:
            st.metric("EcoPoints", points_for(username))

        with c2:

            count = sum(
                1 for r in approved_records()
                if r["username"] == username
            )

            st.metric("Approved", count)

        st.subheader("My contributions")

        mine = [
            r for r in st.session_state.records
            if r["username"] == username
        ]

        if mine:
            st.dataframe(
                pd.DataFrame(mine),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("You have not recorded a contribution yet.")# =====================================================
# RECORD WASTE
# =====================================================

elif page == "Record Waste":

    st.title("♻️ Record a Contribution")

    st.write(
        "Record waste collected for recycling or appropriate recovery."
    )

    user = get_user()

    if not user:

        st.warning("Please create a profile first.")

    else:

        with st.form("waste_form"):

            material = st.selectbox(
                "Material type",
                [
                    "Plastic",
                    "Paper",
                    "Cardboard",
                    "Glass",
                    "Metal",
                    "Organic",
                    "Other"
                ]
            )

            weight = st.number_input(
                "Estimated weight (kg)",
                min_value=0.1,
                max_value=10000.0,
                value=1.0,
                step=0.1
            )

            station = st.selectbox(
                "Collection point",
                [
                    "Community collection point",
                    "School collection point",
                    "NGIH activity",
                    "Other"
                ]
            )

            notes = st.text_area("Additional information")

            submit = st.form_submit_button("Submit contribution")

        if submit:

            st.session_state.records.append({
                "id": make_id(),
                "username": user["username"],
                "name": user["name"],
                "material": material,
                "weight": float(weight),
                "station": station,
                "notes": notes,
                "date": datetime.now().strftime("%d %b %Y %H:%M"),
                "status": "Pending"
            })

            st.success("Contribution submitted for verification.")


# =====================================================
# QR STATIONS
# =====================================================

elif page == "QR Stations":

    st.title("🔳 EcoLoop QR Stations")

    st.write(
        "Demonstration QR codes for identifying collection points."
    )

    stations = [
        "NGIH Community Station",
        "School Recycling Station",
        "Community Collection Point"
    ]

    for station in stations:

        with st.expander(station):

            qr = qrcode.make(f"EcoLoop Station: {station}")

            buffer = BytesIO()
            qr.save(buffer, format="PNG")

            st.image(buffer.getvalue(), width=200)

            st.download_button(
                "Download QR code",
                data=buffer.getvalue(),
                file_name=f"{station.replace(' ', '_')}.png",
                mime="image/png",
                key=f"qr_{station}"
            )


# =====================================================
# LEADERBOARD
# =====================================================

elif page == "Leaderboard":

    st.title("🏆 EcoLoop Leaderboard")

    st.write(
        "Recognising environmental participation through "
        "demonstration EcoPoints."
    )

    if not st.session_state.users:

        st.info("No members have registered yet.")

    else:

        rows = []

        for username, user in st.session_state.users.items():

            rows.append({
                "Member": user["name"],
                "Community": user["area"],
                "EcoPoints": points_for(username)
            })

        rows.sort(
            key=lambda x: x["EcoPoints"],
            reverse=True
        )

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True
        )

    st.caption(
        "EcoPoints are demonstration engagement points, "
        "not money or guaranteed rewards."
    )


# =====================================================
# COLLECTION MANAGEMENT
# =====================================================

elif page == "Collection Management":

    st.title("🚛 Collection Management")

    st.write(
        "A demonstration view of approved waste contributions "
        "available for collection coordination."
    )

    approved = approved_records()

    if approved:

        st.dataframe(
            pd.DataFrame(approved),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info("No approved contributions are listed yet.")

    st.divider()

    st.subheader("Record collection activity")

    notes = st.text_area("Collection activity notes")

    if st.button("Save collection activity"):

        if not notes.strip():

            st.error("Please add collection notes.")

        else:

            st.session_state.collection_log.append({
                "date": datetime.now().strftime("%d %b %Y %H:%M"),
                "notes": notes.strip()
            })

            st.success("Collection activity saved.")

    if st.session_state.collection_log:

        st.subheader("Collection activity log")

        st.dataframe(
            pd.DataFrame(st.session_state.collection_log),
            use_container_width=True,
            hide_index=True
        )


# =====================================================
# ENVIRONMENTAL IMPACT
# =====================================================

elif page == "Environmental Impact":

    st.title("🌱 Environmental Impact")

    st.write(
        "Follow the contributions recorded and approved "
        "through this EcoLoop demonstration."
    )

    records = approved_records()

    total = sum(float(r["weight"]) for r in records)

    members = len(set(r["username"] for r in records))

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("Waste", f"{total:.1f} kg")

    with c2:
        st.metric("Approved", len(records))

    with c3:
        st.metric("Members", members)

    if records:

        df = pd.DataFrame(records)

        st.subheader("Materials recorded")

        chart = df.groupby("material")["weight"].sum()

        st.bar_chart(chart)

        st.subheader("Contribution records")

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "Impact information will appear as contributions "
            "are submitted and approved."
        )

    st.caption(
        "This dashboard reports recorded weights only. "
        "It does not estimate unverified carbon savings."
    )


# =====================================================
# VERIFY CONTRIBUTIONS
# =====================================================

elif page == "Verify Contributions":

    st.title("✅ Verify Contributions")

    st.warning(
        "Demonstration admin area. It is not protected by secure "
        "administrator authentication. Do not use it for real "
        "community records."
    )

    pending = [
        r for r in st.session_state.records
        if r["status"] == "Pending"
    ]

    if not pending:

        st.info("No contributions awaiting review.")

    for record in pending:

        with st.expander(
            f"{record['name']} · {record['material']} · "
            f"{record['weight']} kg"
        ):

            st.write(f"**Station:** {record['station']}")
            st.write(f"**Date:** {record['date']}")
            st.write(f"**Notes:** {record['notes']}")

            a, b = st.columns(2)

            with a:

                if st.button(
                    "Approve",
                    key=f"approve_{record['id']}"
                ):

                    record["status"] = "Approved"

                    st.success("Contribution approved.")
                    st.rerun()

            with b:

                if st.button(
                    "Reject",
                    key=f"reject_{record['id']}"
                ):

                    record["status"] = "Rejected"

                    st.warning("Contribution rejected.")
                    st.rerun()


# =====================================================
# ADMIN STUDIO
# =====================================================

elif page == "Admin Studio":

    st.title("🛠️ NGIH Admin Studio")

    st.warning(
        "This demonstration admin area is not password-protected. "
        "Do not publish sensitive information or use it for real "
        "administrator operations."
    )

    st.subheader("Review gallery submissions")

    pending_photos = [
        p for p in st.session_state.gallery
        if p["status"] == "Pending"
    ]

    if not pending_photos:

        st.info("No photographs awaiting review.")

    for photo in pending_photos:

        with st.expander(photo["caption"]):

            st.image(
                photo["image"],
                use_container_width=True
            )

            st.caption(
                f"Group: {photo['group']} · "
                f"Credit: {photo['credit'] or 'Not supplied'}"
            )

            a, b = st.columns(2)

            with a:

                if st.button(
                    "Approve photo",
                    key=f"approve_photo_{photo['id']}"
                ):

                    photo["status"] = "Approved"

                    st.success("Photo approved.")
                    st.rerun()

            with b:

                if st.button(
                    "Reject photo",
                    key=f"reject_photo_{photo['id']}"
                ):

                    photo["status"] = "Rejected"

                    st.warning("Photo rejected.")
                    st.rerun()

    st.divider()

    st.subheader("Review community group requests")

    pending_groups = [
        g for g in st.session_state.group_requests
        if g["status"] == "Pending"
    ]

    if not pending_groups:

        st.info("No group requests awaiting review.")

    for group in pending_groups:

        with st.expander(group["name"]):

            st.write(f"**Area:** {group['area']}")
            st.write(group["description"])

            a, b = st.columns(2)

            with a:

                if st.button(
                    "Approve group",
                    key=f"approve_group_{group['id']}"
                ):

                    group["status"] = "Approved"

                    if group["name"] not in st.session_state.groups:
                        st.session_state.groups.append(group["name"])

                    st.success("Group approved.")
                    st.rerun()

            with b:

                if st.button(
                    "Decline group",
                    key=f"decline_group_{group['id']}"
                ):

                    group["status"] = "Declined"

                    st.warning("Group request declined.")
                    st.rerun()

    st.divider()

    st.subheader("Preview NGIH logo")

    logo_upload = st.file_uploader(
        "Choose a PNG or JPG logo",
        type=["png", "jpg", "jpeg"],
        key="logo_preview"
    )

    if logo_upload:

        try:

            image = Image.open(logo_upload)

            st.image(image, width=220)

            st.info(
                "This previews your logo. To update it permanently, "
                "upload the original high-resolution file to GitHub."
            )

        except Exception:

            st.error("The logo file could not be opened.")


# =====================================================
# ABOUT NGIH
# =====================================================

elif page == "About NGIH":

    st.title("🌍 About NGIH")

    st.subheader("Next Gen Impact Hub")

    st.markdown(f"""
    <div class="mission-card">
        <b>OUR MISSION</b><br><br>
        {MISSION}
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Our four pillars")

    for pillar in PILLARS:
        st.markdown(f"♻️ **{pillar}**")

    st.divider()

    st.subheader("About EcoLoop Node 2.0")

    st.write(
        "EcoLoop Node 2.0 is a youth-driven environmental "
        "technology project developed under NGIH. It explores "
        "how accessible digital tools can support waste separation, "
        "recycling participation, community coordination and "
        "environmental data."
    )

    st.write(
        "The current platform is a software demonstration. "
        "Future development aims to explore physical smart "
        "collection stations, sensor integration and "
        "AI-assisted waste classification."
    )

    st.divider()

    st.write(
        "We believe young people should not only participate "
        "in development, but also lead, influence and create "
        "solutions across the spaces that shape their communities."
    )

    st.caption("NGIH — A youth-led initiative.")


# =====================================================
# FOOTER
# =====================================================

st.divider()

st.markdown(f"""
<div style="text-align:center; padding:15px;">
    <h4 style="color:{DARK};">♻️ EcoLoop Node 2.0</h4>

    <p style="color:#52645A;">
    A project developed under NGIH — Next Gen Impact Hub.
    </p>

    <p style="color:#52645A;">
    Small actions. Smarter communities. A greener future.
    </p>

    <p style="color:#52645A; font-size:12px;">
    Developed by Munashe R. Mutopa
    </p>
</div>
""", unsafe_allow_html=True)
