import streamlit as st
import pandas as pd
import qrcode
import io
import uuid
from datetime import date
from supabase import create_client

# =====================================================
# ECOLOOP NODE 2.0
# =====================================================

st.set_page_config(
    page_title="EcoLoop Node 2.0",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)
@st.cache_resource
def get_supabase_client():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

try:
    supabase = get_supabase_client()
    st.sidebar.success("Supabase client initialised")

except Exception as e:
    supabase = None
    st.sidebar.error(
        f"Supabase setup error: {type(e).__name__}: {e}"
    )
    )

# =====================================================
# DESIGN SYSTEM
# =====================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');

:root {
    --forest: #123D2B;
    --green: #176B45;
    --lime: #B7F36B;
    --teal: #19B8A5;
    --amber: #FFB84D;
    --ink: #17231D;
    --muted: #52645A;
    --paper: #F5F7F2;
    --white: #FFFFFF;
    --line: #DCE5DC;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background: var(--paper);
    color: var(--ink);
}

h1, h2, h3, h4 {
    color: var(--forest) !important;
    font-weight: 800 !important;
}

p, li, label {
    color: var(--ink);
}

/* HIGH-VISIBILITY MENU */

[data-testid="stSidebarCollapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: fixed !important;
    top: 12px !important;
    left: 12px !important;
    z-index: 999999 !important;
    background: #123D2B !important;
    border: 2px solid #B7F36B !important;
    border-radius: 12px !important;
    width: 54px !important;
    height: 50px !important;
    box-shadow: 0 3px 12px rgba(0,0,0,0.25) !important;
}

[data-testid="stSidebarCollapsedControl"] button {
    width: 50px !important;
    height: 46px !important;
    background: #123D2B !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
}

[data-testid="stSidebarCollapsedControl"] button svg {
    width: 27px !important;
    height: 27px !important;
    stroke: #FFFFFF !important;
    stroke-width: 2.8px !important;
}

[data-testid="stSidebarCollapseButton"] button {
    background: #B7F36B !important;
    color: #123D2B !important;
    border: 2px solid #FFFFFF !important;
    border-radius: 10px !important;
    width: 42px !important;
    height: 42px !important;
}

[data-testid="stSidebarCollapseButton"] button svg {
    stroke: #123D2B !important;
    width: 23px !important;
    height: 23px !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

/* SIDEBAR */

[data-testid="stSidebar"] {
    background: #123D2B !important;
}

[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}

[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.25) !important;
}

[data-testid="stSidebar"] [role="radiogroup"] label {
    background: rgba(255,255,255,0.07);
    border-radius: 9px;
    padding: 8px 10px;
    margin-bottom: 5px;
    color: #FFFFFF !important;
}

[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: rgba(183,243,107,0.18);
}

/* HERO */

.hero {
    background: linear-gradient(120deg, #123D2B, #176B45 65%, #19B8A5);
    border-radius: 22px;
    padding: 35px;
    margin-bottom: 24px;
}

.hero h1 {
    color: #FFFFFF !important;
    font-size: 40px;
    line-height: 1.15;
}

.hero p {
    color: #FFFFFF !important;
    font-size: 16px;
}

.eyebrow {
    color: #B7F36B !important;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 2px;
}

/* CARDS */

.eco-card {
    background: #FFFFFF;
    border: 1px solid #DCE5DC;
    border-radius: 17px;
    padding: 21px;
    margin-bottom: 14px;
    box-shadow: 0 3px 12px rgba(18,61,43,0.04);
}

.eco-card h3 {
    color: #123D2B !important;
    font-size: 19px;
}

.eco-card p {
    color: #26352D !important;
}

.stat-card {
    background: #FFFFFF;
    border: 1px solid #DCE5DC;
    border-radius: 16px;
    padding: 18px;
    min-height: 105px;
}

.stat-number {
    color: #123D2B;
    font-size: 28px;
    font-weight: 800;
}

.stat-caption {
    color: #52645A;
    font-size: 13px;
    font-weight: 600;
}

.section-label {
    color: #176B45;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 1.5px;
}

/* INFORMATION STRIPS */

.green-strip, .teal-strip, .amber-strip {
    border-radius: 11px;
    padding: 15px 18px;
    margin: 14px 0;
}

.green-strip {
    background: #E8F5E8;
    border-left: 5px solid #176B45;
}

.teal-strip {
    background: #E2F7F3;
    border-left: 5px solid #19B8A5;
}

.amber-strip {
    background: #FFF4DF;
    border-left: 5px solid #FFB84D;
}

.green-strip p, .teal-strip p, .amber-strip p {
    color: #17231D !important;
    margin: 0;
}

/* BUTTONS */

div.stButton > button,
div.stDownloadButton > button {
    background: #176B45 !important;
    color: #FFFFFF !important;
    border: 1px solid #176B45 !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    min-height: 43px;
}

div.stButton > button:hover,
div.stDownloadButton > button:hover {
    background: #123D2B !important;
    color: #FFFFFF !important;
}

/* INPUTS */

.stTextInput input,
.stTextArea textarea,
.stNumberInput input {
    background: #FFFFFF !important;
    color: #17231D !important;
    border: 1px solid #C9D8CC !important;
    border-radius: 9px !important;
}

[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #DCE5DC;
    padding: 14px;
    border-radius: 13px;
}

[data-testid="stMetricLabel"] {
    color: #52645A !important;
}

[data-testid="stMetricValue"] {
    color: #123D2B !important;
}

/* FOOTER */

.footer {
    background: #123D2B;
    border-radius: 18px;
    padding: 25px;
    margin-top: 35px;
    text-align: center;
}

.footer p {
    color: #FFFFFF !important;
    margin: 6px;
}

.footer .small {
    color: #D4E5D8 !important;
    font-size: 12px;
}
</style>
""", unsafe_allow_html=True)


# =====================================================
# SESSION DATA
# =====================================================

defaults = {
    "profile": {
        "name": "",
        "community": ""
    },
    "waste_records": [],
    "gallery": [],
    "groups": [{
        "id": "NGIH",
        "name": "Next Gen Impact Hub",
        "type": "Youth-led initiative",
        "description": "A youth-led initiative creating opportunities for positive change.",
        "status": "Approved"
    }],
    "pending_groups": [],
    "quiz_attempts": [],
    "points": 0,
    "quiz_score": None,
    "nodes": [
        {
            "id": "NODE-001",
            "name": "EcoLoop Node 001",
            "location": "Bulawayo",
            "function": "General recycling",
            "fill": 25,
            "status": "Active"
        },
        {
            "id": "NODE-002",
            "name": "EcoLoop Node 002",
            "location": "Bulawayo",
            "function": "Plastic collection",
            "fill": 65,
            "status": "Active"
        },
        {
            "id": "NODE-003",
            "name": "EcoLoop Node 003",
            "location": "Bulawayo",
            "function": "Paper collection",
            "fill": 90,
            "status": "Needs collection"
        }
    ],
    "collection_log": []
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def verified_records():
    return [
        record for record in st.session_state.waste_records
        if record["status"] == "Verified"
    ]


def verified_weight():
    return sum(
        float(record["weight"])
        for record in verified_records()
    )


def qr_image(value):
    qr = qrcode.QRCode(box_size=8, border=3)
    qr.add_data(value)
    qr.make(fit=True)

    img = qr.make_image(
        fill_color="#123D2B",
        back_color="white"
    )

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def stat_card(number, label):
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{number}</div>
        <div class="stat-caption">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def footer():
    st.markdown("""
    <div class="footer">
        <p><b>EcoLoop Node 2.0</b></p>
        <p>A project developed under NGIH — Next Gen Impact Hub.</p>
        <p>Small actions. Smarter communities. A greener future.</p>
        <p class="small">Developed by Munashe R. Mutopa</p>
    </div>
    """, unsafe_allow_html=True)


# =====================================================
# NAVIGATION
# =====================================================

with st.sidebar:

    try:
        st.image("IMG-20261028-WA0000.jpg", width=110)
    except Exception:
        st.markdown("## ♻️ ECOLOOP")

    st.markdown("### EcoLoop Node 2.0")
    st.caption("Smarter waste. Stronger communities.")
    st.divider()

    pages = {
        "HOME": ["Home"],
        "DISCOVER": [
            "Explore & Learn",
            "Eco Quiz",
            "Action Gallery",
            "Community Groups"
        ],
        "PARTICIPATE": [
            "My Profile",
            "Record Waste",
            "EcoLoop Nodes",
            "Leaderboard"
        ],
        "MONITOR": [
            "Environmental Impact",
            "Collection Management"
        ],
        "MANAGE": [
            "Verify Contributions",
            "Admin Studio"
        ],
        "ABOUT": ["About NGIH"]
    }

    page_options = []

    for section, items in pages.items():
        st.caption(section)
        page_options.extend(items)

    if "current_page" not in st.session_state:
        st.session_state.current_page = "Home"

    selected_page = st.radio(
        "Choose a page",
        page_options,
        key="current_page",
        label_visibility="collapsed"
    )

    st.divider()
    st.markdown(f"**🌱 EcoPoints: {st.session_state.points}**")
    st.caption("EcoLoop Node 2.0 • Prototype")


# =====================================================
# HOME PAGE
# =====================================================

if selected_page == "Home":

    st.markdown("""
    <div class="hero">
        <p class="eyebrow">NGIH • CLIMATE ACTION & ENVIRONMENT</p>
        <h1>Waste less.<br>Think smarter.<br>Act together.</h1>
        <p>
        A digital platform exploring how technology and community
        participation can support better waste management.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Welcome to EcoLoop Node 2.0")

    st.write(
        "A community-focused platform bringing environmental learning, "
        "waste contributions and local action together."
    )

    a, b, c, d = st.columns(4)

    with a:
        stat_card(
            len(st.session_state.waste_records),
            "Submissions"
        )

    with b:
        stat_card(
            f"{verified_weight():.1f} kg",
            "Verified waste"
        )

    with c:
        stat_card(
            len([
                item for item in st.session_state.gallery
                if item["status"] == "Approved"
            ]),
            "Published photos"
        )

    with d:
        stat_card(
            len(st.session_state.groups),
            "Community groups"
        )

    st.write("")

    st.markdown(
        '<p class="section-label">GET INVOLVED</p>',
        unsafe_allow_html=True
    )

    st.subheader("Small actions create collective impact")

    a, b, c = st.columns(3)

    with a:

        st.markdown("""
        <div class="eco-card">
            <h3>♻️ Record waste</h3>
            <p>Register waste contributions and support responsible recycling.</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Record a contribution"):
            st.session_state.current_page = "Record Waste"
            st.rerun()

    with b:

        st.markdown("""
        <div class="eco-card">
            <h3>🌱 Explore EcoLoop Nodes</h3>
            <p>Discover collection points and scan their QR codes.</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Explore EcoLoop Nodes"):
            st.session_state.current_page = "EcoLoop Nodes"
            st.rerun()

    with c:

        st.markdown("""
        <div class="eco-card">
            <h3>🧠 Learn and play</h3>
            <p>Explore environmental topics and test your knowledge.</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Try an eco quiz"):
            st.session_state.current_page = "Eco Quiz"
            st.rerun()

    st.markdown(
        '<p class="section-label">OUR APPROACH</p>',
        unsafe_allow_html=True
    )

    st.subheader("Technology meets community action")

    a, b = st.columns(2)

    with a:

        st.markdown("""
        <div class="eco-card">
            <h3>📊 Better information</h3>
            <p>Understand waste contributions and local patterns.</p>
        </div>
        <div class="eco-card">
            <h3>🤝 Community participation</h3>
            <p>Connect schools, youth groups and local initiatives.</p>
        </div>
        """, unsafe_allow_html=True)

    with b:

        st.markdown("""
        <div class="eco-card">
            <h3>📱 Accessible technology</h3>
            <p>Explore digital tools for reporting and coordination.</p>
        </div>
        <div class="eco-card">
            <h3>🌍 Environmental learning</h3>
            <p>Build awareness through quizzes and shared experiences.</p>
        </div>
        """, unsafe_allow_html=True)# =====================================================
# EXPLORE & LEARN
# =====================================================

elif selected_page == "Explore & Learn":

    st.title("🌍 Explore & Learn")
    st.write(
        "Discover practical ways to protect the environment "
        "and build more sustainable communities."
    )

    topics = {
        "Waste separation": {
            "description": "Separating waste makes recycling and responsible disposal easier.",
            "tips": [
                "Keep paper and cardboard separate from wet waste.",
                "Rinse recyclable containers where appropriate.",
                "Avoid mixing hazardous waste with ordinary household waste."
            ]
        },
        "Plastic pollution": {
            "description": "Plastic pollution affects land, rivers, wildlife and human settlements.",
            "tips": [
                "Choose reusable bags and containers where possible.",
                "Avoid unnecessary single-use plastics.",
                "Support responsible collection and recycling."
            ]
        },
        "Composting": {
            "description": "Composting turns suitable organic waste into useful soil material.",
            "tips": [
                "Separate fruit and vegetable scraps.",
                "Use suitable dry materials such as leaves.",
                "Avoid adding plastics or unsuitable materials."
            ]
        },
        "Climate action": {
            "description": "Local environmental action contributes to wider climate resilience.",
            "tips": [
                "Protect existing trees and green spaces.",
                "Participate in community clean-up activities.",
                "Share reliable environmental information."
            ]
        },
        "Circular economy": {
            "description": "A circular economy aims to reduce waste by keeping materials in use.",
            "tips": [
                "Repair items instead of immediately discarding them.",
                "Reuse materials where safe and practical.",
                "Support recycling and responsible production."
            ]
        }
    }

    selected_topic = st.selectbox(
        "Choose a learning topic",
        list(topics.keys())
    )

    topic = topics[selected_topic]

    st.markdown(f"""
    <div class="eco-card">
        <h3>{selected_topic}</h3>
        <p>{topic["description"]}</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Practical actions")

    for tip in topic["tips"]:
        st.markdown(f"- {tip}")

    st.markdown("""
    <div class="teal-strip">
        <p><b>Remember:</b> Environmental change begins with informed,
        consistent and collective action.</p>
    </div>
    """, unsafe_allow_html=True)


# =====================================================
# ECO QUIZ
# =====================================================

elif selected_page == "Eco Quiz":

    st.title("🧠 Eco Quiz")
    st.write("Test your environmental knowledge and earn demonstration points.")

    questions = [
        {
            "question": "What is the main purpose of waste separation?",
            "options": [
                "To make waste heavier",
                "To make recycling and disposal easier",
                "To increase pollution",
                "To mix all waste together"
            ],
            "answer": "To make recycling and disposal easier"
        },
        {
            "question": "Which of these is an example of organic waste?",
            "options": [
                "Plastic bottle",
                "Aluminium can",
                "Fruit peel",
                "Glass jar"
            ],
            "answer": "Fruit peel"
        },
        {
            "question": "What does reuse mean?",
            "options": [
                "Using an item again",
                "Burning all waste",
                "Throwing everything away",
                "Mixing recyclable materials"
            ],
            "answer": "Using an item again"
        },
        {
            "question": "Which action can help reduce plastic pollution?",
            "options": [
                "Dumping plastic in rivers",
                "Using reusable bags",
                "Burning plastic",
                "Littering public spaces"
            ],
            "answer": "Using reusable bags"
        },
        {
            "question": "What is composting?",
            "options": [
                "Making suitable organic waste into soil material",
                "Mixing plastic with metal",
                "Burning paper",
                "Dumping waste in water"
            ],
            "answer": "Making suitable organic waste into soil material"
        }
    ]

    with st.form("eco_quiz_form"):

        answers = {}

        for index, question in enumerate(questions):

            st.markdown(f"**Question {index + 1}**")
            st.write(question["question"])

            answers[index] = st.radio(
                "Select your answer",
                question["options"],
                key=f"eco_question_{index}",
                index=None
            )

            st.divider()

        submitted = st.form_submit_button(
            "Submit my answers",
            use_container_width=True
        )

    if submitted:

        unanswered = [
            index for index, answer in answers.items()
            if answer is None
        ]

        if unanswered:

            st.warning("Please answer all five questions first.")

        else:

            score = sum(
                answers[index] == questions[index]["answer"]
                for index in range(len(questions))
            )

            st.session_state.quiz_score = score
            earned = score * 5

            st.session_state.points += earned

            st.session_state.quiz_attempts.append({
                "date": str(date.today()),
                "score": score,
                "points": earned
            })

            st.success(f"You scored {score} out of 5!")
            st.metric("Demonstration EcoPoints earned", earned)

            if score == 5:
                st.balloons()
                st.write("Excellent work! You got every question correct.")

            elif score >= 3:
                st.write("Good effort! Keep learning.")

            else:
                st.write("Keep exploring the learning section and try again.")

    if st.session_state.quiz_score is not None:
        st.info(
            f"Your most recent quiz score: "
            f"{st.session_state.quiz_score}/5"
        )


# =====================================================
# ACTION GALLERY
# =====================================================

elif selected_page == "Action Gallery":

    st.title("📸 Community Action Gallery")

    st.write(
        "A space to showcase environmental activities, "
        "community clean-ups and local action."
    )

    st.markdown("""
    <div class="amber-strip">
        <p><b>Gallery review:</b> Submitted photos remain pending until
        an administrator approves them. Obtain permission before
        uploading identifiable photos of other people, especially minors.</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Share an environmental activity")

    with st.form("gallery_submission", clear_on_submit=True):

        contributor = st.text_input("Your name or group name")
        activity = st.text_input("Activity title")
        location = st.text_input("Activity location")
        description = st.text_area("Describe the activity")

        uploaded_photos = st.file_uploader(
            "Upload activity photos",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True
        )

        gallery_submit = st.form_submit_button(
            "Submit for review",
            use_container_width=True
        )

    if gallery_submit:

        if not contributor or not activity or not uploaded_photos:

            st.error("Please provide your name, activity title and at least one photo.")

        else:

            for photo in uploaded_photos:

                st.session_state.gallery.append({
                    "id": str(uuid.uuid4())[:8],
                    "contributor": contributor,
                    "activity": activity,
                    "location": location,
                    "description": description,
                    "photo": photo.getvalue(),
                    "filename": photo.name,
                    "status": "Pending"
                })

            st.success(
                f"{len(uploaded_photos)} photo(s) submitted for review."
            )

    st.divider()
    st.subheader("Published activities")

    published = [
        item for item in st.session_state.gallery
        if item["status"] == "Approved"
    ]

    if not published:

        st.info("No approved activities have been published yet.")

    else:

        columns = st.columns(2)

        for index, item in enumerate(published):

            with columns[index % 2]:

                st.image(
                    item["photo"],
                    use_container_width=True
                )

                st.markdown(f"**{item['activity']}**")
                st.caption(
                    f"{item['location']} • Shared by {item['contributor']}"
                )

                if item["description"]:
                    st.write(item["description"])


# =====================================================
# COMMUNITY GROUPS
# =====================================================

elif selected_page == "Community Groups":

    st.title("🤝 Community Groups")

    st.write(
        "Discover youth initiatives and community groups "
        "working towards environmental improvement."
    )

    st.subheader("Explore groups")

    approved_groups = [
        group for group in st.session_state.groups
        if group["status"] == "Approved"
    ]

    if not approved_groups:

        st.info("No approved groups are available yet.")

    else:

        for group in approved_groups:

            st.markdown(f"""
            <div class="eco-card">
                <h3>{group['name']}</h3>
                <p><b>Group type:</b> {group['type']}</p>
                <p>{group['description']}</p>
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    st.subheader("Request to add a community group")

    with st.form("group_request_form", clear_on_submit=True):

        group_name = st.text_input("Group or initiative name")

        group_type = st.selectbox(
            "Group type",
            [
                "Youth group",
                "School or university club",
                "Community organisation",
                "Environmental initiative",
                "Other"
            ]
        )

        group_location = st.text_input("Community or location")
        group_description = st.text_area("What does your group do?")
        contact_person = st.text_input("Contact person's name")

        group_submit = st.form_submit_button(
            "Submit group for approval",
            use_container_width=True
        )

    if group_submit:

        if not group_name or not group_location or not group_description:

            st.error("Please complete the required group details.")

        else:

            st.session_state.pending_groups.append({
                "id": str(uuid.uuid4())[:8],
                "name": group_name,
                "type": group_type,
                "location": group_location,
                "description": group_description,
                "contact": contact_person,
                "status": "Pending"
            })

            st.success(
                "Your group request has been submitted for review."
            )

    st.caption(
        "Group requests are demonstration submissions and require "
        "administrator review before publication."
    )# =====================================================
# MY PROFILE
# =====================================================

elif selected_page == "My Profile":

    st.title("👤 My Profile")
    st.write("Set up your EcoLoop participant profile.")

    with st.form("profile_form"):

        name = st.text_input(
            "Your name",
            value=st.session_state.profile["name"]
        )

        community = st.text_input(
            "Your community",
            value=st.session_state.profile["community"]
        )

        save_profile = st.form_submit_button(
            "Save profile",
            use_container_width=True
        )

    if save_profile:

        st.session_state.profile = {
            "name": name,
            "community": community
        }

        st.success("Profile saved for this session.")

    st.divider()
    st.subheader("Your EcoLoop activity")

    a, b, c = st.columns(3)

    with a:
        stat_card(st.session_state.points, "EcoPoints")

    with b:
        stat_card(len(st.session_state.waste_records), "Waste submissions")

    with c:
        stat_card(len(st.session_state.quiz_attempts), "Quiz attempts")

    st.caption(
        "Prototype note: profile information is currently stored "
        "temporarily in your browser session."
    )


# =====================================================
# RECORD WASTE
# =====================================================

elif selected_page == "Record Waste":

    st.title("♻️ Record a Waste Contribution")

    st.write(
        "Record waste collected or separated during a community activity."
    )

    with st.form("waste_record_form", clear_on_submit=True):

        contributor = st.text_input(
            "Contributor or group name",
            value=st.session_state.profile["name"]
        )

        waste_type = st.selectbox(
            "Waste category",
            [
                "Plastic",
                "Paper and cardboard",
                "Glass",
                "Metal",
                "Organic waste",
                "Mixed recyclable waste",
                "Other"
            ]
        )

        weight = st.number_input(
            "Estimated weight (kg)",
            min_value=0.1,
            max_value=10000.0,
            value=1.0,
            step=0.5
        )

        collection_location = st.text_input("Collection location")

        collection_date = st.date_input(
            "Date of collection",
            value=date.today()
        )

        notes = st.text_area("Additional information")

        waste_submit = st.form_submit_button(
            "Submit contribution",
            use_container_width=True
        )

    if waste_submit:

        if not contributor or not collection_location:

            st.error("Please enter the contributor and collection location.")

        else:

            st.session_state.waste_records.append({
                "id": str(uuid.uuid4())[:8],
                "contributor": contributor,
                "type": waste_type,
                "weight": float(weight),
                "location": collection_location,
                "date": str(collection_date),
                "notes": notes,
                "status": "Pending"
            })

            st.success(
                "Contribution submitted. It is awaiting verification."
            )

    st.divider()
    st.subheader("Your submitted contributions")

    if st.session_state.waste_records:

        for record in reversed(st.session_state.waste_records):

            st.markdown(f"""
            <div class="eco-card">
                <h3>{record['type']} • {record['weight']} kg</h3>
                <p><b>Contributor:</b> {record['contributor']}</p>
                <p><b>Location:</b> {record['location']}</p>
                <p><b>Date:</b> {record['date']}</p>
                <p><b>Status:</b> {record['status']}</p>
            </div>
            """, unsafe_allow_html=True)

    else:

        st.info("You have not submitted any contributions yet.")


# =====================================================
# ECOLOOP NODES
# =====================================================

elif selected_page == "EcoLoop Nodes":

    st.title("🌱 EcoLoop Nodes")

    st.write(
        "Explore identified waste collection points within the EcoLoop system."
    )

    st.markdown("""
    <div class="teal-strip">
        <p><b>How nodes work:</b> Each EcoLoop Node has a unique Node ID.
        Its QR code helps identify the node and its collection function.</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Node network overview")

    nodes = st.session_state.nodes

    a, b, c = st.columns(3)

    with a:
        stat_card(len(nodes), "Registered nodes")

    with b:
        stat_card(
            len([node for node in nodes if node["status"] == "Active"]),
            "Active nodes"
        )

    with c:
        stat_card(
            len([
                node for node in nodes
                if node["fill"] >= 80
            ]),
            "Nodes needing attention"
        )

    st.divider()
    st.subheader("Explore the nodes")

    for node in nodes:

        with st.container(border=True):

            left, right = st.columns([2, 1])

            with left:

                st.markdown(f"### {node['name']}")
                st.write(f"**Node ID:** {node['id']}")
                st.write(f"**Location:** {node['location']}")
                st.write(f"**Node function:** {node['function']}")
                st.write(f"**Status:** {node['status']}")

                st.write("Demonstration collection level")

                st.progress(
                    min(node["fill"], 100) / 100
                )

                st.caption(f"{node['fill']}% indicated fill level")

                if node["fill"] >= 80:
                    st.warning("Collection attention may be required.")
                else:
                    st.success("No high fill-level alert in this demonstration.")

            with right:

                qr_data = (
                    f"EcoLoop Node 2.0 | "
                    f"Node ID: {node['id']} | "
                    f"Name: {node['name']} | "
                    f"Location: {node['location']} | "
                    f"Function: {node['function']}"
                )

                qr_buffer = qr_image(qr_data)

                st.image(qr_buffer, width=150)

                st.download_button(
                    "Download Node QR",
                    data=qr_buffer.getvalue(),
                    file_name=f"{node['id']}.png",
                    mime="image/png",
                    key=f"download_{node['id']}"
                )

    st.divider()
    st.subheader("Understand the Node system")

    st.markdown("""
    <div class="eco-card">
        <h3>📍 Node identification</h3>
        <p>Every node has a unique identifier to distinguish it from
        other collection points.</p>
    </div>
    <div class="eco-card">
        <h3>📱 QR code access</h3>
        <p>QR codes provide a quick way to identify a node and view
        its basic information.</p>
    </div>
    <div class="eco-card">
        <h3>📊 Collection monitoring</h3>
        <p>Node records can help coordinate collection activities
        and monitor reported collection levels.</p>
    </div>
    """, unsafe_allow_html=True)

    st.caption(
        "Current prototype: QR codes are generated digitally. "
        "Fill levels are sample values, not live sensor readings."
    )


# =====================================================
# LEADERBOARD
# =====================================================

elif selected_page == "Leaderboard":

    st.title("🏆 EcoLoop Leaderboard")

    st.write(
        "A demonstration ranking based on EcoPoints earned through "
        "quiz participation."
    )

    leaderboard = {}

    for attempt in st.session_state.quiz_attempts:

        participant = st.session_state.profile["name"] or "Guest"

        leaderboard[participant] = (
            leaderboard.get(participant, 0) + attempt["points"]
        )

    leaderboard_data = [
        {
            "Participant": name,
            "EcoPoints": points
        }
        for name, points in leaderboard.items()
    ]

    if leaderboard_data:

        leaderboard_df = pd.DataFrame(leaderboard_data)

        leaderboard_df = leaderboard_df.sort_values(
            "EcoPoints",
            ascending=False
        ).reset_index(drop=True)

        leaderboard_df.index = leaderboard_df.index + 1

        st.dataframe(
            leaderboard_df,
            use_container_width=True
        )

    else:

        st.info(
            "Complete the Eco Quiz to appear on this demonstration leaderboard."
        )

    st.caption(
        "This prototype leaderboard is session-based and is not a shared "
        "community ranking."
    )


# =====================================================
# ENVIRONMENTAL IMPACT
# =====================================================

elif selected_page == "Environmental Impact":

    st.title("🌍 Environmental Impact Dashboard")

    st.write(
        "A snapshot of recorded and verified environmental contributions."
    )

    total_records = len(st.session_state.waste_records)
    verified = verified_records()

    pending = [
        record for record in st.session_state.waste_records
        if record["status"] == "Pending"
    ]

    total_verified = sum(
        record["weight"] for record in verified
    )

    a, b, c, d = st.columns(4)

    with a:
        stat_card(total_records, "Total submissions")

    with b:
        stat_card(len(verified), "Verified submissions")

    with c:
        stat_card(len(pending), "Pending submissions")

    with d:
        stat_card(f"{total_verified:.1f} kg", "Verified waste")

    st.divider()
    st.subheader("Verified waste by category")

    if verified:

        impact_df = pd.DataFrame(verified)

        category_data = (
            impact_df.groupby("type")["weight"]
            .sum()
            .sort_values(ascending=False)
        )

        st.bar_chart(category_data)

        st.dataframe(
            impact_df[
                ["contributor", "type", "weight", "location", "date"]
            ],
            use_container_width=True
        )

    else:

        st.info(
            "Verified waste data will appear here after contributions "
            "have been reviewed."
        )

    st.markdown("""
    <div class="green-strip">
        <p><b>Data integrity:</b> Only verified submissions are included
        in the verified waste total. Figures are based on prototype records.</p>
    </div>
    """, unsafe_allow_html=True)


# =====================================================
# COLLECTION MANAGEMENT
# =====================================================

elif selected_page == "Collection Management":

    st.title("🚛 Collection Management")

    st.write(
        "Monitor EcoLoop Nodes and coordinate collection activities."
    )

    node_df = pd.DataFrame(st.session_state.nodes)

    if not node_df.empty:

        st.dataframe(
            node_df,
            use_container_width=True
        )

        st.subheader("Node collection levels")

        for node in st.session_state.nodes:

            st.write(f"**{node['name']} — {node['location']}**")

            st.progress(
                min(node["fill"], 100) / 100
            )

            if node["fill"] >= 80:
                st.warning("Collection attention may be needed.")
            else:
                st.success("No high fill-level alert in this demonstration.")

    st.divider()
    st.subheader("Record a collection")

    with st.form("collection_form", clear_on_submit=True):

        node_id = st.selectbox(
            "Select EcoLoop Node",
            [node["id"] for node in st.session_state.nodes]
        )

        collection_team = st.text_input(
            "Collection team or responsible group"
        )

        collected_amount = st.number_input(
            "Collected amount (kg)",
            min_value=0.1,
            max_value=10000.0,
            value=1.0
        )

        collection_notes = st.text_area("Collection notes")

        collection_submit = st.form_submit_button(
            "Save collection record",
            use_container_width=True
        )

    if collection_submit:

        if not collection_team:

            st.error("Please enter the collection team.")

        else:

            st.session_state.collection_log.append({
                "node": node_id,
                "team": collection_team,
                "weight": float(collected_amount),
                "notes": collection_notes,
                "date": str(date.today())
            })

            st.success("Collection record saved.")

    if st.session_state.collection_log:

        st.subheader("Collection history")

        st.dataframe(
            pd.DataFrame(st.session_state.collection_log),
            use_container_width=True
        )


# =====================================================
# VERIFY CONTRIBUTIONS
# =====================================================

elif selected_page == "Verify Contributions":

    st.title("✅ Verify Contributions")

    st.write(
        "Review waste submissions, gallery contributions and group requests."
    )

    st.markdown("""
    <div class="amber-strip">
        <p><b>Prototype security notice:</b> This page is not protected
        by administrator authentication. Do not use it for real public
        administration until secure accounts and permissions are added.</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Waste submissions")

    pending_waste = [
        record for record in st.session_state.waste_records
        if record["status"] == "Pending"
    ]

    if not pending_waste:

        st.info("There are no pending waste submissions.")

    else:

        for record in pending_waste:

            with st.expander(
                f"{record['type']} — {record['weight']} kg — {record['contributor']}"
            ):

                st.write(f"Location: {record['location']}")
                st.write(f"Date: {record['date']}")
                st.write(f"Notes: {record['notes']}")

                col1, col2 = st.columns(2)

                with col1:

                    if st.button(
                        "Approve",
                        key=f"approve_waste_{record['id']}"
                    ):

                        record["status"] = "Verified"
                        st.success("Contribution verified.")
                        st.rerun()

                with col2:

                    if st.button(
                        "Reject",
                        key=f"reject_waste_{record['id']}"
                    ):

                        record["status"] = "Rejected"
                        st.warning("Contribution rejected.")
                        st.rerun()

    st.divider()
    st.subheader("Gallery submissions")

    pending_photos = [
        item for item in st.session_state.gallery
        if item["status"] == "Pending"
    ]

    if not pending_photos:

        st.info("There are no pending photos.")

    else:

        for item in pending_photos:

            with st.expander(item["activity"]):

                st.image(
                    item["photo"],
                    use_container_width=True
                )

                st.write(f"Contributor: {item['contributor']}")
                st.write(f"Location: {item['location']}")
                st.write(item["description"])

                col1, col2 = st.columns(2)

                with col1:

                    if st.button(
                        "Approve photo",
                        key=f"approve_photo_{item['id']}"
                    ):

                        item["status"] = "Approved"
                        st.success("Photo approved.")
                        st.rerun()

                with col2:

                    if st.button(
                        "Reject photo",
                        key=f"reject_photo_{item['id']}"
                    ):

                        item["status"] = "Rejected"
                        st.warning("Photo rejected.")
                        st.rerun()

    st.divider()
    st.subheader("Community group requests")

    pending_group_requests = [
        group for group in st.session_state.pending_groups
        if group["status"] == "Pending"
    ]

    if not pending_group_requests:

        st.info("There are no pending group requests.")

    else:

        for group in pending_group_requests:

            with st.expander(group["name"]):

                st.write(f"Type: {group['type']}")
                st.write(f"Location: {group['location']}")
                st.write(f"Description: {group['description']}")
                st.write(f"Contact: {group['contact']}")

                col1, col2 = st.columns(2)

                with col1:

                    if st.button(
                        "Approve group",
                        key=f"approve_group_{group['id']}"
                    ):

                        group["status"] = "Approved"

                        st.session_state.groups.append({
                            "id": group["id"],
                            "name": group["name"],
                            "type": group["type"],
                            "description": group["description"],
                            "status": "Approved"
                        })

                        st.success("Group approved.")
                        st.rerun()

                with col2:

                    if st.button(
                        "Reject group",
                        key=f"reject_group_{group['id']}"
                    ):

                        group["status"] = "Rejected"
                        st.warning("Group request rejected.")
                        st.rerun()


# =====================================================
# ADMIN STUDIO
# =====================================================

elif selected_page == "Admin Studio":

    st.title("⚙️ EcoLoop Admin Studio")

    st.write(
        "A demonstration overview of the platform's administrative data."
    )

    st.markdown("""
    <div class="amber-strip">
        <p><b>Important:</b> This is a prototype administration page.
        It has no secure login or role-based access. Do not expose it
        as a real administrator portal.</p>
    </div>
    """, unsafe_allow_html=True)

    a, b, c = st.columns(3)

    with a:
        stat_card(
            len(st.session_state.waste_records),
            "Waste records"
        )

    with b:
        stat_card(
            len(st.session_state.gallery),
            "Gallery submissions"
        )

    with c:
        stat_card(
            len(st.session_state.nodes),
            "EcoLoop Nodes"
        )

    st.divider()
    st.subheader("Waste contribution data")

    if st.session_state.waste_records:

        waste_export = pd.DataFrame(
            st.session_state.waste_records
        )

        st.dataframe(
            waste_export,
            use_container_width=True
        )

        csv_data = waste_export.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "Download waste records (CSV)",
            data=csv_data,
            file_name="ecoloop_waste_records.csv",
            mime="text/csv"
        )

    else:

        st.info("No waste records available.")

    st.divider()
    st.subheader("Export collection history")

    if st.session_state.collection_log:

        collection_export = pd.DataFrame(
            st.session_state.collection_log
        )

        csv_collection = collection_export.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "Download collection records (CSV)",
            data=csv_collection,
            file_name="ecoloop_collection_records.csv",
            mime="text/csv"
        )

    else:

        st.info("No collection records available.")

    st.divider()
    st.subheader("Prototype data management")

    if st.button("Clear this session's demonstration data"):

        st.session_state.clear()
        st.rerun()


# =====================================================
# ABOUT NGIH
# =====================================================

elif selected_page == "About NGIH":

    st.title("🌍 About NGIH")

    st.markdown("""
    <div class="hero">
        <p class="eyebrow">NEXT GEN IMPACT HUB</p>
        <h1>Young people.<br>Ideas. Impact.</h1>
        <p>
        Creating a generation of youth who lead and influence
        across governance, economy, environment and technology.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Our mission")

    st.write(
        "To create a generation of youth who lead and influence "
        "across governance, economy, environment, and technology."
    )

    st.subheader("Our four pillars")

    pillars = [
        (
            "🏛️ Governance & Civic Education",
            "Supporting informed participation, accountability and civic awareness."
        ),
        (
            "💼 Business & Entrepreneurship",
            "Encouraging innovation, enterprise and economic participation."
        ),
        (
            "🌱 Climate Action & Environment",
            "Promoting environmental responsibility and sustainable communities."
        ),
        (
            "💻 Technology, Innovation, Media & Arts",
            "Using creativity and technology to address real-world challenges."
        )
    ]

    for title, description in pillars:

        st.markdown(f"""
        <div class="eco-card">
            <h3>{title}</h3>
            <p>{description}</p>
        </div>
        """, unsafe_allow_html=True)

    st.subheader("About EcoLoop Node 2.0")

    st.write(
        "EcoLoop Node 2.0 is a digital environmental management "
        "prototype developed under NGIH's Climate Action & Environment pillar. "
        "It explores how accessible digital technology can support "
        "waste separation, recycling awareness, community participation "
        "and collection coordination."
    )

    st.markdown("""
    <div class="teal-strip">
        <p><b>Our vision:</b> Small actions. Smarter communities. A greener future.</p>
    </div>
    """, unsafe_allow_html=True)

    st.caption(
        "NGIH is presented here as a youth-led initiative."
    )


# =====================================================
# FOOTER
# =====================================================

footer()
